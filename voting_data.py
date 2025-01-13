import os, pandas as pd, csv, dotenv

#pd.set_option('display.max_rows', 100)

dotenv.load_dotenv()
data_folder = os.getenv("data_folder")

def _init_df(data_folder):
    temp_data = {"datetime": [], "voter": []}
    file_names = os.listdir(data_folder)

    for file_name in file_names:
        with open(f"{data_folder}/{file_name}", "r") as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader) 
            csv_rows = [row for row in csv_reader]

            #if headers[-1] == "voter":
            temp_data["voter"].extend([row[-1] for row in csv_rows])

            temp_data["datetime"].extend([row[0] for row in csv_rows])

    if len(temp_data["voter"]) == 0:
        del temp_data["voter"]

    temp_data = {k: pd.Series(v) for k, v in temp_data.items()}
    return pd.DataFrame(temp_data)

df = _init_df(data_folder)

df["datetime"] = pd.to_datetime(df["datetime"])

# offset the day since poll is usually opened just before the next month
df["datetime"] = df["datetime"] + pd.DateOffset(days=2)
df["day"] = df["datetime"].dt.day - 2

# offset month by 2 since months are given on a 1-12 range and voting
# occurs in the month following the file's labeled month
df["month"] = df["datetime"].dt.month - 2
df[df["month"] == -1] = 11

df["year"] = df["datetime"].dt.year
df["hour"] = df["datetime"].dt.hour

df.sort_values("datetime", inplace=True)
