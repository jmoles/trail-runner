import datetime
import os
import StringIO
import base64
from flask import Flask, render_template, request, make_response, url_for
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as pltagg
import mimetypes
import numpy as np

from flask_wtf import Form
import wtforms

from GATools.DBUtils import DBUtils
from GATools.plot.chart import chart

DEBUG = True
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
WTF_I18N_ENABLED = False

app = Flask(__name__)
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
    "/plot_img_old/<int:plot_type>/<int:network>/" +
    "<int:trail>/<int:gen>/<int:pop>/<ext>")
def plot_img_old(plot_type, network=0, trail=0, gen=0, pop=0, ext="jpg", inline=False):
    """ Generates an image of specified by ext.

    Keyword arguments:
    plot_type -- The type of plot to generate with this enumeration:
        0 : Plot all matching runs with generations on x-axis.
        1 : Plot all matching runs with max atfinal generation plotted
            against networks sweeping from 2 up to 10. Network is ignored
            for this search.

    """

    # Generate the figure and axes common to all of these.
    fig = plt.Figure()
    axis = fig.add_subplot(1,1,1)

    # Determine the maximum amount of food
    traiL_grid, _, _ = pgdb.getTrailData(trail)
    max_food = np.bincount(np.array(traiL_grid.flatten())[0])[1]

    if plot_type == 0:
        # Fetch all of the run ids that match the criteria.
        ids_l = pgdb.findRuns(network, trail, gen, pop)

        # Take each run and now fetch data for each.
        gens_data = pgdb.fetchRunGenerations(ids_l)

        # Find the network name.
        net_name = pgdb.getNetworks()[network]

        # Find the trail name.
        trail_name = pgdb.getTrails()[trail]

        # Manipulate thie data into preperation for a plot.
        plot_data = np.zeros((len(gens_data), gen))

        item_idx = 0
        for curr_gdata in gens_data:
            for curr_gen in range(0, gen):
                print plot_data
                plot_data[item_idx][curr_gen] = (
                    curr_gdata[curr_gen]["food"]["max"])
            item_idx = item_idx + 1

        x = np.linspace(0, gen - 1, num=gen)

        plot_title = (
            "{0} - {1} g{2}/p{3}".format(
                net_name, trail_name, gen, pop))

        axis.plot(x, np.transpose(plot_data), '-')
        axis.plot(x, np.repeat(np.array(max_food), gen), 'r--')
        axis.axis((0, gen, 0, max_food + 5))
        axis.set_xlabel("Generations")
        axis.set_ylabel("Food Consumed")
        axis.set_title(plot_title)

    elif plot_type == 1:
        nets = [4, 5, 7, 3, 8, 9, 10, 11, 12]

        max_foods = []

        # Go through each network and get the maximum at the generation.
        for curr_net in nets:
            # Fetch all of the run ids that match the criteria.
            ids_l = pgdb.findRuns(curr_net, trail, gen, pop)

            curr_val = pgdb.getMaxFoodAtGeneration(ids_l, gen)

            max_foods.append(curr_val)

        x = np.linspace(2, 10, num=9)

        plot_title = (
            "Max food sweep with MDLn (2n)-1-4 Networks g{0}/p{1}".format(
                gen, pop))
        axis.plot(x, max_foods, '-')
        axis.plot(x, np.repeat(np.array(max_food), len(x)), 'r--')
        axis.axis((min(x), max(x), 0, max_food + 5))
        axis.set_xlabel("Delay Line Length")
        axis.set_ylabel("Food Consumed")
        axis.set_title(plot_title)

    canvas = pltagg.FigureCanvasAgg(fig)
    output = StringIO.StringIO()

    if ext == "tif" or ext == "tiff":
        canvas.print_tif(output)
    elif ext == "bmp":
        canvas.print_bmp(output)
        this_mime = "image/bmp"
    elif ext == "eps":
        canvas.print_eps(output)
        this_mime = "application/postscript"
    elif ext == "png":
        canvas.print_png(output)
        this_mime = "image/png"
    elif ext == "pdf":
        canvas.print_pdf(output)
        this_mime = "application/pdf"
    elif ext == "svg":
        canvas.print_svg(output)
        this_mime = "image/svg+xml"
    else:
        canvas.print_jpg(output)
        this_mime = "image/jpg"
        ext = "jpg"

    if (inline):
        return base64.b64encode(output.getvalue()), plot_title
    else:
        response = make_response(output.getvalue())
        response.mimetype = this_mime
        response.headers['Content-Disposition'] = (
            'filename=plot.{0}'.format(ext))
        return response


@app.route(
    "/plot_old/<int:plot_type>/<int:network>/<int:trail>/<int:gen>/<int:pop>")
def plot_old(plot_type, network, trail, gen, pop):
    start = datetime.datetime.now()

    output, plot_title = plot_img(
        plot_type, network, trail, gen, pop, "png", True)

    finish_time_s = str((datetime.datetime.now() - start).total_seconds())

    pdf_url = url_for(
        'plot_img', plot_type=plot_type, network=network,
        trail=trail, gen=gen, pop=pop, ext="pdf")

    eps_url = url_for(
        'plot_img', plot_type=plot_type, network=network,
        trail=trail, gen=gen, pop=pop, ext="eps")

    jpg_url = url_for(
        'plot_img', plot_type=plot_type, network=network,
        trail=trail, gen=gen, pop=pop, ext="jpg")

    return render_template(
        "plot_results.html", title=plot_title, image_data=output,
        time_sec=finish_time_s, pdf_url=pdf_url, eps_url=eps_url,
        jpg_url=jpg_url)

@app.route('/plot/', defaults={'run_id': 1})
@app.route('/plot/run_id/<int:run_id>')
def plot_by_run_id(run_id):
    start = datetime.datetime.now()

    ch = chart()
    output, plot_title = plot_img(run_id, "png", inline=True)

    finish_time_s = str((datetime.datetime.now() - start).total_seconds())

    pdf_url = url_for(
        'plot_img', run_id=run_id, ext="pdf")

    eps_url = url_for(
        'plot_img', run_id=run_id, ext="eps")

    jpg_url = url_for(
        'plot_img', run_id=run_id, ext="jpg")

    images_l = []
    image_d  = {}
    image_d["data"] = output
    image_d["pdf"]  = pdf_url
    image_d["eps"]  = eps_url
    image_d["jpg"]  = jpg_url
    images_l.append(image_d)

    return render_template(
        "plot_results.html", title=plot_title, images_l=images_l,
        time_sec=finish_time_s)

@app.route("/plot/img/<int:run_id>/<ext>")
def plot_img(run_id, ext="png", inline=False):
    ch = chart()

    output, plot_title = ch.lineChart([run_id], ext)

    if (inline):
        return base64.b64encode(output.getvalue()), plot_title
    else:
        response = make_response(output.getvalue())
        response.mimetype = mimetypes.guess_type("plot.{0}".format(ext))[0]
        response.headers['Content-Disposition'] = (
            'filename=plot.{0}'.format(ext))
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


if __name__ == '__main__':
    app.run(debug=True)
