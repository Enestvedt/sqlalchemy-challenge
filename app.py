# ## Step 2 - Climate App

## Dependencies
import numpy as np
import datetime as dt
import re

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

from logging import debug, error
from flask import Flask, jsonify

# * Use Flask to create your routes.
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()

Base.prepare(engine, reflect=True)
Inspector = inspect(engine)

my_tables = Base.classes.keys()

Station = Base.classes.station
Measurement = Base.classes.measurement


app = Flask(__name__)

# ### Routes
#   * Home page.
#   * List all routes that are available.

@app.route("/")
@app.route("/home")
@app.route("/index")
def index():
    print("access to home page")
    return """<h1>Welcome to the Hawaii Weather Database!</h1>
    <br>
    <h3>Available Routes:</h3>
    <a href = '/api/v1.0/precipitation'target="blank">/api/v1.0/precipitation<a>
    <br>
    <a href = '/api/v1.0/stations'target="blank">/api/v1.0/stations<a>
    <br>
    <a href = '/api/v1.0/tobs'target="blank">/api/v1.0/tobs<a>
    <br>
    <a href = '/api/v1.0/' target='blank'>/api/v1.0</a>
    """


# * `/api/v1.0/precipitation`
#   * Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
#   * Return the JSON representation of your dictionary.

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    prcp_rslt = []
    for result in session.query(Measurement.date, Measurement.prcp).all():
        prcp_rslt.append({result.date: result.prcp})

    session.close()

    return jsonify(prcp_rslt)


# * `/api/v1.0/stations`
#   * Return a JSON list of stations from the dataset.

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    sttn_data = []

    def object_as_dict(obj):
        return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

    query = session.query(Station)

    for station in query:
        sttn_data.append(object_as_dict(station))
    
    session.close()

    return jsonify(sttn_data)


# * `/api/v1.0/tobs`
#   * Query the dates and temperature observations of the most active station for the last year of data. 
#   * Return a JSON list of temperature observations (TOBS) for the previous year.

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    max_date = session.query(func.max(Measurement.date)).scalar()
    max_date = dt.datetime.strptime(max_date, '%Y-%m-%d')
    start_date = max_date - dt.timedelta(days=730)
    end_date = (max_date - dt.timedelta(days=365))

    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')

    active_station = (session.query(Measurement.station)
        .filter(Measurement.date >= end_date)
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc()).first()[0])

    result = (session.query(Measurement.tobs)
        .filter(Measurement.station == active_station)
        .filter(Measurement.date >= start_date)
        .filter(Measurement.date <= end_date)
        .all())
    result = list(np.ravel(result))

    session.close()

    return jsonify(result)


# * `/api/v1.0/<start>` and `/api/v1.0/<start>/<end>`
#   * Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
#   * When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
#   * When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.

@app.route("/api/v1.0/")
def dates_route():
    print("Access to Date Search Home")
    return """<h1>Hawaii Weather Database Date Search Home!</h1>
    <br>
    <h3>Date-based Searches:</h3>
    <p>/api/v1.0/&lt;start&gt;</p>
    <p>/api/v1.0/&ltstart&gt;/&lt;end&gt;</p>

    In the URL, replace the &lt;start&gt; or the &lt;start&gt; and &lt;end&gt; with dates in the yyyy-mm-dd format to search the database.
    """

@app.route('/api/v1.0/<start>')
def s_date(start=None, end=None):
            
    if isinstance(dt.datetime.strptime(start, '%Y-%m-%d'), dt.date):   
        
        if re.match('\d\d\d\d-\d\d-\d\d', start):  

            session = Session(engine)

            daily_normals = []
            
            date_list = session.query(Measurement.date).filter(Measurement.date >= start).all()
            date_list = list(np.ravel(date_list))

            sel = [Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
            
            for date in date_list:
                result = session.query(*sel).filter(Measurement.date == date).all()
                result = list(np.ravel(result))
                daily_normals.append(result)
            session.close()
            return jsonify(daily_normals)



    return jsonify({"error": "Date not found. Enter as yyyy-mm-dd format.  If you've used this format, try a different date"}), 404


@app.route('/api/v1.0/<start>/<end>')
def e_date(start=None, end=None):
            
    if isinstance(dt.datetime.strptime(start, '%Y-%m-%d'), dt.date) and isinstance(dt.datetime.strptime(end, '%Y-%m-%d'), dt.date):   
        
        if re.match('\d\d\d\d-\d\d-\d\d', start) and re.match('\d\d\d\d-\d\d-\d\d', end):  

            session = Session(engine)

            daily_normals = []
            
            date_list = (session.query(Measurement.date)
                .filter(Measurement.date >= start)
                .filter(Measurement.date <= end)
                .all())

            date_list = list(np.ravel(date_list))

            sel = [Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
            
            for date in date_list:
                result = session.query(*sel).filter(Measurement.date == date).all()
                result = list(np.ravel(result))
                daily_normals.append(result)
            session.close()
            return jsonify(daily_normals)

    return jsonify({"error": "Date not found. Enter as yyyy-mm-dd format.  If you've used this format, try a different date"}), 404



if __name__ == "__main__":
    app.run(debug=True)



