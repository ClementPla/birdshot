from pathlib import Path
import numpy as np

from birdshot.io.load import load_patient, get_photo_step_for_patient, extract_markers
from birdshot.io.files import list_patient_files, extract_date_from_file
from tqdm.auto import tqdm


class PatientsData:
    def __init__(self):
        self.ids = []
        self.data = []
        self.i = []
        self.b = []
        self.a = []
        self.lat = []
        self.date = []
        self.index = []
        self.time = None

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key)
        elif isinstance(key, int):
            return {
                "id": self.ids[key],
                "data": self.data[key],
                "lat": self.lat[key],
                "date": self.date[key],
                "index": self.index[key],
                "i": self.i[key],
                "b": self.b[key],
                "a": self.a[key],
            }
        else:
            raise KeyError("Key must be either a string or an integer.")

    def get_xy(self, mode="all"):
        x = self.data
        match mode:
            case "i":
                y = self.i
            case "b":
                y = self.b
            case "a":
                y = self.a
            case _:
                npoints = len(x[0])
                y = []
                for i, b, a in zip(self.i, self.b, self.a):
                    gt = np.zeros((npoints))
                    if i is not None:
                        i_index = np.searchsorted(self.time.values, i)
                        gt[i_index] = 1
                    if b is not None:
                        b_index = np.searchsorted(self.time.values, b)
                        gt[b_index] = 2
                    if a is not None:
                        a_index = np.searchsorted(self.time.values, a)
                        gt[a_index] = 3

                    y.append(gt)

        return np.array(x).squeeze(), np.array(y)


def get_patients_photopic_trainable_data(root):
    patients = PatientsData()
    root = Path(root)

    num_patients = len(list(root.glob("Patient *")))
    if num_patients == 0:
        raise ValueError("No patients found in the specified directory.")

    for i in tqdm(range(1, num_patients + 1)):
        patient = f"{i:0=3}"
        patient_filepath = Path(root) / f"Patient {patient}/"
        patients_data = list_patient_files(patient_filepath)
        for index, file in enumerate(patients_data["Photo"]):
            date = extract_date_from_file(file)
            for lat in ["OS", "OD"]:
                step = get_photo_step_for_patient(file)

                data = load_patient(file)
                patients.time = data[("", "Time (ms)")]
                x = data[(step, lat)]
                x = np.expand_dims(x, axis=1)
                try:
                    marker = extract_markers(file)
                except KeyError:
                    print(f"Failed to read markers for file {file}")
                    continue
                patients.ids.append(int(patient))
                patients.data.append(x)
                patients.lat.append(lat)
                patients.date.append(date)
                patients.index.append(index)

                for m in ["i", "a", "b"]:
                    try:
                        pt = int(marker[(step, lat, m)].iloc[0])
                        patients[m].append(pt)
                    except (KeyError, ValueError):
                        print(
                            f"Patient {patient} does not have marker {m} for {lat} eye, index {index}"
                        )
                        patients[m].append(None)

    return patients
