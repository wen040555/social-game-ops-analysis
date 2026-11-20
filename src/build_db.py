# -*- coding: utf-8 -*-
"""把 CSV 数据导入 SQLite，建立索引。"""
import os
import sqlite3
import pandas as pd

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(root, "data", "game.db")
users = pd.read_csv(os.path.join(root, "data", "users.csv"))
events = pd.read_csv(os.path.join(root, "data", "events.csv"))

if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
users.to_sql("users", con, index=False)
events.to_sql("events", con, index=False)
cur = con.cursor()
cur.execute("CREATE INDEX idx_events_user ON events(user_id)")
cur.execute("CREATE INDEX idx_events_date ON events(event_date, event_type)")
cur.execute("CREATE INDEX idx_users_reg ON users(reg_date)")
con.commit()
con.close()
print("数据库已生成：", db_path)
