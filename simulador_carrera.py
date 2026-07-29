"""
⚽ Simulador de Carrera Futbolística
Dashboard dinámico en Streamlit inspirado en el "simulador de carrera" de Copero.
Creá un jugador, tomá decisiones cada temporada y viví las consecuencias.
"""

import random
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIGURACIÓN Y DATOS BASE
# ----------------------------------------------------------------------------

ATTRS = ["ritmo", "tiro", "pase", "regate", "defensa", "fisico"]
ATTR_LABELS = {
    "ritmo": "Ritmo",
    "tiro": "Tiro",
    "pase": "Pase",
    "regate": "Regate",
    "defensa": "Defensa",
    "fisico": "Físico",
}

POSITIONS = ["Portero", "Defensa", "Mediocampista", "Delantero"]
POSITION_ICON = {"Portero": "🧤", "Defensa": "🛡️", "Mediocampista": "🎯", "Delantero": "⚡"}

POSITION_WEIGHTS = {
    "Portero":        {"ritmo": 0.05, "tiro": 0.00, "pase": 0.15, "regate": 0.05, "defensa": 0.55, "fisico": 0.20},
    "Defensa":        {"ritmo": 0.15, "tiro": 0.05, "pase": 0.15, "regate": 0.10, "defensa": 0.40, "fisico": 0.15},
    "Mediocampista":  {"ritmo": 0.15, "tiro": 0.15, "pase": 0.30, "regate": 0.20, "defensa": 0.10, "fisico": 0.10},
    "Delantero":      {"ritmo": 0.20, "tiro": 0.35, "pase": 0.10, "regate": 0.25, "defensa": 0.00, "fisico": 0.10},
}

GOAL_RATE = {"Delantero": 0.55, "Mediocampista": 0.22, "Defensa": 0.07, "Portero": 0.0}
ASSIST_RATE = {"Delantero": 0.25, "Mediocampista": 0.35, "Defensa": 0.12, "Portero": 0.01}

TALENT_TIERS = {
    "Cantera humilde 🌱": {"base": (35, 50), "potential": (55, 72)},
    "Promesa prometedora ⭐": {"base": (45, 60), "potential": (70, 85)},
    "Prodigio 🌟": {"base": (55, 68), "potential": (85, 97)},
}

CLUB_TIERS = {1: "Liga Regional", 2: "Segunda División", 3: "Primera División", 4: "Liga Élite Europea"}
CLUB_NAMES = {
    1: ["Deportivo Barrio Norte", "Unión Juvenil", "Atlético Cantera", "Social y Deportivo Sur"],
    2: ["Club Atlético Progreso", "Deportivo Central", "Racing del Valle", "Independiente Andino"],
    3: ["Real Nacional", "Atlético Metropolitano", "Deportivo Capital", "Club Campeón"],
    4: ["FC Estrella Continental", "Real Imperio", "Atlético Galáctico", "Unión Europa FC"],
}
COUNTRIES = ["Colombia", "Argentina", "Brasil", "España", "México", "Chile", "Uruguay", "Alemania"]

