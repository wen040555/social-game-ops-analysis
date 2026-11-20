# -*- coding: utf-8 -*-
"""
执行 SQL 指标、计算 AB 实验结果、生成图表。
输出：output/*.png、output/results.json、output/sql_results/*.csv
"""
import os
import re
import json
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "game.db")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "sql_results"), exist_ok=True)

ACCENT = "#1F4E79"
LIGHT = "#7FA7C9"
GREY = "#C9D3DE"
ORANGE = "#C0703F"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

con = sqlite3.connect(DB)

# ---------- 读取并执行 metrics.sql ----------
sql_text = open(os.path.join(ROOT, "src", "metrics.sql"), encoding="utf-8").read()
pattern = re.compile(r"^--\s*@(Q\d+)\s+(.+)$", re.M)
matches = list(pattern.finditer(sql_text))
queries = {}
for i, m in enumerate(matches):
    qid = m.group(1)
    title = m.group(2).strip()
    body_start = m.end()
    body_end = matches[i + 1].start() if i + 1 < len(matches) else len(sql_text)
    sql = sql_text[body_start:body_end].strip().rstrip(";")
    queries[qid] = (title, sql)

results = {}
for qid, (title, sql) in queries.items():
    df = pd.read_sql_query(sql, con)
    results[qid] = df
    df.to_csv(os.path.join(OUT, "sql_results", f"{qid}.csv"), index=False, encoding="utf-8-sig")

dau = results["Q1"]
newu = results["Q2"]
d1 = results["Q3"]
d7 = results["Q4"]
pay = results["Q5"].iloc[0]
funnel = results["Q6"].iloc[0]
dod = results["Q7"]
dip = results["Q8"]
channel = results["Q9"]
retention = results["Q14"]
ab_d1 = results["Q11"]
ab_pay = results["Q12"]
ab_amt = results["Q15"]

# ---------- AB 统计 ----------
def prop_test(x1, n1, x2, n2, alpha=0.05):
    p1, p2 = x1 / n1, x2 / n2
    diff = p2 - p1
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z = diff / se
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    zc = stats.norm.ppf(1 - alpha / 2)
    return {
        "p1": round(p1, 4), "p2": round(p2, 4),
        "diff_pp": round(diff * 100, 2),
        "ci_low_pp": round((diff - zc * se) * 100, 2),
        "ci_high_pp": round((diff + zc * se) * 100, 2),
        "z": round(float(z), 3), "p_value": float(f"{pval:.4g}"),
    }

ctrl = ab_d1[ab_d1.group_name == "对照组"].iloc[0]
trt = ab_d1[ab_d1.group_name == "实验组"].iloc[0]
ab_d1_stat = prop_test(ctrl.retained_d1, ctrl.users, trt.retained_d1, trt.users)

d7_q = pd.read_sql_query("""
WITH d7 AS (SELECT DISTINCT user_id, event_date FROM events WHERE event_type = 'login')
SELECT u.group_name, COUNT(*) AS users,
       SUM(CASE WHEN d7.user_id IS NOT NULL THEN 1 ELSE 0 END) AS retained_d7
FROM users u
LEFT JOIN d7 ON d7.user_id = u.user_id AND d7.event_date = date(u.reg_date, '+7 day')
GROUP BY u.group_name
""", con)
c7 = d7_q[d7_q.group_name == "对照组"].iloc[0]
t7 = d7_q[d7_q.group_name == "实验组"].iloc[0]
ab_d7_stat = prop_test(c7.retained_d7, c7.users, t7.retained_d7, t7.users)

cp = ab_pay[ab_pay.group_name == "对照组"].iloc[0]
tp = ab_pay[ab_pay.group_name == "实验组"].iloc[0]
ab_pay_stat = prop_test(cp.payers, cp.users, tp.payers, tp.users)

# 卡方检验（次留 2×2）
table = np.array([[ctrl.retained_d1, ctrl.users - ctrl.retained_d1],
                  [trt.retained_d1, trt.users - trt.retained_d1]])
chi2, chi_p, dof, _ = stats.chi2_contingency(table)

# ARPU 的 Welch t 检验
a_ctrl = ab_amt[ab_amt.group_name == "对照组"].amount
a_trt = ab_amt[ab_amt.group_name == "实验组"].amount
t_stat, t_p = stats.ttest_ind(a_trt, a_ctrl, equal_var=False)

