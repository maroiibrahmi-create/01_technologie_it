from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard Support IT", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "01_Technologie_IT.xlsx"
EXPECTED_COLUMNS = [
    "ID ticket", "Date ouverture", "Ville", "Service", "Canal",
    "Type de demande", "Priorité", "Réponse (h)", "Résolution (h)",
    "Statut", "Objectif SLA (h)", "Satisfaction /5",
]


@st.cache_data
def read_data(file_bytes=None):
    """Read and validate the workbook's Données sheet."""
    if file_bytes is None:
        source = DATA_FILE
    else:
        from io import BytesIO
        source = BytesIO(file_bytes)

    data = pd.read_excel(source, sheet_name="Données", skiprows=2)
    data.columns = data.columns.astype(str).str.strip()

    missing = [column for column in EXPECTED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError("Colonnes manquantes : " + ", ".join(missing))

    data["Date ouverture"] = pd.to_datetime(data["Date ouverture"], errors="coerce")
    for column in ["Réponse (h)", "Résolution (h)", "Objectif SLA (h)", "Satisfaction /5"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["Mois"] = data["Date ouverture"].dt.to_period("M").astype(str)
    data["Est résolu"] = data["Statut"].astype(str).str.strip().str.casefold().eq("résolu")
    data["SLA évaluable"] = (
        data["Est résolu"]
        & data["Résolution (h)"].notna()
        & data["Objectif SLA (h)"].notna()
    )
    data["Dépassement SLA"] = pd.Series(pd.NA, index=data.index, dtype="boolean")
    evaluable = data["SLA évaluable"]
    data.loc[evaluable, "Dépassement SLA"] = (
        data.loc[evaluable, "Résolution (h)"] > data.loc[evaluable, "Objectif SLA (h)"]
    )
    return data


def chart_style(ax, title, xlabel=None, ylabel=None):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def render(fig):
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


st.title("📊 Dashboard — Tickets de support informatique")
st.caption("Analyse des 800 tickets (janvier–août 2026) et réponses aux six questions du mode d’emploi.")

with st.sidebar:
    st.header("Filtres")
    uploaded_file = st.file_uploader("Importer un fichier Excel (facultatif)", type=["xlsx"])

try:
    if uploaded_file is not None:
        original = read_data(uploaded_file.getvalue())
    elif DATA_FILE.exists():
        original = read_data()
    else:
        st.error("Fichier Excel introuvable. Placez 01_Technologie_IT.xlsx à côté de app.py ou importez-le dans la barre latérale.")
        st.stop()
except Exception as error:
    st.error(f"Erreur de lecture du fichier Excel : {error}")
    st.stop()

with st.sidebar:
    def filter_options(label, column):
        values = sorted(original[column].dropna().astype(str).unique().tolist())
        return st.multiselect(label, values, default=values)

    cities = filter_options("Ville", "Ville")
    services = filter_options("Service", "Service")
    channels = filter_options("Canal", "Canal")
    types = filter_options("Type de demande", "Type de demande")
    priorities = filter_options("Priorité", "Priorité")
    statuses = filter_options("Statut", "Statut")

    min_date = original["Date ouverture"].min().date()
    max_date = original["Date ouverture"].max().date()
    date_range = st.date_input(
        "Dates d'ouverture",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

data = original[
    original["Ville"].astype(str).isin(cities)
    & original["Service"].astype(str).isin(services)
    & original["Canal"].astype(str).isin(channels)
    & original["Type de demande"].astype(str).isin(types)
    & original["Priorité"].astype(str).isin(priorities)
    & original["Statut"].astype(str).isin(statuses)
].copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
    data = data[data["Date ouverture"].ge(start) & data["Date ouverture"].lt(end)]

if data.empty:
    st.warning("Aucun ticket ne correspond aux filtres. Modifiez les filtres dans la barre latérale.")
    st.stop()

resolved = data[data["Est résolu"]].copy()
sla_data = data[data["SLA évaluable"]].copy()
sla_data["Dépassement SLA"] = (
    sla_data["Résolution (h)"] > sla_data["Objectif SLA (h)"]
)
sla_rate = sla_data["Dépassement SLA"].mean() if not sla_data.empty else None
satisfaction = data["Satisfaction /5"].mean()

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Tickets analysés", f"{len(data):,}".replace(",", " "))
m2.metric("Tickets résolus", f"{len(resolved):,}".replace(",", " "))
m3.metric("Non résolus", f"{len(data) - len(resolved):,}".replace(",", " "))
m4.metric("Dépassement SLA", f"{sla_rate:.1%}" if sla_rate is not None else "N/A")
m5.metric("Satisfaction moyenne", f"{satisfaction:.2f}/5" if pd.notna(satisfaction) else "N/A")

tabs = st.tabs([
    "1 · Types de demandes",
    "2 · Services",
    "3 · SLA et priorité",
    "4 · Canaux et réponse",
    "5 · Évolution mensuelle",
    "6 · Recommandation",
    "Données",
])

# Question 1
with tabs[0]:
    st.subheader("Quels types de demandes représentent le plus de tickets ?")
    counts = data["Type de demande"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    counts.plot(kind="barh", ax=ax)
    chart_style(ax, "Nombre de tickets par type de demande", xlabel="Nombre de tickets")
    render(fig)
    if not counts.empty:
        top = counts.idxmax()
        st.success(f"**Réponse :** « {top} » est le type le plus fréquent, avec **{counts.max()} tickets** ({counts.max() / len(data):.1%} du volume filtré).")

# Question 2
with tabs[1]:
    st.subheader("Quel service reçoit le plus de tickets et quel est son délai médian de résolution ?")
    volume = data["Service"].value_counts().sort_values()
    medians = resolved.groupby("Service")["Résolution (h)"].median().dropna()
    left, right = st.columns(2)
    with left:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        volume.plot(kind="barh", ax=ax)
        chart_style(ax, "Tickets par service", xlabel="Nombre de tickets")
        render(fig)
    with right:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        medians.sort_values().plot(kind="barh", ax=ax)
        chart_style(ax, "Délai médian de résolution", xlabel="Heures")
        render(fig)
    if not volume.empty:
        service = volume.idxmax()
        median = medians.get(service)
        median_text = f"{median:.2f} heures" if pd.notna(median) else "non disponible (aucun délai exploitable)"
        st.info(f"**Réponse :** le service **{service}** reçoit le plus de tickets (**{volume.max()}**). Son délai médian de résolution est de **{median_text}**.")
    st.caption("La médiane est calculée sur les tickets résolus du service disposant d'une durée de résolution.")

# Question 3
with tabs[2]:
    st.subheader("Quelle part des tickets résolus dépasse l’objectif SLA ? Comparez par priorité.")
    left, right = st.columns(2)
    with left:
        if not sla_data.empty:
            labels = sla_data["Dépassement SLA"].map({True: "SLA dépassé", False: "SLA respecté"}).value_counts()
            fig, ax = plt.subplots(figsize=(6, 4.5))
            labels.plot(kind="bar", ax=ax)
            chart_style(ax, "Tickets résolus évaluables", ylabel="Nombre de tickets")
            ax.tick_params(axis="x", rotation=0)
            render(fig)
        else:
            st.info("Aucun ticket résolu avec les données nécessaires au calcul du SLA.")
    with right:
        by_priority = sla_data.groupby("Priorité")["Dépassement SLA"].mean().sort_values()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        (by_priority * 100).plot(kind="barh", ax=ax)
        chart_style(ax, "Taux de dépassement par priorité", xlabel="Dépassement SLA (%)")
        render(fig)
    if not sla_data.empty:
        exceeded = int(sla_data["Dépassement SLA"].sum())
        st.info(f"**Réponse :** **{sla_data['Dépassement SLA'].mean():.1%}** des tickets résolus évaluables dépassent le SLA (**{exceeded} sur {len(sla_data)}**).")
    if not by_priority.empty:
        table = (by_priority * 100).rename("Taux de dépassement (%)").to_frame().round(1)
        st.dataframe(table, use_container_width=True)
    st.caption("Dénominateur : tickets résolus avec durée de résolution et objectif SLA renseignés. Les tickets en cours ne sont pas comptés comme des dépassements.")

# Question 4
with tabs[3]:
    st.subheader("Les canaux d’entrée diffèrent-ils en temps de première réponse ?")
    response = data.dropna(subset=["Canal", "Réponse (h)"])
    if not response.empty:
        channel_order = response.groupby("Canal")["Réponse (h)"].median().sort_values().index.tolist()
        values = [response.loc[response["Canal"].eq(channel), "Réponse (h)"].values for channel in channel_order]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.boxplot(values, tick_labels=channel_order, showfliers=False)
        chart_style(ax, "Distribution du délai de première réponse par canal", ylabel="Heures")
        ax.tick_params(axis="x", rotation=20)
        render(fig)
        summary = response.groupby("Canal")["Réponse (h)"].agg(
            Tickets="count", Médiane_h="median", Moyenne_h="mean"
        ).round(2).sort_values("Médiane_h")
        st.dataframe(summary, use_container_width=True)
        st.info(f"**Réponse :** la médiane la plus courte est observée via **{summary.index[0]}** ({summary.iloc[0]['Médiane_h']:.2f} h), et la plus longue via **{summary.index[-1]}** ({summary.iloc[-1]['Médiane_h']:.2f} h).")
    else:
        st.info("Aucune donnée de première réponse pour cette sélection.")
    st.caption("Cette comparaison est descriptive et ne démontre pas que le canal est la cause des écarts.")

# Question 5
with tabs[4]:
    st.subheader("Comment le volume de tickets et les dépassements SLA évoluent-ils par mois ?")
    monthly = data.groupby("Mois").agg(
        Tickets=("ID ticket", "count"),
        Résolus=("Est résolu", "sum"),
    )
    monthly_sla = sla_data.groupby("Mois").agg(
        Dépassements=("Dépassement SLA", "sum"),
        Tickets_SLA_évaluables=("Dépassement SLA", "count"),
    )
    monthly = monthly.join(monthly_sla, how="left")
    monthly[["Dépassements", "Tickets_SLA_évaluables"]] = monthly[
        ["Dépassements", "Tickets_SLA_évaluables"]
    ].fillna(0)
    monthly["Taux dépassement (%)"] = (
        monthly["Dépassements"].div(
        monthly["Tickets_SLA_évaluables"].where(monthly["Tickets_SLA_évaluables"].ne(0))
    ) * 100
    )
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(monthly.index, monthly["Tickets"], marker="o", label="Tous les tickets")
    ax.plot(monthly.index, monthly["Dépassements"], marker="o", label="Dépassements SLA")
    chart_style(ax, "Volume mensuel et dépassements SLA", ylabel="Nombre de tickets")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    render(fig)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(monthly.index, monthly["Taux dépassement (%)"], marker="o")
    chart_style(ax, "Taux mensuel de dépassement SLA", ylabel="Pourcentage (%)")
    ax.tick_params(axis="x", rotation=30)
    render(fig)
    if not monthly.empty:
        busiest = monthly["Tickets"].idxmax()
        message = f"Le mois le plus chargé est **{busiest}** ({int(monthly.loc[busiest, 'Tickets'])} tickets)."
        valid = monthly["Taux dépassement (%)"].dropna()
        if not valid.empty:
            worst = valid.idxmax()
            message += f" Le taux de dépassement SLA le plus élevé est observé en **{worst}** ({valid.max():.1f}%)."
        st.info("**Réponse :** " + message)
    st.dataframe(monthly.round(2), use_container_width=True)

# Question 6
with tabs[5]:
    st.subheader("Quelle action concrète proposer au responsable du support ?")
    priority_rates = sla_data.groupby("Priorité")["Dépassement SLA"].mean().sort_values(ascending=False)
    helpdesk_count = int(data["Service"].astype(str).str.casefold().eq("helpdesk").sum())
    top_type_series = data["Type de demande"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tickets Helpdesk", helpdesk_count)
    if not priority_rates.empty:
        c2.metric("Priorité avec le plus fort taux SLA", str(priority_rates.index[0]), f"{priority_rates.iloc[0]:.1%} de dépassement")
    else:
        c2.metric("Priorité SLA", "Données insuffisantes")
    c3.metric("Tickets SLA évaluables", len(sla_data))
    st.markdown(
        """
        **Recommandation : mettre en place un triage quotidien des tickets à priorité Critique et Haute, avec des alertes avant l’échéance SLA.**

        1. **Prévenir les dépassements :** déclencher des alertes à 75 % puis 90 % du délai SLA.
        2. **Suivre les tickets prioritaires :** attribuer un responsable et escalader rapidement les tickets proches de l’échéance.
        3. **Réduire les demandes récurrentes :** créer une FAQ ou une base de connaissances pour les types de demandes les plus fréquents.
        4. **Piloter chaque semaine :** suivre le taux SLA par priorité, service et canal, ainsi que les délais de première réponse.
        5. **Mesurer l’effet :** comparer les résultats du mois suivant avec la période de référence avant de conclure que l’action fonctionne.
        """
    )
    if not top_type_series.empty:
        st.caption(f"À vérifier en priorité dans les données filtrées : « {top_type_series.idxmax()} », première catégorie en volume.")

# Data export
with tabs[6]:
    st.subheader("Données filtrées")
    st.write(f"{len(data)} tickets affichés sur {len(original)} dans le fichier.")
    st.dataframe(data.drop(columns=["Est résolu", "SLA évaluable"], errors="ignore"), use_container_width=True, height=450)
    st.download_button(
        "Télécharger les données filtrées en CSV",
        data=data.to_csv(index=False).encode("utf-8-sig"),
        file_name="tickets_support_filtres.csv",
        mime="text/csv",
    )

with st.expander("Méthodologie"):
    st.markdown(
        """
        - Les données sont lues depuis la feuille **Données**, en sautant les deux premières lignes de titre.
        - Tous les graphiques et indicateurs réagissent aux filtres de la barre latérale.
        - Un dépassement SLA signifie `Résolution (h) > Objectif SLA (h)`.
        - Le taux SLA utilise uniquement les tickets résolus disposant des deux valeurs nécessaires.
        - Les médianes sont utilisées pour résumer les délais, car elles sont moins sensibles aux valeurs extrêmes.
        """
    )
