import io
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Visualizador de ventas (Video Game Sales)", layout="wide")

st.title("📊 Visualizador de ventas desde fichero (CSV)")
st.write("Sube un fichero CSV como el ejemplo y filtra por **años** y **plataformas** para ver las gráficas de ventas.")

# -------------------------
# Helpers
# -------------------------
@st.cache_data
def load_csv(uploaded_file) -> pd.DataFrame:
    # Intentamos leer con separador automático (funciona bien con CSV estándar)
    raw = uploaded_file.read()
    # Reposiciona el puntero por si acaso
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    # Detectar encoding de forma simple (utf-8 primero, luego latin-1)
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except Exception:
            continue
    # Último intento sin encoding explícito
    return pd.read_csv(io.BytesIO(raw))

def ensure_columns(df: pd.DataFrame):
    required = {"Platform", "Year", "Global_Sales"}
    missing = required - set(df.columns)
    return missing

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Year a numérico e int (con NaN drop)
    out["Year"] = pd.to_numeric(out["Year"], errors="coerce")
    out = out.dropna(subset=["Year", "Platform", "Global_Sales"])
    out["Year"] = out["Year"].astype(int)

    # Asegurar numéricos en columnas de ventas típicas
    sales_cols = [c for c in ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"] if c in out.columns]
    for c in sales_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)

    return out

def top_platforms(df: pd.DataFrame, n=8):
    s = df.groupby("Platform", as_index=False)["Global_Sales"].sum().sort_values("Global_Sales", ascending=False)
    return s["Platform"].head(n).tolist()

# -------------------------
# UI - Upload
# -------------------------
with st.sidebar:
    st.header("⚙️ Controles")
    uploaded = st.file_uploader("Sube tu CSV", type=["csv"])

    st.markdown("---")
    st.caption("El fichero debe incluir al menos: **Platform**, **Year**, **Global_Sales**.")

if not uploaded:
    st.info("⬅️ Sube un CSV desde la barra lateral para empezar.")
    st.stop()

df = load_csv(uploaded)

missing = ensure_columns(df)
if missing:
    st.error(f"Faltan columnas necesarias: {', '.join(sorted(missing))}")
    st.write("Columnas detectadas:", list(df.columns))
    st.stop()

df = clean_df(df)

if df.empty:
    st.warning("No hay datos válidos tras limpiar (revisa la columna Year / Platform / Global_Sales).")
    st.stop()

min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
platform_options = sorted(df["Platform"].unique().tolist())
default_platforms = top_platforms(df, n=min(8, len(platform_options)))

with st.sidebar:
    year_range = st.slider(
        "📅 Rango de años",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
    )

    selected_platforms = st.multiselect(
        "🎮 Plataformas",
        options=platform_options,
        default=default_platforms,
    )

    show_region_breakdown = st.checkbox("Mostrar desglose por regiones (NA/EU/JP/Other)", value=True)
    show_raw_table = st.checkbox("Mostrar tabla filtrada", value=False)

# -------------------------
# Filter
# -------------------------
y0, y1 = year_range
fdf = df[(df["Year"] >= y0) & (df["Year"] <= y1)]
if selected_platforms:
    fdf = fdf[fdf["Platform"].isin(selected_platforms)]

if fdf.empty:
    st.warning("No hay datos para esos filtros (años/plataformas). Prueba a ampliar el rango o seleccionar más plataformas.")
    st.stop()

# -------------------------
# Aggregations
# -------------------------
by_year = (
    fdf.groupby("Year", as_index=False)["Global_Sales"]
    .sum()
    .sort_values("Year")
)

by_year_platform = (
    fdf.groupby(["Year", "Platform"], as_index=False)["Global_Sales"]
    .sum()
    .sort_values(["Year", "Platform"])
)

