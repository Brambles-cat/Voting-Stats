import os, csv, pandas as pd, numpy as np

base_pos = ord("A")

voter_probs = {
    chr(val + base_pos): 0.9 - val * 0.025 for val in range(26)
}

potential_voters = np.array(list(voter_probs.keys()))
probs = np.array(list(voter_probs.values()))

for file_name in os.listdir("raw data"):
    data = { "timestamp": [] }

    with open(f"raw data/{file_name}", "r") as file:
        reader = csv.reader(file)
        next(reader)
        data["timestamp"].extend(row[0] for row in reader)

    df = pd.DataFrame(data)

    rand_vals = np.random.random(size=len(voter_probs))

    voter_appearances = potential_voters[rand_vals < probs]

    df["voter"] = pd.Series(voter_appearances)
    df.to_csv(f"test data/{file_name}", index=False)
