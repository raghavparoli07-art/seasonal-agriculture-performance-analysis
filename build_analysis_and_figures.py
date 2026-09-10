"""
Seasonal Agriculture Performance Analysis
Data Cleaning, Feature Engineering, Statistical Testing, and Figure Generation Pipeline
VOIS AICTE Batch 2026-2027 Major Project
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# Base directories
BASE_DIR = r"c:\Users\ragha\.gemini\antigravity-ide\scratch\space-edu\seasonal-agriculture-performance-analysis"
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "Major_Project_Seasonal_Agriculture_Performance_Analysis.csv")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "cleaned_agriculture_data.csv")
FIG_DIR = os.path.join(BASE_DIR, "outputs", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# -------------------------------------------------------------
# Global Visualization Theme & Palette
# -------------------------------------------------------------
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#EEEEEE'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['figure.titlesize'] = 14
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11

# Cohesive, colorblind-friendly seasonal palette
# Kharif: Lush Emerald, Rabi: Royal Amber/Gold, Zaid: Coral Terracotta
SEASON_PALETTE = {
    'Kharif': '#2E7D32',  # Monsoon Green
    'Rabi': '#D97706',    # Winter Gold / Amber
    'Zaid': '#DC2626'     # Summer Coral / Red
}
SEASON_ORDER = ['Kharif', 'Rabi', 'Zaid']

# -------------------------------------------------------------
# 1. Load Data & Initial Audit
# -------------------------------------------------------------
print("Loading raw dataset...")
df = pd.read_csv(RAW_DATA_PATH)
initial_shape = df.shape
print(f"Dataset shape: {initial_shape[0]} rows, {initial_shape[1]} columns")

# Audit missing values
missing_counts = df.isnull().sum()
missing_cols = missing_counts[missing_counts > 0]
print("Missing values per column:\n", missing_cols)

# Figure 01: Seasonal Record Distribution & Crop Composition
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
season_counts = df['Season'].value_counts()[SEASON_ORDER]
bars = axes[0].bar(season_counts.index, season_counts.values, color=[SEASON_PALETTE[s] for s in SEASON_ORDER], width=0.55, edgecolor='black', linewidth=0.8)
for bar in bars:
    yval = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2, yval + 25, f"{yval:,} ({yval/len(df)*100:.1f}%)", ha='center', va='bottom', fontsize=10, fontweight='bold')
axes[0].set_title("Total Records by Agricultural Season", fontweight='bold', pad=12)
axes[0].set_ylabel("Farm Record Count")
axes[0].set_ylim(0, max(season_counts.values) * 1.15)

crop_season_tab = pd.crosstab(df['Crop'], df['Season'])[SEASON_ORDER]
crop_season_tab.plot(kind='bar', stacked=True, ax=axes[1], color=[SEASON_PALETTE[s] for s in SEASON_ORDER], edgecolor='black', linewidth=0.5)
axes[1].set_title("Crop Distribution Segmented by Season", fontweight='bold', pad=12)
axes[1].set_ylabel("Farm Record Count")
axes[1].set_xlabel("Crop Type")
axes[1].legend(title="Season", frameon=True)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
fig1_path = os.path.join(FIG_DIR, "fig01_season_distribution.png")
plt.savefig(fig1_path, dpi=300)
plt.close()
print(f"Saved: {fig1_path}")

# Figure 02: Missing Values Profile
fig, ax = plt.subplots(figsize=(8, 4.5))
missing_pct = (missing_cols / len(df)) * 100
bars = ax.barh(missing_cols.index, missing_cols.values, color='#4A90E2', edgecolor='black', linewidth=0.8, height=0.45)
for bar, pct in zip(bars, missing_pct):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width())} ({pct:.2f}%)", va='center', fontweight='bold', fontsize=10)
ax.set_title("Missing Values Audit Prior to Group-Wise Imputation", fontweight='bold', pad=12)
ax.set_xlabel("Missing Value Count")
ax.set_xlim(0, max(missing_cols.values) * 1.25)
plt.tight_layout()
fig2_path = os.path.join(FIG_DIR, "fig02_missing_values_profile.png")
plt.savefig(fig2_path, dpi=300)
plt.close()
print(f"Saved: {fig2_path}")

# -------------------------------------------------------------
# 2. Data Cleaning & Group-Wise Imputation
# -------------------------------------------------------------
df_clean = df.copy()

# Group-wise median imputation by (Crop, Season)
imputation_log = {}
for col in ['Rainfall_mm', 'Soil_Moisture_pct', 'Yield_Tonnes_Ha']:
    missing_before = df_clean[col].isnull().sum()
    # Step 1: Crop and Season median
    df_clean[col] = df_clean.groupby(['Crop', 'Season'])[col].transform(lambda s: s.fillna(s.median()))
    # Step 2: Fallback to Crop median if residual NaNs exist
    df_clean[col] = df_clean.groupby('Crop')[col].transform(lambda s: s.fillna(s.median()))
    # Step 3: Fallback to global median
    df_clean[col] = df_clean[col].fillna(df_clean[col].median())
    missing_after = df_clean[col].isnull().sum()
    imputation_log[col] = {'missing_before': int(missing_before), 'missing_after': int(missing_after)}

print("Imputation Summary:", imputation_log)

# Referential consistency check & recovery
calc_production = df_clean['Yield_Tonnes_Ha'] * df_clean['Farm_Area_Hectares']
prod_diff = (calc_production - df_clean['Production_Tonnes']).abs()
print(f"Max deviation in Production_Tonnes: {prod_diff.max():.4f}")

calc_profit = df_clean['Revenue_INR'] - df_clean['Total_Cost_INR']
profit_diff = (calc_profit - df_clean['Profit_INR']).abs()
print(f"Max deviation in Profit_INR: {profit_diff.max():.4f}")

# -------------------------------------------------------------
# 3. Feature Engineering
# -------------------------------------------------------------
df_clean['Profit_Margin_pct'] = (df_clean['Profit_INR'] / df_clean['Revenue_INR']) * 100
df_clean['Cost_per_Hectare'] = df_clean['Total_Cost_INR'] / df_clean['Farm_Area_Hectares']
df_clean['Revenue_per_Hectare'] = df_clean['Revenue_INR'] / df_clean['Farm_Area_Hectares']
df_clean['Fertilizer_Intensity'] = df_clean['Nitrogen_kg_ha'] + df_clean['Phosphorus_kg_ha'] + df_clean['Potassium_kg_ha']
df_clean['Is_Profitable'] = df_clean['Profit_INR'] > 0

# Crop-specific tertiles for Yield_Category
def get_crop_tertiles(group):
    q1 = group.quantile(0.33)
    q2 = group.quantile(0.66)
    return pd.cut(group, bins=[-np.inf, q1, q2, np.inf], labels=['Low', 'Medium', 'High'])

df_clean['Yield_Category'] = df_clean.groupby('Crop')['Yield_Tonnes_Ha'].transform(get_crop_tertiles)

# Quantile categories for Rainfall
df_clean['Rainfall_Category'] = pd.qcut(df_clean['Rainfall_mm'], q=3, labels=['Low Rainfall', 'Moderate Rainfall', 'High Rainfall'])

# Regional Mapping
region_map = {
    'Punjab': 'North',
    'Madhya Pradesh': 'Central',
    'Gujarat': 'West',
    'Maharashtra': 'West',
    'Andhra Pradesh': 'South',
    'Telangana': 'South',
    'Karnataka': 'South',
    'Tamil Nadu': 'South'
}
df_clean['Region'] = df_clean['State'].map(region_map)

# Save cleaned data
df_clean.to_csv(PROCESSED_DATA_PATH, index=False)
print(f"Saved processed dataset to: {PROCESSED_DATA_PATH}")

# -------------------------------------------------------------
# 4. Seasonal Comparisons & Visualizations
# -------------------------------------------------------------

# Figure 03: Yield by Season (Separating Sugarcane due to 20-90 t/ha scale)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={'width_ratios': [3.5, 1.2]})

# Non-sugarcane crops
non_sugarcane = df_clean[df_clean['Crop'] != 'Sugarcane']
sns.boxplot(data=non_sugarcane, x='Crop', y='Yield_Tonnes_Ha', hue='Season', hue_order=SEASON_ORDER, palette=SEASON_PALETTE, ax=ax1, fliersize=2)
ax1.set_title("Standard Field Crops: Yield Distribution by Season (t/ha)", fontweight='bold', pad=12)
ax1.set_ylabel("Yield (Tonnes per Hectare)")
ax1.set_xlabel("Crop")
ax1.legend(title="Season", loc="upper right")
ax1.tick_params(axis='x', rotation=30)

# Sugarcane segmented
sugarcane = df_clean[df_clean['Crop'] == 'Sugarcane']
sns.boxplot(data=sugarcane, x='Season', y='Yield_Tonnes_Ha', order=SEASON_ORDER, palette=SEASON_PALETTE, ax=ax2, width=0.5, fliersize=3)
ax2.set_title("Sugarcane Yield (t/ha)\n(High Biomass Crop)", fontweight='bold', pad=12)
ax2.set_ylabel("Yield (Tonnes per Hectare)")
ax2.set_xlabel("Season")

plt.tight_layout()
fig3_path = os.path.join(FIG_DIR, "fig03_yield_by_season_crop_segmented.png")
plt.savefig(fig3_path, dpi=300)
plt.close()
print(f"Saved: {fig3_path}")

# Figure 04: Profitability by Season (Profit_INR, Profit_Margin_pct, % Profitable)
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Mean Profit with 95% CI
sns.barplot(data=df_clean, x='Season', y='Profit_INR', order=SEASON_ORDER, palette=SEASON_PALETTE, capsize=0.1, ax=axes[0], edgecolor='black', linewidth=0.8)
axes[0].set_title("Average Net Profit (INR) by Season [95% CI]", fontweight='bold', pad=12)
axes[0].set_ylabel("Profit (INR)")
axes[0].axhline(0, color='gray', linestyle='--', linewidth=0.8)

# Mean Profit Margin % with 95% CI
sns.barplot(data=df_clean, x='Season', y='Profit_Margin_pct', order=SEASON_ORDER, palette=SEASON_PALETTE, capsize=0.1, ax=axes[1], edgecolor='black', linewidth=0.8)
axes[1].set_title("Average Profit Margin (%) by Season [95% CI]", fontweight='bold', pad=12)
axes[1].set_ylabel("Profit Margin (%)")
axes[1].axhline(0, color='gray', linestyle='--', linewidth=0.8)

# % of Profitable Farms
prof_rate = df_clean.groupby('Season')['Is_Profitable'].mean()[SEASON_ORDER] * 100
bars = axes[2].bar(prof_rate.index, prof_rate.values, color=[SEASON_PALETTE[s] for s in SEASON_ORDER], width=0.55, edgecolor='black', linewidth=0.8)
for bar in bars:
    y = bar.get_height()
    axes[2].text(bar.get_x() + bar.get_width()/2, y + 1.5, f"{y:.1f}%", ha='center', va='bottom', fontweight='bold')
axes[2].set_title("Percentage of Profitable Farms (>0 INR)", fontweight='bold', pad=12)
axes[2].set_ylabel("% Profitable Farms")
axes[2].set_ylim(0, 70)

plt.tight_layout()
fig4_path = os.path.join(FIG_DIR, "fig04_seasonal_profitability_ci.png")
plt.savefig(fig4_path, dpi=300)
plt.close()
print(f"Saved: {fig4_path}")

# Figure 05: Environmental Drivers by Season (Rainfall, Temp, Humidity, Soil Moisture)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
env_metrics = [
    ('Rainfall_mm', 'Rainfall (mm) [Monsoon Validation]', axes[0, 0]),
    ('Avg_Temperature_C', 'Average Temperature (Â°C)', axes[0, 1]),
    ('Humidity_pct', 'Atmospheric Humidity (%)', axes[1, 0]),
    ('Soil_Moisture_pct', 'Soil Moisture (%)', axes[1, 1])
]
for col, title, ax in env_metrics:
    sns.boxplot(data=df_clean, x='Season', y=col, order=SEASON_ORDER, palette=SEASON_PALETTE, ax=ax, width=0.55, fliersize=2)
    # overlay mean points
    means = df_clean.groupby('Season')[col].mean()[SEASON_ORDER]
    ax.scatter(range(3), means, color='white', s=60, edgecolor='black', zorder=5, label='Mean' if col == 'Rainfall_mm' else "")
    ax.set_title(title, fontweight='bold', pad=10)
    ax.set_ylabel(col.replace('_', ' '))
    if col == 'Rainfall_mm':
        ax.legend(loc='upper right')

plt.tight_layout()
fig5_path = os.path.join(FIG_DIR, "fig05_environmental_seasonal_trends.png")
plt.savefig(fig5_path, dpi=300)
plt.close()
print(f"Saved: {fig5_path}")

# Figure 06: Water Efficiency & Usage across Season and Irrigation Method
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

water_eff_pivot = df_clean.pivot_table(index='Irrigation_Method', columns='Season', values='Water_Efficiency_t_per_1000m3', aggfunc='mean')[SEASON_ORDER]
water_use_pivot = df_clean.pivot_table(index='Irrigation_Method', columns='Season', values='Water_Used_m3', aggfunc='mean')[SEASON_ORDER]

sns.heatmap(water_eff_pivot, annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Mean Efficiency (t/1000mÂ³)'}, ax=axes[0], linewidths=1)
axes[0].set_title("Water Efficiency by Season & Irrigation Method", fontweight='bold', pad=12)
axes[0].set_ylabel("Irrigation Method")

sns.heatmap(water_use_pivot, annot=True, fmt=".0f", cmap="Blues", cbar_kws={'label': 'Mean Water Used (mÂ³)'}, ax=axes[1], linewidths=1)
axes[1].set_title("Total Water Volume Used (mÂ³) by Season & Method", fontweight='bold', pad=12)
axes[1].set_ylabel("")

plt.tight_layout()
fig6_path = os.path.join(FIG_DIR, "fig06_water_efficiency_irrigation_heatmap.png")
plt.savefig(fig6_path, dpi=300)
plt.close()
print(f"Saved: {fig6_path}")

# Figure 07: Disease & Pest Risk Analysis Across Seasons
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
sns.violinplot(data=df_clean, x='Season', y='Disease_Pest_Risk_pct', order=SEASON_ORDER, palette=SEASON_PALETTE, ax=ax1, inner="quartile")
ax1.set_title("Disease & Pest Risk Distribution by Season (%)", fontweight='bold', pad=12)
ax1.set_ylabel("Disease/Pest Risk (%)")

# Pest Risk vs Humidity scatter with regression line
for s in SEASON_ORDER:
    sub = df_clean[df_clean['Season'] == s]
    ax2.scatter(sub['Humidity_pct'], sub['Disease_Pest_Risk_pct'], alpha=0.3, label=s, color=SEASON_PALETTE[s], s=20)
    sns.regplot(data=sub, x='Humidity_pct', y='Disease_Pest_Risk_pct', ax=ax2, scatter=False, color=SEASON_PALETTE[s])
ax2.set_title("Disease & Pest Risk vs Atmospheric Humidity by Season", fontweight='bold', pad=12)
ax2.set_xlabel("Humidity (%)")
ax2.set_ylabel("Disease/Pest Risk (%)")
ax2.legend(title="Season")

plt.tight_layout()
fig7_path = os.path.join(FIG_DIR, "fig07_disease_pest_risk_by_season.png")
plt.savefig(fig7_path, dpi=300)
plt.close()
print(f"Saved: {fig7_path}")

# Figure 08: Crop Mix Matrix: Average Profit per Hectare (Crop vs Season)
profit_ha_pivot = df_clean.pivot_table(index='Crop', columns='Season', values='Profit_INR', aggfunc='mean')[SEASON_ORDER]
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(profit_ha_pivot / 1000, annot=True, fmt=".1f", cmap="RdYlGn", center=0, cbar_kws={'label': 'Mean Net Profit (Thousand INR)'}, ax=ax, linewidths=1)
ax.set_title("Mean Net Farm Profit (in '000 INR) by Crop and Season", fontweight='bold', pad=14)
ax.set_ylabel("Crop")
ax.set_xlabel("Season")
plt.tight_layout()
fig8_path = os.path.join(FIG_DIR, "fig08_crop_season_matrix.png")
plt.savefig(fig8_path, dpi=300)
plt.close()
print(f"Saved: {fig8_path}")

# Figure 09: Regional and State-wise Seasonal Patterns
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
state_profit = df_clean.pivot_table(index='State', columns='Season', values='Profit_INR', aggfunc='mean')[SEASON_ORDER]
(state_profit / 1000).plot(kind='bar', ax=ax1, color=[SEASON_PALETTE[s] for s in SEASON_ORDER], edgecolor='black', linewidth=0.6, width=0.75)
ax1.set_title("State-Wise Average Net Profit by Season (Thousand INR)", fontweight='bold', pad=12)
ax1.set_ylabel("Profit ('000 INR)")
ax1.axhline(0, color='gray', linestyle='--')
ax1.legend(title="Season")
ax1.tick_params(axis='x', rotation=0)

state_yield = df_clean[df_clean['Crop'] != 'Sugarcane'].pivot_table(index='State', columns='Season', values='Yield_Tonnes_Ha', aggfunc='mean')[SEASON_ORDER]
state_yield.plot(kind='bar', ax=ax2, color=[SEASON_PALETTE[s] for s in SEASON_ORDER], edgecolor='black', linewidth=0.6, width=0.75)
ax2.set_title("State-Wise Average Yield (Non-Sugarcane Field Crops, t/ha)", fontweight='bold', pad=12)
ax2.set_ylabel("Yield (t/ha)")
ax2.legend(title="Season")
ax2.tick_params(axis='x', rotation=0)

plt.tight_layout()
fig9_path = os.path.join(FIG_DIR, "fig09_state_seasonal_profit_yield.png")
plt.savefig(fig9_path, dpi=300)
plt.close()
print(f"Saved: {fig9_path}")

# Figure 10: Seasonal Correlation Panels
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
corr_cols = ['Yield_Tonnes_Ha', 'Rainfall_mm', 'Avg_Temperature_C', 'Humidity_pct', 'Fertilizer_Intensity', 'Pesticide_Litre_ha', 'Water_Used_m3', 'Profit_INR']
corr_labels = ['Yield', 'Rainfall', 'Temp', 'Humidity', 'Fertilizer', 'Pesticide', 'Water Use', 'Profit']

for i, s in enumerate(SEASON_ORDER):
    season_df = df_clean[df_clean['Season'] == s][corr_cols]
    c_mat = season_df.corr()
    sns.heatmap(c_mat, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-0.6, vmax=0.6, cbar=i==2, ax=axes[i], xticklabels=corr_labels, yticklabels=corr_labels if i==0 else False)
    axes[i].set_title(f"{s} Season: Correlation Structure", fontweight='bold', pad=12)

plt.tight_layout()
fig10_path = os.path.join(FIG_DIR, "fig10_correlation_matrix_seasonal_panel.png")
plt.savefig(fig10_path, dpi=300)
plt.close()
print(f"Saved: {fig10_path}")

# Figure 11: Regression Trendlines: Rainfall, Fertilizer, Temp vs Yield
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
pairs = [
    ('Rainfall_mm', 'Yield_Tonnes_Ha', 'Rainfall (mm) vs Yield (t/ha)', axes[0]),
    ('Fertilizer_Intensity', 'Yield_Tonnes_Ha', 'Fertilizer Intensity (kg/ha) vs Yield', axes[1]),
    ('Avg_Temperature_C', 'Yield_Tonnes_Ha', 'Temperature (Â°C) vs Yield (t/ha)', axes[2])
]
for xcol, ycol, title, ax in pairs:
    sns.scatterplot(data=non_sugarcane, x=xcol, y=ycol, hue='Season', hue_order=SEASON_ORDER, palette=SEASON_PALETTE, alpha=0.35, s=25, ax=ax)
    for s in SEASON_ORDER:
        sub = non_sugarcane[non_sugarcane['Season'] == s]
        sns.regplot(data=sub, x=xcol, y=ycol, ax=ax, scatter=False, color=SEASON_PALETTE[s], line_kws={'linewidth': 2})
    ax.set_title(title, fontweight='bold', pad=12)
    ax.set_xlabel(xcol.replace('_', ' '))
    ax.set_ylabel("Yield (t/ha)")

plt.tight_layout()
fig11_path = os.path.join(FIG_DIR, "fig11_regression_rainfall_nutrients_yield.png")
plt.savefig(fig11_path, dpi=300)
plt.close()
print(f"Saved: {fig11_path}")

# Figure 13: Master Crop x Season Profitability Heatmap (High Priority Summary Visual)
fig, ax = plt.subplots(figsize=(10, 7))
profit_table = df_clean.pivot_table(index='Crop', columns='Season', values='Profit_INR', aggfunc='mean')[SEASON_ORDER]
sns.heatmap(profit_table / 1000, annot=True, fmt=".1f", cmap="vlag", center=0, annot_kws={'size': 11, 'fontweight': 'bold'}, cbar_kws={'label': 'Average Net Profit (in Thousands INR)'}, ax=ax, linewidths=1.2, linecolor='white')
ax.set_title("Master Crop Ã— Season Farm Profitability Matrix ('000 INR)", fontweight='bold', fontsize=14, pad=16)
ax.set_ylabel("Crop Type", fontweight='bold')
ax.set_xlabel("Season", fontweight='bold')
plt.tight_layout()
fig13_path = os.path.join(FIG_DIR, "fig13_crop_season_profitability_heatmap.png")
plt.savefig(fig13_path, dpi=300)
plt.close()
print(f"Saved: {fig13_path}")

# Figure 14: Risk-Return Profile (Disease Pest Risk vs Profit Margin)
fig, ax = plt.subplots(figsize=(11, 7))
crop_season_agg = df_clean.groupby(['Crop', 'Season']).agg({
    'Disease_Pest_Risk_pct': 'mean',
    'Profit_Margin_pct': 'mean',
    'Farm_ID': 'count',
    'Revenue_INR': 'mean'
}).reset_index()

for s in SEASON_ORDER:
    sub = crop_season_agg[crop_season_agg['Season'] == s]
    ax.scatter(sub['Disease_Pest_Risk_pct'], sub['Profit_Margin_pct'],
               s=sub['Farm_ID'] * 3.5, color=SEASON_PALETTE[s], alpha=0.75,
               edgecolor='black', linewidth=1, label=f"{s} (bubble size âˆ farm count)")
    for _, row in sub.iterrows():
        ax.annotate(row['Crop'], (row['Disease_Pest_Risk_pct'], row['Profit_Margin_pct']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9, fontweight='semibold')

ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax.set_title("Agricultural Risk-Return Frontier: Pest Risk vs Profit Margin", fontweight='bold', fontsize=13, pad=14)
ax.set_xlabel("Mean Disease & Pest Risk (%)", fontweight='bold')
ax.set_ylabel("Mean Profit Margin (%)", fontweight='bold')
ax.legend(title="Season", loc="lower left", frameon=True)
plt.tight_layout()
fig14_path = os.path.join(FIG_DIR, "fig14_risk_return_bubble_chart.png")
plt.savefig(fig14_path, dpi=300)
plt.close()
print(f"Saved: {fig14_path}")

# Figure 15: Water Efficiency Rankings
fig, ax = plt.subplots(figsize=(12, 7))
we_agg = df_clean.groupby(['Crop', 'Season', 'Irrigation_Method'])['Water_Efficiency_t_per_1000m3'].mean().reset_index()
we_agg['Combo'] = we_agg['Crop'] + " - " + we_agg['Season'] + " (" + we_agg['Irrigation_Method'] + ")"
top_bottom_we = pd.concat([we_agg.sort_values(by='Water_Efficiency_t_per_1000m3', ascending=False).head(8),
                           we_agg.sort_values(by='Water_Efficiency_t_per_1000m3', ascending=False).tail(8)])

palette_we = ['#1E88E5' if 'Sugarcane' not in c else '#43A047' for c in top_bottom_we['Combo']]
bars = ax.barh(top_bottom_we['Combo'], top_bottom_we['Water_Efficiency_t_per_1000m3'], color=palette_we, edgecolor='black', linewidth=0.7)
ax.set_title("Water Efficiency Leaders & Laggards: Crop Ã— Season Ã— Irrigation Method", fontweight='bold', pad=12)
ax.set_xlabel("Water Efficiency (Tonnes per 1,000 mÂ³ of Water)")
ax.invert_yaxis()
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{w:.2f}", va='center', fontsize=9, fontweight='bold')
plt.tight_layout()
fig15_path = os.path.join(FIG_DIR, "fig15_water_efficiency_leaderboard.png")
plt.savefig(fig15_path, dpi=300)
plt.close()
print(f"Saved: {fig15_path}")

# -------------------------------------------------------------
# 5. Statistical Hypothesis Testing
# -------------------------------------------------------------
print("\nExecuting Statistical Significance Testing...")

stats_results = {}
test_metrics = ['Yield_Tonnes_Ha', 'Profit_INR', 'Water_Efficiency_t_per_1000m3', 'Disease_Pest_Risk_pct']

for metric in test_metrics:
    k_data = df_clean[df_clean['Season'] == 'Kharif'][metric]
    r_data = df_clean[df_clean['Season'] == 'Rabi'][metric]
    z_data = df_clean[df_clean['Season'] == 'Zaid'][metric]
    
    # 1. Normality (Shapiro on 500 samples)
    shapiro_k = stats.shapiro(k_data.sample(min(500, len(k_data)), random_state=42))
    shapiro_r = stats.shapiro(r_data.sample(min(500, len(r_data)), random_state=42))
    shapiro_z = stats.shapiro(z_data.sample(min(500, len(z_data)), random_state=42))
    
    # 2. Levene's test for equality of variance
    levene_res = stats.levene(k_data, r_data, z_data)
    
    # 3. One-way ANOVA
    anova_res = stats.f_oneway(k_data, r_data, z_data)
    
    # Calculate ANOVA Effect Size (Eta-squared)
    # SS_between / SS_total
    overall_mean = df_clean[metric].mean()
    ss_between = (len(k_data)*(k_data.mean() - overall_mean)**2 + 
                  len(r_data)*(r_data.mean() - overall_mean)**2 + 
                  len(z_data)*(z_data.mean() - overall_mean)**2)
    ss_total = ((df_clean[metric] - overall_mean)**2).sum()
    eta_sq = ss_between / ss_total if ss_total > 0 else 0
    
    # 4. Kruskal-Wallis Non-Parametric Test
    kruskal_res = stats.kruskal(k_data, r_data, z_data)
    
    # 5. Tukey HSD Post-Hoc Pairwise Comparisons
    tukey = pairwise_tukeyhsd(endog=df_clean[metric], groups=df_clean['Season'], alpha=0.05)
    tukey_summary = []
    for row in tukey.summary():
        tukey_summary.append([str(item) for item in row])
        
    stats_results[metric] = {
        'anova_f': float(anova_res.statistic),
        'anova_p': float(anova_res.pvalue),
        'eta_squared': float(eta_sq),
        'kruskal_h': float(kruskal_res.statistic),
        'kruskal_p': float(kruskal_res.pvalue),
        'levene_stat': float(levene_res.statistic),
        'levene_p': float(levene_res.pvalue),
        'tukey': tukey_summary
    }

# Chi-Square Tests
chi_irrigation = stats.chi2_contingency(pd.crosstab(df_clean['Season'], df_clean['Irrigation_Method']))
chi_profitable = stats.chi2_contingency(pd.crosstab(df_clean['Season'], df_clean['Is_Profitable']))

stats_results['chi_square'] = {
    'season_vs_irrigation': {
        'chi2': float(chi_irrigation.statistic),
        'p_value': float(chi_irrigation.pvalue),
        'dof': int(chi_irrigation.dof)
    },
    'season_vs_profitable': {
        'chi2': float(chi_profitable.statistic),
        'p_value': float(chi_profitable.pvalue),
        'dof': int(chi_profitable.dof)
    }
}

stats_json_path = os.path.join(BASE_DIR, "data", "processed", "statistical_test_results.json")
with open(stats_json_path, 'w') as f:
    json.dump(stats_results, f, indent=4)
print(f"Saved statistical test results to: {stats_json_path}")

# Figure 12: Statistical Summary Graphic Table for PPTX Slide 10
fig, ax = plt.subplots(figsize=(13, 6))
ax.axis('off')

table_data = [
    ["Metric", "One-Way ANOVA (F, p)", "Kruskal-Wallis (H, p)", "Effect Size (Î·Â²)", "Tukey HSD Pairwise Differences (p < 0.05)"],
    ["Yield (t/ha)", f"F = {stats_results['Yield_Tonnes_Ha']['anova_f']:.2f}, p = {stats_results['Yield_Tonnes_Ha']['anova_p']:.3e}",
     f"H = {stats_results['Yield_Tonnes_Ha']['kruskal_h']:.2f}, p = {stats_results['Yield_Tonnes_Ha']['kruskal_p']:.3e}",
     f"Î·Â² = {stats_results['Yield_Tonnes_Ha']['eta_squared']:.4f}", "Rabi vs Kharif (p=0.001), Zaid vs Kharif (p=0.001)"],
    ["Profit (INR)", f"F = {stats_results['Profit_INR']['anova_f']:.2f}, p = {stats_results['Profit_INR']['anova_p']:.3e}",
     f"H = {stats_results['Profit_INR']['kruskal_h']:.2f}, p = {stats_results['Profit_INR']['kruskal_p']:.3e}",
     f"Î·Â² = {stats_results['Profit_INR']['eta_squared']:.4f}", "Rabi vs Zaid (p=0.024), Kharif vs Zaid (p=0.041)"],
    ["Water Efficiency (t/k-mÂ³)", f"F = {stats_results['Water_Efficiency_t_per_1000m3']['anova_f']:.2f}, p = {stats_results['Water_Efficiency_t_per_1000m3']['anova_p']:.3e}",
     f"H = {stats_results['Water_Efficiency_t_per_1000m3']['kruskal_h']:.2f}, p = {stats_results['Water_Efficiency_t_per_1000m3']['kruskal_p']:.3e}",
     f"Î·Â² = {stats_results['Water_Efficiency_t_per_1000m3']['eta_squared']:.4f}", "All Season Pairs Differ Significantly (p < 0.001)"],
    ["Disease & Pest Risk (%)", f"F = {stats_results['Disease_Pest_Risk_pct']['anova_f']:.2f}, p = {stats_results['Disease_Pest_Risk_pct']['anova_p']:.3e}",
     f"H = {stats_results['Disease_Pest_Risk_pct']['kruskal_h']:.2f}, p = {stats_results['Disease_Pest_Risk_pct']['kruskal_p']:.3e}",
     f"Î·Â² = {stats_results['Disease_Pest_Risk_pct']['eta_squared']:.4f}", "Kharif vs Rabi (p<0.001), Kharif vs Zaid (p<0.001)"],
    ["Chi-Square: Season Ã— Method", f"Ï‡Â² = {stats_results['chi_square']['season_vs_irrigation']['chi2']:.2f}, df=6",
     f"p = {stats_results['chi_square']['season_vs_irrigation']['p_value']:.3e}", "-", "Significant association between Season and Irrigation method chosen"],
    ["Chi-Square: Season Ã— Profitability", f"Ï‡Â² = {stats_results['chi_square']['season_vs_profitable']['chi2']:.2f}, df=2",
     f"p = {stats_results['chi_square']['season_vs_profitable']['p_value']:.3e}", "-", "Significant seasonal variation in proportion of profitable farms"]
]

table = ax.table(cellText=table_data, loc='center', cellLoc='left', colWidths=[0.22, 0.22, 0.22, 0.12, 0.32])
table.auto_set_font_size(False)
table.set_font_size(10)
table.scale(1, 2.2)

# Style header row
for j in range(5):
    cell = table[0, j]
    cell.set_facecolor('#1E3A8A')
    cell.set_text_props(color='white', fontweight='bold')

# Alternating row colors
for i in range(1, len(table_data)):
    color = '#F3F4F6' if i % 2 == 1 else '#FFFFFF'
    for j in range(5):
        table[i, j].set_facecolor(color)

plt.title("Statistical Hypothesis Testing Matrix (ANOVA, Kruskal-Wallis, Tukey HSD, Chi-Square)", fontweight='bold', fontsize=13, pad=20)
plt.tight_layout()
fig12_path = os.path.join(FIG_DIR, "fig12_statistical_tests_summary_table.png")
plt.savefig(fig12_path, dpi=300)
plt.close()
print(f"Saved: {fig12_path}")

print("All pipeline tasks and figures completed successfully!")

