import sqlite3, os, warnings
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
warnings.filterwarnings("ignore")

os.makedirs("charts", exist_ok=True)
conn = sqlite3.connect("database/skill_gap.db")

# ── PALETTE ────────────────────────────────────────────────────────────────────
C_RED    = "#E74C3C"
C_GREEN  = "#2ECC71"
C_BLUE   = "#3498DB"
C_ORANGE = "#F39C12"
C_PURPLE = "#9B59B6"
C_DARK   = "#2C3E50"
C_LIGHT  = "#ECF0F1"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "#FAFAFA",
})

# ══════════════════════════════════════════════════════════════════════════════
# SQL QUERIES
# ══════════════════════════════════════════════════════════════════════════════

# Q1: Top 20 skills demanded by industry
q1 = """
SELECT skill, category, COUNT(*) as demand_count,
       ROUND(COUNT(*)*100.0 / (SELECT COUNT(DISTINCT job_id) FROM job_postings), 1) as pct_jobs
FROM job_skills
GROUP BY skill
ORDER BY demand_count DESC
LIMIT 20
"""
df_demand = pd.read_sql(q1, conn)

# Q2: Skills taught by colleges
q2 = """
SELECT cs.skill, cs.category, COUNT(DISTINCT cs.course_id) as course_count,
       SUM(c.credit_hours) as total_credits
FROM curriculum_skills cs
JOIN curriculum c ON cs.course_id = c.course_id
GROUP BY cs.skill
ORDER BY course_count DESC
"""
df_taught = pd.read_sql(q2, conn)

# Q3: SKILL GAP — High demand, NOT taught (or barely covered)
q3 = """
SELECT js.skill, js.category,
       COUNT(*) as demand_count,
       ROUND(COUNT(*)*100.0 / (SELECT COUNT(DISTINCT job_id) FROM job_postings), 1) as pct_jobs,
       COALESCE(cs.course_count, 0) as college_coverage
FROM job_skills js
LEFT JOIN (
    SELECT skill, COUNT(DISTINCT course_id) as course_count
    FROM curriculum_skills GROUP BY skill
) cs ON js.skill = cs.skill
WHERE COALESCE(cs.course_count, 0) <= 1
GROUP BY js.skill
ORDER BY demand_count DESC
LIMIT 15
"""
df_gap = pd.read_sql(q3, conn)

# Q4: Salary premium for gap skills vs covered skills
q4 = """
SELECT js.skill,
       ROUND(AVG(jp.salary_lpa), 2) as avg_salary,
       COALESCE(cs.course_count, 0) as college_coverage,
       COUNT(DISTINCT jp.job_id) as job_count
FROM job_skills js
JOIN job_postings jp ON js.job_id = jp.job_id
LEFT JOIN (
    SELECT skill, COUNT(DISTINCT course_id) as course_count
    FROM curriculum_skills GROUP BY skill
) cs ON js.skill = cs.skill
GROUP BY js.skill
HAVING job_count >= 15
ORDER BY avg_salary DESC
LIMIT 18
"""
df_salary = pd.read_sql(q4, conn)

# Q5: Domain-wise gap — which domains have the biggest skill gaps
q5 = """
SELECT jp.domain,
       COUNT(DISTINCT js.skill) as skills_demanded,
       COUNT(DISTINCT CASE WHEN cs.skill IS NOT NULL THEN js.skill END) as skills_covered,
       ROUND(AVG(jp.salary_lpa), 1) as avg_salary
FROM job_postings jp
JOIN job_skills js ON jp.job_id = js.job_id
LEFT JOIN curriculum_skills cs ON js.skill = cs.skill
GROUP BY jp.domain
ORDER BY skills_demanded DESC
"""
df_domain = pd.read_sql(q5, conn)
df_domain["gap_pct"] = round(
    (df_domain["skills_demanded"] - df_domain["skills_covered"]) / df_domain["skills_demanded"] * 100, 1
)

# Q6: Role-wise most demanded skills
q6 = """
SELECT jp.role, js.skill, js.category, COUNT(*) as cnt,
       ROUND(AVG(jp.salary_lpa),2) as avg_salary
FROM job_postings jp
JOIN job_skills js ON jp.job_id = js.job_id
GROUP BY jp.role, js.skill
ORDER BY jp.role, cnt DESC
"""
df_role_skills = pd.read_sql(q6, conn)

