import datetime
import os
import StringIO
from flask import Flask, render_template, request, make_response
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as pltagg
import numpy as np

from flask_wtf import Form
import wtforms

from GATools.DBUtils import DBUtils

DEBUG = True
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
WTF_I18N_ENABLED = False

app = Flask(__name__, static_folder="static")
app.secret_key = SECRET_KEY

pgdb = DBUtils()

class MultiCheckboxField(wtforms.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False, html_tag="ol")


class MyForm(Form):
    name     = wtforms.TextField('name')
    networks = MultiCheckboxField(u'Network',
        choices=pgdb.getNetworks().items())
    trails   = MultiCheckboxField(u'Trails',
        choices=pgdb.getTrails().items())


def get_trails():
    return pgdb.getTrails().items()

def get_networks():
    return pgdb.getNetworks().items()


@app.route("/", methods=("GET", "POST"))
def index():
    form = MyForm()
    if form.validate_on_submit():
        pass
    return render_template("plot_form.html", form=form,
        get_trails=get_trails,
        get_networks=get_networks)

@app.route(
    "/plot/<int:type>/<int:network>/<int:trail>/<int:gen>/<int:pop>")
def do_plot(type, network, trail, gen, pop):
    start = datetime.datetime.now()

    # Fetch all of the run ids that match the criteria.
    ids_l = pgdb.findRuns(network, trail, gen, pop)

    print "IDs Query Time " + str(datetime.datetime.now() - start)

    # Take each run and now fetch data for each.
    start = datetime.datetime.now()
    gens_data = pgdb.fetchRunGenerations(ids_l)
    # gens_data = []
    # for curr_id in ids_l:
    #     gens_data.append(pgdb.fetchRunGenerations(curr_id))

    print "Gens Query Time " + str(datetime.datetime.now() - start)

    # Find the network name.
    start = datetime.datetime.now()
    net_name = pgdb.getNetworks()[network]
    print "Network Name Query Time " + str(datetime.datetime.now() - start)

    # Find the trail name.
    start = datetime.datetime.now()
    trail_name = pgdb.getTrails()[trail]
    print "Trail Name Query Time " + str(datetime.datetime.now() - start)

    # Determine the maximum amount of food
    start = datetime.datetime.now()
    traiL_grid, _, _ = pgdb.getTrailData(trail)
    print "Trail Data Query Time " + str(datetime.datetime.now() - start)
    max_food = np.bincount(np.array(traiL_grid.flatten())[0])[1]

    # Manipulate thie data into preperation for a plot.
    plot_data = np.zeros((len(gens_data), gen))

    item_idx = 0
    for curr_gdata in gens_data:
        for curr_gen in range(0, gen):
            plot_data[item_idx][curr_gen] = curr_gdata[curr_gen]["food"]["max"]
        item_idx = item_idx + 1

    x = np.linspace(0, gen - 1, num=gen)

    fig = plt.Figure()
    axis = fig.add_subplot(1,1,1)

    axis.plot(x, np.transpose(plot_data), '-')
    axis.plot(x, np.repeat(np.array(max_food), gen), 'r--')
    axis.axis((0, gen, 0, max_food + 5))
    axis.set_xlabel("Generations")
    axis.set_ylabel("Food Consumed")
    axis.set_title(net_name + " - " + trail_name + " g{0}/p{1}".format(gen, pop))

    canvas = pltagg.FigureCanvasAgg(fig)
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = "image/png"
    return response


@app.route("/show.png")
def show_plot():
    fig = plt.Figure()
    axis = fig.add_subplot(1,1,1)
    axis.set_xlabel("Generation")
    axis.set_ylabel("Food Consumed")


    xs = range(100)
    ys = [np.random.randint(1, 50 ) for x in xs]

    axis.plot(xs, ys)



    canvas = pltagg.FigureCanvasAgg(fig)
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = "image/png"
    return response


    pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
