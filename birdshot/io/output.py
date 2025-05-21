import pandas as pd
from typing import Dict
import io


def write_to_excel(patients_data: Dict[int, pd.DataFrame]):
    in_memory_fp = io.BytesIO()
    with pd.ExcelWriter(in_memory_fp) as writer:
        for patient, data in patients_data.items():
            data.to_excel(
                writer,
                sheet_name=f"{patient}",
                header=[d.strftime("%Y/%m/%d") for d in data.columns.tolist()],
            )
    in_memory_fp.seek(0)
    return in_memory_fp.getvalue()