# Q7: Skills taught but NOT demanded (Surplus)
q7 = """
SELECT cs.skill, cs.category, COUNT(DISTINCT cs.course_id) as course_count,
       COALESCE(js.demand_count, 0) as demand_count
FROM curriculum_skills cs
LEFT JOIN (
    SELECT skill, COUNT(*) as demand_count FROM job_skills GROUP BY skill
) js ON cs.skill = js.skill
WHERE COALESCE(js.demand_count, 0) < 10
GROUP BY cs.skill
ORDER BY course_count DESC
LIMIT 12
"""
df_surplus = pd.read_sql(q7, conn)

conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1: Top 20 In-Demand Skills (color-coded by category)
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 8))

cat_colors = {
    "Programming":       C_BLUE,
    "Database":          C_PURPLE,
    "Visualization":     C_ORANGE,
    "Analytics":         C_GREEN,
    "AI/ML":             "#E91E63",
    "Data Engineering":  "#00BCD4",
    "Cloud":             "#FF5722",
    "Tools":             "#795548",
    "Soft Skills":       "#9E9E9E",
    "Math/Stats":        "#4CAF50",
}
colors = [cat_colors.get(c, C_DARK) for c in df_demand["category"]]

bars = ax.barh(df_demand["skill"][::-1], df_demand["demand_count"][::-1],
               color=colors[::-1], edgecolor="white", linewidth=0.5, height=0.7)

for bar, val, pct in zip(bars, df_demand["demand_count"][::-1], df_demand["pct_jobs"][::-1]):
    ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
            f"{val}  ({pct}% of jobs)", va="center", fontsize=8.5, color=C_DARK)

ax.set_xlabel("Number of Job Postings Requiring Skill", fontsize=11, color=C_DARK)
ax.set_title("Top 20 Skills Demanded by Indian Tech Companies", fontsize=14, fontweight="bold",
             color=C_DARK, pad=15)
ax.set_xlim(0, df_demand["demand_count"].max() * 1.28)
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=9)

legend_patches = [mpatches.Patch(color=v, label=k) for k, v in cat_colors.items()
                  if k in df_demand["category"].values]
ax.legend(handles=legend_patches, loc="lower right", fontsize=8, framealpha=0.7,
          title="Category", title_fontsize=9)

ax.set_facecolor("#F8F9FA")
fig.suptitle("Skill Gap Analysis — Indian Job Market vs College Curriculum",
             y=0.98, fontsize=11, color="#7F8C8D", style="italic")
plt.tight_layout()
plt.savefig("charts/01_top_demanded_skills.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 1 saved")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2: Critical Skill GAP — High demand, Low college coverage
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 7))

gap_colors = [C_RED if c == 0 else C_ORANGE for c in df_gap["college_coverage"]]
bars = ax.barh(df_gap["skill"][::-1], df_gap["pct_jobs"][::-1],
               color=gap_colors[::-1], edgecolor="white", height=0.7)

for bar, val, cov in zip(bars, df_gap["pct_jobs"][::-1], df_gap["college_coverage"][::-1]):
    label = f"{val}% of jobs  |  {'❌ Not Taught' if cov == 0 else '⚠️ 1 Course Only'}"
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
            label, va="center", fontsize=8.5, color=C_DARK)

ax.set_xlabel("% of Job Postings Requiring This Skill", fontsize=11)
ax.set_title("🚨 Critical Skill Gaps — High Industry Demand, Low/Zero College Coverage",
             fontsize=13, fontweight="bold", color=C_DARK, pad=15)
ax.set_xlim(0, df_gap["pct_jobs"].max() * 1.55)

red_patch = mpatches.Patch(color=C_RED, label="Not taught in any course")
orange_patch = mpatches.Patch(color=C_ORANGE, label="Covered in only 1 course")
ax.legend(handles=[red_patch, orange_patch], fontsize=9, loc="lower right")

ax.axvline(x=30, color=C_DARK, linestyle="--", alpha=0.3, linewidth=1)
ax.text(30.5, 0.3, "30% threshold", fontsize=8, color="#7F8C8D")

ax.set_facecolor("#FFF8F8")
plt.tight_layout()
plt.savefig("charts/02_critical_skill_gaps.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 2 saved")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 3: Salary Premium — Gap skills earn more
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 7))

