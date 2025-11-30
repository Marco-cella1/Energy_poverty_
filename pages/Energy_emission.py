# --- IMPORT PACKAGES ---
import sys

from sklearn.linear_model import LinearRegression

sys.path.append(".")   # go up one directory so Python sees Librarian/

from Librarian.data_loader import load_world
from Librarian.config import REGION_PALETTE, REGION_NAME_MAP
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from sklearn.metrics import r2_score




# --- APP LAYOUT ---
# Load dataset (cached)
world = load_world()

# Main layout
st.set_page_config(layout="wide") #fill the page

st.title("The hidden cost of energy")

st.markdown("""The chart shows the energy consumption per capita on the x-axis and the Carbon dioxide emission per capita on the y-axis,
with countries colored by regions.""")

# Create two columns
col_left, col_right = st.columns([3, 2])

# Create the slider
with col_right:
    st.subheader("Options")
    year = st.slider("Select a year", min_value=2000, max_value=2022, value=2000, step=1)

# --- BUILD SNAPSHOT FOR SELECTED YEAR ---

snapshot = world.full_snapshot(year,required=["energy_use_per_capita", "co2_per_capita"])



with col_right:
    # Region filter
    all_regions = sorted(snapshot["region_name"].dropna().unique())
    selected_regions = st.multiselect(
        "Choose regions to plot",
        options=all_regions,
        default=all_regions,
    )

    # Linear regression button
    show_linear = st.checkbox("Linear regression", value=False)

if selected_regions:  # if user deselects everything, keep empty
    snapshot = snapshot[snapshot["region_name"].isin(selected_regions)]

with col_right:
    st.subheader("Description")
    st.markdown("This chart illustrates the relationship between national energy consumption per capita and carbon dioxide emissions.  \n"
                "The nearly perfect linear regression reflects a fundamental reality: most of the energy consumed globally is still produced "
                "through the combustion of fossil fuels, which inevitably generates CO₂ alongside other by-products. \n\n"
                "However, the strength of this relationship has weakened over time. Observing the R² across the years, we see a clear downward trend in recent decades.  \n"
                "This happens because many economies have begun to decarbonize their power systems, increasing the share of low-carbon electricity such as renewables and nuclear fission. "
                "As a result, countries with similar levels of energy consumption are now starting to show meaningfully different emissions profiles.  \n"
                "The chart helps identify these diverging trajectories and highlights the growing importance of clean energy systems in breaking "
                "the historical coupling between energy use and carbon output ")




# --- PLOT SCATTER ---

fig, ax = plt.subplots(figsize=(6.5, 4)) # Dimesions
sns.scatterplot(
    data=snapshot,
    x="energy_use_per_capita",
    y="co2_per_capita",
    hue="region_name",
    palette=REGION_PALETTE,
    s=50, # Bubble size
    alpha=0.7, # Bubble transparency
)

# Set the graph
ax.set_xlabel("Energy consumption per capita (kWh / year)")
ax.set_ylabel("CO2 Emission per capita (eq. Ton / year)")

# --- Regression line ---
if show_linear and not snapshot.empty:
    X = snapshot["energy_use_per_capita"].values.reshape(-1, 1)
    y = snapshot["co2_per_capita"].values

    model = LinearRegression()
    model.fit(X, y)

    x_fit = np.linspace(X.min(), X.max(), 200)
    y_fit = model.predict(x_fit.reshape(-1, 1))
    r2 = r2_score(y, model.predict(X))

    ax.plot(
        x_fit,
        y_fit,
        color="blue",
        linewidth=2,
        label=f"Linear fit (R² = {r2:.2f})",
    )


# axis limits
ax.set_xlim(0, 220000)
ax.set_ylim(0, 50)


ax.set_title(f"Energy consumption and CO2 emissions ({year})")
ax.grid(alpha=0.3)
ax.legend(title="Region", loc="upper left", fontsize=5)

with col_left:
    st.pyplot(fig, use_container_width=False)