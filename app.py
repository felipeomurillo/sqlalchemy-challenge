#################################################
# Setup Depencies
#################################################
import sqlalchemy
import numpy as np
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
# Start the engine for the database
engine = create_engine("sqlite:///data/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

#################################################
# Flask Routes
#################################################

# Home Directory used to provide user with available APIs
@app.route("/")
def welcome():
    return (
        f"<b>Available Routes:</b><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<b>The following routes are also available, with specified start and end dates formatted as YYYY-MM-DD:</b><br/>"
        f"/api/v1.0/(start)<br/>"
        f"/api/v1.0/(start)/(end)<br/>"
    )

#################################################
# Precipitation API
#################################################
@app.route("/api/v1.0/precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query precipitation data: date, station, and data
    results = (
        session
        .query(Measurement.date, Measurement.station, Measurement.prcp)
        .group_by(Measurement.date, Measurement.station)
        .all()
    )
    # Close the session
    session.close()

    # Initialize list and default date
    prcp_list = []
    d_o = ''

    # This segment will make a dictionary of 
    # precipitation data fro different station
    # for a given date
    for date, station, prcp in results: 
            prcp_dict = {}
            if date != d_o:
                prcp_dict["date"] = date
            p_dict = {}
            p_dict[station] = prcp
            prcp_dict["prcp"]= p_dict
            prcp_list.append(prcp_dict)
            d_o = date

    # Return JSON formatted-data
    return jsonify(prcp_list)

#################################################
# Weatherstation API
#################################################
@app.route("/api/v1.0/stations")
def stations():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query precipitation data: date, station, and data
    results = (
        session
        .query(Station.station, Station.name, Station.longitude, Station.latitude, Station.elevation)
        .all()
    )
    # Close the session
    session.close()

    st_list = []
    for station, name,longitude, latitude, elevation in results: 
            st_dict = {}
            st_dict["station"] = station
            st_dict["name"]= name
            st_dict["geo"]= {"lng":longitude,"lat":latitude,"elev":elevation}
            st_list.append(st_dict)

    # Return JSON formatted-data
    return jsonify(st_list)

#################################################
# Observed Temperatures from Active Station API
#################################################
@app.route("/api/v1.0/tobs")
def tobs():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Determine the most active station
    activeStation = ( 
               session
              .query(Measurement.station, Station.name, func.count(Measurement.station))
              .group_by(Measurement.station)
              .join(Station, Measurement.station == Station.station)
              .order_by(func.count(Measurement.station).desc())
              .first()
              )

    # Determine the lastest weather data
    stationLast = (
                session
                .query(Measurement.date)
                .filter_by(station = activeStation[0])
                .order_by(Measurement.date.desc())
                .first()
                ._asdict()
                )

    # Determine the start date for a year's worth query
    stationLast_f = dt.datetime.strptime(stationLast['date'],'%Y-%m-%d')
    stationStart = dt.date(stationLast_f.year -1,stationLast_f.month, stationLast_f.day)

    # Query the dates and temperature observations of the 
    # most active station for the last year of data
    activeStationData = (
                    session
                    .query(Measurement.date, Measurement.tobs)
                    .filter_by(station = activeStation[0])
                    .filter(Measurement.date >= stationStart)
                    .filter(Measurement.date <= stationLast['date'])
                    .order_by(Measurement.date.asc())
                    .all()
                    )
    
    # Close the session
    session.close()

    # Pull date and observed temperatures
    tobs_list = []
    for date, tobs in activeStationData: 
            tobs_dict = {}
            tobs_dict["date"] = date
            tobs_dict["tobs"]= tobs
            tobs_list.append(tobs_dict)
   
    # Return JSON formatted-data
    return jsonify(tobs_list)



#################################################
# Start Date API
#################################################
@app.route("/api/v1.0/<start>")
def tobs_start(start):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # This API will only provide temperatures from the most active station
    activeStation = ( 
               session
              .query(Measurement.station, Station.name, func.count(Measurement.station))
              .group_by(Measurement.station)
              .join(Station, Measurement.station == Station.station)
              .order_by(func.count(Measurement.station).desc())
              .first()
              )

    # Query temperature data for dates 
    # after (and including) the specified date
    activeStationData = (
                    session
                    .query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))
                    .filter_by(station = activeStation[0])
                    .filter(Measurement.date >= start)
                    .all()
                    )

    # Close the session
    session.close()

    # Pull date and observed temperatures
    tobs_list = []
    tobs_dict = {}
    tobs_dict["TMIN"] = activeStationData[0][0]
    tobs_dict["TMAX"]= activeStationData[0][1]
    tobs_dict["TAVG"] = round(activeStationData[0][2],2)
    tobs_list.append(tobs_dict)
   
    # Return JSON formatted-data
    return jsonify(tobs_list)

#################################################
# Start/End Date API
#################################################
@app.route("/api/v1.0/<start>/<end>")
def tobs_start_end(start,end):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # This API will only provide temperatures from the most active station
    activeStation = ( 
               session
              .query(Measurement.station, Station.name, func.count(Measurement.station))
              .group_by(Measurement.station)
              .join(Station, Measurement.station == Station.station)
              .order_by(func.count(Measurement.station).desc())
              .first()
              )

    # Query temperature data for dates 
    # after (and including) the specified date
    activeStationData = (
                    session
                    .query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))
                    .filter_by(station = activeStation[0])
                    .filter(Measurement.date >= start)
                    .filter(Measurement.date <= end)
                    .all()
                    )

    # Close the session
    session.close()

    # Pull date and observed temperatures
    tobs_list = []
    tobs_dict = {}
    tobs_dict["TMIN"] = activeStationData[0][0]
    tobs_dict["TMAX"]= activeStationData[0][1]
    tobs_dict["TAVG"] = round(activeStationData[0][2],2)
    tobs_list.append(tobs_dict)
   
    # Return JSON formatted-data
    return jsonify(tobs_list)

#################################################
# Execute API and run in debug mode
#################################################
if __name__ == '__main__':
    app.run(debug=True)
