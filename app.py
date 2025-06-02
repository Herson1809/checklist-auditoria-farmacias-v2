import streamlit as st
import pandas as pd
from pathlib import Path
import json
from io import BytesIO

# Esta línea debe ser la primera llamada de Streamlit
st.set_page_config(page_title="CheckList Auditoría", layout="wide")

# Mensaje de inicio
st.write("💡 La app está corriendo correctamente, ¡listo para cargar el archivo!")

# Configuración persistente
CONFIG_FILE = "audit_config.json"

def load_config():
    try:
        if Path(CONFIG_FILE).exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"last_sucursal": None, "last_procedimiento": None}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Inicialización de estado
if 'config' not in st.session_state:
    st.session_state.config = load_config()

if 'respuestas' not in st.session_state:
    st.session_state.respuestas = {}

if 'nuevos_puntos' not in st.session_state:
    st.session_state.nuevos_puntos = {}

st.title("📋 Checklist Auditoría - Visualización Corporativa")

# Carga de archivo Excel
archivo_excel = st.file_uploader("Arrastra y suelta el archivo aquí", type=["xlsx"])

if archivo_excel:
    try:
        xls = pd.ExcelFile(archivo_excel)
        df_procedimientos = pd.read_excel(xls, sheet_name="Procedimientos", dtype=str)
        df_sucursales = pd.read_excel(xls, sheet_name="SUCURSAL", dtype=str)

        df_procedimientos.columns = df_procedimientos.columns.str.strip()
        df_sucursales.columns = df_sucursales.columns.str.strip()

        sucursales = df_sucursales.iloc[:, 0].dropna().unique().tolist()
        procedimientos = df_procedimientos['Procedimiento'].dropna().unique().tolist()

        col1, col2 = st.columns(2)
        with col1:
            sucursal_seleccionada = st.selectbox("🏪 **Sucursal:**", [""] + sucursales, index=0)
        with col2:
            procedimiento_seleccionado = st.selectbox("📌 **Procedimiento:**", [""] + procedimientos, index=0)

        tabs = st.tabs(["📝 Lista de verificación editable", "📊 Resumen general", "📈 Efectividad e Inexactitud"])

        # ... (Aquí sigue tu código actual para las pestañas, sin ningún cambio adicional)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.info("Asegúrate que el archivo tenga las hojas exactas: 'Procedimientos' y 'SUCURSAL'")
else:
    st.info("💡 Carga el archivo Excel 'Base.xlsx' para comenzar")
