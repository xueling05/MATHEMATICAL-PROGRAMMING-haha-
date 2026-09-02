import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D


# ============================================================
# WAGNER-WHITIN ALGORITHM
# ============================================================

def wagner_whitin_backward(n, demands, setup_cost, holding_cost, variable_cost):

    future_cost = [0.0] * (n + 2)
    optimal_choices = [[] for _ in range(n + 1)]

    # Backward dynamic programming
    for start_period in range(n, 0, -1):

        minimum_cost = float("inf")
        best_end_periods = []

        for end_period in range(start_period, n + 1):

            lot_demand = sum(
                demands[start_period - 1:end_period]
            )

            current_holding_cost = 0

            for period in range(
                start_period,
                end_period + 1
            ):
                current_holding_cost += (
                    (period - start_period)
                    * demands[period - 1]
                    * holding_cost
                )

            current_variable_cost = (
                lot_demand * variable_cost
            )

            total_cost = (
                setup_cost
                + current_holding_cost
                + current_variable_cost
                + future_cost[end_period + 1]
            )

            if total_cost < minimum_cost - 1e-9:

                minimum_cost = total_cost
                best_end_periods = [end_period]

            elif abs(total_cost - minimum_cost) < 1e-9:

                best_end_periods.append(end_period)

        future_cost[start_period] = minimum_cost
        optimal_choices[start_period] = best_end_periods

    # Generate every optimal path
    optimal_paths = []

    def generate_paths(current_period, path):

        if current_period > n:
            optimal_paths.append(path.copy())
            return

        for end_period in optimal_choices[current_period]:

            path.append(
                (current_period, end_period)
            )

            generate_paths(
                end_period + 1,
                path
            )

            path.pop()

    generate_paths(1, [])

    # Use the first optimal path as the selected schedule
    produce_schedule = [0.0] * n
    produce_end_year = [0] * n

    if optimal_paths:

        first_path = optimal_paths[0]

        for start_year, end_year in first_path:

            quantity = sum(
                demands[start_year - 1:end_year]
            )

            produce_schedule[start_year - 1] = quantity
            produce_end_year[start_year - 1] = end_year

    # Cost breakdown
    total_setup_cost = 0
    total_holding_cost = 0
    total_variable_cost = 0

    for year_index in range(n):

        if produce_schedule[year_index] > 0:

            total_setup_cost += setup_cost

            total_variable_cost += (
                produce_schedule[year_index]
                * variable_cost
            )

            end_year = produce_end_year[year_index]

            for demand_index in range(
                year_index + 1,
                end_year
            ):
                total_holding_cost += (
                    (demand_index - year_index)
                    * demands[demand_index]
                    * holding_cost
                )

    total_cost = (
        total_setup_cost
        + total_holding_cost
        + total_variable_cost
    )

    return {
        "n": n,
        "demands": demands,
        "setup_cost": setup_cost,
        "holding_cost": holding_cost,
        "variable_cost": variable_cost,
        "produce_schedule": produce_schedule,
        "produce_end_year": produce_end_year,
        "total_setup_cost": total_setup_cost,
        "total_holding_cost": total_holding_cost,
        "total_variable_cost": total_variable_cost,
        "total_cost": total_cost,
        "optimal_choices": optimal_choices,
        "optimal_paths": optimal_paths
    }


# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_number(
    value,
    integer=False,
    allow_zero=True
):

    try:

        if integer:
            number = int(value)

        else:
            number = float(value)

    except ValueError:

        raise ValueError(
            "Please enter a valid numeric value."
        )

    if allow_zero:

        if number < 0:
            raise ValueError(
                "Value must be 0 or positive."
            )

    else:

        if number <= 0:
            raise ValueError(
                "Value must be greater than 0."
            )

    return number


# ============================================================
# FILE MANAGEMENT
# ============================================================

