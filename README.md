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
5. Antes de deployar, abre **Advanced settings > Secrets** y pega la configuración CSV usando el formato de `.streamlit/secrets.toml.example`.
6. Deploy.

## Configuración de datos (CSV)

La app está configurada para leer exclusivamente desde archivos CSV locales.

1. Coloca estos archivos en la raíz del repo:
    - `bv_hop_registroclientes.csv`
    - `bv_hop_consumos.csv`
2. En `Secrets` de Streamlit agrega:

```toml
[csv]
clientes_path = "bv_hop_registroclientes.csv"
consumos_path = "bv_hop_consumos.csv"
garantias_path = "bv_hop_garantia.csv"
```

Formato esperado:

- `bv_hop_registroclientes.csv`: debe incluir todas las columnas de `COLS_CLIENTES` + `status`.
- `bv_hop_consumos.csv`: debe incluir `id_instalacion` y:
   - `fecha` + `consumo_gj`, o
   - `anio`, `mes`, `dia` + `CONSUMO`.
- `bv_hop_garantia.csv`: debe incluir todas las columnas de `COLS_GARANTIA`.

También se aceptan estos nombres alternativos ya presentes en el directorio:

- `customer_registry.csv`
- `gas_consumption.csv`
- `guarantees.csv`

Notas:

- Si existe columna `archivado`, la app filtrará `archivado = 0`.
- Se considera consumo desde `2026-01-01` para mantener consistencia con la consulta original.
