import os, csv, pandas as pd, numpy as np, dotenv

dotenv.load_dotenv()
data_folder = os.getenv("data_folder")

if not os.path.exists("mock_data"):
    os.mkdir("mock_data")

base_pos = ord("A")

voter_probs = {
    chr(val + base_pos): 0.9 - val * 0.025 for val in range(26)
}

potential_voters = np.array(list(voter_probs.keys()))
probs = np.array(list(voter_probs.values()))

for file_name in os.listdir(data_folder):
    data = []

    with open(f"{data_folder}/{file_name}", "r") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            data.append(row[:11])

    df = pd.DataFrame(data, columns=["Timestamp"] + [f"Vote {i}" for i in range(1, 11)])

    rand_vals = np.random.random(size=len(voter_probs))

    voter_appearances = potential_voters[rand_vals < probs]

    df["voter"] = pd.Series(voter_appearances)
    df.to_csv(f"mock_data/{file_name}", index=False)
