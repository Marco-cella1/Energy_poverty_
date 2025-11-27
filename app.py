# --- IMPORT PACKAGES ---
import sys
sys.path.append("..")   # go up one directory so Python sees Librarian/

from Librarian.models import WorldDataset, CobbDouglasFit
from Librarian.config import REGION_PALETTE, REGION_NAME_MAP, INDICATORS
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st



# --- LOAD WORLD ON CACHE ---
@st.cache_data
def load_world():
    """Download and cache the World Bank panel."""
    world = WorldDataset.from_api(INDICATORS, years=range(2000, 2023))
    return world


# --- APP LAYOUT ---
# Load dataset (cached)
world = load_world()

# Main layout
st.set_page_config(layout="wide") #fill the page

st.title("Energy consumption and life expectancy")

st.markdown("""The chart shows the energy consumption per capita on the x-axis and the life expectancy on the y-axis,
with countries colored by regions.""")

# Create two columns
col_left, col_right = st.columns([3, 2])

# Create the slider
with col_right:
    st.subheader("Options")
    year = st.slider("Select year", min_value=2000, max_value=2022, value=2000, step=1)



# --- BUILD SNAPSHOT FOR SELECTED YEAR ---

snapshot = world.snapshot(year).dropna(subset=["energy_use_per_capita", "life_expectancy"])

# add region names if not already there
snapshot = world.add_region_names(snapshot)
snapshot["region_name"] = snapshot["region"].map(REGION_NAME_MAP).fillna("Other")


with col_right:
    # Cobb Douglass button
    show_cobb = st.checkbox("Cobb–Douglas fit", value=False)

    # Region filter
    all_regions = sorted(snapshot["region_name"].dropna().unique())
    selected_regions = st.multiselect(
        "Show regions",
        options=all_regions,
        default=all_regions,
    )

if selected_regions:  # if user deselects everything, keep empty
    snapshot = snapshot[snapshot["region_name"].isin(selected_regions)]





# --- PLOT SCATTER ---

fig, ax = plt.subplots(figsize=(6.5, 4)) # Dimesions
sns.scatterplot(
    data=snapshot,
    x="energy_use_per_capita",
    y="life_expectancy",
    hue="region_name",
    palette=REGION_PALETTE,
    s=50, # Bubble size
    alpha=0.7, # Bubble transparency
)

# Set the graph
ax.set_xlabel("Energy consumption per capita (kWh)")
ax.set_ylabel("Life expectancy (years)")
ax.set_xlim(0, 220000)
ax.set_ylim(45, 85)

# Cobb Douglas
if show_cobb and not snapshot.empty:
    # Fit Cobb–Douglas on the current snapshot
    fit = CobbDouglasFit.fit(
        x=snapshot["energy_use_per_capita"],
        y=snapshot["life_expectancy"],
    )

    # Build the curve
    x_fit, y_fit = fit.curve(x_min=0, x_max=220000, n=200)

    # Draw the curve
    ax.plot(x_fit, y_fit, color="orange", linewidth=2,
            label=f"Cobb–Douglas (α = {fit.alpha:.2f}, R² = {fit.r2:.2f})")


# Vertical line for energy use mean
mean_energy = snapshot["energy_use_per_capita"].mean()
ax.axvline(mean_energy, color="red", linestyle="--", linewidth=1.5, label=f"Mean: {mean_energy:,.0f} kWh")

# Horizontal line for life expectancy mean
mean_life_expectancy = snapshot["life_expectancy"].mean()
ax.axhline(mean_life_expectancy, color="green", linestyle="--", linewidth=1.5, label=f"Mean: {mean_life_expectancy:,.0f} years")


ax.set_title(f"Energy consumption and Life Expectancy ({year})")
ax.grid(alpha=0.3)
ax.legend(title="Region", loc="lower right", fontsize=5)

with col_left:
    st.pyplot(fig, use_container_width=False)