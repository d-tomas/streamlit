import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar la página
st.title("Análisis de Datos desde CSV")

# Subir archivo CSV
uploaded_file = st.file_uploader("Sube un archivo CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Vista previa de los datos:")
    st.write(df.head())
    
    # Seleccionar columna de año si existe
    year_column = st.selectbox("Selecciona la columna de años:", df.columns)
    if pd.api.types.is_numeric_dtype(df[year_column]):
        min_year, max_year = int(df[year_column].min()), int(df[year_column].max())
        year_range = st.slider("Selecciona el rango de años:", min_year, max_year, (min_year, max_year))
        df = df[(df[year_column] >= year_range[0]) & (df[year_column] <= year_range[1])]
    
    # Seleccionar columnas para análisis
    columns = st.multiselect("Selecciona las columnas a analizar:", df.columns)
    
    # Seleccionar tipo de gráfica
    chart_type = st.selectbox("Selecciona el tipo de gráfica:", ["Barras", "Líneas", "Mapa de calor"])
    
    if columns:
        st.write("### Gráfica seleccionada")
        if chart_type == "Barras":
            st.bar_chart(df[columns])
        elif chart_type == "Líneas":
            st.line_chart(df[columns])
        elif chart_type == "Mapa de calor":
            plt.figure(figsize=(10, 6))
            sns.heatmap(df[columns].corr(), annot=True, cmap="coolwarm", fmt=".2f")
            st.pyplot(plt)
    else:
        st.warning("Por favor, selecciona al menos una columna para analizar.")
