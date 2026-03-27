import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# Configuración de página
st.set_page_config(page_title="SabroAsistencia - Dashboard", layout="wide")

st.title("🍞 SabroAsistencia - Control de Personal")
st.subheader("Reporte de Asistencia en Tiempo Real")

# 1. Conexión a Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# 2. Obtención de datos (Asegúrate de que el nombre de la tabla sea correcto)
# Asumimos que la tabla se llama 'asistencias_view' o similar que une nombres y horas
query = conn.table("asistencias").select("*").execute()
df = pd.DataFrame(query.data)

if not df.empty:
    # --- MOTOR DE LIMPIEZA V1.1 (AUDITORÍA DE DATOS) ---

    # A. Convertir columnas a formato datetime para cálculos y luego a string limpio
    # Usamos errors='coerce' por si hay datos basura en la base
    df['Hora Entrada'] = pd.to_datetime(df['entrada']).dt.strftime('%H:%M')
    
    # B. Lógica para Hora Salida (Blanco si no ha salido)
    def limpiar_salida(row):
        ent = row['Hora Entrada']
        # 'salida' es el nombre de la columna original en tu DB
        sal_raw = row['salida'] 
        
        if pd.isna(sal_raw) or sal_raw == "" or sal_raw == "None":
            return ""
        
        sal_formateada = pd.to_datetime(sal_raw).strftime('%H:%M')
        
        # Si la salida es idéntica a la entrada, el empleado sigue activo
        if sal_formateada == ent:
            return ""
        return sal_formateada

    df['Hora Salida'] = df.apply(limpiar_salida, axis=1)

    # C. Limpieza de Jornada Total (Eliminar segundos y microsegundos)
    def limpiar_jornada(valor):
        if pd.isna(valor) or valor == "" or valor == "00:00:00" or str(valor).startswith('00:00:00'):
            return ""
        
        # Tomamos el string, quitamos microsegundos (split '.') y segundos (split ':')
        # Ejemplo: "08:30:15.123" -> ["08", "30", "15.123"] -> "08:30"
        partes = str(valor).split(':')
        if len(partes) >= 2:
            return f"{partes[0]}:{partes[1]}"
        return ""

    # 'duracion' es el nombre de la columna que trae el cálculo en tu DB
    df['Jornada Total'] = df['duracion'].apply(limpiar_jornada)

    # D. Renombrar columnas para la vista del Administrador
    # 'full_name' es el nombre del empleado en tu tabla
    df_final = df.rename(columns={'full_name': 'Empleado'})

    # 3. Visualización de la Tabla
    columnas_ordenadas = ['Empleado', 'Hora Entrada', 'Hora Salida', 'Jornada Total']
    st.table(df_final[columnas_ordenadas])

else:
    st.info("No hay registros de asistencia para el día de hoy.")

# Pie de página técnico
st.sidebar.markdown("---")
st.sidebar.write("🏷️ **Versión:** 1.1 (Producción)")
st.sidebar.write("🕒 **Horario Base:** 05:00 AM")