# 样本量估算：基线付费率 8%，希望检出 +2pp，α=0.05，power=0.8
p1_base, p2_base = 0.08, 0.10
z_a, z_b = stats.norm.ppf(0.975), stats.norm.ppf(0.8)
n_req = ((z_a + z_b) ** 2 * (p1_base * (1 - p1_base) + p2_base * (1 - p2_base))) / (p2_base - p1_base) ** 2

# ---------- 图表 ----------
def style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GREY, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8.5, colors="#333333")

# 图1 DAU 与新增
fig, ax1 = plt.subplots(figsize=(7.6, 3.0), dpi=200)
ax1.bar(pd.to_datetime(newu.reg_date), newu.new_users, color=GREY, width=0.8, label="新增用户")
ax1.set_ylabel("新增用户数", fontsize=9)
ax1.set_ylim(0, newu.new_users.max() * 2.2)
ax2 = ax1.twinx()
ax2.plot(pd.to_datetime(dau.event_date), dau.dau, color=ACCENT, linewidth=2, marker="o", markersize=2.5, label="DAU")
ax2.set_ylabel("DAU", fontsize=9)
for a in (ax1, ax2):
    style(a)
ax1.set_title("每日新增用户与 DAU", fontsize=11, color="#1A1A1A", pad=8)
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, loc="upper left")
fig.autofmt_xdate(rotation=0)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_dau.png"), bbox_inches="tight")
plt.close(fig)

# 图2 留存曲线
fig, ax = plt.subplots(figsize=(7.6, 2.9), dpi=200)
ax.plot(retention.d, retention.rate * 100, color=ACCENT, marker="o", markersize=3.5, linewidth=2)
for d in (1, 7):
    row = retention[retention.d == d].iloc[0]
    ax.annotate(f"D{d}：{row.rate * 100:.1f}%", (row.d, row.rate * 100),
                textcoords="offset points", xytext=(6, 8), fontsize=8.5, color=ACCENT)
