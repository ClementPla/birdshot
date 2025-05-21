import pandas as pd
import numpy as np
from pathlib import Path
import datetime
from streamlit.runtime.uploaded_file_manager import UploadedFile
from copy import deepcopy


def extract_age_and_sex(filepath):
    age = None
    sex = None
    if isinstance(filepath, UploadedFile):
        f = filepath.getvalue().decode("unicode_escape").split("\n")
        for i, line in enumerate(f):
            if line.startswith("DOB"):
                DOB = line.split("\t")[1]
                # DOB is in the format YYYY-MM-DD

                age = datetime.datetime.now().year - int(DOB.split("-")[0])
            if line.startswith("Gender"):
                sex = line.split("\t")[1][0]
    else:
        with open(filepath, "r", encoding="unicode_escape") as f:
            for i, line in enumerate(f):
                if line.startswith("DOB"):
                    DOB = line.split("\t")[1]
                    # DOB is in the format YYYY-MM-DD

                    age = datetime.datetime.now().year - int(DOB.split("-")[0])
                if line.startswith("Gender"):
                    sex = line.split("\t")[1][0]

    return age, sex


def find_data_line(filepath):
    if isinstance(filepath, UploadedFile):
        f = filepath.getvalue().decode("unicode_escape").split("\n")
        for i, line in enumerate(f):
            if line.startswith("Data Table"):
                try:
                    return int(line.split("\t")[2]) - 2
                except ValueError:
                    return i + 2
    else:
        with open(filepath, "r", encoding="unicode_escape") as f:
            for i, line in enumerate(f):
                if line.startswith("Data Table"):
                    try:
                        return int(line.split("\t")[2]) - 2
                    except ValueError:
                        return i + 2

    raise ValueError("Data line not found in file")


def find_stimulus_line(filepath):
    if isinstance(filepath, UploadedFile):
        f = filepath.getvalue().decode("unicode_escape").split("\n")
        for i, line in enumerate(f):
            if line.startswith("Stimulus Table"):
                start = int(line.split("\t")[2])
                end = int(line.split("\t")[4])
                return start - 3, end
    else:
        with open(filepath, "r", encoding="unicode_escape") as f:
            for i, line in enumerate(f):
                if line.startswith("Stimulus Table"):
                    start = int(line.split("\t")[2])
                    end = int(line.split("\t")[4])
                    return start - 3, end - 1

    raise ValueError("Stimulus line not found in file")


def find_marker_line(filepath):
    if isinstance(filepath, UploadedFile):
        f = filepath.getvalue().decode("unicode_escape").split("\n")
        for i, line in enumerate(f):
            if line.startswith("Marker Table"):
                values = line.split("\t")
                begin = int(values[2])
                end = int(values[4])
                return begin - 3, end
    else:
        with open(filepath, "r", encoding="unicode_escape") as f:
            for i, line in enumerate(f):
                if line.startswith("Marker Table"):
                    values = line.split("\t")
                    begin = int(values[2])
                    end = int(values[4])
                    return begin - 3, end

    raise ValueError("Marker line not found in file")


def load_patient(filepath):
    if isinstance(filepath, str):
        filepath = Path(filepath)

    data_line = find_data_line(filepath)
    try:
        df = pd.read_csv(
            deepcopy(filepath), sep="\t", skiprows=data_line, encoding="unicode_escape"
        )
    except pd.errors.EmptyDataError:
        df = pd.read_csv(
            deepcopy(filepath),
            sep="\t",
            skiprows=data_line + 1,
            encoding="unicode_escape",
        )

    # First columns is the trials
    trials = df[df.columns[0]]
    # Second columns is the index of each trial in the table
    indexes = df[df.columns[4]] - 1
    # Third column is the channel corresponding to the trial
    channels = df[df.columns[2]]
    ODOS_index = [1, 2]
    return extract_data(df, trials, indexes, channels, ODOS_index)


