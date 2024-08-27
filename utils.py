from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///project.db"
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['SECRET_KEY'] = 'fjkfjdkfjkjdjfjijioewjririmvcnnv,mxnxcvn'
app.config['UPLOAD_FOLDER_ALBUM_COVER'] = 'static/uploads/album-cover'
app.config['UPLOAD_FOLDER_COVER'] = 'static/uploads/song-cover'
app.config['UPLOAD_FOLDER_MP3'] = 'static/uploads/mp3'


db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch = True)