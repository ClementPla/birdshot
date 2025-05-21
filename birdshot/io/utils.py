import datetime


def extract_visit_date_from_filepath(filepath):
    filepath = filepath.name.split("/")[-1]
    """Extract the visit date from a file path"""
    date = filepath.split(" ")[1].replace("(", "").replace(")", "")
    date = datetime.datetime.strptime(date, "%Y.%m.%d").date()
    return date
