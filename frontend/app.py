import json
import joblib
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "model" / "best_model.pkl"
METADATA_PATH = BASE_DIR / "model" / "model_metadata.json"
WQI_PATH = BASE_DIR / "data" / "processed" / "wqi_scores.csv"
REPORT_DIR = BASE_DIR / "report_images"


st.set_page_config(
    page_title="Indian Water Quality AI",
    page_icon="💧",
    layout="wide"
)


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metadata():
    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_wqi_data():
    return pd.read_csv(WQI_PATH)


def get_category(wqi):
    if wqi <= 50:
        return "Good"
    elif wqi <= 75:
        return "Poor"
    elif wqi <= 100:
        return "Very Poor"
    else:
        return "Unsuitable for Drinking"


st.title("💧 Indian Water Quality AI")
st.subheader("Water Quality Index Prediction Dashboard")

st.write(
    "Predict the Water Quality Index (WQI) using the trained "
    "Random Forest model."
)


try:
    model = load_model()
    metadata = load_metadata()
    wqi_data = load_wqi_data()
except Exception as e:
    st.error(f"Unable to load project files: {e}")
    st.stop()


st.sidebar.header("Water Quality Input")

temperature = st.sidebar.number_input(
    "Temperature",
    min_value=0.0,
    max_value=60.0,
    value=25.0,
    step=0.1
)

dissolved_oxygen = st.sidebar.number_input(
    "Dissolved Oxygen (assumed)",
    min_value=0.0,
    max_value=30.0,
    value=6.0,
    step=0.1
)

ph = st.sidebar.number_input(
    "pH",
    min_value=0.0,
    max_value=14.0,
    value=7.0,
    step=0.1
)

bod = st.sidebar.number_input(
    "BOD",
    min_value=0.0,
    max_value=100.0,
    value=3.0,
    step=0.1
)

year = st.sidebar.selectbox(
    "Year",
    [2021, 2022, 2023]
)

state = st.sidebar.selectbox(
    "State",
    sorted(wqi_data["State_Name"].dropna().unique())
)

water_body = st.sidebar.selectbox(
    "Water Body Type",
    sorted(wqi_data["Water_Body_Type"].dropna().unique())
)


input_data = pd.DataFrame(
    {
        "Temp_mean": [temperature],
        "DO_assumed_mean": [dissolved_oxygen],
        "pH_mean": [ph],
        "BOD_mean": [bod],
        "Year": [year],
        "State_Name": [state],
        "Water_Body_Type": [water_body],
    }
)


if st.button("🔍 Predict Water Quality", type="primary"):

    try:
        prediction = float(model.predict(input_data)[0])
        category = get_category(prediction)

        st.divider()

        st.header("Prediction Result")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Predicted WQI",
                f"{prediction:.2f}"
            )

        with col2:
            st.metric(
                "WQI Category",
                category
            )

        progress_value = min(max(prediction / 150, 0.0), 1.0)

        st.progress(progress_value)

        st.info(
            f"Predicted WQI for **{state}** "
            f"({water_body}, {year}) is **{prediction:.2f}**."
        )

    except Exception as e:
        st.error(f"Prediction failed: {e}")


st.divider()

st.header("📊 Project Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Raw Records",
        "194"
    )

with col2:
    st.metric(
        "WQI Records",
        "160"
    )

with col3:
    st.metric(
        "ML Stations",
        "150"
    )

with col4:
    st.metric(
        "Random Forest R²",
        "0.9513"
    )


st.divider()

st.header("📈 Analysis Visualizations")

chart_names = [
    "V01_wqi_distribution.png",
    "V02_wqi_category_counts.png",
    "V03_wqi_by_state.png",
    "V04_wqi_by_water_body_type.png",
    "V05_parameter_correlation.png",
    "V06_do_vs_bod.png",
    "V07_fc_vs_tc.png",
    "V08_missing_values.png",
    "V09_temporal_trend.png",
    "V10_top_10_polluted_stations.png",
    "V11_top_10_cleanest_stations.png",
    "V12_feature_importance.png",
    "V13_actual_vs_predicted.png",
    "V14_residuals.png",
]


for chart_name in chart_names:

    chart_path = REPORT_DIR / chart_name

    if chart_path.exists():

        st.image(
            str(chart_path),
            caption=chart_name,
            width="stretch"
        )


st.divider()

st.header("⚠️ Project Disclosures")

st.warning(
    """
1. DO_assumed_mean is based on the raw column "Dissolved" and is unverified.

2. The WQI used in this project is a modified/custom index.

3. Annual parameter values use (Min + Max) / 2 as a range-midpoint approximation.

4. The ML model uses DO, pH and BOD, which are also components of the WQI.
   Therefore, the model approximates a partial WQI formula reconstruction.

5. Stage 3 group-median imputation occurred before the ML fold split,
   leaving possible residual leakage for a small number of rows.
    """
)


st.divider()
