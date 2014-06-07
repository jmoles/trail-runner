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

@app.route('/plot/', defaults={'run_id': 1})
@app.route('/plot/run_id/<int:run_id>')
def plot_by_run_id(run_id):
    start = datetime.datetime.now()

    images_l       = []
    group_images_l = []

    ch = chart()

    for c_elem in ("food", "moves", "moves_stats"):
        output, _ = plot_img(
            run_id=run_id, ext="png", stat_group=c_elem, inline=True,
            chart_inst=ch)

        pdf_url = url_for(
            'plot_img', run_id=run_id, ext="pdf", stat_group=c_elem,
            group=False, chart_inst=ch)

        eps_url = url_for(
            'plot_img', run_id=run_id, ext="eps", stat_group=c_elem,
            group=False, chart_inst=ch)

        jpg_url = url_for(
            'plot_img', run_id=run_id, ext="jpg", stat_group=c_elem,
            group=False, chart_inst=ch)

        image_d  = {}
        image_d["data"] = output
        image_d["pdf"]  = pdf_url
        image_d["eps"]  = eps_url
        image_d["jpg"]  = jpg_url
        images_l.append(image_d)

    for c_elem in ("food", "moves", "moves_stats"):
        output, multiple_run_count = plot_img(
            run_id=run_id, ext="png", stat_group=c_elem, group=True,
            inline=True, chart_inst=ch)

        pdf_url = url_for(
            'plot_img', run_id=run_id, ext="pdf", stat_group=c_elem,
            group=True, chart_inst=ch)

        eps_url = url_for(
            'plot_img', run_id=run_id, ext="eps", stat_group=c_elem,
            group=True, chart_inst=ch)

        jpg_url = url_for(
            'plot_img', run_id=run_id, ext="jpg", stat_group=c_elem,
            group=True, chart_inst=ch)

        image_d  = {}
        image_d["data"] = output
        image_d["pdf"]  = pdf_url
        image_d["eps"]  = eps_url
        image_d["jpg"]  = jpg_url
        group_images_l.append(image_d)

    finish_time_s = str((datetime.datetime.now() - start).total_seconds())

    return render_template(
        "plot_results.html",
        title="Run ID {0} Plots".format(run_id),
        images_l=images_l, group_images_l=group_images_l,
        time_sec=finish_time_s, multiple_run_count=multiple_run_count)

@app.route("/plot/img/<int:run_id>/<ext>/<stat_group>/<group>")
def plot_img(run_id, ext="png", stat_group="food", group=False, inline=False,
    chart_inst=chart(), chart_type="line", gp_group=0, net_group=0):
    """ Plots an image of all run_ids that match run_id.

    The returned image will be of type ext.
    Valid stat_group for plotting are:
        food, moves, moves_stats
    If group is True, will take the average across all runs with same
        run parameters as run_id.

    """
    if chart_type == "line":
        output, plot_title = chart_inst.lineChart(run_id, ext,
            stat_group=stat_group, group=group)
    elif chart_type == "sweep":
        output, plot_title = chart_inst.sweepChart(ext="png",
            stat_group=stat_group, stat="max", sweep="dl_length",
            gp_group=gp_group, net_group=net_group)

    if (inline):
        return base64.b64encode(output.getvalue()), plot_title
    else:
        response = make_response(output.getvalue())
        response.mimetype = mimetypes.guess_type("plot.{0}".format(ext))[0]
        response.headers['Content-Disposition'] = (
            'filename=plot.{0}'.format(ext))
        return response

@app.route("/plot_sweep/")
def plot_sweep():
    start = datetime.datetime.now()

    ch = chart()

    run_id = 0

    images_l = []

    for c_grp in range(0, 4):
        for c_netgrp in range(0, 4):

            output, multiple_run_count = plot_img(
                run_id=0, ext="png", stat_group="food", group=True,
                inline=True, chart_inst=ch, chart_type="sweep",
                gp_group=c_grp, net_group=c_netgrp)

            pdf_url = url_for(
                'plot_img', run_id=0, ext="pdf", stat_group="food",
                group=True, chart_inst=ch, chart_type="sweep",
                gp_group=c_grp, net_group=c_netgrp)

            eps_url = url_for(
                'plot_img', run_id=0, ext="eps", stat_group="food",
                group=True, chart_inst=ch, chart_type="sweep",
                gp_group=c_grp, net_group=c_netgrp)

            jpg_url = url_for(
                'plot_img', run_id=0, ext="jpg", stat_group="food",
                group=True, chart_inst=ch, chart_type="sweep",
                gp_group=c_grp, net_group=c_netgrp)

            image_d  = {}
            image_d["data"] = output
            image_d["pdf"]  = pdf_url
            image_d["eps"]  = eps_url
            image_d["jpg"]  = jpg_url
            images_l.append(image_d)


    finish_time_s = str((datetime.datetime.now() - start).total_seconds())

    return render_template(
        "plot_results.html",
        title="Sweep Charts with Moves Limit: {0}".format(325),
        images_l=images_l, group_images_l=None,
        time_sec=finish_time_s, multiple_run_count=None)


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
