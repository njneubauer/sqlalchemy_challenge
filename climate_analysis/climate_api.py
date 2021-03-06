from flask import Flask, jsonify, render_template
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import numpy as np
import pandas as pd
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
year_ago = dt.date(2017,8,23) - dt.timedelta(days=365)
date_format = '%Y-%m-%d'

@app.route("/")
def index():
    # Call HTML index file
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
        pcrp_dict[date]= pcrp
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
    stations_list = []
    stations_results = {"results": stations_list}
    # Loop through data & create dictionary. Then jsonify dictionary for API
    for station, name in all_stations:
        stations_dict = {}
        stations_dict[station] = name
        stations_list.append(stations_dict)
    return jsonify(stations_results)

@app.route("/api/v1.0/tobs")
def tobs():
    # Open session
    session = Session(engine)

    '''Query the dates and temperature observations of the most active station for the last year of data.
    Return a JSON list of temperature observations (TOBS) for the previous year.'''
    active_station_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= year_ago).\
        filter(Measurement.station == 'USC00519281').all()
  
    # Close session
    session.close()

    # Initialize dictionaries
    tobs_dict = {}
    tobs_results = {'USC00519281': tobs_dict}

    # Loop through data to obtain temperature data for station:'USC00519281'
    for date, tobs in active_station_data:
        tobs_dict[date]= tobs
    return jsonify(tobs_results)


@app.route("/api/v1.0/<start>")
def start(start):
    # Check date format
    try: 
        normalized_date = dt.datetime.strptime(start, date_format).date()
    except:
        return jsonify({"error": f"date {start} format is not supported use: yyyy-mm-dd format"})

    # Open session
    session = Session(engine)
 
    # Obtain min & max date from query
    min_max_date = session.query(func.min(Measurement.date), func.max(Measurement.date)).all()
    
    # Put dates into dataframe to extract dates
    min_max_df = pd.DataFrame(min_max_date, columns={"min", "max"})
    
    # Assign min & max dates to variables
    min_date = min_max_df.iloc[0,0]
    max_date = min_max_df.iloc[0,1]
    
    # convert to datetime date
    min_date_format = dt.datetime.strptime(min_date, date_format).date()
    max_date_format = dt.datetime.strptime(max_date, date_format).date()

    # Check input to make sure date is within dataset range
    if (normalized_date >= min_date_format) and (normalized_date <= max_date_format):
        pass
    else:
        return jsonify({"error":f"Start date {start} out of range. Dataset range is: {min_date_format} to {max_date_format}"}), 404

    '''Return a JSON list of the minimum temperature, the average temperature, 
    and the max temperature for a given start date. When given the start only, 
    calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.'''
    
    # Query for all dates >= start date. Calc tobs: min, max, avg.
    start_only_dates = session.query(func.min(Measurement.date), func.min(Measurement.tobs), func.max(Measurement.tobs), func.round(func.avg(Measurement.tobs),2)).\
        filter(Measurement.date >= normalized_date).all()

    # Close session
    session.close()

    start_only_list = []
    # Loop through dataset and obtain tobs for all dates
    for date, min_tobs, max_tobs, avg_tobs in start_only_dates:
        start_only_dict = {
            "_start date": date,
            "min_temp": min_tobs,
            "max_temp": max_tobs,
            "avg_temp": avg_tobs,
        }
        start_only_list.append(start_only_dict)
    return jsonify(start_only_list)
    
@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
      # Check date format
    try: 
        start_date = dt.datetime.strptime(start, date_format).date()
        end_date = dt.datetime.strptime(end, date_format).date()
    except:
        return jsonify({"error": f"date {start} format is not supported use: yyyy-mm-dd format"})

    # Open session
    session = Session(engine)
 
    # Obtain min & max date from query
    min_max_date = session.query(func.min(Measurement.date), func.max(Measurement.date)).all()
    
    # Put dates into dataframe to extract dates
    min_max_df = pd.DataFrame(min_max_date, columns={"min", "max"})
    
    # Assign min & max dates to variables
    min_date = min_max_df.iloc[0,0]
    max_date = min_max_df.iloc[0,1]
    
    # convert to datetime date format
    min_date_format = dt.datetime.strptime(min_date, date_format).date()
    max_date_format = dt.datetime.strptime(max_date, date_format).date()
  
    # Check start and end dates to ensure the range exists in the dataset
    if (start_date >= min_date_format) and (start_date <= max_date_format) and (end_date >= min_date_format) and (end_date <= max_date_format):
        pass
    elif (start_date < min_date_format) or (start_date > max_date_format):
        return jsonify({"error":f"Start date {start} out of range for the dataset. Dataset range is: {min_date_format} to {max_date_format}"}), 404
    elif (end_date < min_date_format) or (end_date > max_date_format):
        return jsonify({"error":f"End date {end} out of range for the dataset. Dataset range is: {min_date_format} to {max_date_format}"}), 404

    '''Return a JSON list of the minimum temperature, the average temperature, 
    and the max temperature for a given start date. When given the start only, 
    calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.'''
    
    # Query for all dates >= start date. Calc tobs: min, max, avg
    start_only_dates = session.query(func.min(Measurement.date), func.max(Measurement.date), func.min(Measurement.tobs), func.max(Measurement.tobs), func.round(func.avg(Measurement.tobs),2)).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()

    # Close session
    session.close()
    
  
    start_only_list = []
    # Loop through dataset and obtain tobs for all dates
    for start_date, end_date, min_tobs, max_tobs, avg_tobs in start_only_dates:
        start_only_dict = {
            "_start date": start_date,
            "_end date": end_date,
            "min_temp": min_tobs,
            "max_temp": max_tobs,
            "avg_temp": avg_tobs,
        }
        start_only_list.append(start_only_dict)
    return jsonify(start_only_list)


if __name__ == "__main__":
    app.run(debug=True)