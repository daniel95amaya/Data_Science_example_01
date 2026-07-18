"""
Dashboard COVID-19 (datos sintéticos)
======================================
Streamlit + Plotly. Genera 10,000 registros sintéticos con 8 columnas de
distintos tipos de dato, ofrece estadística cuantitativa/cualitativa y
gráficas dinámicas totalmente personalizables por el usuario.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------
# Configuración general de la página
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard COVID-19 (Datos Sintéticos)",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

N_REGISTROS = 10_000

PAISES = [
    "Colombia", "México", "Argentina", "Chile", "Perú",
    "Brasil", "España", "Estados Unidos", "Ecuador", "Uruguay",
]
GRUPOS_EDAD = ["0-18", "19-35", "36-50", "51-65", "66+"]
GENEROS = ["Femenino", "Masculino", "Otro"]


# ----------------------------------------------------------------------
# Generación de datos sintéticos (cacheada por semilla)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner="Simulando registros sintéticos de COVID-19...")
def generar_datos(seed: int, n: int = N_REGISTROS) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    fechas = pd.to_datetime("2021-01-01") + pd.to_timedelta(
        rng.integers(0, 900, size=n), unit="D"
    )

    pais = rng.choice(PAISES, size=n, p=_pesos(len(PAISES), rng_seed=seed))
    grupo_edad = rng.choice(
        GRUPOS_EDAD, size=n, p=[0.20, 0.28, 0.24, 0.18, 0.10]
    )
    genero = rng.choice(GENEROS, size=n, p=[0.49, 0.49, 0.02])

    # Casos confirmados: distribución log-normal (asimétrica, realista)
    casos_confirmados = rng.lognormal(mean=4.2, sigma=1.1, size=n).astype(int)
    casos_confirmados = np.clip(casos_confirmados, 1, 5000)

    # Tasa de letalidad simulada por grupo de edad (mayor en adultos mayores)
    letalidad_base = pd.Series(grupo_edad).map(
        {"0-18": 0.001, "19-35": 0.003, "36-50": 0.008,
         "51-65": 0.02, "66+": 0.06}
    ).to_numpy()
    muertes = rng.binomial(casos_confirmados, letalidad_base)

    tasa_vacunacion = np.clip(rng.normal(65, 20, size=n), 0, 100).round(1)
    ocupacion_uci = np.clip(rng.normal(55, 25, size=n), 0, 100).round(1)

    df = pd.DataFrame({
        "fecha": fechas,
        "pais": pais,
        "grupo_edad": pd.Categorical(grupo_edad, categories=GRUPOS_EDAD, ordered=True),
        "genero": genero,
        "casos_confirmados": casos_confirmados.astype(int),
        "muertes": muertes.astype(int),
        "tasa_vacunacion": tasa_vacunacion.astype(float),
        "ocupacion_uci": ocupacion_uci.astype(float),
    })
    return df.sort_values("fecha").reset_index(drop=True)


def _pesos(k: int, rng_seed: int):
    rng = np.random.default_rng(rng_seed + 1)
    w = rng.dirichlet(np.ones(k) * 4)
    return w


# ----------------------------------------------------------------------
# Sidebar: control de datos, filtros y umbrales
# ----------------------------------------------------------------------
st.sidebar.title("⚙️ Panel de control")

st.sidebar.subheader("1. Datos sintéticos")
if "seed" not in st.session_state:
    st.session_state.seed = 42

col_a, col_b = st.sidebar.columns([1, 1])
with col_a:
    if st.button("🔄 Regenerar", use_container_width=True):
        st.session_state.seed = int(np.random.randint(0, 1_000_000))
with col_b:
    st.session_state.seed = st.number_input(
        "Semilla", value=st.session_state.seed, step=1, label_visibility="collapsed"
    )

df_full = generar_datos(st.session_state.seed)
st.sidebar.caption(f"📊 {len(df_full):,} registros · 8 columnas simuladas")

st.sidebar.divider()
st.sidebar.subheader("2. Filtros")

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(df_full["fecha"].min().date(), df_full["fecha"].max().date()),
    min_value=df_full["fecha"].min().date(),
    max_value=df_full["fecha"].max().date(),
)
paises_sel = st.sidebar.multiselect("País", PAISES, default=PAISES)
edad_sel = st.sidebar.multiselect("Grupo de edad", GRUPOS_EDAD, default=GRUPOS_EDAD)
genero_sel = st.sidebar.multiselect("Género", GENEROS, default=GENEROS)

st.sidebar.divider()
st.sidebar.subheader("3. Umbrales (alertas)")
umbral_casos = st.sidebar.slider(
    "Umbral casos confirmados", 0, int(df_full["casos_confirmados"].max()), 1500
)
umbral_vacunacion = st.sidebar.slider("Umbral mínimo tasa de vacunación (%)", 0, 100, 60)
umbral_uci = st.sidebar.slider("Umbral ocupación UCI crítica (%)", 0, 100, 80)

# Aplicar filtros
if len(rango_fechas) == 2:
    ini, fin = rango_fechas
else:
    ini, fin = df_full["fecha"].min().date(), df_full["fecha"].max().date()

df = df_full[
    (df_full["fecha"].dt.date >= ini)
    & (df_full["fecha"].dt.date <= fin)
    & (df_full["pais"].isin(paises_sel))
    & (df_full["grupo_edad"].isin(edad_sel))
    & (df_full["genero"].isin(genero_sel))
].copy()

if df.empty:
    st.warning("No hay registros con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

df["sobre_umbral_casos"] = df["casos_confirmados"] > umbral_casos
df["uci_critica"] = df["ocupacion_uci"] >= umbral_uci
df["vacunacion_baja"] = df["tasa_vacunacion"] < umbral_vacunacion

# ----------------------------------------------------------------------
# Encabezado + KPIs
# ----------------------------------------------------------------------
st.title("🦠 Dashboard COVID-19 — Datos Sintéticos Interactivos")
st.caption(
    "Todos los datos son **simulados** dentro de la plataforma con NumPy/Pandas "
    "y no representan cifras reales de salud pública."
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Registros filtrados", f"{len(df):,}")
k2.metric("Casos confirmados", f"{df['casos_confirmados'].sum():,}")
k3.metric("Muertes", f"{df['muertes'].sum():,}")
cfr = (df["muertes"].sum() / df["casos_confirmados"].sum() * 100) if df["casos_confirmados"].sum() else 0
k4.metric("Letalidad (CFR)", f"{cfr:.2f}%")
k5.metric("Vacunación promedio", f"{df['tasa_vacunacion'].mean():.1f}%")

alerta_casos = int(df["sobre_umbral_casos"].sum())
alerta_uci = int(df["uci_critica"].sum())
alerta_vac = int(df["vacunacion_baja"].sum())
a1, a2, a3 = st.columns(3)
a1.metric("🔺 Registros sobre umbral de casos", f"{alerta_casos:,}",
          f"{alerta_casos / len(df) * 100:.1f}% del total")
a2.metric("🏥 Registros con UCI crítica", f"{alerta_uci:,}",
          f"{alerta_uci / len(df) * 100:.1f}% del total")
a3.metric("💉 Registros con vacunación baja", f"{alerta_vac:,}",
          f"{alerta_vac / len(df) * 100:.1f}% del total")

st.divider()

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_cuanti, tab_cuali, tab_viz, tab_datos = st.tabs(
    ["📈 Estadística cuantitativa", "🗂️ Estadística cualitativa",
     "🎨 Gráficas dinámicas", "📄 Datos crudos"]
)

VARS_NUM = ["casos_confirmados", "muertes", "tasa_vacunacion", "ocupacion_uci"]
VARS_CAT = ["pais", "grupo_edad", "genero"]

# ---------------- TAB: Cuantitativa ----------------
with tab_cuanti:
    st.subheader("Resumen estadístico de variables numéricas")

    resumen = df[VARS_NUM].describe().T
    resumen["varianza"] = df[VARS_NUM].var()
    resumen["asimetría"] = df[VARS_NUM].skew()
    resumen["curtosis"] = df[VARS_NUM].kurt()
    st.dataframe(resumen.style.format("{:.2f}"), use_container_width=True)

    var_hist = st.selectbox("Variable para distribución", VARS_NUM, key="hist_cuanti")
    n_bins = st.slider("Número de bins", 5, 100, 30)
    fig_hist = px.histogram(
        df, x=var_hist, nbins=n_bins, marginal="box",
        color_discrete_sequence=["#5B8FF9"],
        title=f"Distribución de {var_hist}",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("**Matriz de correlación (variables numéricas)**")
    corr = df[VARS_NUM].corr()
    fig_corr = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Correlación entre variables numéricas",
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# ---------------- TAB: Cualitativa ----------------
with tab_cuali:
    st.subheader("Resumen de variables categóricas")

    var_cat = st.selectbox("Variable categórica", VARS_CAT, key="cat_select")
    conteo = df[var_cat].value_counts().reset_index()
    conteo.columns = [var_cat, "frecuencia"]
    conteo["porcentaje"] = (conteo["frecuencia"] / conteo["frecuencia"].sum() * 100).round(2)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.dataframe(conteo, use_container_width=True, hide_index=True)
        st.metric("Moda", str(df[var_cat].mode().iloc[0]))
        st.metric("N.º de categorías", df[var_cat].nunique())
    with c2:
        tipo_grafico_cat = st.radio("Tipo de gráfica", ["Barras", "Dona"], horizontal=True)
        if tipo_grafico_cat == "Barras":
            fig_cat = px.bar(conteo, x=var_cat, y="frecuencia", color=var_cat,
                              text="porcentaje", title=f"Frecuencia de {var_cat}")
        else:
            fig_cat = px.pie(conteo, names=var_cat, values="frecuencia", hole=0.45,
                              title=f"Proporción de {var_cat}")
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("**Tabla cruzada (dos variables categóricas)**")
    cc1, cc2 = st.columns(2)
    v1 = cc1.selectbox("Variable A", VARS_CAT, index=0, key="cruz_a")
    v2 = cc2.selectbox("Variable B", VARS_CAT, index=1, key="cruz_b")
    if v1 != v2:
        tabla_cruzada = pd.crosstab(df[v1], df[v2])
        st.dataframe(tabla_cruzada, use_container_width=True)
        fig_cruz = px.bar(tabla_cruzada, barmode="group",
                           title=f"{v1} vs {v2}")
        st.plotly_chart(fig_cruz, use_container_width=True)
    else:
        st.info("Selecciona dos variables distintas para la tabla cruzada.")

# ---------------- TAB: Gráficas dinámicas ----------------
with tab_viz:
    st.subheader("Constructor de gráficas dinámicas")
    st.caption("Elige variables, tipo de gráfica y personaliza el estilo.")

    todas_vars = VARS_NUM + VARS_CAT + ["fecha"]

    col1, col2, col3 = st.columns(3)
    tipo_grafico = col1.selectbox(
        "Tipo de gráfica",
        ["Dispersión", "Línea", "Barras", "Boxplot", "Violin", "Histograma"],
    )
    var_x = col2.selectbox("Variable X", todas_vars, index=todas_vars.index("fecha"))
    default_y = "casos_confirmados" if tipo_grafico != "Histograma" else VARS_NUM[0]
    var_y = col3.selectbox(
        "Variable Y", VARS_NUM,
        index=VARS_NUM.index(default_y) if default_y in VARS_NUM else 0,
        disabled=(tipo_grafico == "Histograma"),
    )

    col4, col5, col6 = st.columns(3)
    color_por = col4.selectbox("Colorear por", ["(ninguno)"] + VARS_CAT)
    paleta = col5.selectbox(
        "Paleta de color",
        ["Plotly", "Vivid", "Bold", "Pastel", "Set1", "Dark24"],
    )
    tema = col6.selectbox(
        "Tema del gráfico",
        ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white"],
    )

    col7, col8, col9 = st.columns(3)
    opacidad = col7.slider("Opacidad", 0.1, 1.0, 0.8)
    tamano_muestra = col8.slider("Tamaño de muestra a graficar", 100, len(df), min(2000, len(df)))
    mostrar_umbral = col9.checkbox("Mostrar línea de umbral (variable Y)", value=True)

    titulo_custom = st.text_input("Título de la gráfica", value=f"{var_y} vs {var_x}")

    df_plot = df.sample(min(tamano_muestra, len(df)), random_state=1)
    color_arg = None if color_por == "(ninguno)" else color_por
    paleta_map = {
        "Plotly": px.colors.qualitative.Plotly,
        "Vivid": px.colors.qualitative.Vivid,
        "Bold": px.colors.qualitative.Bold,
        "Pastel": px.colors.qualitative.Pastel,
        "Set1": px.colors.qualitative.Set1,
        "Dark24": px.colors.qualitative.Dark24,
    }
    color_seq = paleta_map[paleta]

    common_kwargs = dict(
        color=color_arg, color_discrete_sequence=color_seq,
        template=tema, opacity=opacidad, title=titulo_custom,
    )

    if tipo_grafico == "Dispersión":
        fig = px.scatter(df_plot, x=var_x, y=var_y, size="casos_confirmados",
                          hover_data=VARS_CAT, **common_kwargs)
    elif tipo_grafico == "Línea":
        df_line = df_plot.sort_values(var_x if var_x != "fecha" else "fecha")
        fig = px.line(df_line, x=var_x, y=var_y, **common_kwargs)
    elif tipo_grafico == "Barras":
        fig = px.bar(df_plot, x=var_x, y=var_y, **common_kwargs)
    elif tipo_grafico == "Boxplot":
        fig = px.box(df_plot, x=var_x if var_x in VARS_CAT else color_arg,
                     y=var_y, **common_kwargs)
    elif tipo_grafico == "Violin":
        fig = px.violin(df_plot, x=var_x if var_x in VARS_CAT else color_arg,
                         y=var_y, box=True, **common_kwargs)
    else:  # Histograma
        fig = px.histogram(df_plot, x=var_y, **common_kwargs)

    if mostrar_umbral and tipo_grafico not in ("Histograma",):
        umbral_ref = umbral_casos if var_y == "casos_confirmados" else (
            umbral_vacunacion if var_y == "tasa_vacunacion" else (
                umbral_uci if var_y == "ocupacion_uci" else df[var_y].mean()
            )
        )
        fig.add_hline(
            y=umbral_ref, line_dash="dash", line_color="red",
            annotation_text=f"Umbral: {umbral_ref}", annotation_position="top left",
        )

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**Serie temporal agregada**")
    freq = st.select_slider("Agregación temporal", options=["D", "W", "M"],
                             value="W", format_func=lambda x: {"D": "Diaria", "W": "Semanal", "M": "Mensual"}[x])
    var_serie = st.selectbox("Variable a agregar en el tiempo", VARS_NUM, key="serie_var")
    serie = df.set_index("fecha")[var_serie].resample(freq).sum().reset_index()
    fig_serie = px.area(serie, x="fecha", y=var_serie, template=tema,
                         title=f"Evolución temporal ({freq}) de {var_serie}")
    st.plotly_chart(fig_serie, use_container_width=True)

# ---------------- TAB: Datos crudos ----------------
with tab_datos:
    st.subheader("Vista de datos filtrados")
    st.dataframe(df.drop(columns=["sobre_umbral_casos", "uci_critica", "vacunacion_baja"]),
                 use_container_width=True, height=450)
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="covid_datos_sinteticos_filtrados.csv",
        mime="text/csv",
    )
    st.caption("Tipos de datos por columna:")
    st.dataframe(df_full.dtypes.astype(str).rename("tipo_de_dato"), use_container_width=True)