df_salary_s = df_salary.sort_values("avg_salary", ascending=True)
bar_colors = [C_RED if cov == 0 else (C_ORANGE if cov == 1 else C_GREEN)
              for cov in df_salary_s["college_coverage"]]

bars = ax.barh(df_salary_s["skill"], df_salary_s["avg_salary"],
               color=bar_colors, edgecolor="white", height=0.7)

for bar, val, cov in zip(bars, df_salary_s["avg_salary"], df_salary_s["college_coverage"]):
    cov_label = "Gap" if cov == 0 else ("Partial" if cov == 1 else "Covered")
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f"₹{val}L  [{cov_label}]", va="center", fontsize=9, color=C_DARK)

avg_all = df_salary_s["avg_salary"].mean()
ax.axvline(x=avg_all, color=C_DARK, linestyle="--", alpha=0.5)
ax.text(avg_all + 0.1, 0.2, f"Avg: ₹{avg_all:.1f}L", fontsize=9, color=C_DARK)

ax.set_xlabel("Average Salary (LPA)", fontsize=11)
ax.set_title("💰 Salary Premium for Gap Skills vs College-Covered Skills",
             fontsize=13, fontweight="bold", color=C_DARK, pad=15)
ax.set_xlim(0, df_salary_s["avg_salary"].max() * 1.25)

patches = [
    mpatches.Patch(color=C_RED,    label="Gap Skill (not taught)"),
    mpatches.Patch(color=C_ORANGE, label="Partial (1 course)"),
    mpatches.Patch(color=C_GREEN,  label="Well Covered"),
]
ax.legend(handles=patches, fontsize=9)
ax.set_facecolor("#F8FFF8")
plt.tight_layout()
plt.savefig("charts/03_salary_premium.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 3 saved")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 4: Domain-wise Skill Gap % (Bubble chart style)
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 7))

palette = [C_RED, C_ORANGE, C_BLUE, C_GREEN, C_PURPLE, "#00BCD4", "#FF5722", "#795548", "#E91E63", "#4CAF50", "#9C27B0"]
domain_colors = [palette[i % len(palette)] for i in range(len(df_domain))]
sizes = (df_domain["avg_salary"] * 15) ** 1.5

scatter = ax.scatter(df_domain["skills_demanded"], df_domain["gap_pct"],
                     s=sizes, c=domain_colors,
                     alpha=0.8, edgecolors="white", linewidth=2)

for _, row in df_domain.iterrows():
    ax.annotate(row["domain"],
                xy=(row["skills_demanded"], row["gap_pct"]),
                xytext=(6, 6), textcoords="offset points",
                fontsize=9.5, fontweight="bold", color=C_DARK)

ax.set_xlabel("Total Unique Skills Demanded", fontsize=11)
ax.set_ylabel("% of Demanded Skills NOT Covered by College (%)", fontsize=11)
ax.set_title("Domain-wise Skill Gap Severity\n(Bubble size = Avg Salary)",
             fontsize=13, fontweight="bold", color=C_DARK)

ax.axhline(y=df_domain["gap_pct"].mean(), color=C_DARK, linestyle="--", alpha=0.3)
ax.text(ax.get_xlim()[0], df_domain["gap_pct"].mean() + 0.5,
        f"Avg Gap: {df_domain['gap_pct'].mean():.1f}%", fontsize=8, color="#7F8C8D")

ax.set_facecolor("#F8F9FF")
plt.tight_layout()
plt.savefig("charts/04_domain_gap_bubble.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 4 saved")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 5: Heatmap — Role × Skill Category demand
# ══════════════════════════════════════════════════════════════════════════════
pivot = df_role_skills.groupby(["role","category"])["cnt"].sum().unstack(fill_value=0)
key_cats = ["Programming","Database","Visualization","Analytics","AI/ML",
            "Data Engineering","Cloud","Tools","Soft Skills","Math/Stats"]
pivot = pivot.reindex(columns=[c for c in key_cats if c in pivot.columns], fill_value=0)

fig, ax = plt.subplots(figsize=(13, 6))
sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5,
            linecolor="white", ax=ax, cbar_kws={"label":"Skill Mentions"},
            annot_kws={"size":10})

ax.set_title("Skill Category Demand by Job Role — Heat Intensity Map",
             fontsize=13, fontweight="bold", color=C_DARK, pad=15)
