import streamlit as st
import pandas as pd
import numpy as np
import pyodbc
import pgeocode
import folium
import time
import os
import base64
from html import escape
from PIL import Image
from folium.plugins import FastMarkerCluster
from folium import MacroElement
from branca.element import Template
from streamlit_folium import st_folium
from shapely.geometry import Point, Polygon
from shapely.vectorized import contains as shapely_contains
from io import BytesIO
import xml.etree.ElementTree as ET
import unicodedata
import re
from datetime import date, datetime
import plotly.graph_objects as go
from fpdf import FPDF
from pandas.io.formats.style import Styler
from streamlit_sortables import sort_items
from streamlit_echarts import JsCode, st_echarts
import streamlit.components.v1 as components

st.set_page_config(page_title="Mexcom Facherito", layout="wide")

st.markdown("""
<style>
    /* ===== Sidebar estilo ENGIE ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #002B49 0%, #007BC5 100%);
        min-width: 260px;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    /* Encabezado del sidebar */
    .engie-logo {
        text-align: center;
        padding: 18px 0 6px 0;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 1px;
    }
    .engie-sub {
        text-align: center;
        font-size: 11px;
        letter-spacing: 2px;
        opacity: 0.8;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    .engie-section {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.6;
        margin: 18px 0 4px 6px;
    }
    /* Radio como menú de navegación (estilo tarjeta ENGIE) */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        display: flex;
        align-items: center;
        padding: 10px 14px;
        margin: 5px 6px;
        border-radius: 14px;
        cursor: pointer;
        transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
        font-weight: 700;
        border: 1.5px solid #D7E4F3;
        background: #FFFFFF;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #F3F8FF;
        border-color: #BFD7F1;
    }
    /* Botón del sidebar (mismo lenguaje visual de las tarjetas de navegación) */
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        border-radius: 14px !important;
        border: 1.5px solid #D7E4F3 !important;
        background: #FFFFFF !important;
        color: #1F2937 !important;
        fill: #1F2937 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06) !important;
        transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #F3F8FF !important;
        border-color: #BFD7F1 !important;
        color: #1F2937 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:focus {
        box-shadow: 0 0 0 3px rgba(0, 119, 204, 0.15) !important;
        border-color: #0077CC !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button * {
        color: #1F2937 !important;
        fill: #1F2937 !important;
    }
    /* Oculta el círculo del radio */
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none;
    }
    /* Opción seleccionada */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #0077CC 0%, #003C88 100%);
        border-color: #0077CC;
        box-shadow: 0 0 0 3px rgba(0, 119, 204, 0.15);
    }
    /* Contraste de texto: oscuro en no seleccionado, blanco en seleccionado */
    section[data-testid="stSidebar"] div[role="radiogroup"] label,
    section[data-testid="stSidebar"] div[role="radiogroup"] label *,
    section[data-testid="stSidebar"] div[role="radiogroup"] label p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label span,
    section[data-testid="stSidebar"] div[role="radiogroup"] label div {
        color: #1F2937 !important;
        fill: #1F2937 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) *,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) div {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }
    /* Oculta el botón de pantalla completa del logo */
    section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has([data-testid="stImage"]) button[aria-label="Fullscreen"] {
        display: none !important;
    }
    /* Centra el logo en el sidebar */
    section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has([data-testid="stImage"]) {
        display: flex;
        justify-content: center;
    }
    section[data-testid="stSidebar"] div[data-testid="stFullScreenFrame"]:has([data-testid="stImage"]) {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    /* Multiselect de status con la misma estética de tarjeta del filtro de fecha */
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        border-radius: 14px !important;
        border: 1.5px solid #D7E4F3 !important;
        background: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06) !important;
        transition: border-color 0.15s, box-shadow 0.15s;
        min-height: 48px;
        padding-top: 2px;
        padding-bottom: 2px;
    }
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {
        border-color: #0077CC !important;
        box-shadow: 0 0 0 3px rgba(0, 119, 204, 0.15) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] input,
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="select"] svg {
        color: #1F2937 !important;
        fill: #1F2937 !important;
    }
    /* Filtro de zona: variante compacta (más limpia que el menú principal). */
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] {
        display: grid;
        gap: 6px;
    }
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label {
        display: flex;
        align-items: center;
        padding: 7px 10px;
        margin: 0;
        border-radius: 10px;
        cursor: pointer;
        transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
        font-weight: 600;
        font-size: 0.92rem;
        border: 1.5px solid #D7E4F3;
        background: #FFFFFF;
        box-shadow: none;
    }
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label:hover {
        background: #F3F8FF;
        border-color: #BFD7F1;
    }
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label > div:first-child {
        display: none;
    }
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #0077CC 0%, #003C88 100%);
        border-color: #0077CC;
        box-shadow: 0 0 0 2px rgba(0, 119, 204, 0.15);
    }
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label,
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label * {
        color: #1F2937 !important;
        fill: #1F2937 !important;
    }
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label:has(input:checked),
    section[data-testid="stSidebar"] .st-key-zona_widget div[role="radiogroup"] label:has(input:checked) * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }
    /* Number input (ej. "GJ mínimo (exacto)"): el texto hereda color blanco
       del sidebar y queda invisible sobre el fondo blanco del campo. */
    section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input {
        color: #1F2937 !important;
        background: #FFFFFF !important;
        border-radius: 14px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input::placeholder {
        color: #9AA5B1 !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button {
        background: #FFFFFF !important;
        color: #1F2937 !important;
        fill: #1F2937 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
        border-radius: 999px !important;
        border: none !important;
        background: linear-gradient(135deg, #0077CC 0%, #003C88 100%) !important;
        box-shadow: 0 4px 10px rgba(0, 60, 136, 0.18) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }
    div[role="listbox"] {
        border-radius: 18px !important;
        border: 1px solid #D7E4F3 !important;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18) !important;
        padding: 6px !important;
        background: #FFFFFF !important;
    }
    div[role="option"] {
        border-radius: 12px !important;
        color: #1F2937 !important;
        transition: background 0.15s ease;
    }
    div[role="option"][aria-selected="true"] {
        background: linear-gradient(135deg, #0077CC 0%, #003C88 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    div[role="option"]:hover {
        background: #E5F1FF !important;
    }
    /* Selector Clientes/Garantías como botón de acción */
    div[data-testid="stSegmentedControl"] {
        min-height: 62px;
        width: 100% !important;
        max-width: 360px !important;
        margin-left: auto !important;
        margin-right: 0 !important;
    }
    div[data-testid="stSegmentedControl"] > div,
    div[data-testid="stSegmentedControl"] div[role="tablist"],
    div[data-testid="stSegmentedControl"] button {
        width: 100% !important;
        gap: 10px !important;
    }
    div[data-testid="stSegmentedControl"] > div {
        padding: 5px !important;
        border-radius: 18px !important;
        background: linear-gradient(180deg, #EAF5FF 0%, #DCEEFF 100%) !important;
        border: 1px solid #BFD7F1 !important;
        box-shadow: 0 8px 18px rgba(0, 119, 204, 0.10);
    }
    div[data-testid="stSegmentedControl"] div[role="option"],
    div[data-testid="stSegmentedControl"] button {
        font-size: 1.16rem !important;
        font-weight: 800 !important;
        padding: 1rem 1.9rem !important;
        min-height: 54px !important;
        border-radius: 12px !important;
        letter-spacing: 0.2px;
        color: #003C88 !important;
        background: transparent !important;
        border: 1px solid transparent !important;
    }
    div[data-testid="stSegmentedControl"] div[role="option"][aria-selected="true"],
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        background: linear-gradient(135deg, #0077CC 0%, #003C88 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 18px rgba(0, 60, 136, 0.22) !important;
        border-color: rgba(255,255,255,0.25) !important;
    }
    div[data-testid="stSegmentedControl"] div[role="option"]:hover,
    div[data-testid="stSegmentedControl"] button:hover {
        transform: translateY(-1px);
        transition: all 0.15s ease;
    }
    /* Botones de exportacion minimalistas para cabeceras de renovacion */
    div[class*="st-key-renov_no_auto_header"] div[data-testid="stDownloadButton"],
    div[class*="st-key-renov_auto_header"] div[data-testid="stDownloadButton"] {
        display: flex;
        justify-content: flex-end;
    }
    div[class*="st-key-renov_no_auto_header"] div[data-testid="stDownloadButton"] > button,
    div[class*="st-key-renov_auto_header"] div[data-testid="stDownloadButton"] > button {
        border-radius: 10px !important;
        border: 1px solid #D7E4F3 !important;
        background: #FFFFFF !important;
        color: #334155 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        min-height: 32px !important;
        padding: 0.2rem 0.65rem !important;
        box-shadow: none !important;
    }
    div[class*="st-key-renov_no_auto_header"] div[data-testid="stDownloadButton"] > button:hover,
    div[class*="st-key-renov_auto_header"] div[data-testid="stDownloadButton"] > button:hover {
        border-color: #BFD7F1 !important;
        background: #F8FBFF !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
<style>
    .engie-kpi-card {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid #E5EDF6;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
        padding: 12px 12px 10px 12px;
        min-height: 128px;
    }
    .engie-kpi-topline {
        height: 4px;
        border-radius: 999px;
        margin-bottom: 9px;
        opacity: 0.95;
    }
    .engie-kpi-head {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .engie-kpi-icon {
        font-size: 1rem;
        line-height: 1;
    }
    .engie-kpi-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.35px;
        text-transform: uppercase;
        color: #3B4A5A;
    }
    .engie-kpi-main {
        font-size: 1.36rem;
        font-weight: 700;
        color: #1F2937;
        line-height: 1.18;
        margin: 2px 0 4px 0;
        word-break: break-word;
    }
    .engie-kpi-sub {
        font-size: 0.82rem;
        color: #6B7280;
        line-height: 1.25;
    }
    section[data-testid="stSidebar"] {
        min-width: 282px;
        max-width: 282px;
        padding: 0 0.85rem 1rem 0.85rem;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0.15rem;
    }
    section[data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 0 !important;
        max-width: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        border-right: none !important;
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_brand_block"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        padding-top: 0;
        padding-bottom: 0.15rem;
        margin-top: -2.55rem;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_brand_block"] .engie-logo-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin: 0 0 1.1rem;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_brand_block"] .engie-logo-wrap img {
        display: block;
        width: 100px;
        max-width: 100%;
        height: auto;
        margin: 0 auto;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_brand_block"] .engie-sub {
        margin-bottom: 0.35rem;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_shell"] {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        width: 100%;
        margin: 0.35rem 0 0.1rem;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] {
        width: 100%;
        margin: 0 !important;
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        min-height: 44px !important;
        height: 44px !important;
        padding: 0 0.9rem !important;
        border: none !important;
        border-radius: 10px !important;
        background: transparent !important;
        box-shadow: none !important;
        color: #F4F8FB !important;
        font-weight: 500 !important;
        text-align: left !important;
        transition: background 0.18s ease;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button:focus,
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button:focus-visible {
        outline: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"][class*="_active"] div[data-testid="stButton"] > button {
        background: rgba(148, 217, 238, 0.16) !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button p {
        width: 100%;
        margin: 0;
        overflow: hidden;
        font-size: 0.95rem;
        line-height: 1.2;
        text-align: left;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button > div,
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button span {
        display: flex !important;
        justify-content: flex-start !important;
        width: 100% !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"] div[data-testid="stButton"] > button * {
        color: #F4F8FB !important;
        fill: #F4F8FB !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_nav_item_"][class*="_active"] div[data-testid="stButton"] > button * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] .engie-section {
        margin: 16px 0 6px 6px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }
    section[data-testid="stSidebar"] .engie-nav-section {
        margin-top: 4px;
    }
    section[data-testid="stSidebar"] div[class*="st-key-sidebar_period_section"] .engie-section {
        margin-top: 4px;
    }
    section[data-testid="stSidebar"] .stDivider {
        margin: 0.1rem 0 0.2rem;
        opacity: 0.5;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ===== Selector de rango de fechas estilo "tarjeta" (paleta ENGIE) =====
st.markdown(
    """
<style>
    :root {
        --engie-table-head-bg: #002D72;
        --engie-table-head-text: #FFFFFF;
    }

    /* Etiqueta del filtro (arriba del campo) */
    div[data-testid="stDateInput"] label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        color: #003C88;
    }
    /* Campo del rango de fechas: tarjeta redondeada tipo "pill" */
    div[data-testid="stDateInput"] div[data-baseweb="input"] {
        border-radius: 14px !important;
        border: 1.5px solid #D7E4F3 !important;
        background: #FFFFFF;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        transition: border-color 0.15s, box-shadow 0.15s;
    }

    /* Popover MASTER: ampliar área visible y evitar scroll interno */
    div[data-testid="stPopover"] div[role="dialog"] {
        width: min(92vw, 980px) !important;
        max-width: min(92vw, 980px) !important;
    }
    div[data-testid="stPopover"] div[role="dialog"] > div {
        max-height: calc(100vh - 72px) !important;
        overflow-y: visible !important;
    }

    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within {
        border-color: #0077CC !important;
        box-shadow: 0 0 0 3px rgba(0, 119, 204, 0.15);
    }
    div[data-testid="stDateInput"] input {
        font-weight: 600;
        color: #1F2937 !important;
    }
    /* Ventana emergente del calendario */
    div[data-baseweb="popover"] div[data-baseweb="calendar"] {
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
        padding: 6px;
    }
    /* Encabezado (mes / flechas de navegación) */
    div[data-baseweb="calendar"] div[role="presentation"] > div:first-child {
        color: #003C88;
        font-weight: 700;
    }
    /* Día de hoy */
    div[data-baseweb="calendar"] [aria-label*="Today" i] > div,
    div[data-baseweb="calendar"] [aria-label*="hoy" i] > div {
        border: 1.5px solid #0077CC;
        border-radius: 999px;
    }
    /* Día(s) seleccionados: inicio/fin del rango en azul ENGIE, resto del
       rango con un azul claro de fondo (igual que un date-range picker). */
    div[data-baseweb="calendar"] [aria-selected="true"] > div {
        background: linear-gradient(135deg, #0077CC 0%, #003C88 100%) !important;
        color: #FFFFFF !important;
        border-radius: 999px !important;
        font-weight: 700;
    }
    div[data-baseweb="calendar"] div[role="gridcell"]:not([aria-selected="true"]):not([aria-disabled="true"]) > div:hover {
        background: #E5F1FF !important;
        border-radius: 999px !important;
    }
    /* ===== Tablas: contenedor tipo tarjeta ENGIE ===== */
    div[data-testid="stDataFrame"],
    .engie-dataframe-wrapper {
        border-radius: 14px !important;
        border: 1.5px solid #D7E4F3 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06) !important;
        overflow: hidden !important;
        background: #FFFFFF !important;
    }
    .engie-dataframe-scroll {
        overflow: auto;
        width: 100%;
    }
    .engie-dataframe-wrapper table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.95rem;
    }
    .engie-dataframe-wrapper thead th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: var(--engie-table-head-bg) !important;
        color: var(--engie-table-head-text) !important;
        font-weight: 700;
        border-bottom: 1px solid #D7E4F3;
    }
    .engie-dataframe-wrapper thead th *,
    .engie-dataframe-wrapper thead td * {
        color: var(--engie-table-head-text) !important;
    }
    .engie-dataframe-wrapper tbody td,
    .engie-dataframe-wrapper tbody th {
        background: #FFFFFF;
        color: #1F2937;
    }
    .engie-dataframe-wrapper th,
    .engie-dataframe-wrapper td {
        padding: 0.34rem 0.75rem;
        border-right: 1px solid #E5EDF6;
        border-bottom: 1px solid #E5EDF6;
        white-space: nowrap;
        text-align: left;
        vertical-align: middle;
    }
    .engie-dataframe-wrapper tr:last-child td,
    .engie-dataframe-wrapper tr:last-child th {
        border-bottom: none;
    }
    .engie-dataframe-wrapper th:last-child,
    .engie-dataframe-wrapper td:last-child {
        border-right: none;
    }
    div[data-testid="stTable"] table thead th,
    div[data-testid="stTable"] table thead td,
    div[data-testid="stMarkdownContainer"] table thead th,
    div[data-testid="stMarkdownContainer"] table thead td,
    table thead th,
    table thead td {
        background: var(--engie-table-head-bg) !important;
        color: var(--engie-table-head-text) !important;
    }
    div[data-testid="stTable"] table thead th *,
    div[data-testid="stTable"] table thead td *,
    div[data-testid="stMarkdownContainer"] table thead th *,
    div[data-testid="stMarkdownContainer"] table thead td *,
    table thead th *,
    table thead td * {
        color: var(--engie-table-head-text) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

_STREAMLIT_DATAFRAME = st.dataframe


def _engie_table_styles():
    return [
        {
            "selector": "thead th",
            "props": [
                ("background-color", "var(--engie-table-head-bg)"),
                ("color", "var(--engie-table-head-text)"),
                ("font-weight", "700"),
            ],
        },
        {
            "selector": "tbody td",
            "props": [("color", "#1F2937")],
        },
        {
            "selector": "tbody th",
            "props": [("color", "#1F2937")],
        },
    ]


def _python_date_format(streamlit_fmt):
    formatos = {
        "DD/MM/YYYY": "%d/%m/%Y",
        "D/M/YYYY": "%-d/%-m/%Y" if os.name != "nt" else "%#d/%#m/%Y",
    }
    return formatos.get(streamlit_fmt, "%d/%m/%Y")


def _format_number_value(valor, patron):
    if pd.isna(valor):
        return ""
    if not patron or "%" not in patron:
        return str(valor)

    coincidencia = re.match(r"^(?P<prefix>[^%]*?)%(?P<comma>,)?(?:\.(?P<precision>\d+))?(?P<kind>[df])(?P<suffix>.*)$", patron)
    if not coincidencia:
        return str(valor)

    prefix = coincidencia.group("prefix") or ""
    suffix = coincidencia.group("suffix") or ""
    usar_coma = bool(coincidencia.group("comma"))
    precision = int(coincidencia.group("precision") or 0)
    tipo = coincidencia.group("kind")

    if tipo == "d":
        numero = int(round(float(valor)))
        cuerpo = f"{numero:,d}" if usar_coma else f"{numero:d}"
    else:
        spec = "," if usar_coma else ""
        cuerpo = format(float(valor), f"{spec}.{precision}f")
    return f"{prefix}{cuerpo}{suffix}"


def _apply_column_config_to_dataframe(df, column_config):
    if not column_config:
        return df

    resultado = df.copy()
    renombres = {}
    for columna, config in column_config.items():
        if columna not in resultado.columns or not isinstance(config, dict):
            continue

        etiqueta = config.get("label")
        if etiqueta and etiqueta != columna:
            renombres[columna] = etiqueta

        type_config = config.get("type_config") or {}
        tipo = type_config.get("type")
        if tipo == "date":
            fmt = _python_date_format(type_config.get("format"))
            serie = pd.to_datetime(resultado[columna], errors="coerce")
            resultado[columna] = serie.map(lambda v: v.strftime(fmt) if pd.notna(v) else "")
        elif tipo == "number":
            patron = type_config.get("format")
            serie = pd.to_numeric(resultado[columna], errors="coerce")
            resultado[columna] = serie.map(lambda v: _format_number_value(v, patron) if pd.notna(v) else "")

    if renombres:
        resultado = resultado.rename(columns=renombres)
    return resultado


def _engie_dataframe_html(data, hide_index=False, column_config=None):
    if isinstance(data, Styler):
        styler = data.set_table_styles(_engie_table_styles(), overwrite=False)
        if hide_index:
            styler = styler.hide(axis="index")
        return styler.to_html(classes="engie-dataframe-table")

    dataframe = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    dataframe = _apply_column_config_to_dataframe(dataframe, column_config)
    styler = dataframe.style.set_table_styles(_engie_table_styles(), overwrite=False)
    styler = styler.format(na_rep="")
    if hide_index:
        styler = styler.hide(axis="index")
    return styler.to_html(classes="engie-dataframe-table")


_ENGIE_TABLA_CSS = """
:root {
    --engie-table-head-bg: #002D72;
    --engie-table-head-text: #FFFFFF;
}
html, body {
    margin: 0;
    height: 100%;
    background: transparent;
    font-family: "Source Sans Pro", "Source Sans 3", "Segoe UI", Roboto, sans-serif;
}
.engie-dataframe-wrapper {
    box-sizing: border-box;
    height: 100%;
    border-radius: 14px;
    border: 1.5px solid #D7E4F3;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    overflow: hidden;
    background: #FFFFFF;
}
.engie-dataframe-scroll {
    height: 100%;
    overflow: auto;
}
.engie-dataframe-wrapper table {
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.95rem;
    width: 100%;
}
.engie-dataframe-wrapper thead th {
    position: sticky;
    top: 0;
    z-index: 1;
    background: var(--engie-table-head-bg) !important;
    color: var(--engie-table-head-text) !important;
    font-weight: 700;
    border-bottom: 1px solid #D7E4F3;
}
.engie-dataframe-wrapper thead th * {
    color: var(--engie-table-head-text) !important;
}
.engie-dataframe-wrapper tbody td,
.engie-dataframe-wrapper tbody th {
    background: #FFFFFF;
    color: #1F2937;
}
.engie-dataframe-wrapper th,
.engie-dataframe-wrapper td {
    padding: 0.34rem 0.75rem;
    border-right: 1px solid #E5EDF6;
    border-bottom: 1px solid #E5EDF6;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: left;
    vertical-align: middle;
}
.engie-dataframe-wrapper tr:last-child td,
.engie-dataframe-wrapper tr:last-child th {
    border-bottom: none;
}
.engie-dataframe-wrapper th:last-child,
.engie-dataframe-wrapper td:last-child {
    border-right: none;
}
.col-resizer {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 8px;
    cursor: col-resize;
    z-index: 2;
}
.col-resizer::after {
    content: "";
    position: absolute;
    top: 25%;
    bottom: 25%;
    left: 3px;
    width: 1px;
    background: rgba(255, 255, 255, 0.45);
}
.col-resizer:hover::after,
.col-resizer.activo::after {
    left: 2px;
    width: 2px;
    background: #FFFFFF;
}
"""

_ENGIE_TABLA_JS = """
(function () {
    var table = document.querySelector(".engie-dataframe-wrapper table");
    if (!table) return;
    var ths = Array.prototype.slice.call(table.querySelectorAll("thead th"));
    if (!ths.length) return;
    var ultimo = ths.length - 1;
    var anchos = null;

    function sincronizar() {
        var total = 0;
        ths.forEach(function (th, i) {
            if (anchos[i] == null) { th.style.width = ""; return; }
            th.style.width = anchos[i] + "px";
            total += anchos[i];
        });
        table.style.tableLayout = "fixed";
        table.style.width = anchos[ultimo] == null ? "100%" : total + "px";
    }

    function fijar() {
        anchos = ths.map(function (th) { return th.getBoundingClientRect().width; });
        anchos[ultimo] = null;
        sincronizar();
    }

    ths.forEach(function (th, i) {
        var tirador = document.createElement("div");
        tirador.className = "col-resizer";
        th.appendChild(tirador);
        tirador.addEventListener("mousedown", function (e) {
            e.preventDefault();
            if (anchos == null) fijar();
            var inicioX = e.clientX;
            var inicioAncho = th.getBoundingClientRect().width;
            tirador.classList.add("activo");
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";
            function mover(ev) {
                anchos[i] = Math.max(48, inicioAncho + ev.clientX - inicioX);
                sincronizar();
            }
            function soltar() {
                document.removeEventListener("mousemove", mover);
                document.removeEventListener("mouseup", soltar);
                tirador.classList.remove("activo");
                document.body.style.cursor = "";
                document.body.style.userSelect = "";
            }
            document.addEventListener("mousemove", mover);
            document.addEventListener("mouseup", soltar);
        });
    });

    var indicesCliente = [];
    ths.forEach(function (th, i) {
        if (th.textContent.trim() === "Cliente") indicesCliente.push(i);
    });
    if (indicesCliente.length) {
        fijar();
        indicesCliente.forEach(function (i) {
            if (anchos[i] != null) anchos[i] = anchos[i] * 0.55;
        });
        sincronizar();
    }
})();
"""


def _engie_tabla_documento(tabla_html):
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{_ENGIE_TABLA_CSS}</style></head><body>"
        "<div class='engie-dataframe-wrapper'><div class='engie-dataframe-scroll'>"
        f"{tabla_html}</div></div>"
        f"<script>{_ENGIE_TABLA_JS}</script></body></html>"
    )


def _engie_cantidad_filas(data):
    if isinstance(data, Styler):
        return len(data.data.index)
    if isinstance(data, pd.DataFrame):
        return len(data.index)
    try:
        return len(data)
    except TypeError:
        return 0


def _engie_dataframe_height(height, data):
    alto_minimo = 142
    alto_header = 34
    alto_fila = 32
    padding = 2
    cantidad_filas = _engie_cantidad_filas(data)
    if isinstance(height, int):
        return max(height, alto_minimo)
    if height in ("stretch", "content"):
        return alto_header + cantidad_filas * alto_fila + padding

    filas_visibles = min(max(cantidad_filas, 4), 15)
    return alto_header + filas_visibles * alto_fila + padding


def engie_dataframe(
    data=None,
    width="stretch",
    height="auto",
    *,
    use_container_width=None,
    hide_index=None,
    column_config=None,
    **kwargs,
):
    if any(clave in kwargs for clave in ("on_select", "selection_mode", "selection_default")):
        return _STREAMLIT_DATAFRAME(
            data,
            width=width,
            height=height,
            use_container_width=use_container_width,
            hide_index=hide_index,
            column_config=column_config,
            **kwargs,
        )

    alto = _engie_dataframe_height(height, data)
    html = _engie_dataframe_html(data, hide_index=bool(hide_index), column_config=column_config)
    components.html(_engie_tabla_documento(html), height=alto, scrolling=False)
    return None


st.dataframe = engie_dataframe

# Umbral: por encima de este nº de clientes en una zona se usa clustering
# para evitar dibujar miles de marcadores individuales.
UMBRAL_CLUSTER = 1500

BRAND_COLORS = {
    "primary": "#0077CC",
    "primary_dark": "#003C88",
    "accent": "#00AAFF",
}