DILEMMAS = [
    {"title": "🎉 Fiesta de fin de año",
     "text": "Tus compañeros festejan el título de la ciudad y te invitan. Mañana hay doble turno de entrenamiento.",
     "options": [
         {"label": "Ir a la fiesta y socializar", "effects": {"morale": 8, "injury_risk": 0.03, "form": -2}},
         {"label": "Quedarte a descansar", "effects": {"morale": -2, "form": 3}},
     ]},
    {"title": "📰 Rumores de prensa",
     "text": "Un periodista publica que estás en la mira de un club más grande.",
     "options": [
         {"label": "Confirmar tu ambición en una entrevista", "effects": {"reputation": 5, "morale": -2}},
         {"label": "Mantener bajo perfil", "effects": {"reputation": 1, "morale": 2}},
     ]},
    {"title": "⚔️ Conflicto con el entrenador",
     "text": "El DT te deja en el banco de suplentes sin dar explicaciones claras.",
     "options": [
         {"label": "Hablar con calma y pedir explicaciones", "effects": {"morale": 3, "reputation": 1}},
         {"label": "Reclamar públicamente", "effects": {"morale": -4, "reputation": 3}},
     ]},
    {"title": "💪 Entrenamiento extra",
     "text": "El preparador físico te ofrece sesiones extra fuera de horario.",
     "options": [
         {"label": "Aceptar el esfuerzo extra", "effects": {"injury_risk": 0.05, "one_attr": ("fisico", 2)}},
         {"label": "Rechazar y priorizar el descanso", "effects": {"form": 2}},
     ]},
    {"title": "🤝 Propuesta de patrocinador",
     "text": "Una marca deportiva te ofrece ser imagen de campaña a cambio de exposición mediática.",
     "options": [
         {"label": "Aceptar el contrato", "effects": {"reputation": 4, "morale": 2}},
         {"label": "Declinar para enfocarte en lo deportivo", "effects": {"form": 2}},
     ]},
    {"title": "🩹 Molestia física leve",
     "text": "Sentís una molestia muscular tras el último entrenamiento.",
     "options": [
         {"label": "Jugar igual, el equipo te necesita", "effects": {"injury_risk": 0.08, "morale": 3}},
         {"label": "Pedir descanso preventivo", "effects": {"injury_risk": -0.05, "morale": -1}},
     ]},
    {"title": "🎓 Charla del capitán",
     "text": "El capitán del equipo te da consejos sobre liderazgo y constancia.",
     "options": [
         {"label": "Tomarlo como impulso", "effects": {"morale": 6, "form": 2}},
         {"label": "Escuchar sin darle mucha importancia", "effects": {"morale": 1}},
     ]},
    {"title": "🌍 Convocatoria juvenil",
     "text": "Te llaman a un microciclo de la selección juvenil.",
     "options": [
         {"label": "Asistir con orgullo", "effects": {"reputation": 5, "injury_risk": 0.02}},
         {"label": "Pedir postergarlo por carga física", "effects": {"morale": -1, "reputation": -1}},
     ]},
]

CUSTOM_CSS = """
<style>
[data-testid="stMetricValue"] { font-size: 1.6rem; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background-color: rgba(255,255,255,0.05);
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
}
</style>
"""


# ----------------------------------------------------------------------------
# LÓGICA DEL JUEGO
# ----------------------------------------------------------------------------

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def generate_attributes(rango):
    lo, hi = rango
    return {a: random.randint(lo, hi) for a in ATTRS}


def generate_potential(rango, base_attrs):
    lo, hi = rango
    return {a: max(base_attrs[a], random.randint(lo, hi)) for a in ATTRS}


def compute_overall(attrs, position):
    w = POSITION_WEIGHTS[position]
    return round(sum(attrs[a] * w[a] for a in ATTRS))


def compute_market_value(player):
    ov = player["overall"]
    age = player["age"]
    rep = player["reputation"]
    peak = 27
    age_factor = max(0.35, 1 - abs(age - peak) * 0.045)
    tier_factor = {1: 0.3, 2: 0.6, 3: 1.0, 4: 1.9}[player["club_tier"]]
    value = (ov ** 2.6) * 45 * age_factor * tier_factor * (1 + rep / 200)
    return int(value)


def format_value(v):
    if v >= 1_000_000:
        return f"€{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"€{v / 1_000:.0f}K"
    return f"€{v}"


def create_player(name, position, country, talent, age):
    tier = TALENT_TIERS[talent]
    base_attrs = generate_attributes(tier["base"])
    potential = generate_potential(tier["potential"], base_attrs)
    overall = compute_overall(base_attrs, position)
    player = {
        "name": name.strip() or "Jugador Nuevo",
        "position": position,
        "country": country,
        "age": age,
        "attributes": base_attrs,
        "potential": potential,
        "overall": overall,
        "morale": random.randint(55, 75),
        "form": random.randint(55, 75),
        "reputation": random.randint(5, 20),
        "club_tier": 1,
        "club_name": random.choice(CLUB_NAMES[1]),
        "injury_weeks": 0,
        "caps": 0,
        "games_total": 0,
        "goals_total": 0,
        "assists_total": 0,
    }
    player["market_value"] = compute_market_value(player)

    st.session_state.player = player
    st.session_state.started = True
    st.session_state.season = 1
    st.session_state.stage = "training"
    st.session_state.history = []
    st.session_state.news = [f"{player['name']} debuta en {player['club_name']} ({CLUB_TIERS[1]})."]
    st.session_state.trophies = []
    st.session_state.game_over = False
    st.session_state.injury_risk_delta = 0.0
    st.rerun()


