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
    print(f"Error: {e}. Please check filenames.")
    exit()

# --- Step 2: Advanced Cleaning (Sessions) ---
print("\n--- Step 2: Cleaning Sessions & Fixing UTMs ---")

# 1. Deduplication
website_sessions_clean = website_sessions.drop_duplicates().copy()

# 2. Date Conversion (Fix for Monthly/Daily Trends)
website_sessions_clean['created_at'] = pd.to_datetime(website_sessions_clean['created_at'])

# 3. Standardization (Lowercase UTMs)
for col in ['utm_source', 'utm_campaign', 'utm_content']:
    website_sessions_clean[col] = website_sessions_clean[col].str.lower()

# 4. Smart Filling of Null UTM Sources
# Logic: Referer hai toh 'organic', nahi toh 'direct'
def fill_smart_source(row):
    if pd.isnull(row['utm_source']):
        if pd.notnull(row['http_referer']):
            return 'organic'
        else:
            return 'direct'
    return row['utm_source']

website_sessions_clean['utm_source'] = website_sessions_clean.apply(fill_smart_source, axis=1)

# 5. Fix Remaining Nulls (Explicit 'unknown' label)
website_sessions_clean['utm_source'] = website_sessions_clean['utm_source'].fillna('unknown')
website_sessions_clean['utm_campaign'] = website_sessions_clean['utm_campaign'].fillna('uncategorized')

print("Sessions cleaned. Dates converted. Nulls handled.")


# --- Step 3: Cleaning Orders ---
print("\n--- Step 3: Cleaning Orders & Financials ---")

# 1. Date Conversion
orders['created_at'] = pd.to_datetime(orders['created_at'])

# 2. Fixing Missing User IDs (Map from Sessions)
session_user_map = website_sessions_clean.set_index('website_session_id')['user_id'].to_dict()
orders['user_id'] = orders['user_id'].fillna(orders['website_session_id'].map(session_user_map))

# 3. Fixing Null Financials
orders['price_usd'] = orders['price_usd'].fillna(orders['price_usd'].mean())


# --- Step 4: Creating the "Full Funnel" Master Sheet ---
print("\n--- Step 4: Merging for Conversion Analysis ---")

# Critical Change: We use a LEFT JOIN starting from SESSIONS.
# This keeps ALL traffic data (even if no purchase happened), allowing Conversion Rate calculation.
master_df = pd.merge(
    website_sessions_clean,
    orders[['website_session_id', 'order_id', 'price_usd', 'items_purchased', 'primary_product_id']],
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

# --- Step 5: Feature Engineering for Dashboard ---
print("\n--- Step 5: Adding Helper Columns ---")

# 1. Conversion Flag (1 = Order Placed, 0 = No Order)
# Dashboard mein bas is column ka Average nikalne se Conversion Rate mil jayega!
master_df['is_conversion'] = np.where(master_df['order_id'].notnull(), 1, 0)

# 2. Extract Month-Year for easy plotting
master_df['month_year'] = master_df['created_at'].dt.to_period('M').astype(str)

# 3. Clean up columns (Fill product info for non-orders)
master_df['product_name'] = master_df['product_name'].fillna('No Purchase')
master_df['price_usd'] = master_df['price_usd'].fillna(0)


# --- Step 6: Export ---
output_file = 'BearCart_Full_Analytics_Optimized.csv'
master_df.to_csv(output_file, index=False)

print(f"\nSUCCESS! File saved as: {output_file}")
print(f"Total Rows: {len(master_df)} (Includes ALL sessions)")
print(f"Conversion Rate Ready: Use the 'is_conversion' column.")