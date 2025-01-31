"""File for creating a single csv file composed of all given voting data and video titles"""

import pandas as pd, tkinter as tk, numpy as np, os, csv
from tkinter import ttk, filedialog
from modules.typing import Option
from tktooltip import ToolTip


def choose_input_folder():
    path = filedialog.askdirectory(initialdir="./", title="Choose Data Source Folder", mustexist=True)
    if not path: return
    var_input_folder.set(path)


def compose():
    source_dir = var_input_folder.get()

    data: list[list] = []
    for file_name in os.listdir(source_dir):
        with open(f"{source_dir}/{file_name}", encoding="utf8") as file:
            reader = csv.reader(file)
            next(reader)
            file_data = [row for row in reader]
            data.extend(file_data)

    df = pd.DataFrame(data=data)

    if len(df.columns) == 2: # mock data
        df.columns = ["Timestamp", "Contact"]
    elif len(df.columns) == 11: # contacts removed
        df.columns = ["Timestamp"] + ["Vote"] * 10
        df["Contact"] = ""
    elif len(df.columns) == 12: # with contacts
        df.columns = ["Timestamp"] + ["Vote"] * 10 + ["Contact"]

    anonymize_contacts = options["Anonymize Contacts"]["var"].get()
    count_times_voted = options["Count Times Voted"]["var"].get()
    include_titles = options["Include Titles"]["var"].get()

    contacts = df["Contact"][df["Contact"].astype(bool)].unique()
    contact_mappings = [[f"#{voter_num}", contact] for voter_num, contact in enumerate(contacts, 1)]

    if anonymize_contacts:
        pd.DataFrame(data=contact_mappings, columns=["ID", "Contact"]).to_csv("outputs/contact_mappings.csv", index=False)
        df.replace({"Contact": {mapping[1]: mapping[0] for mapping in contact_mappings}}, inplace=True)
        contacts = [mapping[0] for mapping in contact_mappings]

    if count_times_voted:
        voter_metrics = pd.DataFrame(data={"Voter": contacts})
        voter_metrics["# Times Voted"] = voter_metrics["Voter"].map(df.groupby("Contact").size().drop(""))

        voter_metrics.to_csv("outputs/voter_metrics.csv", index=False)

    if not include_titles and "Vote" in df.columns:
        df.drop(columns="Vote", inplace=True)
    else:
        pass # TODO

    if not options["Include Contacts"]["var"].get():
        df.drop(columns="Contact", inplace=True)

    df.to_csv("outputs/composed_data.csv")


def toggle_contacts():
    if options["Include Contacts"]["var"].get():
        options["Anonymize Contacts"]["checkbox"].config(state="normal")
    else:
        options["Anonymize Contacts"]["var"].set(False)
        options["Anonymize Contacts"]["checkbox"].config(state="disabled")


root = tk.Tk()
root.title("Voting Time Analysis")

width, height = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"800x600+{int(width / 2) - 400}+{int(height / 2) - 320}")

frame_input_folder_select = tk.Frame(root)

var_input_folder = tk.StringVar(value="sample_data")

entry_input_folder = tk.Entry(frame_input_folder_select, width=20, textvariable=var_input_folder, state="readonly")
button_choose_input_folder = tk.Button(frame_input_folder_select, text="📁 choose...", command=choose_input_folder)

entry_input_folder.grid(row=0, column=0)
button_choose_input_folder.grid(row=0, column=1)

frame_options = tk.LabelFrame(root, text="Options")

var_include_contacts = tk.BooleanVar()
var_inclide_titles = tk.BooleanVar()
var_include_num_times_voted = tk.BooleanVar()

options: dict[str, Option] = {
    "Count Times Voted": {
        "tooltip": "Create a csv file with the number of times a voter had voted for the showcase"
    },
    "Include Contacts": {
        "tooltip": "Add a column voter contact info"
    },
    "Anonymize Contacts": {
        "tooltip": "Replace all contact information with a short id, and generate a separate csv mapping ids to contacts"
    },
    "Include Titles": {
        "tooltip": "Keep columns where video urls would be, except use their titles instead"
    },
}

for option, d in options.items():
    d["var"] = tk.BooleanVar()
    d["checkbox"] = ttk.Checkbutton(frame_options, text=option, variable=d["var"])
    ToolTip(d["checkbox"], msg=d["tooltip"], delay=0.1)
    d["checkbox"].pack(anchor="w")

options["Include Titles"]["checkbox"].config(state="disabled")
options["Anonymize Contacts"]["checkbox"].config(state="disabled")
options["Include Contacts"]["checkbox"].config(command=toggle_contacts)


button_compose = tk.Button(root, text="Compose", command=compose)

frame_input_folder_select.pack()
frame_options.pack()
button_compose.pack()

root.mainloop()
