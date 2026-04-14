import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN Y ESTILO UI
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; } 
    .stApp { background-color: #FDF8F3; }
    
    /* Fuente maximizada para la tabla */
    [data-testid="stDataFrame"] td, [data-testid="stTable"] td {
        font-size: 24px !important; 
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    [data-testid="stDataFrame"] th {
        font-size: 18px !important;
        background-color: #D9832E !important;
        color: white !important;
    }

    .metric-card { 
        background-color: white; padding: 10px; border-radius: 12px; 
        border-left: 8px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 1rem; }
    .metric-card h2 { margin: 0; color: #D9832E; font-size: 2rem; font-weight: bold; }
    
    div[data-testid="stDateInput"] label { display: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A SUPABASE
conn = st.connection("supabase", type=SupabaseConnection)

# --- ESTRUCTURA DE PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📺 Monitor", "📅 Horarios", "📸 Fotos", "📊 Auditoría"])

# --- TAB 1: MONITOR ---
with tab1:
    col_t, col_cal, col_m1, col_m2, col_m3 = st.columns([1.2, 1, 1, 1, 1])
    
    with col_t:
        st.subheader("🍞 MONITOR")

    with col_cal:
        hoy_col = (datetime.utcnow() - timedelta(hours=5)).date()
        fecha_consulta = st.date_input("Fecha Monitor", hoy_col)

    try:
        # Consulta a la nueva vista de asistencia dinámica
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_consulta].copy()

            # Métricas
            with col_m1: st.markdown(f'<div class="metric-card"><h4>Personal</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with col_m2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            en_p = len(df_hoy[df_hoy["salida_real"] == "--"])
            with col_m3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_p}</h2></div>', unsafe_allow_html=True)

            if not df_hoy.empty:
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                df_hoy['foto_v'] = df_hoy['biometric_id'].apply(lambda x: f"{url_base}{str(x).zfill(8)}.jpg")

                st.dataframe(
                    df_hoy[['foto_v', 'persona', 'entrada_real', 'salida_real', 'tiempo_total', 'tardanza']],
                    column_config={
                        "foto_v": st.column_config.ImageColumn("", width="small"),
                        "persona": "Empleado",
                        "entrada_real": "Entrada",
                        "salida_real": "Salida",
                        "tiempo_total": "⏱️ Tiempo",
                        "tardanza": "¿Tarde?"
                    },
                    use_container_width=True, hide_index=True
                )
            else:
                st.warning(f"No hay horarios asignados para el {fecha_consulta.strftime('%d/%m/%Y')}")
    except Exception as e:
        st.error(f"Error en Monitor: {e}")

# --- TAB 2: GESTIÓN ÁGIL DE HORARIOS ---
with tab2:
    st.header("📅 Planificador Semanal")
    
    # 1. Selector de semana
    lunes_actual = hoy_col - timedelta(days=hoy_col.weekday())
    fecha_semana = st.date_input("Semana del lunes:", lunes_actual)
    
    # 2. Cargar empleados y malla
    res_e = conn.table("employees").select("biometric_id, full_name").execute()
    df_emp = pd.DataFrame(res_e.data)
    
    if not df_emp.empty:
        dias_sem = [fecha_semana + timedelta(days=i) for i in range(7)]
        cols_nombres = [d.strftime('%A %d/%m') for d in dias_sem]
        
        # Construir tabla de edición
        grid_data = []
        for _, e in df_emp.iterrows():
            fila = {"ID": e['biometric_id'], "Nombre": e['full_name']}
            for c in cols_nombres: fila[c] = "06:00 - 14:00"
            grid_data.append(fila)
        
        st.info("💡 Edita las celdas (Formato HH:MM - HH:MM) y presiona Guardar.")
        df_editor = st.data_editor(pd.DataFrame(grid_data), hide_index=True, use_container_width=True)
        
        if st.button("💾 Guardar Horarios de la Semana"):
            registros = []
            for _, r in df_editor.iterrows():
                for i, col_name in enumerate(cols_nombres):
                    val = r[col_name]
                    if "-" in val:
                        try:
                            ent, sal = val.split("-")
                            registros.append({
                                "biometric_id": r["ID"],
                                "fecha": dias_sem[i].isoformat(),
                                "entrada_programada": ent.strip(),
                                "salida_programada": sal.strip()
                            })
                        except: pass
            
            if registros:
                conn.table("employee_schedules_daily").upsert(registros).execute()
                st.success("¡Horarios actualizados en la base de datos!")

# --- TAB 3: CAPTURAR FOTOS ---
with tab3:
    res_f = conn.table("employees").select("biometric_id, full_name").execute()
    df_f = pd.DataFrame(res_f.data)
    if not df_f.empty:
        sel = st.selectbox("Seleccionar Empleado:", [f"{r['biometric_id']} - {r['full_name']}" for _, r in df_f.iterrows()])
        cam = st.camera_input("Tomar Foto")
        if cam:
            b_id = sel.split(" - ")[0].zfill(8)
            conn.client.storage.from_("empleados").upload(path=f"{b_id}.jpg", file=cam.getvalue(), file_options={"content-type":"image/jpeg","upsert":"true"})
            st.success(f"Foto de {b_id} guardada.")

# --- TAB 4: AUDITORÍA Y REPORTES ---
with tab4:
    st.header("📊 Reportes de Asistencia")
    c1, c2 = st.columns(2)
    with c1: f_i = st.date_input("Desde", hoy_col - timedelta(days=15))
    with c2: f_f = st.date_input("Hasta", hoy_col)
    
    if st.button("🔍 Generar Reporte"):
        res_r = conn.table("daily_attendance_summary").select("*").gte("fecha_dia", f_i).lte("fecha_dia", f_f).execute()
        df_r = pd.DataFrame(res_r.data)
        
        if not df_r.empty:
            st.subheader("Resumen General")
            resumen = df_r.groupby("persona").agg({"tardanza": lambda x: (x == "SÍ").sum()}).rename(columns={"tardanza": "Total Tardanzas"})
            st.dataframe(resumen, use_container_width=True)
            
            st.subheader("Detalle por Día")
            st.dataframe(df_r[['fecha_dia', 'persona', 'entrada_real', 'salida_real', 'tardanza']], use_container_width=True)
