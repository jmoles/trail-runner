import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Open the CSV and find what we are wanting to plot.
csv_in = pd.read_csv("../data/summary.csv")

DATA_ROOT        = "../data/runs/"
DESIRED_NETWORKS = [
    "Jefferson 2,5,4 NN v1",
    "Jefferson-like MDL5 10,5,4 NN v1",
    "Jefferson-like MDL5 10,1,4 NN v1",
    "Jefferson-like MDL2 4,1,4 NN v1",
    "Jefferson-like MDL3 6,1,4 NN v1",
    "Jefferson-like MDL5 10,1,3 NN v1",
    "Jefferson-like MDL4 8,1,4 NN v1"]
DESIRED_TRAILS   = [
    "John Muir Trail",
    "John Muir Trail Filled In"]
PLOTS_DIR        = "plots/"

for curr_network in DESIRED_NETWORKS:
    for curr_trail in DESIRED_TRAILS:

        max_x      = 0
        files_list = []

        if curr_trail == "John Muir Trail":
            MAX_FOOD = 89
        elif curr_trail == "John Muir Trail Filled In":
            MAX_FOOD = 127

        for c_row_idx in range(0, len(csv_in["best_food"])):
            if(csv_in["network_name"][c_row_idx] == curr_network):
                if(csv_in["trail_file"][c_row_idx] == curr_trail):

                    if(csv_in["gen_count"][c_row_idx] > max_x):
                        max_x     = csv_in["gen_count"][c_row_idx]

                    curr_dt    = pd.to_datetime(csv_in["run_date"][c_row_idx])
                    curr_fname = curr_dt.strftime("%Y%m%d_%H%M%S") + ".h5"
                    files_list.append(curr_fname)

        if len(files_list) <= 0:
            # No trails match
            continue

        # Build the numpy array to hold the data.
        plot_data = np.zeros((len(files_list), max_x))

        item_idx = 0
        for curr_fname in files_list:
            fname_pd = pd.read_hdf(DATA_ROOT + curr_fname, "gens")
            plot_data[item_idx] = fname_pd["food_avg"]
            item_idx = item_idx + 1


        x = np.linspace(0, max_x - 1, num=max_x)

        plt.plot(x, np.transpose(plot_data), '-')
        plt.title(curr_network + " - " + curr_trail)
        plt.plot(x, np.repeat(np.array(MAX_FOOD), max_x), 'r--')
        plt.axis((0, max_x, 0, MAX_FOOD + 5))

        plt.savefig(PLOTS_DIR +
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f") +
             ".png")

        plt.cla()
