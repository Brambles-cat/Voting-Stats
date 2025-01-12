import tkinter as tk, calendar, pandas as pd
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from voting_data import df
from functools import reduce

calendar.month_name = calendar.month_name[1:]

available_months = df["month"].sort_values().unique()
available_month_names = [calendar.month_name[month_index] for month_index in available_months]
available_years = df["year"].unique()
available_days = df["day"].sort_values().unique()

figure = Figure(figsize=(3, 3), dpi=100)
graph = figure.add_subplot(1, 1, 1)

root = tk.Tk()
root.title("Voting Time Analysis")
width, height = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"800x600+{int(width / 2) - 400}+{int(height / 2) - 320}")

canvas = FigureCanvasTkAgg(figure, master=root)
canvas.get_tk_widget().pack(pady=10)

def ideal_fig_width(data_points: int):
    # max of 6.5 when displaying a max of 24 hour columns
    return 2.5 + 4 * (data_points - 1) / 23

def render(bars=None, xlabel="", vote_sum=None):
    # TODO filter selectable time options in count_votes() to prevent display of no data
    
    # Resizing the figure for when there are so many columns that the x labels overlap
    new_width = ideal_fig_width(len(bars)) if bars is not None else figure.get_size_inches()[0]
    figure.set_size_inches(new_width, 3)
    
    graph.set_xlabel(xlabel)
    graph.set_ylabel("votes")
    figure.tight_layout()

    if bars is not None:
        canvas.get_tk_widget().config(width=new_width * figure.dpi, height=figure.get_size_inches()[1] * figure.dpi)

    if bars is None:
        return canvas.draw()
    
    for bar in bars:
        height = bar.get_height()
        graph.text(bar.get_x() + bar.get_width() / 2, height, height, ha="center", va="bottom")

    canvas.draw()

    if vote_sum:
        label_text.config(text=f"Total: {vote_sum}")

def get_range(time_unit: str, selection: pd.DataFrame):
    values = selection[time_unit].drop_duplicates()
    return range(values.min(), values.max() + 1)

def count_votes(event=None):
    """Count votes using chosen time options and display them on a bar graph"""

    time_inputs = {
        "year": int(var_year.get()) if var_year.get() != "All" else "All",
        "month": calendar.month_name.index(var_month.get()) if var_month.get() != "All" else "All",
        "day": int(var_day.get()) if var_day.get() != "All" else "All",
    }
    tick_label_getters = [
        get_range,
        lambda time_unit, selection: [calendar.month_name[i][0:3] for i in get_range("month", selection)],
        get_range,
        lambda time_unit, selection: [time.strftime("%I\n%p") for time in selection.drop_duplicates("hour").sort_values("hour")["datetime"]]
    ]

    # used for narrowing down the voting data for depending on time selections
    filters = [df[t_unit] == value for t_unit, value in time_inputs.items() if value != "All"]

    if len(filters):
        merged_filter = reduce(lambda merged_filter, t_filter: merged_filter & t_filter, filters)
        selection = df[merged_filter]
    else:
        selection = df

    group_by = var_show_by.get().lower()
    graph.clear()

    if selection.empty:
        graph.text(0.5, 0.5, "No Data D:", ha="center", va="bottom")
        return render(None, group_by, len(selection))

    x_tick_labels = tick_label_getters[["year", "month", "day", "hour"].index(group_by)](group_by, selection)

    vote_counts = selection.groupby(group_by).size()

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

    # maybe update show by combo to have only time units where all is seleted
    # Although this would mostly prevent displaying singular columns if that's what's
    # wanted for some reason
    # combo_show_by.config(values=[*[v._name for v in [var_year, var_month, var_day] if v.get() == "All"], "Hour"])

label_text = tk.Label(root, text="Total: -")
label_text.pack(pady=(0, 20))

frame_time_options = tk.Frame(root)
frame_time_options.pack()

var_year = tk.StringVar(value="All", name="year")
var_month = tk.StringVar(value="All", name="month")
var_day = tk.StringVar(value="All", name="day")
var_use_weekdays = tk.BooleanVar(value=False)
var_show_by = tk.StringVar(value="Year")

combo_year = ttk.Combobox(frame_time_options, textvariable=var_year, values=["All", *available_years], name="year", state="readonly")
combo_month = ttk.Combobox(frame_time_options, textvariable=var_month, values=["All", *available_month_names], name="month", state="readonly")
combo_day = ttk.Combobox(frame_time_options, textvariable=var_day, values=["All", *available_days], name="day", state="readonly")
combo_show_by = ttk.Combobox(frame_time_options, textvariable=var_show_by, values=["Year", "Month", "Day", "Hour"], state="readonly")

label_year = tk.Label(frame_time_options, text="Year : ")
label_month = tk.Label(frame_time_options, text="Month : ")
label_day = tk.Label(frame_time_options, text="Day : ")
label_show_by = tk.Label(frame_time_options, text="Show by : ")

combo_year.bind("<<ComboboxSelected>>", count_votes)
combo_month.bind("<<ComboboxSelected>>", count_votes)
combo_day.bind("<<ComboboxSelected>>", count_votes)
combo_show_by.bind("<<ComboboxSelected>>", count_votes)

label_year.grid(row=0, column=0, sticky="e")
label_month.grid(row=1, column=0, sticky="e")
label_day.grid(row=2, column=0, sticky="e")
label_show_by.grid(row=3, column=0, sticky="e")
combo_year.grid(row=0, column=1)
combo_month.grid(row=1, column=1)
combo_day.grid(row=2, column=1)
combo_show_by.grid(row=3, column=1)

count_votes()

root.mainloop()
