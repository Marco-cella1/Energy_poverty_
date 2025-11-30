import sys
import matplotlib.pyplot as plt
import streamlit as st

sys.path.append(".")

from Librarian.data_loader import load_world



# --- APP LAYOUT ---
# Load dataset (cached)
world = load_world()

# Main layout
st.set_page_config(layout="wide")
st.title("How to produce energy in a sustainable way?")
st.write("The chart shows the electricity production by nuclear fission and renewables sources (excluding hydro)"
         "as a percentage of the total electricity production."
)


col_left, col_right = st.columns([3, 2])

with col_right:
    year = st.slider("Year", 2000, 2021, 2021)

# --- Take snapshot for that year ---
snapshot = world.full_snapshot(year)

# creating another snapshot to avoid empty dataframe problems
cols_needed = ["name", "renewable_electricity_share_nohydro", "nuclear_electricity_share"]
snapshot_sub = snapshot[cols_needed].copy()

snapshot_sub = snapshot_sub.dropna(
    subset=["renewable_electricity_share_nohydro", "nuclear_electricity_share"]
)

if snapshot_sub.empty:
    st.warning("No low-carbon electricity data available for this year.")
else:
    # Force types
    snapshot_sub["name"] = snapshot_sub["name"].astype(str)
    snapshot_sub["renew"] = snapshot_sub["renewable_electricity_share_nohydro"].astype(float)
    snapshot_sub["nuc"] = snapshot_sub["nuclear_electricity_share"].astype(float)

    # Total low-carbon share
    snapshot_sub["total"] = snapshot_sub["renew"] + snapshot_sub["nuc"]

    # Top 20 by total
    top20 = (
        snapshot_sub
        .sort_values("total", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    # If empty bail out
    if top20.empty:
        st.warning("No country passes the filters for this year.")
    else:
        countries = top20["name"]
        renew = top20["renew"]
        nuc = top20["nuc"]

# ---------- PLOT GRAPH ---------------------

        with col_left:
            fig, ax = plt.subplots(figsize=(6.5, 5))

            ax.barh(
                y=countries,
                width=nuc,
                color="#0044FF",
                label="Nuclear",
            )

            ax.barh(
                y=countries,
                width=renew,
                left=nuc,
                color="#00FF22",
                label="Renewables",
            )

            ax.set_xlabel("Low-carbon electricity share (%)")
            ax.set_title(
                f"Top 20 countries by sustainable electricity share ({year})"
            )
            ax.invert_yaxis()
            ax.grid(axis="x", alpha=0.3)
            ax.legend(loc="lower right")

            plt.tight_layout()
            st.pyplot(fig)

# ------ INTERPRETATION -----------------

        with col_right:
            st.markdown("### Interpretation")
            st.markdown("This chart shows the countries with the highest shares of low-carbon electricity, combining renewables (excluding large hydro) "
                        "and nuclear power. Hydro is excluded because it depends heavily on geography: only countries with abundant rivers, suitable terrain, "
                        "and large hydraulic basins can deploy it at scale. "
                        "Including hydro would therefore exaggerate the performance of countries that are simply "
                        "geographically privileged rather than technologically decarbonized.  \n\n"
                        
                        "By focusing on renewables excluding hydro, the chart highlights the countries that have actually invested in modern low-carbon systems "
                        "such as wind, solar, geothermal, and nuclear.  \n\n")
            st.markdown("""
            A clear pattern emerges:
            - Advanced economies dominate the top positions thanks to the combined contribution of renewables and nuclear power. 
            These nations have both the capital and the infrastructure to deploy a diversified low-carbon mix  
            - Less developed or poorer countries often appear in the ranking primarily thanks to renewables alone — typically solar, wind, or geothermal — 
            because they lack the financial and institutional capacity to build or operate nuclear reactors
            """)
            st.markdown(
            "Overall, the figure makes evident that achieving deep decarbonization at scale usually requires both modern renewables and nuclear energy, "
            "especially for nations aiming to maintain high levels of economic development and reliable electricity supply."
            )
