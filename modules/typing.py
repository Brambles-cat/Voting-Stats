from tkinter import BooleanVar, Checkbutton
from typing import TypedDict

class Option(TypedDict):
    tooltip: str
    var: BooleanVar
    checkbox: Checkbutton