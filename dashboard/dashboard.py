# Codingan Dashboard Streamlit
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

# 1. Helper Functions
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return daily_orders_df

def create_monthly_orders_df(df):
    monthly_df = df.resample(rule='M', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    monthly_df = monthly_df.sort_values("order_purchase_timestamp").tail(12)
    
    monthly_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return monthly_df

def create_bycategory_review_df(df):
    category_review_df = df.groupby("product_category_name_english").review_score.mean().sort_values(ascending=True).reset_index()
    return category_review_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_unique_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_unique_id": "customer_count"
    }, inplace=True)
    return bystate_df

def create_product_performance_df(df):
    product_performance_df = df.groupby("product_category_name_english").agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    product_performance_df.rename(columns={
        "order_id": "quantity",
        "price": "revenue"
    }, inplace=True)
    return product_performance_df

def create_rfm_df(df):
    snapshot_date = df['order_purchase_timestamp'].max() + pd.DateOffset(days=1)
    rfm_df = df.groupby('customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
        'order_id': 'nunique',
        'price': 'sum'
    }).reset_index()
    rfm_df.columns = ['customer_id', 'recency', 'frequency', 'monetary']

    rfm_df['r_rank'] = rfm_df['recency'].rank(ascending=False)
    rfm_df['f_rank'] = rfm_df['frequency'].rank(ascending=True)
    rfm_df['m_rank'] = rfm_df['monetary'].rank(ascending=True)

    rfm_df['RFM_score'] = (0.15 * (rfm_df['r_rank']/rfm_df['r_rank'].max())*100) + \
                          (0.28 * (rfm_df['f_rank']/rfm_df['f_rank'].max())*100) + \
                          (0.57 * (rfm_df['m_rank']/rfm_df['m_rank'].max())*100)
    rfm_df['RFM_score'] *= 0.05
    rfm_df = rfm_df.round(2)
    return rfm_df

def create_rfm_segment(df):
    def segment_weighted(score):
        if score > 4.5:
            return 'Top Customers'
        elif score > 4:
            return 'High Value Customers'
        elif score > 3:
            return 'Medium Value Customers'
        elif score > 1.6:
            return 'Low Value Customers'
        else:
            return 'Lost Customers'
            
    df['customer_segment'] = df['RFM_score'].apply(segment_weighted)
    segment_counts = df['customer_segment'].value_counts().reset_index()
    segment_counts.columns = ['customer_segment', 'customer_count']
    return segment_counts

# 2. Load Data
all_df = pd.read_csv("all_data.csv")

datetime_columns = ["order_purchase_timestamp"]
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

# 3. Sidebar Filter
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.title("E-Commerce Dashboard")
    # Ganti URL logo jika perlu
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) &
                 (all_df["order_purchase_timestamp"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
monthly_orders_df = create_monthly_orders_df(main_df)
category_review_df = create_bycategory_review_df(main_df)
bystate_df = create_bystate_df(main_df)
product_performance_df = create_product_performance_df(main_df)
rfm_df = create_rfm_df(main_df)
rfm_segments = create_rfm_segment(rfm_df)

# 4. Main Dashboard
st.header('E-Commerce Performance Dashboard :sparkles:')

# Tampilkan pendapatan dan order
st.subheader('Daily Orders & Revenue')
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Orders", value=daily_orders_df.order_count.sum())
with col2:
    total_rev = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_rev)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"], marker='o', linewidth=2, color="#90CAF9")
st.pyplot(fig)

# Pertanyaan 1
st.subheader('Monthly Orders & Revenue Trend (Last 12 Months)')

col1, col2 = st.columns(2)
with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total Orders (Last 12 Months)", value=total_orders)

with col2:
    total_rev = format_currency(monthly_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue (Last 12 Months)", value=total_rev)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_orders_df["order_purchase_timestamp"].dt.strftime('%B %Y'), # Format nama bulan
    monthly_orders_df["order_count"], 
    marker='o', 
    linewidth=3, 
    color="#90CAF9"
)

for x, y in zip(range(len(monthly_orders_df)), monthly_orders_df["order_count"]):
    ax.text(x, y, str(y), color="black", fontsize=12, ha="center", va="bottom")

ax.set_title("Trend of Total Orders per Month", fontsize=20)
ax.tick_params(axis='x', rotation=45, labelsize=15)
ax.tick_params(axis='y', labelsize=15)
ax.grid(True, linestyle='--', alpha=0.5)

st.pyplot(fig)

# Pertanyaan 2 dan 4
st.subheader("Product Category Performance")
tab1, tab2 = st.tabs(["Review Score", "Sales Performance"])

with tab1:
    st.write("Kategori dengan Kepuasan Terendah")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x="review_score", y="product_category_name_english", data=category_review_df.head(10), palette="Reds_r")
    st.pyplot(fig)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.write("Top 5 by Revenue")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x="revenue", y="product_category_name_english", data=product_performance_df.sort_values("revenue", ascending=False).head(5), palette="Blues_r")
        st.pyplot(fig)
    with col2:
        st.write("Top 5 by Quantity")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x="quantity", y="product_category_name_english", data=product_performance_df.sort_values("quantity", ascending=False).head(5), palette="GnBu_r")
        st.pyplot(fig)

# Pertanyaan 3
st.subheader("Customer Geographics")
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x="customer_count", y="customer_state", data=bystate_df.sort_values("customer_count", ascending=False).head(10), palette="viridis")
st.pyplot(fig)

# RFM Analysis
st.subheader("Best Customer Based on RFM Parameters")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Recency (days)", value=round(rfm_df.recency.mean(), 1))
with col2:
    st.metric("Avg Frequency", value=round(rfm_df.frequency.mean(), 2))
with col3:
    st.metric("Avg Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

# Visualisasi Top 5 Customers per RFM
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 15)) # Figsize ditinggikan sedikit untuk ruang teks

colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Customer ID", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35, rotation=90) # ROTASI 90 DERAJAT

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Customer ID", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35, rotation=90) # ROTASI 90 DERAJAT

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("Customer ID", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35, rotation=90) # ROTASI 90 DERAJAT

st.pyplot(fig)

st.write("### Customer Segment Distribution")
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(
    x="customer_count", 
    y="customer_segment", 
    data=rfm_segments.sort_values(by="customer_count", ascending=False),
    palette="magma",
    ax=ax
)
ax.set_title("Customer Segmentation based on Weighted RFM Score", fontsize=15)
ax.set_xlabel("Number of Customers")
ax.set_ylabel(None)

st.pyplot(fig)

st.caption('Copyright © Nurya Dashboard 2026')