def get_photo_step_for_patient(filepath, val=5.0):
    """
    Get the step for the val (cd.s/m2) asked
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    stimulus_line_start, stimulus_line_end = find_stimulus_line(filepath)
    nrows = stimulus_line_end - stimulus_line_start

    try:
        df = pd.read_csv(
            deepcopy(filepath),
            sep="\t",
            skiprows=stimulus_line_start,
            nrows=nrows,
            encoding="unicode_escape",
        )
    except pd.errors.EmptyDataError:
        df = pd.read_csv(
            deepcopy(filepath),
            sep="\t",
            skiprows=stimulus_line_start,
            nrows=nrows + 1,
            encoding="unicode_escape",
        )
    df = df[df.columns[:3]]
    df = df[1:]
    col_intensity = df.columns[-1]
    col_step = df.columns[0]
    try:
        return int(df[df[col_intensity] == val][col_step].values[0])
    except KeyError:
        print("Failed to load the step for the value asked, returning 13")
        return 13


def extract_data(df: pd.DataFrame, trials, indexes, channels, relevant_channels):
    # We want to find the index of all channels that are relevant ie 1 and 3
    chanOD = np.where(channels == relevant_channels[0])[0]
    chanOS = np.where(channels == relevant_channels[1])[0]

    # the corresponding indexes of the relevant channels
    indexesOD = indexes[chanOD]
    indexesOS = indexes[chanOS]

    # We take the corresponding columns if the df
    dfOD = df.iloc[:, indexesOD]
    dfOS = df.iloc[:, indexesOS]

    # We rename the columns based on the trials
    trialsOD = trials[chanOD]
    trialsOS = trials[chanOS]

    multicolOD = [(int(i), "OD") for i in trialsOD]
    multicolOS = [(int(i), "OS") for i in trialsOS]

    multicol = multicolOD + multicolOS

    dfBoth = pd.concat([dfOD, dfOS], axis=1)

    dfBoth.columns = multicol
    dfBoth.columns = pd.MultiIndex.from_tuples(dfBoth.columns, names=["Step", "Eye"])

    dfBoth = dfBoth.loc[:, ~dfBoth.columns.duplicated(keep="last")]
    dfBoth = dfBoth.reindex(sorted(dfBoth.columns), axis=1)
    dfBoth = dfBoth / 1000
    dfBoth[("", "Time (ms)")] = df["Time (ms)"]
    return dfBoth


def load_gt_spreadcheet(filepath):
    excelFile = pd.ExcelFile(filepath)
    patients = {}
    for sheet in excelFile.sheet_names[1:]:
        patient = int(
            pd.read_excel(excelFile, sheet_name=sheet, header=None)
            .loc[0, 1]
            .split("Patient ")[1]
        )
        df = pd.read_excel(excelFile, sheet_name=sheet, header=1)
        indices = np.arange(len(df))
        good = indices >= 5
        df = df.loc[good]
        name_index = ["Technique", "Wave", "Laterality", "Data type"]
        indices_cols = df.columns[:4]
        data = df[df.columns[4:]]
        data = data.dropna(how="all", axis=1)
        indices_values = df[indices_cols].ffill().values

        # Remove spaces from index values
        indices_values = np.array([list(map(str.strip, row)) for row in indices_values])

        data.index = pd.MultiIndex.from_arrays(
            indices_values.transpose(), names=name_index
        )
        patients[patient] = data
    return patients


def extract_markers(filepath):
    begin, end = find_marker_line(filepath)
    df = pd.read_csv(
        filepath, sep="\t", skiprows=begin, nrows=end - begin, encoding="unicode_escape"
    )
    df = df.dropna(how="all", axis=1)
    df = df.dropna(how="all", axis=0)

    df.columns = ["Markers" if c == "Name.1" else c for c in df.columns]

    df = df[["Markers", "ms", "uV", "S", "C", "Eye", "R"]]
    df = df[df["Markers"].isin(["a", "b", "i"])]

    # Keep only the rows where the marker is either a, b or i
    # Drop the five first columns
    # Only keep the rows where R col is maximum
    idx = df[["S", "C", "Markers", "R"]].groupby(["S", "C", "Markers"]).idxmax()
    df = df.loc[idx["R"].values]
    # Replace "RE" by "OD" and "LE" by "OS"
    df["Eye"] = df["Eye"].replace({"RE": "OD", "LE": "OS"})
    df = df.drop("R", axis=1)
    df = df.drop("C", axis=1)
    df["Step"] = df["S"].astype(int)
    df = df.drop("S", axis=1)

    df = df.set_index(["Step", "Eye", "Markers"])
    return df.transpose()
