# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from datetime import datetime
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
base = automap_base()
# reflect the tables

base.prepare(autoload_with=engine)
# Save references to each table
measurement = base.classes.measurement
station = base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/station<br/>"
        f"//api/v1.0/tobs<br/>"
        f"//api/v1.0/start_date<br/>"
        f"//api/v1.0/start_date/end_date<br/>"

    )
# precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():

# most recent date
    result = session.query(func.max(measurement.date)).all()
    max_date_str = result[0][0] if len(result) > 0 else None
    max_date = dt.datetime.strptime(max_date_str, "%Y-%m-%d").date()

# precipitation data for the last year in the database 
    prev_year = max_date - dt.timedelta(days=365)
    precipitation_results = session.query(measurement.date, measurement.prcp).filter(measurement.date >= prev_year).all()

    precipitation_data = dict()
    for date, prcp in precipitation_results:
        precipitation_data[date] = prcp

    session.close()
    return jsonify(precipitation_data)

# station route
# Returns jsonified data of all of the stations in the database

@app.route("/api/v1.0/station")


def get_station():
    station_results = session.query(
        station.id,
        station.station,
        station.name,
        station.latitude,
        station.longitude,
        station.elevation
    ).all()
    
    station_values = []
    for row in station_results:
        station_dict = {
            "id":       row['id'],
            "station":  row['station'],
            "name": row['name'],
            "latitude": row['latitude'],
            "longitude": row['longitude'],
            "elevation": row['elevation'],
        }
        station_values.append(station_dict)

    session.close()
    return jsonify(station_values)

# tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    # most recent date
    result = session.query(func.max(measurement.date)).all()
    max_date_str = result[0][0] if len(result) > 0 else None
    max_date = dt.datetime.strptime(max_date_str, "%Y-%m-%d").date()
    prev_year = max_date - dt.timedelta(days=365)

    # data for the most active station (USC00519281) 
    most_active_stations = session.query(
        measurement.station, 
        func.count(measurement.station)
    ).group_by(
        measurement.station
    ).order_by(func.count(measurement.station).desc()).all()
    station_id = most_active_stations[0][0]

    # returns the jsonified data for the last year of data

    last_year_tob_result = session.query(measurement.id, measurement.station, measurement.date, measurement.prcp,measurement.tobs).\
                            filter(measurement.date >= prev_year, measurement.station == station_id).\
                            order_by(measurement.date).all()

    date_tobs_values = []
    for row in last_year_tob_result:
        tobs_dict = {
            "id": row["id"],
            "station": row["station"],
            "date": row["date"],
            "prcp": row["prcp"],
            "tobs": row["tobs"]
        }
        date_tobs_values.append(tobs_dict)

    session.close() 
    return jsonify(date_tobs_values)

# start route
@app.route("/api/v1.0/<start>")
def start_date_tobs(start):
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use format: YYYY-MM-DD.'}), 400
    
    # min, max, and average temperatures calculated from the given start date to the end of the dataset

    start_date_result = session.query(func.min(measurement.tobs),
                          func.max(measurement.tobs),
                          func.avg(measurement.tobs)).filter(measurement.date >= start_date).one()

    min, max, avg = start_date_result
    start_date_dict = {
        "min_temp": min,
        "max_temp": max,
        "avg_temp": avg
    }

    session.close()
    return jsonify(start_date_dict)

# start/end route

@app.route("/api/v1.0/<start_date>/<end_date>")
def start_end_date(start_date, end_date):
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use format: YYYY-MM-DD.'}), 400
    
    # min, max, and average temperatures calculated from the given start date to the given end date

    start_end_date_result = session.query(
        func.min(measurement.tobs),
        func.max(measurement.tobs),
        func.avg(measurement.tobs)
    ).filter(
        measurement.date >= start_date
    ).filter(
        measurement.date <= end_date
    ).one()
    
    min, max, avg = start_end_date_result
    start_end_date_dict = {
        "min_temp": min,
        "max_temp": max,
        "avg_temp": avg
    }

    session.close()
    return jsonify(start_end_date_dict)


if __name__ == '__main__':
    app.run(debug=True)