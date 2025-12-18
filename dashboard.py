import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="BearCart Business Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# PROFESSIONAL LIGHT THEME CSS
# ======================================================
st.markdown("""
    <style>
    .stApp { 
        background-color: #ffffff !important; 
        color: #1a1a2e !important; 
    }
    [data-testid="stMetric"] { 
        border: 1px solid #e0e0e0; 
        padding: 24px; 
        border-radius: 8px; 
        background-color: #fafafa; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    [data-testid="stMetricValue"] { 
        color: #0066cc !important; 
        font-size: 2rem !important; 
        font-weight: 700 !important; 
    }
    [data-testid="stMetricLabel"] { 
        color: #444444 !important; 
        font-size: 0.95rem !important; 
        text-transform: uppercase; 
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    h1, h2, h3, h4, h5, h6 { 
        color: #1a1a2e !important; 
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #f5f5f5 !important;
    }
    [data-testid="stSidebar"] * {
        color: #1a1a2e !important;
    }
    hr {
        border-top: 1px solid #e0e0e0;
    }
    /* Force Plotly text to be dark */
    .js-plotly-plot .plotly text {
        fill: #1a1a2e !important;
    }
    .js-plotly-plot .plotly .gtitle, 
    .js-plotly-plot .plotly .xtitle,
    .js-plotly-plot .plotly .ytitle {
        fill: #1a1a2e !important;
    }
    </style>
""", unsafe_allow_html=True)

# Chart styling
chart_template = "plotly_white"
primary_color = "#0066cc"
secondary_color = "#00a86b"
accent_color = "#ff6b35"
neutral_color = "#6c757d"

# ======================================================
# DATA LOAD
# ======================================================
@st.cache_data
def load_data():
    df = pd.read_csv("BearCart_Full_Analytics_With_Refunds.csv")
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    df["is_conversion"] = pd.to_numeric(df["is_conversion"], errors="coerce")
    return df

df = load_data()

# ======================================================
# SIDEBAR FILTERS
# ======================================================
st.sidebar.title("Filters")
st.sidebar.markdown("---")

# Date Range Filter
st.sidebar.subheader("Date Range")
min_date = df["created_at"].min().date()
max_date = df["created_at"].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Device Filter
st.sidebar.subheader("Device Type")
device_options = ["All"] + df["device_type"].dropna().unique().tolist()
selected_device = st.sidebar.selectbox("Select Device", device_options)

# Source Filter
st.sidebar.subheader("Marketing Source")
source_options = ["All"] + df["utm_source"].dropna().unique().tolist()
selected_source = st.sidebar.selectbox("Select Source", source_options)

# Apply Filters
filtered_df = df.copy()

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["created_at"].dt.date >= date_range[0]) & 
        (filtered_df["created_at"].dt.date <= date_range[1])
    ]

if selected_device != "All":
    filtered_df = filtered_df[filtered_df["device_type"] == selected_device]

if selected_source != "All":
    filtered_df = filtered_df[filtered_df["utm_source"] == selected_source]

orders_df = filtered_df[filtered_df["is_conversion"] == 1].drop_duplicates(subset="order_id")

# ======================================================
# HEADER
# ======================================================
st.title("BearCart Business Analytics")
st.caption("Strategic Operations and Financial Performance Overview")
st.markdown("---")

# ======================================================
# LAYER 1: KPI METRICS
# ======================================================
st.subheader("Executive Summary")

# KPI Calculations
total_revenue = orders_df["price_usd"].sum()
total_profit = orders_df["adjusted_net_profit"].sum() if "adjusted_net_profit" in orders_df.columns else 0
total_orders = orders_df["order_id"].nunique()
aov = (total_revenue / total_orders) if total_orders > 0 else 0
total_traffic = filtered_df["website_session_id"].nunique()
conversion_rate = (total_orders / total_traffic * 100) if total_traffic > 0 else 0
items_sold = int(orders_df["items_purchased"].sum()) if "items_purchased" in orders_df.columns else 0
total_refunds = orders_df["refund_amount_usd"].sum() if "refund_amount_usd" in orders_df.columns else 0

# Display 8 KPIs in 2 rows of 4
row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
row1_c1.metric("Total Revenue", f"${total_revenue:,.2f}")
row1_c2.metric("Total Profit", f"${total_profit:,.2f}")
row1_c3.metric("Total Orders", f"{total_orders:,}")
row1_c4.metric("Avg Order Value", f"${aov:,.2f}")

row2_c1, row2_c2, row2_c3, row2_c4 = st.columns(4)
row2_c1.metric("Total Traffic", f"{total_traffic:,}")
row2_c2.metric("Conversion Rate", f"{conversion_rate:.2f}%")
row2_c3.metric("Items Sold", f"{items_sold:,}")
row2_c4.metric("Estimated Refunds", f"${total_refunds:,.2f}")

st.markdown("---")

# ======================================================
# LAYER 2: TRENDS & STRATEGY
# ======================================================
st.subheader("Trends and Strategy Analysis")

