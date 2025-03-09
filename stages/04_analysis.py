import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import pathlib


# setup, load and clean data
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
outdir = pathlib.Path('brick')
aggdf = pd.read_parquet(outdir / 'thyroid_testing_results.parquet')
aggdf = aggdf.assign(guideline=aggdf['guideline'].str.split(';')).explode('guideline').dropna(subset=['guideline'])
aggdf['guideline'] = aggdf['guideline'].str.strip()
aggdf['guideline'] = aggdf['guideline'].str.lower()
aggdf['substance'] = aggdf['substance'].str.lower()
aggdf = aggdf[~aggdf['guideline'].str.contains('attachment a|non-guideline|na|n/a|none|nonguideline|not specified|^$', na=False, regex=True)]
aggdf['guideline'] = aggdf['guideline'].str.replace('guideline', '', case=False).str.strip()
aggdf = aggdf[(aggdf['guideline'].str.len() > 3) & (aggdf['guideline'].str.len() < 40)]
aggdf['value'] = pd.to_numeric(aggdf['value'], errors='coerce')

# 1. PLOT COUNTING DIFFERENT CHEMICALS ====================================================
plt.style.use('seaborn-v0_8-white')  # Use white background style
sns.set_palette("husl")
plt.figure(figsize=(12, 36))  # Made even taller for better readability
chemical_counts = aggdf['substance'].value_counts().sort_values(ascending=False)
guideline_counts = aggdf['guideline'].value_counts().sort_values(ascending=False)
# remove NA, Attachment A and None from results
guideline_counts = guideline_counts[~guideline_counts.index.isin(['NA', 'Attachment A', 'None','','N/A'])]

# Truncate chemical names to first 30 characters plus ellipsis if longer
chemical_counts.index = chemical_counts.index.map(lambda x: x[:30] + '...' if len(x) > 30 else x)
sns.barplot(x=chemical_counts.values, y=chemical_counts.index)
plt.title('Count of Different Chemicals in Dataset', fontsize=16)
plt.xlabel('Count', fontsize=14)
plt.ylabel('Chemical Name', fontsize=14)
plt.xticks(fontsize=12)
plt.tight_layout()
plt.savefig(outdir / 'chemical_counts.pdf', dpi=600, format='pdf')  # Save as PDF for Google Slides
plt.close()

# 2. PLOT COUNTING DIFFERENT GUIDELINE + METRICS COMBINATIONS ====================================================
plt.style.use('seaborn-v0_8-white')  # Use white background style
sns.set_palette("husl")
plt.figure(figsize=(12, 9))

guideline_counts = aggdf['guideline'].value_counts().sort_values(ascending=False)
guideline_counts = guideline_counts[guideline_counts > 3]
guideline_counts.index = guideline_counts.index.map(lambda x: x[:30] + '...' if len(x) > 30 else x)

# Plot heatmap with a dark theme
plt.style.use('seaborn-v0_8-white')  # Use white background for better poster visibility
plt.figure(figsize=(12, 9), facecolor='white')  # Set figure background to white
sns.barplot(x=guideline_counts.values, y=guideline_counts.index, color='#1f77b4')  # Single color for all bars
plt.title('Count of Different Guidelines in Dataset', fontsize=16, pad=20, color='black')
plt.xlabel('Count', fontsize=14, color='black') 
plt.ylabel('Guideline', fontsize=14, color='black')
plt.xticks(fontsize=12, color='black')
plt.yticks(color='black')
plt.tight_layout()
plt.savefig(outdir / 'guideline_counts.pdf', dpi=600, format='pdf', bbox_inches='tight', facecolor='white')  # Set output background to white
plt.close()

# 3. GENERATE DISTRIBUTIONS OF VALUES FOR DIFFERENT GUIDELINE + METRICS ====================================================
plt.style.use('seaborn-v0_8-white')  # Switch to white background
distdf = aggdf.copy()
# distdf = distdf[distdf['guideline'].isin(['ocspp 890.1500', 'oecd 229', 'ocspp 890.1350'])]
# distdf = distdf[distdf['metric'].isin(['NOAEL', 'LOAEL','LD50'])]
distdf = distdf[distdf['units'].isin(['mg/kg/day', 'mg/kg', 'mg/kg-bw/day'])]
distdf = distdf[distdf['value'] > 0.1]
distdf['units'].value_counts()
distdf['metric'].value_counts()
distdf[distdf['metric'] == 'LD50']