# ============================================================
# DEFINICIÓN DE ZONAS (coordenadas en formato lon, lat)
# ============================================================
ZONAS = {
    "Zona 1": [(-106.950758,31.806516),(-107.065289,27.527498),(-105.922711,25.700673),(-105.083082,23.894759),(-102.693556,24.325956),(-102.742994,24.835480),(-102.616652,25.268424),(-102.567213,25.872946),(-102.715528,26.272612),(-102.797926,27.492564),(-103.300323,29.006940),(-104.511277,29.642675),(-104.709170,30.210238),(-105.108948,30.746557),(-105.600586,31.074109),(-105.896941,31.319653),(-106.247424,31.507192),(-106.396853,31.747999),(-106.950758,31.806516)],
    "Zona 2": [(-102.624780,25.313842),(-100.696679,25.040421),(-100.426056,25.539121),(-101.737634,26.750127),(-101.715661,27.205399),(-102.767602,27.034276),(-102.715528,26.272612),(-102.567213,25.872946),(-102.624780,25.313842)],
    "Zona 3": [(-101.715486,27.2052446),(-101.7374591,26.7499726),(-100.4258829,25.5389665),(-97.5282427,25.6801416),(-97.1821741,25.6974676),(-97.1467812,25.9612856),(-97.3153830,25.9385286),(-97.3742539,25.9155676),(-97.3850309,25.8246456),(-97.5721887,26.0064306),(-97.7644084,26.0522096),(-97.9512162,26.0557896),(-98.2505928,26.0816955),(-98.4455205,26.2186405),(-98.6158883,26.2283825),(-98.7502241,26.3243675),(-98.9015319,26.3613515),(-99.1146746,26.5096765),(-99.2530945,26.8426905),(-99.4343682,27.0238915),(-99.3739443,27.1852575),(-99.4906731,27.2878235),(-99.4728202,27.4341825),(-99.5222591,27.5925185),(-99.7425498,27.6960455),(-99.8999135,27.8720925),(-101.715486,27.2052446)],
    "Zona 4": [(-97.182343,25.697622),(-100.426056,25.539121),(-100.696679,25.040421),(-101.733864,22.593775),(-98.196266,21.355946),(-97.548073,21.754447),(-97.855690,22.598846),(-97.763012,22.954704),(-97.668922,24.582143),(-97.182343,25.697622)],
    "Zona 6": [(-101.733864,22.593775),(-103.720781,23.157332),(-104.259111,22.783071),(-103.781205,22.067112),(-103.720781,20.434015),(-103.687822,18.606477),(-103.484575,18.335548),(-102.210160,17.917906),(-102.006913,18.006738),(-101.732255,17.792420),(-100.092094,17.985314),(-100.101707,19.204885),(-100.629051,21.338040),(-101.733864,22.593775)],
    "Zona 5": [(-101.7310799,22.591186),(-100.6262887,21.3354497),(-100.0989547,19.2022945),(-97.1169006,19.1659811),(-96.2929393,19.4459281),(-96.3478707,19.5080729),(-96.4028015,19.7589978),(-96.6033001,20.0533943),(-97.1498624,20.6148220),(-97.2762038,20.8562728),(-97.3970515,21.2407636),(-97.2729933,21.5226778),(-97.5453659,21.7518583),(-98.1935467,21.3533563),(-101.7310799,22.591186)],
    "Zona 7": [(-96.295631,19.448514),(-97.119606,19.168569),(-98.777111,19.194358),(-98.606823,18.932167),(-96.643017,18.539411),(-96.285961,18.103985),(-95.113170,17.968181),(-94.679211,17.772126),(-94.311168,18.169238),(-94.492443,18.148360),(-94.599560,18.200551),(-94.605053,18.281416),(-94.701183,18.367458),(-94.794567,18.542015),(-94.989574,18.568053),(-95.028026,18.604500),(-95.176342,18.703387),(-95.448254,18.698184),(-95.678966,18.742406),(-95.920666,18.882798),(-95.948131,19.054228),(-96.003063,19.046440),(-96.079967,19.108738),(-96.110180,19.199546),(-96.299694,19.331777),(-96.295631,19.448514)],
    "Zona 8": [(-94.311168,18.169238),(-94.679211,17.772126),(-94.808446,17.648203),(-94.785349,17.365413),(-94.286699,17.249023),(-93.846018,17.184448),(-92.903940,16.870246),(-91.862986,17.227365),(-91.743364,18.055131),(-92.813074,18.473079),(-92.994578,18.432697),(-93.200571,18.437908),(-93.439524,18.432697),(-94.311168,18.169238)],
    "Zona 9": [(-95.351145,16.071247),(-95.167124,16.168874),(-95.068247,16.179426),(-94.878733,16.211077),(-94.675486,16.197890),(-94.538157,16.182064),(-93.846018,17.184448),(-94.286699,17.249023),(-94.785349,17.365413),(-94.922678,17.066331),(-95.653269,16.160961),(-95.702708,15.875847),(-95.461008,15.992054),(-95.351145,16.071247)],
}

ZONA_COLORS = {
    "Zona 1": "#CE93D8", "Zona 2": "#A1C2FA", "Zona 3": "#B2EBF2",
    "Zona 4": "#F57C00", "Zona 6": "#C5E1A5", "Zona 5": "#FF5252",
    "Zona 7": "#BDBDBD", "Zona 8": "#0288D1", "Zona 9": "#FFEA00",
}
ZONA_OPACIDAD = {
    "Zona 1": 0.35, "Zona 2": 0.46, "Zona 3": 0.47,
    "Zona 4": 0.26, "Zona 6": 0.36, "Zona 5": 0.33,
    "Zona 7": 0.42, "Zona 8": 0.30, "Zona 9": 0.26,
}

VISTA_CENTRO = [23.6, -102.5]
VISTA_ZOOM = 5


# ============================================================
# PERIODOS DE CONSUMO (columnas Consumo_AAAA_MM_GJ)
# ============================================================
MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}

MESES_ES_ABREV = {
    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic',
}


def periodo_de_columna(col):
    """'Consumo_2025_01_GJ' -> (2025, 1); None si no coincide."""
    m = re.match(r'Consumo_(\d{4})_(\d{2})_GJ$', str(col))
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def etiqueta_periodo(col):
    """'Consumo_2025_01_GJ' -> 'Consumo 2025-01 Enero'."""
    p = periodo_de_columna(col)
    if not p:
        return str(col).replace('Consumo_', '').replace('_GJ', '')
    anio, mes = p
    return f"Consumo {anio}-{mes:02d} {MESES_ES.get(mes, mes)}"


def nombre_consumo(col):
    """Nombre legible para un selector/pestaña de consumo."""
    if col == 'Consumo_Total_Periodo_GJ':
        return 'Total del periodo'
    return etiqueta_periodo(col)


def nombre_tab_consumo(col):
    """Etiqueta compacta para las pestañas de consumo mensual."""
    if col == 'Consumo_Total_Periodo_GJ':
        return 'Total del Periodo'
    p = periodo_de_columna(col)
    if not p:
        return str(col).replace('Consumo_', '').replace('_GJ', '')
    anio, mes = p
    return f"{MESES_ES_ABREV.get(mes, mes)} {anio}"


def col_periodo_anterior(col, columnas_disponibles):
    """Dado 'Consumo_2025_02_GJ', devuelve el nombre de la columna del mes
    inmediatamente anterior (p.ej. 'Consumo_2025_01_GJ') si existe en
    `columnas_disponibles`; None si `col` no tiene formato de periodo o no
    hay mes anterior disponible."""
    p = periodo_de_columna(col)
    if not p:
        return None
    anio, mes = p
    if mes == 1:
        anio_prev, mes_prev = anio - 1, 12
    else:
        anio_prev, mes_prev = anio, mes - 1
    candidato = f"Consumo_{anio_prev:04d}_{mes_prev:02d}_GJ"
    return candidato if candidato in columnas_disponibles else None



# Columnas del registro de clientes que se leen de la base de datos.
COLS_CLIENTES = [
    'cp_localizacion', 'id_bp', 'id_instalacion', 'zona_vpm', 'cuenta_contrato',
    'caseta', 'city_gate', 'bp', 'tipo_de_cliente', 'indice_referencia', 'razon_social', 'ldc', 'permiso_distribucion',
    'transportista', 'permiso_transporte', 'estado_localizacion', 'nodo',
    'primer_fecha_inicio_vigencia', 'inicio_vigencia_contrato',
    'fecha_vigencia_actualizada', 'renovacion', 'duracion_renovacion',
    'fecha_pes_efectiva', 'fecha_baja_efectiva',
    'spread_volumetrico_o_interrumpible', 'spread_firme',
]

# Columnas de la tabla de garantías que se leen de la base de datos (pestaña Garantías).
COLS_GARANTIA = [
    'id_bp', 'id_instalacion', 'cuenta_contrato', 'razon_social', 'ldc',
    'renovacion', 'whitelist', 'id_solicitud_garantia', 'fecha_historico',
    'exento', 'monto_solicitado', 'moneda_monto_solicitado', 'id_garantia',
    'numero_documento', 'existencia_fisica', 'fecha_emision', 'fecha_vigencia',
    'fecha_devolucion', 'status_garantia', 'tipo_garantia', 'id_efectivo_sap',
    'emisor_garantia', 'monto_garantia', 'moneda_garantia', 'garantia_aplicada',
    'monto_aplicado_garantia', 'moneda_aplicada_garantia',
]

# Nombres amigables para columnas mostradas en el generador de reportes.
RENOMBRES_REPORTE = {
    'id_instalacion': 'Instalación',
    'bp': 'Cliente',
    'tipo_de_cliente': 'Segmentación',
    'Consumo_Total_Periodo_GJ': 'Consumo Periodo (GJ)',
    'fecha_consumo': 'Fecha Consumo',
    'consumo_gj_diario': 'Consumo Diario (GJ)',
    'fecha_vigencia_actualizada': 'Fecha Vigencia',
    'renovacion': 'Tipo Renovación',
    'ldc': 'LDC',
    'zona_vpm': 'Zonas',
    'indice_referencia': 'Indice',
    'spread_firme': 'Firm Spread (USD/GJ)',
    'spread_volumetrico_o_interrumpible': 'Volumetric Spread (USD/GJ)',
    'nodo': 'Nodo',
    'pct_cliente_zona': 'Porcentaje Cliente por Zona',
    'spread_ponderado': 'Spread Ponderado (USD)',
    'fecha_pes_efectiva': 'Fecha PES Efectiva',
    'fecha_baja_efectiva': 'Fecha Baja Efectiva',
    'caseta': 'Caseta',
    'status': 'Status',
    'duracion_renovacion': 'Duración Renovación',
    'cuenta_contrato': 'Cuenta Contrato',
    'city_gate': 'City Gate',
    'inicio_vigencia_contrato': 'Inicio de Vigencia',
    'primer_fecha_inicio_vigencia': 'Primer Fecha de Inicio de Vigencia',
    'estado_localizacion': 'Estado de Localización',
    'cp_localizacion': 'Código Postal Localización',
    'transportista': 'Transportista',
    'permiso_distribucion': 'Permiso Distribución',
    'permiso_transporte': 'Permiso Transporte',

    
}

# Columnas de fecha del registro de clientes (se muestran solo como fecha, sin hora).
COLUMNAS_FECHA_CLIENTE = [
    'primer_fecha_inicio_vigencia', 'inicio_vigencia_contrato',
    'fecha_vigencia_actualizada', 'fecha_pes_efectiva', 'fecha_baja_efectiva',
]


def generar_renombres_reporte(columnas):
    """Extiende RENOMBRES_REPORTE con mapeos dinámicos para columnas de consumo
    mensual (p.ej. 'Consumo_2026_01_GJ' -> 'Ene 2026').
    Mantiene los renombres estáticos definidos en RENOMBRES_REPORTE."""
    renombres = RENOMBRES_REPORTE.copy()
    for col in columnas:
        if col not in renombres and periodo_de_columna(col) is not None:
            renombres[col] = etiqueta_periodo(col)
    return renombres


def column_config_fechas(columnas, renombres=None):
    """Genera un column_config de st.dataframe que fuerza formato de fecha
    (sin hora) para las columnas de fecha conocidas presentes en `columnas`.
    `renombres` permite mapear el nombre interno al nombre ya renombrado
    para mostrar (p.ej. en el generador de reportes)."""
    renombres = renombres or {}
    cfg = {}
    for col in COLUMNAS_FECHA_CLIENTE:
        nombre_mostrado = renombres.get(col, col)
        if nombre_mostrado in columnas:
            cfg[nombre_mostrado] = st.column_config.DateColumn(nombre_mostrado, format="DD/MM/YYYY")
    return cfg


@st.cache_data(ttl=3600, show_spinner=False)
def _resumen_zona_reporte(resumen_base):
    """Tabla 'Resumen por zona' del Generador de reportes, cacheada por el
    contenido de `resumen_base`. Evita repetir el groupby/agg cuando el
    reporte se vuelve a renderizar (p.ej. al abrir "Manage Columns" o exportar)
    sin que hayan cambiado los filtros de fecha/zona/status."""
    return (
        resumen_base.groupby('zona_vpm', as_index=False)
        .agg({
            'Consumo_Total_Periodo_GJ': 'sum',
            'spread_ponderado': 'sum',
        })
        .rename(columns={'zona_vpm': 'Zona'})
        .sort_values('Consumo_Total_Periodo_GJ', ascending=False)
    )



@st.dialog("Manage Columns", width="large")
def _dialog_manage_columns(columnas_disponibles, columnas_default, columnas_state_key):
    """Modal "Manage Columns" del generador de reportes.

    Izquierda ("Column Options"): buscador + checkbox por columna disponible
    para agregarla o quitarla de la selección.
    Derecha ("Selected Column"): columnas seleccionadas, reordenables por
    arrastre (drag & drop) con `sort_items`.
    Los cambios se guardan en `st.session_state[columnas_state_key]`
    solo al presionar "Save"; "Cancel" descarta lo hecho en el modal.
    """
    renombres = generar_renombres_reporte(columnas_disponibles)
    
    draft = [
        c for c in st.session_state.get("gestion_columnas_draft", columnas_default)
        if c in columnas_disponibles
    ]
    columnas_disponibles_ordenadas = sorted(
        columnas_disponibles,
        key=lambda c: renombres.get(c, c).casefold(),
    )

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("**Column Options**")
        busqueda = st.text_input(
            "Buscar columna", key="gestion_cols_busqueda",
            label_visibility="collapsed", placeholder="🔍 Search Properties",
        )
        filtro_txt = busqueda.strip().lower()
        with st.container(height=320):
            for c in columnas_disponibles_ordenadas:
                etiqueta = renombres.get(c, c)
                if filtro_txt and filtro_txt not in etiqueta.lower():
                    continue
                marcado = c in draft
                nuevo_valor = st.checkbox(etiqueta, value=marcado, key=f"gestion_col_chk_{c}")
                if nuevo_valor and c not in draft:
                    draft.append(c)
                elif not nuevo_valor and c in draft:
                    draft.remove(c)

    with col_der:
        st.markdown(f"**Selected Column**&nbsp;&nbsp;`{len(draft)}`")
        if draft:
            etiquetas_sel = [renombres.get(c, c) for c in draft]
            etiqueta_a_columna = {renombres.get(c, c): c for c in draft}
            # La key debe cambiar cuando cambia el conjunto seleccionado; si no,
            # el componente conserva el orden/estado anterior.
            sortable_key = "gestion_cols_sort_" + "|".join(etiquetas_sel)
            with st.container(height=320):
                etiquetas_orden = sort_items(
                    etiquetas_sel,
                    key=sortable_key,
                    custom_style="""
                    .sortable-item, .sortable-item:hover {
                        background-color: #0077CC;
                        color: #FFFFFF;
                    }
                    """,
                )
            draft = [etiqueta_a_columna[e] for e in etiquetas_orden]
        else:
            st.info("Aún no hay columnas seleccionadas.")

    st.session_state["gestion_columnas_draft"] = draft

    st.divider()
    b_reset, b_cancel, b_save = st.columns(3)
    with b_reset:
        if st.button("Reset to default", use_container_width=True, key="gestion_cols_reset"):
            for c in columnas_disponibles_ordenadas:
                st.session_state.pop(f"gestion_col_chk_{c}", None)
            st.session_state[columnas_state_key] = list(columnas_default)
            st.session_state["gestion_columnas_draft"] = list(columnas_default)
            st.session_state["mostrar_manage_columns"] = False
            st.rerun()
    with b_cancel:
        if st.button("Cancel", use_container_width=True, key="gestion_cols_cancel"):
            st.session_state["mostrar_manage_columns"] = False
            st.rerun()
    with b_save:
        if st.button("Save", type="primary", use_container_width=True, key="gestion_cols_save"):
            st.session_state[columnas_state_key] = list(draft)
            st.session_state["mostrar_manage_columns"] = False
            st.rerun()


# --- Normalización de status ---
_STATUS_MAPA = {
    "activo": "Activo",
    "inactivo": "Inactivo",
    "cancelado": "Cancelado",
    "pre activo": "Pre Activo",
}

# Normalización de status_garantia (pestaña Garantías). A diferencia del status
# de clientes (4 categorías + 'Sin status'), bv_hop_garantia solo trae 3 valores
# reales (Vigente/Liberado/Vencido); no existe un equivalente de 'Pre Activo'.
_STATUS_GARANTIA_MAPA = {
    "vigente": "Vigente",
    "liberado": "Liberado",
    "vencido": "Vencido",
}


def normalizar_status(valor):
    """Normaliza el status a una de 4 categorías conocidas, o 'Sin status'
    si viene vacío/nulo o con un valor no reconocido."""
    if pd.isna(valor):
        return "Sin status"
    texto = str(valor).strip().lower()
    return _STATUS_MAPA.get(texto, "Sin status")


def normalizar_status_serie(serie):
    """Version vectorizada de `normalizar_status` para una Series completa
    (usa .map en vez de .apply fila a fila, más rápido sobre datasets grandes)."""
    texto = serie.astype("string").str.strip().str.lower()
    return texto.map(_STATUS_MAPA).fillna("Sin status")


def normalizar_status_garantia_serie(serie):
    """Version vectorizada análoga a `normalizar_status_serie`, pero para los
    valores propios de `status_garantia` (Vigente/Liberado/Vencido/Sin status)."""
    texto = serie.astype("string").str.strip().str.lower()
    return texto.map(_STATUS_GARANTIA_MAPA).fillna("Sin status")


def fecha_baja_es_valida(fecha):
    """True solo si hay una fecha de baja real (no vacia y no placeholder 9999)."""
    if pd.isna(fecha):
        return False
    try:
        return pd.Timestamp(fecha).year != 9999
    except (ValueError, TypeError):
        return False


def fecha_baja_es_valida_serie(serie_fecha):
    """Version vectorizada de `fecha_baja_es_valida` para una Series de
    datetimes ya parseados (pd.to_datetime), sin apply fila a fila."""
    return serie_fecha.notna() & (serie_fecha.dt.year != 9999)


def month_to_spanish_label(year_month):
    meses_es = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    try:
        year_txt, month_txt = str(year_month).split("-")
        month_num = int(month_txt)
        return f"{meses_es.get(month_num, month_txt)} {year_txt}"
    except (ValueError, AttributeError):
        return str(year_month)


def render_kpi_card(title, value, subtitle="", icon="", accent_color="#0077CC"):
    safe_title = str(title)
    safe_value = str(value)
    safe_subtitle = str(subtitle) if subtitle is not None else ""
    safe_icon = str(icon) if icon else ""

    st.markdown(
        f"""
        <div class="engie-kpi-card">
          <div class="engie-kpi-topline" style="background:{accent_color};"></div>
          <div class="engie-kpi-head">
            <span class="engie-kpi-icon">{safe_icon}</span>
            <span class="engie-kpi-title">{safe_title}</span>
          </div>
          <div class="engie-kpi-main">{safe_value}</div>
          <div class="engie-kpi-sub">{safe_subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini_alert_card(title, value, subtitle="", icon="", color="#0077CC"):
    safe_title = str(title)
    safe_value = str(value)
    safe_subtitle = str(subtitle) if subtitle is not None else ""
    safe_icon = str(icon) if icon else ""

    st.markdown(
        f"""
        <div class="engie-kpi-card" style="padding:10px 12px 10px 12px; min-height:unset; border-radius:16px;">
            <div class="engie-kpi-topline" style="background:{color}; margin-bottom:8px;"></div>
            <div class="engie-kpi-head" style="margin-bottom:4px;">
                <span class="engie-kpi-icon">{safe_icon}</span>
                <span class="engie-kpi-title">{safe_title}</span>
            </div>
            <div class="engie-kpi-main" style="font-size:0.95rem; margin:1px 0 4px 0;">{safe_value}</div>
            <div class="engie-kpi-sub" style="font-size:0.72rem;">{safe_subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generar_pdf_reporte(df, titulo="Reporte", max_filas=500):
    """Genera un PDF tabular (apaisado) a partir de un DataFrame.
    Trunca a `max_filas` para evitar PDFs excesivamente grandes o lentos."""
    df_pdf = df.head(max_filas).copy()
    df_pdf = df_pdf.mask(df_pdf.isna(), "").astype(str)

    columnas = list(df_pdf.columns)

    def _texto_seguro(valor, max_len=40):
        texto = str(valor)
        if len(texto) > max_len:
            texto = texto[:max_len - 1] + "…"
        return texto.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    _ = pdf.set_auto_page_break(auto=True, margin=10)
    _ = pdf.add_page()

    _ = pdf.set_font("Helvetica", "B", 12)
    _ = pdf.cell(0, 8, _texto_seguro(titulo, 120), ln=1)
    _ = pdf.set_font("Helvetica", "", 8)
    _ = pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} - {len(df)} registro(s)", ln=1)
    _ = pdf.ln(2)

    if not columnas:
        _ = pdf.cell(0, 6, "Sin columnas seleccionadas.", ln=1)
        return bytes(pdf.output())

    ancho_disponible = pdf.w - pdf.l_margin - pdf.r_margin
    ancho_col = ancho_disponible / len(columnas)
    alto_fila = 6

    _ = pdf.set_font("Helvetica", "B", 7)
    _ = pdf.set_fill_color(0, 123, 197)
    _ = pdf.set_text_color(255, 255, 255)
    for col in columnas:
        _ = pdf.cell(ancho_col, alto_fila, _texto_seguro(col, 30), border=1, fill=True)
    _ = pdf.ln(alto_fila)

    _ = pdf.set_font("Helvetica", "", 6.5)
    _ = pdf.set_text_color(0, 0, 0)
    for i, fila in enumerate(df_pdf.itertuples(index=False, name=None)):
        if i % 2 == 0:
            _ = pdf.set_fill_color(245, 248, 250)
        else:
            _ = pdf.set_fill_color(255, 255, 255)
        for valor in fila:
            _ = pdf.cell(ancho_col, alto_fila, _texto_seguro(valor), border=1, fill=True)
        _ = pdf.ln(alto_fila)

    if len(df) > max_filas:
        _ = pdf.ln(2)
        _ = pdf.set_font("Helvetica", "I", 7)
        _ = pdf.cell(0, 6, f"Nota: se muestran los primeros {max_filas} de {len(df)} registros.", ln=1)

    return bytes(pdf.output())


# ============================================================
# KML: INFRAESTRUCTURA DE GAS NATURAL
# ============================================================
RUTA_KML = "Infraestructura de Gas Natural en México.kml"
KML_NS = {"k": "http://www.opengis.net/kml/2.2"}

ESTILOS_CAPAS_KML = {
    "puntos de internacion": {
        "emoji": "📍", "color": "#007BC5", "marker_color": "blue", "marker_icon": "log-in"
    },
    "ductos de importacion eua": {
        "emoji": "🟦", "color": "#005B96", "marker_color": "darkblue", "marker_icon": "transfer"
    },
    "sistrangas": {
        "emoji": "🟢", "color": "#2E8B57", "marker_color": "green", "marker_icon": "tasks"
    },
    "sistemas de transporte": {
        "emoji": "🟠", "color": "#E67E22", "marker_color": "orange", "marker_icon": "road"
    },
    "gasoductos en proyecto": {
        "emoji": "🚧", "color": "#C0392B", "marker_color": "red", "marker_icon": "wrench"
    },
    "proyectos plan quinquenal": {
        "emoji": "🟣", "color": "#7D3C98", "marker_color": "purple", "marker_icon": "briefcase"
    },
}

ESTILO_CAPA_KML_DEFAULT = {
    "emoji": "📌", "color": "#007BC5", "marker_color": "cadetblue", "marker_icon": "map-marker"
}


def _kml_color_a_hex(kml_color):
    """Convierte color KML (aabbggrr) a (hex_rgb, opacidad 0-1)."""
    if not kml_color or len(kml_color) != 8:
        return "#007BC5", 0.5
    a = int(kml_color[0:2], 16) / 255.0
    b = kml_color[2:4]
    g = kml_color[4:6]
    r = kml_color[6:8]
    return f"#{r}{g}{b}", round(a, 3)


def _coords(texto):
    """Convierte el bloque <coordinates> en lista [(lat, lon), ...]."""
    puntos = []
    for token in texto.strip().split():
        partes = token.split(",")
        if len(partes) >= 2:
            try:
                lon, lat = float(partes[0]), float(partes[1])
                puntos.append((lat, lon))
            except ValueError:
                continue
    return puntos


def _normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.lower().split())


def normalizar_zona_etiqueta(valor):
    """Normaliza variantes de zona a formato canonico 'Zona N' cuando aplica.

    Ejemplos aceptados: '9', 'zona9', ' ZONA 9 ', 'Zona 09' -> 'Zona 9'.
    Si no se puede mapear a una zona conocida, devuelve el texto limpio original.
    """
    if pd.isna(valor):
        return ""

    texto = " ".join(str(valor).strip().split())
    if not texto:
        return ""

    m = re.search(r"(\d+)", texto)
    if m:
        zona_canonica = f"Zona {int(m.group(1))}"
        if zona_canonica in ZONAS:
            return zona_canonica

    texto_norm = _normalizar_texto(texto)
    for zona in ZONAS.keys():
        if _normalizar_texto(zona) == texto_norm:
            return zona

    # Estandariza zonas nominales (sin numero) para evitar variaciones de
    # mayusculas/espacios (p.ej. 'MAYAKAN' vs 'Mayakan').
    texto_norm = _normalizar_texto(texto)
    return " ".join(parte.capitalize() for parte in texto_norm.split())


def normalizar_zona_serie(serie):
    """Version vectorizada de normalizacion de etiquetas de zona."""
    return serie.map(normalizar_zona_etiqueta)


def normalizar_zona_clave(valor):
    """Devuelve una clave comparable (case-insensitive) para filtros de zona."""
    return _normalizar_texto(normalizar_zona_etiqueta(valor))


def normalizar_zona_clave_serie(serie):
    """Version vectorizada de `normalizar_zona_clave` para Series."""
    return serie.map(normalizar_zona_clave)


def _estilo_capa_kml(nombre_capa):
    return ESTILOS_CAPAS_KML.get(_normalizar_texto(nombre_capa), ESTILO_CAPA_KML_DEFAULT)


def _label_checkbox_capa(nombre_capa):
    estilo = _estilo_capa_kml(nombre_capa)
    return f"{estilo['emoji']} {nombre_capa}"


def _icono_mapa_capa(nombre_capa):
    estilo = _estilo_capa_kml(nombre_capa)
    return folium.Icon(
        color=estilo["marker_color"],
        icon=estilo["marker_icon"],
        prefix="glyphicon",
    )


