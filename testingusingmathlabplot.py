import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime

# Matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def wagner_whitin_backward(n, demands, s, h, v):

    # Initialize DP tables
    f = [0.0] * (n + 2)

    # Store all optimal choices for each period
    optimal_choices = [[] for _ in range(n + 1)]

    # Backward Dynamic Programming Calculation
    for i in range(n, 0, -1):

        min_cost = float("inf")
        best_ks =[]

        for k in range(i, n + 1):

            current_lot_demand = sum(demands[i - 1:k])

            current_holding_cost = 0

            for m in range(i, k + 1):
 
                current_holding_cost += ((m - i) * demands[m - 1] * h)

            current_variable_cost = (current_lot_demand * v)

            total_cost = (s + current_holding_cost + current_variable_cost + f[k + 1])

            # Found a better solution
            if total_cost < min_cost - 1e-9:
                min_cost = total_cost
                best_ks = [k]

            # Found another solution with the same cost
            elif abs(total_cost - min_cost) < 1e-9:

                best_ks.append(k)

        # Store ALL optimal choices
        f[i] = min_cost
        optimal_choices[i] = best_ks

    # Generate all optimal paths
    optimal_paths = []

    def generate_paths(current_period, path):

        if current_period > n:
            optimal_paths.append(path.copy())
            return

        for end_year in optimal_choices[current_period]:

            path.append((current_period, end_year))

            generate_paths(end_year + 1,path)

            path.pop()

    generate_paths(1, [])

    # Forward Backtracking

    order_schedule = [0.0] * n
    order_end_year = [0] * n

    if optimal_paths:

        first_path = optimal_paths[0]

        for start_year, end_year in first_path:

            qty = sum(
                demands[start_year - 1:end_year]
            )

            order_schedule[start_year - 1] = qty
            order_end_year[start_year - 1] = end_year

    # Cost Breakdown

    total_setup_cost = 0
    total_holding_cost = 0
    total_variable_cost = 0

    for i in range(n):

        if order_schedule[i] > 0:
            total_setup_cost += s
            total_variable_cost += (order_schedule[i] * v)

            end_year = order_end_year[i]

            for m in range(i + 1, end_year):

                total_holding_cost += ((m - i) * demands[m] * h)

    total_cost = (total_setup_cost + total_holding_cost + total_variable_cost)

   
    # calculation results to the GUI.
    return {
        "n": n,
        "demands": demands,
        "setup_cost": s,
        "holding_cost": h,
        "variable_cost": v,

        #first optimal solution
        "order_schedule": order_schedule,
        "order_end_year": order_end_year,
        "total_setup_cost": total_setup_cost,
        "total_holding_cost": total_holding_cost,
        "total_variable_cost": total_variable_cost,
        "total_cost": total_cost,

         #optimal choices
        "optimal_choices": optimal_choices,
        "optimal_paths": optimal_paths
        }


# INPUT VALIDATION FOR GUI

def validate_number(value,integer=False,allow_zero=True):
    try:
        if integer:
            number = int(value)

        else:
            number = float(value)

    except ValueError:
        raise ValueError("Please enter a valid numeric value.")

    if allow_zero:
        if number < 0:
            raise ValueError("Value must be 0 or positive.")

    else:

        if number <= 0:
            raise ValueError("Value must be greater than 0.")

    return number

# FILE MANAGEMENT

