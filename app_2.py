import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ventas por Plataforma y Año", layout="wide")

st.title("📊 Ventas por Plataforma y Año (CSV)")

st.write(
    "Sube un CSV con columnas tipo: `Platform`, `Year` y `Global_Sales` "
    "(como el dataset de ventas de videojuegos)."
)

uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)

    # Normalización básica de columnas esperadas
    required_cols = {"Platform", "Year", "Global_Sales"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

    # Year puede venir como float (ej. 2006.0) -> lo pasamos a entero si es posible
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)

    # Global_Sales a numérico
    df["Global_Sales"] = pd.to_numeric(df["Global_Sales"], errors="coerce").fillna(0)

    return df

if not uploaded_file:
    st.info("⬆️ Sube un CSV para empezar.")
    st.stop()

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"Error leyendo el CSV: {e}")
    st.stop()

# ---- Sidebar filtros ----
st.sidebar.header("Filtros")

platforms = sorted(df["Platform"].dropna().unique().tolist())
years = sorted(df["Year"].dropna().unique().tolist())

selected_platforms = st.sidebar.multiselect(
    "Plataforma(s)",
    options=platforms,
    default=platforms  # por defecto todas
)

selected_years = st.sidebar.multiselect(
    "Año(s)",
    options=years,
    default=years  # por defecto todos
)

filtered = df[df["Platform"].isin(selected_platforms) & df["Year"].isin(selected_years)]

st.subheader("📌 Datos filtrados")
st.caption(f"Filas: {len(filtered):,}")
st.dataframe(filtered, use_container_width=True, height=260)

# ---- Agregación: ventas por plataforma y año ----
agg = (
    filtered.groupby(["Platform", "Year"], as_index=False)["Global_Sales"]
    .sum()
    .rename(columns={"Global_Sales": "Ventas_Globales"})
)

st.subheader("📈 Ventas globales agregadas por Plataforma y Año")

if agg.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# Tabla pivot para visualizar mejor y para el gráfico
pivot = agg.pivot_table(
    index="Year",
    columns="Platform",
    values="Ventas_Globales",
    aggfunc="sum",
    fill_value=0
).sort_index()

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.line_chart(pivot, height=420)

with col2:
    st.write("**Ranking (suma de ventas globales según filtros):**")
    ranking = (
        agg.groupby("Platform", as_index=False)["Ventas_Globales"]
        .sum()
        .sort_values("Ventas_Globales", ascending=False)
    )
    st.dataframe(ranking, use_container_width=True, height=420)

st.download_button(
    "⬇️ Descargar agregación (CSV)",
    data=agg.to_csv(index=False).encode("utf-8"),
    file_name="ventas_por_plataforma_y_ano.csv",
    mime="text/csv",
)
