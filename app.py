import streamlit as st
import pandas as pd
import plotly.express as px


# ============================================================
# 1. PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="LankaMart Retail Dashboard",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# 2. LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    df = pd.read_csv("CIT308_LankaMart_Retail_Transactions.csv")

    # Convert date column
    df["order_date"] = pd.to_datetime(df["order_date"])

    # Standardise product category spelling
    df["product_category"] = df["product_category"].replace(
        {"electronic": "Electronics"}
    )

    # Remove exact duplicate records
    df = df.drop_duplicates()

    # Create calculated fields
    df["profit_margin"] = (
        df["profit_lkr"] / df["revenue_lkr"] * 100
    )

    df["return_flag"] = (
        df["returned"].astype(str).str.lower() == "yes"
    )

    # Missing ratings are kept as missing.
    # We do not invent rating values.
    return df


df = load_data()


# ============================================================
# 3. TITLE
# ============================================================

st.title("📊 LankaMart Retail Performance Dashboard")

st.markdown(
    """
    **Management Question:**  
    How is LankaMart performing, where are the main risks or opportunities,
    and what action should management consider?
    """
)


# ============================================================
# 4. SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🎛️ Dashboard Filters")

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

province_options = sorted(df["province"].dropna().unique())

selected_provinces = st.sidebar.multiselect(
    "Province",
    options=province_options,
    default=province_options
)

category_options = sorted(
    df["product_category"].dropna().unique()
)

selected_categories = st.sidebar.multiselect(
    "Product Category",
    options=category_options,
    default=category_options
)


# ============================================================
# 5. RESET FILTERS
# ============================================================

if st.sidebar.button("🔄 Reset Filters"):
    st.rerun()


# ============================================================
# 6. APPLY FILTERS
# ============================================================

if len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])

    filtered_df = df[
        (df["order_date"] >= start_date)
        & (df["order_date"] <= end_date)
        & (df["province"].isin(selected_provinces))
        & (df["product_category"].isin(selected_categories))
    ].copy()

else:
    filtered_df = df.copy()


# ============================================================
# 7. HANDLE EMPTY RESULTS
# ============================================================

if filtered_df.empty:

    st.warning(
        "No transactions match the selected filters. "
        "Please change the filters."
    )

    st.stop()


# ============================================================
# 8. KPI CALCULATIONS
# ============================================================

total_revenue = filtered_df["revenue_lkr"].sum()

total_profit = filtered_df["profit_lkr"].sum()

profit_margin = (
    total_profit / total_revenue * 100
    if total_revenue != 0
    else 0
)

return_rate = (
    filtered_df["return_flag"].mean() * 100
)


# ============================================================
# 9. KPI CARDS
# ============================================================

st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Revenue",
        f"LKR {total_revenue:,.0f}"
    )

with col2:
    st.metric(
        "Total Profit",
        f"LKR {total_profit:,.0f}"
    )

with col3:
    st.metric(
        "Profit Margin",
        f"{profit_margin:.2f}%"
    )

with col4:
    st.metric(
        "Return Rate",
        f"{return_rate:.2f}%"
    )


# ============================================================
# 10. MONTHLY REVENUE & PROFIT TREND
# ============================================================

st.subheader("📈 Monthly Revenue and Profit Trend")

monthly = (
    filtered_df
    .assign(month=filtered_df["order_date"].dt.to_period("M").astype(str))
    .groupby("month", as_index=False)
    .agg(
        Revenue=("revenue_lkr", "sum"),
        Profit=("profit_lkr", "sum")
    )
)

monthly_long = monthly.melt(
    id_vars="month",
    value_vars=["Revenue", "Profit"],
    var_name="Metric",
    value_name="Amount"
)

fig_trend = px.line(
    monthly_long,
    x="month",
    y="Amount",
    color="Metric",
    markers=True,
    title="Monthly Revenue and Profit"
)

fig_trend.update_yaxes(
    tickprefix="LKR ",
    separatethousands=True
)

st.plotly_chart(
    fig_trend,
    use_container_width=True
)


# ============================================================
# 11. CATEGORY COMPARISON
# ============================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("🛍️ Revenue by Product Category")

    category_sales = (
        filtered_df
        .groupby("product_category", as_index=False)
        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )
        .sort_values("Revenue", ascending=False)
    )

    fig_category = px.bar(
        category_sales,
        x="product_category",
        y="Revenue",
        text_auto=".2s",
        title="Revenue by Product Category"
    )

    fig_category.update_yaxes(
        tickprefix="LKR ",
        separatethousands=True
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )


