import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# 1. Configuración de página
st.set_page_config(page_title="SabroAsistencia - Dashboard", layout="wide")

st.title("🍞 SabroAsistencia - Control de Personal")
st.subheader("Reporte de Asistencia en Tiempo Real")

# 2. Conexión Directa e Infalible
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://scynlrjnuywjcwovnzxh.supabase.co",
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
)

# 3. Obtención de datos de la vista consolidada
try:
    query = conn.table("asistencia_consolidada").select("*").execute()
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
            
            # Si marcó salida el mismo minuto que entró (error o activo), ocultar
            if sal_formateada == ent:
                return ""
            return sal_formateada

        df['Hora Salida'] = df.apply(limpiar_salida, axis=1)

        # C. Limpieza de Jornada Total (HH:MM sin segundos ni microsegundos)
        def limpiar_jornada(valor):
            if pd.isna(valor) or valor == "" or str(valor).startswith('00:00:00'):
                return ""
            # El tipo 'interval' de Postgres viene como 'HH:MM:SS' o 'HH:MM:SS.ms'
            # Tomamos solo los primeros 5 caracteres (HH:MM)
            return str(valor).split('.')[0][:5]

        df['Jornada Total'] = df['duracion_total'].apply(limpiar_jornada)

        # D. Renombrar columnas para el Administrador
        df_final = df.rename(columns={'full_name': 'Empleado'})

        # 4. Visualización de la Tabla con las columnas definitivas
        columnas_ordenadas = ['Empleado', 'Hora Entrada', 'Hora Salida', 'Jornada Total']
        st.table(df_final[columnas_ordenadas])

    else:
        st.info("No hay registros de asistencia para el día de hoy.")

except Exception as e:
    st.error(f"Error técnico de sincronización: {e}")

# Pie de página de control
st.sidebar.markdown("---")
st.sidebar.write("🏷️ **Versión:** 1.2 (Producción)")
st.sidebar.write("✅ **Base de Datos:** Conectada")
