from pathlib import Path
from birdshot.io.files import list_patient_files
from birdshot.io.load import load_patient
from birdshot.analysis.markers import (
    extract_f30_analysis,
    extract_scoto_rod_analysis,
    extract_scoto_rod_cone_analysis,
    extract_photo_analysis,
)
import datetime
import pandas as pd
from birdshot.io.utils import extract_visit_date_from_filepath


class ERGFeatureExtractor:
    def __init__(
        self,
        patient_folder: str | Path = None,
        patient_files: dict = None,
        plot: bool = False,
        verbose: bool = True,
        show_error: bool = False,
        f30_low_pass=150,
        f30_prominance=10,
        f30_delta=0.4,
        scotorodcone_low_pass=75,
        scotorodcone_time_limits=(10, 60),
        scotorod_low_pass=75,
        scotorod_time_limits=(10, 125),
    ):
        if patient_folder is None and patient_files is None:
            raise ValueError("Either patient_folder or patient_files must be provided")
        if patient_folder:
            self.patient_files = list_patient_files(patient_folder)
        else:
            self.patient_files = patient_files
        self.features_per_visit = dict()
        self.plot = plot
        self.verbose = verbose
        self.f30_low_pass = f30_low_pass
        self.f30_prominance = f30_prominance
        self.f30_delta = f30_delta
        self.scotorodcone_low_pass = scotorodcone_low_pass
        self.scotorodcone_time_limits = scotorodcone_time_limits
        self.scotorod_low_pass = scotorod_low_pass
        self.scotorod_time_limits = scotorod_time_limits
        self.show_error = show_error

    def extract_f30_features(self, only_date=None):
        for filepath in self.patient_files["F30"]:
            date = extract_visit_date_from_filepath(filepath)
            if only_date is not None:
                if date != only_date:
                    continue

            if date not in self.features_per_visit:
                self.features_per_visit[date] = dict()
            df = load_patient(filepath)
            try:
                od_peak_amp, os_peak_amp, od_peak_time, os_peak_time = (
                    extract_f30_analysis(
                        df,
                        filtered=self.f30_low_pass,
                        prominance=self.f30_prominance,
                        delta=self.f30_delta,
                        plot=self.plot,
                        title=filepath.stem,
                    )
                )
            except Exception as e:
                if self.verbose:
                    if self.show_error:
                        print("Failed to process F30 analysis")
                    print(filepath.stem)
                    if self.show_error:
                        print(f"With error: {e}")
                continue
            for i, (od_amp, od_time) in enumerate(zip(od_peak_amp, od_peak_time)):
                self.features_per_visit[date][f"F30_OD_amp_{i}"] = od_amp
                self.features_per_visit[date][f"F30_OD_time_{i}"] = od_time
            for i, (os_amp, os_time) in enumerate(zip(os_peak_amp, os_peak_time)):
                self.features_per_visit[date][f"F30_OS_amp_{i}"] = os_amp
                self.features_per_visit[date][f"F30_OS_time_{i}"] = os_time

    def extract_scoto_rod_features(self, only_date=None):
        for filepath in self.patient_files["Scoto"]:
            df = load_patient(filepath)
            date = extract_visit_date_from_filepath(filepath)
            if only_date is not None:
                if date != only_date:
                    continue
            if date not in self.features_per_visit:
                self.features_per_visit[date] = dict()
            try:
                Bamp, B_time_od, B_time_os = extract_scoto_rod_analysis(
                    df,
                    plot=self.plot,
                    title=f"{filepath.stem} (Rod function)",
                    filtered=self.scotorod_low_pass,
                    time_limits=self.scotorod_time_limits,
                )
            except Exception as e:
                if self.verbose:
                    if self.show_error:
                        print("Failed to process scoto rod analysis")
                    print(filepath.stem)
                    if self.show_error:
                        print(f"With error: {e}")
                continue
            self.features_per_visit[date]["Scoto_rod_B_amp_OS"] = Bamp["OS"]
            self.features_per_visit[date]["Scoto_rod_B_time_OS"] = B_time_os
            self.features_per_visit[date]["Scoto_rod_B_amp_OD"] = Bamp["OD"]
            self.features_per_visit[date]["Scoto_rod_B_time_OD"] = B_time_od

    def extract_scoto_rod_cone_features(self, only_date=None):
        for filepath in self.patient_files["Scoto"]:
            df = load_patient(filepath)
            date = extract_visit_date_from_filepath(filepath)
            if only_date is not None:
                if date != only_date:
                    continue
            if date not in self.features_per_visit:
                self.features_per_visit[date] = dict()

            try:
                B_amplitude, A_amplitude, B_time_od, A_time_od, B_time_os, A_time_os = (
                    extract_scoto_rod_cone_analysis(
                        df,
                        plot=self.plot,
                        title=f"{filepath.stem} (Rod-cone function)",
                        filtered=self.scotorodcone_low_pass,
                        time_limits=self.scotorodcone_time_limits,
                    )
                )
            except Exception as e:
                if self.verbose:
                    if self.show_error:
                        print("Failed to process scoto rod cone analysis")
                    print(filepath.stem)
                    if self.show_error:
                        print(f"With error: {e}")
                continue
            self.features_per_visit[date]["Scoto_rod_cone_B_amp_OS"] = B_amplitude["OS"]
            self.features_per_visit[date]["Scoto_rod_cone_B_time_OS"] = B_time_os
            self.features_per_visit[date]["Scoto_rod_cone_A_amp_OS"] = A_amplitude["OS"]
            self.features_per_visit[date]["Scoto_rod_cone_A_time_OS"] = A_time_os
            self.features_per_visit[date]["Scoto_rod_cone_B_amp_OD"] = B_amplitude["OD"]
            self.features_per_visit[date]["Scoto_rod_cone_B_time_OD"] = B_time_od
            self.features_per_visit[date]["Scoto_rod_cone_A_amp_OD"] = A_amplitude["OD"]
            self.features_per_visit[date]["Scoto_rod_cone_A_time_OD"] = A_time_od

    def extract_photo_features(self, only_date=None):
        for filepath in self.patient_files["Photo"]:
            df = load_patient(filepath)
            date = filepath.stem.split(" ")[1].replace("(", "").replace(")", "")
            date = datetime.datetime.strptime(date, "%Y.%m.%d").date()
            if only_date is not None:
                if date != only_date:
                    continue
            if date not in self.features_per_visit:
                self.features_per_visit[date] = dict()

            try:
                extract_photo_analysis(
                    df, plot=self.plot, title=f"{filepath.stem} (Photo function)"
                )

            except Exception as e:
                if self.verbose:
                    if self.show_error:
                        print("Failed to process photo analysis")
                    print(filepath.stem)
                    if self.show_error:
                        print(f"With error: {e}")
                continue

    def extract_all_features(self):
        self.extract_scoto_rod_cone_features()
        self.extract_scoto_rod_features()
        self.extract_f30_features()
        self.extract_photo_features()
        return self.features_per_visit

    def format_results(self):
        techniques = []
        laterality = []
        waves = []
        datatype = []

        df = pd.DataFrame.from_dict(self.features_per_visit)

        for index in df.index:
            if "OD" in index:
                laterality.append("OD")
            elif "OS" in index:
                laterality.append("OS")

            if "amp" in index:
                datatype.append("amp")
            elif "time" in index:
                datatype.append("time")

            if "F30" in index:
                techniques.append("Photopic Flicker30HZ (cone function)")
                waves.append("b-wave")

            elif "Scoto_rod_cone" in index:
                techniques.append("Scotopic (rod-cone function)")
                if "_B_" in index:
                    waves.append("b-wave")
                else:
                    waves.append("a-wave")
            else:
                techniques.append("Scotopic (rod function)")
                waves.append("b-wave")

        indices = [
            techniques,
            waves,
            laterality,
            datatype,
        ]
        df.index = pd.MultiIndex.from_arrays(
            indices, names=["Technique", "Wave", "Laterality", "Data type"]
        )
        df.sort_index()
        return df
