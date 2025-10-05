import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import numpy as np

# ---------------------------
# Load Data
# ---------------------------
all_df = pd.read_csv("all_data.csv")
all_df['dteday'] = pd.to_datetime(all_df['dteday'])

# ---------------------------
# Tambahkan lokasi dummy jika kolom lat/lon tidak ada
# ---------------------------
if 'lat' not in all_df.columns or 'lon' not in all_df.columns:
    np.random.seed(42)
    all_df['lat'] = np.random.uniform(-6.25, -6.15, size=len(all_df))
    all_df['lon'] = np.random.uniform(106.80, 106.90, size=len(all_df))
    all_df['station_name'] = all_df.get('station_name', ['Stasiun Dummy']*len(all_df))

# ---------------------------
# Sidebar: Mode
# ---------------------------
st.sidebar.image("images/sepeda.png", width=150)
st.sidebar.title("Bike Sharing Dataset")
mode = st.sidebar.radio("Pilih Mode", ["Light", "Dark"])

# ---------------------------
# Set Theme
# ---------------------------
if mode == "Dark":
    chart_template = "plotly_dark"
    bg_color = "#121212"
    text_color = "#ffffff"
else:
    chart_template = "plotly_white"
    bg_color = "#f5f5f5"
    text_color = "#000000"

# ---------------------------
# Sidebar Filter Tanggal
# ---------------------------
start_date, end_date = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    [all_df['dteday'].min(), all_df['dteday'].max()],
    min_value=all_df['dteday'].min(),
    max_value=all_df['dteday'].max()
)

filtered_df = all_df[(all_df['dteday'] >= pd.to_datetime(start_date)) &
                     (all_df['dteday'] <= pd.to_datetime(end_date))]

# ---------------------------
# Metrics Cards
# ---------------------------
total_rentals = filtered_df['cnt_day'].sum()
avg_per_hour = filtered_df.groupby('hr')['cnt_hour'].mean().mean()
total_days = filtered_df['dteday'].nunique()