ax.set_xlabel("注册后第 N 天", fontsize=9)
ax.set_ylabel("留存率（%）", fontsize=9)
ax.set_xticks(range(0, 15))
style(ax)
ax.set_title("新用户留存衰减曲线", fontsize=11, pad=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_retention.png"), bbox_inches="tight")
plt.close(fig)

# 图3 新手漏斗
steps = [("注册", int(funnel.reg)), ("完成首局", int(funnel.battle)),
         ("次日回访", int(funnel.d1_login)), ("完成首充", int(funnel.pay))]
fig, ax = plt.subplots(figsize=(7.6, 2.6), dpi=200)
labels = [s[0] for s in steps][::-1]
vals = [s[1] for s in steps][::-1]
base = steps[0][1]
bars = ax.barh(labels, vals, color=[LIGHT, LIGHT, LIGHT, ACCENT], height=0.55)
for b, v in zip(bars, vals):
    ax.text(v + base * 0.01, b.get_y() + b.get_height() / 2, f"{v:,}（{v / base * 100:.1f}%）",
            va="center", fontsize=8.5, color="#333333")
ax.set_xlim(0, base * 1.25)
ax.set_xlabel("用户数", fontsize=9)
style(ax)
ax.grid(axis="x", color=GREY, linewidth=0.6, alpha=0.6)
ax.grid(axis="y", visible=False)
ax.set_title("新手转化漏斗", fontsize=11, pad=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_funnel.png"), bbox_inches="tight")
plt.close(fig)

# 图4 AB 实验对比
metrics = ["次日留存", "7 日留存", "付费率"]
c_vals = [ctrl.retained_d1 / ctrl.users * 100, c7.retained_d7 / c7.users * 100, cp.pay_rate * 100]
t_vals = [trt.retained_d1 / trt.users * 100, t7.retained_d7 / t7.users * 100, tp.pay_rate * 100]
c_err = [1.96 * np.sqrt(p * (1 - p) / ctrl.users) * 100 for p in np.array(c_vals) / 100]
t_err = [1.96 * np.sqrt(p * (1 - p) / trt.users) * 100 for p in np.array(t_vals) / 100]
x = np.arange(len(metrics))
w = 0.34
fig, ax = plt.subplots(figsize=(7.6, 2.9), dpi=200)
b1 = ax.bar(x - w / 2, c_vals, w, color=GREY, label="对照组", yerr=c_err, capsize=3, error_kw={"ecolor": "#888888", "lw": 0.8})
b2 = ax.bar(x + w / 2, t_vals, w, color=ACCENT, label="实验组", yerr=t_err, capsize=3, error_kw={"ecolor": "#888888", "lw": 0.8})
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2, f"{b.get_height():.1f}%",
                ha="center", fontsize=8.5, color="#333333")
ax.set_xticks(x, metrics, fontsize=9)
ax.set_ylabel("%", fontsize=9)
ax.set_ylim(0, max(c_vals + t_vals) * 1.35)
style(ax)
ax.legend(fontsize=8.5, frameon=False, loc="upper right")
ax.set_title("新手礼包 AB 实验：核心指标对比（95% 置信区间）", fontsize=11, pad=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_ab.png"), bbox_inches="tight")
plt.close(fig)

# 图5 渠道对比
fig, ax = plt.subplots(figsize=(7.6, 2.7), dpi=200)
xx = np.arange(len(channel))
b1 = ax.bar(xx - 0.19, channel.d1_rate * 100, 0.36, color=LIGHT, label="次日留存率")
b2 = ax.bar(xx + 0.19, channel.pay_rate * 100, 0.36, color=ACCENT, label="付费率")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"{b.get_height():.1f}%",
                ha="center", fontsize=8, color="#333333")
ax.set_xticks(xx, channel.channel, fontsize=9)
ax.set_ylabel("%", fontsize=9)
ax.set_ylim(0, max(channel.d1_rate.max(), channel.pay_rate.max()) * 100 * 1.35)
style(ax)
ax.legend(fontsize=8.5, frameon=False, loc="upper right")
ax.set_title("各渠道次留与付费率", fontsize=11, pad=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig5_channel.png"), bbox_inches="tight")
plt.close(fig)

# ---------- 汇总结果 ----------
summary = {
    "users": int(len(pd.read_sql_query("SELECT * FROM users", con))),
    "events": int(len(pd.read_sql_query("SELECT * FROM events", con))),
    "date_range": [str(dau.event_date.min()), str(dau.event_date.max())],
    "dau_peak": int(dau.dau.max()),
    "dau_peak_date": str(dau.loc[dau.dau.idxmax(), "event_date"]),
    "dau_avg": round(float(dau.dau.mean()), 1),
    "pay": {"payers": int(pay.payers), "pay_rate": float(pay.pay_rate),
            "arpu": float(pay.arpu), "arppu": float(pay.arppu)},
    "d1_rate": round(float(d1.d1_rate.mean()), 4),
    "d7_rate": round(float(d7.d7_rate.mean()), 4),
    "funnel": {"reg": int(funnel.reg), "battle": int(funnel.battle),
               "d1_login": int(funnel.d1_login), "pay": int(funnel.pay)},
    "dip": {
        "date": "2026-10-18",
        "new_prev": int(newu[newu.reg_date == "2026-10-17"].new_users.iloc[0]),
        "new": int(newu[newu.reg_date == "2026-10-18"].new_users.iloc[0]),
        "new_dod_pct": round((newu[newu.reg_date == "2026-10-18"].new_users.iloc[0] /
                               newu[newu.reg_date == "2026-10-17"].new_users.iloc[0] - 1) * 100, 2),
        "dau_prev": int(dod[dod.event_date == "2026-10-17"].dau.iloc[0]),
        "dau": int(dod[dod.event_date == "2026-10-18"].dau.iloc[0]),
        "dau_dod_pct": float(dod[dod.event_date == "2026-10-18"].dod_pct.iloc[0]),
    },
    "channel": channel.to_dict(orient="records"),
    "ab": {
        "d1": ab_d1_stat, "d7": ab_d7_stat, "pay": ab_pay_stat,
        "chi2": round(float(chi2), 3), "chi2_p": float(f"{chi_p:.4g}"),
        "arpu_ctrl": round(float(a_ctrl.mean()), 2), "arpu_trt": round(float(a_trt.mean()), 2),
        "t_stat": round(float(t_stat), 3), "t_p": float(f"{t_p:.4g}"),
        "n_per_group": int(ctrl.users), "required_n": int(np.ceil(n_req)),
    },
}
json.dump(summary, open(os.path.join(OUT, "results.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2)[:2000])
