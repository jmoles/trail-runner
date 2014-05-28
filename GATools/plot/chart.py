import datetime
import os
import StringIO
import base64
import matplotlib.pyplot as pyplot
import matplotlib.backends.backend_agg as pltagg
import numpy as np

from ..DBUtils import DBUtils

class chart:
    def __init__(self):
        self.__pgdb = DBUtils()

    def lineChart(self, run_ids, ext="png", stat_group="food",
        stat=None):

        if stat_group == "moves_stats" and stat == None:
            stat=["left", "right", "forward", "none"]
        elif stat == None:
            stat=["min", "max", "avg"]

        # Generate the figure and axes common to all of these.
        fig = pyplot.Figure()
        axis = fig.add_subplot(1,1,1)

        # Get information on the run
        run_info  = self.__pgdb.fetchRunInfo(run_ids)

        # Determine the maximum amount of food
        trail_grid, _, _ = self.__pgdb.getTrailData(
            run_info[run_ids[0]]["trails_id"])
        max_food = np.bincount(np.array(trail_grid.flatten())[0])[1]

        # Moves are looked at through iterations
        max_moves = 0

        # Take each run and now fetch data for each.
        gens_data = self.__pgdb.fetchRunGenerations(run_ids)

        # Find the network name.
        net_name = self.__pgdb.getNetworks()[
            run_info[run_ids[0]]["networks_id"]]

        # Find the trail name.
        trail_name = self.__pgdb.getTrails()[run_info[run_ids[0]]["trails_id"]]

        # Manipulate the data into preparation for a plot.
        plot_data = np.zeros((
            len(run_ids) * len(stat),
            len(gens_data),
            ))

        # TODO: Fix this to handle more than one run_ids. Probably need
        # a view in the DB to not make this nasty.
        for e_idx in range(0, len(stat)):
            for g_idx in range(0, run_info[run_ids[0]]["generations"]):
                c_stat = stat[e_idx]

                if stat_group == "moves_stats":
                    c_key = "moves"
                else:
                    c_key = stat_group

                plot_data[e_idx][g_idx] = (
                    gens_data[g_idx][c_key][c_stat])

        x = np.linspace(
            0,
            run_info[run_ids[0]]["generations"] - 1,
            num=run_info[run_ids[0]]["generations"])

        plot_title = (
            "{0} - {1} g{2}/p{3}".format(
                net_name,
                trail_name,
                run_info[run_ids[0]]["generations"],
                run_info[run_ids[0]]["population"]))

        # TODO: May need to transpose when having more than one run_ids.
        for c_data, c_legend in zip(plot_data, stat):
            axis.plot(x, c_data, '-', label=c_legend.title())

        # Determine the maximum type to show.
        if stat_group == "food":
            axis.plot(x, np.repeat(
                np.array(max_food),
                run_info[run_ids[0]]["generations"]), 'r--')
            axis.axis((0, run_info[run_ids[0]]["generations"],
                0, max_food + 5))
            axis.set_ylabel("Food Consumed")
            axis.set_xlabel("Generations")
            axis.legend(loc="best")
        elif stat_group == "moves":
            axis.plot(x, np.repeat(
                np.array(run_info[run_ids[0]]["moves_limit"]),
                run_info[run_ids[0]]["generations"]), 'r--')
            axis.axis((0, run_info[run_ids[0]]["generations"],
                0, run_info[run_ids[0]]["moves_limit"] + 5))
            axis.set_ylabel("Moves Taken")
            axis.set_xlabel("Generations")
            axis.legend(loc="lower left")
        elif stat_group == "moves_stats":
            axis.axis((0, run_info[run_ids[0]]["generations"],
                0, run_info[run_ids[0]]["moves_limit"] + 5))
            axis.set_ylabel("Moves Taken")
            axis.set_xlabel("Generations")
            axis.legend(loc="upper left", ncol=2)

        axis.set_title(plot_title)


        fig.set_facecolor('w')

        return (self.__createImage(fig, ext), plot_title)


    def __createImage(self, fig, ext="jpg"):
        """ Takes a matplotlib fig and generates given ext type.

        Returns

        """
        canvas = pltagg.FigureCanvasAgg(fig)
        output = StringIO.StringIO()

        if ext == "tif" or ext == "tiff":
            canvas.print_tif(output)
        elif ext == "bmp":
            canvas.print_bmp(output)
        elif ext == "eps":
            canvas.print_eps(output)
        elif ext == "png":
            canvas.print_png(output)
        elif ext == "pdf":
            canvas.print_pdf(output)
        elif ext == "svg":
            canvas.print_svg(output)
        else:
            canvas.print_jpg(output)

        return output
