#!/usr/bin/python3
#
# CGI script for rendering a HTML page with RXB6 sensor data
#
# Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.

import cgitb
cgitb.enable()  # for troubleshooting

import sqlite3
import sys
import traceback


def get_data(db, sensors=None):
    """
    Get the data for the specified sensors from the database
    """
    result = {}

    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM data")
        rows = cur.fetchall()

        for row in rows:
            sensor = row[1]
            if not sensors or sensor in sensors:
                if sensor not in result:
                    result[sensor] = []
                result[sensor].append(row)

    return result


def data2array(data):
    """
    Convert a list of lists to a javascript array
    """
    table = []

    # Header
    table.append("['%s','%s']" % tuple(data[0]))

    # Data
    for d in data[1:]:
        # First column is always a date. Google wants milliseconds since the
        # epoch.
        table.append("[new Date(%s),%s]" % (int(d[0] / 60) * 60000, d[1]))

    return "[" + ",".join(table) + "]"


def render_page():
    """
    Render the HTML page
    """
    data = get_data("./rxb6.db")

    sensor = "2491:1"

    # Convert the data

    temperature = [[d[0], d[2]] for d in data[sensor]]
    temperature.insert(0, ["Date", sensor])
    temperature_array = data2array(temperature)

    humidity = [[d[0], d[3]] for d in data[sensor]]
    humidity.insert(0, ["Date", sensor])
    humidity_array = data2array(humidity)

    print("""
<html>
  <head>
    <title>RXB6 Temperature and Humidity</title>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {'packages':['corechart']});
      google.charts.setOnLoadCallback(drawTemperature);
      google.charts.setOnLoadCallback(drawHumidity);

      var global_options = {
        curveType: 'function',
        legend: { position: 'right' },
        hAxis: {
          gridlines: {
            units: {
              days: {format: ['MMM dd']},
              hours: {format: ['HH:mm']},
            }
          }
        }
      };

      function drawTemperature() {
        var data = google.visualization.arrayToDataTable(""" + temperature_array + """);
        var chart = new google.visualization.LineChart(document.getElementById('temperature'));
        var options = global_options;
        options.title = 'Temperature [C]';
        chart.draw(data, options);
      }

      function drawHumidity() {
        var data = google.visualization.arrayToDataTable(""" + humidity_array + """);
        var chart = new google.visualization.LineChart(document.getElementById('humidity'));
        var options = global_options;
        options.title = 'Humidity [%]';
        chart.draw(data, options);
      }
    </script>
  </head>
  <body>
    <div id="temperature" style="width: 900px; height: 500px"></div>
    <div id="humidity" style="width: 900px; height: 500px"></div>
  </body>
</html>
    """)


# -----------------------------------------------------------------------------
# Main entry point

try:
    render_page()
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
    print("<html><body><pre>%s</pre></body></html>" % "".join(tb))
