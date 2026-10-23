-- PostgreSQL example. Supply :start_date and :end_date using parameters
-- through your SQL client. Do not interpolate untrusted input.
SELECT DATE_TRUNC('day', created_at) AS day, COUNT(*) AS event_count
FROM events
WHERE created_at >= :start_date
  AND created_at < :end_date
GROUP BY 1
ORDER BY 1;
