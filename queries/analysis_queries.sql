-- Query 1: Warehouse Performance
SELECT
    w.warehouse_id,
    w.warehouse_name,
    w.region,
    COUNT(o.order_id) as order_count,
    SUM(o.order_amount) as total_revenue
FROM warehouses w
LEFT JOIN orders o ON w.warehouse_id = o.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, w.region
ORDER BY order_count DESC;

-- Query 2: Order Status Distribution
SELECT
    order_status,
    COUNT(*) as order_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) as percentage
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;

-- Query 3: Delivery Performance SLA Analysis
SELECT
    priority_level,
    COUNT(*) as total_orders,
    ROUND(AVG(d.delivery_time_hours), 2) as avg_delivery_hours
FROM orders o
LEFT JOIN shipments s ON o.order_id = s.order_id
LEFT JOIN deliveries d ON s.shipment_id = d.shipment_id
WHERE d.delivery_status = 'Delivered'
GROUP BY priority_level;

-- Query 4: Warehouse Performance Metrics
SELECT
    w.warehouse_name,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.order_amount) as total_revenue,
    COUNT(CASE WHEN o.order_status = 'Completed' THEN 1 END) as completed_orders
FROM warehouses w
LEFT JOIN orders o ON w.warehouse_id = o.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name
ORDER BY total_orders DESC;

-- Query 5: Ticket Analysis
SELECT
    warehouse_id,
    ticket_type,
    COUNT(*) as ticket_count,
    ROUND(AVG(resolution_time_hours), 2) as avg_resolution_hours
FROM tickets
WHERE ticket_status = 'Resolved'
GROUP BY warehouse_id, ticket_type
ORDER BY avg_resolution_hours DESC;

-- Query 6: Full Order Lifecycle
SELECT
    o.order_id,
    o.order_date,
    w.warehouse_name,
    o.order_status,
    s.shipment_status,
    d.delivery_status,
    d.customer_satisfaction_score
FROM orders o
LEFT JOIN warehouses w ON o.warehouse_id = w.warehouse_id
LEFT JOIN shipments s ON o.order_id = s.order_id
LEFT JOIN deliveries d ON s.shipment_id = d.shipment_id
ORDER BY o.order_date DESC;

-- Query 7: High-Risk Orders
SELECT
    o.order_id,
    o.order_date,
    w.warehouse_name,
    o.order_amount,
    COUNT(t.ticket_id) as issue_count
FROM orders o
LEFT JOIN warehouses w ON o.warehouse_id = w.warehouse_id
LEFT JOIN tickets t ON o.order_id = t.order_id
WHERE t.ticket_id IS NOT NULL
GROUP BY o.order_id, o.order_date, w.warehouse_name, o.order_amount
ORDER BY issue_count DESC;

-- Query 8: Warehouse Capacity Utilization
SELECT
    w.warehouse_id,
    w.warehouse_name,
    w.capacity,
    COUNT(DISTINCT o.order_id) as orders_processed,
    ROUND(COUNT(DISTINCT o.order_id) * 100.0 / w.capacity, 2) as utilization_percentage
FROM warehouses w
LEFT JOIN orders o ON w.warehouse_id = o.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, w.capacity
ORDER BY utilization_percentage DESC;

-- Query 9: Carrier Performance
SELECT
    s.carrier,
    COUNT(DISTINCT s.shipment_id) as shipments_handled,
    ROUND(AVG(d.delivery_time_hours), 2) as avg_delivery_time,
    ROUND(AVG(d.customer_satisfaction_score), 2) as avg_satisfaction
FROM shipments s
LEFT JOIN deliveries d ON s.shipment_id = d.shipment_id
GROUP BY s.carrier
ORDER BY avg_satisfaction DESC;

-- Query 10: Daily Order Trend
SELECT
    DATE(o.order_date) as order_date,
    COUNT(*) as daily_orders,
    SUM(o.order_amount) as daily_revenue
FROM orders o
GROUP BY DATE(o.order_date)
ORDER BY order_date DESC;