@st.cache_data(ttl=86400)
def cargar_kml(ruta):
    """Devuelve {carpeta: [ {tipo, nombre, desc, coords, estilo} ]}."""
    tree = ET.parse(ruta)
    root = tree.getroot()

    # 1) Estilos
    estilos = {}
    for st_el in root.iter("{http://www.opengis.net/kml/2.2}Style"):
        sid = st_el.get("id")
        if not sid:
            continue
        info = {"line": "#007BC5", "line_op": 1.0,
                "poly": None, "poly_op": 0.4,
                "width": 2, "icon": None}
        ls = st_el.find("k:LineStyle/k:color", KML_NS)
        if ls is not None:
            info["line"], info["line_op"] = _kml_color_a_hex(ls.text)
        lw = st_el.find("k:LineStyle/k:width", KML_NS)
        if lw is not None:
            info["width"] = float(lw.text)
        ps = st_el.find("k:PolyStyle/k:color", KML_NS)
        if ps is not None:
            info["poly"], info["poly_op"] = _kml_color_a_hex(ps.text)
        ic = st_el.find("k:IconStyle/k:color", KML_NS)
        if ic is not None:
            info["icon"], _ = _kml_color_a_hex(ic.text)
        estilos[sid] = info

    # 2) StyleMap -> estilo normal
    stylemaps = {}
    for sm in root.iter("{http://www.opengis.net/kml/2.2}StyleMap"):
        sid = sm.get("id")
        for pair in sm.findall("k:Pair", KML_NS):
            key = pair.find("k:key", KML_NS)
            url = pair.find("k:styleUrl", KML_NS)
            if key is not None and key.text == "normal" and url is not None:
                stylemaps[sid] = url.text.lstrip("#")

    def resolver_estilo(style_url):
        if not style_url:
            return None
        sid = style_url.lstrip("#")
        sid = stylemaps.get(sid, sid)
        return estilos.get(sid)

    # 3) Carpetas y placemarks
    datos = {}
    for folder in root.iter("{http://www.opengis.net/kml/2.2}Folder"):
        nombre_f = folder.find("k:name", KML_NS)
        nombre_f = nombre_f.text if nombre_f is not None else "Sin nombre"
        elementos = []

        for pm in folder.findall("k:Placemark", KML_NS):
            nom = pm.find("k:name", KML_NS)
            nom = nom.text if nom is not None else ""
            desc = pm.find("k:description", KML_NS)
            desc = desc.text if desc is not None else ""
            su = pm.find("k:styleUrl", KML_NS)
            estilo = resolver_estilo(su.text if su is not None else None)

            punto = pm.find("k:Point/k:coordinates", KML_NS)
            linea = pm.find("k:LineString/k:coordinates", KML_NS)
            poli = pm.find("k:Polygon//k:coordinates", KML_NS)

            if punto is not None:
                elementos.append({"tipo": "punto", "nombre": nom, "desc": desc,
                                  "coords": _coords(punto.text), "estilo": estilo})
            elif linea is not None:
                elementos.append({"tipo": "linea", "nombre": nom, "desc": desc,
                                  "coords": _coords(linea.text), "estilo": estilo})
            elif poli is not None:
                elementos.append({"tipo": "poligono", "nombre": nom, "desc": desc,
                                  "coords": _coords(poli.text), "estilo": estilo})

        datos[nombre_f] = elementos
    return datos


def _dibujar_kml(parent, datos_kml, carpetas_visibles):
    """Añade las carpetas del KML como FeatureGroups al parent (mapa)."""
    for carpeta, elementos in datos_kml.items():
        if carpeta not in carpetas_visibles:
            continue
        estilo_capa = _estilo_capa_kml(carpeta)
        fg = folium.FeatureGroup(name=carpeta, show=True)

        for el in elementos:
            estilo = el["estilo"] or {}
            color = estilo.get("line") or estilo_capa["color"]
            popup = folium.Popup(el["desc"] or el["nombre"], max_width=350)

            if el["tipo"] == "punto" and el["coords"]:
                lat, lon = el["coords"][0]
                folium.Marker(
                    location=[lat, lon],
                    icon=_icono_mapa_capa(carpeta),
                    tooltip=el["nombre"],
                    popup=popup,
                ).add_to(fg)

            elif el["tipo"] == "linea" and len(el["coords"]) > 1:
                folium.PolyLine(
                    locations=el["coords"],
                    color=color,
                    weight=estilo.get("width", 2),
                    opacity=estilo.get("line_op", 1.0),
                    tooltip=el["nombre"],
                    popup=popup,
                ).add_to(fg)

            elif el["tipo"] == "poligono" and len(el["coords"]) > 2:
                folium.Polygon(
                    locations=el["coords"],
                    color=color,
                    weight=estilo.get("width", 2),
                    fill=True,
                    fill_color=estilo.get("poly") or color,
                    fill_opacity=estilo.get("poly_op", 0.4),
                    # Los polígonos grandes no capturan clics para no tapar zonas/clientes
                    interactive=False,
                    tooltip=el["nombre"],
                ).add_to(fg)

        fg.add_to(parent)


# --- Conexión a la base de datos (pyodbc) ---
def get_connection():
    cfg = st.secrets["denodo"]
    conn_str = (
        f"DSN={cfg['DSN']};"
        f"SERVER={cfg['SERVER']};"
        f"DATABASE={cfg['DATABASE']};"
        f"UID={cfg['UID']};"
        f"PWD={cfg['PWD']};"
        "trusted_connection=yes;"
        "TrustServerCertificate=Yes"
    )
    return pyodbc.connect(conn_str)


def read_sql(query):
    conn = get_connection()
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


# --- Carga de datos con caché ---
# cache_resource: devuelve el MISMO objeto en cada rerun (sin copiar/deserializar
# los DataFrames grandes cada vez). Los consumidores no lo mutan in place.
@st.cache_resource(ttl=3600, show_spinner=False)
def cargar_datos():
    """Devuelve (df_clientes, df_consumo_diario).

    df_consumo_diario conserva el detalle DÍA A DÍA (id_instalacion, fecha,
    consumo_gj) sin colapsar a mes, para poder analizar el consumo por
    cualquier rango de fechas exacto. Los distintos periodos (totales,
    mensuales) se construyen sobre la marcha a partir de este detalle
    diario (ver `construir_consumo_mensual`)."""
    cols = COLS_CLIENTES

    r = read_sql(
        f"SELECT {', '.join(cols + ['status'])} "
        "FROM bv_hop_registroclientes"
    )

    con = read_sql(
        "SELECT "
        "    id_instalacion, "
        "    EXTRACT(YEAR FROM fecha) AS anio, "
        "    EXTRACT(MONTH FROM fecha) AS mes, "
        "    EXTRACT(DAY FROM fecha) AS dia, "
        "    SUM(consumo_gj) AS CONSUMO "
        "FROM bv_hop_consumos "
        "WHERE fecha >= '2026-01-01' "
        "  AND archivado = 0 "
        "GROUP BY "
        "    id_instalacion, "
        "    EXTRACT(YEAR FROM fecha), "
        "    EXTRACT(MONTH FROM fecha), "
        "    EXTRACT(DAY FROM fecha) "
    )

    con = con.rename(columns=lambda c: str(c).strip())
    consumo_col = next((c for c in con.columns if c.upper() == 'CONSUMO'), None)
    if consumo_col is None:
        raise KeyError(f"No se encontró la columna de consumo. Columnas disponibles: {list(con.columns)}")

    con['anio'] = pd.to_numeric(con['anio'], errors='coerce').astype('Int64')
    con['mes'] = pd.to_numeric(con['mes'], errors='coerce').astype('Int64')
    con['dia'] = pd.to_numeric(con['dia'], errors='coerce').astype('Int64')
    con = con.dropna(subset=['anio', 'mes', 'dia'])

    # Construye la fecha real (día a día) en lugar de colapsar a "AAAA_MM".
    con['fecha'] = pd.to_datetime(
        con[['anio', 'mes', 'dia']].astype(int).rename(
            columns={'anio': 'year', 'mes': 'month', 'dia': 'day'}
        ),
        errors='coerce',
    )
    con = con.dropna(subset=['fecha'])

    df_consumo_diario = (
        con[['id_instalacion', 'fecha', consumo_col]]
        .rename(columns={consumo_col: 'consumo_gj'})
        .sort_values(['id_instalacion', 'fecha'])
        .reset_index(drop=True)
    )
    df_consumo_diario['consumo_gj'] = pd.to_numeric(df_consumo_diario['consumo_gj'], errors='coerce')

    df = r[cols + ['status']].copy()

    # Normalización del código postal (5 dígitos) para la geocodificación.
    df['cp_localizacion'] = (
        df['cp_localizacion'].astype(str)
        .str.split('.').str[0]
        .str.strip()
    )
    df.loc[df['cp_localizacion'].str.contains('ERROR', case=False, na=False), 'cp_localizacion'] = None
    df['cp_localizacion'] = df['cp_localizacion'].str.zfill(5)

    df = df.dropna(subset=['razon_social'])

    # Crear columna spread_popup (vectorizado — sin apply fila a fila)
    _vol   = pd.to_numeric(df['spread_volumetrico_o_interrumpible'], errors='coerce')
    _firme = pd.to_numeric(df['spread_firme'], errors='coerce')
    _vol_str  = _vol.map(lambda v: f"Volumetric Spread (USD/GJ): {v:.2f}").where(_vol.notna(), "")
    _firm_str = _firme.map(lambda v: f"Firm Spread (USD/GJ): {v:.2f}").where(_firme.notna(), "")
    _sep = ((_vol_str != "") & (_firm_str != "")).map({True: "<br>", False: ""})
    df['spread_popup'] = _vol_str + _sep + _firm_str
    df['status_norm'] = normalizar_status_serie(df['status'])
    df['zona_vpm'] = normalizar_zona_serie(df['zona_vpm'])
    df['zona'] = df['zona_vpm']

    return df, df_consumo_diario


@st.cache_data(ttl=3600)
def cargar_datos_garantias():
    """Devuelve el detalle de garantías (bv_hop_garantia), una fila por
    garantía/documento. Análogo a `cargar_datos()` pero para la pestaña
    Garantías; no incluye consumo diario (esa tabla no aplica aquí).

    Adaptaciones respecto a `cargar_datos()` (bv_hop_garantia no tiene una
    tabla de zonas geográficas como ZONAS, así que se usa `ldc` como
    dimensión equivalente a 'zona'):
      - 'zona' se deriva de `ldc` (en vez de `zona_vpm`).
      - 'status_norm' usa `normalizar_status_garantia_serie` (3 categorías
        reales: Vigente/Liberado/Vencido, más 'Sin status')."""
    cols = COLS_GARANTIA

    df = read_sql(
        f"SELECT {', '.join(cols)} FROM bv_hop_garantia"
    )

    df = df.dropna(subset=['razon_social'])
    df['status_norm'] = normalizar_status_garantia_serie(df['status_garantia'])
    df['zona'] = df['ldc'].astype(str).str.strip()

    return df


def _filtrar_rango_fechas(con, fecha_ini, fecha_fin):
    """Filtra el detalle diario por [fecha_ini, fecha_fin] (inclusive) comparando
    datetime64 directamente (evita `.dt.date`, que crea un objeto Python por fila)."""
    if fecha_ini is None or fecha_fin is None:
        return con
    ini = pd.Timestamp(fecha_ini)
    fin = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1)
    return con[(con['fecha'] >= ini) & (con['fecha'] < fin)]


def construir_consumo_mensual(df_consumo_diario, fecha_ini=None, fecha_fin=None):
    """Agrega el detalle diario de consumo a columnas mensuales
    'Consumo_AAAA_MM_GJ', una fila por id_instalacion.

    Si se pasan `fecha_ini`/`fecha_fin` (objetos date), solo se suman los
    días dentro de ese rango exacto -- por eso un mes parcialmente cubierto
    por el rango aporta solo esos días, y no el mes completo."""
    con = df_consumo_diario
    if con.empty:
        return pd.DataFrame(columns=['id_instalacion'])

    con = _filtrar_rango_fechas(con, fecha_ini, fecha_fin)
    if con.empty:
        return pd.DataFrame(columns=['id_instalacion'])

    # Clave entera AAAAMM (barata de agrupar); los nombres de columna se
    # formatean solo una vez por periodo único, no por fila.
    clave = (con['fecha'].dt.year * 100 + con['fecha'].dt.month).rename('periodo')
    mensual = con.groupby(['id_instalacion', clave])['consumo_gj'].sum().unstack()
    mensual.columns = [f'Consumo_{int(c) // 100:04d}_{int(c) % 100:02d}_GJ' for c in mensual.columns]
    return mensual.reset_index()


def sumar_consumo_periodo(df_consumo_diario, fecha_ini=None, fecha_fin=None):
    """Suma exacta día a día del consumo por id_instalacion dentro del
    rango [fecha_ini, fecha_fin] (ambos inclusive). Devuelve una Serie
    indexada por id_instalacion llamada 'Consumo_Total_Periodo_GJ'."""
    con = df_consumo_diario
    if con.empty:
        return pd.Series(name='Consumo_Total_Periodo_GJ', dtype='float64')

    con = _filtrar_rango_fechas(con, fecha_ini, fecha_fin)
    return con.groupby('id_instalacion')['consumo_gj'].sum().rename('Consumo_Total_Periodo_GJ')


@st.cache_data(ttl=3600, show_spinner=False)
def _consumo_total_cached(fecha_ini, fecha_fin):
    """Versión cacheada de sumar_consumo_periodo, indexada por (fecha_ini, fecha_fin).
    Evita re-agrupar el detalle diario en cada interacción de la UI."""
    _, consumo_diario = cargar_datos()
    return sumar_consumo_periodo(consumo_diario, fecha_ini, fecha_fin).reset_index()


@st.cache_data(ttl=3600, show_spinner=False)
def _consumo_mensual_cached(fecha_ini, fecha_fin):
    """Versión cacheada de construir_consumo_mensual, indexada por (fecha_ini, fecha_fin).
    Evita re-ejecutar el pivot_table sobre el detalle diario en cada rerun."""
    _, consumo_diario = cargar_datos()
    return construir_consumo_mensual(consumo_diario, fecha_ini, fecha_fin)


@st.cache_data(ttl=3600, show_spinner=False)
def _df_geo_con_consumo(status_tuple, fecha_ini, fecha_fin):
    """df_geo base + columnas de consumo, cacheado por (status, fecha_ini, fecha_fin).
    Las geocodificaciones y los merges de consumo solo se recalculan cuando
    cambian el filtro de status o el rango de fechas."""
    df_base = _pipeline_geo(status_tuple)
    if df_base.empty:
        return df_base
    consumo_total = _consumo_total_cached(fecha_ini, fecha_fin)
    df_g = df_base.merge(consumo_total, on='id_instalacion', how='left')
    consumo_mensual = _consumo_mensual_cached(fecha_ini, fecha_fin)
    cols_mensuales = [c for c in consumo_mensual.columns if c != 'id_instalacion']
    if cols_mensuales:
        df_g = df_g.merge(consumo_mensual, on='id_instalacion', how='left')
    return df_g


# --- Geocodificación offline por código postal (México) ---
@st.cache_data(ttl=86400)
def _geocodificar_cps(cp_unicos: tuple) -> pd.DataFrame:
    """Cachea solo el mapa CP -> coordenadas para un conjunto de CPs únicos.
    Recibe una tupla (hashable) para que st.cache_data opere de forma eficiente."""
    nomi = pgeocode.Nominatim('mx')
    if not cp_unicos:
        return pd.DataFrame(columns=['cp_localizacion', 'lat', 'lon'])
    geo_unicos = nomi.query_postal_code(list(cp_unicos))
    return pd.DataFrame({
        'cp_localizacion': list(cp_unicos),
        'lat': geo_unicos['latitude'].to_numpy(),
        'lon': geo_unicos['longitude'].to_numpy(),
    })


def agregar_coordenadas(df):
    """Agrega columnas lat/lon al DataFrame haciendo merge con el mapa
    CP -> coordenadas obtenido de la caché (que solo hashea los CPs únicos)."""
    df = df.copy()
    df['cp_localizacion'] = df['cp_localizacion'].astype('string').str.zfill(5)
    cp_unicos = tuple(sorted(df['cp_localizacion'].dropna().unique().tolist()))
    if not cp_unicos:
        df['lat'] = np.nan
        df['lon'] = np.nan
        return df
    geo_por_cp = _geocodificar_cps(cp_unicos)
    return df.merge(geo_por_cp, on='cp_localizacion', how='left')


# --- Separación de clientes que comparten coordenadas (mismo CP) ---
def aplicar_jitter(df, radio=0.02):
    df = df.copy()
    dup = df.duplicated(subset=['lat', 'lon'], keep=False)
    n = int(dup.sum())
    if n:
        rng = np.random.default_rng(42)
        ang = rng.uniform(0, 2 * np.pi, n)
        rad = rng.uniform(0.002, radio, n)
        df.loc[dup, 'lat'] = df.loc[dup, 'lat'].values + rad * np.sin(ang)
        df.loc[dup, 'lon'] = df.loc[dup, 'lon'].values + rad * np.cos(ang)
    return df


@st.cache_resource
def _polys():
    return {name: Polygon(coords) for name, coords in ZONAS.items()}


def asignar_zona(df):
    """Usa la zona ya definida en el Excel (columna 'Zonas' -> zona_vpm)."""
    df = df.copy()
    df['zona_vpm'] = normalizar_zona_serie(df['zona_vpm'])
    df['zona'] = df['zona_vpm']
    return df


def zona_de_click(lon, lat):
    p = Point(lon, lat)
    for name, poly in _polys().items():
        if poly.contains(p):
            return name
    return None


def calcular_zona_geografica(df):
    """Calcula, a partir de las coordenadas (lat/lon) de cada cliente, la zona
    geográfica real según los polígonos de ZONAS (point-in-polygon).

    Se evita el chequeo fila a fila y la comparación con `None` dentro del loop,
    usando un arreglo de índices válidos y asignación vectorizada sobre esos
    índices. Esto reduce el costo de la comprobación de cada cliente cuando el
    dataframe tiene miles de registros.
    """
    df = df.copy()
    if df.empty:
        df['zona_geografica'] = pd.Series(dtype=object)
        return df

    lat = pd.to_numeric(df['lat'], errors='coerce').to_numpy(dtype=float)
    lon = pd.to_numeric(df['lon'], errors='coerce').to_numpy(dtype=float)
    valido = ~(np.isnan(lat) | np.isnan(lon))
    zona_geografica = np.full(len(df), np.nan, dtype=object)

    if valido.any():
        idx_validos = np.nonzero(valido)[0]
        polys = _polys()
        for name, poly in polys.items():
            # Quedarse solo con los puntos aún sin asignar logra evitar evaluar
            # dos veces el mismo cliente para cada polígono.
            # `zona_geografica` es object (mezcla NaN + strings), usar pd.isna
            # evita TypeError de np.isnan con tipos no numéricos.
            aun_sin_asignar = pd.isna(zona_geografica[idx_validos])
            if not np.any(aun_sin_asignar):
                break
            idx_contenidos = idx_validos[aun_sin_asignar]
            dentro = shapely_contains(poly, lon[idx_contenidos], lat[idx_contenidos])
            zona_geografica[idx_contenidos[dentro]] = name

    df['zona_geografica'] = zona_geografica
    return df


@st.cache_data(ttl=86400, show_spinner=False)
def _pipeline_geo(status_seleccionados: tuple) -> pd.DataFrame:
    """Geocodificación + zona/zona_geografica para los clientes con status en
    `status_seleccionados`, cacheado por esa tupla de status.

    Deliberadamente NO depende del filtro de fecha (rango de consumo): así
    Streamlit reutiliza el resultado cacheado en cada interacción del
    date_input/slider de periodo, en vez de repetir la geocodificación
    (pgeocode) y el cálculo de zona (shapely) que solo dependen del status
    seleccionado, no del rango de fechas."""
    df_todos, _ = cargar_datos()
    df_status = df_todos[df_todos['status_norm'].isin(status_seleccionados)].copy()
    if df_status.empty:
        return df_status
    df_g = agregar_coordenadas(df_status)
    df_g = asignar_zona(df_g)
    df_g = calcular_zona_geografica(df_g)
    return df_g


def bounds_zona(name):
    minx, miny, maxx, maxy = _polys()[name].bounds
    return [[miny, minx], [maxy, maxx]]


def mascara_filtro_cliente_instalacion(df: pd.DataFrame, texto: str) -> pd.Series:
    """Máscara booleana que busca `texto` (sin distinguir mayúsculas/acentos)
    en id_instalacion y en TODAS las columnas de nombre de cliente disponibles
    ('bp' y 'razon_social'), no solo en una. Esto evita falsos "sin resultados"
    cuando una columna existe pero está vacía para ese registro y el nombre
    real está en la otra columna."""
    texto_norm = (
        unicodedata.normalize('NFKD', str(texto))
        .encode('ascii', 'ignore')
        .decode('ascii')
        .strip()
        .lower()
    )
    mascara = pd.Series(False, index=df.index)
    if 'id_instalacion' in df.columns:
        mascara = mascara | df['id_instalacion'].astype(str).str.contains(texto_norm, case=False, na=False, regex=False)
    for col in ('bp', 'razon_social'):
        if col in df.columns:
            col_norm = (
                df[col].astype(str)
                .str.normalize('NFKD')
                .str.encode('ascii', 'ignore')
                .str.decode('ascii')
                .str.lower()
            )
            mascara = mascara | col_norm.str.contains(texto_norm, na=False, regex=False)
    return mascara


@st.cache_data(ttl=3600, show_spinner=False)
def _resumen_zona_tabla(df, col_consumo):
    """Tabla 'Consumo por zona' de la secci\u00f3n Mapa, cacheada por (df, col_consumo).
    Evita repetir el groupby cuando el mapa se reconstruye por acciones que no
    cambian ni los clientes visibles ni la columna de consumo (p.ej. activar
    una capa KML o cerrar el popover de filtros)."""
    return (
        df.dropna(subset=['zona'])
        .groupby('zona')
        .agg(Clientes=('zona', 'size'), Consumo=(col_consumo, 'sum'))
        .reset_index()
        .sort_values('Consumo', ascending=False)
    )


@st.cache_data(ttl=3600, show_spinner=False)
def _top_n_y_ranking_previo(df_local: pd.DataFrame, col: str, col_prev, n_top: int):
    """Calcula el Top N (groupby+sort+merge de estado) y el ranking del
    periodo anterior para la sección Dashboard/Top 10, cacheado por
    (df_local, col, col_prev, n_top). `st.tabs()` ejecuta el cuerpo de TODAS
    las pestañas en cada rerun (no solo la visible); este cacheo evita repetir
    el trabajo de pandas cuando ninguno de estos 4 argumentos cambió entre
    reruns, sin alterar el layout de pestañas ni el resto de la lógica."""
    col_nombre = 'bp' if 'bp' in df_local.columns else 'razon_social'
    usa_instalacion = 'id_instalacion' in df_local.columns
    cols_top = (['id_instalacion'] if usa_instalacion else []) + [col_nombre, col]
    group_cols = (['id_instalacion'] if usa_instalacion else []) + [col_nombre]
    top = (
        df_local[cols_top]
        .dropna(subset=[col])
        .groupby(group_cols, as_index=False)[col]
        .sum()
        .sort_values(col, ascending=False)
        .head(n_top)
        .reset_index(drop=True)
    )
    if usa_instalacion and 'estado_localizacion' in df_local.columns:
        estado_por_instalacion = (
            df_local[['id_instalacion', 'estado_localizacion']]
            .drop_duplicates(subset=['id_instalacion'])
        )
        top = top.merge(estado_por_instalacion, on='id_instalacion', how='left')
    elif 'estado_localizacion' in df_local.columns:
        top['estado_localizacion'] = ''
    top.index = top.index + 1

    ranking_prev = pd.Series(dtype=float)
    if col_prev:
        ranking_prev = (
            df_local[['bp', col_prev]]
            .dropna(subset=[col_prev])
            .groupby('bp')[col_prev]
            .sum()
            .sort_values(ascending=False)
        )
    return top, ranking_prev


def _excel_bytes_desde_hojas(hojas: dict[str, pd.DataFrame]) -> bytes:
    """Construye un archivo Excel en memoria con una hoja por DataFrame."""
    buffer = BytesIO()
    with pd.ExcelWriter(
        buffer,
        engine='xlsxwriter',
        date_format='dd/mm/yyyy',
        datetime_format='dd/mm/yyyy',
    ) as writer:
        for nombre_hoja, df_hoja in hojas.items():
            df_hoja.to_excel(writer, index=False, sheet_name=nombre_hoja[:31])
    return buffer.getvalue()


class HomeButtonControl(MacroElement):
    _template = Template("""
    {% macro script(this, kwargs) %}
    (function() {
        var map = {{this._parent.get_name()}};
        if (!map || map._homeControlAdded) return;

        var HomeControl = L.Control.extend({
            options: { position: '{{this.position}}' },
            onAdd: function(mapRef) {
                var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                var btn = L.DomUtil.create('a', '', container);
                btn.innerHTML = '🏠';
                btn.href = '#';
                btn.title = 'Vista general';
                btn.style.fontSize = '18px';
                btn.style.textAlign = 'center';
                btn.style.lineHeight = '26px';
                btn.style.cursor = 'pointer';
                btn.style.width = '30px';
                btn.style.height = '30px';
                btn.style.display = 'block';

                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.on(btn, 'click', function(e) {
                    L.DomEvent.stop(e);
                    // Reposiciona el mapa en la vista general.
                    mapRef.setView([{{this.center_lat}}, {{this.center_lon}}], {{this.zoom}});
                    // Emite un "clic" en una coordenada centinela cercana a (0,0)
                    // (con un pequeño desplazamiento único por pulsación) que
                    // Python reconoce vía st_folium para resetear la zona.
                    var tag = (Date.now() % 1000000) * 1e-9;  // < 0.001
                    mapRef.fire('click', { latlng: L.latLng(0, tag) });
                });
                return container;
            }
        });

        map.addControl(new HomeControl());
        map._homeControlAdded = true;
    })();
    {% endmacro %}
    """)

    def __init__(self, center, zoom, position='topleft'):
        super().__init__()
        self._name = 'HomeButtonControl'
        self.center_lat = center[0]
        self.center_lon = center[1]
        self.zoom = zoom
        self.position = position


