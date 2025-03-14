import pandas as pd
from typing import Dict


def write_to_excel(patients_data: Dict[int, pd.DataFrame], output_path: str):
    with pd.ExcelWriter(output_path) as writer:
        for patient, data in patients_data.items():
            data.to_excel(
                writer,
                sheet_name=f"Patient {patient}",
                header=[d.strftime("%Y/%m/%d") for d in data.columns.tolist()],
            )