# ============================================================
# 12. PROVINCE COMPARISON
# ============================================================

with col2:

    st.subheader("🗺️ Revenue by Province")

    province_sales = (
        filtered_df
        .groupby("province", as_index=False)
        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )
        .sort_values("Revenue", ascending=False)
    )

    fig_province = px.bar(
        province_sales,
        x="Revenue",
        y="province",
        orientation="h",
        text_auto=".2s",
        title="Revenue by Province"
    )

    fig_province.update_xaxes(
        tickprefix="LKR ",
        separatethousands=True
    )

    st.plotly_chart(
        fig_province,
        use_container_width=True
    )


# ============================================================
# 13. RELATIONSHIP VIEW
# ============================================================

st.subheader("🔗 Delivery Days vs Profit")

fig_scatter = px.scatter(
    filtered_df,
    x="delivery_days",
    y="profit_lkr",
    color="product_category",
    hover_data=[
        "order_id",
        "province",
        "sales_channel",
        "revenue_lkr",
        "returned"
    ],
    title="Relationship Between Delivery Days and Profit"
)

fig_scatter.update_yaxes(
    tickprefix="LKR ",
    separatethousands=True
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)


# ============================================================
# 14. RETURN RATE BY CATEGORY
# ============================================================

st.subheader("⚠️ Return Rate by Product Category")

return_category = (
    filtered_df
    .groupby("product_category", as_index=False)
    .agg(
        Return_Rate=("return_flag", "mean"),
        Orders=("return_flag", "count")
    )
)

return_category["Return_Rate"] = (
    return_category["Return_Rate"] * 100
)

return_category = return_category.sort_values(
    "Return_Rate",
    ascending=False
)

fig_return = px.bar(
    return_category,
    x="product_category",
    y="Return_Rate",
    text=return_category["Return_Rate"].map(
        lambda x: f"{x:.1f}%"
    ),
    title="Return Rate by Product Category"
)

fig_return.update_yaxes(
    ticksuffix="%"
)

st.plotly_chart(
    fig_return,
    use_container_width=True
)


# ============================================================
# 15. DETAILED TRANSACTION TABLE
# ============================================================

st.subheader("📋 Detailed Transaction Data")

display_columns = [
    "order_id",
    "order_date",
    "province",
    "sales_channel",
    "product_category",
    "revenue_lkr",
    "profit_lkr",
    "delivery_days",
    "returned",
    "customer_rating"
]

available_columns = [
    col for col in display_columns
    if col in filtered_df.columns
]

st.dataframe(
    filtered_df[available_columns]
    .sort_values("order_date", ascending=False),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 16. MANAGEMENT INSIGHTS
# ============================================================

st.subheader("💡 Management Insights")

# Highest revenue category
highest_category = (
    category_sales
    .sort_values("Revenue", ascending=False)
    .iloc[0]
)

# Highest revenue province
highest_province = (
    province_sales
    .sort_values("Revenue", ascending=False)
    .iloc[0]
)

# Highest return category
highest_return_category = (
    return_category
    .sort_values("Return_Rate", ascending=False)
    .iloc[0]
)

st.markdown(
    f"""
    **1. Revenue opportunity:**  
    **{highest_category['product_category']}** generates the highest revenue
    among the selected transactions, with approximately
    **LKR {highest_category['Revenue']:,.0f}**.

    **2. Geographical performance:**  
    **{highest_province['province']}** records the highest revenue among the
    selected provinces, at approximately
    **LKR {highest_province['Revenue']:,.0f}**.

    **3. Return risk:**  
    **{highest_return_category['product_category']}** has the highest return
    rate among the selected categories, at approximately
    **{highest_return_category['Return_Rate']:.2f}%**.
    """
)


# ============================================================
# 17. DATA QUALITY / TECHNICAL NOTE
# ============================================================

with st.expander("🔎 Data Preparation Notes"):

    st.write(
        f"Number of transactions after duplicate removal: "
        f"**{len(df):,}**"
    )

    st.write(
        f"Date range: **{df['order_date'].min().date()}** "
        f"to **{df['order_date'].max().date()}**"
    )

    st.write(
        "The product category value 'electronic' was standardised "
        "to 'Electronics'."
    )

    st.write(
        "Missing customer ratings were retained as missing rather "
        "than assigning artificial values."
    )

    st.write(
        "Exact duplicate records were removed programmatically."
    )