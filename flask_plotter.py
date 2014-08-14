import datetime
import json
import math
import os
import base64
from flask import Flask, render_template, request, make_response, url_for
import mimetypes

from GATools.DBUtils import DBUtils
from GATools.plot.chart import chart

DEBUG = True
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
WTF_I18N_ENABLED = False

app = Flask(__name__)
app.secret_key = SECRET_KEY

pgdb = DBUtils()

def get_trails():
    print pgdb.getTrails().items()
    return pgdb.getTrails().items()

def get_networks():
    print pgdb.getNetworks().items()
    return pgdb.getNetworks().items()

@app.route(
    '/',
    defaults={
        'filters' :
            json.dumps({'generations' : 200, 'moves_limit': 200})
        })
@app.route('/filter/<filters>')
def index(filters):
    """ Renders the home page showing a table of results.

    """
    filters_d = json.loads(filters)

    table_data = pgdb.table_listing(filters=filters_d)

    return render_template(
        "home.html",
        table_data=table_data)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/config/<int:config_id>')
def config_by_id(config_id):
    start = datetime.datetime.now()

    group_images_l = []

    ch = chart()

    for c_elem in ("food", "moves", "moves_stats"):
        output, multiple_run_count = plot_by_config_id(
            config_id=config_id,
            ext="svg",
            stat_group=c_elem,
            inline=True,
            show_title=False)

        pdf_url = url_for(
            'plot_by_config_id',
            config_id=config_id,
            ext="pdf",
            stat_group=c_elem,
            show_title=False)

        eps_url = url_for(
            'plot_by_config_id',
            config_id=config_id,
            ext="eps",
            stat_group=c_elem,
            show_title=False)

        jpg_url = url_for(
            'plot_by_config_id',
            config_id=config_id,
            ext="jpg",
            stat_group=c_elem,
            show_title=False)

        png_url = url_for(
            'plot_by_config_id',
            config_id=config_id,
            ext="png",
            stat_group=c_elem,
            show_title=False)

        image_d  = {}
        image_d["data"] = output
        image_d["pdf"]  = pdf_url
        image_d["eps"]  = eps_url
        image_d["jpg"]  = jpg_url
        image_d["png"]  = png_url
        if c_elem == "food":
            image_d["title"] = "Food vs. Generations"
        elif c_elem == "moves":
            image_d["title"] = "Moves vs. Generations"
        elif c_elem == "moves_stats":
            image_d["title"] = "Move Types vs. Generations"
        else:
            image_d["title"] = "Unknown Type"

        group_images_l.append(image_d)

    config_info =  pgdb.fetchConfigInfo(config_id)

    trail_name   = pgdb.getTrails()[config_info["trails_id"]]
    network_name = pgdb.getNetworks()[config_info["networks_id"]]
    mutate_name  = pgdb.getMutates()[config_info["mutate_id"]]

    table_data   = pgdb.fetchConfigRunsInfo(config_id)
    for row in table_data:
        row["run_date"] = row["run_date"].strftime("%c")

    finish_time_s = str((datetime.datetime.now() - start).total_seconds())

    return render_template(
        "run_config.html",
        config_id      = config_id,
        run_config     = config_info,
        group_images_l = group_images_l,
        time_sec       = finish_time_s,
        num_runs       = multiple_run_count,
        trail_name     = trail_name,
        network_name   = network_name,
        mutate_name    = mutate_name,
        table_data     = table_data)

@app.route('/trail/<int:trail_id>')
def trail_by_id(trail_id):
    return render_template('404.html'), 404

@app.route('/network/<int:network_id>')
def network_by_id(network_id):
    return render_template('404.html'), 404

@app.route('/run/<int:run_id>')
def plot_by_run_id(run_id):
    start = datetime.datetime.now()

    images_l       = []

    ch = chart()

    for c_elem in ("food", "moves", "moves_stats"):
        output, plot_title = plot_img(
            run_id=run_id, ext="svg", stat_group=c_elem, inline=True,
            show_title=False)

        pdf_url = url_for(
            'plot_img', run_id=run_id, ext="pdf", stat_group=c_elem,
            group=False, show_title=False)

        eps_url = url_for(
            'plot_img', run_id=run_id, ext="eps", stat_group=c_elem,
            group=False, show_title=False)

        jpg_url = url_for(
            'plot_img', run_id=run_id, ext="jpg", stat_group=c_elem,
            group=False, show_title=False)

        png_url = url_for(
            'plot_img', run_id=run_id, ext="jpg", stat_group=c_elem,
            group=False, show_title=False)

        image_d  = {}
        image_d["data"]  = output
        image_d["pdf"]   = pdf_url
        image_d["eps"]   = eps_url
        image_d["jpg"]   = jpg_url
        image_d["png"]   = png_url
        if c_elem == "food":
            image_d["title"] = "Food vs. Generations"
        elif c_elem == "moves":
            image_d["title"] = "Moves vs. Generations"
        elif c_elem == "moves_stats":
            image_d["title"] = " Move Types vs. Generations"
        else:
            image_d["title"] = "Unknown Type"
        images_l.append(image_d)

    run_information =  pgdb.fetchRunInfo(run_id)[run_id]
    run_information["run_date"] = run_information["run_date"].strftime("%c")
    runtime_sec = run_information["runtime"].total_seconds()
    run_information["runtime"] = '{:02}:{:02}:{:02}'.format(
        int(round(runtime_sec // 3600)),
        int(round(runtime_sec % 3600 // 60)),
        int(round(runtime_sec % 60)))

    trail_name   = pgdb.getTrails()[run_information["trails_id"]]
    network_name = pgdb.getNetworks()[run_information["networks_id"]]
    mutate_name  = pgdb.getMutates()[run_information["mutate_id"]]

    finish_time_s = str((datetime.datetime.now() - start).total_seconds())

    return render_template(
        "plot_results.html",
        run_id=run_id,
        run_info=run_information,
        images_l=images_l,
        time_sec=finish_time_s,
        trail_name=trail_name,
        network_name=network_name,
        mutate_name=mutate_name)

@app.route("/plot/line/config_id/<int:config_id>/<ext>/<stat_group>")
def plot_by_config_id(config_id, ext="png", stat_group ="food",
    inline=False, chart_inst=chart(), show_title=True):

    #TODO: Fix isdsue with variables here.
    print show_title

    print request.args.get('show_title')

    output, plot_title = chart_inst.lineChartByConfigId(config_id, ext,
        stat_group=stat_group, title=show_title)

    if (inline):
        return base64.b64encode(output.getvalue()), plot_title
    else:
        response = make_response(output.getvalue())
        response.mimetype = mimetypes.guess_type("plot.{0}".format(ext))[0]
        response.headers['Content-Disposition'] = (
            'filename=plot.{0}'.format(ext))
        return response

@app.route("/plot/img/<int:run_id>/<ext>/<stat_group>/<group>")
def plot_img(run_id, ext="png", stat_group="food", group=False, inline=False,
    chart_inst=chart(), chart_type="line", gp_group=0, net_group=0,
    show_title=True):
    """ Plots an image of all run_ids that match run_id.

    The returned image will be of type ext.
    Valid stat_group for plotting are:
        food, moves, moves_stats
    If group is True, will take the average across all runs with same
        run parameters as run_id.

    """
    if chart_type == "line":
        output, plot_title = chart_inst.lineChart(run_id, ext,
            stat_group=stat_group, group=group, title=show_title)
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



if __name__ == '__main__':
    app.run(
        debug=True,
        host="0.0.0.0"
        )