class FileManager:

    # READ INPUT FILE FROM CSV

    @staticmethod
    def read_input():

        filename = filedialog.askopenfilename(
            title="Open Input Data", 
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not filename:
            return None

        with open(filename, "r", newline="", encoding="utf-8-sig") as file:

            rows = list(csv.reader(file))

        try:
            # Read number of years
            n = int(float(rows[3][1]))

            # Read costs
            s = float(rows[4][1])
            h = float(rows[5][1])
            v = float(rows[6][1])

            # Read demand
            demands = []

            for row in rows[9:]:

                if len(row) >= 2:

                    if row[0].strip():

                        demands.append(float(row[1]))

            # Check demand count
            if len(demands) != n:

                raise ValueError("The number of demand values does not match the number of years.")

        except Exception as error:

            raise ValueError(f"Invalid input file:\n{error}")

        return (n, demands, s, h, v)

    # EXPORT RESULTS TO CSV

    @staticmethod
    def export_csv(results):

        if results is None:
            raise ValueError("No calculation result available.")

        filename = filedialog.asksaveasfilename(
            title="Export Results to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not filename:
            return False

        try:

            with open(filename, "w", newline="", encoding="utf-8-sig") as file:

                writer = csv.writer(file)

                # TITLE
                writer.writerow(["WAGNER-WHITIN OPTIMAL SOLUTIONS"])
                writer.writerow([])

                # INPUT INFORMATION
                writer.writerow(["INPUT INFORMATION"])
                writer.writerow(["Number of Years", results["n"]])
                writer.writerow(["Setup Cost", results["setup_cost"]])
                writer.writerow(["Holding Cost", results["holding_cost"]])
                writer.writerow(["Variable Cost", results["variable_cost"]])
                writer.writerow([])

                # DEMAND INFORMATION
                writer.writerow(["DEMAND BY YEAR"])
                writer.writerow(["Year", "Demand"])

                for i in range(results["n"]):

                    writer.writerow([i + 1, results["demands"][i]])

                writer.writerow([])

                # FIRST OPTIMAL ORDERING PLAN
                writer.writerow(["SELECTED OPTIMAL ORDERING PLAN"])
                writer.writerow(["Year", "Demand", "Order Quantity", "Covers Until"])

                for i in range(results["n"]):

                    if results["order_schedule"][i] > 0:

                        order_quantity = (results["order_schedule"][i])

                        covers_until = (results["order_end_year"][i])

                    else:

                        order_quantity = 0
                        covers_until = "-"

                    writer.writerow([i + 1, results["demands"][i], order_quantity, covers_until])

                writer.writerow([])

                # ALL OPTIMAL SOLUTIONS
                writer.writerow(["ALL OPTIMAL SOLUTIONS"])
                writer.writerow(["Solution", "Ordering Path", "Total Optimal Cost"])

                optimal_paths = results["optimal_paths"]

                for path_number, path in enumerate(optimal_paths, start=1):

                    # Convert path into readable format
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

                # NUMBER OF OPTIMAL SOLUTIONS
                writer.writerow(["Number of Optimal Solutions", len(optimal_paths)])
                writer.writerow([])

                # COST BREAKDOWN
                writer.writerow(["COST BREAKDOWN"])
                writer.writerow(["Total Setup Cost", results["total_setup_cost"]])
                writer.writerow(["Total Holding Cost", results["total_holding_cost"]])
                writer.writerow(["Total Variable Cost", results["total_variable_cost"]])
                writer.writerow(["TOTAL OPTIMAL COST", results["total_cost"]])

            return True

        except Exception as error:

            raise ValueError(f"Unable to export CSV file:\n{error}")

    
    # EXPORT TEXT REPORT

    @staticmethod
    def export_report(results):

        if results is None:
            raise ValueError("No calculation result available.")

        filename = filedialog.asksaveasfilename(
            title="Export WWA Report",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not filename:
            return False

        try:

            with open(filename, "w", encoding="utf-8") as file:

                # TITLE
                file.write("=" * 70 + "\n")
                file.write("WAGNER-WHITIN OPTIMAL SOLUTIONS\n")
                file.write("=" * 70 + "\n")
                file.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")

                # INPUT INFORMATION
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

                # DEMAND
                file.write("\nDEMAND BY YEAR\n")
                file.write("-" * 70 + "\n")

                for i in range(results["n"]):

                    file.write(
                        f"Year {i + 1:<3}: "
                        f"{results['demands'][i]:.2f}\n"
                    )

                # SELECTED OPTIMAL ORDERING PLAN
                file.write("\nSELECTED OPTIMAL ORDERING PLAN\n")
                file.write("-" * 70 + "\n")

                file.write(
                    f"{'Year':<10}"
                    f"{'Demand':<15}"
                    f"{'Order Qty':<15}"
                    f"{'Covers Until':<15}\n"
                )

                file.write("-" * 70 + "\n")

                for i in range(results["n"]):

                    if results["order_schedule"][i] > 0:

                        qty = (results["order_schedule"][i])

                        end = (results["order_end_year"][i])

                    else:

                        qty = 0
                        end = "-"

                    file.write(
                        f"{i + 1:<10}"
                        f"{results['demands'][i]:<15.2f}"
                        f"{qty:<15.2f}"
                        f"{str(end):<15}\n"
                    )

                # ALL OPTIMAL SOLUTIONS
                file.write("\n\nALL OPTIMAL SOLUTIONS\n")
                file.write("=" * 70 + "\n")

                optimal_paths = results["optimal_paths"]

                file.write(
                    f"Number of Optimal Solutions: "
                    f"{len(optimal_paths)}\n"
                )

                file.write(
                    f"Minimum Total Cost: "
                    f"RM {results['total_cost']:.2f}\n\n"
                )

                # Display every optimal path
                for path_number, path in enumerate(optimal_paths, start=1):

                    file.write(f"OPTIMAL SOLUTION {path_number}\n")
                    file.write("-" * 50 + "\n")
                    file.write("Ordering Path: ")

                    path_text = " → ".join(
                        f"Year {start}"
                        if start == end
                        else f"Year {start}-{end}"
                        for start, end in path
                    )

                    file.write(path_text + "\n")

                    file.write(
                        f"Total Cost: "
                        f"RM {results['total_cost']:.2f}\n\n"
                    )

                # COST BREAKDOWN
                file.write("COST BREAKDOWN\n")
                file.write("=" * 70 + "\n")

                file.write(
                    f"Total Setup Cost   : "
                    f"RM {results['total_setup_cost']:.2f}\n"
                )

                file.write(
                    f"Total Holding Cost : "
                    f"RM {results['total_holding_cost']:.2f}\n"
                )

                file.write(
                    f"Total Variable Cost: "
                    f"RM {results['total_variable_cost']:.2f}\n"
                )

                file.write("-" * 70 + "\n")

                file.write(
                    f"TOTAL OPTIMAL COST : "
                    f"RM {results['total_cost']:.2f}\n"
                )

                file.write("=" * 70 + "\n")

            return True

        except Exception as error:

            raise ValueError(f"Unable to export report:\n{error}")

# GRAPHICAL USER INTERFACE

class WagnerWhitinGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Wagner-Whitin Algorithm")

        self.root.geometry("1150x750")

        self.build_gui()

    # BUILD GUI
    def build_gui(self):

        self.demand_entries = []
        self.results = None

        # Store demand input boxes
        self.demand_entries = []

        # Store calculation result
        self.results = None

        # Build GUI
        self.build_gui()

    # BUILD GUI

    def build_gui(self):

        # Title
        title = ttk.Label(
            self.root,
            text="WAGNER-WHITIN ALGORITHM",
            font=("Arial", 22, "bold"))

        title.pack(pady=15)

        subtitle = ttk.Label(self.root,text=(
                "Dynamic Lot Size Model "
                "| Duration is measured in Years"),
            font=("Arial", 11))

        subtitle.pack(pady=(0, 10))

        # INPUT FRAME

        input_frame = ttk.LabelFrame(self.root,text="Input Information",padding=15)

        input_frame.pack( fill="x",padx=20,pady=5)

        # Number of years
        ttk.Label(input_frame,text="Number of Years:").grid(
            row=0,
            column=0,
            padx=10,
            pady=7)

        self.period_entry = ttk.Entry(input_frame, width=15)
        self.period_entry.grid(row=0,column=1) 

        # Setup cost
        ttk.Label(input_frame,text="Setup Cost:").grid(
            row=0,
            column=2,
            padx=10)

        self.setup_entry = ttk.Entry(input_frame,width=15)

        self.setup_entry.grid(row=0,column=3)

        # Holding cost
        ttk.Label(input_frame,text="Holding Cost / Unit / Year:").grid(
            row=1,
            column=0,
            padx=10,
            pady=7)

        self.holding_entry = ttk.Entry(input_frame,width=15)
        self.holding_entry.grid( row=1,column=1)

        # Variable cost

        ttk.Label(input_frame,text="Variable Cost / Unit:").grid(
            row=1,
            column=2,
            padx=10)

        self.variable_entry = ttk.Entry(input_frame,width=15)

        self.variable_entry.grid(row=1,column=3)

        # Create demand fields
        ttk.Button(input_frame,text="Create Demand Fields",command=self.create_demands).grid(
            row=0,
            column=4,
            rowspan=2,
            padx=20,
            ipadx=10)

        # DEMAND FRAME
        self.demand_frame = ttk.LabelFrame(self.root,text="Demand for Each Year",padding=15)
        self.demand_frame.pack(fill="x", padx=20,pady=8)

        # BUTTON FRAME
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        # Calculate
        ttk.Button(button_frame,text="Calculate",command=self.calculate).grid(
            row=0,
            column=0,
            padx=5)

        # Read Input
        ttk.Button(button_frame,text="Read Input",command=self.read_input).grid(
            row=0,
            column=1,
            padx=5)

        # Export CSV
        ttk.Button(button_frame,text="Export CSV",command=self.export_csv).grid(
            row=0,
            column=3,
            padx=5)

        # Export Report
        ttk.Button(button_frame,text="Export Report",command=self.export_report).grid(
            row=0,
            column=4,
            padx=5)

        # Clear
        ttk.Button(button_frame,text="Clear",command=self.clear).grid(
            row=0,
            column=5,
            padx=5)

        # Exit
        ttk.Button(button_frame,text="Exit",command=self.root.destroy).grid(
            row=0,
            column=6,
            padx=5)

        ttk.Button(button_frame,text="Demand Trend Line Graph",command=self.show_demand_trend).grid(
            row=0,
            column=7,
            padx=5)

        ttk.Button(button_frame,text="Network Flow Diagram",command=self.show_network_flow).grid(
            row=0,
            column=8,
            padx=5)

        # RESULT TABLE
        result_frame = ttk.LabelFrame(
            self.root,
            text="Optimal Ordering Plan",
            padding=10)

        result_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5)

        columns = (
            "Solution",
            "Year",
            "Demand",
            "Order Quantity",
            "Covers Until"
        )

        self.table = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings"
        )

        for column in columns:

            self.table.heading(
                column,
                text=column
            )

            self.table.column(
                column,
                anchor="center",
                width=150
            )

        self.table.pack(
            fill="both",
            expand=True
        )

        # COST DISPLAY

        self.cost_label = ttk.Label(
            self.root,
            text="Total Optimal Cost: RM 0.00",
            font=("Arial", 16, "bold"))

        self.cost_label.pack(pady=10)

        # Status bar
        self.status = ttk.Label(
            self.root,
            text="Ready.",
            relief="sunken",
            anchor="w")

        self.status.pack(
            side="bottom",
            fill="x")

        

    # CREATE DEMAND INPUT BOXES
    def create_demands(self):

        for widget in (self.demand_frame.winfo_children()):

            widget.destroy()

        self.demand_entries = []

        try:
            n = validate_number(self.period_entry.get(),integer=True,allow_zero=False)

        except ValueError as error:
            messagebox.showerror("Input Error",str(error))
            return

        for i in range(n):
            row = i // 5
            column = (i % 5) * 2
            ttk.Label(self.demand_frame,text=f"Year {i + 1}:").grid(
                row=row,
                column=column,
                padx=8,
                pady=5)

            entry = ttk.Entry(self.demand_frame,width=12)

            entry.grid(
                row=row,
                column=column + 1,
                padx=8,
                pady=5)

            self.demand_entries.append(entry)

        self.status.config(text=(
                f"Demand fields created for "
                f"{n} years."))

    # GET INPUT FROM GUI
    def get_inputs(self):

        n = validate_number(
            self.period_entry.get(),
            integer=True,
            allow_zero=False)

        s = validate_number(
            self.setup_entry.get(),
            allow_zero=False)

        h = validate_number(
            self.holding_entry.get(),
            allow_zero=False)

        v = validate_number(
            self.variable_entry.get(),
            allow_zero=False)

        if len(self.demand_entries) != n:

            raise ValueError("Please click 'Create Demand Fields' before entering demand.")

        demands = []

        for entry in self.demand_entries:
            demand = validate_number(entry.get(),allow_zero=True)

            demands.append(demand)

        return (n,demands,s,h,v)

    # RUN CALCULATION FROM GUI
    def calculate(self):

        try:
            n, demands, s, h, v = (self.get_inputs())

            # Call the ORIGINAL WWA calculation
            self.results = (wagner_whitin_backward(n,demands,s,h,v))

            # Display returned results
            self.display_results()
            self.status.config(text="Calculation completed successfully.")

        except Exception as error:
            messagebox.showerror("Calculation Error",str(error))

    # DISPLAY RESULTS IN GUI
 
    # DISPLAY ALL OPTIMAL RESULTS IN MAIN TABLE
    def display_results(self):

        # ============================================================
        # CLEAR OLD RESULTS
        # ============================================================

        for item in self.table.get_children():
            self.table.delete(item)

        # ============================================================
        # GET RESULTS
        # ============================================================

        optimal_paths = self.results["optimal_paths"]
        demands = self.results["demands"]

        total_cost = self.results["total_cost"]

        # Number of optimal solutions
        path_count = len(optimal_paths)

        # ============================================================
        # DISPLAY EVERY OPTIMAL PATH
        # ============================================================

        for path_number, path in enumerate(
            optimal_paths,
            start=1
            
        ):

            # --------------------------------------------------------
            # Calculate order quantity for every year
            # --------------------------------------------------------

            order_quantities = [0.0] * len(demands)

            order_end_years = [0] * len(demands)

            for start_year, end_year in path:

                # Calculate quantity covered by this order
                qty = sum(
                    demands[
                        start_year - 1:end_year
                    ]
                )

                order_quantities[
                    start_year - 1
                ] = qty

                order_end_years[
                    start_year - 1
                ] = end_year

            # --------------------------------------------------------
            # DISPLAY EVERY YEAR
            # --------------------------------------------------------

            for year in range(
                1,
                len(demands) + 1
            ):

                order_qty = order_quantities[
                    year - 1
                ]

                # ----------------------------------------------------
                # If order is placed in this year
                # ----------------------------------------------------

                if order_qty > 0:

                    order_text = (
                        f"{order_qty:.0f}"
                    )

                    covers_until = (
                        order_end_years[
                            year - 1
                        ]
                    )

                # ----------------------------------------------------
                # No order in this year
                # ----------------------------------------------------

                else:

                    order_text = "-"

                    covers_until = "-"

                # ----------------------------------------------------
                # Insert into table
                # ----------------------------------------------------

                self.table.insert(
                    "",
                    "end",
                    values=(
                        f"Path {path_number}",
                        year,
                        f"{demands[year - 1]:.0f}",
                        order_text,
                        covers_until
                    )
                )

            if path_number < path_count:
                    self.table.insert("", "end", values=("", "", "", "", ""))

                

        # ============================================================
        # UPDATE COST DISPLAY
        # ============================================================

        self.cost_label.config(
            text=(
                f"Optimal Solutions: {path_count}    |    "
                f"Minimum Total Cost: "
                f"RM {total_cost:,.2f}"
            )
        )

        # ============================================================
        # UPDATE STATUS
        # ============================================================

        self.status.config(
            text=(
                f"Calculation completed. "
                f"{path_count} optimal solution(s) found "
                f"with the same minimum total cost."
            )
        )


    # READ INPUT
    def read_input(self):

        try:

            data = FileManager.read_input()
            if data is None:
                return
            
            n, demands, s, h, v = data

            # Fill number of years
            self.period_entry.delete(0,tk.END)
            self.period_entry.insert(0,str(n))

            # Fill setup cost
            self.setup_entry.delete(0,tk.END)
            self.setup_entry.insert(0,str(s))

            # Fill holding cost
            self.holding_entry.delete(0,tk.END)
            self.holding_entry.insert(0,str(h))

            # Fill variable cost
            self.variable_entry.delete(0,tk.END)
            self.variable_entry.insert(0,str(v))

            # Create demand fields
            self.create_demands()

            # Fill demand
            for i in range(n):

                self.demand_entries[i].insert(0,str(demands[i]))

            self.status.config(text="Input file loaded successfully.")

            messagebox.showinfo(
                "Success",
                "Input data loaded successfully.")

        except Exception as error:

            messagebox.showerror(
                "Read Error",
                str(error))

    # EXPORT CSV

    def export_csv(self):

        if self.results is None:
            messagebox.showwarning(
                "No Results",
                "Please calculate the WWA solution first.")

            return

        try:

            success = (
                FileManager.export_csv(
                    self.results
                )
            )

            if success:

                messagebox.showinfo(
                    "Success",
                    "Results exported to CSV successfully.")

                self.status.config(text="Results exported to CSV.")

        except Exception as error:

            messagebox.showerror("Export Error",str(error))

    # EXPORT TEXT REPORT

    def export_report(self):

        if self.results is None:

            messagebox.showwarning(
                "No Results",
                "Please calculate the WWA solution first."
            )

            return

        try:

            success = (
                FileManager.export_report(
                    self.results
                )
            )

            if success:

                messagebox.showinfo(
                    "Success",
                    "WWA report exported successfully.")

                self.status.config(text="Report exported.")

        except Exception as error:

            messagebox.showerror(
                "Export Error",
                str(error))

    # demand trend line graph
    def show_demand_trend(self):

        # Check whether calculation has been performed
        if self.results is None:
            messagebox.showwarning(
                "No Results",
                "Please calculate the WWA solution first.")
            return

        #Create new window
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Demand Trend")
        graph_window.geometry("850x600")

        # Get data from WWA results
        years = list(
            range(1, self.results["n"] + 1)
        )

        demands = self.results["demands"]

        #  Create matplotlib figure
        figure = Figure(
            figsize=(8, 5),
            dpi=100)

        axis = figure.add_subplot(111)

        # Plot demand trend
        axis.plot(
            years,
            demands,
            marker="o",
            linewidth=2,
            markersize=6)

        # Graph title
        axis.set_title(
            "Demand Trend Line Graph",
            fontsize=14,
            fontweight="bold")

        # Axis labels
        axis.set_xlabel("Year")
        axis.set_ylabel("Number of Demand")

        # Show every year on x-axis
        axis.set_xticks(years)

        # Add grid
        axis.grid(
            True,
            linestyle="--",
            alpha=0.5)

        # Display value for every points
        for year, demand in zip(
            years,
            demands):

            axis.annotate(
                f"{demand:.2f}",
                (year, demand),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center")

        # Adjust layout
        figure.tight_layout()

        # Put matplotlib graph inside Tkinter window
        canvas = FigureCanvasTkAgg(
            figure,
            master=graph_window)

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10)

    # DIRECTED NETWORK FLOW DIAGRAM
    def show_network_flow(self):

        # Check whether calculation has been performed
        if self.results is None:
            messagebox.showwarning(
                "No Results",
                "Please calculate the WWA solution first."
            )
            return

        # GET WWA RESULTS
        n = self.results["n"]
        demands = self.results["demands"]

        # all solution
        optimal_paths = self.results["optimal_paths"]
        total_cost = self.results["total_cost"]

        # Check whether optimal paths
        if not optimal_paths:
            messagebox.showwarning(
                "No Optimal Path",
                "No optimal path was found."
            )
            return

        # create window
        flow_window = tk.Toplevel(self.root)
        flow_window.title("Multiple Optimal Network Flow Paths")
        flow_window.geometry("1400x850")

        # cretae figure
        figure = Figure(
            figsize=(14, 8),
            dpi=100
        )

        axis = figure.add_subplot(111)

        # NODE STRUCTURE
        node_count = n + 1

        x_positions = list(
            range(1, node_count + 1)
        )

        y_position = 0

        # draw node
        axis.scatter(
            x_positions,
            [y_position] * node_count,
            s=1000,
            zorder=5
        )

        # node label
        for i in range(1, n + 1):

            axis.text(
                i,
                y_position,
                f"Y{i}",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="white",
                zorder=6
            )

        # end node
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

        # DEMAND LABELS
        for i in range(1, n + 1):

            axis.text(
                i,
                -0.8,
                f"Demand = {demands[i - 1]:.2f}",
                ha="center",
                va="top",
                fontsize=9
            )

        # DRAW ALL POSSIBLE DIRECTED ARCS
        for start in range(1, n + 1):

            for end in range(start + 1, n + 2):

                distance = end - start

                # Keep the arcs separated
                arc_height = (
                    0.20 + distance * 0.08
                )

                axis.annotate(
                    "",
                    xy=(end, 0),
                    xytext=(start, 0),

                    arrowprops=dict(
                        arrowstyle="->",
                        linewidth=1,
                        alpha=0.15,
                        color="gray",

                        connectionstyle=(
                            f"arc3,rad=-{arc_height}"
                        )
                    ),

                    zorder=1
                )

        # DRAW ALL OPTIMAL PATHS
        path_count = len(optimal_paths)

        # Height used to separate multiple paths
        path_spacing = 0.10

        for path_index, path in enumerate(
            optimal_paths,
            start=1
        ):

            # Calculate path-specific vertical position
            if path_count == 1:

                path_offset = 0

            else:

                path_offset = (
                    (path_index - 1)
                    - (path_count - 1) / 2
                ) * path_spacing

            path_height_offset = path_offset

            # Draw every arc belonging to this optimal path
            for start_year, end_year in path:

                # Convert WWA period representation into network node representation.
                network_start = start_year
                network_end = end_year + 1

                distance = (
                    network_end - network_start
                )

                # Base arc height
                base_height = (
                    0.25 + distance * 0.10
                )

                # Add path separation
                arc_height = (
                    base_height
                    + path_height_offset
                )

                # Draw optimal arc
                axis.annotate(
                    "",
                    xy=(
                        network_end,
                        0
                    ),

                    xytext=(
                        network_start,
                        0
                    ),

                    arrowprops=dict(
                        arrowstyle="->",
                        linewidth=3,
                        alpha=0.90,

                        # default color cycle
                        color=f"C{(path_index - 1) % 10}",

                        connectionstyle=(
                            f"arc3,rad=-{arc_height}"
                        )
                    ),

                    zorder=4
                )

                # LABEL POSITION

                middle = (
                    network_start
                    + network_end
                ) / 2

                label_height = (
                    arc_height + 0.15
                )

                # ORDER QUANTITY
                order_quantity = sum(
                    demands[
                        start_year - 1:end_year
                    ]
                )

                # COVERAGE DESCRIPTION

                if start_year == end_year:

                    coverage_text = (
                        f"P{path_index}: "
                        f"Order = {order_quantity:.2f}\n"
                        f"Covers Y{start_year}"
                    )

                else:

                    coverage_text = (
                        f"P{path_index}: "
                        f"Order = {order_quantity:.2f}\n"
                        f"Covers Y{start_year}"
                        f"-Y{end_year}"
                    )

                # DRAW LABEL
                axis.text(
                    middle,
                    label_height,
                    coverage_text,

                    ha="center",
                    va="bottom",

                    fontsize=8,
                    fontweight="bold",

                    color=f"C{(path_index - 1) % 10}",

                    zorder=7,

                    bbox=dict(
                        boxstyle="round,pad=0.25",
                        facecolor="white",
                        alpha=0.75
                    )
                )
        #Axis title
        axis.set_title(
            "Directed Network Flow Diagram\n",

            fontsize=16,
            fontweight="bold",
            pad=25
        )

        # axis lable
        axis.set_xlabel(
            "Planning Period",
            fontsize=11
        )

        # X-AXIS
        axis.set_xlim(
            0.5,
            n + 1.5
        )

        axis.set_xticks(
            x_positions
        )

        # Y-AXIS
        # Increase the Y range because multiple paths

        max_path_height = (
            0.25
            + n * 0.10
            + abs(path_spacing * path_count)
            + 1.0
        )

        axis.set_ylim(
            -1.6,
            max_path_height
        )

        axis.set_yticks([])

        # GRID

        axis.grid(
            axis="x",
            linestyle="--",
            alpha=0.25
        )

        # LEGEND / INFORMATION BOX
        legend_text = (
            "NETWORK FLOW INFORMATION\n"
            "--------------------------------\n"
            "Gray arrows = Possible ordering decisions\n"
            "Colored arrows = Optimal WWA paths\n\n"
            f"Number of Optimal Paths = {path_count}\n"
            f"Minimum Total Cost = RM {total_cost:,.2f}"
        )

        axis.text(
            0.02,
            0.97,

            legend_text,

            transform=axis.transAxes,

            fontsize=9,

            verticalalignment="top",

            bbox=dict(
                boxstyle="round",
                facecolor="white",
                alpha=0.9
            )
        )

        # result summary
        summary_text = (
            "OPTIMAL PATHS\n"
            "==============================\n"
        )

        for path_number, path in enumerate(
            optimal_paths,
            start=1
        ):

            path_text = " → ".join(

                f"Y{start}"
                if start == end

                else f"Y{start}-Y{end}"

                for start, end in path
            )

            # Add END to the network path
            if path:

                last_end = path[-1][1]

                path_text += f" → END"

            summary_text += (
                f"Path {path_number}: "
                f"{path_text}\n"
            )

        summary_text += (
            "\n"
            f"Same Minimum Cost: "
            f"RM {total_cost:,.2f}"
        )

        # Put summary at bottom-left
        axis.text(
            0.02,
            0.02,

            summary_text,

            transform=axis.transAxes,

            fontsize=9,

            verticalalignment="bottom",

            bbox=dict(
                boxstyle="round",
                facecolor="white",
                alpha=0.90
            )
        )

        # REMOVE TOP / RIGHT SPINES
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        # ADJUST LAYOUT
        figure.tight_layout()

        # DISPLAY MATPLOTLIB IN TKINTER
        canvas = FigureCanvasTkAgg(
            figure,
            master=flow_window
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        
    def show_optimal_paths(self):

        if self.results is None:
            messagebox.showwarning(
            "No Results",
            "Please calculate the WWA solution first."
            )
            return

        paths = self.results["optimal_paths"]
        demands = self.results["demands"]

        path_window = tk.Toplevel(self.root)
        path_window.title("Multiple Optimal Solutions")
        path_window.geometry("700x600")

        ttk.Label(
            path_window,
            text=f"Number of Optimal Solutions: {len(paths)}",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        ttk.Label(
            path_window,
            text="The following ordering plans have the same minimum total cost.\n",
            font=("Arial", 10)
        ).pack(pady=(0, 10))

        text = tk.Text(
            path_window,
            width=70,
            height=30,
            font=("Courier New", 10)
            )

        text.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
            )

        for path_number, path in enumerate(paths, start=1):

            text.insert(
                tk.END,
                f"OPTIMAL SOLUTION {path_number}\n"
            )

            text.insert(
                tk.END,
                "-" * 40 + "\n"
            )

            # Create order quantity for every year
            order_quantities = [0.0] * len(demands)

            for start_year, end_year in path:

                qty = sum(
                    demands[start_year - 1:end_year]
                )

                order_quantities[start_year - 1] = qty

            # Display every year
            for year in range(1, len(demands) + 1):

                if order_quantities[year - 1] > 0:
                    text.insert(
                        tk.END,
                        f"Year {year:<3}: "
                        f"{order_quantities[year - 1]:.2f}\n"
                    )
                else:
                    text.insert(
                        tk.END,
                        f"Year {year:<3}: -\n"
                    )

            text.insert(
                tk.END,
                "\n"
            )

        text.config(state="disabled")

    # CLEAR GUI
    def clear(self):

        self.period_entry.delete(
            0,
            tk.END
        )

        self.setup_entry.delete(
            0,
            tk.END
        )

        self.holding_entry.delete(
            0,
            tk.END
        )

        self.variable_entry.delete(
            0,
            tk.END
        )

        for widget in (
            self.demand_frame.winfo_children()
        ):

            widget.destroy()

        self.demand_entries = []

        for item in (
            self.table.get_children()
        ):

            self.table.delete(
                item
            )

        self.results = None

        self.cost_label.config(
            text="Total Optimal Cost: RM 0.00"
        )

        self.status.config(
            text="All fields cleared."
        )

# MAIN PROGRAM
def main():

    # Create the main GUI window
    root = tk.Tk()

    # Create the WWA GUI application
    app = WagnerWhitinGUI(root)

    # Start the GUI
    root.mainloop()

# PROGRAM START
if __name__ == "__main__":

    main()