# Create three stacked plots with both density and histogram
# Cap values at 2000 mg/kg
distdf['value'] = distdf['value'].apply(lambda x: min(x, 2000))

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
plt.subplots_adjust(hspace=0.3)  # Adjust space between plots

# Set color palette
colors = sns.husl_palette(3)

# Plot for NOAEL
noael_data = distdf[distdf['metric'] == 'NOAEL']['value']
sns.histplot(data=noael_data, ax=ax1, bins=10, color=colors[0], alpha=0.3, stat='density')
sns.kdeplot(data=noael_data, ax=ax1, color=colors[0], linewidth=2)
ax1.set_ylabel('NOAEL')
ax1.set_xlim(0, 2000)

# Plot for LOAEL
loael_data = distdf[distdf['metric'] == 'LOAEL']['value']
sns.histplot(data=loael_data, ax=ax2, bins=10, color=colors[1], alpha=0.3, stat='density')
sns.kdeplot(data=loael_data, ax=ax2, color=colors[1], linewidth=2)
ax2.set_ylabel('LOAEL')
ax2.set_xlim(0, 2000)

# Plot for LD50
ld50_data = distdf[distdf['metric'] == 'LD50']['value']
sns.histplot(data=ld50_data, ax=ax3, bins=10, color=colors[2], alpha=0.3, stat='density')
sns.kdeplot(data=ld50_data, ax=ax3, color=colors[2], linewidth=2)
ax3.set_ylabel('LD50')
ax3.set_xlabel('Value (mg/kg)')
ax3.set_xlim(0, 2000)

# Add title to the figure
fig.suptitle('Distribution of Values by Metric Type', fontsize=16, y=0.95)

plt.tight_layout()
plt.savefig(outdir / 'value_distributions.pdf', dpi=400, bbox_inches='tight', facecolor='white')
plt.close()

# 4. GENERATE A PRETTY SHUFFLED TABLE OF VALUES ====================================================
# Create a nicely formatted table for visualization
# Shuffle and take first 20 rows
# Remove rows where any column has more than 40 characters first
import pandas as pd
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def mktable():
    # Create a DataFrame with formatted data
    filtered_df = aggdf.copy()[['guideline', 'substance', 'metric', 'value', 'units']]
    filtered_df = filtered_df[filtered_df.map(lambda x: len(str(x)) <= 30).all(axis=1)]
    filtered_df = filtered_df[filtered_df['units'].isin(['mg/kg/day', 'mg/kg', 'mg/kg-bw/day', '%', 'mg/L', 'ppm', 'days'])]

    # Sample 15 random rows
    display_df = filtered_df.sample(n=min(20, len(filtered_df)), random_state=42).reset_index(drop=True)

    # Create figure and axis with white background
    fig, ax = plt.subplots(figsize=(15, 8), facecolor='white')
    
    # Hide axes
    ax.axis('off')

    # Create table
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc='right',
        loc='center',
        colWidths=[0.15, 0.15, 0.15, 0.1, 0.1]  # Made first three columns slightly narrower
    )

    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    
    # Style header
    for j, cell in enumerate(table._cells[(0, j)] for j in range(len(display_df.columns))):
        cell.set_facecolor('black')
        cell.set_text_props(color='white', weight='bold', ha='right')  # Right align header text
        cell.set_fontsize(10)
        cell.PAD = 0.02  # Reduce padding

    # Style alternating rows
    for i in range(len(display_df)):
        for j in range(len(display_df.columns)):
            cell = table._cells[(i + 1, j)]
            if i % 2 == 0:
                cell.set_facecolor('#f0f0f0')
            else:
                cell.set_facecolor('white')
            cell.PAD = 0.02  # Reduce padding
    
    plt.tight_layout()
    
    # Save as SVG with white background
    plt.savefig(outdir / 'summary_table.svg', format='svg', bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"SVG successfully created: {outdir / 'summary_table.svg'}")

mktable()