# Chart 1: Monthly Sales Trend (Full Width)
st.markdown("#### Monthly Sales Trend")

monthly_sales = orders_df.groupby(
    orders_df["created_at"].dt.to_period("M")
)["price_usd"].sum().reset_index()
monthly_sales["created_at"] = monthly_sales["created_at"].astype(str)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=monthly_sales["created_at"],
    y=monthly_sales["price_usd"],
    mode="lines+markers",
    name="Revenue",
    line=dict(color=primary_color, width=3),
    marker=dict(size=10, color=primary_color),
    fill="tozeroy",
    fillcolor="rgba(0, 102, 204, 0.1)"
))
fig_trend.update_layout(
    template=chart_template,
    xaxis_title="Month",
    yaxis_title="Revenue (USD)",
    hovermode="x unified",
    height=500,
    font=dict(size=14, color="#1a1a2e"),
    xaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
    yaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), tickformat="$,.0f", linecolor="#cccccc", gridcolor="#eeeeee"),
    margin=dict(l=60, r=40, t=40, b=60),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff"
)
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("")

# Two column charts
col1, col2 = st.columns(2)

# Chart 2: Revenue by Marketing Channel
with col1:
    st.markdown("#### Revenue by Marketing Channel")
    
    channel_revenue = orders_df.groupby("utm_source")["price_usd"].sum().reset_index()
    channel_revenue = channel_revenue.sort_values("price_usd", ascending=True)
    
    fig_channel = go.Figure()
    fig_channel.add_trace(go.Bar(
        x=channel_revenue["price_usd"],
        y=channel_revenue["utm_source"],
        orientation="h",
        marker=dict(color=primary_color),
        text=[f"${x:,.0f}" for x in channel_revenue["price_usd"]],
        textposition="outside",
        textfont=dict(size=12)
    ))
    fig_channel.update_layout(
        template=chart_template,
        xaxis_title="Revenue (USD)",
        yaxis_title="Marketing Source",
        height=450,
        font=dict(size=14, color="#1a1a2e"),
        xaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
        yaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc"),
        margin=dict(l=100, r=80, t=40, b=60),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )
    st.plotly_chart(fig_channel, use_container_width=True)

# Chart 3: Monthly Orders Trend
with col2:
    st.markdown("#### Monthly Orders Volume")
    
    monthly_orders = orders_df.groupby(
        orders_df["created_at"].dt.to_period("M")
    )["order_id"].nunique().reset_index()
    monthly_orders["created_at"] = monthly_orders["created_at"].astype(str)
    
    fig_orders = go.Figure()
    fig_orders.add_trace(go.Bar(
        x=monthly_orders["created_at"],
        y=monthly_orders["order_id"],
        marker_color=secondary_color,
        text=monthly_orders["order_id"],
        textposition="outside",
        textfont=dict(size=12)
    ))
    fig_orders.update_layout(
        template=chart_template,
        xaxis_title="Month",
        yaxis_title="Number of Orders",
        height=450,
        font=dict(size=14, color="#1a1a2e"),
        xaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
        yaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
        margin=dict(l=60, r=40, t=40, b=60),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )
    st.plotly_chart(fig_orders, use_container_width=True)

st.markdown("")

# Chart: Monthly Refunds Trend (Full Width)
st.markdown("#### Monthly Refunds Trend")

monthly_refunds = orders_df.groupby(
    orders_df["created_at"].dt.to_period("M")
)["refund_amount_usd"].sum().reset_index()
monthly_refunds["created_at"] = monthly_refunds["created_at"].astype(str)

fig_refunds = go.Figure()
fig_refunds.add_trace(go.Bar(
    x=monthly_refunds["created_at"],
    y=monthly_refunds["refund_amount_usd"],
    marker_color="#d93025",
    text=[f"${x:,.0f}" for x in monthly_refunds["refund_amount_usd"]],
    textposition="outside",
    textfont=dict(size=11, color="#1a1a2e"),
    name="Refunds"
))
fig_refunds.update_layout(
    template=chart_template,
    xaxis_title="Month",
    yaxis_title="Refund Amount (USD)",
    height=450,
    font=dict(size=14, color="#1a1a2e"),
    xaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
    yaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), tickformat="$,.0f", linecolor="#cccccc", gridcolor="#eeeeee"),
    margin=dict(l=60, r=40, t=40, b=60),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff"
)
st.plotly_chart(fig_refunds, use_container_width=True)

st.markdown("---")

# ======================================================
# LAYER 3: DEEP DIVE INSIGHTS
# ======================================================
st.subheader("Deep Dive Insights")

col3, col4 = st.columns(2)

