"""File for creating a single csv file composed of all given voting data and video titles"""

import pandas as pd, tkinter as tk, numpy as np
from tkinter import ttk, filedialog
from modules.typing import Option
from modules.external import fetch, save_to_cache
from tktooltip import ToolTip
import os, csv


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
            header = next(reader)

            file_data = [row for row in reader]
            data.extend(file_data)
            
            split = [""] * len(header)
            data.append(split)

    df = pd.DataFrame(data=data)

    if len(df.columns) == 11: # contacts removed
        df.columns = ["Timestamp"] + [f"Vote {i}" for i in range(1, 11)]
        df["Contact"] = ""
    elif len(df.columns) == 12: # with contacts
        df.columns = ["Timestamp"] + [f"Vote {i}" for i in range(1, 11)] + ["Contact"]
    else:
        raise Exception("Unexpected column count in dataset")
    
    df["Range #"] = (df["Timestamp"] == "").cumsum()

    anonymize_contacts = options["Anonymize Contacts"]["var"].get()
    include_titles = options["Include Titles"]["var"].get()
    include_dates = options["Include Upload Dates"]["var"].get()
    include_uploaders = options["Include Uploaders"]["var"].get()
    include_rel_upload_time = options["Include Relative Upload Time"]["var"].get()

    contacts = df["Contact"][df["Contact"].astype(bool)].unique()
    contact_mappings = [[f"#{voter_num}", contact] for voter_num, contact in enumerate(contacts, 1)]

    if anonymize_contacts:
        pd.DataFrame(data=contact_mappings, columns=["ID", "Contact"]).to_csv("outputs/contact_mappings.csv", index=False)
        df.replace({"Contact": {mapping[1]: mapping[0] for mapping in contact_mappings}}, inplace=True)
        contacts = [mapping[0] for mapping in contact_mappings]

    if include_titles:
        for i in range(1, 11):
            df[f"Title {i}"] = df[f"Vote {i}"].apply(lambda url: fetch(url).get("title", url))
            save_to_cache()

    if include_dates:
        for i in range(1, 11):
            df[f"Date {i}"] = df[f"Vote {i}"].apply(lambda url: fetch(url).get("upload_date", ""))
            save_to_cache()
    
    if include_uploaders:
        for i in range(1, 11):
            df[f"Uploader {i}"] = df[f"Vote {i}"].apply(lambda url: fetch(url).get("uploader", ""))
            save_to_cache()
    
    if include_rel_upload_time:
        for i in range(1, 11):
            df[f"Rel Time {i}"] = df[f"Vote {i}"].apply(lambda url: fetch(url).get("upload_date", ""))
            save_to_cache()

        df[[f"Rel Time {i}" for i in range(1, 11)]] = df.groupby("Range #", group_keys=False).apply(rank_dates)

    if not options["Include Contacts"]["var"].get():
        df.drop(columns="Contact", inplace=True)

    df.drop(columns=[f"Vote {i}" for i in range(1, 11)], inplace=True)
    df.to_csv("outputs/composed_data.csv", index=False)

def rank_dates(df: pd.DataFrame):
    columns =[f"Rel Time {i}" for i in range(1, 11)]
    temp: pd.DataFrame = df[columns].replace("", pd.NaT)
    temp[columns] = temp[columns].rank(method="min")
    return temp

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
    "Include Contacts": {
        "tooltip": "Add a column voter contact info"
    },
    "Anonymize Contacts": {
        "tooltip": "Replace all contact information with a short id, and generate a separate csv mapping ids to contacts"
    },
    "Include Titles": {
        "tooltip": "Verbatim"
    },
    "Include Upload Dates": {
        "tooltip": "Verbatim"
    },
    "Include Uploaders": {
        "tooltip": "Verbatim"
    },
    "Include Relative Upload Time": {
        "tooltip": "Include order number of a video's release relative to all others in each month. 1 = Earlist video from month's data"
    }
}

for option, d in options.items():
    d["var"] = tk.BooleanVar()
    d["checkbox"] = ttk.Checkbutton(frame_options, text=option, variable=d["var"])
    ToolTip(d["checkbox"], msg=d["tooltip"], delay=0.1)
    d["checkbox"].pack(anchor="w")

options["Anonymize Contacts"]["checkbox"].config(state="disabled")
options["Include Contacts"]["checkbox"].config(command=toggle_contacts)


button_compose = tk.Button(root, text="Compose", command=compose)

frame_input_folder_select.pack()
frame_options.pack()
button_compose.pack()

root.mainloop()
