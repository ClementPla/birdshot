import streamlit as st
import pandas as pd
from birdshot.io.files import list_patients
from birdshot.io.utils import extract_visit_date_from_filepath
from ui.utils.builder import (
    build_export_tab,
    build_plot_tab,
    build_progression_tab,
    build_file_uploader,
    build_sidebar,
)
import warnings

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        footer {visibility: hidden;}
        #stDecoration {display:none;}
        .stAppDeployButton {display:none;}
    </style>
""",
    unsafe_allow_html=True,
)

warnings.simplefilter(
    action="ignore", category=(pd.errors.PerformanceWarning, RuntimeWarning)
)


patientsFiles = None


@st.cache_data
def start(inputPath):
    return list_patients(inputPath)


def init_params():
    st.session_state.f30_low_pass = 150
    st.session_state.f30_prominance = 10
    st.session_state.f30_delta = 0.4

    st.session_state.srod_low_pass = 75
    st.session_state.srod_time_limits = (10, 125)
    st.session_state.srodcone_low_pass = 75
    st.session_state.srodcone_time_limits = (10, 125)
    st.session_state.scotoOptions = "Rod Function"


def main():
    patientsFiles = None
    inputTab, analysisTab, exportTab = st.tabs(["Input", "Inspect", "Export"])

    with inputTab:
        st.write("Choose the files to analyze")

        patientsFiles = build_file_uploader()

    with analysisTab:
        if patientsFiles:
            init_params()
            build_sidebar(patientsFiles)

            if st.session_state.selectPatient and st.session_state.selectExam:
                filepath = patientsFiles[st.session_state.selectPatient][
                    st.session_state.selectExam
                ]
                visits = [
                    extract_visit_date_from_filepath(visit).strftime("%Y/%m/%d")
                    for visit in filepath
                ]
                tabs = st.tabs(["Visits", "Progression"])
                with tabs[0]:
                    build_plot_tab(
                        visits,
                        filepath,
                    )
                with tabs[1]:
                    build_progression_tab(
                        visits,
                        filepath,
                    )
        else:
            st.write("No patients found")

    with exportTab:
        build_export_tab(
            patientsFiles,
        )


if __name__ == "__main__":
    main()
