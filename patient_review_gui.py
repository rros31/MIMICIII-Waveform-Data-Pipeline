# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import tkinter as tk
# import pandas as pd

# class PatientReviewGUI:
#     def __init__(self, master, data, num_plots =2):
#         self.master = master
#         self.data = data
#         self.current_index = 0
#         self.accepted_ids = []
        
#         # GUI setup
#         self.master.title("Patient Data Review")
#         self.figure, self.ax = plt.subplots()
#         self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
#         self.canvas.get_tk_widget().pack()
#         self.num_plots =num_plots
#         # Accept and Discard buttons
#         accept_button = tk.Button(master, text="Accept", command=self.accept_patient)
#         discard_button = tk.Button(master, text="Discard", command=self.next_patient)
#         accept_button.pack(side=tk.LEFT)
#         discard_button.pack(side=tk.RIGHT)

#         # Initial plot
#         self.plot_data()

#     def plot_data(self):
#         self.ax.clear()

#         patient = self.data.iloc[self.current_index]
#         # time = patient['time']
#         # rass = patient['rass']
#         # propofol_doses = patient['propofol']

#         for ii in range(self.num_plots):
#             time = patient[f"time{ii}"]
#             data = patient[f"data{ii}"]
#             self.ax.subplot(self.num_plots,1,ii)
#             self.ax.plot(time, data)
#             # self.ax.plot(time, propofol_doses)
#         self.ax.set_title(f"Patient ID: {patient['id']}")
#         self.ax.legend()
        
#         self.canvas.draw()

#     def accept_patient(self):
#         patient_id = self.data.iloc[self.current_index]['id']
#         self.accepted_ids.append(patient_id)
#         self.next_patient()

#     def next_patient(self):
#         self.current_index += 1
#         if self.current_index < len(self.data):
#             self.plot_data()
#         else:
#             print("No more patients")
#             self.master.quit()

# # Sample data for demonstration
# data = pd.DataFrame({
#     'id': [1, 2, 3],
#     'time0': [range(10), range(10), range(10)],
#     'data0': [[1, 0, -1, -1, 0, 1, 1, 0, -1, -1]] * 3,
#     'time1': [range(10), range(10), range(10)],
#     'propofol1': [[0.5, 0.3, 0.1, 0.1, 0.3, 0.5, 0.6, 0.3, 0.1, 0.1]] * 3
# })

# # Initialize the GUI
# root = tk.Tk()
# app = PatientReviewGUI(root, data)
# root.mainloop()

# # Save accepted IDs if needed
# print("Accepted Patient IDs:", app.accepted_ids)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import pandas as pd

class PatientReviewGUI:
    def __init__(self, master, data, plot_vars,plot_symbols):
        self.master = master
        self.data = data
        self.plot_vars = plot_vars  # List of variable names to plot (e.g., ["RASS", "propofol"])
        self.plot_symbols = plot_symbols
        self.current_index = 0
        self.accepted_ids = []

        # GUI setup
        self.master.title("Patient Data Review")
        self.figure, self.axes = plt.subplots(len(plot_vars), 1, figsize=(10, 5 * len(plot_vars)))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().pack()

        # Accept and Discard buttons in a frame
        button_frame = tk.Frame(master)
        button_frame.pack(side=tk.BOTTOM, anchor="e", pady=10)

        # Increase button size with width and height properties
        accept_button = tk.Button(button_frame, text="Accept", command=self.accept_patient, 
                                bg="green", fg="white", width=15, height=2)
        discard_button = tk.Button(button_frame, text="Discard", command=self.next_patient, 
                                bg="red", fg="white", width=15, height=2)

        # Place both buttons to the right side of the frame
        discard_button.pack(side=tk.RIGHT, padx=5)
        accept_button.pack(side=tk.RIGHT, padx=5)
        # Place both buttons to the right side of the frame
        discard_button.pack(side=tk.RIGHT, padx=5)
        accept_button.pack(side=tk.RIGHT, padx=5)

        # Initial plot
        self.plot_data()

    def plot_data(self):
        # Clear previous plots on each subplot
        for ax in self.axes:
            ax.clear()

        # Get data for the current patient
        patient = self.data.iloc[self.current_index]
        max_time = 0
        for i, var in enumerate(self.plot_vars):
            time_data = patient[f"time_{var}"]
            if max(time_data)>max_time:
                max_time =  max(time_data)
        # Plot each variable specified in plot_vars
        for i, var in enumerate(self.plot_vars):
            time_data = patient[f"time_{var}"]  # Time column for the variable
            value_data = patient[f"{var}"]      # Data column for the variable
            
            self.axes[i].plot(time_data, value_data, self.plot_symbols[i], label=var, color="blue" if i % 2 == 0 else "green")
            self.axes[i].set_title(f"{var} Over Time")
            self.axes[i].set_xlabel("Time")
            self.axes[i].set_ylabel(f"{var}")
            self.axes[i].legend()
            self.axes[i].set_xlim((0, max_time))
        # Set the main title with patient ID
        self.figure.suptitle(f"Patient ID: {patient['id']},   Total Accepted:{len(self.accepted_ids )}")

        # Draw canvas to update the plot display
        self.canvas.draw()

    def accept_patient(self):
        patient_id = self.data.iloc[self.current_index]['id']
        self.accepted_ids.append(patient_id)
        self.next_patient()

    def next_patient(self):
        self.current_index += 1
        if self.current_index < len(self.data):
            self.plot_data()
        else:
            print("No more patients")
            self.master.quit()


def testGui():
    # Sample data for demonstration
    data = pd.DataFrame({
        'id': [1, 2],
        'time_RASS': [range(10), range(10)],
        'RASS': [[1, 0, -1, -1, 0, 1, 1, 0, -1, -1], [0, -1, -2, -1, 0, 1, 2, 1, 0, -1]],
        'time_propofol': [range(10), range(10)],
        'propofol': [[0.5, 0.3, 0.1, 0.1, 0.3, 0.5, 0.6, 0.3, 0.1, 0.1], [0.4, 0.2, 0.1, 0.2, 0.3, 0.5, 0.5, 0.3, 0.2, 0.1]]
    })

    # Define the variables you want to plot
    plot_vars = ["RASS", "propofol"]
    plot_syms =["o","-"]
    # Initialize the GUI
    root = tk.Tk()
    app = PatientReviewGUI(root, data, plot_vars, plot_syms)
    root.mainloop()

    # Save accepted IDs if needed
    print("Accepted Patient IDs:", app.accepted_ids)

if __name__ == "__main__":
    testGui()