def apply_effects(player, effects):
    if "morale" in effects:
        player["morale"] = clamp(player["morale"] + effects["morale"], 0, 100)
    if "reputation" in effects:
        player["reputation"] = clamp(player["reputation"] + effects["reputation"], 0, 100)
    if "form" in effects:
        player["form"] = clamp(player["form"] + effects["form"], 0, 100)
    if "injury_risk" in effects:
        st.session_state.injury_risk_delta = st.session_state.get("injury_risk_delta", 0.0) + effects["injury_risk"]
    if "one_attr" in effects:
        attr, delta = effects["one_attr"]
        pot = player["potential"][attr]
        player["attributes"][attr] = clamp(player["attributes"][attr] + delta, 20, pot)
        player["overall"] = compute_overall(player["attributes"], player["position"])


def apply_growth(player, training_focus):
    age = player["age"]
    for attr in ATTRS:
        current = player["attributes"][attr]
        pot = player["potential"][attr]
        if age <= 21:
            base = random.randint(1, 3)
        elif age <= 25:
            base = random.randint(0, 2)
        elif age <= 29:
            base = random.randint(-1, 1)
        elif age <= 33:
            base = random.randint(-2, 0)
        else:
            base = random.randint(-4, -1)
        if attr == training_focus:
            base += random.randint(2, 4)
        new_val = current + base
        if base > 0:
            new_val = min(new_val, pot)
        player["attributes"][attr] = clamp(new_val, 20, 99)
    player["overall"] = compute_overall(player["attributes"], player["position"])


def simulate_season(player, training_focus):
    season = st.session_state.season
    matches_available = 38
    leftover_injury = player.get("injury_weeks", 0)
    matches_available = clamp(matches_available - round(leftover_injury * 1.2), 5, 38)

    injury_risk_delta = st.session_state.get("injury_risk_delta", 0.0)
    st.session_state.injury_risk_delta = 0.0
    injury_chance = clamp(0.15 - player["attributes"]["fisico"] / 100 * 0.10 + injury_risk_delta, 0.02, 0.4)

    new_injury_weeks = 0
    if random.random() < injury_chance:
        new_injury_weeks = random.randint(2, 12)
        matches_available = clamp(matches_available - round(new_injury_weeks * 1.1), 3, 38)

    matches_played = clamp(matches_available - random.randint(0, 3), 0, 38)

    form_factor = player["form"] / 100
    overall_factor = player["overall"] / 100
    pos = player["position"]

    goals_exp = (matches_played * GOAL_RATE[pos] * (0.4 + 0.6 * overall_factor)
                 * (0.6 + 0.4 * form_factor) * (player["attributes"]["tiro"] / 100))
    assists_exp = (matches_played * ASSIST_RATE[pos] * (0.4 + 0.6 * overall_factor)
                   * (player["attributes"]["pase"] / 100))

    goals = int(np.random.poisson(max(goals_exp, 0.01)))
    assists = int(np.random.poisson(max(assists_exp, 0.01)))

    avg_rating = round(clamp(5.7 + (player["overall"] - 50) / 50 * 2.3
                              + (player["form"] - 50) / 120 + random.uniform(-0.35, 0.35), 3.5, 10.0), 2)

    player["games_total"] += matches_played
    player["goals_total"] += goals
    player["assists_total"] += assists

    form_delta = round((avg_rating - 6.5) * 5 + random.randint(-4, 4))
    player["form"] = clamp(player["form"] + form_delta, 10, 100)
    player["morale"] = clamp(player["morale"] + random.randint(-6, 6), 10, 100)

    rep_gain = round(goals * 0.7 + assists * 0.35 + (player["overall"] - 60) * 0.15)
    player["reputation"] = clamp(player["reputation"] + rep_gain, 0, 100)

    apply_growth(player, training_focus)

    called_up = False
    if player["overall"] >= 74 and player["age"] < 33 and random.random() < 0.3:
        called_up = True
        player["caps"] += random.randint(1, 5)
        player["reputation"] = clamp(player["reputation"] + 4, 0, 100)

    trophy = None
    trophy_prob = {1: 0.05, 2: 0.08, 3: 0.13, 4: 0.20}[player["club_tier"]] + max(0, player["overall"] - 70) * 0.002
    if random.random() < min(trophy_prob, 0.4):
        trophy_name = random.choice(["Liga Nacional", "Copa Nacional", "Copa Continental", "Supercopa"])
        trophy = f"{trophy_name} con {player['club_name']}"
        st.session_state.trophies.append({"season": season, "title": trophy})

    transfer_happened = False
    threshold = 50 + player["club_tier"] * 9
    if player["club_tier"] < 4 and player["overall"] >= threshold and random.random() < 0.28:
        player["club_tier"] += 1
        player["club_name"] = random.choice(CLUB_NAMES[player["club_tier"]])
        transfer_happened = True

    player["injury_weeks"] = new_injury_weeks
    player["age"] += 1
    player["market_value"] = compute_market_value(player)

    record = {
        "season": season, "age": player["age"] - 1, "club": player["club_name"],
        "division": CLUB_TIERS[player["club_tier"]], "matches": matches_played,
        "goals": goals, "assists": assists, "avg_rating": avg_rating,
        "overall": player["overall"], "market_value": player["market_value"],
    }
    st.session_state.history.append(record)

    news_bits = [f"Temporada {season}: {matches_played} partidos, {goals} goles, {assists} asistencias (rating {avg_rating})."]
    if trophy:
        news_bits.append(f"🏆 ¡{player['name']} ganó {trophy}!")
    if called_up:
        news_bits.append(f"🌍 Convocatoria a la selección de {player['country']}.")
    if transfer_happened:
        news_bits.append(f"🔁 Transferencia: ahora juega en {player['club_name']} ({CLUB_TIERS[player['club_tier']]}).")
    if new_injury_weeks > 0:
        news_bits.append(f"🩹 Lesión de {new_injury_weeks} semanas.")
    for nb in news_bits:
        st.session_state.news.insert(0, nb)

    return {
        "matches": matches_played, "goals": goals, "assists": assists, "avg_rating": avg_rating,
        "trophy": trophy, "called_up": called_up, "transfer": transfer_happened,
        "injury_weeks": new_injury_weeks,
    }


