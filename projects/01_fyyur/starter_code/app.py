#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import ForeignKey, and_
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate()
migrate.init_app(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent =db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship("Show", back_populates="venue")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(500))
  
    shows = db.relationship("Show", back_populates="artist")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, ForeignKey('Venue.id'))
  venue = db.relationship("Venue", back_populates="shows")
  artist_id = db.Column(db.Integer, ForeignKey("Artist.id"))
  artist = db.relationship("Artist", back_populates="shows")
  start_time = db.Column(db.DateTime)


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def datetime_to_s(datetime):
  return datetime.strftime("%m/%d/%Y, %H:%M:%S")

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

def num_upcoming_shows_for_venue(venueid):
  return Show.query.filter(and_(Show.start_time >= datetime.now(), Show.venue_id == venueid)).count()

def num_upcoming_shows_for_artist(artistid):
  return Show.query.filter(and_(Show.start_time >= datetime.now(), Show.artist_id == artistid)).count()

@app.route('/venues')
def venues():
  query_result = Venue.query.all()
  formatted_result = {}
  for venue in query_result:
    city_and_state = (venue.city, venue.state)
    if city_and_state not in formatted_result.keys():
      formatted_result[city_and_state] = []
    formatted_result[city_and_state].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows_for_venue(venue.id)
    })
    
  v2_response = []
  for key, value in formatted_result:
    v2_response.append({
      "city": key[0],
      "state": key[1],
      "venues": value
    })

  return render_template('pages/venues.html', areas=v2_response);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  query_result = Venue.query.filter(Venue.name.ilike(search)).all()
  data = []

  for venue in query_result:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows_for_venue(venue.id)
    })

  v2_response = {
    "count": query_result.count(),
    "data": data
  }
  return render_template('pages/search_venues.html', results=v2_response, search_term=request.form.get('search_term', ''))

def shows_by_timing_and_venue(timing, venue_id):
  query_result = Show.query.filter(and_(Show.venue_id==venue_id, Show.start_time < datetime.now())).all() if timing == "past" else Show.query.filter(and_(Show.venue_id==venue_id, Show.start_time > datetime.now())).all()
  result = []
  for show in query_result:
    artist = Artist.query.get(show.artist_id)
    result.append({
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": datetime_to_s(show.start_time)
    })
  return result

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue)
  past_shows = shows_by_timing_and_venue("past", venue_id)
  upcoming_shows = shows_by_timing_and_venue("upcoming", venue_id)
  v2_response={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  
  return render_template('pages/show_venue.html', venue=v2_response)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venue = Venue(
    name=request.form['name'],
    city=request.form['city'],
    state=request.form['state'],
    address=request.form['address'],
    phone=request.form['phone'],
    image_link=request.form['image_link'],
    genres=request.form['genres'],
    facebook_link=request.form['facebook_link'],
    website=request.form['website_link'],
    seeking_talent=True if request.form['seeking_talent'] == "y" else False,
    seeking_description=request.form['seeking_description']
  )
  db.session.add(venue)
  db.session.commit()

  # on successful db insert, flash success
  flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  venue = Venue.query.get(venue_id)
  venue.delete()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  query_result = Artist.query.all()
  v2_response = []
  for artist in query_result:
    v2_response.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=v2_response)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  query_result = Artist.query.filter(Artist.name.ilike(search)).all()
  data = []

  for artist in query_result:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows_for_artist(artist.id)
    })

  v2_response = {
    "count": query_result.count(),
    "data": data
  }
  return render_template('pages/search_artists.html', results=v2_response, search_term=request.form.get('search_term', ''))

def shows_by_timing_and_artist(timing, artist_id):
  query_result = Show.query.filter(and_(Show.artist_id==artist_id, Show.start_time < datetime.now())).all() if timing == "past" else Show.query.filter(and_(Show.artist_id==artist_id, Show.start_time > datetime.now())).all()
  result = []
  for show in query_result:
    venue = Venue.query.get(show.venue_id)
    result.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": datetime_to_s(show.start_time)
    })
  return result

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  past_shows = shows_by_timing_and_artist("past", artist_id)
  upcoming_shows = shows_by_timing_and_artist("upcoming", artist_id)
  
  v2_response = {
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state":artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=v2_response)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  query_result = Artist.query.get(artist_id)
  artist = {
    "id": artist_id,
    "name": query_result.name,
    "genres": query_result.genres,
    "city": query_result.city,
    "state": query_result.state,
    "phone": query_result.phone,
    "website": query_result.website,
    "facebook_link": query_result.facebook_link,
    "seeking_venue": query_result.seeking_venue,
    "seeking_description": query_result.seeking_description,
    "image_link": query_result.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  Artist.query.get(artist_id).update({
    "name": request.form['name'],
    "genres": request.form['genres'],
    "city": request.form['city'],
    "state": request.form['state'],
    "phone": request.form['phone'],
    "website": request.form['website_link'],
    "facebook_link": request.form['facebook_link'],
    "seeking_venue": True if request.form['seeking_venue'] == "y" else False,
    "seeking_description": request.form['seeking_description'],
    "image_link": request.form['image_link']
  })
  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  query_result = Venue.query.get(venue_id)
  venue = {
    "id": query_result.id,
    "name": query_result.name,
    "genres": query_result.genres,
    "address":query_result.address,
    "city": query_result.city,
    "state":query_result.state,
    "phone":query_result.phone,
    "website":query_result.website,
    "facebook_link":query_result.facebook_link,
    "seeking_talent":query_result.seeking_talent,
    "seeking_description":query_result.seeking_description,
    "image_link":query_result.image_link,

  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  Venue.query.get(venue_id).update({
    "name": request.form['name'],
    "city": request.form['city'],
    "state": request.form['state'],
    "address": request.form['address'],
    "phone": request.form['phone'],
    "image_link": request.form['image_link'],
    "genres": request.form['genres'],
    "facebook_link": request.form['facebook_link'],
    "website": request.form['website_link'],
    "seeking_talent": request.form['seeking_talent'],
    "seeking_description": request.form['seeking_description']
  })
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  artist = Artist(
    name=request.form['name'],
    city=request.form['city'],
    state=request.form['state'],
    phone= request.form['phone'],
    image_link=request.form['image_link'],
    genres=request.form['genres'],
    facebook_link= request.form['facebook_link'],
    website= request.form['website_link'],
    seeking_venue=True if request.form['seeking_venue'] == "y" else False,
    seeking_description=request.form['seeking_description']
  )
  db.session.add(artist)
  db.session.commit()

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  v2_response = []
  query_result = Show.query.all()
  for show in query_result:
    artist_details = Artist.query.get(show.artist_id)
    venue_details = Venue.query.get(show.venue_id)
    v2_response.append({
      "venue_id": show.venue_id,
      "venue_name": venue_details.name,
      "artist_id": show.artist_id,
      "artist_name": artist_details.name,
      "artist_image_link": artist_details.image_link,
      "start_time": datetime_to_s(show.start_time)
    })

  return render_template('pages/shows.html', shows=v2_response)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  show = Show(
    artist_id=request.form['artist_id'],
    venue_id=request.form['venue_id'],
    start_time=request.form['start_time']
  )
  db.session.add(show)
  db.session.commit()

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
  app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
