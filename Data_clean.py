import pandas as pd
import numpy as np
import os

# --- STEP 1: Files Load Karna ---
# Ensure karein ki ye saari files usi folder me hon jaha ye script hai
try:
    print("Files load ho rahi hain...")
    products = pd.read_csv('products.csv')
    orders = pd.read_csv('orders.csv')
    website_sessions = pd.read_csv('website_sessions.csv')
    print("Sabhi files safaltapurvak load ho gayi hain.")
except FileNotFoundError as e:
    print(f"Error: Koi file missing hai. Kripya check karein: {e}")
    exit()

# --- STEP 2: Website Sessions Cleaning ---
print("\nCleaning Website Sessions...")

# 1. Duplicates remove karna
original_count = len(website_sessions)
website_sessions_cleaned = website_sessions.drop_duplicates().copy()
print(f"- {original_count - len(website_sessions_cleaned)} duplicate sessions remove kiye gaye.")

# 2. UTM tags ko standard karna (lowercase)
# Taki 'Gsearch' aur 'gsearch' ek hi maana jaye
utm_cols = ['utm_source', 'utm_campaign', 'utm_content']
for col in utm_cols:
    website_sessions_cleaned[col] = website_sessions_cleaned[col].str.lower()
print("- UTM tags ko lowercase me convert kiya gaya.")

# 3. Null UTM Sources ko fix karna
# Logic: Agar referer hai toh 'organic', nahi toh 'direct'
def fill_source(row):
    if pd.isnull(row['utm_source']):
        if pd.notnull(row['http_referer']):
            return 'organic'
        else:
            return 'direct'
    return row['utm_source']

website_sessions_cleaned['utm_source'] = website_sessions_cleaned.apply(fill_source, axis=1)
print("- Missing UTM sources ko 'organic' ya 'direct' se fill kiya gaya.")


# --- STEP 3: Orders Data Cleaning ---
print("\nCleaning Orders Data...")

# 1. Missing User IDs ko map karna
# Website session ID se user ID dhundh kar orders table me bharna
session_user_map = website_sessions_cleaned.set_index('website_session_id')['user_id'].to_dict()

missing_users_before = orders['user_id'].isna().sum()
orders['user_id'] = orders['user_id'].fillna(orders['website_session_id'].map(session_user_map))
print(f"- {missing_users_before} orders me missing User IDs ko fix kiya gaya.")

# 2. Null Price/COGS ko Mean value se fill karna
orders['price_usd'] = orders['price_usd'].fillna(orders['price_usd'].mean())
orders['cogs_usd'] = orders['cogs_usd'].fillna(orders['cogs_usd'].mean())
print("- Missing price values ko average se fill kiya gaya.")


# --- STEP 4: Master Sheet Banana (Merging) ---
print("\nCreating Master Sheet...")

# Orders ko Sessions ke saath merge karna (Traffic source janne ke liye)
master_df = pd.merge(
    orders,
    website_sessions_cleaned[['website_session_id', 'utm_source', 'utm_campaign', 'device_type', 'http_referer']],
    on='website_session_id',
    how='left'
)

# Product ka naam add karna
master_df = pd.merge(
    master_df,
    products[['product_id', 'product_name']],
    left_on='primary_product_id',
    right_on='product_id',
    how='left'
)

# --- STEP 5: Export ---
output_filename = 'BearCart_Final_Cleaned_Data.csv'
master_df.to_csv(output_filename, index=False)

print(f"\nSUCCESS! Aapka data clean ho gaya hai.")
print(f"New file save ho gayi hai: {output_filename}")
print(f"Total Rows: {len(master_df)}")