def advance_to_next_season():
    st.session_state.season += 1
    st.session_state.stage = "training"
    if st.session_state.player["age"] >= 40:
        st.session_state.game_over = True
    st.rerun()


def auto_simulate(n):
    for _ in range(n):
        if st.session_state.get("game_over"):
            break
        player = st.session_state.player
        focus = random.choice(ATTRS)
        st.session_state.training_focus = focus
        dilemma = random.choice(DILEMMAS)
        opt = random.choice(dilemma["options"])
        apply_effects(player, opt["effects"])
        st.session_state.news.insert(0, f"Temporada {st.session_state.season}: {dilemma['title']} → {opt['label']} (auto)")
        result = simulate_season(player, focus)
        st.session_state.last_result = result
        st.session_state.stage = "summary"
        if player["age"] >= 40:
            st.session_state.game_over = True
            break
        st.session_state.season += 1
        st.session_state.stage = "training"
    st.rerun()


def reset_career():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ----------------------------------------------------------------------------
# COMPONENTES DE UI
# ----------------------------------------------------------------------------

def radar_chart(player):
    categories = [ATTR_LABELS[a] for a in ATTRS]
    values = [player["attributes"][a] for a in ATTRS]
    potentials = [player["potential"][a] for a in ATTRS]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]],
        fill="toself", name="Actual", line_color="#00d4ff"))
    fig.add_trace(go.Scatterpolar(
        r=potentials + [potentials[0]], theta=categories + [categories[0]],
        name="Potencial", line=dict(color="#ff5f5f", dash="dot")))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, template="plotly_dark", height=400,
        margin=dict(l=30, r=30, t=30, b=30))
    return fig


