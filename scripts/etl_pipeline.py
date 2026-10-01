#!/usr/bin/env python3
"""
ETL Pipeline: Load WMS data from CSVs to SQLite Database
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
DB_PATH = PROJECT_ROOT / 'data' / 'logistics.db'

def create_connection():
    return sqlite3.connect(str(DB_PATH))

def load_csv_to_db(csv_file, table_name, conn):
    df = pd.read_csv(csv_file)
    print(f"  Loading {table_name}: {len(df)} rows")
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    return df

def create_indexes(conn):
    cursor = conn.cursor()
    indexes = [
        "CREATE INDEX idx_orders_warehouse ON orders(warehouse_id);",
        "CREATE INDEX idx_orders_status ON orders(order_status);",
        "CREATE INDEX idx_orders_date ON orders(order_date);",
        "CREATE INDEX idx_shipments_order ON shipments(order_id);",
        "CREATE INDEX idx_shipments_status ON shipments(shipment_status);",
        "CREATE INDEX idx_deliveries_shipment ON deliveries(shipment_id);",
        "CREATE INDEX idx_tickets_warehouse ON tickets(warehouse_id);",
        "CREATE INDEX idx_tickets_status ON tickets(ticket_status);",
    ]

    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    print("  Indexes created")

def create_views(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS vw_order_summary AS
    SELECT
        o.order_id,
        o.order_date,
        o.warehouse_id,
        w.warehouse_name,
        o.order_amount,
        o.order_status,
        o.priority_level
    FROM orders o
    JOIN warehouses w ON o.warehouse_id = w.warehouse_id;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS vw_order_lifecycle AS
    SELECT
        o.order_id,
        o.order_date,
        o.warehouse_id,
        w.warehouse_name,
        o.order_amount,
        o.order_status,
        s.shipment_status,
        d.delivery_status,
        d.delivery_time_hours,
        d.customer_satisfaction_score,
        CASE WHEN t.ticket_id IS NOT NULL THEN 1 ELSE 0 END as has_issue
    FROM orders o
    LEFT JOIN warehouses w ON o.warehouse_id = w.warehouse_id
    LEFT JOIN shipments s ON o.order_id = s.order_id
    LEFT JOIN deliveries d ON s.shipment_id = d.shipment_id
    LEFT JOIN tickets t ON o.order_id = t.order_id;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS vw_warehouse_performance AS
    SELECT
        w.warehouse_id,
        w.warehouse_name,
        COUNT(DISTINCT o.order_id) as total_orders,
        SUM(o.order_amount) as total_order_value,
        COUNT(CASE WHEN o.order_status = 'Completed' THEN 1 END) as completed_orders,
        COUNT(CASE WHEN t.ticket_id IS NOT NULL THEN 1 END) as total_tickets,
        ROUND(COUNT(CASE WHEN o.order_status = 'Completed' THEN 1 END) * 100.0 /
              COUNT(DISTINCT o.order_id), 2) as completion_rate
    FROM warehouses w
    LEFT JOIN orders o ON w.warehouse_id = o.warehouse_id
    LEFT JOIN tickets t ON w.warehouse_id = t.warehouse_id
    GROUP BY w.warehouse_id, w.warehouse_name;
    """)

    conn.commit()
    print("  Views created")

def validate_data(conn):
    cursor = conn.cursor()
    print("\nData Quality Checks:")

    cursor.execute("SELECT COUNT(*) FROM orders WHERE order_id IS NULL;")
    null_orders = cursor.fetchone()[0]
    print(f"  Null order_ids: {null_orders}")

    cursor.execute("""
    SELECT COUNT(*) FROM shipments s
    WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.order_id = s.order_id);
    """)
    orphaned = cursor.fetchone()[0]
    print(f"  Orphaned shipments: {orphaned}")

    cursor.execute("""
    SELECT COUNT(*) FROM orders o
    WHERE NOT EXISTS (SELECT 1 FROM warehouses w WHERE w.warehouse_id = o.warehouse_id);
    """)
    invalid_warehouse = cursor.fetchone()[0]
    print(f"  Invalid warehouse references: {invalid_warehouse}")

    cursor.execute("SELECT COUNT(*) FROM orders;")
    total_orders = cursor.fetchone()[0]
    print(f"  Total orders loaded: {total_orders}")

def main():
    print("Starting ETL Pipeline...\n")

    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"Removed existing database\n")

    conn = create_connection()

    try:
        print("Loading CSV files:")
        load_csv_to_db(RAW_DATA_DIR / 'warehouses.csv', 'warehouses', conn)
        load_csv_to_db(RAW_DATA_DIR / 'orders.csv', 'orders', conn)
        load_csv_to_db(RAW_DATA_DIR / 'shipments.csv', 'shipments', conn)
        load_csv_to_db(RAW_DATA_DIR / 'deliveries.csv', 'deliveries', conn)
        load_csv_to_db(RAW_DATA_DIR / 'tickets.csv', 'tickets', conn)

        print("\nCreating indexes:")
        create_indexes(conn)

        print("\nCreating views:")
        create_views(conn)

        validate_data(conn)

        print(f"\n✓ ETL Pipeline completed successfully!")
        print(f"✓ Database created at: data/logistics.db")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
