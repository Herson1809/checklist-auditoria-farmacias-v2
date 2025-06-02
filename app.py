import streamlit as st
import pandas as pd
from pathlib import Path
import json
from io import BytesIO

st.set_page_config(page_title="CheckList Auditoría", layout="wide")

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

# Configuración de página
st.set_page_config(page_title="Checklist Auditoría", layout="wide")
st.title("📋 Checklist Auditoría - Visualización Corporativa")

# Carga de archivo Excel
archivo_excel = st.file_uploader("Arrastra y suelta el archivo aquí", type=["xlsx"])

if archivo_excel:
    try:
        xls = pd.ExcelFile(archivo_excel)
        
        # Carga de hojas
        df_procedimientos = pd.read_excel(xls, sheet_name="Procedimientos", dtype=str)
        df_sucursales = pd.read_excel(xls, sheet_name="SUCURSAL", dtype=str)

        # Limpieza de columnas
        df_procedimientos.columns = df_procedimientos.columns.str.strip()
        df_sucursales.columns = df_sucursales.columns.str.strip()

        # Obtener listas únicas
        sucursales = df_sucursales.iloc[:, 0].dropna().unique().tolist()
        procedimientos = df_procedimientos['Procedimiento'].dropna().unique().tolist()

        # Selectores
        col1, col2 = st.columns(2)
        with col1:
            sucursal_seleccionada = st.selectbox(
                "🏪 **Sucursal:**", 
                [""] + sucursales,
                index=0
            )
        with col2:
            procedimiento_seleccionado = st.selectbox(
                "📌 **Procedimiento:**", 
                [""] + procedimientos,
                index=0
            )

        # Sistema de pestañas
        tabs = st.tabs([
            "📝 Lista de verificación editable",
            "📊 Resumen general",
            "📈 Efectividad e Inexactitud",
        ])

        # --- Pestaña 1: Checklist Editable ---
        with tabs[0]:
            if sucursal_seleccionada and procedimiento_seleccionado:
                st.header("✅ Checklist editable")
                
                # Inicializar estructuras
                st.session_state.respuestas.setdefault(sucursal_seleccionada, {}).setdefault(procedimiento_seleccionado, {})
                st.session_state.nuevos_puntos.setdefault(sucursal_seleccionada, {}).setdefault(procedimiento_seleccionado, [])
                
                # Sección para agregar nuevos puntos
                with st.expander("➕ Agregar nuevo punto de control", expanded=False):
                    nuevo_punto = st.text_input("Descripción del nuevo punto:")
                    nuevo_responsable = st.selectbox(
                        "Responsable:",
                        options=df_procedimientos['Responsable'].unique().tolist()
                    )
                    
                    if st.button("Agregar punto"):
                        if nuevo_punto:
                            nuevo_item = {
                                "Punto de control": nuevo_punto,
                                "Responsable": nuevo_responsable,
                                "Estado": "✅ Cumple",
                                "Comentario": "",
                                "EsNuevo": True
                            }
                            st.session_state.nuevos_puntos[sucursal_seleccionada][procedimiento_seleccionado].append(nuevo_item)
                            st.success("✅ Punto agregado correctamente")
                        else:
                            st.warning("⚠️ Ingresa una descripción para el punto")
                
                # Combinar puntos originales y agregados
                df_filtrado = df_procedimientos[df_procedimientos['Procedimiento'] == procedimiento_seleccionado].copy()
                puntos_agregados = pd.DataFrame(st.session_state.nuevos_puntos[sucursal_seleccionada][procedimiento_seleccionado])
                if not puntos_agregados.empty:
                    df_filtrado = pd.concat([df_filtrado, puntos_agregados], ignore_index=True)
                
                # Mostrar checklist
                for i, row in df_filtrado.iterrows():
                    punto = row['Punto de control']
                    responsable = row['Responsable']
                    es_nuevo = row.get('EsNuevo', False)
                    clave = f"{sucursal_seleccionada}_{procedimiento_seleccionado}_{punto}"
                    
                    # Obtener valores guardados
                    estado_guardado = st.session_state.respuestas[sucursal_seleccionada][procedimiento_seleccionado].get(punto, {}).get("Estado", "✅ Cumple")
                    comentario_guardado = st.session_state.respuestas[sucursal_seleccionada][procedimiento_seleccionado].get(punto, {}).get("Comentario", "")
                    
                    with st.expander(f"{'🆕 ' if es_nuevo else '🔹 '}{punto}"):
                        col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                        col1.markdown(f"👤 **Responsable:** {responsable}")
                        
                        estado = col2.radio(
                            "Estado:",
                            ["✅ Cumple", "❌ No cumple", "⚠️ Parcial"],
                            index=["✅ Cumple", "❌ No cumple", "⚠️ Parcial"].index(estado_guardado),
                            key=f"estado_{clave}"
                        )
                        
                        # Comentario obligatorio si no cumple
                        comentario = col3.text_input(
                            "🗨️ Comentario (Obligatorio si no cumple):",
                            value=comentario_guardado if estado_guardado != "✅ Cumple" else "",
                            key=f"comentario_{clave}"
                        )
                        
                        if estado in ["⚠️ Parcial", "❌ No cumple"] and not comentario:
                            st.error("Debes ingresar un comentario para este estado.")
                        
                        # Botón para eliminar (solo puntos agregados)
                        if es_nuevo and col4.button("🗑️", key=f"eliminar_{clave}"):
                            st.session_state.nuevos_puntos[sucursal_seleccionada][procedimiento_seleccionado] = [
                                p for p in st.session_state.nuevos_puntos[sucursal_seleccionada][procedimiento_seleccionado]
                                if p['Punto de control'] != punto
                            ]
                            st.rerun()
                        
                        # Guardar en estado
                        st.session_state.respuestas[sucursal_seleccionada][procedimiento_seleccionado][punto] = {
                            "Responsable": responsable,
                            "Estado": estado,
                            "Comentario": comentario if estado != "✅ Cumple" else "N/A",
                            "EsNuevo": es_nuevo
                        }

        # --- Pestaña 2: Resumen General ---
        with tabs[1]:
            if 'vista_resumen' not in st.session_state:
                st.session_state.vista_resumen = "general"
            
            # Vista General (Procedimientos)
            if st.session_state.vista_resumen == "general":
                st.header("📊 Resumen General por Procedimiento")
                
                if st.session_state.respuestas:
                    resumen_procedimientos = []
                    procedimientos_unicos = procedimientos  # Lista completa de 29 procedimientos
                    total_procedimientos = len(procedimientos_unicos)  # Total de procedimientos posibles (29)
                    
                    for idx, proc in enumerate(procedimientos_unicos):
                        # Obtener todas las sucursales que evaluaron este procedimiento
                        sucursales_con_proc = [
                            suc for suc in st.session_state.respuestas.keys() 
                            if proc in st.session_state.respuestas[suc]
                        ]
                        total_sucursales = len(sucursales_con_proc)
                        
                        # Si no hay sucursales evaluadas para este procedimiento
                        if total_sucursales == 0:
                            resumen_procedimientos.append({
                                "No": idx + 1,
                                "Procedimiento": proc,
                                "Cuantas sucursales fueron": 0,
                                "Cuantos procedimientos": f"0/{total_procedimientos}",
                                "Procedimientos cumplidos al 100%": 0,
                                "Efectividad": "0.00%",
                                "Riesgo": "⚪ No evaluado"
                            })
                            continue
                        
                        # Contar cuántas sucursales cumplieron 100% este procedimiento
                        sucursales_100 = sum(
                            1 for suc in sucursales_con_proc
                            if all(p["Estado"] == "✅ Cumple" 
                                   for p in st.session_state.respuestas[suc][proc].values())
                        )
                        
                        efectividad = (sucursales_100 / total_sucursales * 100) if total_sucursales > 0 else 0
                        
                        # Determinar riesgo según umbral de % de sucursales que cumplieron 100%
                        if efectividad == 100:
                            riesgo = "🟢 Bajo"
                        elif efectividad >= 70:
                            riesgo = "🟡 Moderado"
                        else:
                            riesgo = "🔴 Alto"
                        
                        resumen_procedimientos.append({
                            "No": idx + 1,
                            "Procedimiento": proc,
                            "Cuantas sucursales fueron": total_sucursales,
                            "Cuantos procedimientos": f"{total_sucursales}/{total_procedimientos}",
                            "Procedimientos cumplidos al 100%": sucursales_100,
                            "Efectividad": f"{efectividad:.2f}%",
                            "Riesgo": riesgo
                        })
                    
                    # Mostrar tabla con estilo
                    df_resumen = pd.DataFrame(resumen_procedimientos)
                    st.dataframe(
                        df_resumen,
                        use_container_width=True,
                        column_config={
                            "No": "No",
                            "Procedimiento": "Procedimiento",
                            "Cuantas sucursales fueron": st.column_config.NumberColumn("Cuantas sucursales fueron"),
                            "Cuantos procedimientos": "Cuantos procedimientos",
                            "Procedimientos cumplidos al 100%": st.column_config.NumberColumn("Procedimientos cumplidos al 100%"),
                            "Efectividad": "Efectividad",
                            "Riesgo": "Riesgo"
                        }
                    )
                    
                    # Botón para exportar a Excel (actualizado)
                    if st.button("📤 Exportar a Excel"):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            # Hoja 1: Checklist completo
                            df_export = pd.DataFrame([
                                {
                                    "Sucursal": suc,
                                    "Procedimiento": proc,
                                    "Punto de control": punto,
                                    "Estado": data["Estado"],
                                    "Comentario": data["Comentario"],
                                    "Responsable": data["Responsable"]
                                }
                                for suc, procs in st.session_state.respuestas.items()
                                for proc, puntos in procs.items()
                                for punto, data in puntos.items()
                            ])
                            df_export.to_excel(writer, sheet_name="Checklist", index=False)
                            
                            # Hoja 2: Inexactitudes
                            df_issues = df_export[df_export["Estado"].isin(["⚠️ Parcial", "❌ No cumple"])]
                            df_issues.to_excel(writer, sheet_name="Inexactitudes", index=False)
                            
                            # Hoja 3: Resumen General por Procedimiento
                            df_resumen_general = pd.DataFrame(resumen_procedimientos)
                            df_resumen_general.to_excel(writer, sheet_name="Resumen General", index=False)
                            
                            # Hoja 4: Detalle por Sucursal
                            datos_sucursales = []
                            for proc in procedimientos_unicos:
                                sucursales_con_proc = [suc for suc in st.session_state.respuestas.keys() 
                                                     if proc in st.session_state.respuestas[suc]]
                                for suc in sucursales_con_proc:
                                    puntos = st.session_state.respuestas[suc][proc]
                                    total_puntos = len(puntos)
                                    cumplidos = sum(1 for p in puntos.values() if p["Estado"] == "✅ Cumple")
                                    efectividad = (cumplidos / total_puntos) * 100 if total_puntos > 0 else 0
                                    
                                    datos_sucursales.append({
                                        "Sucursal": suc,
                                        "Procedimiento": proc,
                                        "Puntos evaluados": total_puntos,
                                        "Puntos cumplidos": cumplidos,
                                        "Puntos no cumplidos": total_puntos - cumplidos,
                                        "% Exactitud": f"{efectividad:.2f}%",
                                        "% Inexactitud": f"{100 - efectividad:.2f}%",
                                        "Riesgo": "🟢 Bajo" if efectividad == 100 else 
                                                 "🟡 Moderado" if efectividad >= 70 else 
                                                 "🔴 Alto"
                                    })
                            
                            df_detalle_sucursal = pd.DataFrame(datos_sucursales)
                            df_detalle_sucursal.to_excel(writer, sheet_name="Detalle Sucursales", index=False)
                        
                        st.download_button(
                            label="⬇️ Descargar Excel",
                            data=output.getvalue(),
                            file_name="auditoria_resultados.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    if st.button("🔍 Ver detalle por sucursal", type="primary"):
                        st.session_state.vista_resumen = "especifica"
                        st.rerun()
                
                else:
                    st.warning("No hay datos para mostrar")
            
            # Vista Específica (Sucursales)
            elif st.session_state.vista_resumen == "especifica":
                st.header("📋 Detalle por Sucursal")
                
                # Filtro por riesgo
                riesgo_filtro = st.selectbox(
                    "Filtrar por nivel de riesgo:",
                    options=["Todos", "Bajo 🟢", "Moderado 🟡", "Alto 🔴"],
                    index=0
                )
                
                procedimiento_seleccionado_resumen = st.selectbox(
                    "Selecciona un procedimiento:",
                    options=procedimientos,
                    index=0
                )
                
                # Obtener todas las sucursales que evaluaron este procedimiento
                sucursales_con_proc = [
                    suc for suc in st.session_state.respuestas.keys() 
                    if procedimiento_seleccionado_resumen in st.session_state.respuestas[suc]
                ]
                
                # Obtener el total de puntos que debería tener este procedimiento
                total_puntos_procedimiento = len(df_procedimientos[df_procedimientos['Procedimiento'] == procedimiento_seleccionado_resumen])
                
                st.subheader(f"Procedimiento: {procedimiento_seleccionado_resumen}")
                st.write(f"**Total de puntos esperados:** {total_puntos_procedimiento}")
                st.write(f"**Sucursales evaluadas:** {len(sucursales_con_proc)}")
                
                datos_sucursales = []
                for suc in sucursales_con_proc:
                    puntos = st.session_state.respuestas[suc][procedimiento_seleccionado_resumen]
                    total_puntos = len(puntos)
                    cumplidos = sum(1 for p in puntos.values() if p["Estado"] == "✅ Cumple")
                    no_cumplidos = total_puntos - cumplidos
                    efectividad = (cumplidos / total_puntos) * 100
                    
                    # Determinar riesgo según umbral de % de puntos cumplidos
                    if efectividad == 100:
                        riesgo = "🟢 Bajo"
                    elif efectividad >= 70:
                        riesgo = "🟡 Moderado"
                    else:
                        riesgo = "🔴 Alto"
                    
                    datos_sucursales.append({
                        "Sucursal": suc,
                        "Puntos evaluados": total_puntos,
                        "Puntos cumplidos": cumplidos,
                        "Puntos no cumplidos": no_cumplidos,
                        "% Exactitud": f"{efectividad:.2f}%",
                        "% Inexactitud": f"{100 - efectividad:.2f}%",
                        "Riesgo": riesgo
                    })
                
                # Aplicar filtro de riesgo si no es "Todos"
                if riesgo_filtro != "Todos":
                    riesgo_map = {
                        "Bajo 🟢": "🟢 Bajo",
                        "Moderado 🟡": "🟡 Moderado",
                        "Alto 🔴": "🔴 Alto"
                    }
                    datos_filtrados = [s for s in datos_sucursales if s["Riesgo"] == riesgo_map[riesgo_filtro]]
                else:
                    datos_filtrados = datos_sucursales
                
                # Mostrar tabla con estilo
                df_detalle = pd.DataFrame(datos_filtrados)
                st.dataframe(
                    df_detalle,
                    use_container_width=True,
                    column_config={
                        "Sucursal": "Sucursal",
                        "Puntos evaluados": st.column_config.NumberColumn("Puntos evaluados"),
                        "Puntos cumplidos": st.column_config.NumberColumn("Puntos cumplidos"),
                        "Puntos no cumplidos": st.column_config.NumberColumn("Puntos no cumplidos"),
                        "% Exactitud": "% Exactitud",
                        "% Inexactitud": "% Inexactitud",
                        "Riesgo": "Riesgo"
                    }
                )
                
                if st.button("← Volver al resumen general", type="primary"):
                    st.session_state.vista_resumen = "general"
                    st.rerun()

        # --- Pestaña 3: Efectividad e Inexactitud ---
        with tabs[2]:
            st.header("📈 Efectividad e Inexactitud")
            
            if st.session_state.respuestas:
                # Calcular inexactitud (Parcial + No cumple)
                df_inexactitud = pd.DataFrame([
                    {
                        "Sucursal": suc,
                        "Procedimiento": proc,
                        "Punto de control": punto,
                        "Estado": data["Estado"],
                        "Comentario": data["Comentario"]
                    }
                    for suc, procs in st.session_state.respuestas.items()
                    for proc, puntos in procs.items()
                    for punto, data in puntos.items()
                    if data["Estado"] in ["⚠️ Parcial", "❌ No cumple"]
                ])
                
                if not df_inexactitud.empty:
                    st.write("### 📌 Puntos con inexactitudes")
                    st.dataframe(df_inexactitud, use_container_width=True)
                    
                    # Gráfico de distribución
                    st.write("### 📊 Distribución de inexactitudes")
                    distribucion = df_inexactitud["Estado"].value_counts()
                    st.bar_chart(distribucion)
                else:
                    st.success("🎉 No hay puntos con inexactitudes registradas")
            else:
                st.warning("No hay datos para mostrar")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.info("Asegúrate que el archivo tenga las hojas exactas: 'Procedimientos' y 'SUCURSAL'")

else:
    st.info("💡 Carga el archivo Excel 'Base.xlsx' para comenzar")