def render_creation_screen():
    st.title("⚽ Simulador de Carrera Futbolística")
    st.caption("Creá tu jugador y viví su carrera, temporada a temporada: decisiones, lesiones, "
               "convocatorias, trofeos y transferencias.")
    with st.form("crear_jugador"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Nombre del jugador", value="")
            position = st.selectbox("Posición", POSITIONS, format_func=lambda p: f"{POSITION_ICON[p]} {p}")
            age = st.slider("Edad inicial", 16, 19, 17)
        with c2:
            country = st.selectbox("País", COUNTRIES)
            talent = st.selectbox("Nivel de talento inicial", list(TALENT_TIERS.keys()))
        submitted = st.form_submit_button("🚀 Comenzar carrera", type="primary", use_container_width=True)
    if submitted:
        create_player(name, position, country, talent, age)


def render_sidebar():
    player = st.session_state.player
    with st.sidebar:
        st.markdown("### 🎮 Panel de control")
        st.write(f"**{player['name']}**")
        st.write(f"{POSITION_ICON[player['position']]} {player['position']} · {player['country']}")
        st.write(f"🏟️ {player['club_name']} ({CLUB_TIERS[player['club_tier']]})")
        st.divider()
        st.markdown("#### ⚡ Simulación rápida")
        n_auto = st.number_input("Temporadas a simular automáticamente", min_value=1, max_value=10, value=3)
        if st.button("Simular automáticamente", use_container_width=True):
            auto_simulate(int(n_auto))
        st.divider()
        if st.button("🔄 Reiniciar carrera", use_container_width=True):
            reset_career()


def render_header(player):
    st.markdown(f"## {POSITION_ICON[player['position']]} {player['name']} — {player['position']}")
    st.caption(f"Temporada {st.session_state.season} · {player['club_name']} "
               f"({CLUB_TIERS[player['club_tier']]}) · {player['country']} · {player['age']} años")


def render_resumen(player):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall", player["overall"])
    c2.metric("Valor de mercado", format_value(player["market_value"]))
    c3.metric("Reputación", f"{player['reputation']}/100")
    c4.metric("Moral", f"{player['morale']}/100")

    colA, colB = st.columns([1.1, 1])
    with colA:
        st.plotly_chart(radar_chart(player), use_container_width=True)
    with colB:
        st.markdown("**Estado físico y anímico**")
        st.progress(player["form"] / 100, text=f"Forma: {player['form']}/100")
        st.progress(player["morale"] / 100, text=f"Moral: {player['morale']}/100")
        st.markdown(
            f"**Club:** {player['club_name']}  \n"
            f"**División:** {CLUB_TIERS[player['club_tier']]}  \n"
            f"**País:** {player['country']}  \n"
            f"**Convocatorias a selección:** {player['caps']}  \n"
            f"**Estadísticas totales:** {player['games_total']} PJ · "
            f"{player['goals_total']} goles · {player['assists_total']} asistencias"
        )
        if player["injury_weeks"] > 0:
            st.error(f"🩹 Lesionado: {player['injury_weeks']} semanas restantes")


def render_decision(player):
    st.subheader("🎯 Decisión de la Temporada")
    stage = st.session_state.stage

    if stage == "training":
        st.markdown(f"**Temporada {st.session_state.season}** — Elegí en qué enfocar el entrenamiento")
        attr_choice = st.radio(
            "Atributo a entrenar",
            ATTRS,
            format_func=lambda a: f"{ATTR_LABELS[a]} ({player['attributes'][a]} / pot. {player['potential'][a]})",
            key="attr_choice_radio",
        )
        if st.button("Confirmar enfoque de entrenamiento ✅", type="primary"):
            st.session_state.training_focus = attr_choice
            st.session_state.current_dilemma = random.choice(DILEMMAS)
            st.session_state.stage = "dilemma"
            st.rerun()

    elif stage == "dilemma":
        dilemma = st.session_state.current_dilemma
        st.info(f"**{dilemma['title']}**\n\n{dilemma['text']}")
        cols = st.columns(len(dilemma["options"]))
        for i, opt in enumerate(dilemma["options"]):
            with cols[i]:
                if st.button(opt["label"], key=f"dilemma_opt_{i}", use_container_width=True):
                    apply_effects(player, opt["effects"])
                    st.session_state.news.insert(
                        0, f"Temporada {st.session_state.season}: {dilemma['title']} → {opt['label']}")
                    st.session_state.stage = "ready_to_sim"
                    st.rerun()

    elif stage == "ready_to_sim":
        st.success("Todo listo. El cuerpo técnico definió los planes de la temporada.")
        st.write(f"Enfoque de entrenamiento: **{ATTR_LABELS[st.session_state.training_focus]}**")
        if st.button("⚽ Simular Temporada", type="primary"):
            result = simulate_season(player, st.session_state.training_focus)
            st.session_state.last_result = result
            st.session_state.stage = "summary"
            st.rerun()

    elif stage == "summary":
        render_summary(player, st.session_state.last_result)
        if player["age"] >= 35:
            st.warning(f"{player['name']} tiene {player['age']} años. ¿Continúa la carrera?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Seguir una temporada más 💪", use_container_width=True):
                    advance_to_next_season()
            with c2:
                if st.button("Retirarse 🏁", use_container_width=True):
                    st.session_state.game_over = True
                    st.rerun()
        else:
            if st.button("➡️ Continuar a la próxima temporada", type="primary"):
                advance_to_next_season()


def render_summary(player, result):
    st.markdown("### 📋 Resumen de la Temporada")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Partidos", result["matches"])
    c2.metric("Goles", result["goals"])
    c3.metric("Asistencias", result["assists"])
    c4.metric("Rating promedio", result["avg_rating"])
    if result["trophy"]:
        st.success(f"🏆 ¡Ganaste el {result['trophy']}!")
        st.balloons()
    if result["called_up"]:
        st.info("🌍 Fuiste convocado a la selección nacional.")
    if result["transfer"]:
        st.warning(f"🔁 ¡Transferencia! Ahora jugás en {player['club_name']} ({CLUB_TIERS[player['club_tier']]}).")
    if result["injury_weeks"] > 0:
        st.error(f"🩹 Sufriste una lesión de {result['injury_weeks']} semanas.")


def render_progresion():
    hist = st.session_state.history
    if not hist:
        st.info("Todavía no hay datos históricos. Jugá tu primera temporada en la pestaña Decisión.")
        return
    df = pd.DataFrame(hist)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["season"], y=df["overall"], mode="lines+markers", name="Overall",
                               line_color="#00d4ff"))
    fig1.update_layout(template="plotly_dark", height=320, title="Evolución del Overall",
                        margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df["season"], y=df["goals"], name="Goles", marker_color="#2ecc71"))
    fig2.add_trace(go.Bar(x=df["season"], y=df["assists"], name="Asistencias", marker_color="#f1c40f"))
    fig2.update_layout(barmode="group", template="plotly_dark", height=320,
                        title="Goles y Asistencias por Temporada", margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df["season"], y=df["market_value"], mode="lines+markers",
                               name="Valor de mercado", line_color="#e67e22"))
    fig3.update_layout(template="plotly_dark", height=320, title="Valor de Mercado (€)",
                        margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig3, use_container_width=True)


