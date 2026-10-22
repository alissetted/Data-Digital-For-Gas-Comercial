import ast
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import MagicMock

import pandas as pd


APP_PATH = Path(__file__).resolve().parents[1] / "mapa_gas.py"
FUNCTIONS = {
    "get_connection", "read_sql", "cargar_datos", "cargar_datos_garantias",
    "construir_consumo_mensual", "_filtrar_rango_fechas",
    "_dataframe_para_excel", "_excel_bytes_desde_hojas",
    "_calcular_dias_restantes",
}


def load_data_functions():
    # Isolate the data layer without executing the Streamlit UI or network calls.
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8-sig"))
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
            node.decorator_list = []
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name)
            and target.id in {"COLS_CLIENTES", "COLS_GARANTIA"}
            for target in node.targets
        ):
            nodes.append(node)
    namespace = {
        "__file__": str(APP_PATH),
        "Path": Path,
        "Mapping": Mapping,
        "tomllib": tomllib,
        "pd": pd,
        "datetime": datetime,
        "BytesIO": BytesIO,
        "sql": MagicMock(),
        "st": MagicMock(),
        "normalizar_status_serie": lambda series: series,
        "normalizar_zona_serie": lambda series: series,
        "normalizar_status_garantia_serie": lambda series: series,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(APP_PATH), "exec"), namespace)
    return namespace


class RemainingDaysTimezoneTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_data_functions()

    def test_remaining_days_with_timezone_aware_dates(self):
        vigencias = pd.Series(pd.to_datetime(
            ["2026-10-24", "2026-10-20"], utc=True
        ))
        result = self.ns["_calcular_dias_restantes"](
            vigencias, pd.Timestamp("2026-10-22")
        )
        self.assertEqual(result.tolist(), [2, -2])

    def test_remaining_days_with_timezone_naive_dates(self):
        vigencias = pd.Series(pd.to_datetime(["2026-10-24", "2026-10-20"]))
        result = self.ns["_calcular_dias_restantes"](
            vigencias, pd.Timestamp("2026-10-22")
        )
        self.assertEqual(result.tolist(), [2, -2])


class DatabricksTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_data_functions()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ns["__file__"] = str(self.root / "mapa_gas.py")
        self.cfg = {
            "server_hostname": "example.cloud.databricks.com",
            "http_path": "/sql/1.0/warehouses/example",
            "access_token": "test-token",
        }
        self.ns["st"].secrets = {"databricks": self.cfg.copy()}

    def write_secrets(self, content):
        folder = self.root / ".streamlit"
        folder.mkdir()
        (folder / "secretsdatabricks.toml").write_text(content, encoding="utf-8")

    def test_streamlit_secrets_for_deployment(self):
        self.ns["get_connection"]()
        self.ns["sql"].connect.assert_called_once_with(**self.cfg)

    def test_local_file_takes_priority_and_trims_values(self):
        self.write_secrets(
            '[databricks]\nserver_hostname = " local.cloud.databricks.com "\n'
            'http_path = " /sql/1.0/warehouses/local "\naccess_token = " local-token "\n'
        )
        self.ns["get_connection"]()
        self.ns["sql"].connect.assert_called_once_with(
            server_hostname="local.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/local",
            access_token="local-token",
        )

    def test_incomplete_local_file_does_not_fall_back(self):
        self.write_secrets('[databricks]\naccess_token = ""\n')
        with self.assertRaisesRegex(ValueError, "access_token"):
            self.ns["get_connection"]()
        self.ns["sql"].connect.assert_not_called()

    def test_missing_invalid_and_blank_fields_are_rejected(self):
        for field in self.cfg:
            for value in (None, "", "  ", 123):
                with self.subTest(field=field, value=value):
                    self.ns["st"].secrets = {"databricks": {**self.cfg, field: value}}
                    with self.assertRaisesRegex(ValueError, field) as error:
                        self.ns["get_connection"]()
                    self.assertNotIn("test-token", str(error.exception))
        self.ns["sql"].connect.assert_not_called()

    def test_missing_or_invalid_section_is_rejected(self):
        for secrets in ({}, {"databricks": "invalid"}):
            with self.subTest(secrets=secrets):
                self.ns["st"].secrets = secrets
                with self.assertRaisesRegex(ValueError, "databricks"):
                    self.ns["get_connection"]()

    def test_malformed_toml_is_not_silenced(self):
        self.write_secrets("[databricks")
        with self.assertRaises(tomllib.TOMLDecodeError):
            self.ns["get_connection"]()

    def test_connection_error_is_not_silenced(self):
        self.ns["sql"].connect.side_effect = RuntimeError("Connection failed")
        with self.assertRaisesRegex(RuntimeError, "Connection failed"):
            self.ns["get_connection"]()

    def cursor(self):
        conn = self.ns["sql"].connect.return_value.__enter__.return_value
        return conn.cursor.return_value.__enter__.return_value

    def test_dataframe_preserves_columns_dates_and_numeric_amounts(self):
        cursor = self.cursor()
        cursor.description = [("id_instalacion",), ("fecha",), ("consumo_gj",)]
        cursor.fetchall.return_value = [(123, date(2026, 1, 2), Decimal("12.50"))]
        result = self.ns["read_sql"]("SELECT example")
        cursor.execute.assert_called_once_with("SELECT example")
        self.assertEqual(list(result.columns), ["id_instalacion", "fecha", "consumo_gj"])
        self.assertEqual(result.iloc[0]["fecha"], date(2026, 1, 2))
        self.assertEqual(result.iloc[0]["consumo_gj"], 12.5)
        self.assertEqual(result["consumo_gj"].dtype.kind, "f")
        self.assert_resources_closed()

    def assert_resources_closed(self):
        connection = self.ns["sql"].connect.return_value
        connection.__exit__.assert_called_once()
        connection.__enter__.return_value.cursor.return_value.__exit__.assert_called_once()

    def test_empty_query_result_keeps_columns(self):
        self.cursor().description = [("id_instalacion",), ("CONSUMO",)]
        self.cursor().fetchall.return_value = []
        result = self.ns["read_sql"]("SELECT example")
        self.assertTrue(result.empty)
        self.assertEqual(list(result.columns), ["id_instalacion", "CONSUMO"])
        self.assert_resources_closed()

    def test_query_and_fetch_errors_close_resources_and_propagate(self):
        for method in ("execute", "fetchall"):
            with self.subTest(method=method):
                self.ns["sql"].reset_mock()
                getattr(self.cursor(), method).side_effect = RuntimeError("Query failed")
                with self.assertRaisesRegex(RuntimeError, "Query failed"):
                    self.ns["read_sql"]("SELECT example")
                self.assert_resources_closed()
                getattr(self.cursor(), method).side_effect = None

    def test_client_and_daily_consumption_loaders_keep_output_contract(self):
        client = dict.fromkeys(self.ns["COLS_CLIENTES"])
        client.update(
            razon_social="Cliente de prueba", id_instalacion=123,
            cp_localizacion="1234", status="Activo", zona_vpm="Norte",
        )
        daily = pd.DataFrame({
            "id_instalacion": [123, 123],
            "anio": [2026, 2026], "mes": [1, 1], "dia": [1, 2],
            "CONSUMO": [Decimal("10.5"), Decimal("20.5")],
        })
        reader = MagicMock(side_effect=[pd.DataFrame([client]), daily])
        self.ns["read_sql"] = reader
        clients, consumption = self.ns["cargar_datos"]()
        self.assertEqual(clients.iloc[0]["cp_localizacion"], "01234")
        self.assertEqual(list(consumption.columns), ["id_instalacion", "fecha", "consumo_gj"])
        self.assertEqual(consumption["consumo_gj"].sum(), 31)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(consumption["fecha"]))
        monthly = self.ns["construir_consumo_mensual"](consumption)
        self.assertEqual(monthly.iloc[0]["Consumo_2026_01_GJ"], 31)
        client_query, consumption_query = [call.args[0] for call in reader.call_args_list]
        self.assertIn("`engie_mex_apm`.`03-gold`.`denodo_registroclientes`", client_query)
        self.assertIn("`engie_mex_apm`.`03-gold`.`denodo_consumos`", consumption_query)
        self.assertIn("fecha >= DATE '2026-01-01'", consumption_query)
        self.assertIn("archivado = FALSE", consumption_query)
        self.assertIn("EXTRACT(DAY FROM fecha)", consumption_query)
        self.assertIn("SUM(consumo_gj) AS CONSUMO", consumption_query)

    def test_guarantees_loader_keeps_columns_and_filters(self):
        row = dict.fromkeys(self.ns["COLS_GARANTIA"])
        row.update(razon_social="Cliente de prueba", ldc=" Norte ", status_garantia="Vigente")
        self.ns["read_sql"] = MagicMock(return_value=pd.DataFrame([row, {**row, "razon_social": None}]))
        result = self.ns["cargar_datos_garantias"]()
        query = self.ns["read_sql"].call_args.args[0]
        self.assertIn("`engie_mex_apm`.`03-gold`.`denodo_garantia`", query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["zona"], "Norte")
        self.assertEqual(result.iloc[0]["status_norm"], "Vigente")
        self.assertTrue(set(self.ns["COLS_GARANTIA"]).issubset(result.columns))


class ExcelTimezoneTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_data_functions()

    def test_timezone_columns_preserve_wall_time_and_original_data(self):
        original = pd.DataFrame({
            "UTC": pd.to_datetime(["2026-10-22 02:30:00", None], utc=True),
            "Local": pd.DatetimeIndex(["2026-10-21 20:30:00", None], tz="America/Mexico_City"),
            "Sin zona": pd.to_datetime(["2026-10-22", None]),
            "Monto": [12.5, 20.0],
            "Texto": ["2026-10-22T02:30:00Z", "cliente"],
        })
        before = original.copy(deep=True)
        result = self.ns["_dataframe_para_excel"](original)
        for column in ("UTC", "Local"):
            pd.testing.assert_series_equal(result[column], original[column].dt.tz_localize(None))
        for column in ("Sin zona", "Monto", "Texto"):
            pd.testing.assert_series_equal(result[column], original[column])
        pd.testing.assert_frame_equal(original, before)

    def test_mixed_objects_strip_timezones_without_parsing_other_values(self):
        aware = datetime(2026, 10, 21, 23, 30, tzinfo=timezone(timedelta(hours=-6)))
        original = pd.DataFrame({"Mixta": pd.Series([
            aware, pd.Timestamp("2026-10-22T02:30:00Z"), datetime(2026, 10, 22),
            date(2026, 10, 22), None, pd.NaT, "texto", 123,
        ], dtype=object)})
        before = original.copy(deep=True)
        result = self.ns["_dataframe_para_excel"](original)
        self.assertEqual(result.iloc[0, 0], datetime(2026, 10, 21, 23, 30))
        self.assertEqual(result.iloc[1, 0], pd.Timestamp("2026-10-22T02:30:00"))
        self.assertIsNone(result.iloc[0, 0].tzinfo)
        self.assertIsNone(result.iloc[1, 0].tzinfo)
        pd.testing.assert_series_equal(result["Mixta"].iloc[2:], original["Mixta"].iloc[2:])
        pd.testing.assert_frame_equal(original, before)

    def test_excel_round_trip_for_reports_and_multiple_sheets(self):
        frame = pd.DataFrame({
            "Fecha UTC": pd.to_datetime(["2026-10-22 02:30:00"], utc=True),
            "Mixta": pd.Series([
                datetime(2026, 10, 21, 23, 30, tzinfo=timezone(timedelta(hours=-6)))
            ], dtype=object),
            "Monto": [123.5],
        })
        before = frame.copy(deep=True)
        data = self.ns["_excel_bytes_desde_hojas"]({
            "Reporte": frame, "Renovacion No Automatica": frame,
            "Renovacion Automatica": frame, "Vacia": frame.iloc[:0],
        })
        sheets = pd.read_excel(BytesIO(data), sheet_name=None)
        self.assertEqual(len(sheets), 4)
        for name, result in sheets.items():
            self.assertEqual(list(result.columns), list(frame.columns))
            if name == "Vacia":
                self.assertTrue(result.empty)
            else:
                self.assertEqual(result.iloc[0]["Fecha UTC"], datetime(2026, 10, 22, 2, 30))
                self.assertEqual(result.iloc[0]["Mixta"], datetime(2026, 10, 21, 23, 30))
                self.assertEqual(result.iloc[0]["Monto"], 123.5)
        pd.testing.assert_frame_equal(frame, before)


if __name__ == "__main__":
    unittest.main()
