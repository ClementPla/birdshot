from birdshot.analysis.markers import (
    extract_f30_analysis,
    extract_scoto_rod_analysis,
    extract_scoto_rod_cone_analysis,
)
from birdshot.io.load import load_patient, get_photo_step_for_patient


class Results:
    def __init__(
        self,
        scoto=None,
        f30=None,
        photo=None,
        age=None,
        patient=None,
        sex=None,
        index=None,
    ):
        self.scoto = scoto
        self.f30 = f30
        self.photo = photo

        self.age = int(age)
        self.patient = patient
        self.index = index
        self.sex = sex

    def __repr__(self):
        return f"Results(scoto={self.scoto}, f30={self.f30}, photo={self.photo})"


def get_normal_trials(data):
    plot = False
    all_results = []
    for patient in data:
        p = patient.split(" ")[1]
        sex = patient.split("(")[1][0]

        nfiles = len(data[patient]["Scoto"])
        years = patient.split("yrs")[0][-2:]
        for i in range(nfiles):
            result = Results(None, None, None, years, p, sex, i)
            scoto_file = data[patient]["Scoto"][i]
            laterality = []
            if "use only" in scoto_file.name:
                if "OS" in scoto_file.name:
                    laterality.append("OS")
                if "OD" in scoto_file.name:
                    laterality.append("OD")
            else:
                laterality = ["OS", "OD"]
            result.scoto = (
                extract_scoto_rod_analysis(
                    load_patient(scoto_file),
                    plot=plot,
                    filtered=False,
                    return_filtered=True,
                )
            )[-1]

            f30_file = data[patient]["F30"][i]
            result.f30 = extract_f30_analysis(
                load_patient(f30_file), plot=plot, filtered=False, return_filtered=True
            )[-1]

            photo_file = data[patient]["Photo"][i]

            try:
                photo_step = get_photo_step_for_patient(photo_file)
                trials = load_patient(photo_file)
            except (KeyError, IndexError):
                print(f"Could not load patient data {patient}")
                continue
            time = trials[("", "Time (ms)")]
            trial = trials[photo_step]
            trial["Time (ms)"] = time

            result.photo = trial
            all_results.append(result)
    return all_results
