import pandas as pd
import numpy as np
import os

print("--- Step 1: Loading All Datasets ---")
try:
    products = pd.read_csv('products.csv')
    orders = pd.read_csv('orders.csv', on_bad_lines='skip', engine='python')
    website_sessions = pd.read_csv('website_sessions.csv')
    order_item_refunds = pd.read_csv('order_item_refunds.csv') # New File Loaded
    print("Files loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: {e}. Please ensure all CSV files are in the folder.")
    exit()
except Exception as e:
    print(f"Error loading files: {e}")
    exit()

# --- Step 2: Cleaning Sessions (Standard Procedure) ---
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

# --- Step 3: Processing Refunds (New Logic) ---
print("\n--- Processing Refunds ---")
# Refunds item level par hote hain, hum unhe Order level par sum karenge
refunds_grouped = order_item_refunds.groupby('order_id')['refund_amount_usd'].sum().reset_index()
print(f"Total Refunded Orders Found: {len(refunds_grouped)}")


# --- Step 4: Cleaning Orders & Merging Refunds ---
print("\n--- Processing Orders & Financials ---")
orders['created_at'] = pd.to_datetime(orders['created_at'])

# Mapping Missing User IDs
user_map = sessions_clean.set_index('website_session_id')['user_id'].to_dict()
orders['user_id'] = orders['user_id'].fillna(orders['website_session_id'].map(user_map))

# Filling Null Prices & Costs
orders['price_usd'] = orders['price_usd'].fillna(orders['price_usd'].mean())
orders['cogs_usd'] = orders['cogs_usd'].fillna(orders['cogs_usd'].mean())

# Merging Refunds into Orders Table
orders = pd.merge(orders, refunds_grouped, on='order_id', how='left')

# Filling NaN Refunds with 0 (Kyunki jinka refund nahi hua wo 0 hain)
orders['refund_amount_usd'] = orders['refund_amount_usd'].fillna(0)

# Creating 'is_refunded' Flag (1 = Refunded, 0 = No Refund)
orders['is_refunded'] = np.where(orders['refund_amount_usd'] > 0, 1, 0)


# --- Step 5: The Master Merge ---
print("\n--- Creating Master Sheet ---")
# Merging Sessions with Orders (now containing Refund info)
master_df = pd.merge(
    sessions_clean,
    orders[['website_session_id', 'order_id', 'price_usd', 'cogs_usd', 'refund_amount_usd', 'is_refunded', 'items_purchased', 'primary_product_id']], 
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

# --- Step 6: Final Calculations ---
print("\n--- Calculating Final Profit ---")

# Filling Nulls for Non-Orders
cols_to_zero = ['price_usd', 'cogs_usd', 'refund_amount_usd', 'is_refunded']
for col in cols_to_zero:
    master_df[col] = master_df[col].fillna(0)

master_df['is_conversion'] = np.where(master_df['order_id'].notnull(), 1, 0)

# Adjusted Net Profit = Sales - Cost - Refunds
master_df['adjusted_net_profit'] = master_df['price_usd'] - master_df['cogs_usd'] - master_df['refund_amount_usd']

# Helper Columns
master_df['month_year'] = master_df['created_at'].dt.to_period('M').astype(str)
master_df['product_name'] = master_df['product_name'].fillna('No Purchase')

# --- Step 7: Export ---
output_file = 'BearCart_Full_Analytics_With_Refunds.csv'
master_df.to_csv(output_file, index=False)

print(f"\nSUCCESS! File generated: {output_file}")
print(f"Total Refunds Recorded: ${master_df['refund_amount_usd'].sum():,.2f}")
print(f"New Columns Added: 'is_refunded', 'refund_amount_usd', 'adjusted_net_profit'")