class FileManager:

    @staticmethod
    def read_input():

        filename = filedialog.askopenfilename(
            title="Open Input Data",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if not filename:
            return None

        try:

            with open(
                filename,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                rows = list(
                    csv.reader(file)
                )

            n = int(float(rows[3][1]))
            setup_cost = float(rows[4][1])
            holding_cost = float(rows[5][1])
            variable_cost = float(rows[6][1])

            demands = []

            for row in rows[9:]:

                if (
                    len(row) >= 2
                    and row[0].strip()
                ):
                    demands.append(
                        float(row[1])
                    )

            if len(demands) != n:

                raise ValueError(
                    "The number of demand values does not "
                    "match the number of years."
                )

            return (
                n,
                demands,
                setup_cost,
                holding_cost,
                variable_cost
            )

        except Exception as error:

            raise ValueError(
                f"Invalid input file:\n{error}"
            )

    @staticmethod
    def export_csv(results):

        if results is None:

            raise ValueError(
                "No calculation result available."
            )

        filename = filedialog.asksaveasfilename(
            title="Export Results to CSV",
            defaultextension=".csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if not filename:
            return False

        try:

            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "WAGNER-WHITIN OPTIMAL SOLUTIONS"
                ])

                writer.writerow([])

                writer.writerow([
                    "INPUT INFORMATION"
                ])

                writer.writerow([
                    "Number of Years",
                    results["n"]
                ])

                writer.writerow([
                    "Setup Cost",
                    results["setup_cost"]
                ])

                writer.writerow([
                    "Holding Cost",
                    results["holding_cost"]
                ])

                writer.writerow([
                    "Variable Cost",
                    results["variable_cost"]
                ])

                writer.writerow([])

                writer.writerow([
                    "DEMAND BY YEAR"
                ])

                writer.writerow([
                    "Year",
                    "Demand"
                ])

                for year in range(results["n"]):

                    writer.writerow([
                        year + 1,
                        results["demands"][year]
                    ])

                writer.writerow([])

                writer.writerow([
                    "SELECTED OPTIMAL PRODUCING PLAN"
                ])

                writer.writerow([
                    "Year",
                    "Demand",
                    "Production Quantity",
                    "Covers Until"
                ])

                for year in range(results["n"]):

                    if (
                        results["produce_schedule"][year]
                        > 0
                    ):

                        production_quantity = (
                            results["produce_schedule"][year]
                        )

                        covers_until = (
                            results["produce_end_year"][year]
                        )

                    else:

                        production_quantity = 0
                        covers_until = "-"

                    writer.writerow([
                        year + 1,
                        results["demands"][year],
                        production_quantity,
                        covers_until
                    ])

                writer.writerow([])

                writer.writerow([
                    "ALL OPTIMAL SOLUTIONS"
                ])

                writer.writerow([
                    "Solution",
                    "Producing Path",
                    "Total Optimal Cost"
                ])

                for path_number, path in enumerate(
                    results["optimal_paths"],
                    start=1
                ):

                    path_text = " → ".join(
                        f"Year {start}"
                        if start == end
                        else f"Year {start}-{end}"
                        for start, end in path
                    )

                    writer.writerow([
                        f"Solution {path_number}",
                        path_text,
                        results["total_cost"]
                    ])

                writer.writerow([])

                writer.writerow([
                    "Number of Optimal Solutions",
                    len(results["optimal_paths"])
                ])

                writer.writerow([])

                writer.writerow([
                    "COST BREAKDOWN"
                ])

                writer.writerow([
                    "Total Setup Cost",
                    results["total_setup_cost"]
                ])

                writer.writerow([
                    "Total Holding Cost",
                    results["total_holding_cost"]
                ])

                writer.writerow([
                    "Total Variable Cost",
                    results["total_variable_cost"]
                ])

                writer.writerow([
                    "TOTAL OPTIMAL COST",
                    results["total_cost"]
                ])

            return True

        except Exception as error:

            raise ValueError(
                f"Unable to export CSV file:\n{error}"
            )

    @staticmethod
    def export_report(results):

        if results is None:

            raise ValueError(
                "No calculation result available."
            )

        filename = filedialog.asksaveasfilename(
            title="Export Wagner-Whitin Report",
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )

        if not filename:
            return False

        try:

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:

                file.write("=" * 70 + "\n")
                file.write(
                    "WAGNER-WHITIN OPTIMAL SOLUTIONS\n"
                )
                file.write("=" * 70 + "\n")

                file.write(
                    "Generated: "
                    + datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    + "\n\n"
                )

                file.write("INPUT INFORMATION\n")
                file.write("-" * 70 + "\n")

                file.write(
                    f"Number of Years : "
                    f"{results['n']}\n"
                )

                file.write(
                    f"Setup Cost      : "
                    f"RM {results['setup_cost']:.2f}\n"
                )

                file.write(
                    f"Holding Cost    : "
                    f"RM {results['holding_cost']:.2f}\n"
                )

                file.write(
                    f"Variable Cost   : "
                    f"RM {results['variable_cost']:.2f}\n"
                )

                file.write("\nDEMAND BY YEAR\n")
                file.write("-" * 70 + "\n")

                for year in range(results["n"]):

                    file.write(
                        f"Year {year + 1:<3}: "
                        f"{results['demands'][year]:.0f}\n"
                    )

                file.write(
                    "\nSELECTED OPTIMAL PRODUCING PLAN\n"
                )

                file.write("-" * 70 + "\n")

                file.write(
                    f"{'Year':<10}"
                    f"{'Demand':<15}"
                    f"{'Produce Qty':<18}"
                    f"{'Covers Until':<15}\n"
                )

                file.write("-" * 70 + "\n")

                for year in range(results["n"]):

                    production_quantity = (
                        results["produce_schedule"][year]
                    )

                    if production_quantity > 0:

                        covers_until = (
                            results["produce_end_year"][year]
                        )

                    else:

                        covers_until = "-"

                    file.write(
                        f"{year + 1:<10}"
                        f"{results['demands'][year]:<15.0f}"
                        f"{production_quantity:<18.0f}"
                        f"{str(covers_until):<15}\n"
                    )

                file.write(
                    "\n\nALL OPTIMAL SOLUTIONS\n"
                )

                file.write("=" * 70 + "\n")

                file.write(
                    "Number of Optimal Solutions: "
                    f"{len(results['optimal_paths'])}\n"
                )

                file.write(
                    "Minimum Total Cost: "
                    f"RM {results['total_cost']:.2f}\n\n"
                )

                for path_number, path in enumerate(
                    results["optimal_paths"],
                    start=1
                ):

                    file.write(
                        f"OPTIMAL SOLUTION {path_number}\n"
                    )

                    file.write("-" * 50 + "\n")

                    path_text = " → ".join(
                        f"Year {start}"
                        if start == end
                        else f"Year {start}-{end}"
                        for start, end in path
                    )

                    file.write(
                        f"Producing Path: {path_text}\n"
                    )

                    file.write(
                        "Total Cost: "
                        f"RM {results['total_cost']:.2f}\n\n"
                    )

                file.write("COST BREAKDOWN\n")
                file.write("=" * 70 + "\n")

                file.write(
                    "Total Setup Cost   : "
                    f"RM {results['total_setup_cost']:.2f}\n"
                )

                file.write(
                    "Total Holding Cost : "
                    f"RM {results['total_holding_cost']:.2f}\n"
                )

                file.write(
                    "Total Variable Cost: "
                    f"RM {results['total_variable_cost']:.2f}\n"
                )

                file.write("-" * 70 + "\n")

                file.write(
                    "TOTAL OPTIMAL COST : "
                    f"RM {results['total_cost']:.2f}\n"
                )

                file.write("=" * 70 + "\n")

            return True

        except Exception as error:

            raise ValueError(
                f"Unable to export report:\n{error}"
            )


# ============================================================
# GRAPHICAL USER INTERFACE
# ============================================================

class WagnerWhitinGUI:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Wagner–Whitin Production Planner"
        )

        self.root.geometry("1280x720")
        self.root.minsize(1050, 650)

        # Comfortable professional colour palette
        self.colors = {
            "background": "#F3F5F7",
            "surface": "#FFFFFF",

            "primary": "#334E68",
            "primary_hover": "#243B53",
            "primary_soft": "#EAF0F5",

            "teal": "#3F7774",
            "teal_hover": "#315F5D",
            "teal_soft": "#EAF3F2",

            "slate": "#65788C",
            "slate_hover": "#536579",
            "slate_soft": "#EEF1F4",

            "success": "#557A6A",
            "success_hover": "#456657",
            "success_soft": "#EDF3F0",

            "danger": "#9B5C57",
            "danger_hover": "#814A46",
            "danger_soft": "#F5ECEB",

            "text": "#1F2937",
            "muted": "#667085",
            "border": "#D6DDE5",
            "table_alt": "#F7F9FB"
        }

        self.bg_color = self.colors["background"]
        self.panel_color = self.colors["surface"]
        self.primary_color = self.colors["primary"]
        self.primary_dark = self.colors["primary_hover"]
        self.success_color = self.colors["success"]
        self.text_color = self.colors["text"]
        self.border_color = self.colors["border"]

        self.root.configure(
            bg=self.bg_color
        )

        self._configure_styles()
        self.build_gui()

        self.root.bind(
            "<Control-Return>",
            lambda _event: self.calculate()
        )

        self.root.bind(
            "<F5>",
            lambda _event: self.calculate()
        )

        self.root.bind(
            "<Control-o>",
            lambda _event: self.read_input()
        )

        self.root.after_idle(
            self.period_entry.focus_set
        )

    # ========================================================
    # GUI STYLE
    # ========================================================

    def _configure_styles(self):

        style = ttk.Style(self.root)

        try:
            style.theme_use("clam")

        except tk.TclError:
            pass

        style.configure(
            "App.TFrame",
            background=self.bg_color
        )

        style.configure(
            "Card.TFrame",
            background=self.panel_color
        )

        style.configure(
            "Header.TFrame",
            background=self.colors["primary"]
        )

        style.configure(
            "Footer.TFrame",
            background=self.colors["primary_hover"]
        )

        style.configure(
            "TLabel",
            font=("Segoe UI", 10),
            foreground=self.text_color,
            background=self.panel_color
        )

        style.configure(
            "Title.TLabel",
            font=("Segoe UI Semibold", 22),
            foreground="#FFFFFF",
            background=self.colors["primary"]
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
            foreground="#DDE7F0",
            background=self.colors["primary"]
        )

        style.configure(
            "DialogTitle.TLabel",
            font=("Segoe UI Semibold", 13),
            foreground="#FFFFFF",
            background=self.colors["primary"]
        )

        style.configure(
            "DialogSubtitle.TLabel",
            font=("Segoe UI", 10),
            foreground="#DDE7F0",
            background=self.colors["primary"]
        )

        style.configure(
            "CardTitle.TLabel",
            font=("Segoe UI Semibold", 13),
            foreground=self.text_color,
            background=self.panel_color
        )

        style.configure(
            "Field.TLabel",
            font=("Segoe UI Semibold", 9),
            foreground=self.colors["muted"],
            background=self.panel_color
        )

        style.configure(
            "Hint.TLabel",
            font=("Segoe UI", 9),
            foreground=self.colors["muted"],
            background=self.panel_color
        )

        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 9),
            foreground="#FFFFFF",
            background=self.colors["primary_hover"]
        )

        style.configure(
            "TEntry",
            font=("Segoe UI", 10),
            padding=(9, 8),
            fieldbackground="#FFFFFF",
            foreground=self.text_color,
            bordercolor=self.border_color,
            lightcolor=self.border_color,
            darkcolor=self.border_color
        )

        style.map(
            "TEntry",
            bordercolor=[
                ("focus", self.colors["primary"])
            ],
            lightcolor=[
                ("focus", self.colors["primary"])
            ],
            darkcolor=[
                ("focus", self.colors["primary"])
            ]
        )

        style.configure(
            "TSpinbox",
            font=("Segoe UI", 10),
            padding=(9, 8),
            fieldbackground="#FFFFFF",
            foreground=self.text_color,
            bordercolor=self.border_color,
            arrowcolor=self.colors["primary"]
        )

        button_settings = {
            "font": ("Segoe UI Semibold", 10),
            "padding": (14, 9),
            "borderwidth": 0
        }

        def configure_button(
            style_name,
            background,
            hover
        ):

            style.configure(
                style_name,
                foreground="#FFFFFF",
                background=background,
                **button_settings
            )

            style.map(
                style_name,
                background=[
                    ("disabled", "#C4CAD3"),
                    ("pressed", hover),
                    ("active", hover)
                ],
                foreground=[
                    ("disabled", "#F4F5F7")
                ]
            )

        configure_button(
            "Primary.TButton",
            self.colors["primary"],
            self.colors["primary_hover"]
        )

        configure_button(
            "Secondary.TButton",
            self.colors["teal"],
            self.colors["teal_hover"]
        )

        configure_button(
            "Neutral.TButton",
            self.colors["slate"],
            self.colors["slate_hover"]
        )

        configure_button(
            "Success.TButton",
            self.colors["success"],
            self.colors["success_hover"]
        )

        configure_button(
            "Danger.TButton",
            self.colors["danger"],
            self.colors["danger_hover"]
        )

        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=31,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=self.text_color,
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI Semibold", 10),
            foreground="#FFFFFF",
            background=self.colors["primary"],
            padding=(10, 9),
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[
                (
                    "selected",
                    self.colors["primary_soft"]
                )
            ],
            foreground=[
                (
                    "selected",
                    self.colors["primary"]
                )
            ]
        )

        style.map(
            "Treeview.Heading",
            background=[
                (
                    "active",
                    self.colors["primary_hover"]
                )
            ]
        )

    # ========================================================
    # REUSABLE CARD
    # ========================================================

    def _card(
        self,
        parent,
        accent=None
    ):

        outer = tk.Frame(
            parent,
            bg=self.panel_color,
            highlightbackground=self.border_color,
            highlightthickness=1,
            bd=0
        )

        if accent:

            accent_bar = tk.Frame(
                outer,
                bg=accent,
                height=4
            )

            accent_bar.pack(
                side="top",
                fill="x"
            )

            accent_bar.pack_propagate(False)

        content = ttk.Frame(
            outer,
            style="Card.TFrame",
            padding=18
        )

        content.pack(
            fill="both",
            expand=True
        )

        return outer, content

    # ========================================================
    # BUILD GUI
    # ========================================================

    def build_gui(self):

        self.demand_entries = []
        self.results = None

        self.root.grid_rowconfigure(
            1,
            weight=1
        )

        self.root.grid_columnconfigure(
            0,
            weight=1
        )

        # Header
        header = ttk.Frame(
            self.root,
            style="Header.TFrame",
            padding=(24, 16)
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        header.grid_columnconfigure(
            0,
            weight=1
        )

        ttk.Label(
            header,
            text="Wagner–Whitin Production Planner",
            style="Title.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            header,
            text=(
                "Find the minimum-cost dynamic "
                "lot-size plan across multiple years."
            ),
            style="Subtitle.TLabel"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0)
        )

        ttk.Label(
            header,
            text=(
                "1  Enter costs     "
                "2  Add demand     "
                "3  Calculate"
            ),
            style="Subtitle.TLabel"
        ).grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
            padx=(24, 0)
        )

        # Main content
        main = ttk.Frame(
            self.root,
            style="App.TFrame",
            padding=(20, 18, 20, 14)
        )

        main.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        main.grid_columnconfigure(
            0,
            minsize=320
        )

        main.grid_columnconfigure(
            1,
            minsize=165
        )

        main.grid_columnconfigure(
            2,
            minsize=330,
            weight=1
        )

        main.grid_columnconfigure(
            3,
            minsize=175
        )

        # Guarantee visible space for the result table
        main.grid_rowconfigure(
            1,
            minsize=210,
            weight=1
        )

        # ====================================================
        # PLANNING INPUTS
        # ====================================================

        input_card, input_frame = self._card(
            main,
            self.colors["primary"]
        )

        input_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        ttk.Label(
            input_frame,
            text="Planning inputs",
            style="CardTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w"
        )

        ttk.Label(
            input_frame,
            text=(
                "Enter the planning horizon "
                "and cost assumptions."
            ),
            style="Hint.TLabel"
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(2, 14)
        )

        self.period_var = tk.StringVar()
        self.setup_var = tk.StringVar()
        self.holding_var = tk.StringVar()
        self.variable_var = tk.StringVar()

        ttk.Label(
            input_frame,
            text="NUMBER OF YEARS",
            style="Field.TLabel"
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w"
        )

        self.period_entry = ttk.Spinbox(
            input_frame,
            from_=1,
            to=200,
            textvariable=self.period_var,
            width=12
        )

        self.period_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(4, 11)
        )

        ttk.Button(
            input_frame,
            text="Generate fields",
            command=self.create_demands,
            style="Secondary.TButton"
        ).grid(
            row=3,
            column=1,
            sticky="ew",
            padx=(8, 0),
            pady=(4, 11)
        )

        self.period_entry.bind(
            "<Return>",
            lambda _event: self.create_demands()
        )

        self._add_cost_field(
            input_frame,
            4,
            "SETUP COST",
            self.setup_var,
            "RM per production run"
        )

        self.setup_entry = self._last_cost_entry

        self._add_cost_field(
            input_frame,
            6,
            "HOLDING COST",
            self.holding_var,
            "RM per unit per year"
        )

        self.holding_entry = self._last_cost_entry

        self._add_cost_field(
            input_frame,
            8,
            "VARIABLE COST",
            self.variable_var,
            "RM per unit produced"
        )

        self.variable_entry = self._last_cost_entry

        input_frame.grid_columnconfigure(
            0,
            weight=1
        )

        input_frame.grid_columnconfigure(
            1,
            weight=1
        )

        # ====================================================
        # FUNCTION BUTTONS
        # ====================================================

        function_card, function_frame = self._card(
            main,
            self.colors["slate"]
        )

        function_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(0, 10)
        )

        function_frame.grid_columnconfigure(
            0,
            weight=1
        )

        function_frame.grid_rowconfigure(
            7,
            weight=1
        )

        ttk.Label(
            function_frame,
            text="Functions",
            style="CardTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            function_frame,
            text="Calculate and manage files.",
            style="Hint.TLabel",
            wraplength=130
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 12)
        )

        ttk.Button(
            function_frame,
            text="Calculate plan",
            command=self.calculate,
            style="Primary.TButton"
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 5)
        )

        ttk.Button(
            function_frame,
            text="Open CSV",
            command=self.read_input,
            style="Secondary.TButton"
        ).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=5
        )

        self.export_csv_button = ttk.Button(
            function_frame,
            text="Export CSV",
            command=self.export_csv,
            style="Success.TButton",
            state="disabled"
        )

        self.export_csv_button.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=5
        )

        self.export_report_button = ttk.Button(
            function_frame,
            text="Export report",
            command=self.export_report,
            style="Neutral.TButton",
            state="disabled"
        )

        self.export_report_button.grid(
            row=5,
            column=0,
            sticky="ew",
            pady=5
        )

        ttk.Button(
            function_frame,
            text="Clear inputs",
            command=self.clear,
            style="Danger.TButton"
        ).grid(
            row=8,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        # ====================================================
        # DEMAND SCHEDULE
        # ====================================================

        demand_card, demand_frame = self._card(
            main,
            self.colors["teal"]
        )

        # nsew removes the empty space below the card
        demand_card.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=(0, 10)
        )

        demand_frame.grid_columnconfigure(
            0,
            weight=1
        )

        # Allow the demand canvas to fill the card vertically
        demand_frame.grid_rowconfigure(
            2,
            weight=1
        )

        ttk.Label(
            demand_frame,
            text="Demand schedule",
            style="CardTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.demand_count_label = ttk.Label(
            demand_frame,
            text=(
                "Set the number of years, then "
                "generate the demand fields."
            ),
            style="Hint.TLabel"
        )

        self.demand_count_label.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 10)
        )

        demand_body = ttk.Frame(
            demand_frame,
            style="Card.TFrame"
        )

        demand_body.grid(
            row=2,
            column=0,
            sticky="nsew"
        )

        demand_body.grid_rowconfigure(
            0,
            weight=1
        )

        demand_body.grid_columnconfigure(
            0,
            weight=1
        )

        self.demand_canvas = tk.Canvas(
            demand_body,
            bg=self.panel_color,
            bd=0,
            highlightthickness=0,
            height=190
        )

        demand_scrollbar = ttk.Scrollbar(
            demand_body,
            orient="vertical",
            command=self.demand_canvas.yview
        )

        self.demand_canvas.configure(
            yscrollcommand=demand_scrollbar.set
        )

        self.demand_canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        demand_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.demand_input_frame = ttk.Frame(
            self.demand_canvas,
            style="Card.TFrame"
        )

        self._demand_window = (
            self.demand_canvas.create_window(
                (0, 0),
                window=self.demand_input_frame,
                anchor="nw"
            )
        )

        self.demand_input_frame.bind(
            "<Configure>",
            lambda _event: (
                self.demand_canvas.configure(
                    scrollregion=(
                        self.demand_canvas.bbox("all")
                    )
                )
            )
        )

        self.demand_canvas.bind(
            "<Configure>",
            lambda event: (
                self.demand_canvas.itemconfigure(
                    self._demand_window,
                    width=event.width
                )
            )
        )

        self.demand_canvas.bind(
            "<Enter>",
            lambda _event: (
                self.demand_canvas.bind_all(
                    "<MouseWheel>",
                    self._scroll_demands
                )
            )
        )

        self.demand_canvas.bind(
            "<Leave>",
            lambda _event: (
                self.demand_canvas.unbind_all(
                    "<MouseWheel>"
                )
            )
        )

        # ====================================================
        # VISUAL TOOLS
        # ====================================================

        visual_card, visual_frame = self._card(
            main,
            self.colors["slate"]
        )

        # nsew removes the empty space below the card
        visual_card.grid(
            row=0,
            column=3,
            sticky="nsew"
        )

        visual_frame.grid_columnconfigure(
            0,
            weight=1
        )

        # Distribute the visual buttons evenly
        visual_frame.grid_rowconfigure(
            2,
            weight=1,
            uniform="visual_buttons"
        )

        visual_frame.grid_rowconfigure(
            3,
            weight=1,
            uniform="visual_buttons"
        )

        visual_frame.grid_rowconfigure(
            4,
            weight=1,
            uniform="visual_buttons"
        )

        ttk.Label(
            visual_frame,
            text="Visual tools",
            style="CardTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            visual_frame,
            text="Explore the calculated plan.",
            style="Hint.TLabel",
            wraplength=140
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 12)
        )

        self.paths_button = ttk.Button(
            visual_frame,
            text="View plans",
            command=self.show_optimal_paths,
            style="Neutral.TButton",
            state="disabled"
        )

        self.paths_button.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=6
        )

        self.trend_button = ttk.Button(
            visual_frame,
            text="Demand chart",
            command=self.show_demand_trend,
            style="Secondary.TButton",
            state="disabled"
        )

        self.trend_button.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=6
        )

        self.flow_button = ttk.Button(
            visual_frame,
            text="Network diagram",
            command=self.show_network_flow,
            style="Neutral.TButton",
            state="disabled"
        )

        self.flow_button.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=6
        )

        # ====================================================
        # OPTIMAL PRODUCTION PLAN
        # ====================================================

        result_card, result_frame = self._card(
            main,
            self.colors["primary"]
        )

        result_card.grid(
            row=1,
            column=0,
            columnspan=4,
            sticky="nsew",
            pady=(12, 0)
        )

        result_frame.grid_columnconfigure(
            0,
            weight=1
        )

        result_frame.grid_rowconfigure(
            3,
            weight=1
        )

        ttk.Label(
            result_frame,
            text="Optimal production plan",
            style="CardTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            result_frame,
            text=(
                "All production paths that achieve "
                "the same minimum total cost."
            ),
            style="Hint.TLabel"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 12)
        )

        # Summary metrics
        metrics_frame = ttk.Frame(
            result_frame,
            style="Card.TFrame"
        )

        metrics_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 12)
        )

        self.metric_values = {}

        metric_definitions = (
            (
                "solutions",
                "OPTIMAL SOLUTIONS",
                "0",
                self.colors["primary"],
                self.colors["primary_soft"]
            ),
            (
                "setup",
                "SETUP COST",
                "RM 0.00",
                self.colors["slate"],
                self.colors["slate_soft"]
            ),
            (
                "holding",
                "HOLDING COST",
                "RM 0.00",
                self.colors["teal"],
                self.colors["teal_soft"]
            ),
            (
                "variable",
                "VARIABLE COST",
                "RM 0.00",
                self.colors["slate"],
                self.colors["slate_soft"]
            ),
            (
                "total",
                "MINIMUM TOTAL COST",
                "RM 0.00",
                self.colors["success"],
                self.colors["success_soft"]
            )
        )

        for column, (
            key,
            label,
            value,
            accent_color,
            background_color
        ) in enumerate(metric_definitions):

            metrics_frame.grid_columnconfigure(
                column,
                weight=1
            )

            metric_box = tk.Frame(
                metrics_frame,
                bg=background_color,
                highlightbackground=accent_color,
                highlightthickness=1,
                padx=13,
                pady=10
            )

            metric_box.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(
                    0 if column == 0 else 4,
                    0 if column == 4 else 4
                )
            )

            tk.Label(
                metric_box,
                text=label,
                font=("Segoe UI Semibold", 9),
                foreground=accent_color,
                background=background_color
            ).pack(
                anchor="w"
            )

            value_label = tk.Label(
                metric_box,
                text=value,
                font=("Segoe UI Semibold", 15),
                foreground=accent_color,
                background=background_color
            )

            value_label.pack(
                anchor="w",
                pady=(3, 0)
            )

            self.metric_values[key] = value_label

        # Result table
        columns = (
            "Solution",
            "Year",
            "Demand",
            "Production Quantity",
            "Coverage"
        )

        table_holder = ttk.Frame(
            result_frame,
            style="Card.TFrame"
        )

        table_holder.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        table_holder.grid_rowconfigure(
            0,
            weight=1
        )

        table_holder.grid_columnconfigure(
            0,
            weight=1
        )

        self.table = ttk.Treeview(
            table_holder,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=5
        )

        headings = {
            "Solution": (
                "Solution",
                130
            ),
            "Year": (
                "Year",
                80
            ),
            "Demand": (
                "Demand (units)",
                145
            ),
            "Production Quantity": (
                "Production quantity",
                180
            ),
            "Coverage": (
                "Covers through",
                145
            )
        }

        for column in columns:

            heading_text, width = (
                headings[column]
            )

            self.table.heading(
                column,
                text=heading_text
            )

            self.table.column(
                column,
                anchor="center",
                width=width,
                minwidth=80
            )

        table_scroll_y = ttk.Scrollbar(
            table_holder,
            orient="vertical",
            command=self.table.yview
        )

        table_scroll_x = ttk.Scrollbar(
            table_holder,
            orient="horizontal",
            command=self.table.xview
        )

        self.table.configure(
            yscrollcommand=table_scroll_y.set,
            xscrollcommand=table_scroll_x.set
        )

        self.table.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        table_scroll_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        table_scroll_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.table.tag_configure(
            "even",
            background="#FFFFFF"
        )

        self.table.tag_configure(
            "odd",
            background=self.colors["table_alt"]
        )

        self.table.tag_configure(
            "production",
            foreground=self.colors["primary"],
            font=("Segoe UI Semibold", 10)
        )

        self.table.tag_configure(
            "separator",
            background=self.colors["primary_soft"]
        )

        # Status bar
        status_bar = ttk.Frame(
            self.root,
            style="Footer.TFrame",
            padding=(20, 8)
        )

        status_bar.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        status_bar.grid_columnconfigure(
            0,
            weight=1
        )

        self.status = ttk.Label(
            status_bar,
            text="Ready.",
            style="Status.TLabel"
        )

        self.status.grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            status_bar,
            text=(
                "Tip: Ctrl+Enter calculates "
                "· Ctrl+O opens a CSV"
            ),
            style="Status.TLabel"
        ).grid(
            row=0,
            column=1,
            sticky="e"
        )

        self.cost_label = (
            self.metric_values["total"]
        )

    # ========================================================
    # INPUT FIELD HELPERS
    # ========================================================

    def _add_cost_field(
        self,
        parent,
        row,
        label,
        variable,
        hint
    ):

        ttk.Label(
            parent,
            text=f"{label}  ·  {hint}",
            style="Field.TLabel"
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w"
        )

        field_row = ttk.Frame(
            parent,
            style="Card.TFrame"
        )

        field_row.grid(
            row=row + 1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(4, 9)
        )

        field_row.grid_columnconfigure(
            1,
            weight=1
        )

        ttk.Label(
            field_row,
            text="RM",
            style="Hint.TLabel"
        ).grid(
            row=0,
            column=0,
            padx=(0, 8)
        )

        entry = ttk.Entry(
            field_row,
            textvariable=variable
        )

        entry.grid(
            row=0,
            column=1,
            sticky="ew"
        )

        self._last_cost_entry = entry

    def _scroll_demands(self, event):

        if event.delta > 0:
            direction = -1

        else:
            direction = 1

        self.demand_canvas.yview_scroll(
            direction,
            "units"
        )

    def _set_result_actions(
        self,
        enabled
    ):

        state = (
            "normal"
            if enabled
            else "disabled"
        )

        for button in (
            self.export_csv_button,
            self.export_report_button,
            self.paths_button,
            self.trend_button,
            self.flow_button
        ):
            button.configure(
                state=state
            )

    # ========================================================
    # CREATE DEMAND FIELDS
    # ========================================================

    def create_demands(self):

        for widget in (
            self.demand_input_frame.winfo_children()
        ):
            widget.destroy()

        self.demand_entries = []

        try:

            n = validate_number(
                self.period_entry.get(),
                integer=True,
                allow_zero=False
            )

        except ValueError as error:

            messagebox.showerror(
                "Input Error",
                str(error)
            )

            return

        if n > 200:

            messagebox.showerror(
                "Input Error",
                "Number of years cannot exceed 200."
            )

            return

        number_of_columns = 4

        for column in range(
            number_of_columns
        ):

            self.demand_input_frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="demand"
            )

        for index in range(n):

            row = index // number_of_columns
            column = index % number_of_columns

            cell = ttk.Frame(
                self.demand_input_frame,
                style="Card.TFrame",
                padding=(0, 0, 10, 10)
            )

            cell.grid(
                row=row,
                column=column,
                sticky="ew"
            )

            cell.grid_columnconfigure(
                0,
                weight=1
            )

            ttk.Label(
                cell,
                text=f"YEAR {index + 1}",
                style="Field.TLabel"
            ).grid(
                row=0,
                column=0,
                sticky="w",
                pady=(0, 3)
            )

            entry = ttk.Entry(cell)

            entry.grid(
                row=1,
                column=0,
                sticky="ew"
            )

            self.demand_entries.append(
                entry
            )

        self.demand_count_label.config(
            text=(
                f"{n} demand "
                f"value{'s' if n != 1 else ''} "
                "required. Values may be zero."
            )
        )

        self.demand_canvas.yview_moveto(0)

        if self.demand_entries:

            self.demand_entries[0].focus_set()

        self.status.config(
            text=(
                f"Demand fields generated "
                f"for {n} years."
            )
        )

    # ========================================================
    # GET INPUTS
    # ========================================================

    def get_inputs(self):

        n = validate_number(
            self.period_entry.get(),
            integer=True,
            allow_zero=False
        )

        setup_cost = validate_number(
            self.setup_entry.get(),
            allow_zero=False
        )

        holding_cost = validate_number(
            self.holding_entry.get(),
            allow_zero=False
        )

        variable_cost = validate_number(
            self.variable_entry.get(),
            allow_zero=False
        )

        if len(self.demand_entries) != n:

            raise ValueError(
                "Generate the demand fields for the "
                "selected number of years first."
            )

        demands = []

        for year, entry in enumerate(
            self.demand_entries,
            start=1
        ):

            try:

                demand = validate_number(
                    entry.get(),
                    allow_zero=True
                )

            except ValueError as error:

                entry.focus_set()

                raise ValueError(
                    f"Year {year} demand: {error}"
                ) from error

            demands.append(demand)

        return (
            n,
            demands,
            setup_cost,
            holding_cost,
            variable_cost
        )

    # ========================================================
    # CALCULATE
    # ========================================================

    def calculate(self):

        try:

            (
                n,
                demands,
                setup_cost,
                holding_cost,
                variable_cost
            ) = self.get_inputs()

            self.status.config(
                text=(
                    "Calculating the optimal "
                    "production plan..."
                )
            )

            self.root.update_idletasks()

            self.results = (
                wagner_whitin_backward(
                    n,
                    demands,
                    setup_cost,
                    holding_cost,
                    variable_cost
                )
            )

            self.display_results()
            self._set_result_actions(True)

        except Exception as error:

            messagebox.showerror(
                "Calculation Error",
                str(error)
            )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    def display_results(self):

        for item in self.table.get_children():

            self.table.delete(item)

        optimal_paths = (
            self.results["optimal_paths"]
        )

        demands = self.results["demands"]
        total_cost = self.results["total_cost"]
        path_count = len(optimal_paths)

        row_number = 0

        for path_number, path in enumerate(
            optimal_paths,
            start=1
        ):

            production_quantities = (
                [0.0] * len(demands)
            )

            production_end_years = (
                [0] * len(demands)
            )

            for start_year, end_year in path:

                quantity = sum(
                    demands[
                        start_year - 1:end_year
                    ]
                )

                production_quantities[
                    start_year - 1
                ] = quantity

                production_end_years[
                    start_year - 1
                ] = end_year

            for year in range(
                1,
                len(demands) + 1
            ):

                production_quantity = (
                    production_quantities[
                        year - 1
                    ]
                )

                if production_quantity > 0:

                    production_text = (
                        f"{production_quantity:,.0f}"
                    )

                    end_year = (
                        production_end_years[
                            year - 1
                        ]
                    )

                    covers_until = (
                        f"Year {end_year}"
                    )

                else:

                    production_text = "—"
                    covers_until = "—"

                base_tag = (
                    "even"
                    if row_number % 2 == 0
                    else "odd"
                )

                if production_quantity > 0:

                    tags = (
                        base_tag,
                        "production"
                    )

                else:

                    tags = (base_tag,)

                self.table.insert(
                    "",
                    "end",
                    values=(
                        (
                            f"Plan {path_number}"
                            if year == 1
                            else ""
                        ),
                        year,
                        f"{demands[year - 1]:,.0f}",
                        production_text,
                        covers_until
                    ),
                    tags=tags
                )

                row_number += 1

            if path_number < path_count:

                self.table.insert(
                    "",
                    "end",
                    values=(
                        "",
                        "",
                        "",
                        "",
                        ""
                    ),
                    tags=("separator",)
                )

                row_number += 1

        self.metric_values[
            "solutions"
        ].config(
            text=str(path_count)
        )

        self.metric_values[
            "setup"
        ].config(
            text=(
                "RM "
                f"{self.results['total_setup_cost']:,.2f}"
            )
        )

        self.metric_values[
            "holding"
        ].config(
            text=(
                "RM "
                f"{self.results['total_holding_cost']:,.2f}"
            )
        )

        self.metric_values[
            "variable"
        ].config(
            text=(
                "RM "
                f"{self.results['total_variable_cost']:,.2f}"
            )
        )

        self.metric_values[
            "total"
        ].config(
            text=f"RM {total_cost:,.2f}"
        )

        self.status.config(
            text=(
                f"Calculation complete — "
                f"{path_count} optimal plan(s) "
                f"found at RM {total_cost:,.2f}."
            )
        )

    # ========================================================
    # READ INPUT
    # ========================================================

    def read_input(self):

        try:

            data = FileManager.read_input()

            if data is None:
                return

            (
                n,
                demands,
                setup_cost,
                holding_cost,
                variable_cost
            ) = data

            self.period_var.set(str(n))
            self.setup_var.set(str(setup_cost))
            self.holding_var.set(str(holding_cost))
            self.variable_var.set(str(variable_cost))

            self.create_demands()

            for index in range(n):

                self.demand_entries[
                    index
                ].insert(
                    0,
                    str(demands[index])
                )

            self.status.config(
                text="Input file loaded successfully."
            )

            messagebox.showinfo(
                "Input Loaded",
                "The CSV data is ready to calculate."
            )

        except Exception as error:

            messagebox.showerror(
                "Read Error",
                str(error)
            )

    # ========================================================
    # EXPORT FUNCTIONS
    # ========================================================

    def export_csv(self):

        if self.results is None:

            messagebox.showwarning(
                "No Results",
                "Calculate a production plan first."
            )

            return

        try:

            success = FileManager.export_csv(
                self.results
            )

            if success:

                messagebox.showinfo(
                    "Export Complete",
                    "Results were exported to CSV."
                )

                self.status.config(
                    text="Results exported to CSV."
                )

        except Exception as error:

            messagebox.showerror(
                "Export Error",
                str(error)
            )

    def export_report(self):

        if self.results is None:

            messagebox.showwarning(
                "No Results",
                "Calculate a production plan first."
            )

            return

        try:

            success = FileManager.export_report(
                self.results
            )

            if success:

                messagebox.showinfo(
                    "Export Complete",
                    "The text report was exported."
                )

                self.status.config(
                    text="Report exported."
                )

        except Exception as error:

            messagebox.showerror(
                "Export Error",
                str(error)
            )

    # ========================================================
    # DEMAND TREND GRAPH
    # ========================================================

    def show_demand_trend(self):

        if self.results is None:

            messagebox.showwarning(
                "No Results",
                "Calculate a production plan first."
            )

            return

        graph_window = tk.Toplevel(
            self.root
        )

        graph_window.title(
            "Demand Trend · Wagner–Whitin Planner"
        )

        graph_window.geometry("850x600")
        graph_window.minsize(680, 460)

        graph_window.configure(
            bg=self.bg_color
        )

        years = list(
            range(
                1,
                self.results["n"] + 1
            )
        )

        demands = self.results["demands"]

        figure = Figure(
            figsize=(8, 5),
            dpi=100,
            facecolor=self.panel_color
        )

        axis = figure.add_subplot(111)

        axis.plot(
            years,
            demands,
            marker="o",
            linewidth=2.5,
            markersize=7,
            color=self.colors["primary"],
            markerfacecolor="#FFFFFF",
            markeredgewidth=2
        )

        axis.set_title(
            "Demand by Year",
            fontsize=17,
            fontweight="bold",
            color=self.text_color,
            pad=18
        )

        axis.set_xlabel(
            "Year",
            fontsize=11,
            color=self.colors["muted"]
        )

        axis.set_ylabel(
            "Demand (units)",
            fontsize=11,
            color=self.colors["muted"]
        )

        axis.set_xticks(years)

        axis.grid(
            True,
            linestyle="--",
            alpha=0.25
        )

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        for year, demand in zip(
            years,
            demands
        ):

            axis.annotate(
                f"{demand:,.0f}",
                (year, demand),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                color=self.colors["muted"]
            )

        figure.tight_layout()

        canvas = FigureCanvasTkAgg(
            figure,
            master=graph_window
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

    # ========================================================
    # NETWORK FLOW DIAGRAM
    # ========================================================

    def show_network_flow(self):

        if self.results is None:

            messagebox.showwarning(
                "No Results",
                "Calculate a production plan first."
            )

            return

        n = self.results["n"]
        demands = self.results["demands"]
        optimal_paths = self.results["optimal_paths"]
        total_cost = self.results["total_cost"]

        if not optimal_paths:

            messagebox.showwarning(
                "No Optimal Path",
                "No optimal path was found."
            )

            return

        flow_window = tk.Toplevel(
            self.root
        )

        flow_window.title(
            "Optimal Network Paths · "
            "Wagner–Whitin Planner"
        )

        flow_window.geometry("1350x800")
        flow_window.minsize(900, 600)

        flow_window.configure(
            bg=self.bg_color
        )

        figure = Figure(
            figsize=(13, 7.5),
            dpi=100,
            facecolor=self.panel_color
        )

        axis = figure.add_subplot(111)

        node_count = n + 1
        x_positions = list(
            range(1, node_count + 1)
        )

        y_position = 0

        # Draw nodes
        axis.scatter(
            x_positions,
            [y_position] * node_count,
            s=920,
            color=self.colors["primary"],
            edgecolor="#FFFFFF",
            linewidth=2,
            zorder=5
        )

        for node in range(1, n + 1):

            axis.text(
                node,
                y_position,
                f"Y{node}",
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color="white",
                zorder=6
            )

        axis.text(
            n + 1,
            y_position,
            "END",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
            zorder=6
        )

        # Demand labels
        for year in range(1, n + 1):

            axis.text(
                year,
                -2.2,
                f"{demands[year - 1]:,.0f} units",
                ha="center",
                va="top",
                fontsize=9,
                color=self.colors["muted"]
            )

        # Draw every possible production decision in gray
        for start in range(1, n + 1):

            for end in range(
                start + 1,
                n + 2
            ):

                distance = end - start

                arc_height = (
                    0.20
                    + distance * 0.08
                )

                axis.annotate(
                    "",
                    xy=(end, 0),
                    xytext=(start, 0),
                    arrowprops=dict(
                        arrowstyle="->",
                        linewidth=1.2,
                        alpha=0.22,
                        color=self.colors["muted"],
                        connectionstyle=(
                            f"arc3,rad=-{arc_height}"
                        )
                    ),
                    zorder=1
                )

        # Professional muted colours for optimal paths
        path_palette = (
            "#334E68",
            "#3F7774",
            "#65788C",
            "#557A6A",
            "#8A744F",
            "#765E73"
        )

        path_count = len(optimal_paths)
        path_spacing = 0.10

        # Draw optimal production paths
        for path_index, path in enumerate(
            optimal_paths,
            start=1
        ):

            if path_count == 1:

                path_offset = 0

            else:

                path_offset = (
                    (
                        (path_index - 1)
                        - (path_count - 1) / 2
                    )
                    * path_spacing
                )

            path_color = path_palette[
                (path_index - 1)
                % len(path_palette)
            ]

            for start_year, end_year in path:

                network_start = start_year
                network_end = end_year + 1

                distance = (
                    network_end
                    - network_start
                )

                arc_height = (
                    0.25
                    + distance * 0.10
                    + path_offset
                )

                axis.annotate(
                    "",
                    xy=(network_end, 0),
                    xytext=(network_start, 0),
                    arrowprops=dict(
                        arrowstyle="->",
                        linewidth=3,
                        alpha=0.92,
                        color=path_color,
                        connectionstyle=(
                            f"arc3,rad=-{arc_height}"
                        )
                    ),
                    zorder=4
                )

        axis.set_title(
            "Optimal Production Network",
            fontsize=17,
            fontweight="bold",
            color=self.text_color,
            pad=25
        )

        axis.set_xlabel(
            "Planning period",
            fontsize=10,
            color=self.colors["muted"]
        )

        axis.set_xlim(
            0.5,
            n + 1.5
        )

        axis.set_xticks(
            x_positions
        )

        maximum_height = (
            0.25
            + n * 0.10
            + abs(
                path_spacing * path_count
            )
            + 1.0
        )

        axis.set_ylim(
            -2.5,
            maximum_height
        )

        axis.set_yticks([])

        axis.grid(
            axis="x",
            linestyle="--",
            alpha=0.25
        )

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_visible(False)

        # Explicit network line legend
        network_legend = [
            Line2D(
                [0],
                [0],
                color=self.colors["muted"],
                linewidth=2,
                alpha=0.50,
                label=(
                    "Gray arcs: all possible "
                    "production decisions"
                )
            ),
            Line2D(
                [0],
                [0],
                color=self.colors["primary"],
                linewidth=3,
                label=(
                    "Colored arcs: optimal "
                    "production decisions"
                )
            )
        ]

        axis.legend(
            handles=network_legend,
            loc="upper right",
            fontsize=9,
            frameon=True,
            facecolor="white",
            edgecolor=self.border_color,
            framealpha=0.95
        )

        # Optimal path information box
        path_lines = []

        for path_number, path in enumerate(
            optimal_paths,
            start=1
        ):

            path_text = " → ".join(
                (
                    f"Y{start}"
                    if start == end
                    else f"Y{start}-Y{end}"
                )
                for start, end in path
            )

            if path:
                path_text += " → END"

            path_lines.append(
                f"Plan {path_number}: {path_text}"
            )

        summary = (
            "OPTIMAL PRODUCTION PATHS\n\n"
            + "\n".join(path_lines[:8])
            + (
                f"\n… and {path_count - 8} more"
                if path_count > 8
                else ""
            )
            + (
                "\n\nMinimum cost: "
                f"RM {total_cost:,.2f}"
            )
        )

        axis.text(
            0.02,
            0.97,
            summary,
            transform=axis.transAxes,
            fontsize=9,
            verticalalignment="top",
            color=self.text_color,
            bbox=dict(
                boxstyle="round,pad=0.8",
                facecolor="white",
                edgecolor=self.border_color,
                alpha=0.96
            )
        )

        figure.tight_layout()

        canvas = FigureCanvasTkAgg(
            figure,
            master=flow_window
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

    # ========================================================
    # SHOW OPTIMAL PLANS
    # ========================================================

    def show_optimal_paths(self):

        if self.results is None:

            messagebox.showwarning(
                "No Results",
                "Calculate a production plan first."
            )

            return

        paths = self.results["optimal_paths"]
        demands = self.results["demands"]

        path_window = tk.Toplevel(
            self.root
        )

        path_window.title(
            "Optimal Plans · Wagner–Whitin Planner"
        )

        path_window.geometry("760x620")
        path_window.minsize(600, 460)

        path_window.configure(
            bg=self.bg_color
        )

        heading = ttk.Frame(
            path_window,
            style="Header.TFrame",
            padding=(20, 16)
        )

        heading.pack(
            fill="x"
        )

        ttk.Label(
            heading,
            text=(
                f"{len(paths)} optimal "
                "production plan(s)"
            ),
            style="DialogTitle.TLabel"
        ).pack(
            anchor="w"
        )

        ttk.Label(
            heading,
            text=(
                "Each plan has the same minimum "
                f"cost of RM "
                f"{self.results['total_cost']:,.2f}."
            ),
            style="DialogSubtitle.TLabel"
        ).pack(
            anchor="w",
            pady=(2, 0)
        )

        text_holder = tk.Frame(
            path_window,
            bg=self.panel_color,
            highlightbackground=self.border_color,
            highlightthickness=1
        )

        text_holder.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        text = tk.Text(
            text_holder,
            width=70,
            height=30,
            font=("Consolas", 11),
            bg=self.panel_color,
            fg=self.text_color,
            relief="flat",
            padx=16,
            pady=14
        )

        text_scrollbar = ttk.Scrollbar(
            text_holder,
            orient="vertical",
            command=text.yview
        )

        text.configure(
            yscrollcommand=text_scrollbar.set
        )

        text.pack(
            side="left",
            fill="both",
            expand=True
        )

        text_scrollbar.pack(
            side="right",
            fill="y"
        )

        for path_number, path in enumerate(
            paths,
            start=1
        ):

            text.insert(
                tk.END,
                f"PLAN {path_number}\n"
            )

            text.insert(
                tk.END,
                "─" * 48 + "\n"
            )

            production_quantities = (
                [0.0] * len(demands)
            )

            for start_year, end_year in path:

                quantity = sum(
                    demands[
                        start_year - 1:end_year
                    ]
                )

                production_quantities[
                    start_year - 1
                ] = quantity

            for year in range(
                1,
                len(demands) + 1
            ):

                quantity = (
                    production_quantities[
                        year - 1
                    ]
                )

                if quantity > 0:

                    text.insert(
                        tk.END,
                        f"Year {year:<3}  "
                        f"Produce {quantity:,.2f} units\n"
                    )

                else:

                    text.insert(
                        tk.END,
                        f"Year {year:<3}  "
                        "No production\n"
                    )

            text.insert(
                tk.END,
                "\n"
            )

        text.config(
            state="disabled"
        )

    # ========================================================
    # CLEAR GUI
    # ========================================================

    def clear(self):

        self.period_var.set("")
        self.setup_var.set("")
        self.holding_var.set("")
        self.variable_var.set("")

        for widget in (
            self.demand_input_frame.winfo_children()
        ):
            widget.destroy()

        self.demand_entries = []

        self.demand_count_label.config(
            text=(
                "Set the number of years, then "
                "generate the demand fields."
            )
        )

        for item in self.table.get_children():

            self.table.delete(item)

        self.results = None

        self.metric_values[
            "solutions"
        ].config(
            text="0"
        )

        for key in (
            "setup",
            "holding",
            "variable",
            "total"
        ):

            self.metric_values[
                key
            ].config(
                text="RM 0.00"
            )

        self._set_result_actions(False)

        self.status.config(
            text="All fields cleared."
        )

        self.period_entry.focus_set()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    root = tk.Tk()

    WagnerWhitinGUI(root)

    root.mainloop()


if __name__ == "__main__":

    main()
