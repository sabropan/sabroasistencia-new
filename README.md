# 🍞 SabroAsistencia v1.0 - Sabropan

Sistema integral de gestión de asistencia biométrica con sincronización en la nube y monitoreo remoto.

## 🚀 Descripción del Proyecto
SabroAsistencia automatiza la captura de entradas y salidas del personal de Sabropan. Utiliza un capturador local basado en Python que sincroniza datos con **Supabase** (PostgreSQL) y los visualiza en un Dashboard interactivo en **Streamlit Cloud**.

## 🛠️ Stack Tecnológico
- **Lenguaje:** Python 3.11
- **Base de Datos:** Supabase (Cloud PostgreSQL)
- **Interfaz:** Streamlit (Dashboard móvil/web)
- **Persistence:** VBScript (Lanzador invisible para Windows)

## 📂 Estructura de Archivos
- `main.py`: Script capturador que se comunica con el hardware biométrico.
- `dashboard.py`: Aplicación web de Streamlit para el Administrador.
- `requirements.txt`: Dependencias necesarias para el despliegue en la nube.
- `invisible_start.vbs`: Script para ejecutar el sistema en segundo plano sin ventanas de CMD.

## 🛡️ Configuración de Seguridad y Blindaje
El proyecto está alojado en la PC de caja de Sabropan bajo medidas de "Seguridad por Ocultamiento":
1. **Atributos:** La carpeta está marcada como protegida por el sistema (`+s +h`).
2. **Arranque:** Ubicado en `shell:startup` para persistencia tras reinicios.
3. **Acceso:** Ruta directa `C:\Users\Admin\Desktop\BIO_SABROPAN`.

## ⚙️ Configuración de Secrets (Streamlit Cloud)
Para el despliegue en la nube, es obligatorio configurar los *Secrets* en el panel de Streamlit con el siguiente formato:
```toml
[connections.supabase]
url = "[https://tu-proyecto.supabase.co](https://tu-proyecto.supabase.co)"
key = "tu-anon-key"