# Chart 4: Device Performance
with col3:
    st.markdown("#### Device Performance Analysis")
    
    device_stats = filtered_df.groupby("device_type").agg({
        "is_conversion": ["sum", "count"]
    }).reset_index()
    device_stats.columns = ["device_type", "conversions", "sessions"]
    device_stats["conversion_rate"] = (device_stats["conversions"] / device_stats["sessions"] * 100)
    
    fig_device = go.Figure()
    fig_device.add_trace(go.Pie(
        labels=device_stats["device_type"],
        values=device_stats["conversions"],
        hole=0.5,
        marker=dict(colors=[primary_color, secondary_color, accent_color, neutral_color]),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=14),
        hovertemplate="<b>%{label}</b><br>Conversions: %{value:,}<br>Share: %{percent}<extra></extra>"
    ))
    fig_device.update_layout(
        template=chart_template,
        height=500,
        showlegend=True,
        font=dict(size=14, color="#1a1a2e"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, font=dict(size=12, color="#1a1a2e")),
        margin=dict(l=40, r=40, t=40, b=80),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )
    st.plotly_chart(fig_device, use_container_width=True)
    
    # Conversion Rate Table
    st.markdown("**Conversion Rate by Device**")
    device_table = device_stats[["device_type", "sessions", "conversions", "conversion_rate"]].copy()
    device_table.columns = ["Device", "Sessions", "Conversions", "Conversion Rate (%)"]
    device_table["Conversion Rate (%)"] = device_table["Conversion Rate (%)"].round(2)
    st.dataframe(device_table, hide_index=True, use_container_width=True)

# Chart 5: Top Products
with col4:
    st.markdown("#### Top Products by Revenue")
    
    product_sales = orders_df.groupby("product_name").agg({
        "items_purchased": "sum",
        "price_usd": "sum"
    }).reset_index()
    product_sales = product_sales.sort_values("price_usd", ascending=True).tail(10)
    
    fig_products = go.Figure()
    fig_products.add_trace(go.Bar(
        x=product_sales["price_usd"],
        y=product_sales["product_name"],
        orientation="h",
        marker=dict(color=accent_color),
        text=[f"${x:,.0f}" for x in product_sales["price_usd"]],
        textposition="outside",
        textfont=dict(size=12)
    ))
    fig_products.update_layout(
        template=chart_template,
        xaxis_title="Revenue (USD)",
        yaxis_title="Product",
        height=500,
        font=dict(size=14, color="#1a1a2e"),
        xaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
        yaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc"),
        margin=dict(l=150, r=80, t=40, b=60),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )
    st.plotly_chart(fig_products, use_container_width=True)

st.markdown("---")

# ======================================================
# CHANNEL PERFORMANCE ANALYSIS
# ======================================================
st.subheader("Channel Performance Analysis")

st.markdown("#### Sessions vs Conversion Rate by Source")

source_analysis = filtered_df.groupby("utm_source").agg({
    "website_session_id": "nunique",
    "is_conversion": "sum"
}).reset_index()
source_analysis.columns = ["utm_source", "sessions", "conversions"]
source_analysis["conversion_rate"] = (source_analysis["conversions"] / source_analysis["sessions"] * 100)
source_analysis = source_analysis.sort_values("sessions", ascending=False)

fig_source = go.Figure()
fig_source.add_trace(go.Bar(
    name="Sessions",
    x=source_analysis["utm_source"],
    y=source_analysis["sessions"],
    marker_color=primary_color,
    yaxis="y",
    text=source_analysis["sessions"],
    textposition="outside",
    textfont=dict(size=11)
))
fig_source.add_trace(go.Scatter(
    name="Conversion Rate (%)",
    x=source_analysis["utm_source"],
    y=source_analysis["conversion_rate"],
    mode="lines+markers+text",
    marker=dict(color=accent_color, size=12),
    line=dict(color=accent_color, width=3),
    yaxis="y2",
    text=[f"{x:.1f}%" for x in source_analysis["conversion_rate"]],
    textposition="top center",
    textfont=dict(size=11, color=accent_color)
))
fig_source.update_layout(
    template=chart_template,
    xaxis_title="Marketing Source",
    yaxis=dict(title="Sessions", side="left", tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc", gridcolor="#eeeeee"),
    yaxis2=dict(title="Conversion Rate (%)", side="right", overlaying="y", tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e")),
    height=500,
    font=dict(size=14, color="#1a1a2e"),
    xaxis=dict(tickfont=dict(size=12, color="#1a1a2e"), title_font=dict(color="#1a1a2e"), linecolor="#cccccc"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12, color="#1a1a2e")),
    margin=dict(l=60, r=60, t=60, b=60),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff"
)
st.plotly_chart(fig_source, use_container_width=True)

st.markdown("---")

# ======================================================
# DATA TABLE
# ======================================================
with st.expander("View Raw Data"):
    st.dataframe(
        orders_df[["order_id", "created_at", "product_name", "price_usd", "items_purchased", "utm_source", "device_type"]].head(100),
        hide_index=True,
        use_container_width=True
    )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d; padding: 20px;'>
        <p><strong>BearCart Analytics Dashboard</strong></p>
        <p style='font-size: 0.9rem;'>Data-driven insights for strategic decision making</p>
    </div>
    """,
    unsafe_allow_html=True
)
