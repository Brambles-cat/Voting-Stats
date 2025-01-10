import tkinter as tk, calendar, pandas as pd
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data import df
from functools import reduce

calendar.month_name = calendar.month_name[1:]

available_months = df["month"].sort_values().unique()
available_month_names = [calendar.month_name[month_index] for month_index in available_months]
available_years = df["year"].unique()
available_days = df["day"].sort_values().unique()

figure = Figure(figsize=(4, 3), dpi=100)
graph = figure.add_subplot(1, 1, 1)

def render(bars=None, xlabel="", vote_sum=None):
    graph.set_xlabel(xlabel)
    graph.set_ylabel("votes")
    figure.tight_layout()

    if bars is None:
        return canvas.draw()
    
    for bar in bars:
        height = bar.get_height()
        graph.text(bar.get_x() + bar.get_width() / 2, height, height, ha="center", va="bottom")

    canvas.draw()

    if vote_sum:
        label_text.config(text=f"Total: {vote_sum}")

root = tk.Tk()
root.title("Voting Time Analysis")
width, height = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"800x600+{int(width / 2) - 400}+{int(height / 2) - 320}")

canvas = FigureCanvasTkAgg(figure, master=root)
canvas.get_tk_widget().pack(pady=10)

def get_day_range(selection: pd.DataFrame):
    days = selection["day"].sort_values().unique()
    return range(days.min(), days.max() + 1)

def count_votes(event):
    """Get the x axis label, x tick labels, and filteres voting data based on selected times in the ui"""

    time_inputs = {
        "year": int(var_year.get()) if var_year.get() != "All" else "All",
        "month": calendar.month_name.index(var_month.get()) if var_month.get() != "All" else "All",
        "day": int(var_day.get()) if var_day.get() != "All" else "All",
    }
    tick_label_getters = [
        lambda selection: selection["year"].unique(),
        lambda selection: [calendar.month_name[month][0:3] for month in selection.drop_duplicates("month")["month"].sort_values()],
        get_day_range,
    ]

    # used for narrowing down the voting data for depending on time selections
    filters = [df[t_unit] == value for t_unit, value in time_inputs.items() if value != "All"]

    if len(filters):
        merged_filter = reduce(lambda merged_filter, t_filter: merged_filter & t_filter, filters)
        selection = df[merged_filter]
    else:
        selection = df

    group_by, x_tick_labels = next(
        ((unit, label_getter(selection)) for unit, val, label_getter in zip(time_inputs.keys(), time_inputs.values(), tick_label_getters) if val == "All"),
        ("hour", [time.strftime("%I\n%p") for time in selection.drop_duplicates("hour").sort_values("hour")["datetime"]])
    )
    
    graph.clear()

    vote_counts = selection.groupby(group_by).size()

    if len(vote_counts) == 0:
        graph.text(0.5, 0.5, "No Data D:", ha="center", va="bottom")
        return render(None, group_by, len(selection))

    # different for day since some columns will be displayed as empty
    if group_by == "day":
        graph.set_xticks(x_tick_labels, x_tick_labels)
        bars = graph.bar(vote_counts.index, vote_counts.values)
    elif group_by == "hour":
        graph.set_xticks(range(len(vote_counts)), x_tick_labels)
        bars = graph.bar(range(len(vote_counts)), vote_counts.values)
    else:
        graph.set_xticks(vote_counts.index, x_tick_labels)
        bars = graph.bar(vote_counts.index, vote_counts.values)

    render(bars, group_by, len(selection))

label_text = tk.Label(root, text="Total: -")
label_text.pack(pady=(0, 20))

frame_time_options = tk.Frame(root)
frame_time_options.pack()

var_year = tk.StringVar(value="All", name="year")
var_month = tk.StringVar(value="All", name="month")
var_day = tk.StringVar(value="All", name="day")

combo_year = ttk.Combobox(frame_time_options, textvariable=var_year, values=["All", *available_years], name="year", state="readonly")
combo_month = ttk.Combobox(frame_time_options, textvariable=var_month, values=["All", *available_month_names], name="month", state="readonly")
combo_day = ttk.Combobox(frame_time_options, textvariable=var_day, values=["All", *available_days], name="day", state="readonly")

label_year = tk.Label(frame_time_options, text="Year : ")
label_month = tk.Label(frame_time_options, text="Month : ")
label_day = tk.Label(frame_time_options, text="Day : ")

combo_year.bind("<<ComboboxSelected>>", count_votes)
combo_month.bind("<<ComboboxSelected>>", count_votes)
combo_day.bind("<<ComboboxSelected>>", count_votes)

# precedence y/m/d or d/m/y
# bool display hours
# bool use weekdays instead of days

label_year.grid(row=0, column=0, sticky="e")
label_month.grid(row=1, column=0, sticky="e")
label_day.grid(row=2, column=0, sticky="e")
combo_year.grid(row=0, column=1)
combo_month.grid(row=1, column=1)
combo_day.grid(row=2, column=1)

count_votes(None)

root.mainloop()
