import pandas as pd
import numpy as np
import os

print("--- Step 1: Data Loading ---")
# Ensure karein ki raw files same folder mein ho
try:
    products = pd.read_csv('products.csv')
    orders = pd.read_csv('orders.csv')
    website_sessions = pd.read_csv('website_sessions.csv')
    print("Files loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: {e}. Please ensure 'orders.csv', 'products.csv', and 'website_sessions.csv' are in the folder.")
    exit()

# --- Step 2: Cleaning Sessions ---
print("\n--- Cleaning Sessions ---")
sessions_clean = website_sessions.drop_duplicates().copy()
sessions_clean['created_at'] = pd.to_datetime(sessions_clean['created_at'])

# Standardize UTMs
for col in ['utm_source', 'utm_campaign', 'utm_content']:
    sessions_clean[col] = sessions_clean[col].str.lower()

# Smart Filling of Null UTM Sources
def fill_smart_source(row):
    if pd.isnull(row['utm_source']):
        if pd.notnull(row['http_referer']):
            return 'organic'
        else:
            return 'direct'
    return row['utm_source']

sessions_clean['utm_source'] = sessions_clean.apply(fill_smart_source, axis=1)
sessions_clean['utm_source'] = sessions_clean['utm_source'].fillna('unknown')
sessions_clean['utm_campaign'] = sessions_clean['utm_campaign'].fillna('uncategorized')

# --- Step 3: Cleaning Orders & Adding Cost (COGS) ---
print("\n--- Processing Financials ---")
orders['created_at'] = pd.to_datetime(orders['created_at'])

# Mapping Missing User IDs
user_map = sessions_clean.set_index('website_session_id')['user_id'].to_dict()
orders['user_id'] = orders['user_id'].fillna(orders['website_session_id'].map(user_map))

# Filling Null Prices & Costs with Mean (Optimization)
orders['price_usd'] = orders['price_usd'].fillna(orders['price_usd'].mean())
orders['cogs_usd'] = orders['cogs_usd'].fillna(orders['cogs_usd'].mean())  # <--- COGS added here

# --- Step 4: The Master Merge (With Profit Logic) ---
print("\n--- Merging Data ---")
# Merging Sessions with Orders + COGS
master_df = pd.merge(
    sessions_clean,
    orders[['website_session_id', 'order_id', 'price_usd', 'cogs_usd', 'items_purchased', 'primary_product_id']], # Included cogs_usd
    on='website_session_id',
    how='left'
)

# Adding Product Names
master_df = pd.merge(
    master_df,
    products[['product_id', 'product_name']],
    left_on='primary_product_id',
    right_on='product_id',
    how='left'
)

# --- Step 5: Profit Calculation ---
print("\n--- Calculating Net Profit ---")

# Filling Non-Order rows with 0
master_df['price_usd'] = master_df['price_usd'].fillna(0)
master_df['cogs_usd'] = master_df['cogs_usd'].fillna(0)
master_df['is_conversion'] = np.where(master_df['order_id'].notnull(), 1, 0)

# Net Profit Formula: Sales Price - Cost of Goods
master_df['net_profit'] = master_df['price_usd'] - master_df['cogs_usd']

# Helper Columns
master_df['month_year'] = master_df['created_at'].dt.to_period('M').astype(str)
master_df['product_name'] = master_df['product_name'].fillna('No Purchase')

# --- Step 6: Export ---
output_file = 'BearCart_Full_Analytics_With_Profit.csv'
master_df.to_csv(output_file, index=False)

print(f"\nSUCCESS! New file generated: {output_file}")
print(f"Total Net Profit Calculated: ${master_df['net_profit'].sum():,.2f}")