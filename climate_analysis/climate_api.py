from flask import Flask, jsonify, render_template
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

##### GLOBAL VARIABLE #####
year_ago = dt.date(2017,8,23)- dt.timedelta(days=365)


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Open session
    session = Session(engine)
    # Return query result for precipitation by date
    prcp_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago).all()
    # Close session
    session.close()
    pcrp_dict = {}
    pcrp_results={"results":pcrp_dict}
    for date, pcrp in prcp_data:
        pcrp_dict[f"{date}"]= pcrp
    return jsonify(pcrp_results)

@app.route("/api/v1.0/stations")
def stations():
    # Open session
    session = Session(engine)
    # Query for all station ids & common names
    all_stations = session.query(Station.station, Station.name).\
        group_by(Station.station).all()
    # Close session
    session.close()
    # Initalize dictionary to hold results for json conversion
    stations_dict = {}
    stations_results = {"results": stations_dict}
    # Loop through data & create dictionary. Then jsonify dictionary for API
    for station, name in all_stations:
        stations_dict[f"{station}"] = name
    return jsonify(stations_results)

@app.route("/api/v1.0/tobs")
def tobs():
    # Open session
    session = Session(engine)
    '''Query the dates and temperature observations of the most active station for the last year of data.
    Return a JSON list of temperature observations (TOBS) for the previous year.'''
    active_station_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= year_ago).\
        filter(Measurement.station == 'USC00519281').all()
    # Close session
    session.close()
    tobs_dict = {}
    tobs_results={"results": tobs_dict}
    for date, tobs in active_station_data:
        tobs_dict[f"{date}"]= tobs
    return jsonify(tobs_results)



if __name__ == "__main__":
    app.run(debug=True)