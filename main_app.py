"""
Dashboard Messi vs Ronaldo — Datos reales
==========================================
Streamlit + Plotly. Estadisticas reales (no sinteticas) de Lionel Messi y
Cristiano Ronaldo, temporada a temporada desde su debut hasta la actualidad:
goles, asistencias, regates, titulos de equipo y premios individuales.

Fuentes: MessivsRonaldo.app, FBref, Wikipedia (paginas "career statistics"),
consultadas en julio de 2026. Cifras oficiales de partidos senior de club y
seleccion; excluyen amistosos de club y partidos juveniles salvo que se
indique lo contrario.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------
# Configuracion general
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Messi vs Ronaldo — Dashboard de Datos Reales",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCESS_CODE = "4004"

# ----------------------------------------------------------------------
# Control de acceso
# ----------------------------------------------------------------------
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.title("⚽ Messi vs Ronaldo — Dashboard")
    st.markdown("Este tablero esta protegido. Introduce la clave de acceso para continuar.")
    col1, _ = st.columns([1, 2])
    with col1:
        code_input = st.text_input("Clave de acceso", type="password")
        if st.button("Entrar", use_container_width=True):
            if code_input == ACCESS_CODE:
                st.session_state.unlocked = True
                st.rerun()
            else:
                st.error("Clave incorrecta. Intenta de nuevo.")
    st.stop()

# ----------------------------------------------------------------------
# Datos reales — temporada a temporada (club)
# Fuente: MessivsRonaldo.app (desglose por temporada), actualizado jul-2026
# ----------------------------------------------------------------------
SEASONS = [
    "2002/03", "2003/04", "2004/05", "2005/06", "2006/07", "2007/08",
    "2008/09", "2009/10", "2010/11", "2011/12", "2012/13", "2013/14",
    "2014/15", "2015/16", "2016/17", "2017/18", "2018/19", "2019/20",
    "2020/21", "2021/22", "2022/23", "2023/24", "2024/25", "2025/26",
]

messi_season = dict(
    goals_total=[0, 0, 1, 8, 17, 16, 38, 47, 53, 73, 60, 41, 58, 41, 54, 45, 51, 31, 38, 11, 21, 25, 33, 32],
    goals_league=[0, 0, 1, 6, 14, 10, 23, 34, 31, 50, 46, 28, 43, 26, 37, 34, 36, 25, 30, 6, 16, 13, 26, 23],
    goals_champions_league=[0, 0, 0, 1, 1, 6, 9, 8, 12, 14, 8, 8, 10, 6, 11, 6, 12, 3, 5, 5, 4, 0, 0, 0],
    goals_other_cups=[0, 0, 0, 1, 2, 0, 6, 5, 10, 9, 6, 5, 5, 6, 9, 5, 3, 3, 3, 0, 1, 12, 7, 9],
    assists_total=[0, 0, 0, 5, 4, 18, 19, 14, 29, 36, 18, 16, 33, 23, 24, 23, 24, 28, 18, 17, 21, 18, 9, 27],
    successful_dribbles=[0, 0, 6, 46, 121, 168, 143, 206, 265, 222, 143, 169, 266, 151, 154, 222, 169, 239, 188, 87, 116, 62, 98, 62],
)

ronaldo_season = dict(
    goals_total=[5, 6, 9, 12, 23, 42, 26, 33, 53, 60, 55, 51, 61, 51, 42, 44, 28, 37, 36, 24, 17, 50, 35, 30],
    goals_league=[3, 4, 5, 9, 17, 31, 18, 26, 40, 46, 34, 31, 48, 35, 25, 26, 21, 31, 29, 18, 15, 35, 25, 28],
    goals_champions_league=[0, 0, 0, 0, 3, 8, 4, 7, 6, 10, 12, 17, 10, 16, 12, 15, 6, 4, 4, 6, 0, 0, 0, 0],
    goals_other_cups=[2, 2, 4, 3, 3, 3, 4, 0, 7, 4, 9, 3, 3, 0, 5, 3, 1, 2, 3, 0, 2, 15, 10, 2],
    assists_total=[6, 9, 12, 9, 22, 9, 13, 13, 18, 15, 13, 17, 24, 15, 12, 8, 13, 9, 6, 3, 4, 17, 5, 6],
    successful_dribbles=[0, 72, 146, 133, 132, 126, 86, 105, 107, 102, 81, 92, 79, 60, 40, 53, 63, 67, 68, 30, 27, 17, 25, 16],
)

BIRTH_YEAR = {"Messi": 1987, "Ronaldo": 1985}
CLUB_BY_ERA = {
    "Messi": [(2002, "Barcelona"), (2021, "PSG"), (2023, "Inter Miami")],
    "Ronaldo": [(2002, "Sporting CP"), (2003, "Man Utd"), (2009, "Real Madrid"), (2018, "Juventus"), (2023, "Al-Nassr")],
}


def club_for(player, season_start_year):
    club = CLUB_BY_ERA[player][0][1]
    for start_year, name in CLUB_BY_ERA[player]:
        if season_start_year >= start_year:
            club = name
    return club


def build_season_df(player, data):
    rows = []
    for i, season in enumerate(SEASONS):
        start_year = int(season[:4])
        rows.append({
            "player": player,
            "season": season,
            "season_start_year": start_year,
            "age": start_year - BIRTH_YEAR[player],
            "club": club_for(player, start_year),
            "goals_total": data["goals_total"][i],
            "goals_league": data["goals_league"][i],
            "goals_champions_league": data["goals_champions_league"][i],
            "goals_other_cups": data["goals_other_cups"][i],
            "assists_total": data["assists_total"][i],
            "successful_dribbles": data["successful_dribbles"][i],
            "goal_contributions": data["goals_total"][i] + data["assists_total"][i],
        })
    return pd.DataFrame(rows)


@st.cache_data
def load_season_stats():
    df = pd.concat([
        build_season_df("Messi", messi_season),
        build_season_df("Ronaldo", ronaldo_season),
    ], ignore_index=True)
    return df


# ----------------------------------------------------------------------
# Datos reales — seleccion nacional, por ano calendario (2003-2026)
# ----------------------------------------------------------------------
INTL_YEARS = list(range(2003, 2027))

messi_intl_goals = [0, 0, 0, 2, 6, 2, 3, 2, 4, 12, 6, 8, 4, 8, 4, 4, 5, 1, 9, 18, 8, 6, 3, 10]
messi_intl_assists = [0, 0, 2, 2, 6, 3, 1, 4, 10, 1, 5, 3, 3, 6, 0, 3, 2, 0, 5, 6, 1, 5, 3, 2]
ronaldo_intl_goals = [0, 7, 2, 6, 5, 1, 1, 3, 7, 5, 10, 5, 3, 13, 11, 6, 14, 3, 13, 3, 10, 7, 8, 3]
ronaldo_intl_assists = [0, 8, 3, 2, 1, 3, 1, 7, 2, 3, 1, 3, 0, 3, 4, 1, 0, 1, 1, 3, 2, 2, 0, 0]


@st.cache_data
def load_international_stats():
    rows = []
    for i, year in enumerate(INTL_YEARS):
        rows.append({"player": "Messi", "year": year, "age": year - BIRTH_YEAR["Messi"],
                     "goals_international": messi_intl_goals[i], "assists_international": messi_intl_assists[i],
                     "team": "Argentina"})
        rows.append({"player": "Ronaldo", "year": year, "age": year - BIRTH_YEAR["Ronaldo"],
                     "goals_international": ronaldo_intl_goals[i], "assists_international": ronaldo_intl_assists[i],
                     "team": "Portugal"})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Datos reales — resumen de carrera (totales, hasta jul-2026)
# ----------------------------------------------------------------------
@st.cache_data
def load_career_totals():
    data = [
        dict(player="Messi", goals_club=794, assists_club=353, appearances_club=957, minutes_club=78653,
             goals_international=125, assists_international=73, career_goals_total=919,
             successful_dribbles_club=3636, shots_club=3763, shots_on_target_club=1746,
             key_passes_club=1813, big_chances_created_club=529, aerial_duels_won_club=144,
             hat_tricks_club=50, penalties_scored_club=89, free_kick_goals_club=60,
             ballon_dor_count=8, avg_match_rating_club=8.45, motm_club=401),
        dict(player="Ronaldo", goals_club=830, assists_club=224, appearances_club=1097, minutes_club=90229,
             goals_international=146, assists_international=51, career_goals_total=976,
             successful_dribbles_club=1817, shots_club=4664, shots_on_target_club=1890,
             key_passes_club=1155, big_chances_created_club=226, aerial_duels_won_club=943,
             hat_tricks_club=56, penalties_scored_club=161, free_kick_goals_club=54,
             ballon_dor_count=5, avg_match_rating_club=7.79, motm_club=205),
    ]
    return pd.DataFrame(data)


# ----------------------------------------------------------------------
# Datos reales — palmares de equipo (titulos)
# ----------------------------------------------------------------------
@st.cache_data
def load_trophies():
    rows = []

    def add(player, category, trophy, years, team):
        for y in years:
            rows.append({"player": player, "category": category, "trophy": trophy, "year": y, "team": team})

    # MESSI
    add("Messi", "Champions League", "UEFA Champions League", ["2014/15", "2010/11", "2008/09", "2005/06"], "Barcelona")
    add("Messi", "Liga", "MLS Supporters' Shield", ["2024"], "Inter Miami")
    add("Messi", "Liga", "Ligue 1", ["2022/23", "2021/22"], "PSG")
    add("Messi", "Liga", "La Liga", ["2018/19", "2017/18", "2015/16", "2014/15", "2012/13", "2010/11", "2009/10", "2008/09", "2005/06", "2004/05"], "Barcelona")
    add("Messi", "Copa Nacional", "MLS Cup", ["2025"], "Inter Miami")
    add("Messi", "Copa Nacional", "Copa del Rey", ["2020/21", "2017/18", "2016/17", "2015/16", "2014/15", "2011/12", "2008/09"], "Barcelona")
    add("Messi", "Supercopa Nacional", "Trophee des Champions", ["2022"], "PSG")
    add("Messi", "Supercopa Nacional", "Supercopa de Espana", ["2018", "2016", "2013", "2011", "2010", "2009", "2006", "2005"], "Barcelona")
    add("Messi", "UEFA Super Cup", "UEFA Super Cup", ["2015", "2011", "2009"], "Barcelona")
    add("Messi", "Mundial de Clubes", "FIFA Club World Cup", ["2015", "2011", "2009"], "Barcelona")
    add("Messi", "Otros Club", "Eastern Conference Champions", ["2025"], "Inter Miami")
    add("Messi", "Otros Club", "Leagues Cup", ["2023"], "Inter Miami")
    add("Messi", "Seleccion", "Copa America", ["2024", "2021"], "Argentina")
    add("Messi", "Seleccion", "FIFA World Cup", ["2022"], "Argentina")
    add("Messi", "Seleccion", "Finalissima", ["2022"], "Argentina")
    add("Messi", "Seleccion", "Juegos Olimpicos (oro U23)", ["2008"], "Argentina")
    add("Messi", "Seleccion", "FIFA U20 World Cup", ["2005"], "Argentina")

    # RONALDO
    add("Ronaldo", "Champions League", "UEFA Champions League", ["2017/18", "2016/17", "2015/16", "2013/14"], "Real Madrid")
    add("Ronaldo", "Champions League", "UEFA Champions League", ["2007/08"], "Man Utd")
    add("Ronaldo", "Liga", "Saudi Pro League", ["2025/26"], "Al-Nassr")
    add("Ronaldo", "Liga", "Serie A", ["2019/20", "2018/19"], "Juventus")
    add("Ronaldo", "Liga", "La Liga", ["2016/17", "2011/12"], "Real Madrid")
    add("Ronaldo", "Liga", "Premier League", ["2008/09", "2007/08", "2006/07"], "Man Utd")
    add("Ronaldo", "Copa Nacional", "Coppa Italia", ["2020/21"], "Juventus")
    add("Ronaldo", "Copa Nacional", "Copa del Rey", ["2013/14", "2010/11"], "Real Madrid")
    add("Ronaldo", "Copa Nacional", "English League Cup", ["2008/09", "2005/06"], "Man Utd")
    add("Ronaldo", "Copa Nacional", "FA Cup", ["2003/04"], "Man Utd")
    add("Ronaldo", "Supercopa Nacional", "Supercoppa Italiana", ["2021", "2019"], "Juventus")
    add("Ronaldo", "Supercopa Nacional", "Supercopa de Espana", ["2017", "2012"], "Real Madrid")
    add("Ronaldo", "Supercopa Nacional", "Community Shield", ["2007"], "Man Utd")
    add("Ronaldo", "UEFA Super Cup", "UEFA Super Cup", ["2017", "2014"], "Real Madrid")
    add("Ronaldo", "Mundial de Clubes", "FIFA Club World Cup", ["2017", "2016", "2014"], "Real Madrid")
    add("Ronaldo", "Mundial de Clubes", "FIFA Club World Cup", ["2008"], "Man Utd")
    add("Ronaldo", "Otros Club", "Arab Club Champions Cup", ["2023"], "Al-Nassr")
    add("Ronaldo", "Seleccion", "UEFA Nations League", ["2024/25", "2018/19"], "Portugal")
    add("Ronaldo", "Seleccion", "UEFA European Championship", ["2016"], "Portugal")

    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Datos reales — premios individuales
# ----------------------------------------------------------------------
@st.cache_data
def load_individual_awards():
    rows = []

    def add(player, award, years, detail=""):
        for y in years:
            rows.append({"player": player, "award": award, "year": y, "detail": detail})

    add("Messi", "Balon de Oro", ["2023", "2021", "2019", "2015", "2012", "2011", "2010", "2009"])
    add("Ronaldo", "Balon de Oro", ["2017", "2016", "2014", "2013", "2008"])

    add("Messi", "FIFA The Best / FIFA World Player", ["2023", "2022", "2019"])
    add("Ronaldo", "FIFA The Best / FIFA World Player", ["2017", "2016"])

    add("Messi", "Bota de Oro Europea", ["2018/19", "2017/18", "2016/17", "2012/13", "2011/12", "2009/10"])
    add("Ronaldo", "Bota de Oro Europea", ["2014/15", "2013/14", "2010/11", "2007/08"])

    add("Messi", "Maximo goleador Champions League", ["2018/19", "2014/15", "2011/12", "2010/11", "2009/10", "2008/09"])
    add("Ronaldo", "Maximo goleador Champions League", ["2017/18", "2016/17", "2015/16", "2014/15", "2013/14", "2012/13", "2007/08"])

    add("Messi", "Pichichi La Liga", ["2020/21", "2019/20", "2018/19", "2017/18", "2016/17", "2012/13", "2011/12", "2009/10"])
    add("Ronaldo", "Pichichi La Liga", ["2014/15", "2013/14", "2010/11"])

    add("Messi", "Balon de Oro Mundial (World Cup)", ["2022", "2014"])
    add("Messi", "Bota de Plata Mundial (World Cup)", ["2022"])
    add("Messi", "Balon de Oro Copa America", ["2021", "2015"])
    add("Ronaldo", "Bota de Oro Eurocopa", ["2021"])
    add("Ronaldo", "Maximo goleador Premier League", ["2007/08"])
    add("Ronaldo", "Maximo goleador Serie A", ["2020/21"])
    add("Ronaldo", "Maximo goleador Saudi Pro League", ["2024/25", "2023/24"])
    add("Messi", "Maximo goleador MLS", ["2025"])

    return pd.DataFrame(rows)


season_stats = load_season_stats()
international_stats = load_international_stats()
career_totals = load_career_totals()
trophies = load_trophies()
individual_awards = load_individual_awards()

# ----------------------------------------------------------------------
# Sidebar — filtros
# ----------------------------------------------------------------------
st.sidebar.title("⚙️ Panel de control")
st.sidebar.caption("Datos reales (no simulados) · Fuente: MessivsRonaldo.app, FBref, Wikipedia · actualizado jul-2026")

players_sel = st.sidebar.multiselect("Jugadores", ["Messi", "Ronaldo"], default=["Messi", "Ronaldo"])
season_range = st.sidebar.select_slider(
    "Rango de temporadas (club)",
    options=SEASONS,
    value=(SEASONS[0], SEASONS[-1]),
)

st.sidebar.divider()
st.sidebar.subheader("Umbrales de rendimiento")
umbral_goles = st.sidebar.slider("Umbral de goles por temporada", 0, 80, 40)
umbral_regates = st.sidebar.slider("Umbral de regates exitosos por temporada", 0, 300, 150)

if not players_sel:
    st.warning("Selecciona al menos un jugador en la barra lateral.")
    st.stop()

i_start, i_end = SEASONS.index(season_range[0]), SEASONS.index(season_range[1])
seasons_filtered = SEASONS[i_start:i_end + 1]

df_season = season_stats[
    season_stats["player"].isin(players_sel) & season_stats["season"].isin(seasons_filtered)
].copy()
df_season["sobre_umbral_goles"] = df_season["goals_total"] > umbral_goles
df_season["sobre_umbral_regates"] = df_season["successful_dribbles"] > umbral_regates

df_intl = international_stats[international_stats["player"].isin(players_sel)].copy()
df_trophies = trophies[trophies["player"].isin(players_sel)].copy()
df_awards = individual_awards[individual_awards["player"].isin(players_sel)].copy()
df_totals = career_totals[career_totals["player"].isin(players_sel)].copy()

# ----------------------------------------------------------------------
# Encabezado + KPIs
# ----------------------------------------------------------------------
st.title("⚽ Messi vs Ronaldo — Dashboard de Datos Reales")
st.caption(
    "Estadisticas reales de partidos oficiales de club y seleccion, desde el debut de cada "
    "jugador hasta julio de 2026. No son datos simulados."
)

cols = st.columns(len(players_sel) * 3 if players_sel else 3)
idx = 0
for p in players_sel:
    row = df_totals[df_totals["player"] == p].iloc[0]
    cols[idx].metric(f"{p} — Goles totales", f"{int(row['career_goals_total']):,}")
    cols[idx + 1].metric(f"{p} — Asistencias (club)", f"{int(row['assists_club']):,}")
    cols[idx + 2].metric(f"{p} — Balones de Oro", f"{int(row['ballon_dor_count'])}")
    idx += 3

st.divider()

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_resumen, tab_temporadas, tab_seleccion, tab_palmares, tab_premios, tab_viz, tab_datos = st.tabs([
    "📊 Resumen de carrera", "📈 Progresion por temporada", "🌎 Seleccion nacional",
    "🏆 Palmares (equipo)", "🥇 Premios individuales", "🎨 Graficas dinamicas", "📄 Datos crudos",
])

METRIC_LABELS = {
    "goals_total": "Goles (club, total)",
    "goals_league": "Goles en liga",
    "goals_champions_league": "Goles en Champions League",
    "goals_other_cups": "Goles en otras copas",
    "assists_total": "Asistencias (club, total)",
    "successful_dribbles": "Regates exitosos (liga + Champions)",
    "goal_contributions": "Goles + asistencias (club)",
}

# ---------------- TAB: Resumen de carrera ----------------
with tab_resumen:
    st.subheader("Estadistica cuantitativa — totales de carrera (hasta jul-2026)")
    st.dataframe(df_totals.set_index("player").T, use_container_width=True)

    metric_cols = ["goals_club", "assists_club", "successful_dribbles_club", "hat_tricks_club",
                    "free_kick_goals_club", "penalties_scored_club", "big_chances_created_club",
                    "key_passes_club", "motm_club"]
    metric_bar = st.selectbox("Metrica a comparar", metric_cols, index=0, key="resumen_metric")
    fig_bar = px.bar(
        df_totals, x="player", y=metric_bar, color="player",
        text=metric_bar, title=f"Comparacion: {metric_bar.replace('_', ' ')}",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("**Perfil comparativo (radar normalizado 0-100)**")
    radar_cols = ["goals_club", "assists_club", "successful_dribbles_club", "aerial_duels_won_club",
                  "key_passes_club", "big_chances_created_club"]
    radar_df = career_totals.set_index("player")[radar_cols]
    radar_norm = (radar_df / radar_df.max()) * 100
    fig_radar = go.Figure()
    for p in players_sel:
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_norm.loc[p].values, theta=[c.replace("_club", "").replace("_", " ") for c in radar_cols],
            fill="toself", name=p,
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Perfil de impacto en el juego (normalizado)")
    st.plotly_chart(fig_radar, use_container_width=True)

# ---------------- TAB: Progresion por temporada ----------------
with tab_temporadas:
    st.subheader("Progresion temporada a temporada (club)")

    metric_sel = st.selectbox("Variable", list(METRIC_LABELS.keys()), format_func=lambda k: METRIC_LABELS[k], key="temp_metric")
    fig_line = px.line(
        df_season, x="season", y=metric_sel, color="player", markers=True,
        title=f"{METRIC_LABELS[metric_sel]} por temporada",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
        hover_data=["club", "age"],
    )
    if metric_sel == "goals_total":
        fig_line.add_hline(y=umbral_goles, line_dash="dash", line_color="gray",
                            annotation_text=f"Umbral: {umbral_goles} goles")
    if metric_sel == "successful_dribbles":
        fig_line.add_hline(y=umbral_regates, line_dash="dash", line_color="gray",
                            annotation_text=f"Umbral: {umbral_regates} regates")
    fig_line.update_layout(height=550)
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("**Descomposicion de goles por competicion**")
    comp_df = df_season.melt(
        id_vars=["player", "season"],
        value_vars=["goals_league", "goals_champions_league", "goals_other_cups"],
        var_name="competicion", value_name="goles",
    )
    comp_df["competicion"] = comp_df["competicion"].map({
        "goals_league": "Liga", "goals_champions_league": "Champions League", "goals_other_cups": "Otras copas",
    })
    player_for_stack = st.radio("Jugador para el desglose", players_sel, horizontal=True, key="stack_player")
    fig_stack = px.bar(
        comp_df[comp_df["player"] == player_for_stack], x="season", y="goles", color="competicion",
        title=f"Goles de {player_for_stack} por competicion y temporada", barmode="stack",
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    st.markdown("**Temporadas que superan los umbrales fijados**")
    tabla_umbral = df_season[df_season["sobre_umbral_goles"] | df_season["sobre_umbral_regates"]][
        ["player", "season", "club", "goals_total", "successful_dribbles", "sobre_umbral_goles", "sobre_umbral_regates"]
    ]
    st.dataframe(tabla_umbral, use_container_width=True, hide_index=True)

# ---------------- TAB: Seleccion nacional ----------------
with tab_seleccion:
    st.subheader("Estadistica cualitativa y cuantitativa — seleccion nacional (por ano calendario)")
    fig_intl = px.bar(
        df_intl, x="year", y="goals_international", color="player", barmode="group",
        title="Goles con la seleccion por ano",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
        hover_data=["team", "age"],
    )
    st.plotly_chart(fig_intl, use_container_width=True)

    resumen_intl = df_intl.groupby("player")[["goals_international", "assists_international"]].sum().reset_index()
    st.dataframe(resumen_intl, use_container_width=True, hide_index=True)

    fig_intl_scatter = px.scatter(
        df_intl, x="goals_international", y="assists_international", color="player", size="age",
        hover_data=["year", "team"], title="Goles vs asistencias con la seleccion, por ano",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
    )
    st.plotly_chart(fig_intl_scatter, use_container_width=True)

# ---------------- TAB: Palmares ----------------
with tab_palmares:
    st.subheader("Estadistica cualitativa — titulos de equipo")
    conteo_trofeos = df_trophies.groupby(["player", "category"]).size().reset_index(name="cantidad")
    fig_troph = px.bar(
        conteo_trofeos, x="category", y="cantidad", color="player", barmode="group",
        title="Titulos de equipo por categoria",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
    )
    st.plotly_chart(fig_troph, use_container_width=True)

    totales_trofeos = df_trophies.groupby("player").size().reset_index(name="total_titulos")
    st.dataframe(totales_trofeos, use_container_width=True, hide_index=True)

    categoria_sel = st.selectbox("Filtrar por categoria", ["(todas)"] + sorted(df_trophies["category"].unique()))
    tabla_trofeos = df_trophies if categoria_sel == "(todas)" else df_trophies[df_trophies["category"] == categoria_sel]
    st.dataframe(tabla_trofeos.sort_values(["player", "year"]), use_container_width=True, hide_index=True, height=350)

# ---------------- TAB: Premios individuales ----------------
with tab_premios:
    st.subheader("Estadistica cualitativa — premios y distinciones individuales")
    conteo_premios = df_awards.groupby(["player", "award"]).size().reset_index(name="veces")
    fig_awards = px.bar(
        conteo_premios, x="award", y="veces", color="player", barmode="group",
        title="Premios individuales ganados",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
    )
    fig_awards.update_layout(xaxis_tickangle=-40, height=550)
    st.plotly_chart(fig_awards, use_container_width=True)

    st.markdown("**Linea de tiempo de premios**")
    award_choice = st.selectbox("Premio", sorted(df_awards["award"].unique()))
    linea_df = df_awards[df_awards["award"] == award_choice].sort_values("year")
    fig_timeline = px.scatter(
        linea_df, x="year", y="player", color="player", size=[10] * len(linea_df),
        title=f"Anos en los que se gano: {award_choice}",
        color_discrete_map={"Messi": "#75AADB", "Ronaldo": "#C8102E"},
    )
    fig_timeline.update_yaxes(title="")
    st.plotly_chart(fig_timeline, use_container_width=True)

# ---------------- TAB: Graficas dinamicas ----------------
with tab_viz:
    st.subheader("Constructor de graficas dinamicas")
    st.caption("Elige el dataset, las variables y el estilo de la grafica.")

    dataset_choice = st.selectbox("Fuente de datos", ["Temporadas (club)", "Seleccion nacional (anual)"])

    if dataset_choice == "Temporadas (club)":
        base_df = df_season
        num_vars = list(METRIC_LABELS.keys())
        x_default = "season"
        cat_vars = ["player", "club"]
    else:
        base_df = df_intl
        num_vars = ["goals_international", "assists_international"]
        x_default = "year"
        cat_vars = ["player", "team"]

    col1, col2, col3 = st.columns(3)
    tipo_grafico = col1.selectbox("Tipo de grafica", ["Linea", "Barras", "Dispersion", "Boxplot", "Violin", "Area"])
    var_x = col2.selectbox("Variable X", [x_default, "age"] if "age" in base_df.columns else [x_default])
    var_y = col3.selectbox("Variable Y", num_vars)

    col4, col5, col6 = st.columns(3)
    color_por = col4.selectbox("Colorear por", cat_vars)
    paleta = col5.selectbox("Paleta", ["Plotly", "Vivid", "Bold", "Set1", "Pastel"])
    tema = col6.selectbox("Tema", ["plotly_white", "plotly", "plotly_dark", "ggplot2", "seaborn", "simple_white"])

    col7, col8 = st.columns(2)
    opacidad = col7.slider("Opacidad", 0.2, 1.0, 0.85)
    mostrar_umbral_din = col8.checkbox("Mostrar linea de umbral de goles", value=(var_y == "goals_total"))

    titulo_custom = st.text_input("Titulo de la grafica", value=f"{var_y} vs {var_x}")

    paleta_map = {
        "Plotly": px.colors.qualitative.Plotly, "Vivid": px.colors.qualitative.Vivid,
        "Bold": px.colors.qualitative.Bold, "Set1": px.colors.qualitative.Set1,
        "Pastel": px.colors.qualitative.Pastel,
    }
    common = dict(color=color_por, color_discrete_sequence=paleta_map[paleta], template=tema,
                  opacity=opacidad, title=titulo_custom)

    if tipo_grafico == "Linea":
        fig = px.line(base_df, x=var_x, y=var_y, markers=True, **common)
    elif tipo_grafico == "Barras":
        fig = px.bar(base_df, x=var_x, y=var_y, barmode="group", **common)
    elif tipo_grafico == "Dispersion":
        fig = px.scatter(base_df, x=var_x, y=var_y, size=var_y, **common)
    elif tipo_grafico == "Boxplot":
        fig = px.box(base_df, x=color_por, y=var_y, **common)
    elif tipo_grafico == "Violin":
        fig = px.violin(base_df, x=color_por, y=var_y, box=True, **common)
    else:
        fig = px.area(base_df, x=var_x, y=var_y, **common)

    if mostrar_umbral_din and var_y == "goals_total":
        fig.add_hline(y=umbral_goles, line_dash="dash", line_color="red",
                       annotation_text=f"Umbral: {umbral_goles}")

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB: Datos crudos ----------------
with tab_datos:
    st.subheader("Tablas de datos reales")
    st.caption(f"Temporadas (club): {len(season_stats)} filas — Seleccion: {len(international_stats)} filas — "
               f"Titulos: {len(trophies)} filas — Premios: {len(individual_awards)} filas — todas por debajo del "
               "limite de 10,000 registros y 20 columnas.")

    dataset_view = st.selectbox("Elige la tabla a mostrar", [
        "Resumen de carrera", "Temporadas (club)", "Seleccion nacional", "Titulos (palmares)", "Premios individuales",
    ])
    view_map = {
        "Resumen de carrera": df_totals, "Temporadas (club)": df_season, "Seleccion nacional": df_intl,
        "Titulos (palmares)": df_trophies, "Premios individuales": df_awards,
    }
    tabla_actual = view_map[dataset_view]
    st.dataframe(tabla_actual, use_container_width=True, height=420)
    st.download_button(
        f"⬇️ Descargar '{dataset_view}' en CSV",
        data=tabla_actual.to_csv(index=False).encode("utf-8"),
        file_name=f"{dataset_view.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )
    st.caption("Tipos de datos por columna (tabla seleccionada):")
    st.dataframe(tabla_actual.dtypes.astype(str).rename("tipo_de_dato"), use_container_width=True)
