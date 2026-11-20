-- ============================================================
-- 社交游戏运营分析 · SQL 指标库
-- 数据库：SQLite（game.db），表：users、events
-- 说明：每条查询以 “-- @Q编号 名称” 开头，供 run_analysis.py 自动执行
-- ============================================================

-- @Q1 每日 DAU
SELECT event_date,
       COUNT(DISTINCT user_id) AS dau
FROM events
WHERE event_type = 'login'
GROUP BY event_date
ORDER BY event_date;

-- @Q2 每日新增用户
SELECT reg_date,
       COUNT(*) AS new_users
FROM users
GROUP BY reg_date
ORDER BY reg_date;

-- @Q3 各注册日 cohort 的次日留存
SELECT u.reg_date,
       COUNT(*) AS cohort,
       SUM(CASE WHEN e.user_id IS NOT NULL THEN 1 ELSE 0 END) AS d1_users,
       ROUND(SUM(CASE WHEN e.user_id IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS d1_rate
FROM users u
LEFT JOIN (SELECT DISTINCT user_id, event_date FROM events WHERE event_type = 'login') e
       ON e.user_id = u.user_id
      AND e.event_date = date(u.reg_date, '+1 day')
GROUP BY u.reg_date
ORDER BY u.reg_date;

-- @Q4 各注册日 cohort 的 7 日留存
SELECT u.reg_date,
       COUNT(*) AS cohort,
       SUM(CASE WHEN e.user_id IS NOT NULL THEN 1 ELSE 0 END) AS d7_users,
       ROUND(SUM(CASE WHEN e.user_id IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS d7_rate
FROM users u
LEFT JOIN (SELECT DISTINCT user_id, event_date FROM events WHERE event_type = 'login') e
       ON e.user_id = u.user_id
      AND e.event_date = date(u.reg_date, '+7 day')
GROUP BY u.reg_date
ORDER BY u.reg_date;

-- @Q5 整体付费率、ARPU、ARPPU
WITH p AS (
  SELECT user_id,
         SUM(CASE WHEN event_type = 'pay' THEN amount ELSE 0 END) AS amt,
         SUM(CASE WHEN event_type = 'pay' THEN 1 ELSE 0 END) AS cnt
  FROM events
  GROUP BY user_id
)
SELECT COUNT(*) AS users,
       SUM(CASE WHEN cnt > 0 THEN 1 ELSE 0 END) AS payers,
       ROUND(SUM(CASE WHEN cnt > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS pay_rate,
       ROUND(SUM(amt) / COUNT(*), 2) AS arpu,
       ROUND(SUM(amt) / NULLIF(SUM(CASE WHEN cnt > 0 THEN 1 ELSE 0 END), 0), 2) AS arppu
FROM p;

-- @Q6 新手漏斗：注册 → 首局 → 次日回访 → 首充
WITH f AS (
  SELECT u.user_id,
         u.reg_date,
         MIN(CASE WHEN e.event_type = 'battle' THEN e.event_date END) AS first_battle,
         MIN(CASE WHEN e.event_type = 'pay' THEN e.event_date END) AS first_pay,
         MAX(CASE WHEN e.event_type = 'login'
                   AND e.event_date = date(u.reg_date, '+1 day') THEN 1 ELSE 0 END) AS d1
  FROM users u
  LEFT JOIN events e ON e.user_id = u.user_id
  GROUP BY u.user_id, u.reg_date
)
SELECT COUNT(*) AS reg,
       SUM(CASE WHEN first_battle IS NOT NULL THEN 1 ELSE 0 END) AS battle,
       SUM(d1) AS d1_login,
       SUM(CASE WHEN first_pay IS NOT NULL THEN 1 ELSE 0 END) AS pay
FROM f;

-- @Q7 每日 DAU 环比（用于异动发现）
WITH d AS (
  SELECT event_date, COUNT(DISTINCT user_id) AS dau
  FROM events WHERE event_type = 'login'
  GROUP BY event_date
)
SELECT event_date,
       dau,
       LAG(dau) OVER (ORDER BY event_date) AS prev_dau,
       ROUND((dau * 1.0 / LAG(dau) OVER (ORDER BY event_date) - 1) * 100, 2) AS dod_pct
FROM d
ORDER BY event_date;

-- @Q8 异动日（10-18）前后各渠道新增拆解
SELECT reg_date,
       channel,
       COUNT(*) AS new_users
FROM users
WHERE reg_date IN ('2026-10-17', '2026-10-18', '2026-10-19')
GROUP BY reg_date, channel
ORDER BY reg_date, new_users DESC;

-- @Q9 渠道分群：用户规模、次留、付费率、ARPU
WITH d1 AS (SELECT DISTINCT user_id, event_date FROM events WHERE event_type = 'login'),
     pay AS (SELECT user_id, SUM(CASE WHEN event_type = 'pay' THEN amount ELSE 0 END) AS amt
             FROM events GROUP BY user_id)
SELECT u.channel,
       COUNT(*) AS users,
       ROUND(SUM(CASE WHEN d1.user_id IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS d1_rate,
       ROUND(SUM(CASE WHEN pay.amt > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS pay_rate,
       ROUND(SUM(COALESCE(pay.amt, 0)) / COUNT(*), 2) AS arpu
FROM users u
LEFT JOIN d1  ON d1.user_id = u.user_id AND d1.event_date = date(u.reg_date, '+1 day')
LEFT JOIN pay ON pay.user_id = u.user_id
GROUP BY u.channel
ORDER BY users DESC;

-- @Q10 新老用户 DAU 结构
SELECT e.event_date,
       CASE WHEN date(u.reg_date) = e.event_date THEN '新用户' ELSE '老用户' END AS seg,
       COUNT(DISTINCT e.user_id) AS dau
FROM events e
JOIN users u ON u.user_id = e.user_id
WHERE e.event_type = 'login'
GROUP BY e.event_date, seg
ORDER BY e.event_date;

-- @Q11 AB 组次留对比
WITH d1 AS (SELECT DISTINCT user_id, event_date FROM events WHERE event_type = 'login')
SELECT u.group_name,
       COUNT(*) AS users,
       SUM(CASE WHEN d1.user_id IS NOT NULL THEN 1 ELSE 0 END) AS retained_d1,
       ROUND(SUM(CASE WHEN d1.user_id IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS d1_rate
FROM users u
LEFT JOIN d1 ON d1.user_id = u.user_id AND d1.event_date = date(u.reg_date, '+1 day')
GROUP BY u.group_name;

-- @Q12 AB 组付费对比
WITH pay AS (SELECT user_id, SUM(CASE WHEN event_type = 'pay' THEN amount ELSE 0 END) AS amt
             FROM events GROUP BY user_id)
SELECT u.group_name,
       COUNT(*) AS users,
       SUM(CASE WHEN pay.amt > 0 THEN 1 ELSE 0 END) AS payers,
       ROUND(SUM(CASE WHEN pay.amt > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS pay_rate,
       ROUND(SUM(COALESCE(pay.amt, 0)) / COUNT(*), 2) AS arpu
FROM users u
LEFT JOIN pay ON pay.user_id = u.user_id
GROUP BY u.group_name;

-- @Q13 人均对局与送礼次数
SELECT event_type,
       COUNT(*) AS total_events,
       ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM users), 2) AS per_user
FROM events
WHERE event_type IN ('battle', 'gift')
GROUP BY event_type;

-- @Q14 留存衰减曲线（注册后第 0—14 天）
WITH pairs AS (
  SELECT u.user_id,
         CAST(julianday(e.event_date) - julianday(u.reg_date) AS INTEGER) AS d
  FROM users u
  JOIN events e ON e.user_id = u.user_id AND e.event_type = 'login'
),
elig AS (
  SELECT CAST(julianday('2026-11-10') - julianday(reg_date) AS INTEGER) AS max_d FROM users
)
SELECT p.d,
       COUNT(DISTINCT p.user_id) AS retained,
       (SELECT COUNT(*) FROM elig WHERE max_d >= p.d) AS eligible,
       ROUND(COUNT(DISTINCT p.user_id) * 1.0 /
             (SELECT COUNT(*) FROM elig WHERE max_d >= p.d), 4) AS rate
FROM pairs p
WHERE p.d BETWEEN 0 AND 14
GROUP BY p.d
ORDER BY p.d;

-- @Q15 AB 组每个用户的付费金额（用于 t 检验）
WITH pay AS (SELECT user_id, SUM(CASE WHEN event_type = 'pay' THEN amount ELSE 0 END) AS amt
             FROM events GROUP BY user_id)
SELECT u.group_name, u.user_id, COALESCE(pay.amt, 0) AS amount
FROM users u
LEFT JOIN pay ON pay.user_id = u.user_id;