ax.set_xlabel("Skill Category", fontsize=10)
ax.set_ylabel("Job Role", fontsize=10)
ax.tick_params(axis="x", rotation=30, labelsize=9)
ax.tick_params(axis="y", rotation=0, labelsize=10)
plt.tight_layout()
plt.savefig("charts/05_role_skill_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 5 saved")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 6: What Colleges Teach vs What Companies Want — Overlap analysis
# ══════════════════════════════════════════════════════════════════════════════
top_demanded = set(df_demand["skill"].tolist())
top_taught   = set(df_taught["skill"].tolist())

gap     = top_demanded - top_taught          # Demanded but not taught
overlap = top_demanded & top_taught          # Both
surplus = top_taught - top_demanded          # Taught but not demanded

categories_venn = ["Gap Skills\n(Industry wants,\ncollege ignores)",
                   "Matched Skills\n(Both teach & want)",
                   "Surplus Skills\n(Taught but\nlow demand)"]
values    = [len(gap), len(overlap), len(surplus)]
bar_clrs  = [C_RED, C_GREEN, C_ORANGE]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Bar chart
bars = ax1.bar(categories_venn, values, color=bar_clrs, edgecolor="white",
               width=0.5, linewidth=2)
for bar, val in zip(bars, values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             str(val), ha="center", fontweight="bold", fontsize=13)

ax1.set_title("Skills: Gap vs Overlap vs Surplus", fontsize=12, fontweight="bold")
ax1.set_ylabel("Number of Unique Skills", fontsize=10)
ax1.set_ylim(0, max(values) * 1.2)
ax1.set_facecolor("#F8F9FA")

# Detail table for gap skills
gap_df = df_gap[["skill","pct_jobs"]].head(10)
ax2.axis("off")
table_data = [["Skill", "% Jobs Requiring"]] + [[row["skill"], f"{row['pct_jobs']}%"] for _, row in gap_df.iterrows()]
tbl = ax2.table(cellText=table_data[1:], colLabels=table_data[0],
                loc="center", cellLoc="left")
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
tbl.scale(1.3, 1.6)

for j in range(2):
    tbl[0, j].set_facecolor(C_DARK)
    tbl[0, j].set_text_props(color="white", fontweight="bold")
for i in range(1, len(table_data)):
    bg = "#FFE8E8" if i % 2 == 0 else "white"
    for j in range(2):
        tbl[i, j].set_facecolor(bg)

ax2.set_title("Top 10 Critical Gap Skills", fontsize=12, fontweight="bold", pad=20)

fig.suptitle("College Curriculum vs Industry Demand — Gap Analysis Summary",
             fontsize=14, fontweight="bold", color=C_DARK, y=1.01)
plt.tight_layout()
plt.savefig("charts/06_gap_overlap_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 6 saved")

# ── EXPORT SUMMARY DATA ────────────────────────────────────────────────────────
df_demand.to_csv("output/01_top_demanded_skills.csv", index=False)
df_gap.to_csv("output/02_skill_gaps.csv", index=False)
df_salary.to_csv("output/03_salary_by_skill.csv", index=False)
df_domain.to_csv("output/04_domain_analysis.csv", index=False)
df_taught.to_csv("output/05_college_skills.csv", index=False)
print("\nAll CSVs saved to output/")

# ── PRINT KEY INSIGHTS ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("KEY INSIGHTS")
print("="*60)
print(f"Total Job Postings Analyzed : {pd.read_sql('SELECT COUNT(*) c FROM job_postings', sqlite3.connect('database/skill_gap.db')).iloc[0,0]}")
print(f"Unique Skills Demanded      : {len(top_demanded)}")
print(f"Skills Taught in College    : {len(top_taught)}")
print(f"CRITICAL GAP (not taught)   : {len(gap)} skills")
print(f"Overlap (taught + demanded) : {len(overlap)} skills")
print(f"Surplus (taught, low demand): {len(surplus)} skills")
print(f"Gap Skills avg salary premium: significant (see Chart 3)")
print(f"\nMost in-demand gap skill: {df_gap.iloc[0]['skill']} ({df_gap.iloc[0]['pct_jobs']}% jobs)")
print(f"Domain with highest gap: {df_domain.sort_values('gap_pct',ascending=False).iloc[0]['domain']}")