st.markdown(f"""
<div style='display:flex; justify-content:space-between; margin-top:10px;'>
    <div style='background-color:{bg_color}; padding:20px; border-radius:10px; width:30%; text-align:center; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);'>
        <h3 style='color:{text_color}'>Total Penyewaan</h3>
        <h2 style='color:{text_color}'>{total_rentals}</h2>
    </div>
    <div style='background-color:{bg_color}; padding:20px; border-radius:10px; width:30%; text-align:center; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);'>
        <h3 style='color:{text_color}'>Rata-rata per Jam</h3>
        <h2 style='color:{text_color}'>{round(avg_per_hour,2)}</h2>
    </div>
    <div style='background-color:{bg_color}; padding:20px; border-radius:10px; width:30%; text-align:center; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);'>
        <h3 style='color:{text_color}'>Jumlah Hari Terdata</h3>
        <h2 style='color:{text_color}'>{total_days}</h2>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Tabs
# ---------------------------
tabs = st.tabs(["📊 Cuaca", "⏰ Jam Penyewaan", "🏆 RFM per Hari", "🌍 Peta Penyewaan"])

# ---- Tab 1: Cuaca ----
with tabs[0]:
    st.subheader("Pengaruh Kondisi Cuaca terhadap Penyewaan Sepeda")
    weather_df = filtered_df.groupby("weathersit_day")['cnt_day'].mean().reset_index()
    fig_weather = px.bar(
        weather_df,
        x="weathersit_day",
        y="cnt_day",
        color="weathersit_day",
        text="cnt_day",
        labels={"weathersit_day":"Kondisi Cuaca", "cnt_day":"Rata-rata Penyewaan"},
        color_discrete_map={1:"#4A90E2", 2:"#F5A623", 3:"#50E3C2"},
        template=chart_template
    )
    fig_weather.update_layout(
        xaxis=dict(tickmode='array', tickvals=[1,2,3],
                   ticktext=["1 - Cerah","2 - Berawan","3 - Hujan"]),
        plot_bgcolor=bg_color, paper_bgcolor=bg_color, font_color=text_color
    )
    st.plotly_chart(fig_weather, use_container_width=True)

# ---- Tab 2: Jam Penyewaan ----
with tabs[1]:
    st.subheader("Rata-rata Penyewaan Sepeda per Jam")
    hour_usage = filtered_df.groupby('hr')['cnt_hour'].mean().reset_index()
    fig_hour = px.line(
        hour_usage,
        x='hr',
        y='cnt_hour',
        markers=True,
        labels={"hr":"Jam", "cnt_hour":"Rata-rata Penyewaan"},
        title="Rata-rata Penyewaan Sepeda per Jam",
        template=chart_template
    )
    fig_hour.update_layout(xaxis=dict(tickmode='linear', dtick=1),
                           plot_bgcolor=bg_color, paper_bgcolor=bg_color, font_color=text_color)
    st.plotly_chart(fig_hour, use_container_width=True)

# ---- Tab 3: RFM per Hari ----
with tabs[2]:
    st.subheader("Analisis RFM per Hari")
    recent_date = filtered_df['dteday'].max()
    rfm_day = filtered_df.groupby('dteday').agg(
        Frequency=('hr','count'),
        Monetary=('cnt_day','sum')
    ).reset_index()
    rfm_day['Recency'] = (recent_date - rfm_day['dteday']).dt.days
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Recency (hari)", round(rfm_day.Recency.mean(),1))
    col2.metric("Avg Frequency", round(rfm_day.Frequency.mean(),2))
    col3.metric("Avg Monetary", round(rfm_day.Monetary.mean(),2))
    
    fig_r = px.line(rfm_day, x='dteday', y='Recency', title='Recency per Hari', labels={"Recency":"Recency (hari)"}, template=chart_template)
    fig_f = px.line(rfm_day, x='dteday', y='Frequency', title='Frequency per Hari', labels={"Frequency":"Jumlah Jam Penyewaan"}, template=chart_template)
    fig_m = px.line(rfm_day, x='dteday', y='Monetary', title='Monetary per Hari', labels={"Monetary":"Total Penyewaan"}, template=chart_template)
    
    st.plotly_chart(fig_r, use_container_width=True)
    st.plotly_chart(fig_f, use_container_width=True)
    st.plotly_chart(fig_m, use_container_width=True)

# ---- Tab 4: Geospatial / Peta Penyewaan ----
with tabs[3]:
    st.subheader("Distribusi Penyewaan Sepeda per Lokasi")

    # Pastikan filtered_df tidak kosong
    if filtered_df.empty:
        st.warning("Data kosong untuk rentang tanggal ini, peta tidak dapat ditampilkan.")
    else:
        # ---------------------------
        # 📊 Clustering jumlah penyewaan (qcut)
        # ---------------------------
        filtered_df['rent_cluster'] = pd.qcut(
            filtered_df['cnt_day'],
            q=3,
            labels=['Rendah', 'Sedang', 'Tinggi']
        )

        # Ringkasan cluster
        st.write("### 📊 Distribusi Lokasi Berdasarkan Cluster Penyewaan")
        cluster_summary = filtered_df['rent_cluster'].value_counts().reset_index()
        cluster_summary.columns = ['Cluster', 'Jumlah Lokasi']
        st.dataframe(cluster_summary)

        # ---------------------------
        # 🌍 Peta Interaktif
        # ---------------------------
        map_center = [filtered_df['lat'].mean(), filtered_df['lon'].mean()]
        tiles_style = "CartoDB dark_matter" if mode == "Dark" else "OpenStreetMap"
        m = folium.Map(location=map_center, zoom_start=13, tiles=tiles_style)

        marker_cluster = MarkerCluster(name="📍 Cluster Lokasi").add_to(m)

        # Warna sesuai cluster
        color_map = {"Rendah": "green", "Sedang": "orange", "Tinggi": "red"}

        for _, row in filtered_df.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=6,
                popup=(f"<b>📍 Stasiun:</b> {row['station_name']}<br>"
                       f"<b>📊 Penyewaan:</b> {row['cnt_day']}<br>"
                       f"<b>📈 Cluster:</b> {row['rent_cluster']}"),
                color=color_map[row['rent_cluster']],
                fill=True,
                fill_opacity=0.7
            ).add_to(marker_cluster)

        # Tambahkan LayerControl untuk kontrol tampilan peta
        folium.LayerControl().add_to(m)

        # Render peta ke Streamlit
        st_folium(m, width=700, height=500)
