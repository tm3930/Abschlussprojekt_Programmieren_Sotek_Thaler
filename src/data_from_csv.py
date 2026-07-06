import pandas as pd
from pathlib import Path


def get_data_from_csv(csv_name):
    path_to_csv = Path("data") / "raw" / csv_name
    data = pd.read_csv(path_to_csv, sep=";", parse_dates=["time"]) # Semikolon als Trennzeichen; parse_dates = Zeit direkt als datetime einlesen
    return data