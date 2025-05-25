SELECT 
  dp.id AS pinned_deployment_id, 
  dp.endpoint AS endpoint,
  COUNT(inv.id) AS invocation_count
FROM 
  sys_deployment dp
LEFT JOIN 
  sys_invocation_status inv 
  ON dp.id = inv.pinned_deployment_id
WHERE
  dp.id NOT IN (
    SELECT DISTINCT deployment_id FROM sys_service
  )
GROUP BY 
  dp.id,
  dp.endpoint
HAVING invocation_count = 0;
