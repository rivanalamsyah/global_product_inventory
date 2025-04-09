import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Inventaris Produk", page_icon="📦", layout="wide")
st.title("📦 Dashboard Inventaris Produk Global")

# Styling Modern
st.markdown("""
    <style>
        .stDataFrame {background-color: white; border-radius: 10px; padding: 10px;}
        section.main > div {padding-top: 2rem;}
        .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# Fungsi Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("global_products_inventory.csv")
    
    # Parsing kolom tanggal
    for date_col in ['Manufacturing Date', 'Expiration Date', 'Last Update']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Tambahan kolom derivatif
    if 'Manufacturing Date' in df.columns:
        df['Manufacturing Year'] = df['Manufacturing Date'].dt.year

    if 'Product Ratings' in df.columns:
        df['Product Ratings'] = pd.to_numeric(df['Product Ratings'], errors='coerce')
    
    if 'Last Update' in df.columns:
        df['Warehouse Last Update'] = df['Last Update']
    else:
        df['Warehouse Last Update'] = pd.Timestamp.today()

    return df

# Load Data
try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# Sidebar Filter
with st.sidebar:
    st.header("🔍 Filter Data")
    kategori = st.multiselect("Kategori Produk", options=df['Product Category'].dropna().unique(), default=df['Product Category'].dropna().unique())
    harga_min = st.number_input("Harga Minimum", min_value=0.0, step=1.0, value=0.0)
    harga_max = st.number_input("Harga Maksimum", min_value=0.0, step=1.0, value=float(df['Price'].max()))
    rating_min = st.slider("Rating Minimum", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
    rating_max = st.slider("Rating Maksimum", min_value=0.0, max_value=5.0, value=5.0, step=0.1)

# Filter Data
filtered_df = df[
    (df['Product Category'].isin(kategori)) &
    (df['Price'] >= harga_min) & (df['Price'] <= harga_max) &
    (df['Product Ratings'] >= rating_min) & (df['Product Ratings'] <= rating_max)
]

if filtered_df.empty:
    st.warning("⚠️ Tidak ada data sesuai filter yang dipilih.")
    st.stop()

# Ringkasan Statistik
st.markdown("## 📊 Ringkasan Statistik")
col1, col2, col3 = st.columns(3)
col1.metric("💰 Rata-rata Harga", f"${filtered_df['Price'].mean():,.2f}")
col2.metric("📦 Total Produk", f"{filtered_df.shape[0]}")
col3.metric("⭐ Rata-rata Rating", f"{filtered_df['Product Ratings'].mean():.2f}")

# Visualisasi Distribusi
st.markdown("## 📁 Distribusi Produk dan Harga")

category_counts = filtered_df['Product Category'].value_counts().reset_index()
category_counts.columns = ['Product Category', 'count']
fig_cat = px.bar(category_counts, x='Product Category', y='count', color='Product Category',
                 labels={'Product Category': 'Kategori', 'count': 'Jumlah'},
                 title="Jumlah Produk per Kategori",
                 color_discrete_sequence=px.colors.qualitative.Set2)
fig_cat.update_layout(template='plotly_white', legend_title="Kategori", title_x=0.5)
st.plotly_chart(fig_cat, use_container_width=True)


# Visualisasi Stok Waktu
st.markdown("---")
st.markdown("## 📈 Visualisasi Lanjutan")

# Heatmap Stok
if 'Warehouse Location' in df.columns:
    heatmap_df = df.groupby(['Warehouse Location', 'Product Category'])['Stock Quantity'].sum().reset_index()
    pivot = heatmap_df.pivot(index='Warehouse Location', columns='Product Category', values='Stock Quantity')
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='YlGnBu',
        hoverongaps=False
    ))
    fig_heatmap.update_layout(title='Heatmap Stok per Lokasi dan Kategori', template='plotly_white', title_x=0.5)
    st.plotly_chart(fig_heatmap, use_container_width=True)

# Boxplot Harga per Kategori
fig_box = px.box(filtered_df, x='Product Category', y='Price', color='Product Category',
                 title="Distribusi Harga per Kategori",
                 labels={"Product Category": "Kategori", "Price": "Harga"},
                 color_discrete_sequence=px.colors.qualitative.Pastel)
fig_box.update_layout(template='plotly_white', title_x=0.5)
st.plotly_chart(fig_box, use_container_width=True)

# Analisis Penjualan Potensial
st.markdown("---")
st.markdown("## 📊 Analisis Penjualan Potensial")

# Produk dengan Stok Rendah
top_products = df.sort_values(by='Stock Quantity').head(10)
fig_top = px.bar(top_products, x='Product Name', y='Stock Quantity', color='Product Category',
                 title="📉 Produk dengan Stok Rendah (Berpotensi Laris)",
                 labels={'Stock Quantity': 'Jumlah Stok'},
                 color_discrete_sequence=px.colors.qualitative.Prism)
fig_top.update_layout(xaxis_tickangle=-45, template='plotly_white', title_x=0.5)
st.plotly_chart(fig_top, use_container_width=True)

# Segmentasi Fast-Moving
median_stock = df['Stock Quantity'].median()
fast_moving = df[df['Stock Quantity'] < median_stock]
fig_fast = px.histogram(fast_moving, x='Product Category', color='Product Category',
                        title="🚀 Produk Fast-Moving Berdasarkan Kategori",
                        labels={'count': 'Jumlah Produk'},
                        color_discrete_sequence=px.colors.qualitative.Set3)
fig_fast.update_layout(template='plotly_white', title_x=0.5)
st.plotly_chart(fig_fast, use_container_width=True)

# Tabel dan Tombol Download
st.markdown("---")
st.markdown("## 📄 Tabel Produk Tersaring")
st.dataframe(filtered_df[['Product Name', 'Product Category', 'Price', 'Stock Quantity', 'Product Ratings']], use_container_width=True)

st.download_button("⬇️ Unduh Data CSV", filtered_df.to_csv(index=False), file_name="filtered_inventory.csv", mime="text/csv")
