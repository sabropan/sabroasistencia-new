import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="SabroAsistencia - Reportes", layout="wide")

st.title("🍞 SabroAsistencia - Control de Personal")

# --- COMPONENTE DE CALENDARIO (FILTRO DE FECHA) ---
# Colocamos el selector en la barra lateral o en el cuerpo principal
fecha_seleccionada = st.date_input("Selecciona una fecha para consultar:", datetime.now())
st.info(f"Mostrando registros para el día: {fecha_seleccionada.strftime('%d/%m/%Y')}")

# 2. Conexión Directa e Infalible
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://scynlrjnuywjcwovnzxh.supabase.co",
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
)

# 3. Obtención de datos filtrados por la fecha seleccionada
try:
    # Filtramos en la consulta SQL para traer solo la fecha que el usuario eligió
    query = conn.table("asistencia_consolidada").select("*").eq("fecha", str(fecha_seleccionada)).execute()
    df = pd.DataFrame(query.data)

    if not df.empty:
        # --- MOTOR DE LIMPIEZA V1.2 (SABROPAN PROFESIONAL) ---

        # A. Formatear Hora de Entrada (HH:MM)
        df['Hora Entrada'] = pd.to_datetime(df['hora_entrada_real']).dt.strftime('%H:%M')
        
        # B. Lógica para Hora Salida (En blanco si es igual a entrada o NULL)
        def limpiar_salida(row):
            ent = row['Hora Entrada']
            sal_raw = row['hora_salida_real'] 
            
            if pd.isna(sal_raw) or sal_raw == "" or str(sal_raw).lower() == "none":
                return ""
            
            sal_formateada = pd.to_datetime(sal_raw).strftime('%H:%M')
            
            # Si marcó salida el mismo minuto que entró (activo), ocultar
            if sal_formateada == ent:
                return ""
            return sal_formateada

        df['Hora Salida'] = df.apply(limpiar_salida, axis=1)

        # C. Limpieza de Jornada Total (HH:MM)
        def limpiar_jornada(valor):
            if pd.isna(valor) or valor == "" or str(valor).startswith('00:00:00'):
                return ""
            # El tipo 'interval' de Postgres: tomamos HH:MM
            return str(valor).split('.')[0][:5]

        df['Jornada Total'] = df['duracion_total'].apply(limpiar_jornada)

        # D. Renombrar columnas para el Administrador
        df_final = df.rename(columns={'full_name': 'Empleado'})

        # 4. Visualización de la Tabla
        columnas_ordenadas = ['Empleado', 'Hora Entrada', 'Hora Salida', 'Jornada Total']
        st.table(df_final[columnas_ordenadas])

    else:
        st.warning(f"No se encontraron registros para el {fecha_seleccionada.strftime('%d/%m/%Y')}.")

except Exception as e:
    st.error(f"Error técnico de sincronización: {e}")

# Pie de página de control
st.sidebar.markdown("---")
st.sidebar.write("🏷️ **Versión:** 1.3 (Calendario Activo)")
st.sidebar.write("✅ **Base de Datos:** Conectada")