def render_historial():
    hist = st.session_state.history
    st.markdown("#### 📊 Historial de temporadas")
    if hist:
        df = pd.DataFrame(hist).rename(columns={
            "season": "Temporada", "age": "Edad", "club": "Club", "division": "División",
            "matches": "PJ", "goals": "Goles", "assists": "Asist.", "avg_rating": "Rating",
            "overall": "Overall", "market_value": "Valor (€)",
        })
        df["Valor (€)"] = df["Valor (€)"].apply(format_value)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no jugaste ninguna temporada.")

    st.markdown("#### 🏆 Trofeos")
    trophies = st.session_state.trophies
    if trophies:
        for t in trophies:
            st.write(f"🏆 Temporada {t['season']}: {t['title']}")
    else:
        st.caption("Todavía no ganaste trofeos.")


def render_noticias():
    st.markdown("#### 📰 Últimas noticias")
    news = st.session_state.news[:30]
    if not news:
        st.caption("Sin noticias todavía.")
    for n in news:
        st.write(f"• {n}")


def render_retirement_screen():
    player = st.session_state.player
    st.title("🏁 Fin de la Carrera")
    st.markdown(f"### {player['name']} se retira a los {player['age']} años")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Partidos jugados", player["games_total"])
    c2.metric("Goles totales", player["goals_total"])
    c3.metric("Asistencias totales", player["assists_total"])
    c4.metric("Trofeos ganados", len(st.session_state.trophies))
    for t in st.session_state.trophies:
        st.write(f"🏆 Temporada {t['season']}: {t['title']}")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button("🔄 Comenzar nueva carrera", type="primary"):
        reset_career()


# ----------------------------------------------------------------------------
# APP PRINCIPAL
# ----------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="⚽ Simulador de Carrera", page_icon="⚽", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not st.session_state.get("started"):
        render_creation_screen()
        return

    if st.session_state.get("game_over"):
        render_retirement_screen()
        return

    player = st.session_state.player
    render_sidebar()
    render_header(player)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏟️ Resumen", "🎯 Decisión", "📈 Progresión", "📊 Historial", "📰 Noticias"])
    with tab1:
        render_resumen(player)
    with tab2:
        render_decision(player)
    with tab3:
        render_progresion()
    with tab4:
        render_historial()
    with tab5:
        render_noticias()


if __name__ == "__main__":
    main()
