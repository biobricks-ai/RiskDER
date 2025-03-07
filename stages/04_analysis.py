import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import pathlib


# Read the data
# Assuming your dataframe is stored in a CSV file. If not, adjust the data loading accordingly
outdir = pathlib.Path('brick')
aggdf = pd.read_parquet(outdir / 'thyroid_testing_results.parquet')

# Set the style for better-looking plots
plt.style.use('seaborn-v0_8-white')  # Use white background style
sns.set_palette("husl")

# 1. Plot counting different chemicals
plt.figure(figsize=(12, 36))  # Made even taller for better readability
chemical_counts = aggdf['substance'].value_counts()
sns.barplot(x=chemical_counts.values, y=chemical_counts.index)
plt.title('Count of Different Chemicals in Dataset', fontsize=16)
plt.xlabel('Count', fontsize=14)
plt.ylabel('Chemical Name', fontsize=14)
plt.xticks(fontsize=12)
plt.tight_layout()
plt.savefig(outdir / 'chemical_counts.png', dpi=400)  # Higher DPI for poster quality
plt.close()

# 2. Plot counting different guideline + metrics combinations
plt.figure(figsize=(12, 9))
guideline_metric_counts = aggdf.groupby(['guideline', 'metric']).size().reset_index(name='count')
guideline_metric_counts = guideline_metric_counts.sort_values('count', ascending=False)

# Get top 5 guidelines and metrics by count
top_guidelines = guideline_metric_counts['guideline'].value_counts().nlargest(5).index
top_metrics = guideline_metric_counts['metric'].value_counts().nlargest(3).index

# Filter data to only include top categories
filtered_counts = guideline_metric_counts[
    guideline_metric_counts['guideline'].isin(top_guidelines) & 
    guideline_metric_counts['metric'].isin(top_metrics)
]

# Create a pivot table for better visualization
pivot_data = filtered_counts.pivot_table(
    index='guideline',
    columns='metric',
    values='count',
    fill_value=0
)

# Plot heatmap with a dark theme
plt.style.use('dark_background')
sns.heatmap(pivot_data, annot=True, fmt='g', cmap='magma')
plt.title('Frequency of Top Guideline-Metric Combinations', fontsize=16, pad=20)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)
plt.tight_layout()
plt.savefig('guideline_metric_heatmap.png', dpi=400, bbox_inches='tight', facecolor='black', edgecolor='none')
plt.close()

# Reset style for next plots
plt.style.use('seaborn-v0_8-dark')

# 3. Generate distributions of values for different guideline + metrics
# First, convert values to numeric, handling any non-numeric values
aggdf['value'] = pd.to_numeric(aggdf['value'], errors='coerce')

# Filter out rows with non-numeric values and keep only top categories
numeric_df = aggdf.dropna(subset=['value'])
numeric_df = numeric_df[
    numeric_df['guideline'].isin(top_guidelines) & 
    numeric_df['metric'].isin(top_metrics)
]

# Create violin plots with custom styling
plt.figure(figsize=(12, 9))
sns.set_palette("husl")
violin = sns.violinplot(data=numeric_df, x='guideline', y='value', hue='metric',
                       saturation=0.8, inner='box')
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.title('Distribution of Values by Top Guidelines and Metrics', fontsize=16, pad=20)
plt.ylabel('Value', fontsize=12)
plt.xlabel('Guideline', fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, facecolor='black', edgecolor='white')
for spine in violin.spines.values():
    spine.set_edgecolor('white')
plt.tight_layout()
plt.savefig('value_distributions.png', dpi=400, bbox_inches='tight', facecolor='black', edgecolor='none')
plt.close()

# Log-scale version with enhanced styling
plt.figure(figsize=(12, 9))
violin = sns.violinplot(data=numeric_df, x='guideline', y='value', hue='metric',
                       saturation=0.8, inner='box')
plt.yscale('log')
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.title('Distribution of Values by Top Guidelines and Metrics (Log Scale)', fontsize=16, pad=20)
plt.ylabel('Value (log scale)', fontsize=12)
plt.xlabel('Guideline', fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, facecolor='black', edgecolor='white')
for spine in violin.spines.values():
    spine.set_edgecolor('white')
plt.tight_layout()
plt.savefig('value_distributions_log.png', dpi=400, bbox_inches='tight', facecolor='black', edgecolor='none')
plt.close()

# Print some summary statistics with formatting
print("\n" + "="*50)
print("Summary Statistics".center(50))
print("="*50)
print(f"\nNumber of unique chemicals: {len(chemical_counts)}")
print("\nTop 5 most frequent chemicals:")
for chem, count in chemical_counts.head().items():
    print(f"  • {chem}: {count}")
print(f"\nNumber of unique guideline-metric combinations: {len(guideline_metric_counts)}")
print("="*50)