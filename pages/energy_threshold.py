# --- IMPORT PACKAGES ---
import sys
sys.path.append("..")   # go up one directory so Python sees Librarian/

from Librarian.data_loader import load_world
from Librarian.models import WorldDataset, CobbDouglasFit
from Librarian.config import REGION_PALETTE, REGION_NAME_MAP
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st





# --- APP LAYOUT ---
# Load dataset (cached)
world = load_world()

# Main layout
st.set_page_config(layout="wide")
st.title("How much energy do we need?")
st.markdown("""The chart shows the energy consumption per capita on the x-axis and the life expectancy on the y-axis,
with countries colored by regions.""")

# Create two columns
col_left, col_right = st.columns([3, 2])

# --------- DATA INPUTS AND PROCESSING ------------

# Create the year and threshold sliders
with col_right:
    st.subheader("Options")
    year = st.slider("Select a year", min_value=2000, max_value=2022, value=2022, step=1)
    life_exp_target = st.slider("Select a threshold for life expectancy", min_value=50, max_value=83, value=50, step=1)

# Build the snapshot
snapshot = world.full_snapshot(year,required=["energy_use_per_capita", "life_expectancy"])

# Create the other options
with col_right:
    # Region filter
    all_regions = sorted(snapshot["region_name"].dropna().unique())
    selected_regions = st.multiselect(
        "Choose regions to plot",
        options=all_regions,
        default=all_regions,
    )

    # Cobb Douglass button
    show_cobb = st.checkbox("Cobb–Douglas fit", value=False)
    # Log scale button
    use_log_scale = st.checkbox("Log scale on energy axis", value=False)


# if user deselects everything, keep empty
if selected_regions:
    snapshot = snapshot[snapshot["region_name"].isin(selected_regions)]

# ------------- THRESHOLD APPLICATION -------------------------

eligible = snapshot[snapshot["life_expectancy"] >= life_exp_target].copy()

if eligible.empty:
     best_countries = None
     single_best = None
     mean_energy = None
else:
     # Minimum energy use among eligible countries
     single_best = eligible["energy_use_per_capita"].min()
     # All countries above the limit
     best_countries = eligible[eligible["energy_use_per_capita"] == single_best].copy()
     # Mean energy use among all countries above the threshold
     mean_energy = eligible["energy_use_per_capita"].mean()


# -------------------- PRINT THE RESULTS -------------------------

with col_right:
    st.subheader("Results")
    #if no data avaiable for a given threshold
    if best_countries is None or best_countries.empty:
        st.write(
             f"No country in the selected regions reaches at least "
            f"**{life_exp_target} years** of life expectancy in {year}.")
    else:
        names = ", ".join(best_countries["name"].fillna(best_countries["country_code"]))
        st.write(
            f"- **Best observed threshold** (minimum energy among countries "
            f"with life expectancy ≥ {life_exp_target} years):\n"
            f"  - {names} with **{single_best:,.0f} kWh/year per capita**.")
        st.write(
            f"- **Average energy use** among all countries above the threshold: "
             f"**{mean_energy:,.0f} kWh/year per capita** "
              f"({len(eligible)} countries)." )



# ------------- PLOT SCATTER --------------------------

fig, ax = plt.subplots(figsize=(6.5, 4)) # Dimesions
sns.scatterplot(
    data=eligible,
    x="energy_use_per_capita",
    y="life_expectancy",
    hue="region_name",
    palette=REGION_PALETTE,
    s=50, # Bubble size
    alpha=0.7, # Bubble transparency
)

# Set the graph
ax.set_xlabel("Energy consumption per capita (kWh / year)")
ax.set_ylabel("Life expectancy (years)")
ax.set_ylim(45, 85)

# --- Cobb Douglas ---
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

# --- Log Scale ---
if use_log_scale:
    ax.set_xscale("log")
    ax.set_xlim(100, 220000)   # >0, same max as before
else:
    ax.set_xlim(0, 220000)


# Vertical line for energy use mean
mean_energy = eligible["energy_use_per_capita"].mean()
ax.axvline(mean_energy, color="red", linestyle="--", linewidth=1.5, label="Energy Mean")

# Horizontal line for life expectancy mean
mean_life_expectancy = life_exp_target
ax.axhline(mean_life_expectancy, color="green", linestyle="--", linewidth=1.5, label="Threshold")


ax.set_title(f"Energy consumption threshold ({year})")
ax.grid(alpha=0.3)
ax.legend(title="Region", loc="lower right", fontsize=5)

with col_left:
    st.pyplot(fig, use_container_width=False)