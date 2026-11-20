# -*- coding: utf-8 -*-
"""
社交游戏运营数据 —— 模拟数据生成
说明：本脚本生成的用户与行为数据均为模拟，用于演示指标体系、SQL 取数与 AB 实验分析，
     不对应任何真实公司或产品。
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta
import os

rng = np.random.default_rng(42)

N_USERS = 5000
START = date(2026, 10, 1)          # 最早注册日
REG_DAYS = 30                       # 注册窗口 30 天
OBSERVE_END = date(2026, 11, 10)    # 观察截止日（保证后期用户有 7 天以上观察期）
DIP_DATE = date(2026, 10, 18)       # 人为制造一次渠道投放波动，用于“异动排查”演示
DIP_CHANNEL = "抖音"

CHANNELS = ["抖音", "微信", "应用商店", "老带新"]
CHANNEL_P = [0.35, 0.30, 0.25, 0.10]
DEVICES = ["Android", "iOS"]
DEVICE_P = [0.62, 0.38]

rows_users = []
attempts = 0
while len(rows_users) < N_USERS and attempts < N_USERS * 3:
    attempts += 1
    d = START + timedelta(days=int(rng.integers(0, REG_DAYS)))
    ch = rng.choice(CHANNELS, p=CHANNEL_P)
    # 投放波动：10-18 抖音渠道新增下降约 60%
    if d == DIP_DATE and ch == DIP_CHANNEL and rng.random() < 0.60:
        continue
    rows_users.append({
        "user_id": len(rows_users) + 1,
        "reg_date": d.isoformat(),
        "channel": ch,
        "device": rng.choice(DEVICES, p=DEVICE_P),
        "propensity": float(rng.beta(1.6, 3.0)),   # 潜在外向/活跃度，越小越沉默
    })

users = pd.DataFrame(rows_users)

# 50/50 随机分组（AB 实验：新手礼包）
order = rng.permutation(len(users))
users["group_name"] = "对照组"
users.loc[order[: len(users) // 2], "group_name"] = "实验组"

events = []
for u in users.itertuples(index=False):
    reg = date.fromisoformat(u.reg_date)
    max_d = (OBSERVE_END - reg).days
    p0 = 0.36 + 0.30 * u.propensity
    pay_daily = 0.004 + 0.025 * u.propensity
    plays = rng.random() < (0.82 + 0.12 * u.propensity)
    for d in range(max_d + 1):
        if d == 0:
            active = True
        else:
            p = p0 * np.exp(-d / 10.0) + 0.015
            if u.group_name == "实验组":
                p *= 1.12          # 新手礼包提升回访
            active = rng.random() < min(p, 0.95)
        if not active:
            continue
        day = (reg + timedelta(days=d)).isoformat()
        events.append((u.user_id, day, "login", 0.0))
        # 对局（部分用户当天不参与对局，形成漏斗）
        if plays:
            for _ in range(int(rng.poisson(2 + 5 * u.propensity))):
                events.append((u.user_id, day, "battle", 0.0))
        # 送礼（社交行为）
        for _ in range(int(rng.poisson(0.4 + 2 * u.propensity))):
            events.append((u.user_id, day, "gift", 0.0))
        # 付费
        pp = pay_daily * (1.35 if u.group_name == "实验组" else 1.0)
        if rng.random() < pp:
            amt = float(min(648, max(6, rng.lognormal(mean=np.log(30), sigma=0.8))))
            events.append((u.user_id, day, "pay", round(amt, 2)))

events = pd.DataFrame(events, columns=["user_id", "event_date", "event_type", "amount"])

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(root, "data"), exist_ok=True)
users.drop(columns=["propensity"]).to_csv(os.path.join(root, "data", "users.csv"), index=False, encoding="utf-8-sig")
events.to_csv(os.path.join(root, "data", "events.csv"), index=False, encoding="utf-8-sig")

print("用户数：", len(users))
print("事件数：", len(events))
print("付费事件：", (events.event_type == "pay").sum())
print("人均活跃天数：", round(events[events.event_type == "login"].groupby("user_id").size().mean(), 2))
