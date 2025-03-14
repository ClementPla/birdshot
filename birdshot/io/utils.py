import datetime


def extract_visit_date_from_filepath(filepath):
    """Extract the visit date from a file path"""
    date = filepath.stem.split(" ")[1].replace("(", "").replace(")", "")
    date = datetime.datetime.strptime(date, "%Y.%m.%d").date()
    return date
