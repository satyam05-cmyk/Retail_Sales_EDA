import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURATION
df = pd.read_csv('data/superstore_sales.csv')

# SET STYLE
sns.set_theme(style="whitegrid")
plt.figure(figsize=(20, 15))

# --- CHART 1: THE MACRO VIEW (Sales vs Profit) ---
# Summing up per Sub-Category to see who is making money vs losing money
subcat_profit = df.groupby('Sub-Category')[['Sales', 'Profit']].sum().sort_values('Profit', ascending=False)

plt.subplot(2, 2, 1)
# We plot Profit. Red bars = Negative Profit.
colors = ['red' if x < 0 else 'green' for x in subcat_profit['Profit']]
subcat_profit['Profit'].plot(kind='bar', color=colors)
plt.title('Total Profit by Sub-Category (The "Bleeding" Chart)')
plt.ylabel('Total Profit ($)')
plt.axhline(0, color='black', linewidth=1) # The "Zero" line

# --- CHART 2: THE CORRELATION TRAP ---
# Does Discounting kill Profit?
plt.subplot(2, 2, 2)
sns.scatterplot(data=df, x='Discount', y='Profit', hue='Category', alpha=0.6)
plt.title('Impact of Discount on Profit')
plt.axhline(0, color='black', linestyle='--')

# --- CHART 3: REGIONAL PERFORMANCE ---
plt.subplot(2, 2, 3)
sns.barplot(data=df, x='Region', y='Profit', estimator=sum, errorbar=None, palette="viridis")
plt.title('Total Profit by Region')
plt.ylabel('Total Profit ($)')

# --- CHART 4: THE HEATMAP (The "Smoking Gun") ---
# Correlation Matrix to show relationship strength
plt.subplot(2, 2, 4)
corr = df[['Sales', 'Quantity', 'Discount', 'Profit']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix: Discount vs Profit')

# --- SAVE THE EVIDENCE ---
plt.tight_layout()
plt.savefig('executive_dashboard.png')
print("SUCCESS: Dashboard saved as 'executive_dashboard.png'")
# plt.show() # Commented out to avoid blocking execution in non-interactive environments, but can be enabled if running locally with UI.
