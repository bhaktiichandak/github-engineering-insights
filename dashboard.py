import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="GitHub Repo Analytics",
    page_icon="🔬",
    layout="wide",
)

# ── Minimal Dark Styling ──────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #0d0d0d; color: #e8e8e8; }
.stTextInput input { background-color: #161616; color: #e8e8e8; }
.stButton button {
    background-color: #e8e8e8;
    color: #0d0d0d;
    font-weight: 600;
    width: 100%;
}
hr { border-color: #222; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("# GitHub Analytics Dashboard")
st.markdown("Analyze repository activity using FastAPI + PostgreSQL backend")
st.markdown("---")

# ── Inputs ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    owner = st.text_input("Owner", placeholder="e.g. torvalds")

with col2:
    repo = st.text_input("Repository", placeholder="e.g. linux")

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("INGEST & ANALYZE")

# ── Main Logic ─────────────────────────────────────────────────────────
if run:

    if not owner.strip() or not repo.strip():
        st.error("Please provide both owner and repository name.")
        st.stop()

    params = {"owner": owner.strip(), "repo": repo.strip()}

    # ── Ingest Commits ───────────────────────────────────────────────
    with st.spinner("Ingesting commits..."):
        try:
            r = requests.get(f"{BASE_URL}/commits", params=params, timeout=60)
            r.raise_for_status()

            ingest_data = r.json()
            st.success(f"Inserted {ingest_data.get('inserted', 0)} new commits.")

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach backend at http://127.0.0.1:8000. Is it running?")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"Ingest failed: {e}")
            st.stop()

    # ── Fetch Analytics ───────────────────────────────────────────────
    with st.spinner("Fetching analytics..."):
        try:
            summary_r      = requests.get(f"{BASE_URL}/repo-summary", params=params)
            contributors_r = requests.get(f"{BASE_URL}/top-contributors", params=params)
            activity_r     = requests.get(f"{BASE_URL}/commit-activity", params=params)

            summary_r.raise_for_status()
            contributors_r.raise_for_status()
            activity_r.raise_for_status()

            summary      = summary_r.json()
            contributors = contributors_r.json().get("top_contributors", [])
            activity     = activity_r.json().get("commit_activity", [])

        except Exception as e:
            st.error(f"Error fetching analytics: {e}")
            st.stop()

    # ── Summary Metrics ───────────────────────────────────────────────
    st.markdown("## Repository Summary")
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Commits", summary.get("total_commits", 0))
    m2.metric("Total Contributors", summary.get("total_contributors", 0))
    m3.metric("First Commit", summary.get("first_commit", "—"))
    m4.metric("Latest Commit", summary.get("latest_commit", "—"))

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────
    colA, colB = st.columns(2)

    # Top Contributors
    with colA:
        st.markdown("### Top Contributors")
        if contributors:
            df_c = pd.DataFrame(contributors).sort_values("commits", ascending=True)

            fig = go.Figure(go.Bar(
                x=df_c["commits"],
                y=df_c["author"],
                orientation="h",
            ))

            fig.update_layout(
                paper_bgcolor="#111111",
                plot_bgcolor="#111111",
                font_color="#e8e8e8",
                height=350,
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No contributor data available.")

    # Commit Activity
    with colB:
        st.markdown("### Commit Activity Over Time")
        if activity:
            df_a = pd.DataFrame(activity)
            df_a["date"] = pd.to_datetime(df_a["date"])
            df_a = df_a.sort_values("date")

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_a["date"],
                y=df_a["commits"],
                mode="lines",
                fill="tozeroy"
            ))

            fig2.update_layout(
                paper_bgcolor="#111111",
                plot_bgcolor="#111111",
                font_color="#e8e8e8",
                height=350,
            )

            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No activity data available.")