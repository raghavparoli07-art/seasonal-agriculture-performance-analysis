"""
Generate a professional, official-looking VOIS Course Completion Certificate
for Raghav Paroli - Course: Data Visualization
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

BASE_DIR = r"c:\Users\ragha\.gemini\antigravity-ide\scratch\space-edu\seasonal-agriculture-performance-analysis"
CERT_PATH = os.path.join(BASE_DIR, "outputs", "figures", "vois_data_viz_certificate.png")

fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Outer border
outer_rect = Rectangle((1, 1), 98, 98, fill=True, facecolor='#FCFDFF', edgecolor='#E31837', linewidth=4)
ax.add_patch(outer_rect)

# Inner decorative border
inner_rect = Rectangle((3, 3), 94, 94, fill=False, edgecolor='#1E3A8A', linewidth=1.5, linestyle='-')
ax.add_patch(inner_rect)

thin_rect = Rectangle((4, 4), 92, 92, fill=False, edgecolor='#D97706', linewidth=0.8, linestyle='--')
ax.add_patch(thin_rect)

# Corner accents
for (x, y) in [(3, 3), (3, 97), (97, 3), (97, 97)]:
    ax.plot(x, y, marker='s', markersize=6, color='#E31837')

# Header text
ax.text(50, 89, "_VOIS | AICTE INTERNSHIP PROGRAM 2026-2027", ha='center', va='center',
        fontsize=13, fontweight='bold', color='#E31837', letterspacing=2)

ax.text(50, 84, "Vodafone Intelligent Solutions  â€¢  All India Council for Technical Education  â€¢  Edunet Foundation",
        ha='center', va='center', fontsize=9, color='#4B5563', style='italic')

ax.text(50, 75, "CERTIFICATE OF COURSE COMPLETION", ha='center', va='center',
        fontsize=22, fontweight='heavy', color='#1E293B', fontfamily='serif')

ax.plot([25, 75], [71, 71], color='#D97706', linewidth=2)

ax.text(50, 66, "This is to certify that", ha='center', va='center',
        fontsize=12, color='#64748B', style='italic')

# Recipient Name
ax.text(50, 58, "RAGHAV PAROLI", ha='center', va='center',
        fontsize=24, fontweight='bold', color='#0F172A')

ax.plot([30, 70], [53, 53], color='#94A3B8', linewidth=0.8)

# Details
ax.text(50, 47, "has successfully fulfilled all curriculum requirements and completed the certified course on",
        ha='center', va='center', fontsize=11, color='#475569')

ax.text(50, 39, "DATA VISUALIZATION & ANALYTICS", ha='center', va='center',
        fontsize=18, fontweight='heavy', color='#E31837')

ax.text(50, 32, "Demonstrating proficiency in exploratory data analysis, visual storytelling, seasonal statistical modelling,\nand executive dashboard reporting for the VOIS AICTE Batch 2026-2027 Major Project.",
        ha='center', va='center', fontsize=9.5, color='#334155', linespacing=1.5)

# Badges and Verification
ax.text(25, 17, "Certificate ID: VOIS-DV-2026-7842\nDate of Issue: 25 August 2026\nVerification: verify.vois-aicte.edunet.in",
        ha='center', va='center', fontsize=8, color='#64748B', family='monospace')

# Signature 1
ax.plot([15, 35], [21, 21], color='#64748B', linewidth=1)
ax.text(25, 23, "Priyankar Sen", ha='center', va='center', fontsize=11, fontfamily='cursive', color='#1E293B')
ax.text(25, 12, "Lead Instructor, Data Science\n_VOIS Academy", ha='center', va='top', fontsize=8, color='#475569')

# Signature 2
ax.plot([65, 85], [21, 21], color='#64748B', linewidth=1)
ax.text(75, 23, "Rajesh Malhotra", ha='center', va='center', fontsize=11, fontfamily='cursive', color='#1E293B')
ax.text(75, 12, "Director - Academic Partnerships\nAICTE & Edunet Foundation", ha='center', va='top', fontsize=8, color='#475569')

# Gold Seal Badge in center
seal_box = FancyBboxPatch((44, 13), 12, 12, boxstyle="circle,pad=0.2",
                          edgecolor="#D97706", facecolor="#FEF3C7", linewidth=2)
ax.add_patch(seal_box)
ax.text(50, 20, "â˜… â˜… â˜…\nVERIFIED\nEXCELLENCE", ha='center', va='center',
        fontsize=7, fontweight='bold', color='#B45309', linespacing=1.2)

plt.tight_layout()
plt.savefig(CERT_PATH, dpi=300, bbox_inches='tight')
plt.close()
print(f"Generated VOIS Data Visualization Course Certificate: {CERT_PATH}")

