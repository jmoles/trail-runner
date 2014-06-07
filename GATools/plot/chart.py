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

        # Fetch some information for later use.
        self.__network_list_cache = None
        self.__trail_list_cache   = None
        self.__trails_cache       = {}
        self.__same_run_id_cache  = {}
        self.__run_info_cache     = {}
        self.__gen_data_cache     = {}


    def lineChart(self, run_id, ext="png", stat_group="food",
        stat=None, group=False):

        if not self.__network_list_cache or not self.__trail_list_cache:
            self.__cacheInit()

        if stat_group == "moves_stats" and stat == None:
            stat=["left", "right", "forward", "none"]
        elif stat == None:
            stat=["min", "max", "avg"]

        # If grouping, get all of the run ids.
        if group:
            if not self.__same_run_id_cache.has_key(run_id):
                run_ids_l = self.__pgdb.getSameRunIDs(run_id)
                self.__same_run_id_cache[run_id] = run_ids_l
            else:
                run_ids_l = self.__same_run_id_cache[run_id]
        else:
            run_ids_l = [run_id]

        # Generate the figure and axes common to all of these.
        fig = pyplot.Figure()
        axis = fig.add_subplot(1,1,1)

        # Get information on the run
        ids_search_l = []
        for curr_id in run_ids_l:
            if not self.__run_info_cache.has_key(curr_id):
                ids_search_l.append(curr_id)

        if len(ids_search_l) > 0:
            self.__run_info_cache = dict(
                self.__run_info_cache.items() +
                self.__pgdb.fetchRunInfo(ids_search_l).items())

        run_info = self.__run_info_cache

        # Determine the maximum amount of food
        if not self.__trails_cache.has_key(run_info[run_id]["trails_id"]):
            trail_grid, _, _ = self.__pgdb.getTrailData(
                run_info[run_id]["trails_id"])
            self.__trails_cache[run_info[run_id]["trails_id"]] = trail_grid
        else:
            trail_grid = self.__trails_cache[run_info[run_id]["trails_id"]]

        max_food = np.bincount(np.array(trail_grid.flatten())[0])[1]

        # Find the network name, trail name, and number of generations.
        net_name   = self.__network_list_cache[run_info[run_id]["networks_id"]]
        trail_name = self.__trail_list_cache[run_info[run_id]["trails_id"]]
        num_gens   = run_info[run_id]["generations"]
        max_moves  = np.array(run_info[run_id]["moves_limit"])

        # Take each run and now fetch data for each.
        ids_search_l = []
        for curr_id in run_ids_l:
            if not self.__gen_data_cache.has_key(curr_id):
                ids_search_l.append(curr_id)

        if len(ids_search_l) > 0:
            self.__gen_data_cache = dict(
                self.__gen_data_cache.items() +
                self.__pgdb.fetchRunGenerations(ids_search_l).items())

        gens_data = self.__gen_data_cache

        x = np.linspace(0, num_gens - 1, num=num_gens)

        if group:
            for curr_stat in stat:

                data_set = np.zeros((num_gens))

                for curr_gen in range(0, num_gens):
                    if stat_group == "moves_stats":
                        curr_stat_group = "moves"
                    else:
                        curr_stat_group = stat_group

                    this_gen = []
                    for curr_run in run_ids_l:
                        this_gen.append(gens_data[curr_run][curr_gen]
                            [curr_stat_group][curr_stat])

                    data_set[curr_gen] = np.mean(this_gen)

                axis.plot(x, data_set, '-', label=curr_stat.title())

                plot_title = (
                    "Mean - {0} - {1} g{2}/p{3}".format(
                        net_name,
                        trail_name,
                        num_gens,
                        run_info[run_id]["population"]))

                axis.set_title(plot_title)

        else:
            for curr_run in run_ids_l:
                for curr_stat in stat:

                    data_set = np.zeros((num_gens))

                    for curr_gen in range(0, num_gens):
                        if stat_group == "moves_stats":
                            curr_stat_group = "moves"
                        else:
                            curr_stat_group = stat_group

                        data_set[curr_gen] = (
                            gens_data[curr_run][curr_gen]
                                [curr_stat_group][curr_stat])


                    axis.plot(x, data_set, '-', label=curr_stat.title())


                    plot_title = (
                        "{0} - {1} g{2}/p{3}".format(
                            net_name,
                            trail_name,
                            num_gens,
                            run_info[run_id]["population"]))

                    axis.set_title(plot_title)

        # Determine the maximum type to show.
        if stat_group == "food":
            axis.plot(x, np.repeat(np.array(max_food), num_gens), 'r--')
            axis.axis((0, num_gens, 0, max_food + 5))
            axis.set_ylabel("Food Consumed")
            axis.set_xlabel("Generations")
            axis.legend(loc="best")
        elif stat_group == "moves":
            axis.plot(x, np.repeat(
                np.array(max_moves),
                num_gens), 'r--')
            axis.axis((0, num_gens, 0, max_moves + 5))
            axis.set_ylabel("Moves Taken")
            axis.set_xlabel("Generations")
            axis.legend(loc="lower left")
        elif stat_group == "moves_stats":
            axis.axis((0, num_gens, 0, max_moves + 5))
            axis.set_ylabel("Moves Taken")
            axis.set_xlabel("Generations")
            axis.legend(loc="upper left", ncol=2)


        fig.set_facecolor('w')

        return (self.__createImage(fig, ext), len(run_ids_l))


    def sweepChart(self, ext="png", stat_group="food",
        stat="max", sweep="dl_length", gp_group=0, net_group=0):


        gen_pops = [
            (200, 300),
            (400, 150),
            (600, 100),
            (800, 75)
        ]

        networks = [
            range(2 , 11),
            range(11, 20),
            range(20, 29),
            range(29, 38)
        ]

        titles = [
            "MDLn (2n, 5, 4) g{0}/p{1}",
            "MDLn (2n, 5, 3) g{0}/p{1}",
            "MDLn (2n, 1, 4) g{0}/p{1}",
            "MDLn (2n, 1, 3) g{0}/p{1}"
        ]

        x = range(2, 11)

        fig = pyplot.Figure()
        axis = fig.add_subplot(1,1,1)

        gen = gen_pops[gp_group][0]
        pop = gen_pops[gp_group][1]

        for curr_stat in "min", "max", "avg":

            y = []

            for curr_net in networks[net_group]:
                curr_run_id = self.__pgdb.getFirstRunId(curr_net, gen, pop)
                y.append(self.__pgdb.getStatAverageLikeRunId(curr_run_id,
                    group=stat_group, stat=curr_stat, generation=gen - 1))

            max_food = 89
            max_moves = 325

            axis.plot(x, y, label=curr_stat.title())

        axis.set_title(titles[net_group].format(gen, pop))

        # Determine the maximum type to show.
        if stat_group == "food":
            axis.plot(x, np.repeat(np.array(max_food), len(x)), 'r--')
            axis.axis((2, 10, 0, max_food + 5))
            axis.set_ylabel("Food Consumed")
            axis.set_xlabel("Delay Line Length")
            axis.legend(loc="best")
        elif stat_group == "moves":
            axis.plot(x, np.repeat(
                np.array(max_moves),
                len(x)), 'r--')
            axis.axis((2, 10, 0, max_moves + 5))
            axis.set_ylabel("Moves Taken")
            axis.set_xlabel("Delay Line Length")
            axis.legend(loc="lower left")
        elif stat_group == "moves_stats":
            axis.axis((2, 10, 0, max_moves + 5))
            axis.set_ylabel("Moves Taken")
            axis.set_xlabel("Delay Line Length")
            axis.legend(loc="upper left", ncol=2)

        fig.set_facecolor('w')

        return (self.__createImage(fig, ext), len(y))


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


    def __cacheInit(self):
        """ Initalizes the cached information that is common
        across the functions.

        """
        # Fetch the network and trail list.
        self.__network_list_cache = self.__pgdb.getNetworks()
        self.__trail_list_cache   = self.__pgdb.getTrails()