@st.cache_resource(show_spinner=False)
def _cargar_textura_tierra():
    """Carga `earth_texture.jpg` (imagen equirectangular real de la Tierra,
    ubicada junto a este script) y la devuelve como array numpy RGB. Se usa
    una resolución alta (2700x1350) para que el zoom final hacia México no
    se vea borroso/pixelado. Se cachea una sola vez por proceso de
    Streamlit."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "earth_texture.jpg")
    try:
        img = Image.open(ruta).convert("RGB").resize((2700, 1350), Image.LANCZOS)
        return np.asarray(img)
    except Exception:
        return None


def _proyectar_orto_textura(textura, lon0_deg, lat0_deg, radio_px, size, canvas_r, roll_deg=0.0):
    """Remapea la textura equirectangular a una proyección ortográfica (vista
    de esfera 3D real) centrada en (lat0_deg, lon0_deg), con `radio_px` como
    radio aparente de la esfera en píxeles (mayor que `canvas_r` = efecto de
    zoom, ya que solo se ve una porción más pequeña y central del planeta).
    `roll_deg` inclina el eje de rotación visible (como la inclinación axial
    real de la Tierra, ~23°), rotando el plano de la imagen antes de
    proyectar, para que el planeta no gire siempre "derecho".
    Devuelve una imagen PIL RGBA (transparente fuera del disco)."""
    H, W, _ = textura.shape
    cx = cy = size / 2
    yi, xi = np.mgrid[0:size, 0:size]
    x = xi - cx
    y = cy - yi  # y positivo hacia arriba

    if roll_deg:
        rr = np.radians(roll_deg)
        cr, sr = np.cos(rr), np.sin(rr)
        x, y = x * cr - y * sr, x * sr + y * cr

    rho = np.sqrt(x ** 2 + y ** 2)
    visible = rho <= canvas_r
    rho_c = np.clip(rho, 1e-9, radio_px)
    c = np.arcsin(np.clip(rho_c / radio_px, -1, 1))
    lat0 = np.radians(lat0_deg)
    lon0 = np.radians(lon0_deg)
    sin_c, cos_c = np.sin(c), np.cos(c)
    lat = np.arcsin(cos_c * np.sin(lat0) + (y * sin_c * np.cos(lat0)) / rho_c)
    lon = lon0 + np.arctan2(x * sin_c, rho_c * np.cos(lat0) * cos_c - y * sin_c * np.sin(lat0))

    lon_deg = (np.degrees(lon) + 180) % 360 - 180
    lat_deg = np.clip(np.degrees(lat), -90, 90)
    col = ((lon_deg + 180) / 360 * W).astype(int) % W
    row = np.clip(((90 - lat_deg) / 180 * H).astype(int), 0, H - 1)

    out = np.zeros((size, size, 4), dtype=np.uint8)
    out[visible, :3] = textura[row[visible], col[visible]]
    out[visible, 3] = 255
    return Image.fromarray(out, mode="RGBA")


def _geometria_rotacion_fija(lat0_deg, radio_px, size, canvas_r, roll_deg, H, W):
    """Precalcula toda la geometría de la proyección ortográfica que NO
    depende de la longitud (lon0) cuando lat0/radio/roll se mantienen fijos
    (fase de giro puro del planeta, la mayoría de los fotogramas). Con
    lat0/radio/roll constantes, la fila de textura (`row`) y el offset
    angular de longitud (`delta_lon_deg`) resultan CONSTANTES por píxel: lo
    único que cambia entre fotogramas es `lon0`, que se suma directo a
    `delta_lon_deg`. Esto evita recalcular arcsin/arctan2 sobre toda la
    grilla en cada fotograma, dejando solo una suma + módulo + indexado."""
    cx = cy = size / 2
    yi, xi = np.mgrid[0:size, 0:size]
    x = xi - cx
    y = cy - yi

    if roll_deg:
        rr = np.radians(roll_deg)
        cr, sr = np.cos(rr), np.sin(rr)
        x, y = x * cr - y * sr, x * sr + y * cr

    rho = np.sqrt(x ** 2 + y ** 2)
    visible = rho <= canvas_r
    rho_c = np.clip(rho, 1e-9, radio_px)
    c = np.arcsin(np.clip(rho_c / radio_px, -1, 1))
    lat0 = np.radians(lat0_deg)
    sin_c, cos_c = np.sin(c), np.cos(c)
    lat = np.arcsin(cos_c * np.sin(lat0) + (y * sin_c * np.cos(lat0)) / rho_c)
    delta = np.arctan2(x * sin_c, rho_c * np.cos(lat0) * cos_c - y * sin_c * np.sin(lat0))

    lat_deg = np.clip(np.degrees(lat), -90, 90)
    row = np.clip(((90 - lat_deg) / 180 * H).astype(int), 0, H - 1)
    delta_lon_deg = np.degrees(delta)
    return visible, row, delta_lon_deg


def _frame_rotacion_rapida(textura, visible, row, delta_lon_deg, lon0_deg, size, W):
    """Genera un fotograma reutilizando la geometría precalculada por
    `_geometria_rotacion_fija`; solo desplaza la longitud del frame actual,
    mucho más barato que recalcular la proyección ortográfica completa."""
    lon_deg = (lon0_deg + delta_lon_deg + 180) % 360 - 180
    col = ((lon_deg + 180) / 360 * W).astype(int) % W
    out = np.zeros((size, size, 4), dtype=np.uint8)
    out[visible, :3] = textura[row[visible], col[visible]]
    out[visible, 3] = 255
    return Image.fromarray(out, mode="RGBA")


def mostrar_intro_globo(destino_lat, destino_lon, zoom_destino=7.0):
    """Animación de introducción con un globo terráqueo REAL: remapea la
    imagen `earth_texture.jpg` (textura satelital real) a una proyección
    ortográfica (esfera 3D genuina, calculada con la fórmula inversa de
    proyección ortográfica) fotograma a fotograma, primero girando el
    planeta y luego haciendo zoom hacia México. Cada fotograma se muestra
    como una imagen PNG embebida (base64) sobre el MISMO `st.empty()`
    placeholder (elemento HTML nativo, no un componente con iframe, por lo
    que no hay parpadeo por remount). Solo se ejecuta una vez por sesión de
    Streamlit (`st.session_state`)."""
    if st.session_state.get("intro_globo_mostrada"):
        return
    st.session_state["intro_globo_mostrada"] = True

    textura = _cargar_textura_tierra()
    if textura is None:
        return  # earth_texture.jpg no disponible: se omite la intro sin error visible

    placeholder = st.empty()
    ALTO_CONTENEDOR = 600  # mismo alto que st_folium(..., height=600) para no saltar de tamaño
    SIZE = 460
    CANVAS_R = SIZE / 2 - 6
    TILT = 20.0  # inclinación axial visible, similar a la de la Tierra real (~23.4°)

    def _html_de_imagen(img):
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"""
        <div style="display:flex;justify-content:center;align-items:center;
                    width:100%;height:{ALTO_CONTENEDOR}px;
                    background:radial-gradient(ellipse at center, #060912 0%, #000103 75%);
                    border-radius:16px;box-sizing:border-box;">
            <img src="data:image/png;base64,{b64}" width="{SIZE}" height="{SIZE}"
                 style="border-radius:50%;display:block;
                        box-shadow:0 0 55px rgba(80,170,255,0.55), 0 0 130px rgba(60,140,255,0.3);" />
        </div>
        """

    def _frame_html(lon0, lat0, radio_px, roll=TILT):
        img = _proyectar_orto_textura(textura, lon0, lat0, radio_px, SIZE, CANVAS_R, roll_deg=roll)
        return _html_de_imagen(img)

    # Fase de giro: lat0/radio/roll fijos, solo cambia la longitud. Se
    # precalcula la geometría UNA vez (arcsin/arctan2 sobre toda la grilla)
    # y cada fotograma solo hace una suma + módulo + indexado, en vez de
    # recalcular la proyección ortográfica completa 100 veces.
    H, W, _ = textura.shape
    visible_giro, row_giro, delta_lon_giro = _geometria_rotacion_fija(
        12, CANVAS_R, SIZE, CANVAS_R, TILT, H, W
    )

    pasos_giro = 60
    lon = -50.0
    for i in range(pasos_giro):
        lon = -50 + i * (360 / pasos_giro)  # una vuelta completa, suave
        img = _frame_rotacion_rapida(textura, visible_giro, row_giro, delta_lon_giro, lon, SIZE, W)
        placeholder.markdown(_html_de_imagen(img), unsafe_allow_html=True)
        time.sleep(0.005)

    pasos_zoom = 16
    lon_ini, lat_ini = lon, 12
    # Fase 1: primero solo gira/inclina hasta encuadrar México a zoom 1x
    # (evita "pasar zoomeado" por otros países en el camino).
    for i in range(1, pasos_zoom + 1):
        t = i / pasos_zoom
        t_suave = t * t * (3 - 2 * t)
        lon_i = lon_ini + (destino_lon - lon_ini) * t_suave
        lat_i = lat_ini + (destino_lat - lat_ini) * t_suave
        roll_i = TILT * (1 - t_suave)
        placeholder.markdown(_frame_html(lon_i, lat_i, CANVAS_R, roll=roll_i), unsafe_allow_html=True)
        time.sleep(0.04)

    # Fase 2: ya centrado y sin inclinación, ahora sí hace zoom hacia México.
    pasos_acercar = 14
    for i in range(1, pasos_acercar + 1):
        t = i / pasos_acercar
        t_suave = t * t * (3 - 2 * t)
        radio_i = CANVAS_R * (1 + (zoom_destino - 1) * t_suave)
        placeholder.markdown(_frame_html(destino_lon, destino_lat, radio_i, roll=0.0), unsafe_allow_html=True)
        time.sleep(0.045)

    time.sleep(0.4)
    placeholder.empty()



# --- Construcción del mapa (objeto folium) ---
@st.cache_data(ttl=3600, show_spinner=False)
def _stats_zona_mapa(df, col_consumo):
    """Consumo total y n° de clientes por zona, cacheado por (df, col_consumo).
    `crear_mapa` se reconstruye en cada rerun de la sección Mapa (p.ej. al
    activar/desactivar una capa KML o buscar un CP), aunque el dataframe de
    clientes y la columna de consumo elegida no cambien; cachear estos dos
    groupby evita repetir esa agregación cuando el contenido es idéntico."""
    if 'zona' not in df.columns:
        return pd.Series(dtype='float64'), pd.Series(dtype='int64')
    consumo_zona = df.groupby('zona')[col_consumo].sum()
    clientes_zona = df.groupby('zona').size()
    return consumo_zona, clientes_zona


def crear_mapa(df, col_consumo, zona_sel, datos_kml=None, carpetas_kml=None, min_gj=0, cp_marker=None):
    m = folium.Map(
        location=VISTA_CENTRO,
        zoom_start=VISTA_ZOOM,
        min_zoom=VISTA_ZOOM,
        tiles="OpenStreetMap",
        max_bounds=True,
        min_lat=12.0,
        max_lat=35.0,
        min_lon=-120.0,
        max_lon=-84.0,
    )

    consumo_zona, clientes_zona = _stats_zona_mapa(df, col_consumo)

    # --- Capa 1: polígonos de zonas ---
    for name, coords in ZONAS.items():
        total = float(consumo_zona.get(name, 0) or 0)
        n = int(clientes_zona.get(name, 0) or 0)
        locations = [(lat, lon) for lon, lat in coords]
        color = ZONA_COLORS.get(name, "#007BC5")
        opac = ZONA_OPACIDAD.get(name, 0.35)

        tooltip_html = (
            f"<b>{name}</b><br>"
            f"Clientes: {n}<br>"
            f"Consumo: {total:,.0f} GJ<br>"
            f"<i>Clic para explorar</i>"
        )

        folium.Polygon(
            locations=locations,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=opac,
            tooltip=folium.Tooltip(tooltip_html),
        ).add_to(m)

    # --- Capa 2: infraestructura KML (debajo de los clientes) ---
    if datos_kml and carpetas_kml:
        _dibujar_kml(m, datos_kml, carpetas_kml)

    # --- Capa 3: burbujas de clientes (SIEMPRE encima) ---
    if zona_sel and zona_sel != "Vista general":
        df_z = df[df['zona'] == zona_sel].copy()
        df_z[col_consumo] = df_z[col_consumo].fillna(0)
        df_z = df_z.dropna(subset=['lat', 'lon'])
        if min_gj > 0:
            df_z = df_z[pd.to_numeric(df_z[col_consumo], errors='coerce').fillna(0) >= min_gj].copy()
        df_z = aplicar_jitter(df_z)
        if 'fecha_vigencia_actualizada' in df_z.columns:
            df_z['fecha_vigencia_popup'] = (
                pd.to_datetime(df_z['fecha_vigencia_actualizada'], errors='coerce')
                .dt.strftime('%d/%m/%Y').fillna('N/D')
            )
        else:
            df_z['fecha_vigencia_popup'] = 'N/D'

        if not df_z.empty:
            consumos = df_z[col_consumo]
            max_c = consumos.max()
            if pd.isna(max_c) or max_c == 0:
                max_c = 1

            pos = consumos[consumos > 0]
            if len(pos):
                l1, l2, l3, l4 = pos.quantile([0.2, 0.4, 0.6, 0.8]).tolist()
            else:
                l1, l2, l3, l4 = [max_c * f for f in (0.2, 0.4, 0.6, 0.8)]

            usar_cluster = len(df_z) >= UMBRAL_CLUSTER

            if not usar_cluster:
                # Colores/radios calculados una sola vez, vectorizado con numpy,
                # en vez de llamar a una función Python (color_de) por cada fila
                # dentro del loop de creación de marcadores.
                consumo_arr = pd.to_numeric(df_z[col_consumo], errors='coerce').fillna(0).to_numpy(dtype=float)
                radios_arr = 5 + (consumo_arr / max_c) * 25
                colores_arr = np.select(
                    [consumo_arr <= l1, consumo_arr <= l2, consumo_arr <= l3, consumo_arr <= l4],
                    ['#CCD4DA', '#7FA8D8', '#278CBC', '#007BC5'],
                    default='#005C9A',
                )

                fg = folium.FeatureGroup(name=f"Clientes {zona_sel}")
                columnas = df_z.columns
                idx_lat = columnas.get_loc('lat')
                idx_lon = columnas.get_loc('lon')
                idx_consumo = columnas.get_loc(col_consumo)
                idx_id = columnas.get_loc('id_instalacion')
                idx_estado = columnas.get_loc('estado_localizacion')
                idx_vig = columnas.get_loc('fecha_vigencia_popup')
                idx_nombre = columnas.get_loc('bp') if 'bp' in columnas else columnas.get_loc('razon_social')
                idx_spread = columnas.get_loc('spread_popup') if 'spread_popup' in columnas else None

                for i, row in enumerate(df_z.itertuples(index=False, name=None)):
                    c = consumo_arr[i]
                    radio = radios_arr[i]
                    col = colores_arr[i]
                    spread_html = row[idx_spread] if idx_spread is not None else ''
                    tooltip_parts = [
                        f"<b>{row[idx_nombre]}</b><br>",
                        f"Instalación: {row[idx_id]}<br>",
                        f"Estado: {row[idx_estado]}<br>",
                        f"Fecha Vigencia: {row[idx_vig]}<br>",
                        f"Consumo: {c:,.0f} GJ"
                    ]
                    if spread_html:
                        tooltip_parts.append(f"<br>{spread_html}")
                    tooltip = "".join(tooltip_parts)
                    folium.CircleMarker(
                        location=[row[idx_lat], row[idx_lon]],
                        radius=radio,
                        color=col,
                        fill=True,
                        fill_color=col,
                        fill_opacity=0.7,
                        weight=1,
                        tooltip=folium.Tooltip(tooltip, sticky=True),
                    ).add_to(fg)
                fg.add_to(m)

            else:
                c1, c2, c3, c4 = max_c * 1, max_c * 3, max_c * 6, max_c * 12

                cols_cluster = ['lat', 'lon', col_consumo, 'bp',
                                'id_instalacion', 'estado_localizacion', 'fecha_vigencia_popup']
                # fallback si bp no está en el df por caché antiguo
                if 'bp' not in df_z.columns:
                    cols_cluster[3] = 'razon_social'
                if 'spread_popup' in df_z.columns:
                    cols_cluster.append('spread_popup')
                data = df_z[cols_cluster].copy()
                if 'spread_popup' not in data.columns:
                    data['spread_popup'] = ''
                data_list = data.values.tolist()

                callback = """
                function(row) {
                    var consumo = row[2] || 0;
                    var nombre  = row[3];
                    var instalacion = row[4];
                    var estado  = row[5];
                    var vigencia = row[6];
                    var spread  = row[7] || '';
                    var maxc    = MAXC;
                    var color;
                    if      (consumo <= L1) { color = '#CCD4DA'; }
                    else if (consumo <= L2) { color = '#7FA8D8'; }
                    else if (consumo <= L3) { color = '#278CBC'; }
                    else if (consumo <= L4) { color = '#007BC5'; }
                    else                    { color = '#005C9A'; }
                    var radio = 5 + (consumo / maxc) * 25;
                    var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {
                        radius: radio, color: color, fillColor: color,
                        fillOpacity: 0.7, weight: 1
                    });
                    marker.options.consumo = consumo;
                    var contenido = '<b>' + nombre + '</b><br>Instalación: ' + instalacion +
                        '<br>Estado: ' + estado +
                        '<br>Fecha Vigencia: ' + vigencia + '<br>Consumo: ' +
                        Math.round(consumo).toLocaleString() + ' GJ';
                    if (spread && spread.trim() !== '') {
                        contenido += '<br>' + spread;
                    }
                    marker.bindTooltip(contenido, {sticky: true, direction: 'top', opacity: 0.95});
                    return marker;
                }
                """
                callback = (callback.replace('MAXC', str(max_c))
                            .replace('L1', str(l1)).replace('L2', str(l2))
                            .replace('L3', str(l3)).replace('L4', str(l4)))

                icon_create = """
                function(cluster) {
                    var markers = cluster.getAllChildMarkers();
                    var sum = 0;
                    for (var i = 0; i < markers.length; i++) {
                        sum += (markers[i].options.consumo || 0);
                    }
                    var color;
                    if      (sum <= C1) { color = '#CCD4DA'; }
                    else if (sum <= C2) { color = '#7FA8D8'; }
                    else if (sum <= C3) { color = '#278CBC'; }
                    else if (sum <= C4) { color = '#007BC5'; }
                    else                { color = '#005C9A'; }
                    var size = 40 + Math.min(markers.length, 40);
                    var texto = Math.round(sum).toLocaleString() + ' GJ';
                    var icon = L.divIcon({
                        html: '<div title="' + markers.length + ' clientes - ' + texto +
                              '" style="background-color:' + color +
                              ';opacity:0.9;border-radius:50%;display:flex;align-items:center;' +
                              'justify-content:center;color:white;font-weight:bold;' +
                              'font-size:10px;text-align:center;line-height:1.1;' +
                              'width:' + size + 'px;height:' + size + 'px;">' + texto + '</div>',
                        className: 'engie-cluster',
                        iconSize: L.point(size, size),
                        iconAnchor: L.point(size / 2, size / 2)
                    });
                    return icon;
                }
                """
                icon_create = (icon_create.replace('C1', str(c1)).replace('C2', str(c2))
                               .replace('C3', str(c3)).replace('C4', str(c4)))

                FastMarkerCluster(
                    data=data_list,
                    callback=callback,
                    icon_create_function=icon_create
                ).add_to(m)

        if zona_sel in ZONAS:
            m.fit_bounds(bounds_zona(zona_sel))
        elif not df_z.empty:
            lat_min = float(df_z['lat'].min())
            lat_max = float(df_z['lat'].max())
            lon_min = float(df_z['lon'].min())
            lon_max = float(df_z['lon'].max())
            if lat_min == lat_max:
                lat_min -= 0.15
                lat_max += 0.15
            if lon_min == lon_max:
                lon_min -= 0.15
                lon_max += 0.15
            m.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])

    # --- Marcador de búsqueda por código postal ---
    # Bloque desactivado temporalmente: se comenta para quitar la marca roja
    # y el comportamiento de búsqueda por CP en el mapa.
    # if cp_marker:
    #     lat_cp = cp_marker.get('lat')
    #     lon_cp = cp_marker.get('lon')
    #     cp_val = cp_marker.get('cp', '')
    #     n_cp = cp_marker.get('n_clientes', 0)
    #     if lat_cp is not None and lon_cp is not None and not (pd.isna(lat_cp) or pd.isna(lon_cp)):
    #         popup_html = (
    #             f"<b>Código Postal: {cp_val}</b><br>"
    #             f"Clientes en este CP: {n_cp}"
    #         )
    #         folium.Marker(
    #             location=[lat_cp, lon_cp],
    #             icon=folium.Icon(color='red', icon='search', prefix='glyphicon'),
    #             tooltip=f"📍 CP buscado: {cp_val}  ({n_cp} clientes)",
    #             popup=folium.Popup(popup_html, max_width=220),
    #         ).add_to(m)
    #         if zona_sel == "Vista general":
    #             m.fit_bounds([
    #                 [lat_cp - 0.4, lon_cp - 0.4],
    #                 [lat_cp + 0.4, lon_cp + 0.4],
    #             ])

    # Agregar botón de casa para "Vista general"
    HomeButtonControl(VISTA_CENTRO, VISTA_ZOOM, position='topleft').add_to(m)

    # LayerControl al final (para que registre todas las capas)
    #if datos_kml and carpetas_kml:
        #folium.LayerControl(collapsed=False).add_to(m)

    return m


def _calcular_step_gj(limite_max: int) -> int:
    """Escala el paso del slider según el tamaño del rango para evitar saltos bruscos."""
    if limite_max <= 100:
        return 1
    if limite_max <= 1000:
        return 10
    if limite_max <= 5000:
        return 25
    if limite_max <= 25000:
        return 100
    if limite_max <= 100000:
        return 250
    if limite_max <= 500000:
        return 500
    return 1000


def _calcular_limite_slider_gj(serie):
    """Calcula un tope útil para el filtro usando los percentiles altos, no el máximo
    aislado de la cola, para mantener sensibilidad en zonas con colas muy altas."""
    if serie is None or len(serie) == 0:
        return 0, 1

    valores = pd.to_numeric(serie, errors='coerce').fillna(0)
    valores = valores[valores > 0]
    if valores.empty:
        return 0, 1

    max_val = int(valores.max())
    valores_unicos = valores.nunique()
    if valores_unicos <= 1:
        return max_val, _calcular_step_gj(max_val)

    q90 = float(valores.quantile(0.90))
    q95 = float(valores.quantile(0.95))
    q97 = float(valores.quantile(0.97))
    q99 = float(valores.quantile(0.99))

    # Si la cola es muy alta, el slider debe basarse en los percentiles altos y no en
    # el máximo extremo; esto evita que un cliente aislado lo haga saltar todo.
    if max_val > q95 * 1.5:
        # Cuando existen colas altas, el tope útil del filtro se estabiliza en el 95-97%
        # para que el movimiento del slider sea gradual y no dependa del valor extremo.
        limite = int(min(q97, q95 * 1.10))
    else:
        limite = int(max(q95 * 1.15, q99 * 0.9, q90 * 1.8))

    # Mantén el límite en un rango observable y razonable.
    limite = max(1, min(int(limite), max_val))
    return limite, _calcular_step_gj(limite)


def sync_gj_global_from_slider():
    maximo = int(st.session_state.get("max_gj_global", 0))
    valor = int(st.session_state.get("min_gj_global_slider", 0))
    valor = max(0, min(valor, maximo))
    st.session_state["min_gj_global"] = valor
    st.session_state["min_gj_global_exact"] = valor


def sync_gj_global_from_exact():
    maximo = int(st.session_state.get("max_gj_global", 0))
    valor_raw = st.session_state.get("min_gj_global_exact")
    valor = int(valor_raw) if valor_raw is not None else 0
    valor = max(0, min(valor, maximo))
    st.session_state["min_gj_global"] = valor
    st.session_state["min_gj_global_slider"] = valor


def reconciliar_gj_global():
    """Asegura que slider y número exacto siempre compartan el mismo valor, aunque
    el rango o la zona cambie entre reruns."""
    maximo = int(st.session_state.get("max_gj_global", 0))
    if maximo <= 0:
        st.session_state["min_gj_global"] = 0
        st.session_state["min_gj_global_slider"] = 0
        st.session_state["min_gj_global_exact"] = 0
        return

    slider_val = int(st.session_state.get("min_gj_global_slider", 0))
    exact_raw = st.session_state.get("min_gj_global_exact")
    exact_val = int(exact_raw) if exact_raw not in (None, "") else slider_val
    valor = max(0, min(int(slider_val if slider_val == exact_val else exact_val), maximo))
    st.session_state["min_gj_global"] = valor
    st.session_state["min_gj_global_slider"] = valor
    st.session_state["min_gj_global_exact"] = valor


def sync_zona_widget_unica():
    """Mantiene una sola zona seleccionada y conserva la mas reciente."""
    seleccionadas = st.session_state.get("zona_widget_multi", [])
    opciones_zona = st.session_state.get("zona_widget_options", [])

    # "Select all" del multiselect equivale a quitar filtro de zona.
    if opciones_zona and len(seleccionadas) >= len(opciones_zona):
        st.session_state["zona_widget_multi"] = []
        st.session_state["zona_widget"] = "Vista general"
        return

    if not seleccionadas:
        st.session_state["zona_widget"] = "Vista general"
        return

    zona_activa = seleccionadas[-1]
    st.session_state["zona_widget_multi"] = [zona_activa]
    st.session_state["zona_widget"] = zona_activa


# --- Interfaz ---

# ===== SIDEBAR DE NAVEGACIÓN =====
SECCIONES_SIDEBAR = ["Mapa", "Reportes", "Dashboard", "Gestión Comercial"]
SECCIONES_SIDEBAR_LEGACY = {
    "🗺️  Mapa": "Mapa",
    "📄  Reportes": "Reportes",
    "📊  Dashboard": "Dashboard",
    "💼  Gestión Comercial": "Gestión Comercial",
}
seccion_guardada = st.session_state.get("sidebar_selected_section_gas", SECCIONES_SIDEBAR[0])
seccion_guardada = SECCIONES_SIDEBAR_LEGACY.get(seccion_guardada, seccion_guardada)
st.session_state["sidebar_selected_section_gas"] = (
    seccion_guardada if seccion_guardada in SECCIONES_SIDEBAR else SECCIONES_SIDEBAR[0]
)
with st.sidebar:
    with st.container(key="sidebar_brand_block"):
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_engie_blanco.png")
        if os.path.isfile(logo_path):
            with open(logo_path, "rb") as logo_file:
                logo_b64 = base64.b64encode(logo_file.read()).decode("ascii")
            st.markdown(
                f'<div class="engie-logo-wrap"><img src="data:image/png;base64,{logo_b64}" alt="ENGIE"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="engie-logo">ENGIE</div>', unsafe_allow_html=True)
        st.markdown('<div class="engie-sub">Data & Digital for Gas Commercial</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="engie-section engie-nav-section">Navegación</div>', unsafe_allow_html=True)
    with st.container(key="sidebar_nav_shell"):
        for idx, section_name in enumerate(SECCIONES_SIDEBAR):
            state_suffix = "active" if section_name == st.session_state["sidebar_selected_section_gas"] else "inactive"
            with st.container(key=f"sidebar_nav_item_{idx}_{state_suffix}"):
                if st.button(section_name, key=f"sidebar_nav_btn_gas_{idx}", use_container_width=True):
                    if st.session_state["sidebar_selected_section_gas"] != section_name:
                        st.session_state["sidebar_selected_section_gas"] = section_name
                        st.rerun()
    seccion = st.session_state["sidebar_selected_section_gas"]
    st.divider()
    periodo_sidebar_container = st.container(key="sidebar_period_section")

# El navegador conserva el scroll al cambiar de sección; se marca el cambio aquí.
_should_scroll_top = st.session_state.get("_active_view") != seccion
st.session_state["_active_view"] = seccion

_status_options = ["Activo", "Inactivo", "Cancelado", "Pre Activo", "Sin status"]
if "status_filter_gas" not in st.session_state:
    st.session_state.status_filter_gas = ["Activo"]
selected_status_gas = st.session_state.get("status_filter_gas", ["Activo"])

# ===== CARGA Y FILTRADO (común a todas las secciones) =====
with st.spinner("Consultando la base de datos..."):
    resultado, consumo_diario = cargar_datos()
resultado_todos_status = resultado.copy()

# --- Filtro de status (aplicado antes de todo el análisis) ---
if selected_status_gas:
    resultado = resultado[resultado['status_norm'].isin(selected_status_gas)].copy()
else:
    resultado = resultado.iloc[0:0].copy()

st.title("Registro de Clientes y Consumos Diarios")

# Nota: el filtro por Id de Instalación se define de forma independiente
# dentro de cada sección (Mapa, Clientes, Top 10), para que no afecte a las demás.
df_mostrar = resultado

# ===== FILTRO DE PERIODO (rango de días, calculado día a día) =====
cols_periodo_sel = []
cols_consumo = []
fecha_ini = fecha_fin = None

if not consumo_diario.empty:
    fecha_min = consumo_diario['fecha'].min().date()
    fecha_max = consumo_diario['fecha'].max().date()

    with periodo_sidebar_container:
        st.markdown('<div class="engie-section">Periodo de consumo</div>', unsafe_allow_html=True)
        if fecha_min == fecha_max:
            fecha_ini = fecha_fin = fecha_min
            st.caption(f"Único día con datos disponible: **{fecha_min.strftime('%d/%m/%Y')}**")
        else:
            rango = st.date_input(
                "📅 Periodo de consumo",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                format="DD/MM/YYYY",
                help="Selecciona la fecha inicial y final. El consumo se calcula día a día dentro del rango elegido (no se redondea a meses completos).",
            )

            # date_input devuelve una tupla al elegir ambas fechas; mientras solo hay
            # una seleccionada, se usa esa fecha como inicio y fin provisionalmente.
            if isinstance(rango, (list, tuple)):
                fecha_ini = rango[0]
                fecha_fin = rango[1] if len(rango) > 1 else rango[0]
            else:
                fecha_ini = fecha_fin = rango

            if fecha_ini > fecha_fin:
                fecha_ini, fecha_fin = fecha_fin, fecha_ini

    # --- Suma exacta día a día del consumo dentro del rango elegido (cacheado) ---
    consumo_total_cliente = _consumo_total_cached(fecha_ini, fecha_fin)
    df_mostrar = df_mostrar.merge(consumo_total_cliente, on='id_instalacion', how='left')

    # --- Desglose mensual (cacheado) — solo se recalcula cuando cambia el rango de fechas ---
    consumo_mensual = _consumo_mensual_cached(fecha_ini, fecha_fin)
    cols_periodo_sel = sorted(
        [c for c in consumo_mensual.columns if c != 'id_instalacion'],
        key=periodo_de_columna,
    )
    if cols_periodo_sel:
        df_mostrar = df_mostrar.merge(consumo_mensual, on='id_instalacion', how='left')

    if len(cols_periodo_sel) > 1:
        cols_consumo = ['Consumo_Total_Periodo_GJ'] + cols_periodo_sel
    else:
        cols_consumo = ['Consumo_Total_Periodo_GJ']

mes_ref_cartera = None
periodos_referencia = [periodo_de_columna(c) for c in cols_periodo_sel]
periodos_referencia = [p for p in periodos_referencia if p]
if periodos_referencia:
    anio_ref, mes_ref = sorted(periodos_referencia)[-1]
    mes_ref_cartera = f"{anio_ref:04d}-{mes_ref:02d}"

# Opciones del filtro de zona: zonas con poligono + zonas nominales presentes
# en datos (ej. "Mayakan"), para que Reportes/Dashboard puedan filtrarlas.
zonas_datos = []
if 'zona_vpm' in df_mostrar.columns:
    zonas_datos = (
        normalizar_zona_serie(df_mostrar['zona_vpm'])
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )
    zonas_datos = [
        z for z in zonas_datos
        if z and _normalizar_texto(z) not in {"", "nan", "none", "sin zona"}
    ]

zonas_extra = sorted(
    {z for z in zonas_datos if z not in ZONAS},
    key=lambda x: x.casefold(),
)
opciones_zona = ["Vista general"] + list(ZONAS.keys()) + zonas_extra
if "zona_widget" not in st.session_state:
    st.session_state.zona_widget = "Vista general"
if "zona_widget_multi" not in st.session_state:
    st.session_state.zona_widget_multi = [] if st.session_state.zona_widget == "Vista general" else [st.session_state.zona_widget]
if st.session_state.zona_widget not in opciones_zona:
    st.session_state.zona_widget = "Vista general"
if st.session_state.zona_widget_multi:
    zona_multi_actual = st.session_state.zona_widget_multi[0]
    if zona_multi_actual not in opciones_zona:
        st.session_state.zona_widget_multi = []

if "pending_zona" in st.session_state:
    zona_pendiente = st.session_state.pop("pending_zona")
    if zona_pendiente in ZONAS:
        st.session_state.zona_widget_multi = [zona_pendiente]
        st.session_state.zona_widget = zona_pendiente
    else:
        st.session_state.zona_widget_multi = []
        st.session_state.zona_widget = "Vista general"
elif st.session_state.zona_widget_multi:
    st.session_state.zona_widget = st.session_state.zona_widget_multi[0]
else:
    st.session_state.zona_widget = "Vista general"

# df_geo cacheado: solo se recalcula cuando cambian el status o el rango de fechas,
# y se construye solo en secciones que realmente lo usan.
df_geo = pd.DataFrame()
secciones_con_geo = {"Mapa", "Reportes", "Dashboard"}
if seccion in secciones_con_geo and cols_consumo and selected_status_gas:
    with st.spinner("Geocodificando..."):
        df_geo = _df_geo_con_consumo(
            tuple(sorted(selected_status_gas)), fecha_ini, fecha_fin
        )

# ===== FILTRO GLOBAL DE VOLUMEN (alcance GLOBAL, igual que Periodo de consumo) =====
# Afecta Mapa, Reportes y Top 10 por igual, usando el consumo total del periodo.
# El tope adaptativo se calcula sobre la zona activa para que Z3 y Z5 no compartan
# el mismo rango si su curva de consumo es distinta.
max_gj_global = 0
max_gj_global_ui = 0
slider_step_gj = 1
zona_sel_global = st.session_state.get("zona_widget", "Vista general")
if not df_geo.empty and 'Consumo_Total_Periodo_GJ' in df_geo.columns:
    serie_gj = pd.to_numeric(df_geo['Consumo_Total_Periodo_GJ'], errors='coerce').fillna(0)
    if zona_sel_global != "Vista general" and 'zona' in df_geo.columns:
        zona_norm = normalizar_zona_clave(zona_sel_global)
        zona_mask = normalizar_zona_clave_serie(df_geo['zona']) == zona_norm
        serie_gj = pd.to_numeric(df_geo.loc[zona_mask, 'Consumo_Total_Periodo_GJ'], errors='coerce').fillna(0)
    if len(serie_gj) > 0:
        max_gj_global = int(serie_gj.max())
        max_gj_global_ui, slider_step_gj = _calcular_limite_slider_gj(serie_gj)
st.session_state["max_gj_global"] = max_gj_global_ui if max_gj_global_ui > 0 else max_gj_global
reconciliar_gj_global()

with st.sidebar:
    st.markdown('<div class="engie-section">Filtrar por zona</div>', unsafe_allow_html=True)
    opciones_zona_filtrables = [z for z in opciones_zona if z != "Vista general"]
    st.session_state["zona_widget_options"] = opciones_zona_filtrables
    zonas_seleccionadas = st.multiselect(
        "Filtrar por zona",
        options=opciones_zona_filtrables,
        key="zona_widget_multi",
        placeholder="Vista general",
        label_visibility="collapsed",
        on_change=sync_zona_widget_unica,
        help="Solo permite 1 zona activa; al elegir otra, reemplaza automaticamente la anterior. Si usas Select all, se aplica Vista general.",
    )
    if opciones_zona_filtrables and len(zonas_seleccionadas) >= len(opciones_zona_filtrables):
        st.session_state.zona_widget_multi = []
        st.session_state.zona_widget = "Vista general"
        zonas_seleccionadas = []
    if len(zonas_seleccionadas) > 1:
        zona_activa = zonas_seleccionadas[-1]
        st.session_state.zona_widget_multi = [zona_activa]
        st.session_state.zona_widget = zona_activa
    else:
        st.session_state.zona_widget = zonas_seleccionadas[0] if zonas_seleccionadas else "Vista general"

    st.markdown('<div class="engie-section">Filtro de volumen</div>', unsafe_allow_html=True)
    #st.caption("Aplica a Mapa, Reportes y Top 10 según el consumo total del periodo.")
    # max_gj_global / max_gj_global_ui / slider_step_gj ya se calcularon arriba
    # (antes de abrir el sidebar) con la misma zona activa; evitamos repetir
    # el filtrado + cálculo de cuantiles sobre df_geo.
    if max_gj_global > 0:
        slider_max = max_gj_global_ui if max_gj_global_ui > 0 else max_gj_global
        valor_actual = int(st.session_state.get("min_gj_global_slider", 0))
        valor_actual = max(0, min(valor_actual, slider_max))
        st.slider(
            "Mostrar clientes con al menos (GJ)",
            min_value=0,
            max_value=slider_max,
            step=slider_step_gj,
            key="min_gj_global_slider",
            value=valor_actual,
            on_change=sync_gj_global_from_slider,
        )
        st.number_input(
            "GJ mínimo (exacto)",
            min_value=0,
            max_value=slider_max,
            step=slider_step_gj,
            value=valor_actual,
            key="min_gj_global_exact",
            on_change=sync_gj_global_from_exact,
        )
    else:
        st.caption("Sin consumo para aplicar filtro de GJ en el contexto actual.")

    st.markdown('<div class="engie-section">Status de clientes</div>', unsafe_allow_html=True)
    selected_status_gas = st.multiselect(
        "Status de clientes a mostrar",
        _status_options,
        key="status_filter_gas",
        label_visibility="collapsed",
        placeholder="Selecciona status",
        help="Filtra el mapa, tabla de clientes y Top 10 por status.",
    )
    if not selected_status_gas:
        st.warning("Selecciona al menos un status para ver clientes.")

    st.divider()
    st.markdown('<div class="engie-section">Datos</div>', unsafe_allow_html=True)
    if st.button("🔄  Cargar / Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        cargar_datos.clear()

min_gj_global = int(st.session_state.get("min_gj_global", 0)) if max_gj_global > 0 else 0
ui_max_gj = max_gj_global_ui if max_gj_global_ui > 0 else max_gj_global
if max_gj_global > 0:
    min_gj_global = max(0, min(min_gj_global, ui_max_gj))

# Guardar df_geo sin el filtro de GJ para los graficos de distribucion por zona.
# Solo se necesitan 'zona' + las columnas de consumo (no todo el dataframe),
# lo que evita copiar decenas de columnas irrelevantes para estos gráficos.
_cols_todas_zonas = list(dict.fromkeys(['zona', 'Consumo_Total_Periodo_GJ'] + list(cols_consumo)))
df_geo_todas_zonas = df_geo[[c for c in _cols_todas_zonas if c in df_geo.columns]].copy()

if min_gj_global > 0 and not df_geo.empty:
    df_geo = df_geo[
        pd.to_numeric(df_geo['Consumo_Total_Periodo_GJ'], errors='coerce').fillna(0) >= min_gj_global
    ].copy()

# ===== FILTRO GLOBAL DE ZONA (alcance GLOBAL, igual que el filtro de volumen) =====
# Afecta Reportes y Dashboard directamente sobre df_geo. El Mapa usa aparte
# `df_geo_pre_zona` (sin este filtro) para seguir mostrando los totales reales
# de todas las zonas en los polígonos; sus marcadores ya se limitan a la zona
# elegida mediante el parámetro `zona_sel` de `crear_mapa`.
df_geo_pre_zona = df_geo.copy()
zona_sel_global = st.session_state.get("zona_widget", "Vista general")
zona_sel_global_norm = normalizar_zona_clave(zona_sel_global)
if zona_sel_global != "Vista general" and not df_geo.empty and 'zona' in df_geo.columns:
    zonas_norm = normalizar_zona_clave_serie(df_geo['zona'])
    df_geo = df_geo[zonas_norm == zona_sel_global_norm].copy()


DASHBOARD_ECHARTS_FONT = '"Open Sans", verdana, arial, sans-serif'
DASHBOARD_TOOLBOX = {
    "right": 8,
    "top": 4,
    "itemSize": 16,
    "iconStyle": {"borderColor": "#587084"},
    "emphasis": {"iconStyle": {"borderColor": "#0077CC"}},
    "feature": {
        "saveAsImage": {
            "title": "Descargar gráfico",
            "type": "png",
            "pixelRatio": 2,
            "backgroundColor": "#FFFFFF",
        },
    },
}
DASHBOARD_TOOLTIP = {
    "backgroundColor": "#FFFFFF",
    "borderColor": "#D9E0E8",
    "textStyle": {"color": "#334155", "fontSize": 12},
}
DASHBOARD_LINE_COLORS = ["#0068c9", "#83c9ff", "#ffabab", "#29b09d", "#7defa1", "#ff2b2b", "#ffd16a", "#6d3fc0"]


def _mezclar(hex_color, factor):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    destino = 255 if factor > 0 else 0
    f = abs(factor)
    r, g, b = (round(c + (destino - c) * f) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def _degradado_radial(hex_color, oscuro=-0.08, claro=0.12):
    return {
        "type": "radial",
        "x": 0.5, "y": 0.5, "r": 0.5,
        "colorStops": [
            {"offset": 0.0, "color": _mezclar(hex_color, oscuro)},
            {"offset": 0.55, "color": hex_color},
            {"offset": 1.0, "color": _mezclar(hex_color, claro)},
        ],
    }


def _degradado_radial_donut(hex_color, cx, cy, r_out, r_in, oscuro=-0.15, claro=0.22):
    """Degradado radial global: más oscuro junto al hueco y más claro al exterior."""
    frac_in = r_in / r_out
    frac_mid = frac_in + (1 - frac_in) * 0.5
    return {
        "type": "radial",
        "x": cx, "y": cy, "r": r_out,
        "global": True,
        "colorStops": [
            {"offset": 0.0, "color": _mezclar(hex_color, oscuro)},
            {"offset": frac_in, "color": _mezclar(hex_color, oscuro)},
            {"offset": frac_mid, "color": hex_color},
            {"offset": 1.0, "color": _mezclar(hex_color, claro)},
        ],
    }


def _degradado_lineal(hex_color, oscuro=-0.08, claro=0.12, vertical=False):
    return {
        "type": "linear",
        "x": 0, "y": 0, "x2": 0 if vertical else 1, "y2": 1 if vertical else 0,
        "colorStops": [
            {"offset": 0.0, "color": _mezclar(hex_color, oscuro)},
            {"offset": 0.55, "color": hex_color},
            {"offset": 1.0, "color": _mezclar(hex_color, claro)},
        ],
    }


def _dashboard_echarts(option, height, key):
    opcion = {
        "animation": False,
        "textStyle": {"fontFamily": DASHBOARD_ECHARTS_FONT},
        "toolbox": DASHBOARD_TOOLBOX,
        **option,
    }
    st_echarts(options=opcion, height=f"{height}px", key=key)


# ============================================================
# VISTA REUTILIZABLE: SALUD Y CICLO DE VIDA (Cartera / Garantías)
# ============================================================
# Refactor (2026-08-28): Cartera y Garantías compartían exactamente el mismo
# layout/lógica y solo diferían en el origen de datos y algunas etiquetas.
# Se fusionaron en una única vista reutilizable (`render_salud_ciclo_vida`)
# parametrizada por un diccionario de configuración (CARTERA_CONFIG /
# GARANTIAS_CONFIG, definidos más abajo). Un selector arriba a la derecha de
# la sección decide qué configuración/dataset se renderiza en cada rerun.

def _pct_generico(n, total, sufijo):
    """Formatea 'n' como % de 'total' + sufijo (p.ej. 'de la cartera')."""
    return f"{n / total:.1%} {sufijo}" if total else None


def _nivel_riesgo_vencimiento(dias):
    """Etiqueta de riesgo según días restantes a la vigencia (usada por
    Cartera y Garantías por igual)."""
    if pd.isna(dias):
        return "N/D"
    dias = int(dias)
    if dias <= 7:
        return "🔴 Riesgo crítico"
    if dias <= 30:
        return "🟠 Riesgo alto"
    if dias <= 60:
        return "🟡 Riesgo medio"
    return "🟢 Riesgo bajo"


def render_salud_ciclo_vida(cfg):
    """Renderiza la vista de 'Salud y ciclo de vida' (filtro, tarjetas KPI,
    gráfico de altas/bajas, detalle histórico y alertas de vigencia),
    reutilizable tanto para Cartera como para Garantías. `cfg` concentra
    todas las diferencias entre ambas fuentes de datos (columnas, etiquetas,
    status disponibles, colores, etc.), manteniendo idéntico el layout."""
    st.subheader(cfg["subheader"])
    st.caption(cfg["caption"])

    # --- Carga de datos (con o sin spinner, según la fuente) ---
    if cfg["spinner_msg"]:
        with st.spinner(cfg["spinner_msg"]):
            base_df = cfg["data_loader"]()
    else:
        base_df = cfg["data_loader"]()

    # --- Filtro por zona/LDC ---
    # Cartera reutiliza el filtro de Zona del sidebar (zona_widget) en lugar de
    # duplicar un selector local, para evitar filtros redundantes y mantener
    # consistencia de navegación entre todos los componentes de la pestaña.
    # Garantías conserva su propio selectbox (LDC), que no tiene equivalente
    # en la barra lateral.
    if cfg.get("usa_filtro_zona_sidebar"):
        zona_sidebar = st.session_state.get("zona_widget", "Vista general")
        if zona_sidebar != "Vista general" and cfg["filter_column"] in base_df.columns:
            zona_norm = normalizar_zona_clave(zona_sidebar)
            ciclo_base = base_df[
                normalizar_zona_clave_serie(base_df[cfg["filter_column"]]) == zona_norm
            ].copy()
        else:
            ciclo_base = base_df.copy()
    else:
        opciones_filtro = [cfg["selector_placeholder"]] + cfg["selector_options_fn"](base_df)
        valor_filtro = st.selectbox(
            cfg["selector_label"],
            opciones_filtro,
            key=cfg["selector_key"],
        )

        if valor_filtro != cfg["selector_placeholder"]:
            ciclo_base = base_df[base_df[cfg["filter_column"]] == valor_filtro].copy()
        else:
            ciclo_base = base_df.copy()

    if ciclo_base.empty:
        st.info(cfg["empty_base_msg"])
        return

    ciclo_df = ciclo_base.copy()
    ciclo_df["status_norm"] = cfg["status_normalizer"](ciclo_df[cfg["status_column"]])
    ciclo_df["fecha_pes_efectiva"] = pd.to_datetime(ciclo_df[cfg["fecha_pes_col"]], errors="coerce")
    ciclo_df["fecha_baja_efectiva"] = pd.to_datetime(ciclo_df[cfg["fecha_baja_col"]], errors="coerce")
    ciclo_df["vigencia"] = pd.to_datetime(ciclo_df[cfg["vigencia_col"]], errors="coerce")
    ciclo_df["baja_valida"] = fecha_baja_es_valida_serie(ciclo_df["fecha_baja_efectiva"])

    total_ciclo = len(ciclo_df)
    conteo_status = ciclo_df["status_norm"].value_counts()

    conteos = {card["status"]: int(conteo_status.get(card["status"], 0)) for card in cfg["status_cards"]}
    sin_status_n = int(conteo_status.get("Sin status", 0))
    base_para_churn = sum(conteos.values())

    # --- Tarjetas KPI de status (cantidad dinámica según cfg["status_cards"]) ---
    kpi_cols = st.columns(len(cfg["status_cards"]) + 1)
    for col, card in zip(kpi_cols, cfg["status_cards"]):
        with col:
            render_kpi_card(
                title=card["title"],
                value=f"{conteos[card['status']]:,}",
                subtitle=_pct_generico(conteos[card["status"]], total_ciclo, cfg["pct_suffix"]) or "Sin datos",
                icon=card["icon"],
                accent_color=card["color"],
            )
    with kpi_cols[-1]:
        subtitle_sin_status = _pct_generico(sin_status_n, total_ciclo, cfg["pct_suffix"]) if total_ciclo else "Sin datos"
        if sin_status_n:
            subtitle_sin_status = f"{subtitle_sin_status} · Revisar origen"
        render_kpi_card(
            title="SIN STATUS",
            value=f"{sin_status_n:,}",
            subtitle=subtitle_sin_status,
            icon="🔹",
            accent_color="#66C2FF",
        )

    st.write("")

    if mes_ref_cartera:
        bajas_mes = ciclo_df[
            ciclo_df["baja_valida"] & (ciclo_df["fecha_baja_efectiva"].dt.strftime("%Y-%m") == mes_ref_cartera)
        ]
        altas_mes = ciclo_df[
            ciclo_df["fecha_pes_efectiva"].notna() & (ciclo_df["fecha_pes_efectiva"].dt.strftime("%Y-%m") == mes_ref_cartera)
        ]
        tasa_churn = (len(bajas_mes) / base_para_churn) if base_para_churn else 0
        tasa_activacion = (len(altas_mes) / total_ciclo) if total_ciclo else 0

        kc_a, kc_b = st.columns(2)
        with kc_a:
            render_kpi_card(
                title=f"BAJAS · {month_to_spanish_label(mes_ref_cartera).upper()}",
                value=f"{len(bajas_mes):,}",
                subtitle=f"{cfg['churn_label']}: {tasa_churn:.2%}",
                icon="📉",
                accent_color="#E03131",
            )
        with kc_b:
            render_kpi_card(
                title=f"ALTAS · {month_to_spanish_label(mes_ref_cartera).upper()}",
                value=f"{len(altas_mes):,}",
                subtitle=f"{cfg['activation_label']}: {tasa_activacion:.2%}",
                icon="📈",
                accent_color="#0077CC",
            )
    else:
        st.info("No hay referencia de mes para calcular altas y bajas del periodo filtrado.")

    st.write("")
    st.markdown("**Altas y bajas por mes (histórico)**")

    altas_serie = (
        ciclo_df[ciclo_df["fecha_pes_efectiva"].notna()]
        .assign(AñoMes=lambda d: d["fecha_pes_efectiva"].dt.to_period("M").astype(str))
        .groupby("AñoMes").size().rename("Altas")
    )
    bajas_serie = (
        ciclo_df[ciclo_df["baja_valida"]]
        .assign(AñoMes=lambda d: d["fecha_baja_efectiva"].dt.to_period("M").astype(str))
        .groupby("AñoMes").size().rename("Bajas")
    )

    timeline = pd.concat([altas_serie, bajas_serie], axis=1).fillna(0).sort_index().reset_index()
    timeline = timeline.rename(columns={"index": "AñoMes"})
    timeline["Altas"] = timeline["Altas"].astype(int)
    timeline["Bajas"] = timeline["Bajas"].astype(int)
    timeline["Neto"] = timeline["Altas"] - timeline["Bajas"]
    timeline_plot = timeline[timeline["AñoMes"] >= "2019-01"].copy()

    if timeline.empty:
        st.info(cfg["timeline_empty_msg"])
    elif timeline_plot.empty:
        st.info("No hay datos históricos desde 2019 para mostrar en este gráfico.")
    else:
        color_altas = [
            BRAND_COLORS["accent"] if mes == mes_ref_cartera else BRAND_COLORS["primary"]
            for mes in timeline_plot["AñoMes"]
        ]
        color_bajas = [
            "#F76707" if mes == mes_ref_cartera else "#E03131"
            for mes in timeline_plot["AñoMes"]
        ]
        option_timeline = {
            "tooltip": {
                **DASHBOARD_TOOLTIP,
                "trigger": "axis",
                "axisPointer": {"type": "shadow"},
                "formatter": JsCode(
                    "function (params) {"
                    " var lineas = ['<b>' + params[0].axisValue + '</b>'];"
                    " params.forEach(function (p) {"
                    " var v = p.seriesName === 'Bajas' ? Math.abs(p.value) : p.value;"
                    " lineas.push(p.marker + p.seriesName + ': ' + v.toLocaleString('es-MX'));"
                    " });"
                    " return lineas.join('<br/>');"
                    " }"
                ),
            },
            "legend": {
                "top": 4,
                "right": 60,
                "icon": "roundRect",
                "itemWidth": 12,
                "itemHeight": 12,
                "textStyle": {"color": "#1F2937"},
            },
            "grid": {"left": 70, "right": 20, "top": 56, "bottom": 80},
            "xAxis": {
                "type": "category",
                "name": "Mes",
                "nameLocation": "middle",
                "nameGap": 34,
                "nameTextStyle": {"fontSize": 14, "color": "#1F2937"},
                "data": [month_to_spanish_label(mes) for mes in timeline_plot["AñoMes"]],
                "axisLine": {"show": False},
                "axisTick": {"show": False},
                "axisLabel": {"color": "#1F2937", "fontSize": 11, "hideOverlap": True, "rotate": 0},
            },
            "yAxis": {
                "type": "value",
                "name": cfg["timeline_yaxis"],
                "nameLocation": "middle",
                "nameGap": 50,
                "nameTextStyle": {"fontSize": 14, "color": "#1F2937"},
                "axisLine": {"show": False},
                "axisTick": {"show": False},
                "splitLine": {"show": True, "lineStyle": {"color": "#EEF2F7"}},
                "axisLabel": {"color": "#1F2937"},
            },
            "series": [
                {
                    "name": "Altas",
                    "type": "bar",
                    "stack": "cambios",
                    "barCategoryGap": "20%",
                    "itemStyle": {"color": BRAND_COLORS["primary"], "shadowBlur": 20, "shadowColor": "rgba(0,0,0,0.15)", "shadowOffsetX": 6},
                    "emphasis": {"itemStyle": {"shadowBlur": 28, "shadowColor": "rgba(0,0,0,0.25)"}},
                    "data": [
                        {
                            "value": int(valor),
                            "itemStyle": {"color": _degradado_lineal(color, vertical=True), "borderRadius": [10, 10, 0, 0]},
                        }
                        for valor, color in zip(timeline_plot["Altas"], color_altas)
                    ],
                },
                {
                    "name": "Bajas",
                    "type": "bar",
                    "stack": "cambios",
                    "barCategoryGap": "20%",
                    "itemStyle": {"color": "#E03131", "shadowBlur": 20, "shadowColor": "rgba(0,0,0,0.15)", "shadowOffsetX": 6},
                    "emphasis": {"itemStyle": {"shadowBlur": 28, "shadowColor": "rgba(0,0,0,0.25)"}},
                    "data": [
                        {
                            "value": -int(valor),
                            "itemStyle": {"color": _degradado_lineal(color, vertical=True), "borderRadius": [0, 0, 10, 10]},
                        }
                        for valor, color in zip(timeline_plot["Bajas"], color_bajas)
                    ],
                },
                {
                    "name": "Neto",
                    "type": "line",
                    "symbol": "circle",
                    "symbolSize": 6,
                    "lineStyle": {"color": BRAND_COLORS["primary_dark"], "width": 2},
                    "itemStyle": {"color": BRAND_COLORS["primary_dark"]},
                    "data": [int(valor) for valor in timeline_plot["Neto"]],
                },
            ],
        }
        _dashboard_echarts(option_timeline, 380, key=f"timeline_altas_bajas_{cfg['mes_historico_key']}")
        if mes_ref_cartera:
            st.caption(
                f"El mes resaltado ({month_to_spanish_label(mes_ref_cartera)}) corresponde al periodo de consumo seleccionado arriba."
            )

    if not timeline.empty:
        meses_hist = timeline["AñoMes"].dropna().astype(str).tolist()
        meses_hist = sorted(set(meses_hist))

        idx_mes_hist = len(meses_hist) - 1
        if mes_ref_cartera and mes_ref_cartera in meses_hist:
            idx_mes_hist = meses_hist.index(mes_ref_cartera)

        mes_historico = st.selectbox(
            "Mes histórico",
            options=meses_hist,
            index=idx_mes_hist,
            format_func=month_to_spanish_label,
            key=cfg["mes_historico_key"],
        )

        bajas_mes_historico = ciclo_df[
            ciclo_df["baja_valida"]
            & (ciclo_df["fecha_baja_efectiva"].dt.strftime("%Y-%m") == mes_historico)
        ]
        altas_mes_historico = ciclo_df[
            ciclo_df["fecha_pes_efectiva"].notna()
            & (ciclo_df["fecha_pes_efectiva"].dt.strftime("%Y-%m") == mes_historico)
        ]

        col_bajas_det, col_altas_det = st.columns(2)
        with col_bajas_det:
            with st.expander(
                f"{cfg['expander_baja_title']} · {month_to_spanish_label(mes_historico)} ({len(bajas_mes_historico)})",
                expanded=True,
            ):
                if bajas_mes_historico.empty:
                    st.caption(cfg["expander_baja_empty"])
                else:
                    st.dataframe(
                        bajas_mes_historico[["razon_social", "zona", "fecha_baja_efectiva"]]
                        .rename(columns={
                            "razon_social": "Cliente",
                            "zona": cfg["col_rename_label"],
                            "fecha_baja_efectiva": "Fecha",
                        })
                        .sort_values("Fecha"),
                        use_container_width=True,
                        hide_index=True,
                        height="content",
                        column_config={
                            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                        },
                    )
        with col_altas_det:
            with st.expander(
                f"{cfg['expander_alta_title']} · {month_to_spanish_label(mes_historico)} ({len(altas_mes_historico)})",
                expanded=True,
            ):
                if altas_mes_historico.empty:
                    st.caption(cfg["expander_alta_empty"])
                else:
                    st.dataframe(
                        altas_mes_historico[["razon_social", "zona", "fecha_pes_efectiva"]]
                        .rename(columns={
                            "razon_social": "Cliente",
                            "zona": cfg["col_rename_label"],
                            "fecha_pes_efectiva": "Fecha",
                        })
                        .sort_values("Fecha"),
                        use_container_width=True,
                        hide_index=True,
                        height="content",
                        column_config={
                            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                        },
                    )

    bajas_pendientes = int((~ciclo_df["baja_valida"] & ciclo_df["status_norm"].isin(cfg["pendientes_statuses"])).sum())
    if bajas_pendientes:
        st.caption(
            f"⚠️ {bajas_pendientes} {cfg['pendientes_entity']} {cfg['pendientes_participio']} como "
            f"{'/'.join(cfg['pendientes_statuses'])} no tienen fecha de {cfg['pendientes_fecha_label']} registrada "
            "y no aparecen en la gráfica anterior. Conviene corregirlo en el sistema origen."
        )

    st.write("")
    st.markdown(cfg["alert_heading"])
    dias_alerta = 90

    activos_df = ciclo_df[ciclo_df["status_norm"] == cfg["alert_status_value"]].copy()
    hoy = pd.Timestamp(datetime.now().date())
    activos_df["dias_restantes"] = (activos_df["vigencia"] - hoy).dt.days

    # Normalizar texto de renovación para cubrir "Automática/No Automática" con y sin tildes.
    renovacion_norm = activos_df["renovacion"].fillna("").astype(str).str.strip().str.lower()
    renovacion_norm = (
        renovacion_norm.str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("ascii")
    )

    es_no_automatica = renovacion_norm.str.contains("no automatica", na=False)
    es_automatica = renovacion_norm.str.contains("automatica", na=False) & ~es_no_automatica

    # Usar 'bp' si existe, si no usar 'razon_social'
    col_nombre = 'bp' if 'bp' in activos_df.columns else 'razon_social'
    cols_alertas = [col_nombre, "zona", "vigencia", "dias_restantes", "renovacion"]
    
    alertas = activos_df[
        activos_df["vigencia"].notna()
        & (activos_df["dias_restantes"] >= 0)
        & (activos_df["dias_restantes"] <= dias_alerta)
        & es_no_automatica
    ][cols_alertas].sort_values("dias_restantes")

    alertas_automatica = activos_df[
        activos_df["vigencia"].notna()
        & (activos_df["dias_restantes"] >= 0)
        & (activos_df["dias_restantes"] <= dias_alerta)
        & es_automatica
    ][cols_alertas].sort_values("dias_restantes")

    if alertas.empty:
        st.success(cfg["alert_empty_msg"].format(dias=dias_alerta))
    else:
        st.warning(cfg["alert_found_msg"].format(n=len(alertas), dias=dias_alerta))

        dias_minimos = int(alertas["dias_restantes"].min())
        color_proximo = "#12B886"
        if dias_minimos <= 7:
            color_proximo = "#EF4444"
        elif dias_minimos <= 30:
            color_proximo = "#F59F00"

        zona_top = "N/D"
        zona_top_n = 0
        if alertas["zona"].notna().any():
            zona_counts = alertas["zona"].value_counts()
            if not zona_counts.empty:
                zona_top = str(zona_counts.index[0])
                zona_top_n = int(zona_counts.iloc[0])

        a1, a2, a3 = st.columns(3)
        with a1:
            render_mini_alert_card(
                title=cfg["alert_kpi1_title"],
                value=f"{len(alertas):,}",
                subtitle=f"En los próximos {dias_alerta} días",
                icon="⚠️",
                color="#F59F00",
            )
        with a2:
            render_mini_alert_card(
                title="MÁS PRÓXIMO A VENCER",
                value=f"{dias_minimos:,}",
                subtitle="Días restantes",
                icon="⏳",
                color=color_proximo,
            )
        with a3:
            render_mini_alert_card(
                title=cfg["alert_kpi3_title"],
                value=zona_top,
                subtitle=f"{zona_top_n:,} {cfg['alert_kpi3_entity']} en riesgo",
                icon="📍",
                color="#0077CC",
            )

        st.write("")

        alertas_det = alertas.copy()
        alertas_det["riesgo_vencimiento"] = alertas_det["dias_restantes"].apply(_nivel_riesgo_vencimiento)
        alertas_det = alertas_det.sort_values("dias_restantes", ascending=True)

        # Crear mapping de renombre dinámico
        col_nombre_actual = 'bp' if 'bp' in alertas_det.columns else 'razon_social'
        rename_mapping = {
            col_nombre_actual: "Cliente",
            "zona": cfg["col_rename_label"],
            "vigencia": "Fecha Vigencia",
            "dias_restantes": "Días restantes",
            "renovacion": "Renovación",
            "riesgo_vencimiento": "Riesgo de vencimiento",
        }

        alertas_det_export = alertas_det.rename(columns=rename_mapping)
        no_auto_excel = _excel_bytes_desde_hojas(
            {"Renovacion No Automatica": alertas_det_export}
        )

        with st.container(key="renov_no_auto_header"):
            col_titulo_no_auto, col_btn_no_auto = st.columns([0.82, 0.18])
            with col_titulo_no_auto:
                st.markdown("**Renovación No Automática**")
            with col_btn_no_auto:
                st.download_button(
                    label="Export",
                    data=no_auto_excel,
                    file_name=f"renovacion_no_automatica_{date.today():%Y%m%d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_renovacion_no_automatica",
                )

        st.dataframe(
            alertas_det_export,
            use_container_width=True,
            hide_index=True,
            height=min(400, 44 + 35 * len(alertas)),
            column_config={
                "Fecha Vigencia": st.column_config.DateColumn("Fecha Vigencia", format="DD/MM/YYYY"),
                "Días restantes": st.column_config.NumberColumn("Días restantes", format="%d días"),
                "Renovación": st.column_config.TextColumn("Renovación"),
                "Riesgo de vencimiento": st.column_config.TextColumn("Riesgo de vencimiento"),
            },
        )

    st.write("")

    if alertas_automatica.empty:
        alertas_automatica_export = pd.DataFrame()
        automatica_excel = b""
    else:
        alertas_automatica_det_preview = alertas_automatica.copy()
        alertas_automatica_det_preview["riesgo_vencimiento"] = alertas_automatica_det_preview["dias_restantes"].apply(
            _nivel_riesgo_vencimiento
        )
        alertas_automatica_det_preview = alertas_automatica_det_preview.sort_values("dias_restantes", ascending=True)
        col_nombre_actual_preview = 'bp' if 'bp' in alertas_automatica_det_preview.columns else 'razon_social'
        rename_mapping_preview = {
            col_nombre_actual_preview: "Cliente",
            "zona": cfg["col_rename_label"],
            "vigencia": "Fecha Vigencia",
            "dias_restantes": "Días restantes",
            "renovacion": "Renovación",
            "riesgo_vencimiento": "Riesgo de vencimiento",
        }
        alertas_automatica_export = alertas_automatica_det_preview.rename(columns=rename_mapping_preview)
        automatica_excel = _excel_bytes_desde_hojas(
            {"Renovacion Automatica": alertas_automatica_export}
        )

    with st.container(key="renov_auto_header"):
        col_titulo_auto, col_btn_auto = st.columns([0.82, 0.18])
        with col_titulo_auto:
            st.markdown("**Renovación automática**")
        with col_btn_auto:
            st.download_button(
                label="Export",
                data=automatica_excel,
                file_name=f"renovacion_automatica_{date.today():%Y%m%d}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_renovacion_automatica",
                disabled=alertas_automatica.empty,
            )

    if alertas_automatica.empty:
        st.info(
            f"No hay clientes activos con vigencia venciendo en los próximos {dias_alerta} días y renovación automática."
        )
    else:
        alertas_automatica_det = alertas_automatica.copy()
        alertas_automatica_det["riesgo_vencimiento"] = alertas_automatica_det["dias_restantes"].apply(
            _nivel_riesgo_vencimiento
        )
        alertas_automatica_det = alertas_automatica_det.sort_values("dias_restantes", ascending=True)
        
        # Crear mapping de renombre dinámico
        col_nombre_actual = 'bp' if 'bp' in alertas_automatica_det.columns else 'razon_social'
        rename_mapping = {
            col_nombre_actual: "Cliente",
            "zona": cfg["col_rename_label"],
            "vigencia": "Fecha Vigencia",
            "dias_restantes": "Días restantes",
            "renovacion": "Renovación",
            "riesgo_vencimiento": "Riesgo de vencimiento",
        }

        st.dataframe(
            alertas_automatica_det.rename(columns=rename_mapping),
            use_container_width=True,
            hide_index=True,
            height=min(400, 44 + 35 * len(alertas_automatica_det)),
            column_config={
                "Fecha Vigencia": st.column_config.DateColumn("Fecha Vigencia", format="DD/MM/YYYY"),
                "Días restantes": st.column_config.NumberColumn("Días restantes", format="%d días"),
                "Renovación": st.column_config.TextColumn("Renovación"),
                "Riesgo de vencimiento": st.column_config.TextColumn("Riesgo de vencimiento"),
            },
        )


# --- Configuración de la vista Cartera (fuente: resultado_todos_status) ---
CARTERA_CONFIG = {
    "subheader": "Salud de cartera y ciclo de vida de clientes",
    "caption": (
        "Esta sección siempre incluye todos los status (Activo, Inactivo, Cancelado, Pre Activo), "
        "sin importar el filtro de status de la barra lateral."
    ),
    "data_loader": lambda: resultado_todos_status,
    "spinner_msg": None,
    "usa_filtro_zona_sidebar": True,
    "filter_column": "zona",
    "empty_base_msg": "No hay datos base para el análisis de status de clientes.",
    "status_column": "status",
    "status_normalizer": normalizar_status_serie,
    "fecha_pes_col": "fecha_pes_efectiva",
    "fecha_baja_col": "fecha_baja_efectiva",
    "vigencia_col": "fecha_vigencia_actualizada",
    "pct_suffix": "de la cartera",
    "status_cards": [
        {"status": "Activo", "title": "ACTIVOS", "icon": "🟢", "color": "#12B886"},
        {"status": "Inactivo", "title": "INACTIVOS", "icon": "⚪", "color": "#6B7280"},
        {"status": "Cancelado", "title": "CANCELADOS", "icon": "🔴", "color": "#E03131"},
        {"status": "Pre Activo", "title": "PRE ACTIVO", "icon": "🟠", "color": "#F59F00"},
    ],
    "churn_label": "Tasa de churn del mes",
    "activation_label": "Tasa de activación del mes",
    "timeline_yaxis": "Número de Clientes",
    "timeline_empty_msg": "No hay fechas de alta/baja suficientes para construir la línea de tiempo.",
    "mes_historico_key": "mes_historico_altas_bajas_gas",
    "expander_baja_title": "Clientes dados de baja",
    "expander_baja_empty": "Sin bajas en el mes histórico seleccionado.",
    "expander_alta_title": "Clientes dados de alta",
    "expander_alta_empty": "Sin altas en el mes histórico seleccionado.",
    "col_rename_label": "Zona",
    "pendientes_entity": "cliente(s)",
    "pendientes_participio": "marcados",
    "pendientes_fecha_label": "baja",
    "pendientes_statuses": ["Inactivo", "Cancelado"],
    "alert_heading": "**Alertas: vigencia próxima a vencer (solo clientes Activos)**",
    "alert_status_value": "Activo",
    "alert_empty_msg": "No hay clientes activos con vigencia venciendo en los próximos {dias} días.",
    "alert_found_msg": "{n} cliente(s) activo(s) con vigencia venciendo en los próximos {dias} días.",
    "alert_kpi1_title": "CLIENTES POR VENCER",
    "alert_kpi3_title": "ZONA MÁS AFECTADA",
    "alert_kpi3_entity": "cliente(s)",
}

# --- Configuración de la vista Garantías (fuente: cargar_datos_garantias) ---
# Adaptaciones respecto a Cartera (mismo criterio de la versión previa):
#   - "Zona" -> `ldc` (bv_hop_garantia no tiene zona geográfica ZONAS).
#   - Alta/Baja -> `fecha_emision`/`fecha_devolucion`.
#   - Vigencia contractual -> `fecha_vigencia`.
#   - Solo 3 status reales (Vigente/Liberado/Vencido), sin equivalente de "Pre Activo".
GARANTIAS_CONFIG = {
    "subheader": "Salud de garantías y ciclo de vida de solicitudes",
    "caption": (
        "Esta sección utiliza la tabla de garantías (bv_hop_garantia) de forma "
        "independiente y siempre incluye todos los status (Vigente, Liberado, Vencido), "
        "sin importar el filtro de status de clientes de la barra lateral."
    ),
    "data_loader": cargar_datos_garantias,
    "spinner_msg": "Consultando la base de datos...",
    "selector_label": "LDC para análisis de garantías",
    "selector_placeholder": "Todas las LDC",
    "selector_options_fn": lambda df: sorted(
        df["ldc"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().unique().tolist()
    ),
    "selector_key": "ldc_garantias",
    "filter_column": "zona",
    "empty_base_msg": "No hay datos base para el análisis de status de garantías.",
    "status_column": "status_garantia",
    "status_normalizer": normalizar_status_garantia_serie,
    "fecha_pes_col": "fecha_emision",
    "fecha_baja_col": "fecha_devolucion",
    "vigencia_col": "fecha_vigencia",
    "pct_suffix": "de las garantías",
    "status_cards": [
        {"status": "Vigente", "title": "VIGENTES", "icon": "🟢", "color": "#12B886"},
        {"status": "Liberado", "title": "LIBERADAS", "icon": "⚪", "color": "#6B7280"},
        {"status": "Vencido", "title": "VENCIDAS", "icon": "🔴", "color": "#E03131"},
    ],
    "churn_label": "Tasa de devolución del mes",
    "activation_label": "Tasa de emisión del mes",
    "timeline_yaxis": "Garantías",
    "timeline_empty_msg": "No hay fechas de emisión/devolución suficientes para construir la línea de tiempo.",
    "mes_historico_key": "mes_historico_altas_bajas_garantias",
    "expander_baja_title": "Garantías devueltas",
    "expander_baja_empty": "Sin devoluciones en el mes histórico seleccionado.",
    "expander_alta_title": "Garantías emitidas",
    "expander_alta_empty": "Sin emisiones en el mes histórico seleccionado.",
    "col_rename_label": "LDC",
    "pendientes_entity": "garantía(s)",
    "pendientes_participio": "marcadas",
    "pendientes_fecha_label": "devolución",
    "pendientes_statuses": ["Liberado", "Vencido"],
    "alert_heading": "**Alertas: vigencia próxima a vencer (solo garantías Vigentes)**",
    "alert_status_value": "Vigente",
    "alert_empty_msg": "No hay garantías vigentes con vencimiento en los próximos {dias} días.",
    "alert_found_msg": "{n} garantía(s) vigente(s) con vencimiento en los próximos {dias} días.",
    "alert_kpi1_title": "GARANTÍAS POR VENCER",
    "alert_kpi3_title": "LDC MÁS AFECTADA",
    "alert_kpi3_entity": "garantía(s)",
}


# ============================================================
# SECCIÓN: MAPA
# ============================================================
if seccion == "Mapa":
    mostrar_intro_globo(VISTA_CENTRO[0], VISTA_CENTRO[1], zoom_destino=6.0)

    col_head_title, col_head_actions = st.columns([0.78, 0.22])
    with col_head_title:
        st.subheader("Mapa de zonas de Gas Natural")

    df_geo_seccion = df_geo_pre_zona

    if not cols_consumo:
        st.info("No hay columnas de consumo para graficar.")
    else:
        # ===== Selector de capas con casillas (excluye "Regionalización") =====
        # Todas las capas excepto "Regionalización"
        try:
            datos_kml = cargar_kml(RUTA_KML)
        except Exception as e:
            datos_kml = {}
            st.warning(f"No se pudo cargar el KML: {e}")

        capas = [c for c in datos_kml.keys() if c.strip().lower() != "regionalización"]

        # Capas activas por defecto (solo la primera vez que aparecen en sesión).
        CAPAS_KML_DEFAULT = {"sistrangas", "sistemas de transporte"}
        for capa in capas:
            if f"kml_{capa}" not in st.session_state:
                st.session_state[f"kml_{capa}"] = _normalizar_texto(capa) in CAPAS_KML_DEFAULT

        capas_activas = sum(1 for c in capas if st.session_state.get(f"kml_{c}", False))

        with col_head_actions:
            with st.popover("⚙️ Filtro(s)", help="Abrir panel maestro de mapa", use_container_width=True):
                st.markdown("**Visualización**")
                col_sel = st.selectbox(
                    "Consumo a visualizar",
                    cols_consumo,
                    format_func=nombre_consumo,
                    key="col_sel_mapa",
                )

                st.markdown("**Capas de infraestructura**")
                st.caption(f"{capas_activas} de {len(capas)} activas")

                col_accion_1, col_accion_2 = st.columns(2)
                with col_accion_1:
                    if st.button("Seleccionar todo", key="kml_todo", use_container_width=True):
                        for capa in capas:
                            st.session_state[f"kml_{capa}"] = True
                        st.rerun()
                with col_accion_2:
                    if st.button("Deseleccionar todo", key="kml_nada", use_container_width=True):
                        for capa in capas:
                            st.session_state[f"kml_{capa}"] = False
                        st.rerun()

                if capas:
                    num_cols_capas = 4 if len(capas) >= 8 else (3 if len(capas) >= 5 else 2)
                    cols_capas = st.columns(num_cols_capas)
                    for i, capa in enumerate(capas):
                        with cols_capas[i % num_cols_capas]:
                            st.checkbox(_label_checkbox_capa(capa), key=f"kml_{capa}")
                else:
                    st.caption("No hay capas de infraestructura disponibles en el KML.")

        zona_sel = st.session_state.zona_widget

        st.caption(f"Consumo: {nombre_consumo(col_sel)}")

        # ===== Buscador de Código Postal =====
        # Bloque desactivado temporalmente: se comenta para ocultar el buscador
        # y evitar que aparezca el texto "Ej: 64000" en la interfaz del mapa.
        # with st.form(key="form_cp_busqueda", border=False):
        #     col_cp_input, col_cp_btn = st.columns([0.75, 0.25])
        #     with col_cp_input:
        #         cp_input_val = st.text_input(
        #             "🔍 Buscar código postal",
        #             key="cp_busqueda_mapa_input",
        #             placeholder="Ej: 64000",
        #             max_chars=5,
        #             help="Escribe un código postal (5 dígitos) y presiona Buscar o Enter.",
        #             label_visibility="collapsed",
        #         )
        #     with col_cp_btn:
        #         cp_submitted = st.form_submit_button("🔍 Buscar", use_container_width=True)
        #
        # if cp_submitted:
        #     raw = cp_input_val.strip()
        #     if raw.isdigit() and len(raw) <= 5:
        #         cp_norm = raw.zfill(5)
        #         geo_cp = _geocodificar_cps((cp_norm,))
        #         lat_r = geo_cp['lat'].iloc[0] if not geo_cp.empty else None
        #         lon_r = geo_cp['lon'].iloc[0] if not geo_cp.empty else None
        #         if lat_r is not None and lon_r is not None and pd.notna(lat_r) and pd.notna(lon_r):
        #             n_cp = int((df_geo_seccion['cp_localizacion'].astype(str).str.zfill(5) == cp_norm).sum())
        #             st.session_state["cp_marker_result"] = {
        #                 'lat': float(lat_r), 'lon': float(lon_r),
        #                 'cp': cp_norm, 'n_clientes': n_cp,
        #             }
        #         else:
        #             st.session_state["cp_marker_result"] = {'error': f"No se encontraron coordenadas para el CP **{raw}**."}
        #     elif raw == "":
        #         st.session_state.pop("cp_marker_result", None)
        #     else:
        #         st.session_state["cp_marker_result"] = {'error': "El código postal debe contener solo dígitos (máx. 5)."}
        #
        # cp_result = st.session_state.get("cp_marker_result")
        cp_marker_data = None
        #
        # with st.container():
        #     if cp_result:
        #         if 'error' in cp_result:
        #             st.warning(cp_result['error'])
        #         else:
        #             cp_marker_data = cp_result
        #             n_cp = cp_result['n_clientes']
        #             cp_norm_show = cp_result['cp']
        #             col_cp_info, col_cp_table = st.columns([0.30, 0.70])
        #             with col_cp_info:
        #                 st.success(f"CP **{cp_norm_show}** — {n_cp} cliente(s)")
        #             if n_cp > 0:
        #                 df_cp = df_geo_seccion[
        #                     df_geo_seccion['cp_localizacion'].astype(str).str.zfill(5) == cp_norm_show
        #                 ][['id_instalacion', 'bp', 'zona', col_sel]].copy()
        #                 df_cp[col_sel] = pd.to_numeric(df_cp[col_sel], errors='coerce').fillna(0)
        #                 df_cp = df_cp.rename(columns={
        #                     'id_instalacion': 'Instalación', 'bp': 'Cliente',
        #                     'zona': 'Zona', col_sel: f'Consumo GJ',
        #                 })
        #                 with col_cp_table:
        #                     st.dataframe(
        #                         df_cp.sort_values('Consumo GJ', ascending=False),
        #                         use_container_width=True,
        #                         hide_index=True,
        #                         height=min(180, 40 + 35 * len(df_cp)),
        #                     )

        # El filtro de volumen (GJ) ya se aplicó de forma global sobre df_geo
        # antes de llegar a esta sección, por lo que aquí solo se copia.
        df_geo_mapa = df_geo_seccion.copy()

        carpetas_sel = [c for c in capas if st.session_state.get(f"kml_{c}", False)]

        if df_geo_pre_zona.empty:
            st.warning("No se pudieron obtener coordenadas de los códigos postales.")
        elif df_geo_seccion.empty:
            st.info("Ningún cliente coincide con el filtro de Id de Instalación en esta sección.")
        else:
            if zona_sel == "Vista general":
                st.caption("Selecciona una zona en el menú o haz clic sobre una geometría del mapa.")
            else:
                n_z = int((df_geo_mapa['zona'] == zona_sel).sum())
                st.caption(f"Mostrando {n_z} clientes en {zona_sel}. Clic en otra zona para cambiar.")

            # Nota: no se cachea el objeto folium.Map en session_state.
            # Reutilizar la misma instancia entre reruns puede dejar el
            # componente en estado inconsistente al hacer clic y causar que
            # el mapa se renderice en blanco.
            m = crear_mapa(df_geo_mapa, col_sel, zona_sel,
                           datos_kml=datos_kml, carpetas_kml=carpetas_sel,
                           # cp_marker=cp_marker_data  # buscador por CP desactivado
                           )

            map_data = st_folium(
                m,
                use_container_width=True,
                height=600,
                key="mapa_zonas",
                returned_objects=["last_object_clicked", "last_clicked"],
            )

            # st_folium conserva el último clic entre reruns, por eso guardamos
            # una "firma" de lo ya procesado y solo actuamos ante un clic nuevo.
            click_obj = (map_data or {}).get("last_object_clicked") or {}
            click_map = (map_data or {}).get("last_clicked") or {}

            def _firma(p):
                if p.get("lat") is None or p.get("lng") is None:
                    return None
                return (round(p["lat"], 6), round(p["lng"], 6))

            def _es_centinela(sig):
                # El botón 🏠 emite un clic cerca de (0,0).
                return sig is not None and abs(sig[0]) < 0.001 and abs(sig[1]) < 0.01

            sig_obj = _firma(click_obj)
            sig_map = _firma(click_map)

            # 1) Botón "home" (🏠): clic centinela en last_clicked -> Vista general.
            if _es_centinela(sig_map) and sig_map != st.session_state.get("sig_home_proc"):
                st.session_state.sig_home_proc = sig_map
                if st.session_state.zona_widget != "Vista general":
                    st.session_state.pending_zona = "Vista general"
                    st.rerun()

            # 2) Selección de zona por clic sobre una geometría del mapa.
            sig_zona, click_zona = None, None
            if sig_obj is not None and not _es_centinela(sig_obj):
                sig_zona, click_zona = sig_obj, click_obj
            elif sig_map is not None and not _es_centinela(sig_map):
                sig_zona, click_zona = sig_map, click_map

            if sig_zona is not None and sig_zona != st.session_state.get("sig_zona_proc"):
                st.session_state.sig_zona_proc = sig_zona
                nueva_zona = zona_de_click(click_zona["lng"], click_zona["lat"])
                if nueva_zona and nueva_zona != st.session_state.zona_widget:
                    st.session_state.pending_zona = nueva_zona
                    st.rerun()

            leyenda = " &nbsp; ".join(
                f'<span style="color:{ZONA_COLORS[z]}">&#9679;</span> {z}'
                for z in ZONAS.keys()
            )
            st.markdown(f"**Zonas:** {leyenda}", unsafe_allow_html=True)

            st.markdown("**Consumo por zona**")
            resumen_zona = _resumen_zona_tabla(df_geo_mapa, col_sel)
            st.dataframe(
                resumen_zona.rename(columns={'zona': 'Zona', 'Consumo': 'Consumo (GJ)'})
                .style.format({'Consumo (GJ)': '{:,.0f}'}),
                use_container_width=True,
                hide_index=True,
                height="content",
            )


# ============================================================
# SECCIÓN: REPORTES
# ============================================================
elif seccion == "Reportes":
    if "reporte_periodicidad" not in st.session_state:
        st.session_state["reporte_periodicidad"] = "Mensual"
    periodicidad_reporte = st.session_state.get("reporte_periodicidad", "Mensual")

    filtro_clientes = st.text_input(
        "Filtrar por Cliente o Id de Instalación",
        key="filtro_instalacion_clientes",
        placeholder="Ej: Alpezzi Chocolate o 600601101",
    )
    df_mostrar_seccion = df_mostrar
    if filtro_clientes:
        df_mostrar_seccion = df_mostrar[mascara_filtro_cliente_instalacion(df_mostrar, filtro_clientes)]

    # Reportes usa el dataset de negocio (df_mostrar) para no depender de la
    # geocodificación (df_geo). Asi, el filtro de zona funciona incluso cuando
    # una zona tiene pocos/sin puntos geocodificados.
    base_reporte = df_mostrar_seccion.copy()

    # Mantener comportamiento del filtro global de volumen tambien en Reportes.
    if min_gj_global > 0 and 'Consumo_Total_Periodo_GJ' in base_reporte.columns:
        base_reporte = base_reporte[
            pd.to_numeric(base_reporte['Consumo_Total_Periodo_GJ'], errors='coerce').fillna(0) >= min_gj_global
        ].copy()

    # Aplicar filtro global de zona sobre zona_vpm (fuente canonica en reportes).
    if zona_sel_global != "Vista general" and not base_reporte.empty:
        col_zona_reporte = 'zona_vpm' if 'zona_vpm' in base_reporte.columns else ('zona' if 'zona' in base_reporte.columns else None)
        if col_zona_reporte is not None:
            zonas_reporte_norm = normalizar_zona_clave_serie(base_reporte[col_zona_reporte])
            base_reporte = base_reporte[zonas_reporte_norm == zona_sel_global_norm].copy()

    # Periodicidad del reporte personalizado:
    # - Mensual: conserva el dataset actual (una fila por cliente)
    # - Diario: expande a detalle por cliente-fecha con consumo_gj_diario
    if periodicidad_reporte == "Diario":
        if consumo_diario.empty:
            base_reporte = base_reporte.iloc[0:0].copy()
        else:
            consumo_rep = consumo_diario[['id_instalacion', 'fecha', 'consumo_gj']].copy()
            if fecha_ini and fecha_fin:
                mascara_periodo = (
                    (consumo_rep['fecha'].dt.date >= fecha_ini)
                    & (consumo_rep['fecha'].dt.date <= fecha_fin)
                )
                consumo_rep = consumo_rep[mascara_periodo].copy()
            consumo_rep = consumo_rep.rename(columns={
                'fecha': 'fecha_consumo',
                'consumo_gj': 'consumo_gj_diario',
            })
            base_reporte = base_reporte.merge(consumo_rep, on='id_instalacion', how='inner')

    if base_reporte.empty:
        st.subheader("📄 Generador de reportes personalizados")
        st.info("No hay datos disponibles para generar un reporte.")
    else:
        # --- 1) Selección de columnas ---
        # spread_popup, zona_geografica y status_norm se ocultan únicamente en
        # este selector (uso interno); siguen disponibles en el resto de la app.
        columnas_ocultas_reporte = {'spread_popup', 'zona_geografica', 'status_norm', 'zona', 'lat', 'lon', 'id_bp', 'razon_social'}
        columnas_disponibles = [
            c for c in base_reporte.columns if c not in columnas_ocultas_reporte
        ]

        # Columna calculada: % que representa el consumo del cliente dentro de
        # su zona (zona_vpm). Se agrega al selector solo si existen las
        # columnas base necesarias; el valor real se calcula más abajo sobre
        # `df_reporte` (después de aplicar los filtros de fecha/zona).
        tiene_columnas_pct_zona = (
            'zona_vpm' in columnas_disponibles and 'Consumo_Total_Periodo_GJ' in columnas_disponibles
        )
        if tiene_columnas_pct_zona and 'pct_cliente_zona' not in columnas_disponibles:
            columnas_disponibles = columnas_disponibles + ['pct_cliente_zona']

        # Columna calculada: Spread Ponderado (USD), depende de pct_cliente_zona
        # (arriba) y de spread_firme/spread_volumetrico_o_interrumpible.
        tiene_columnas_spread_ponderado = (
            tiene_columnas_pct_zona
            and 'spread_firme' in columnas_disponibles
            and 'spread_volumetrico_o_interrumpible' in columnas_disponibles
        )
        if tiene_columnas_spread_ponderado and 'spread_ponderado' not in columnas_disponibles:
            columnas_disponibles = columnas_disponibles + ['spread_ponderado']

        if periodicidad_reporte == "Diario":
            columnas_default = [
                c for c in [
                    'id_instalacion', 'bp', 'tipo_de_cliente', 'fecha_consumo',
                    'consumo_gj_diario', 'fecha_vigencia_actualizada', 'renovacion',
                    'ldc', 'zona_vpm', 'indice_referencia',
                    'spread_firme', 'spread_volumetrico_o_interrumpible',
                    'pct_cliente_zona', 'spread_ponderado'
                ]
                if c in columnas_disponibles
            ]
        else:
            columnas_default = [
                c for c in [
                    'id_instalacion', 'bp', 'tipo_de_cliente', 'Consumo_Total_Periodo_GJ',
                    'fecha_vigencia_actualizada', 'renovacion', 'ldc', 'zona_vpm',
                    'indice_referencia', 'spread_firme',
                    'spread_volumetrico_o_interrumpible', 'pct_cliente_zona', 'spread_ponderado'
                ]
                if c in columnas_disponibles
            ]

        columnas_state_key = f"reporte_columnas_orden_{periodicidad_reporte.lower()}"

        # El orden y la selección de columnas se gestionan desde el modal
        # "Manage Columns" (ver `_dialog_manage_columns`) y se persisten aquí.
        if columnas_state_key not in st.session_state:
            st.session_state[columnas_state_key] = list(columnas_default)
        else:
            # Elimina columnas que ya no existen en el dataset actual.
            st.session_state[columnas_state_key] = [
                c for c in st.session_state[columnas_state_key] if c in columnas_disponibles
            ]
        columnas_orden = st.session_state[columnas_state_key]

        # El filtro por fecha se deshabilita en la pestaña de reportes.
        if "mostrar_manage_columns" not in st.session_state:
            st.session_state["mostrar_manage_columns"] = False

        col_fecha_sel = "(sin filtro)"
        fecha_ini_rep = fecha_fin_rep = None
        f_min = f_max = None
        serie_fecha = None

        # --- Aplicar filtros ---
        df_reporte = base_reporte.copy()

        # % cliente por Zona = Consumo_Total_Periodo_GJ del cliente / suma de
        # Consumo_Total_Periodo_GJ de su zona (zona_vpm), sobre los datos ya
        # filtrados por fecha/zona. Expresado en escala 0-100.
        col_consumo_base = 'consumo_gj_diario' if periodicidad_reporte == "Diario" and 'consumo_gj_diario' in df_reporte.columns else 'Consumo_Total_Periodo_GJ'

        if 'zona_vpm' in df_reporte.columns and col_consumo_base in df_reporte.columns:
            consumo_num = pd.to_numeric(df_reporte[col_consumo_base], errors='coerce').fillna(0)
            zona_grupo = df_reporte['zona_vpm'].astype(str).str.strip()
            suma_zona = consumo_num.groupby(zona_grupo).transform('sum')
            df_reporte['pct_cliente_zona'] = np.where(
                suma_zona > 0, (consumo_num / suma_zona) * 100, 0.0
            )

        # Spread Ponderado (USD): si spread_firme != 0, promedio de ambos
        # spreads ponderado por pct_cliente_zona; si spread_firme == 0, solo
        # el spread volumétrico/interrumpible ponderado por pct_cliente_zona.
        if (
            'spread_firme' in df_reporte.columns
            and 'spread_volumetrico_o_interrumpible' in df_reporte.columns
            and 'pct_cliente_zona' in df_reporte.columns
        ):
            spread_firme_num = pd.to_numeric(df_reporte['spread_firme'], errors='coerce').fillna(0)
            spread_vol_num = pd.to_numeric(df_reporte['spread_volumetrico_o_interrumpible'], errors='coerce').fillna(0)
            pct_zona_num = pd.to_numeric(df_reporte['pct_cliente_zona'], errors='coerce').fillna(0) / 100
            df_reporte['spread_ponderado'] = np.where(
                spread_firme_num != 0,
                ((spread_firme_num + spread_vol_num) / 2) * pct_zona_num,
                spread_vol_num * pct_zona_num,
            )

        # Aplicar filtro de Cliente/Id de Instalación solo para visualización
        # (los cálculos de % zona y spreads ya fueron hechos sobre datos completos)
        if filtro_clientes:
            df_reporte = df_reporte[mascara_filtro_cliente_instalacion(df_reporte, filtro_clientes)]

        # --- 4) Vista previa ---
        df_reporte_final = None
        if columnas_orden:
            df_reporte_final = df_reporte[columnas_orden].copy()
            df_reporte_final = df_reporte_final.rename(columns=generar_renombres_reporte(df_reporte_final.columns))

        col_titulo, col_acciones = st.columns([4, 2])
        with col_titulo:
            st.subheader("📄 Generador de reportes personalizados")
        with col_acciones:
            col_btn_manage, col_btn_export = st.columns(2)
            with col_btn_manage:
                if st.button("🛠️ Manage Columns", key="btn_manage_columns", use_container_width=True):
                    for c in columnas_disponibles:
                        st.session_state.pop(f"gestion_col_chk_{c}", None)
                    st.session_state["gestion_columnas_draft"] = list(columnas_orden)
                    st.session_state["mostrar_manage_columns"] = True
            with col_btn_export:
                if df_reporte_final is not None:
                    buffer_export = BytesIO()
                    with pd.ExcelWriter(
                        buffer_export,
                        engine='xlsxwriter',
                        date_format='dd/mm/yyyy',
                        datetime_format='dd/mm/yyyy',
                    ) as writer:
                        df_reporte_final.to_excel(writer, index=False, sheet_name='Reporte')
                    export_clicked = st.download_button(
                        "Export",
                        buffer_export.getvalue(),
                        "reporte_personalizado.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_excel_reporte_header",
                        use_container_width=True,
                    )
                    if export_clicked:
                        st.session_state["mostrar_manage_columns"] = False
                else:
                    st.button("Export", key="btn_export_disabled_header", disabled=True, use_container_width=True)

            st.segmented_control(
                "Periodicidad",
                options=["Mensual", "Diario"],
                key="reporte_periodicidad",
                default="Mensual",
                label_visibility="collapsed",
            )

            if st.session_state.get("mostrar_manage_columns"):
                _dialog_manage_columns(columnas_disponibles, columnas_default, columnas_state_key)

        texto_registros = f"Registros: {len(df_reporte_final)}" if df_reporte_final is not None else ""
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.5rem;">
                <strong>Vista previa del reporte</strong>
                <span>{texto_registros}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not columnas_orden:
            st.info("Selecciona al menos una columna para generar el reporte.")
        else:
            renombres_aplicados = generar_renombres_reporte(columnas_orden)
            column_config_reporte = column_config_fechas(df_reporte_final.columns, renombres_aplicados)
            nombre_fecha_consumo = renombres_aplicados.get('fecha_consumo')
            if nombre_fecha_consumo in df_reporte_final.columns:
                column_config_reporte[nombre_fecha_consumo] = st.column_config.DateColumn(
                    nombre_fecha_consumo, format="DD/MM/YYYY"
                )
            nombre_consumo_diario = renombres_aplicados.get('consumo_gj_diario')
            if nombre_consumo_diario in df_reporte_final.columns:
                column_config_reporte[nombre_consumo_diario] = st.column_config.NumberColumn(
                    nombre_consumo_diario, format='%,.4f GJ'
                )
            nombre_pct_zona = renombres_aplicados.get('pct_cliente_zona')
            if nombre_pct_zona in df_reporte_final.columns:
                column_config_reporte[nombre_pct_zona] = st.column_config.NumberColumn(
                    nombre_pct_zona, format='%.4f%%'
                )
            nombre_spread_ponderado = renombres_aplicados.get('spread_ponderado')
            if nombre_spread_ponderado in df_reporte_final.columns:
                column_config_reporte[nombre_spread_ponderado] = st.column_config.NumberColumn(
                    nombre_spread_ponderado, format='$%,.4f'
                )
            st.dataframe(
                df_reporte_final,
                use_container_width=True,
                hide_index=True,
                column_config=column_config_reporte,
            )

            st.markdown("**Resumen por zona**")
            col_resumen_consumo = col_consumo_base
            if 'zona_vpm' not in df_reporte.columns or col_resumen_consumo not in df_reporte.columns:
                st.info("No hay datos suficientes para construir el resumen por zona.")
            else:
                columnas_resumen = ['zona_vpm', col_resumen_consumo]
                if 'spread_ponderado' in df_reporte.columns:
                    columnas_resumen.append('spread_ponderado')
                resumen_base = df_reporte[columnas_resumen].copy()
                resumen_base['zona_vpm'] = resumen_base['zona_vpm'].astype(str).str.strip()
                resumen_base['zona_vpm'] = resumen_base['zona_vpm'].replace({'': 'Sin zona', 'nan': 'Sin zona', 'None': 'Sin zona'})
                resumen_base[col_resumen_consumo] = pd.to_numeric(
                    resumen_base[col_resumen_consumo], errors='coerce'
                ).fillna(0)
                if 'spread_ponderado' in resumen_base.columns:
                    resumen_base['spread_ponderado'] = pd.to_numeric(
                        resumen_base['spread_ponderado'], errors='coerce'
                    ).fillna(0)
                else:
                    resumen_base['spread_ponderado'] = 0.0

                if col_resumen_consumo != 'Consumo_Total_Periodo_GJ':
                    resumen_base = resumen_base.rename(columns={col_resumen_consumo: 'Consumo_Total_Periodo_GJ'})

                resumen_zona = _resumen_zona_reporte(resumen_base)

                total_consumo_zonas = float(resumen_zona['Consumo_Total_Periodo_GJ'].sum())
                if total_consumo_zonas > 0:
                    resumen_zona['% por Zona'] = (
                        resumen_zona['Consumo_Total_Periodo_GJ'] / total_consumo_zonas
                    ) * 100
                else:
                    resumen_zona['% por Zona'] = 0.0

                resumen_zona['Spread Promedio Ponderado (USD)'] = resumen_zona['spread_ponderado']
                resumen_zona = resumen_zona.drop(columns=['spread_ponderado'])

                st.dataframe(
                    resumen_zona,
                    use_container_width=True,
                    hide_index=True,
                    height="content",
                    column_config={
                        'Consumo_Total_Periodo_GJ': st.column_config.NumberColumn(
                            'Consumo_Total_Periodo_GJ', format='%,.0f GJ'
                        ),
                        '% por Zona': st.column_config.NumberColumn('% por Zona', format='%.2f'),
                        'Spread Promedio Ponderado (USD)': st.column_config.NumberColumn(
                            'Spread Promedio Ponderado (USD)', format='$%,.4f'
                        ),
                    },
                )

            # Descargas adicionales removidas: solo se conserva Export (Excel)

    # ========================================================
    # INICIO BLOQUE COMENTADO — Resultado y Clientes fuera de su zona
    # (descomentar si se necesita volver a mostrar estas secciones)
    # ========================================================
    # st.markdown("---")
    # st.subheader("Resultado")
    #
    # st.write(f"Total de registros: {len(df_mostrar_seccion)}")
    # st.dataframe(
    #     df_mostrar_seccion,
    #     use_container_width=True,
    #     hide_index=True,
    #     column_config=column_config_fechas(df_mostrar_seccion.columns),
    # )
    #
    # col1, col2 = st.columns(2)
    # with col1:
    #     csv = df_mostrar_seccion.to_csv(index=False).encode('utf-8-sig')
    #     st.download_button("Descargar CSV", csv, "resultado.csv", "text/csv")
    # with col2:
    #     buffer = BytesIO()
    #     with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    #         df_mostrar_seccion.to_excel(writer, index=False, sheet_name='Datos')
    #     st.download_button(
    #         "Descargar Excel", buffer.getvalue(),
    #         "resultado.xlsx",
    #         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #     )
    #
    # # ========================================================
    # # Clientes cuya zona declarada no concuerda con su ubicación
    # # ========================================================
    # st.markdown("---")
    # st.subheader("⚠️ Clientes fuera de su zona")
    # st.caption(
    #     "Compara la zona declarada (columna Zonas del Excel) contra la zona "
    #     "geográfica real calculada a partir de las coordenadas del cliente "
    #     "(point-in-polygon). Incluye a todos los clientes, sin importar el "
    #     "filtro aplicado arriba."
    # )
    #
    # if df_geo.empty:
    #     st.info("No hay datos geocodificados disponibles todavía.")
    # else:
    #     df_no_concuerda = df_geo[
    #         df_geo['zona_geografica'].notna()
    #         & (df_geo['zona_geografica'] != df_geo['zona'])
    #     ].copy()
    #
    #     columnas_no_concuerda = [
    #         c for c in [
    #             'id_instalacion', 'bp', 'cp_localizacion', 'estado_localizacion',
    #             'nodo', 'zona_vpm', 'zona_geografica',
    #         ] if c in df_no_concuerda.columns
    #     ]
    #     df_no_concuerda = df_no_concuerda[columnas_no_concuerda].rename(
    #         columns={'zona_vpm': 'zona_HOP'}
    #     )
    #
    #     st.write(f"Total de clientes fuera de su zona: {len(df_no_concuerda)}")
    #
    #     if df_no_concuerda.empty:
    #         st.success("Todos los clientes geocodificados están dentro de su zona declarada.")
    #     else:
    #         st.dataframe(df_no_concuerda, use_container_width=True, hide_index=True)
    #
    #         colnz1, colnz2 = st.columns(2)
    #         with colnz1:
    #             csv_nz = df_no_concuerda.to_csv(index=False).encode('utf-8-sig')
    #             st.download_button(
    #                 "Descargar CSV (fuera de zona)", csv_nz,
    #                 "clientes_fuera_de_zona.csv", "text/csv",
    #                 key="csv_fuera_zona",
    #             )
    #         with colnz2:
    #             buffer_nz = BytesIO()
    #             with pd.ExcelWriter(buffer_nz, engine='xlsxwriter') as writer:
    #                 df_no_concuerda.to_excel(writer, index=False, sheet_name='Fuera de zona')
    #             st.download_button(
    #                 "Descargar Excel (fuera de zona)", buffer_nz.getvalue(),
    #                 "clientes_fuera_de_zona.xlsx",
    #                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #                 key="excel_fuera_zona",
    #             )
    # ========================================================
    # FIN BLOQUE COMENTADO
    # ========================================================


# ============================================================
# SECCIÓN: TOP 10
# ============================================================
elif seccion == "Dashboard":
    st.subheader("Top N consumidores por periodo")

    df_geo_top10 = df_geo

    if cols_consumo and not df_geo_top10.empty:
        # El filtro de zona ya se aplicó de forma global (sidebar) sobre df_geo,
        # por lo que aquí solo se usa directamente.
        base_top = df_geo_top10

        # Filtro global de instalación antes de las pestañas
        filtro_top10_global = st.text_input(
            "Filtrar por Cliente o Id de Instalación",
            key="filtro_instalacion_top10_global",
            placeholder="Ej: Alpezzi Chocolate o 600601101",
        )

        subtabs = st.tabs([nombre_tab_consumo(c) for c in cols_consumo])

        zona_sel_global_top10 = st.session_state.get("zona_widget", "Vista general")
        zona_txt = f"en {zona_sel_global_top10}" if zona_sel_global_top10 != "Vista general" else "a nivel nacional"

        # Paleta ENGIE de 10 colores (del mas oscuro al mas claro)
        ENGIE_TOP10_COLORS = [
            "#002B49", "#003C88", "#005C9A", "#0077CC",
            "#278CBC", "#7FA8D8", "#A8C8EE", "#BDD9F5",
            "#CDE7FF", "#DFF0FF",
        ]

        # Paleta ENGIE de 50 colores (del mas oscuro al mas claro)
        ENGIE_TOP50_COLORS = [
        "#002B49", "#00304F", "#003555", "#003A5B", "#003F61",
        "#004467", "#00496D", "#004E73", "#005379", "#00587F",
        "#005D85", "#00628B", "#006791", "#006C97", "#00719D",

        "#003C88", "#00418D", "#004692", "#004B97", "#00509C",
        "#0055A1", "#005AA6", "#005FAB", "#0064B0", "#0069B5",
        "#006EBA", "#0073BF", "#0078C4", "#007DC9", "#0082CE",

        "#005C9A", "#00619F", "#0066A4", "#006BA9", "#0070AE",
        "#0075B3", "#007AB8", "#007FBD", "#0084C2", "#0089C7",

        "#278CBC", "#2E91C0", "#3596C4", "#3C9BC8", "#43A0CC",
        "#4AA5D0", "#51AAD4", "#58AFD8", "#5FB4DC", "#66B9E0"
        ]



        for subtab, col in zip(subtabs, cols_consumo):
            with subtab:
                # Fila de control: slider y descarga alineados
                control_col, _ = st.columns([5, 1.4])
                
                with control_col:
                    n_top = st.slider(
                        "Número de clientes en el Top N",
                        min_value=3,
                        max_value=50,
                        value=10,
                        step=1,
                        key=f"top_n_consumidores_dashboard_{col}",
                        help="Selecciona cuántos clientes quieres ver en la gráfica y en el ranking.",
                    )



                df_geo_top10_local = base_top
                if filtro_top10_global and not base_top.empty:
                    df_geo_top10_local = base_top[mascara_filtro_cliente_instalacion(base_top, filtro_top10_global)]

                # Usar 'bp' si existe, si no usar 'razon_social'
                col_nombre = 'bp' if 'bp' in df_geo_top10_local.columns else 'razon_social'
                # Se agrupa por id_instalacion (clave única real) + nombre de
                # cliente, para no fusionar en una sola barra instalaciones
                # distintas de un mismo cliente (p.ej. un cliente con plantas
                # en varios estados). El estado se agrega después solo para
                # mostrarlo en la tabla/hover, no como parte del agrupado.
                usa_instalacion = 'id_instalacion' in df_geo_top10_local.columns

                col_prev = col_periodo_anterior(col, df_geo_top10_local.columns)
                # Groupby/sort/merge pesado factorizado y cacheado (ver
                # _top_n_y_ranking_previo): st.tabs() ejecuta el cuerpo de las
                # 12 pestañas en cada rerun, así que este cálculo se repetiría
                # aunque el usuario no cambie de mes; con @st.cache_data se
                # reusa el resultado si (df_geo_top10_local, col, col_prev,
                # n_top) no cambiaron desde el rerun anterior.
                # IMPORTANTE: aunque el resultado esté cacheado, st.cache_data
                # igual necesita hashear el DataFrame de entrada en cada una
                # de las 12 llamadas por rerun; hacerlo sobre df_geo completo
                # (decenas de columnas: consumo mensual, lat/lon, zonas, etc.)
                # es en sí mismo costoso. Se recorta a solo las columnas que la
                # función realmente usa ANTES de llamarla, para que el hash se
                # calcule sobre un DataFrame angosto y el cache hit sea casi
                # instantáneo.
                cols_necesarias = []
                for col_extra in ('id_instalacion', 'bp', 'razon_social', 'estado_localizacion'):
                    if col_extra in df_geo_top10_local.columns:
                        cols_necesarias.append(col_extra)
                cols_necesarias.append(col)
                if col_prev and col_prev not in cols_necesarias:
                    cols_necesarias.append(col_prev)
                df_top_slim = df_geo_top10_local[cols_necesarias]

                top, ranking_prev = _top_n_y_ranking_previo(
                    df_top_slim, col, col_prev, n_top
                )

                if top.empty:
                    st.info("Sin datos de consumo para esta combinación de periodo y zona.")
                else:
                    total_periodo = pd.to_numeric(df_geo_top10_local[col], errors='coerce').fillna(0).sum()
                    top10_sum = float(top[col].sum())
                    concentracion = (top10_sum / total_periodo) if total_periodo else 0
                    lider = top.iloc[0]

                    rank_prev_map = {}
                    top_prev10_set = set()
                    if col_prev:
                        rank_prev_map = {nombre: i + 1 for i, nombre in enumerate(ranking_prev.index)}
                        top_prev10_set = set(ranking_prev.head(10).index.tolist())

                    top_actual_set = set(top['bp'].dropna().tolist())
                    entradas_top10 = sorted(top_actual_set - top_prev10_set)
                    salidas_top10 = sorted(top_prev10_set - top_actual_set)
                    repiten_top10 = sorted(top_actual_set & top_prev10_set)
                    base_rotacion = len(top_actual_set) if top_actual_set else 10
                    rotacion_top10 = (len(entradas_top10) / base_rotacion) if top_prev10_set else 0
                    persistencia_top10 = (len(repiten_top10) / base_rotacion) if top_prev10_set else 0

                    if top_prev10_set:
                        st.caption(
                            f"🔄 Rotación vs {etiqueta_periodo(col_prev)}: "
                            f"{len(entradas_top10)} entrada(s), {len(salidas_top10)} salida(s), "
                            f"{len(repiten_top10)} cliente(s) que se mantienen."
                        )
                    else:
                        st.caption("No hay un mes anterior disponible para comparar tendencia.")

                    k1, k2, k3, k4 = st.columns(4)
                    with k1:
                        render_mini_alert_card(
                            "LÍDER DEL PERIODO", f"{lider[col]:,.0f} GJ",
                            subtitle=str(lider['bp']), icon="🥇", color="#0077CC",
                        )
                    with k2:
                        render_mini_alert_card(
                            "CONCENTRACIÓN TOP 10", f"{concentracion:.0%}",
                            subtitle=f"de {total_periodo:,.0f} GJ totales", icon="🎯", color="#12B886",
                        )
                    with k3:
                        render_mini_alert_card(
                            "ENTRADAS AL TOP 10",
                            f"{len(entradas_top10)}" if top_prev10_set else "N/D",
                            subtitle=f"Rotación {rotacion_top10:.0%}" if top_prev10_set else "Sin mes anterior disponible",
                            icon="🆕", color="#F59F00",
                        )
                    with k4:
                        render_mini_alert_card(
                            "SALIDAS DEL TOP 10",
                            f"{len(salidas_top10)}" if top_prev10_set else "N/D",
                            subtitle=f"Persistencia {persistencia_top10:.0%}" if top_prev10_set else "Sin mes anterior disponible",
                            icon="📤", color="#E03131",
                        )

                    if top_prev10_set:
                        ent_txt = ", ".join(map(str, entradas_top10)) if entradas_top10 else "Sin entradas"
                        sal_txt = ", ".join(map(str, salidas_top10)) if salidas_top10 else "Sin salidas"
                        st.caption(f"Entran: {ent_txt}")
                        st.caption(f"Salen: {sal_txt}")

                    st.write("")

                    top_fmt = top.rename(columns={
                        'id_instalacion': 'Instalación',
                        col_nombre: 'Cliente',
                        'estado_localizacion': 'Estado',
                        col: 'Consumo (GJ)',
                    })
                    cols_top_fmt = (['Instalación'] if usa_instalacion else []) + ['Cliente', 'Estado', 'Consumo (GJ)']
                    top_fmt = top_fmt[cols_top_fmt]

                    # ---- Grafico de barras horizontal, mayor a menor, paleta ENGIE ----
                    top_chart = top_fmt.sort_values('Consumo (GJ)', ascending=True).reset_index(drop=True)
                    n_bars = len(top_chart)
                    paleta = ENGIE_TOP10_COLORS if n_bars <= 10 else ENGIE_TOP50_COLORS
                    bar_colors = paleta[:n_bars][::-1]

                    # Clientes que aparecen más de una vez en el Top N (varias
                    # instalaciones distintas dentro del ranking).
                    conteo_cliente = top_chart['Cliente'].value_counts()

                    # Etiqueta del eje Y: el nombre del cliente (bp); si un mismo
                    # cliente aparece más de una vez (varias instalaciones), se
                    # añade un sufijo corto con el id_instalacion para que cada
                    # barra sea una categoría distinta y no se fusionen entre sí.
                    if usa_instalacion:
                        y_labels = top_chart.apply(
                            lambda row: (
                                f"{row['Cliente']} ({row['Instalación']})"
                                if conteo_cliente.get(row['Cliente'], 1) > 1
                                else str(row['Cliente'])
                            ),
                            axis=1,
                        )
                    else:
                        y_labels = top_chart['Cliente'].astype(str)

                    def _hover_fila(row):
                        lineas = [f"<b>{row['Cliente']}</b>"]
                        if usa_instalacion:
                            lineas.append(f"Instalación: {row['Instalación']}")
                        lineas.append(f"Estado: {row['Estado']}")
                        lineas.append(f"Consumo: {row['Consumo (GJ)']:,.0f} GJ")
                        if conteo_cliente.get(row['Cliente'], 1) > 1:
                            lineas.append(
                                f"⚠️ {row['Cliente']} tiene {conteo_cliente[row['Cliente']]} "
                                f"instalaciones distintas dentro de este Top {n_top}."
                            )
                        return "<br>".join(lineas)

                    hovertext = top_chart.apply(_hover_fila, axis=1)

                    option_top10 = {
                        "tooltip": {
                            **DASHBOARD_TOOLTIP,
                            "trigger": "item",
                            "formatter": JsCode("function (p) { return p.data.hover; }"),
                        },
                        "grid": {"left": 10, "right": 200, "top": 56, "bottom": 48, "containLabel": True},
                        "xAxis": {
                            "type": "value",
                            "name": "Consumo (GJ)",
                            "nameLocation": "middle",
                            "nameGap": 30,
                            "axisLine": {"show": False},
                            "axisTick": {"show": False},
                            "splitLine": {"show": True, "lineStyle": {"color": "#EEF2F7"}},
                            "axisLabel": {"color": "#1F2937"},
                        },
                        "yAxis": {
                            "type": "category",
                            "data": list(y_labels),
                            "axisLine": {"show": False},
                            "axisTick": {"show": False},
                            "axisLabel": {"fontSize": 11, "color": "#111827"},
                        },
                        "series": [{
                            "type": "bar",
                            "barCategoryGap": "20%",
                            "itemStyle": {"shadowBlur": 20, "shadowColor": "rgba(0,0,0,0.15)", "shadowOffsetX": 6},
                            "emphasis": {"itemStyle": {"shadowBlur": 28, "shadowColor": "rgba(0,0,0,0.25)"}},
                            "data": [
                                {
                                    "value": float(valor),
                                    "itemStyle": {"color": _degradado_lineal(color), "borderRadius": [0, 10, 10, 0]},
                                    "texto": f"{valor:,.0f}",
                                    "hover": hover,
                                }
                                for valor, color, hover in zip(top_chart['Consumo (GJ)'], bar_colors, hovertext)
                            ],
                            "label": {
                                "show": True,
                                "position": "right",
                                "fontSize": 10,
                                "fontWeight": "bold",
                                "color": "#1F2937",
                                "formatter": JsCode("function (p) { return p.data.texto; }"),
                            },
                        }],
                    }
                    _dashboard_echarts(option_top10, max(300, 44 * n_bars), key=f"top_chart_{col}")

                    clientes_repetidos = conteo_cliente[conteo_cliente > 1]
                    if not clientes_repetidos.empty:
                        st.caption(
                            "ℹ️ Algunos clientes aparecen más de una vez porque tienen varias "
                            "instalaciones (id_instalacion) con consumo propio: "
                            + ", ".join(f"{c} ({n})" for c, n in clientes_repetidos.items())
                        )

                    st.dataframe(
                        top_fmt.style.format({'Consumo (GJ)': '{:,.0f}'}),
                        use_container_width=True,
                        hide_index=True,
                    )

                    # ============================================================
                    # ANALISIS (KPIs + evolucion + zonas)
                    # ============================================================
                    st.markdown("---")
                    st.markdown("### Análisis")

                    df_an = base_top.copy()
                    df_an['Consumo_Total_Periodo_GJ'] = pd.to_numeric(
                        df_an.get('Consumo_Total_Periodo_GJ', 0), errors='coerce'
                    ).fillna(0)
                    ids_an = set(df_an['id_instalacion'].dropna().unique())

                    # ---- Serie mensual de volumen (historico) ----
                    base_mensual = consumo_diario[consumo_diario['id_instalacion'].isin(ids_an)].copy()
                    base_mensual['AñoMes'] = base_mensual['fecha'].dt.to_period('M')
                    serie_mensual = base_mensual.groupby('AñoMes')['consumo_gj'].sum().sort_index()
                    clientes_por_mes = base_mensual.groupby('AñoMes')['id_instalacion'].nunique()

                    meses_an = serie_mensual.index.tolist()
                    mes_act = meses_an[-1] if meses_an else None
                    mes_ant = meses_an[-2] if len(meses_an) > 1 else None

                    def _delta_pct(actual, previo):
                        if previo in (None, 0) or previo != previo:
                            return None
                        return (actual - previo) / previo * 100

                    def _sub_delta(delta):
                        if delta is None:
                            return "Sin mes anterior"
                        flecha = "▲" if delta >= 0 else "▼"
                        return f"{flecha} {delta:+.1f}% vs mes anterior"

                    vol_act = float(serie_mensual.get(mes_act, 0)) if mes_act is not None else 0.0
                    vol_ant = float(serie_mensual.get(mes_ant, 0)) if mes_ant is not None else None
                    cli_act = int(clientes_por_mes.get(mes_act, 0)) if mes_act is not None else 0
                    cli_ant = int(clientes_por_mes.get(mes_ant, 0)) if mes_ant is not None else None
                    vol_prom = (vol_act / cli_act) if cli_act else 0.0
                    vol_prom_ant = (vol_ant / cli_ant) if (vol_ant and cli_ant) else None
                    mes_act_txt = month_to_spanish_label(str(mes_act)) if mes_act is not None else "N/D"

                    # Spread ponderado promedio
                    spread_pond_prom = 0.0
                    if {'zona_vpm', 'spread_firme', 'spread_volumetrico_o_interrumpible'}.issubset(df_an.columns):
                        consumo_num = df_an['Consumo_Total_Periodo_GJ']
                        zona_grupo = df_an['zona_vpm'].astype(str).str.strip()
                        suma_zona = consumo_num.groupby(zona_grupo).transform('sum')
                        pct = np.where(suma_zona > 0, consumo_num / suma_zona, 0.0)
                        sf = pd.to_numeric(df_an['spread_firme'], errors='coerce').fillna(0)
                        sv = pd.to_numeric(df_an['spread_volumetrico_o_interrumpible'], errors='coerce').fillna(0)
                        spread_pond = np.where(sf != 0, ((sf + sv) / 2) * pct, sv * pct)
                        spread_pond_prom = float(np.mean(spread_pond)) if len(spread_pond) else 0.0

                    k1, k2, k3 = st.columns(3)
                    with k1:
                        render_mini_alert_card(
                            "CLIENTES", f"{cli_act:,}",
                            subtitle=_sub_delta(_delta_pct(cli_act, cli_ant)),
                            icon="👥", color="#12B886",
                        )
                    with k2:
                        render_mini_alert_card(
                            "VOLUMEN TOTAL", f"{vol_act:,.0f} GJ",
                            subtitle=f"Mes seleccionado: {mes_act_txt}",
                            icon="⚡", color="#0077CC",
                        )
                    with k3:
                        render_mini_alert_card(
                            "VOLUMEN PROMEDIO", f"{vol_prom:,.1f} GJ",
                            subtitle=_sub_delta(_delta_pct(vol_prom, vol_prom_ant)),
                            icon="📊", color="#F59F00",
                        )

                    st.write("")

                    st.markdown("**Evolución mensual de volumen**")
                    if serie_mensual.empty:
                        st.info("Sin datos mensuales para graficar.")
                    else:
                        x_labels = [month_to_spanish_label(str(m)) for m in serie_mensual.index]
                        option_evol = {
                            "tooltip": {
                                "trigger": "axis",
                                "axisPointer": {
                                    "type": "line",
                                    "lineStyle": {"color": "#7FB4D8", "width": 1},
                                },
                                "backgroundColor": "#111827",
                                "borderColor": "#111827",
                                "textStyle": {"color": "#FFFFFF", "fontSize": 12},
                                "formatter": JsCode(
                                    "function (params) {"
                                    " var points = Array.isArray(params) ? params : [params];"
                                    " var point = points[0];"
                                    " var value = Number(point.value).toLocaleString('es-MX', {maximumFractionDigits: 0});"
                                    " return '<b>' + point.axisValue + '</b><br>' + point.marker + 'Volumen: ' + value + ' GJ';"
                                    " }"
                                ),
                            },
                            "grid": {"left": 86, "right": 34, "top": 56, "bottom": 52, "containLabel": True},
                            "xAxis": {
                                "type": "category",
                                "data": x_labels,
                                "boundaryGap": False,
                                "axisLine": {"show": False},
                                "axisTick": {"show": False},
                                "axisLabel": {
                                    "margin": 12,
                                    "hideOverlap": False,
                                    "showMinLabel": True,
                                    "showMaxLabel": True,
                                    "formatter": JsCode(
                                        "function (value) { var parts = String(value).split(' '); if (parts.length >= 2) { return parts[0] + '\\n' + parts.slice(1).join(' '); } return value; }"
                                    ),
                                },
                                "splitLine": {"show": False},
                            },
                            "yAxis": {
                                "type": "value",
                                "name": "Volumen (GJ)",
                                "nameLocation": "middle",
                                "nameRotate": 90,
                                "nameGap": 118,
                                "nameTextStyle": {"fontWeight": 600, "color": "#334155", "fontSize": 12},
                                "min": 0,
                                "axisLabel": {
                                    "formatter": JsCode("function (v) { return Number(v).toLocaleString('en-US'); }"),
                                },
                                "axisLine": {"show": False},
                                "axisTick": {"show": False},
                                "splitLine": {"show": True, "lineStyle": {"color": "#EEF2F7"}},
                            },
                            "series": [{
                                "name": "Volumen",
                                "type": "line",
                                "data": [float(v) for v in serie_mensual.values],
                                "symbol": "circle",
                                "symbolSize": 7,
                                "lineStyle": {"color": "#007BC5", "width": 2},
                                "itemStyle": {"color": "#007BC5"},
                                "areaStyle": {"color": "rgba(0, 119, 204, 0.15)"},
                            }],
                        }
                        _dashboard_echarts(option_evol, 360, key=f"evol_{col}")

                    st.write("")
                    col_donut, col_barras = st.columns(2)

                    with col_donut:
                        st.markdown("**Participación de volumen por zona**")
                        vol_zona = (
                            df_geo_todas_zonas.groupby('zona')['Consumo_Total_Periodo_GJ']
                            .apply(lambda s: pd.to_numeric(s, errors='coerce').fillna(0).sum())
                            .sort_values(ascending=False)
                        )
                        vol_zona = vol_zona[vol_zona > 0]
                        if vol_zona.empty:
                            st.info("Sin volumen por zona.")
                        else:
                            total_zona = float(vol_zona.sum())
                            DONUT_CX, DONUT_CY = 230, 198
                            DONUT_R_IN, DONUT_R_OUT = 72, 162
                            # Color de respaldo distinto para zonas sin color definido (ej. Mayakan),
                            # para que no se confunda con el azul de Zona 8.
                            colores_donut_extra = {"Zona Mayakan": "#00897B"}
                            data_donut = []
                            for z, v in vol_zona.items():
                                color_z = ZONA_COLORS.get(z, colores_donut_extra.get(z, "#0077CC"))
                                item = {
                                    "name": z,
                                    "value": float(v),
                                    "itemStyle": {"color": _degradado_radial_donut(
                                        color_z, DONUT_CX, DONUT_CY, DONUT_R_OUT, DONUT_R_IN,
                                        oscuro=-0.30, claro=0.40,
                                    )},
                                }
                                if v / total_zona < 0.05:
                                    item["label"] = {"position": "outside", "color": "#333333"}
                                    item["labelLine"] = {"show": True, "length": 8, "length2": 6}
                                data_donut.append(item)

                            option_donut = {
                                "tooltip": {
                                    **DASHBOARD_TOOLTIP,
                                    "trigger": "item",
                                    "formatter": JsCode("function (p) { return '<b>' + p.name + '</b><br>' + Number(p.value).toLocaleString('en-US', {maximumFractionDigits: 0}) + ' GJ<br>' + Number(p.percent).toFixed(2) + '%'; }"),
                                },
                                "legend": {"orient": "vertical", "right": 10, "top": "middle", "selectedMode": False, "textStyle": {"color": "#1F2937"}},
                                "series": [{
                                    "type": "pie",
                                    "radius": [DONUT_R_IN, DONUT_R_OUT],
                                    "center": [DONUT_CX, DONUT_CY],
                                    "padAngle": 2.3,
                                    "minAngle": 5,
                                    "percentPrecision": 1,
                                    "selectedMode": "single",
                                    "itemStyle": {"borderRadius": 10, "shadowBlur": 20, "shadowColor": "rgba(0,0,0,0.15)", "shadowOffsetY": 6},
                                    "label": {"show": True, "position": "inside", "formatter": "{d}%", "fontWeight": "bold", "fontSize": 18, "color": "#1F2937"},
                                    "labelLine": {"show": False},
                                    "emphasis": {"scale": True, "scaleSize": 6},
                                    "data": data_donut,
                                }],
                            }
                            _dashboard_echarts(option_donut, 380, key=f"donut_{col}")

                    with col_barras:
                        st.markdown("**Clientes por zona**")
                        mes_col = col if col in df_geo_todas_zonas.columns else 'Consumo_Total_Periodo_GJ'
                        cli_zona = (
                            df_geo_todas_zonas[pd.to_numeric(df_geo_todas_zonas[mes_col], errors='coerce').fillna(0) > 0]
                            .groupby('zona').size()
                            .sort_values(ascending=True)
                        )
                        cli_zona = cli_zona[cli_zona > 0]
                        if cli_zona.empty:
                            st.info("Sin clientes por zona.")
                        else:
                            option_cli = {
                                "tooltip": {
                                    **DASHBOARD_TOOLTIP,
                                    "trigger": "item",
                                    "formatter": JsCode("function (p) { return '<b>' + p.name + '</b><br>' + Number(p.value).toLocaleString('en-US') + ' clientes'; }"),
                                },
                                "grid": {"left": 10, "right": 40, "top": 56, "bottom": 48, "containLabel": True},
                                "xAxis": {
                                    "type": "value",
                                    "name": "Clientes",
                                    "nameLocation": "middle",
                                    "nameGap": 30,
                                    "axisLine": {"show": False},
                                    "axisTick": {"show": False},
                                    "splitLine": {"show": True, "lineStyle": {"color": "#EEF2F7"}},
                                },
                                "yAxis": {
                                    "type": "category",
                                    "data": cli_zona.index.tolist(),
                                    "axisLine": {"show": False},
                                    "axisTick": {"show": False},
                                    "axisLabel": {"fontSize": 11},
                                },
                                "series": [{
                                    "type": "bar",
                                    "data": [int(v) for v in cli_zona.values],
                                    "itemStyle": {"color": "#007BC5"},
                                    "label": {"show": True, "position": "right", "fontSize": 11, "color": "#1F2937"},
                                }],
                            }
                            _dashboard_echarts(option_cli, 380, key=f"barzona_{col}")

                    st.markdown("---")

                    # ----- Tendencia diaria de consumo (detalle dia a dia) -----
                    base_tendencia = base_top.rename(
                        columns={'tipo_de_cliente': 'Segmentación'}
                    ).copy()
                    opciones_segmentacion = (
                        sorted(
                            base_tendencia['Segmentación'].dropna().astype(str).unique().tolist(),
                            key=str.casefold,
                        )
                        if 'Segmentación' in base_tendencia.columns else []
                    )
                    key_segmentacion = f"segmentacion_tendencia_{col}"
                    if key_segmentacion not in st.session_state:
                        st.session_state[key_segmentacion] = list(opciones_segmentacion)
                    else:
                        st.session_state[key_segmentacion] = [
                            valor for valor in st.session_state[key_segmentacion]
                            if valor in opciones_segmentacion
                        ]

                    mask_fecha = pd.Series(True, index=consumo_diario.index)
                    if col == 'Consumo_Total_Periodo_GJ':
                        if fecha_ini and fecha_fin:
                            mask_fecha = (
                                (consumo_diario['fecha'].dt.date >= fecha_ini)
                                & (consumo_diario['fecha'].dt.date <= fecha_fin)
                            )
                    else:
                        p = periodo_de_columna(col)
                        if p:
                            anio_p, mes_p = p
                            mask_fecha = (
                                (consumo_diario['fecha'].dt.year == anio_p)
                                & (consumo_diario['fecha'].dt.month == mes_p)
                            )
                            if fecha_ini and fecha_fin:
                                mask_fecha &= (
                                    (consumo_diario['fecha'].dt.date >= fecha_ini)
                                    & (consumo_diario['fecha'].dt.date <= fecha_fin)
                                )

                    columnas_tendencia = st.columns([5, 1])
                    with columnas_tendencia[0]:
                        st.markdown("**📈 Tendencia diaria de consumo**")
                    seleccion_count = len(st.session_state[key_segmentacion])
                    with columnas_tendencia[1]:
                        with st.popover(
                            f"Segmentación ({seleccion_count}/{len(opciones_segmentacion)})",
                            disabled=not opciones_segmentacion,
                        ):
                            botones_segmentacion = st.columns(2)
                            with botones_segmentacion[0]:
                                if st.button(
                                    "Seleccionar todo",
                                    key=f"segmentacion_todo_{col}",
                                    disabled=not opciones_segmentacion,
                                    use_container_width=True,
                                ):
                                    for valor in opciones_segmentacion:
                                        st.session_state[f"{key_segmentacion}_opcion_{valor}"] = True
                            with botones_segmentacion[1]:
                                if st.button(
                                    "Limpiar selección",
                                    key=f"segmentacion_limpiar_{col}",
                                    disabled=not opciones_segmentacion,
                                    use_container_width=True,
                                ):
                                    for valor in opciones_segmentacion:
                                        st.session_state[f"{key_segmentacion}_opcion_{valor}"] = False
                            segmentaciones_sel = []
                            for valor in opciones_segmentacion:
                                key_opcion = f"{key_segmentacion}_opcion_{valor}"
                                if key_opcion not in st.session_state:
                                    st.session_state[key_opcion] = valor in st.session_state[key_segmentacion]
                                if st.checkbox(valor, key=key_opcion):
                                    segmentaciones_sel.append(valor)
                            st.session_state[key_segmentacion] = segmentaciones_sel

                    if not segmentaciones_sel:
                        st.info("Selecciona al menos una segmentación")
                    else:
                        base_segmentada = base_tendencia[
                            base_tendencia['Segmentación'].astype(str).isin(segmentaciones_sel)
                        ]
                        ids_grupo = base_segmentada['id_instalacion'].dropna().unique().tolist()
                        diario_grupo = consumo_diario[
                            consumo_diario['id_instalacion'].isin(ids_grupo) & mask_fecha
                        ]

                        if diario_grupo.empty:
                            st.caption("Sin detalle diario disponible para graficar la tendencia de este periodo.")
                        else:
                            fechas_eje = pd.DatetimeIndex(
                                diario_grupo['fecha'].drop_duplicates().sort_values()
                            )
                            tendencia_total = (
                                diario_grupo.groupby('fecha')['consumo_gj'].sum()
                                .reindex(fechas_eje, fill_value=0)
                                .rename('Consumo (GJ)')
                                .sort_index()
                            )
                            st.caption(f"Consumo diario total {zona_txt} - {nombre_consumo(col)}")
                            fechas_total = [pd.Timestamp(f).strftime("%Y-%m-%d") for f in fechas_eje]
                            option_tend_total = {
                                "tooltip": {**DASHBOARD_TOOLTIP, "trigger": "axis"},
                                "grid": {"left": 65, "right": 20, "top": 56, "bottom": 35, "containLabel": True},
                                "xAxis": {
                                    "type": "category",
                                    "data": fechas_total,
                                    "boundaryGap": False,
                                    "name": "Fecha",
                                    "nameLocation": "middle",
                                    "nameGap": 28,
                                    "axisLine": {"show": False},
                                    "axisTick": {"show": False},
                                    "splitLine": {"show": False},
                                },
                                "yAxis": {
                                    "type": "value",
                                    "scale": True,
                                    "name": "Consumo (GJ)",
                                    "nameLocation": "middle",
                                    "nameRotate": 90,
                                    "nameGap": 85,
                                    "axisLine": {"show": False},
                                    "axisTick": {"show": False},
                                    "splitLine": {"show": True, "lineStyle": {"color": "#EEF2F7"}},
                                },
                                "series": [{
                                    "name": "Consumo (GJ)",
                                    "type": "line",
                                    "showSymbol": False,
                                    "data": [float(v) for v in tendencia_total.values],
                                    "lineStyle": {"color": "#007BC5", "width": 2},
                                    "itemStyle": {"color": "#007BC5"},
                                }],
                            }
                            _dashboard_echarts(option_tend_total, 500, key=f"tend_total_{col}")
                            datos_total_descarga = tendencia_total.rename('Consumo_GJ').reset_index()
                            datos_total_descarga.columns = ['Fecha', 'Consumo_GJ']
                            st.download_button(
                                "Descargar datos del consumo diario",
                                _excel_bytes_desde_hojas({'Tendencia_total': datos_total_descarga}),
                                "tendencia_diaria_consumo.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"dl_tendencia_total_{col}",
                                use_container_width=False,
                            )

                            meta_clientes = base_segmentada[
                                ['id_instalacion', 'bp']
                            ].dropna(subset=['id_instalacion', 'bp']).drop_duplicates()
                            diario_clientes = diario_grupo.merge(
                                meta_clientes, on='id_instalacion', how='inner'
                            )
                            top_lideres = (
                                diario_clientes.groupby('bp')['consumo_gj'].sum()
                                .sort_values(ascending=False)
                                .head(5)
                                .index.tolist()
                            )
                            diario_top = diario_clientes[diario_clientes['bp'].isin(top_lideres)]
                            if not diario_top.empty:
                                tendencia_clientes = (
                                    diario_top.groupby(['fecha', 'bp'])['consumo_gj'].sum()
                                    .reset_index()
                                    .pivot(index='fecha', columns='bp', values='consumo_gj')
                                    .reindex(index=fechas_eje)
                                    .sort_index()
                                )
                                st.caption("Tendencia diaria de los 5 clientes líderes del periodo")
                                fechas_lideres = fechas_total
                                clientes_ordenados = sorted(
                                    base_tendencia['bp'].dropna().astype(str).unique().tolist(),
                                    key=str.casefold,
                                )
                                colores_cliente = {
                                    nombre: DASHBOARD_LINE_COLORS[i % len(DASHBOARD_LINE_COLORS)]
                                    for i, nombre in enumerate(clientes_ordenados)
                                }
                                option_tend_lideres = {
                                    "legend": {"top": 0, "textStyle": {"color": "#1F2937"}},
                                    "tooltip": {**DASHBOARD_TOOLTIP, "trigger": "axis"},
                                    "grid": {"left": 65, "right": 20, "top": 56, "bottom": 35, "containLabel": True},
                                    "xAxis": {
                                        "type": "category",
                                        "data": fechas_lideres,
                                        "boundaryGap": False,
                                        "name": "Fecha",
                                        "nameLocation": "middle",
                                        "nameGap": 28,
                                        "axisLine": {"show": False},
                                        "axisTick": {"show": False},
                                        "splitLine": {"show": False},
                                    },
                                    "yAxis": {
                                        "type": "value",
                                        "scale": True,
                                        "name": "Consumo (GJ)",
                                        "nameLocation": "middle",
                                        "nameRotate": 90,
                                        "nameGap": 85,
                                        "axisLine": {"show": False},
                                        "axisTick": {"show": False},
                                        "splitLine": {"show": True, "lineStyle": {"color": "#EEF2F7"}},
                                    },
                                    "series": [
                                        {
                                            "name": str(nombre),
                                            "type": "line",
                                            "showSymbol": False,
                                            "connectNulls": False,
                                            "data": [None if pd.isna(v) else float(v) for v in tendencia_clientes[nombre]],
                                            "lineStyle": {"color": colores_cliente.get(str(nombre), DASHBOARD_LINE_COLORS[0]), "width": 2},
                                            "itemStyle": {"color": colores_cliente.get(str(nombre), DASHBOARD_LINE_COLORS[0])},
                                        }
                                        for nombre in tendencia_clientes.columns
                                    ],
                                }
                                _dashboard_echarts(option_tend_lideres, 500, key=f"tend_lideres_{col}")
                                datos_lideres_descarga = tendencia_clientes.reset_index().rename(columns={'fecha': 'Fecha'})
                                st.download_button(
                                    "Descargar datos de los 5 clientes líderes",
                                    _excel_bytes_desde_hojas({'Top_5_lideres': datos_lideres_descarga}),
                                    "tendencia_diaria_top_5_clientes.xlsx",
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"dl_tendencia_lideres_{col}",
                                    use_container_width=False,
                                )
    elif cols_consumo and df_geo.empty:
        st.info("No hay coordenadas para calcular el Top 10 por zona.")
    elif cols_consumo:
        st.info("Ningún cliente coincide con el filtro de Id de Instalación en esta sección.")
    else:
        st.info("No hay columnas de consumo para calcular el Top 10.")


# ============================================================
# SECCIÓN: GESTIÓN COMERCIAL (vista unificada)
# ============================================================
elif seccion == "Gestión Comercial":
    # Selector Clientes/Garantías arriba a la derecha de la sección. El valor
    # elegido se persiste en st.session_state["vista_cartera_garantias"] y
    # determina qué configuración (dataset + etiquetas) se le pasa a la
    # función reutilizable render_salud_ciclo_vida (layout/lógica idénticos).
    col_espacio, col_selector = st.columns([4.9, 1.1])
    with col_selector:
        vista_cartera_garantias = st.segmented_control(
            "Vista",
            options=["Clientes", "Garantías"],
            default="Clientes",
            key="vista_cartera_garantias",
            label_visibility="collapsed",
        )

    cfg_activa = GARANTIAS_CONFIG if vista_cartera_garantias == "Garantías" else CARTERA_CONFIG
    render_salud_ciclo_vida(cfg_activa)

# Se ejecuta al final para resetear el scroll después de renderizar la nueva sección.
if _should_scroll_top:
    components.html(
        f"""
        <script>
            // seccion: {escape(seccion)}
            (function () {{
                const win = window.parent;
                const doc = win.document;
                let stop = false;
                const halt = () => {{ stop = true; }};
                ['wheel', 'touchstart', 'keydown', 'mousedown'].forEach((evt) =>
                    doc.addEventListener(evt, halt, {{ once: true, passive: true }})
                );

                function toTop() {{
                    if (stop) return;
                    doc.querySelectorAll('*').forEach((node) => {{
                        if (node.scrollTop > 0 && node.scrollHeight > node.clientHeight) {{
                            node.scrollTop = 0;
                        }}
                    }});
                    win.scrollTo(0, 0);
                }}

                toTop();
                const timer = setInterval(toTop, 100);
                setTimeout(() => {{ clearInterval(timer); }}, 4000);
            }})();
        </script>
        """,
        height=0,
    )
