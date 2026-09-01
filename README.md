# Dashboard de Gas Comercial (Streamlit)

Aplicación principal: `mapa_gas.py`

## Ejecutar local

```powershell
pip install -r requirements.txt
streamlit run mapa_gas.py
```

## Despliegue en Streamlit Cloud

1. Sube este repositorio a GitHub.
2. Entra a Streamlit Cloud: https://share.streamlit.io/
3. Clic en **New app**.
4. Selecciona:
   - **Repository**: este repo
   - **Branch**: `Desarrollo` (o la rama donde hagas push)
   - **Main file path**: `mapa_gas.py`
5. Antes de deployar, abre **Advanced settings > Secrets** y pega tus credenciales usando el formato de `.streamlit/secrets.toml.example`.
6. Deploy.

## Secrets requeridos

La app busca una sección `[denodo]` en `st.secrets`.

Puedes usar:

- `CONNECTION_STRING` (recomendado), o
- claves separadas (`DRIVER`, `SERVER`, `DATABASE`, `UID`, `PWD`).

## Modo temporal sin Denodo (CSV)

Si no hay acceso de red/ODBC a Denodo, la app puede correr con CSV.

1. Coloca estos archivos en la raíz del repo:
    - `bv_hop_registroclientes.csv`
    - `bv_hop_consumos.csv`
2. En `Secrets` de Streamlit agrega:

```toml
[app]
data_source = "csv"

[csv]
clientes_path = "bv_hop_registroclientes.csv"
consumos_path = "bv_hop_consumos.csv"
```

Formato esperado:

- `bv_hop_registroclientes.csv`: debe incluir todas las columnas de `COLS_CLIENTES` + `status`.
- `bv_hop_consumos.csv`: debe incluir `id_instalacion` y:
   - `fecha` + `consumo_gj`, o
   - `anio`, `mes`, `dia` + `CONSUMO`.

Notas:

- Si existe columna `archivado`, la app filtrará `archivado = 0`.
- Se considera consumo desde `2026-01-01` para mantener consistencia con la consulta original.

## Notas importantes para pyodbc en nube

- Este repo incluye `packages.txt` con paquetes de sistema para ODBC.
- Si tu servidor exige un driver ODBC específico no disponible, necesitarás ajustar la conexión/driver en Secrets.
- Si ves error de conexión al iniciar, revisa primero `Secrets` y conectividad de red al servidor Denodo.
