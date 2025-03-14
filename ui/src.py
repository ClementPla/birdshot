import streamlit as st
import pandas as pd
from birdshot.io.files import list_patients
from birdshot.io.load import load_patient
from birdshot.io.utils import extract_visit_date_from_filepath
from ui.st_chart import plot_F30, plot_scoto
from ui.st_charts_progress import plot_f30_progression
from birdshot.analysis.engine import ERGFeatureExtractor
from birdshot.io.output import write_to_excel
import warnings

st.set_page_config(layout="wide")

warnings.simplefilter(
    action="ignore", category=(pd.errors.PerformanceWarning, RuntimeWarning)
)

inputTab, analysisTab, exportTab = st.tabs(["Input", "Inspect", "Export"])
hasStarted = False

patientsFiles = None


@st.cache_data
def st_load_patient(filepath):
    data = load_patient(filepath)
    return data


def build_export_tab(
    patientsFiles,
    f30_low_pass,
    f30_prominance,
    f30_delta,
    srod_low_pass,
    srodcone_low_pass,
    srod_time_limits,
    srodcone_time_limits,
):
    def export_fn():
        progress_text = "Operation in progress. Please wait."
        spinner = st.spinner(progress_text, show_time=True)
        data = dict()
        with spinner:
            my_bar = st.progress(0, text=progress_text)

            for i, (patient, exams) in enumerate(patientsFiles.items()):
                featex = ERGFeatureExtractor(
                    patient_files=exams,
                    plot=False,
                    verbose=False,
                    f30_low_pass=f30_low_pass,
                    f30_prominance=f30_prominance,
                    f30_delta=f30_delta,
                    scotorod_low_pass=srod_low_pass,
                    scotorod_time_limits=srod_time_limits,
                    scotorodcone_low_pass=srodcone_low_pass,
                    scotorodcone_time_limits=srodcone_time_limits,
                )
                featex.extract_all_features()
                data[patient] = featex.format_results()
                my_bar.progress(i / len(patientsFiles))
        my_bar.empty()
        write_to_excel(data, output_path="results.xlsx")
        st.success("Exported successfully")

    if patientsFiles:
        st.button("Export", on_click=export_fn)
    else:
        st.write("No patients found")


def build_plot_tab(
    visits,
    files,
    markerExtraction,
    selectExam,
    f30_low_pass,
    f30_prominance,
    f30_delta,
    srod_low_pass,
    srodcone_low_pass,
    srod_time_limits,
    srodcone_time_limits,
    scotoOptions,
):
    tabs = st.tabs(visits)
    for tab, visit in zip(tabs, files):
        with tab:
            data = st_load_patient(visit)

            match selectExam:
                case "F30":
                    plot_F30(
                        data,
                        extract_markers=markerExtraction,
                        prominance=f30_prominance,
                        delta=f30_delta,
                        filtered=f30_low_pass,
                    )
                case "Scoto":
                    plot_scoto(
                        data,
                        extract_markers=markerExtraction,
                        rodOnly=scotoOptions == "Rod Function",
                        scotorod_low_pass=srod_low_pass,
                        scotorod_time_limits=srod_time_limits,
                        scotorodcone_low_pass=srodcone_low_pass,
                        scotorodcone_time_limits=srodcone_time_limits,
                    )
                case _:
                    st.write(data)


def build_progression_tab(
    visits,
    files,
    selectExam,
    f30_low_pass,
    f30_prominance,
    f30_delta,
    srod_low_pass,
    srodcone_low_pass,
    srod_time_limits,
    srodcone_time_limits,
    scotoOptions,
):
    data = dict()
    for visit, file in zip(visits, files):
        data[visit] = st_load_patient(file)

    match selectExam:
        case "F30":
            plot_f30_progression(data, f30_low_pass, f30_prominance, f30_delta)
        case "Scoto":
            pass


def main():
    @st.cache_data
    def start(inputPath):
        return list_patients(inputPath)

    with inputTab:
        st.write("Choose the files to analyze")
        inputPath = st.text_input("Path to the folder containing the patient files")
        startButton = st.button("Start")
        if startButton:
            start(inputPath)

    patientsFiles = start(inputPath)
    f30_prominance = 10
    f30_delta = 0.4
    f30_low_pass = 150
    srod_low_pass = 75
    srodcone_low_pass = 75
    srod_time_limits = (10, 125)
    srodcone_time_limits = (10, 125)
    scotoOptions = "Rod Function"
    with analysisTab:
        if patientsFiles:
            with st.sidebar:
                markerExtraction = st.toggle("Automatic marker extraction", True)
                selectPatient = st.selectbox("Select a patient", patientsFiles.keys())
                selectExam = st.radio("Select an exam", patientsFiles[selectPatient])

                match selectExam:
                    case "F30":
                        if markerExtraction:
                            f30_low_pass = st.slider("Low pass", 0, 200, 150)
                            f30_prominance = st.slider("Prominance", 0, 20, 10)
                            f30_delta = st.slider("Delta", 0.0, 1.0, 0.4)
                    case "Scoto":
                        scotoOptions = st.radio(
                            "Select an option", ["Rod Function", "Cone + Rod Function"]
                        )
                        if markerExtraction:
                            if scotoOptions == "Rod Function":
                                srod_low_pass = st.slider("Low pass Rod", 0, 200, 75)
                                srod_time_limits = st.slider(
                                    "Time limits Rod", 0, 250, (10, 125)
                                )
                            else:
                                srodcone_low_pass = st.slider(
                                    "Low pass Cone+Rod", 0, 200, 75
                                )
                                srodcone_time_limits = st.slider(
                                    "Time limits Rod+Cone", 0, 250, (10, 125)
                                )

            if selectPatient and selectExam:
                filepath = patientsFiles[selectPatient][selectExam]
                visits = [
                    extract_visit_date_from_filepath(visit).strftime("%Y/%m/%d")
                    for visit in filepath
                ]
                tabs = st.tabs(["Visits", "Progression"])
                with tabs[0]:
                    build_plot_tab(
                        visits,
                        filepath,
                        markerExtraction,
                        selectExam,
                        f30_low_pass,
                        f30_prominance,
                        f30_delta,
                        srod_low_pass,
                        srodcone_low_pass,
                        srod_time_limits,
                        srodcone_time_limits,
                        scotoOptions,
                    )
                with tabs[1]:
                    build_progression_tab(
                        visits,
                        filepath,
                        selectExam,
                        f30_low_pass,
                        f30_prominance,
                        f30_delta,
                        srod_low_pass,
                        srodcone_low_pass,
                        srod_time_limits,
                        srodcone_time_limits,
                        scotoOptions,
                    )

        else:
            st.write("No patients found")

    with exportTab:
        build_export_tab(
            patientsFiles,
            f30_low_pass,
            f30_prominance,
            f30_delta,
            srod_low_pass,
            srodcone_low_pass,
            srod_time_limits,
            srodcone_time_limits,
        )


if __name__ == "__main__":
    main()
