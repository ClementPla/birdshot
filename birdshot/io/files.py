from pathlib import Path
from datetime import datetime


def list_patient_files(patient_directory: Path | str) -> dict[str, list]:
    """List files in a patient directory.
    returns a dictionary with 3 keys Scoto, Photo and F30.
    Each corresponding value is a list of files in the directory
    with the corresponding suffix representing a visit date.
    Order of the files is guaranteed (date is expected to be in the file name).
    """

    patient_directory = Path(patient_directory)
    files = patient_directory.glob("*.TXT")
    files_dict = {"Scoto": [], "Photo": [], "F30": []}

    for file in files:
        if "F30" in file.stem:
            files_dict["F30"].append(file)
        elif "Scoto" in file.stem:
            files_dict["Scoto"].append(file)
        elif "Photo" in file.stem:
            files_dict["Photo"].append(file)

    for key in files_dict:
        files_dict[key].sort(
            key=lambda x: datetime.strptime(
                x.stem.split(" ")[1].replace("(", "").replace(")", ""),
                "%Y.%m.%d",
            )
        )

    return files_dict


def list_patients(input_folder):
    """List all patients in a folder"""
    input_folder = Path(input_folder)
    all_patients = dict()
    for patient in input_folder.iterdir():
        if patient.is_dir():
            patient_name = patient.stem
            data = list_patient_files(patient)
            if data["F30"] or data["Scoto"] or data["Photo"]:
                all_patients[patient_name] = data
    # Sort the dict by key

    all_patients = dict(
        sorted(all_patients.items(), key=lambda x: int(x[0].split(" ")[1]))
    )

    return all_patients


def extract_date_from_file(filepath: str) -> str:
    filepath = Path(filepath)
    filename = filepath.stem
    # The date is between parentheses in the file name
    # Example: "Photo (2023.10.01) - Patient 1"

    str_date = filename.split(" ")[1]
    str_date = str_date.replace("(", "").replace(")", "")
    # Convert the string to a datetime object
    date = datetime.strptime(str_date, "%Y.%m.%d")
    return date
