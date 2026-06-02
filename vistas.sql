-- ────────────────────────────────────────────────────────────
-- Vista 1: vista_ventas_por_categoria
-- Pregunta: ¿Cuántos pedidos y cuántos ingresos genera
--           cada categoría de producto, mes a mes?
-- Útil para: gráfica de barras / columnas en Looker Studio
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vista_ventas_por_categoria AS
SELECT
    DATE_TRUNC('month', p.fecha_pedido)::DATE  AS mes,
    c.nombre AS categoria,
    COUNT(DISTINCT p.pedido_id) AS num_pedidos,
    SUM(d.cantidad) AS unidades_vendidas,
    ROUND(SUM(d.subtotal)::NUMERIC, 2) AS ingresos
FROM pedidos p
JOIN detalle_pedido d  ON d.pedido_id  = p.pedido_id
JOIN productos pr ON pr.producto_id = d.producto_id
JOIN categorias c  ON c.categoria_id = pr.categoria_id
WHERE p.estado = 'Entregado'
GROUP BY mes, c.nombre
ORDER BY mes DESC, ingresos DESC;


-- ────────────────────────────────────────────────────────────
-- Vista 2: vista_pedidos_mensuales
-- Pregunta: ¿Cómo evolucionan el volumen de pedidos y los
--           ingresos totales a lo largo del tiempo?
-- Útil para: serie de tiempo (gráfica de líneas) en Looker Studio
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vista_pedidos_mensuales AS
SELECT
    DATE_TRUNC('month', p.fecha_pedido)::DATE AS mes,
    COUNT(DISTINCT p.pedido_id) AS total_pedidos,
    COUNT(DISTINCT p.pedido_id)
        FILTER (WHERE p.estado = 'Entregado') AS pedidos_entregados,
    COUNT(DISTINCT p.pedido_id)
        FILTER (WHERE p.estado = 'Cancelado') AS pedidos_cancelados,
    ROUND(SUM(d.subtotal)::NUMERIC, 2) AS ingresos_brutos,
    ROUND(AVG(p.total)::NUMERIC, 2) AS ticket_promedio
FROM pedidos p
JOIN detalle_pedido d
    ON d.pedido_id = p.pedido_id
GROUP BY mes
ORDER BY mes ASC;


-- ────────────────────────────────────────────────────────────
-- Vista 3: vista_clientes_resumen
-- Pregunta: ¿Cuáles son los clientes más valiosos?
--           ¿Cuánto ha gastado cada uno y cuántos pedidos tiene?
-- Útil para: tabla de métricas / scorecard en Looker Studio
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vista_clientes_resumen AS
SELECT
    u.usuario_id,
    u.nombre || ' ' || u.apellido AS cliente,
    u.pais,
    u.ciudad,
    u.genero,
    COUNT(DISTINCT p.pedido_id) AS total_pedidos,
    ROUND(SUM(p.total)::NUMERIC, 2) AS gasto_total,
    ROUND(AVG(p.total)::NUMERIC, 2) AS ticket_promedio,
    MAX(p.fecha_pedido) AS ultimo_pedido
FROM usuarios u
JOIN pedidos p ON p.usuario_id = u.usuario_id
GROUP BY u.usuario_id, u.nombre, u.apellido, u.pais, u.ciudad, u.genero
ORDER BY gasto_total DESC;