# Region breakdown (si están las columnas)
region_cols = [c for c in ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"] if c in fdf.columns]
by_year_regions = None
if region_cols:
    by_year_regions = (
        fdf.groupby("Year", as_index=False)[region_cols]
        .sum()
        .sort_values("Year")
    )
    by_year_regions_long = by_year_regions.melt("Year", var_name="Región", value_name="Ventas")

# -------------------------
# KPIs
# -------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Años (rango)", f"{y0}–{y1}")
c2.metric("Plataformas seleccionadas", str(len(selected_platforms)) if selected_platforms else "Todas")
c3.metric("Registros (filtrados)", f"{len(fdf):,}".replace(",", "."))
c4.metric("Ventas globales (suma)", f"{by_year['Global_Sales'].sum():,.2f}".replace(",", "."))

st.markdown("---")

# -------------------------
# Charts
# -------------------------
left, right = st.columns([1.2, 1])

with left:
    st.subheader("📈 Ventas globales por año (total)")
    chart_total = (
        alt.Chart(by_year)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:O", title="Año"),
            y=alt.Y("Global_Sales:Q", title="Ventas (millones)"),
            tooltip=[alt.Tooltip("Year:O", title="Año"), alt.Tooltip("Global_Sales:Q", title="Ventas", format=",.2f")],
        )
        .properties(height=320)
    )
    st.altair_chart(chart_total, use_container_width=True)

with right:
    st.subheader("🎮 Top plataformas (ventas globales)")
    top_plat = (
        fdf.groupby("Platform", as_index=False)["Global_Sales"]
        .sum()
        .sort_values("Global_Sales", ascending=False)
        .head(12)
    )
    chart_bar = (
        alt.Chart(top_plat)
        .mark_bar()
        .encode(
            y=alt.Y("Platform:N", sort="-x", title="Plataforma"),
            x=alt.X("Global_Sales:Q", title="Ventas (millones)"),
            tooltip=[alt.Tooltip("Platform:N", title="Plataforma"), alt.Tooltip("Global_Sales:Q", title="Ventas", format=",.2f")],
        )
        .properties(height=320)
    )
    st.altair_chart(chart_bar, use_container_width=True)

st.subheader("🧵 Ventas por año y plataforma (líneas)")
chart_lines = (
    alt.Chart(by_year_platform)
    .mark_line(point=False)
    .encode(
        x=alt.X("Year:O", title="Año"),
        y=alt.Y("Global_Sales:Q", title="Ventas (millones)"),
        color=alt.Color("Platform:N", title="Plataforma"),
        tooltip=[
            alt.Tooltip("Year:O", title="Año"),
            alt.Tooltip("Platform:N", title="Plataforma"),
            alt.Tooltip("Global_Sales:Q", title="Ventas", format=",.2f"),
        ],
    )
    .properties(height=380)
)
st.altair_chart(chart_lines, use_container_width=True)

if show_region_breakdown:
    st.subheader("🗺️ Desglose por regiones (stacked)")
    if by_year_regions is None:
        st.info("No encuentro columnas de regiones (NA_Sales / EU_Sales / JP_Sales / Other_Sales) en tu fichero.")
    else:
        chart_regions = (
            alt.Chart(by_year_regions_long)
            .mark_area()
            .encode(
                x=alt.X("Year:O", title="Año"),
                y=alt.Y("Ventas:Q", stack="zero", title="Ventas (millones)"),
                color=alt.Color("Región:N", title="Región"),
                tooltip=[
                    alt.Tooltip("Year:O", title="Año"),
                    alt.Tooltip("Región:N", title="Región"),
                    alt.Tooltip("Ventas:Q", title="Ventas", format=",.2f"),
                ],
            )
            .properties(height=380)
        )
        st.altair_chart(chart_regions, use_container_width=True)

if show_raw_table:
    st.subheader("🧾 Tabla (filtrada)")
    # Columnas más útiles primero (si existen)
    preferred = ["Name", "Platform", "Year", "Genre", "Publisher", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]
    cols = [c for c in preferred if c in fdf.columns] + [c for c in fdf.columns if c not in preferred]
    st.dataframe(fdf[cols], use_container_width=True)
