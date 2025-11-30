# --- Import packages ---
import wbgapi as wb
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score


class WorldDataset:
    # --- Create a dataframe with data of all countries, all years and all indicators ---
    # --- and one with meta data ---

    def __init__(self, panel: pd.DataFrame, meta: pd.DataFrame, indicators: dict):
        self.panel = panel
        self.meta = meta
        self.indicators = indicators

    # -----------------------------------------------------------------------
    # ----------------- DOWNLOAD DATA FROM WB API ---------------------------
    # -----------------------------------------------------------------------


    @classmethod
    def from_api(cls, indicators: dict, years=2021) -> "WorldDataset":
        # --- Download the chosen indicators with the WB api and build the dataframe ---

        # --- Load and clean country metadata ---
        meta = wb.economy.DataFrame()
        meta = meta.reset_index()
        meta = meta[meta["aggregate"] == False]     # Remove aggregates from metadata
        meta = meta[["id", "region", "name"]]       # Columns of meta dataframe

        # --- Download indicator data ---
        raw_df = wb.data.DataFrame(
            indicators.values(),
            time=years
        )

        # --- WB api returns a dataframe with countries and indicators as rows, 
        # and years as columns. So it needs to be reshaped as rows containing the year,
        # the country id, an indicator, and it's value ---
        
        
        # --- Reshape  ---
        tmp = raw_df.reset_index()

        long_df = tmp.melt(
            id_vars=["economy", "series"],
            var_name="year",
            value_name="value"
        )

        # --- Change indicators name with a map function --- 
        code_to_name = {v: k for k, v in indicators.items()}
        long_df["indicator_name"] = long_df["series"].map(code_to_name)

        # --- Second reshape in order to get the final version of the dataframe ---
        # --- Now the columns are: ---
        # --- |economy| |year| |gdp_per_capita| |life_expectancy| |co2_emisson| |....| ---
        panel = long_df.pivot_table(
            index=["economy", "year"],
            columns="indicator_name",
            values="value"
        ).reset_index()

        panel = panel.rename(columns={"economy": "country_code"})

        # --- Remove the aggregates from the real data---
        panel = panel[panel["country_code"].isin(meta["id"])]

        # --- Convert energy_use_per_capita from kg oil eq to kWh per capita ---
        # --- 1 kg oil equivalent = 11.63 kWh --- 
        if "energy_use_per_capita" in panel.columns:
            panel["energy_use_per_capita"] = panel["energy_use_per_capita"] * 11.63
            
            

        # --- Clean the 'year' column (remove 'YR' prefix) ---
        panel["year"] = panel["year"].astype(str)
        panel["year"] = panel["year"].str.replace("YR", "", regex=False)
        panel["year"] = panel["year"].astype(int)

        return cls(panel=panel, meta=meta, indicators=indicators)

    # -----------------------------------------------------------------------
    # ------------------------ BUILD THE SNAPSHOT ---------------------------
    # -----------------------------------------------------------------------


    def snapshot(self, year: int, dropna_cols=None) -> pd.DataFrame:
        # --- Return a dataframe for a single year ---
        
        df = self.panel[self.panel["year"] == year].copy() 
        if dropna_cols is not None:     # Removes the countries with no data
            df = df.dropna(subset=dropna_cols)
        return df


    # -----------------------------------------------------------------------
    # ----------------------- ADD REGIONS -----------------------------------
    # -----------------------------------------------------------------------


    def add_region_names(self, df: pd.DataFrame) -> pd.DataFrame:
        # --- Merge the two datadframes in one --- 
        return df.merge(
            self.meta[["id", "name", "region"]],
            left_on="country_code",
            right_on="id",
            how="left"
        )

    # -----------------------------------------------------------------------
    # ------------- MAP REGION NAME AND COLOR TO COUNTRIES ------------------ previously done in every page
    # -----------------------------------------------------------------------

    def full_snapshot(self, year: int, required=None) -> pd.DataFrame:

        # Get the basic snapshot
        snap = self.snapshot(year, dropna_cols=required)

        # Merge with metadata
        snap = snap.merge(
            self.meta,                  # your metadata (id, name, region)
            left_on="country_code",
            right_on="id",
            how="left")

        # Add readable region
        from Librarian.config import REGION_NAME_MAP
        snap["region_name"] = snap["region"].map(REGION_NAME_MAP).fillna("Other")

        return snap






class CobbDouglasFit:
    # --- Fit and represent a Cobb–Douglas relationship:

    #    Y = A * X^alpha

    # using a log–log linear regression. --- 

    def __init__(self, A: float, alpha: float, r2: float):
        # Parameters:
        
        # A : Scale parameter
        # alpha : Elasticity exponent
        # r2 : R² of the fit in log–log space
        
        self.A = A
        self.alpha = alpha
        self.r2 = r2

    @classmethod
    def fit(cls, x: pd.Series, y: pd.Series) -> "CobbDouglasFit":

        # --- Convert to numpy arrays ---
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

        # --- Drop non-positive values for log ---
        mask = (x > 0) & (y > 0)
        x = x[mask]
        y = y[mask]

        # --- Linearization ---
        x_log = np.log(x)
        y_log = np.log(y)

        # --- polyfit fits a line in log space --- 
        alpha, logA = np.polyfit(x_log, y_log, 1) 
        A = np.exp(logA)

        # --- Compute R2 in order to check if the curve fits the data --- 
        y_log_pred = np.log(A) + alpha * x_log
        r2 = r2_score(y_log, y_log_pred)

        return cls(A=A, alpha=alpha, r2=r2)

    def predict(self, x: np.ndarray) -> np.ndarray:
        # --- Predict Y values given X using the fitted Cobb–Douglas model ---

        x = np.asarray(x, dtype=float)
        return self.A * x**self.alpha

    def curve(self, x_min: float, x_max: float, n: int = 200):
        
        # --- Generate a smooth curve for plotting ---
        x_fit = np.linspace(x_min, x_max, n)
        y_fit = self.predict(x_fit)
        return x_fit, y_fit
    
    