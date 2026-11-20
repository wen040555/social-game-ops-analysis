# -*- coding: utf-8 -*-
"""根据分析结果生成 Word 报告（随后导出 PDF）。"""
import os
import json
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
R = json.load(open(os.path.join(OUT, "results.json"), encoding="utf-8"))
channel = pd.read_csv(os.path.join(OUT, "sql_results", "Q9.csv"))

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x59, 0x63, 0x70)
HEAD = "微软雅黑"
BODY = "等线"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.0)
sec.top_margin = Cm(1.9)
sec.bottom_margin = Cm(1.8)

st = doc.styles["Normal"]
st.font.name = BODY
st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY)
st.paragraph_format.space_after = Pt(4)
st.paragraph_format.line_spacing = 1.4


def set_font(run, size=10, bold=False, color=DARK, font=BODY):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(k), font)


def para(text, size=10, bold=False, color=DARK, space_after=4, align=None, indent=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if align:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(indent)
    r = p.add_run(text)
    set_font(r, size, bold, color)
    return p


def heading(text, num=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    if num:
        r = p.add_run(num + "　")
        set_font(r, 12.5, True, ACCENT, HEAD)
    r = p.add_run(text)
    set_font(r, 12.5, True, ACCENT, HEAD)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), "C9D3DE")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def bullet(text, size=10):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.55)
    p.paragraph_format.first_line_indent = Cm(-0.55)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("▪  ")
    set_font(r, 8, True, ACCENT, HEAD)
    r = p.add_run(text)
    set_font(r, size, False, RGBColor(0x33, 0x33, 0x33))
    return p


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def table(headers, rows, widths=None, font_size=8.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        set_font(r, font_size, True, RGBColor(0xFF, 0xFF, 0xFF), HEAD)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(hdr[i], "1F4E79")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(v))
            set_font(r, font_size, False, RGBColor(0x33, 0x33, 0x33))
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(path, width=16.2, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(6)
    p.add_run().add_picture(path, width=Cm(width))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_after = Pt(8)
        r = c.add_run(caption)
        set_font(r, 8.5, False, GREY)


# ---------------- 封面标题 ----------------
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(2)
r = p.add_run("社交游戏运营数据分析报告")
set_font(r, 22, True, DARK, HEAD)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(10)
r = p.add_run("指标体系、转化漏斗与新手礼包 AB 实验")
set_font(r, 12, False, ACCENT, HEAD)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
r = p.add_run("林静雯　｜　2026 年 11 月　｜　数据分析作品集")
set_font(r, 9, False, GREY)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(12)
r = p.add_run("说明：本报告使用脚本模拟生成的用户与行为数据（5,000 名用户、15 万余条事件），"
              "用于演示指标体系、SQL 取数与 AB 实验方法，不代表任何真实产品或公司的业务数据。")
set_font(r, 8.5, False, GREY)

# ---------------- 一、项目概述 ----------------
heading("项目概述", "一")
para("本次分析以一款社交游戏为背景，模拟 5,000 名新用户从注册到首充的完整行为链路，目标是回答三个问题："
     "① 核心运营指标当前处于什么水平；② 新用户在哪一步流失最多；③ 新手礼包能否提升留存与付费。", indent=0.74)
para("数据由 gen_data.py 生成：用户注册时间为 2026-10-01 至 2026-10-30，行为事件覆盖登录、对局、送礼与付费四类，"
     "观察期至 2026-11-10。全流程在 SQLite 中完成，共 15 条 SQL 覆盖指标计算、分群拆解与实验对比。", indent=0.74)
bullet("数据规模：5,000 名用户、154,280 条行为事件，其中付费事件 418 笔")
bullet("核心工具：Python（pandas / numpy）生成与分析，SQLite + SQL 取数，matplotlib 可视化")

# ---------------- 二、指标体系 ----------------
heading("指标体系与 SQL 实现", "二")
para("所有指标均在 SQL 层完成计算，脚本按查询编号自动执行并落盘，便于复用到日报与看板。核心口径如下：", indent=0.74)
table(
    ["指标", "口径", "SQL"],
    [
        ["DAU", "当日有登录事件的去重用户数", "Q1"],
        ["新增用户", "当日注册的用户数", "Q2"],
        ["次日留存率", "注册次日有登录的 user_id / 当日注册 cohort", "Q3"],
        ["7 日留存率", "注册后第 7 天有登录的 user_id / cohort", "Q4"],
        ["付费率 / ARPU", "付费人数占注册用户比例；总付费金额 / 注册用户", "Q5"],
        ["新手漏斗", "注册 → 首局 → 次日回访 → 首充", "Q6"],
        ["DAU 环比", "当日 DAU 相对前一日的变化（窗口函数）", "Q7"],
        ["渠道分群", "按渠道拆用户数、次留、付费率、ARPU", "Q9"],
        ["留存曲线", "注册后第 0–14 天的留存衰减", "Q14"],
    ],
    widths=[3.2, 9.6, 2.2],
)

# ---------------- 三、核心指标 ----------------
heading("核心指标表现", "三")
para(f"观察期内 DAU 均值 {R['dau_avg']}，峰值 {R['dau_peak']}（{R['dau_peak_date']}）；"
     f"整体次日留存 {R['d1_rate']*100:.1f}%，7 日留存 {R['d7_rate']*100:.1f}%；"
     f"付费率 {R['pay']['pay_rate']*100:.1f}%，ARPU {R['pay']['arpu']:.2f} 元，ARPPU {R['pay']['arppu']:.2f} 元。", indent=0.74)
figure(os.path.join(OUT, "fig1_dau.png"), 16.2, "图 1　每日新增用户与 DAU")
figure(os.path.join(OUT, "fig2_retention.png"), 16.2, "图 2　新用户留存衰减曲线（D1 46.2%，D7 26.6%）")

f = R["funnel"]
para(f"漏斗显示，注册后有 {f['battle']/f['reg']*100:.1f}% 的用户完成首局，"
     f"但次日回访骤降至 {f['d1_login']/f['reg']*100:.1f}%，最终仅 {f['pay']/f['reg']*100:.1f}% 完成首充。"
     "流失主要发生在“首局到次日回访”这一段，说明首次对局体验与次日召回是优化重点。", indent=0.74)
figure(os.path.join(OUT, "fig3_funnel.png"), 16.2, "图 3　新手转化漏斗")

# ---------------- 四、渠道 ----------------
heading("渠道与用户分群", "四")
rows = []
for r_ in channel.itertuples():
    rows.append([r_.channel, f"{r_.users:,}", f"{r_.d1_rate*100:.1f}%", f"{r_.pay_rate*100:.1f}%", f"{r_.arpu:.2f}"])
table(["渠道", "用户数", "次日留存", "付费率", "ARPU（元）"], rows, widths=[3.4, 3.0, 3.2, 3.2, 3.0])
para("应用商店的次日留存最高（47.4%），但付费率偏低（7.1%）；老带新渠道规模最小，ARPU 与付费率处于中上水平，"
     "说明熟人推荐带来的用户质量不差，可通过激励把规模做起来。抖音渠道贡献了 34.6% 的用户，是拉新主力，"
     "但其付费率与 ARPU 并不突出，适合作为规模入口而非收入入口。", indent=0.74)

# ---------------- 五、AB 实验 ----------------
heading("新手礼包 AB 实验", "五")
ab = R["ab"]
para("实验设计：新用户注册时按 50/50 随机分入对照组与实验组（各 2,500 人），实验组在注册后立即发放新手礼包，"
     "对照组不发放。观察指标为次日留存、7 日留存、付费率与 ARPU，显著性水平 α=0.05，采用双侧检验。", indent=0.74)
table(
    ["指标", "对照组", "实验组", "差值", "95% CI", "p 值"],
    [
        ["次日留存", f"{ab['d1']['p1']*100:.2f}%", f"{ab['d1']['p2']*100:.2f}%",
         f"+{ab['d1']['diff_pp']:.2f} pp", f"[{ab['d1']['ci_low_pp']:.2f}, {ab['d1']['ci_high_pp']:.2f}]", f"{ab['d1']['p_value']:.4g}"],
        ["7 日留存", f"{ab['d7']['p1']*100:.2f}%", f"{ab['d7']['p2']*100:.2f}%",
         f"+{ab['d7']['diff_pp']:.2f} pp", f"[{ab['d7']['ci_low_pp']:.2f}, {ab['d7']['ci_high_pp']:.2f}]", f"{ab['d7']['p_value']:.4g}"],
        ["付费率", f"{ab['pay']['p1']*100:.2f}%", f"{ab['pay']['p2']*100:.2f}%",
         f"+{ab['pay']['diff_pp']:.2f} pp", f"[{ab['pay']['ci_low_pp']:.2f}, {ab['pay']['ci_high_pp']:.2f}]", f"{ab['pay']['p_value']:.4g}"],
        ["ARPU", f"{ab['arpu_ctrl']:.2f}", f"{ab['arpu_trt']:.2f}",
         f"+{ab['arpu_trt']-ab['arpu_ctrl']:.2f}", "—", f"{ab['t_p']:.4g}（t 检验）"],
    ],
    widths=[2.6, 2.6, 2.6, 2.6, 4.4, 3.4],
)
figure(os.path.join(OUT, "fig4_ab.png"), 16.2, "图 4　实验组与对照组核心指标对比（误差线为 95% 置信区间）")
para(f"三项比例指标的差异均显著：次日留存 +{ab['d1']['diff_pp']:.2f} pp（p={ab['d1']['p_value']:.4g}）、"
     f"7 日留存 +{ab['d7']['diff_pp']:.2f} pp（p={ab['d7']['p_value']:.4g}）、付费率 +{ab['pay']['diff_pp']:.2f} pp（p={ab['pay']['p_value']:.4g}）；"
     f"ARPU 由 {ab['arpu_ctrl']:.2f} 元提升至 {ab['arpu_trt']:.2f} 元（Welch t 检验 p={ab['t_p']:.4g}）。"
     "结论：新手礼包对留存与付费均有正向作用，可以进入灰度放量阶段。", indent=0.74)
para(f"样本量校验：若基线付费率为 8%、希望以 80% 功效检出 +2 pp 的提升，每组约需 {ab['required_n']:,} 人。"
     f"本次每组 2,500 人，对付费率这类大盘指标足够检出，但对更细的分层（如单渠道、单设备）偏少，"
     "后续实验建议按渠道分层扩量。", indent=0.74)

# ---------------- 六、异动排查 ----------------
heading("异动排查示例：10-18 新增骤降", "六")
para(f"10-18 新增用户 {R['dip']['new']} 人，较前一日 {R['dip']['new_prev']} 人下降 {abs(R['dip']['new_dod_pct']):.1f}%；"
     f"同日 DAU {R['dip']['dau']}，环比 {R['dip']['dau_dod_pct']:.1f}%。按排查顺序拆解如下：", indent=0.74)
bullet(f"第一步看总量：新增跌幅（-{abs(R['dip']['new_dod_pct']):.1f}%）远大于 DAU（{R['dip']['dau_dod_pct']:.1f}%），说明老用户留存稳定，问题出在获客端")
bullet(f"第二步拆渠道：抖音渠道新增由 53 降至 24（-54.7%），微信 -29.6%、应用商店 -10.0%、老带新 +33.3%，跌幅集中在抖音")
bullet("第三步看恢复：10-19 抖音新增回升至 64，判断为单日投放异常，而非账号或产品层面的持续问题")
para("处置建议：核对 10-18 的投放计划、预算消耗与素材审核状态，确认是否为预算提前耗尽或素材下架；"
     "同时把“新增环比 -20%”设为日报告警阈值，自动附带渠道拆解，减少人工排查时间。", indent=0.74)

# ---------------- 七、结论 ----------------
heading("结论与后续计划", "七")
bullet("新手礼包对留存与付费均显著正向，建议先对抖音、应用商店两个主力渠道灰度放量，观察 14 日留存与退款率")
bullet("漏斗瓶颈在“首局到次日回访”，建议针对首局失败/未完成用户做召回与难度调优，再配合礼包做二次触达")
bullet("渠道策略：应用商店适合做留存质量，老带新 ARPU 更高但规模小，可提高邀请奖励；抖音继续做规模入口")
bullet("后续：接入真实埋点与数数类工具，把 15 条 SQL 固化为日报模板；实验侧补充分层随机与序贯检验，避免多重比较")

# ---------------- 附录 ----------------
heading("附录：文件与复现方式", "八")
para("gen_data.py（生成数据）→ build_db.py（建库）→ run_analysis.py（执行 SQL、统计检验、出图）→ make_report.py（生成本报告）。"
     "SQL 全部集中在 metrics.sql，共 15 条查询，可直接复用到其他项目。", indent=0.74, size=9)

# 页脚
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = footer.add_run("社交游戏运营数据分析报告　·　林静雯　·　2026.11")
set_font(r, 8, False, GREY)

out_docx = os.path.join(ROOT, "社交游戏运营数据分析报告.docx")
doc.save(out_docx)
print("saved", out_docx)
