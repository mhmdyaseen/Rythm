from utils import app, db, migrate
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    username = db.Column(db.String(50), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(120), nullable = False)
    role = db.Column(db.Integer, nullable = False)
    status = db.Column(db.Integer, nullable = False)
    
    # Define one to many relationship between users and playlists.
    playlists = db.relationship('Playlist', backref = 'User', lazy = 'dynamic', primaryjoin="User.username == foreign(Playlist.user_username)")


class Album(db.Model):
    __tablename__ = 'Album'
    id = db.Column(db.Integer, primary_key = True)
    album_cover_path = db.Column(db.String(250), unique = True, nullable = True)
    name = db.Column(db.String(30), unique = True, nullable = False)
    artist_username = db.Column(db.String(50), nullable = False)
    artist_name = db.Column(db.String(50), nullable = False)
    year = db.Column(db.Integer, nullable = False)
    

class Song(db.Model):
    __tablename__ = 'Song'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), unique = True, nullable = False)
    artist_username = db.Column(db.String(50), nullable = False)
    artist_name = db.Column(db.String(50), nullable = False)
    album_id = db.Column(db.Integer, db.ForeignKey('Album.id'), nullable = True)
    genre = db.Column(db.String(50), nullable = False)
    year = db.Column(db.Integer, nullable = False)
    audio_file_path = db.Column(db.String(250), unique = True, nullable = False)
    cover_path = db.Column(db.String(250), nullable = False) 
    duration = db.Column(db.Integer, nullable = False)
    lyrics = db.Column(db.Text, nullable = True)
    lyrics_rating = db.Column(db.Float, nullable = False)
    lyrics_rating_count = db.Column(db.Integer, nullable = False)
    total_lyrics_rating = db.Column(db.Float) 
    views = db.Column(db.Integer, nullable = False)
    song_rating = db.Column(db.Float)
    song_rating_count = db.Column(db.Integer)
    total_song_rating = db.Column(db.Float)

    # Define many to many relationship between songs and playlists.
    playlists = db.relationship('Playlist', secondary = 'Playlist_song', back_populates = 'songs')


class Playlist(db.Model):
    __tablename__ = 'Playlist'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), unique = False, nullable = False)
    user_username = db.Column(db.String(50), nullable = False)
    
    # Define many to many relationship between songs and playlists.
    songs = db.relationship('Song', secondary = 'Playlist_song', back_populates = 'playlists')
    
    __table_args__ = (db.UniqueConstraint('user_username','name'),) 

class Playlist_song(db.Model):
    __tablename__ = 'Playlist_song'
    id = db.Column(db.Integer, primary_key = True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('Playlist.id'))
    song_id = db.Column(db.Integer, db.ForeignKey('Song.id'))

