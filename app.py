from utils import app, db, migrate
from model.main import *
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Response, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user
from sqlalchemy import and_, desc
import matplotlib.pyplot as plt
from io import BytesIO
import threading
import os

login_manager = LoginManager(app)
login_manager.login_view = '/login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

@app.route('/', methods = ['GET','POST'])
def hello():
    return render_template('index.html')

@app.route('/admin', methods = ['GET','POST'])
def admin():
    user = User.query.filter_by(email = 'admin@email.com').first()

    if not user:
        user = User(name = 'Admin', 
                    username = 'admin', 
                    email = 'admin@email.com',
                    password = generate_password_hash('password', method = 'sha256'), 
                    role = 2, 
                    status = 1)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember = True) 

    return render_template('admin-home.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('pass')

        user = User.query.filter_by(email = email).first()
        
        if user:
            if check_password_hash(user.password, password) and user.role != 2:
                login_user(user, remember = True)
                return redirect(url_for('home'))
            else:
                flash('Incorrect Password! Try again.', category = 'error')
        else:
            flash('Account doesn\'nt exist. Please Sign Up.', category = 'error')

    return render_template('login.html')

@app.route('/sign up', methods = ['GET','POST'])
def sign_in():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('pass1')
        password2 = request.form.get('pass2')

        user = User.query.filter_by(email = email).first()

        if user:
            flash('Email already exists.', category = 'error')
        elif len(name) < 2:
            flash('Enter a valid Name.', category = 'error')
        elif len(username) < 5:
            flash('Enter a valid Username.', category = 'error')
        elif len(email) < 5:
            flash('Enter a valid Email.', category = 'error')
        elif password1 != password2:
            flash('Passwords doesn\'t Match!', category = 'error')
        elif len(password1) < 7:
            flash('Password must be atleast 8 characters long.', category = 'error')
        else:
            user = User(name = name, 
                        username = username, 
                        email = email,
                        password = generate_password_hash(password1, method = 'sha256'), 
                        role = 0, 
                        status = 1)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember = True)
            return redirect(url_for('home'))
            
    return render_template('sign_up.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('hello'))

@app.route('/home', methods = ['GET','POST'])
@login_required
def home():
    top_songs = db.session.query(Song.cover_path, Song.name, Song.artist_name).order_by(Song.total_song_rating.desc()).limit(5).all()
    songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).limit(5).all()
    albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).limit(5).all()
    genres = ['Hip-Hop', 'Rap', 'Rock', 'No Genre', 'Pop']
    genre_covers = ['Hip-Hop.jpg', 'Rap.jpg', 'Rock.jpg', 'No-Genre.jpg', 'Pop.jpg']    
    genre_zipped = zip(genres, genre_covers)
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    playlists_name = [playlist[0] for playlist in playlists_info]
    return render_template('home.html', top_songs = top_songs, 
                                        songs_info = songs_info, 
                                        albums_info = albums_info, 
                                        genre_zipped = genre_zipped, 
                                        playlists_info = playlists_info, 
                                        playlists_name = playlists_name)

@app.route('/upload_song', methods = ['POST'])
@login_required
def upload_song():
    if current_user.status == 1:
        if request.method == 'POST':
            song_cover = request.files['song-cover']
            song_mp3 = request.files['song']
            song_name = request.form['song-name']
            artist_name = request.form['artist-name']
            year = request.form['year']
            lyrics = request.files['lyrics']
            duration = request.form['duration']
            genre = request.form['genre-select']

            cover_filename = secure_filename(song_cover.filename)
            song_filename = secure_filename(song_mp3.filename)
            
            cover_path = os.path.join(app.config['UPLOAD_FOLDER_COVER'], cover_filename)
            song_path = os.path.join(app.config['UPLOAD_FOLDER_MP3'], song_filename)

            song_cover.save(cover_path)
            song_mp3.save(song_path)

            lyrics_text = lyrics.read().decode('utf-8')

            new_song = Song(name = song_name, 
                            artist_username = current_user.username, 
                            artist_name = artist_name, 
                            genre = genre,
                            year = year, 
                            audio_file_path = song_path, 
                            cover_path = cover_path, 
                            duration = duration,
                            lyrics = lyrics_text,
                            lyrics_rating = 0,
                            lyrics_rating_count = 0,
                            total_lyrics_rating = 0,
                            views = 0,
                            song_rating = 0,
                            song_rating_count = 0,
                            total_song_rating = 0)
                
            db.session.add(new_song)
            db.session.commit()

            songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).all()
            playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
            return render_template('CC-song.html', songs_info = songs_info, playlists_info = playlists_info)

    return render_template('status-block.html')

@app.route('/upload_album', methods = ['POST'])
@login_required
def upload_album():
    if current_user.status == 1:
        if request.method == 'POST':
            album_cover = request.files['album-cover']
            album_name = request.form['album-name']
            artist_name = request.form['artist-name']
            year = request.form['year']


            album_cover_filename = secure_filename(album_cover.filename)
            album_cover_path = os.path.join(app.config['UPLOAD_FOLDER_ALBUM_COVER'], album_cover_filename)
            album_cover.save(album_cover_path)

            new_album = Album(album_cover_path = album_cover_path,
                            name = album_name, 
                            artist_username = current_user.username,  
                            artist_name = artist_name,
                            year = year)

            db.session.add(new_album)
            db.session.commit()

            albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == current_user.username).all()
            playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
            return render_template('CC-albums.html', albums_info = albums_info, playlists_info = playlists_info)
    
    return render_template('status-block.html')

@app.route('/upload_album_song', methods = ['POST'])
@login_required
def upload_album_song():
    if current_user.status == 1:
        if request.method == 'POST':
            song_cover = request.files['song-cover']
            song_mp3 = request.files['song']
            song_name = request.form['song-name']
            artist_name = request.form['artist-name']
            album_name = request.form['album-name']
            year = request.form['year']
            genre = request.form['genre-select']
            lyrics = request.files['lyrics']
            duration = request.form['duration']


            existing_album = Album.query.filter_by(name = album_name).first()
            album_id = existing_album.id
            
            cover_filename = secure_filename(song_cover.filename)
            song_filename = secure_filename(song_mp3.filename)

            cover_path = os.path.join(app.config['UPLOAD_FOLDER_COVER'], cover_filename)
            song_path = os.path.join(app.config['UPLOAD_FOLDER_MP3'], song_filename)

            song_cover.save(cover_path)
            song_mp3.save(song_path)

            lyrics_text = lyrics.read().decode('utf-8')

            new_song = Song(name = song_name, 
                            artist_username = current_user.username, 
                            artist_name = artist_name, 
                            album_id = album_id,
                            genre = genre,
                            year = year, 
                            audio_file_path = song_path, 
                            cover_path = cover_path, 
                            duration = duration,
                            lyrics = lyrics_text,
                            lyrics_rating = 0,
                            lyrics_rating_count = 0,
                            total_lyrics_rating = 0,
                            views = 0,
                            song_rating = 0,
                            song_rating_count = 0,
                            total_song_rating = 0)
                
            db.session.add(new_song)
            db.session.commit()

            album_details = db.session.query(Album.album_cover_path,
                                        Album.name.label('album_name'),
                                        Song.artist_username.label('album_artist_name')).filter(Album.name == album_name).first()
            songs_info = db.session.query(Song.name, Song.artist_name, Song.duration).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).all()
            playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
            return render_template('album-song-CC.html', album_details = album_details, songs_info = songs_info, playlists_info = playlists_info)

    return render_template('status-block.html')

@app.route('/content_creator')
@login_required
def content_creator():
    if current_user.role == 0:
        return render_template('CC-start.html')
    elif current_user.role == 1:
        songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).limit(5).all()
        ratings = db.session.query(Song.total_song_rating).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).all()
        no_of_songs = len(ratings)
          
        tot_rating = 0

        for rate in ratings:
            tot_rating += rate[0]
        
        if no_of_songs == 0:
            no_of_songs = 1

        user_avg_rating = round(tot_rating / no_of_songs, 2)
        albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == current_user.username).limit(5).all()
        no_of_albums = len(albums_info)
        top_rated_song = db.session.query(Song.name, Song.total_song_rating).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).order_by(desc(Song.total_song_rating)).limit(1).first()
        
        if top_rated_song == None:
            no_of_songs = 0
            top_rated_song = '-'
            rate_of_topsong = 0
            playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
            return render_template('CC-home.html', songs_info = songs_info, 
                                                   no_of_songs = no_of_songs, 
                                                   user_avg_rating = user_avg_rating, 
                                                   albums_info = albums_info, 
                                                   no_of_albums = no_of_albums, 
                                                   top_rated_song = top_rated_song, 
                                                   rate_of_topsong = rate_of_topsong, 
                                                   playlists_info = playlists_info)
        
        rate_of_topsong = round(top_rated_song[1], 2)

        playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
        return render_template('CC-home.html', songs_info = songs_info, 
                                               no_of_songs = no_of_songs, 
                                               user_avg_rating = user_avg_rating, 
                                               albums_info = albums_info, 
                                               no_of_albums = no_of_albums, 
                                               top_rated_song = top_rated_song, 
                                               rate_of_topsong = rate_of_topsong, 
                                               playlists_info = playlists_info)
    
@app.route('/new_cc')
@login_required
def new_cc():
    current_user.role = 1
    db.session.commit()
    return render_template('CC-home.html')

@app.route('/for_you')
@login_required
def for_you():
    top_songs = db.session.query(Song.cover_path, Song.name, Song.artist_name).order_by(Song.total_song_rating.desc()).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    playlists_name = [playlist[0] for playlist in playlists_info]
    return render_template('foryou.html', top_songs = top_songs, playlists_info = playlists_info, playlists_name = playlists_name)

@app.route('/songs')
@login_required
def songs():
    songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('songs.html', songs_info = songs_info, playlists_info = playlists_info) 

@app.route('/cc_song')
@login_required
def cc_song():
    songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('CC-song.html', songs_info = songs_info, playlists_info = playlists_info)

@app.route('/albums')
@login_required
def albums():
    albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('albums.html', albums_info = albums_info, playlists_info = playlists_info) 

@app.route('/cc_album')
@login_required
def cc_album():
    albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == current_user.username).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('CC-albums.html', albums_info = albums_info, playlists_info = playlists_info)

@app.route('/genre/<string:genre>')
@login_required
def genre(genre):
    genres = {'Hip-Hop':'Hip-Hop.jpg', 'Rap':'Rap.jpg', 'Rock':'Rock.jpg', 'No Genre':'No-Genre.jpg', 'Pop':'Pop.jpg'}
    genres_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).filter(Song.genre == genre).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    playlists_name = [playlist[0] for playlist in playlists_info]
    return render_template('genre-song.html', genre = genre, genres = genres, genres_info = genres_info, playlists_info = playlists_info, playlists_name = playlists_name)

@app.route('/new_song')
@login_required
def new_song():
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('new-song.html', playlists_info = playlists_info)

@app.route('/new_album')
@login_required
def new_album():
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('new-album.html', playlists_info = playlists_info)

@app.route('/new_album_song/<string:album_name>')
@login_required
def new_album_song(album_name):
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('new-album-song.html', album_name = album_name, playlists_info = playlists_info)

@app.route('/<filename>')
def song_cover(filename):
    return send_from_directory('static/uploads/song-cover', filename)

@app.route('/<filename>')
def album_cover(filename):
    return send_from_directory('static/uploads/album-cover', filename)

@app.route('/<filename>')
def playlist_cover(filename):
    return send_from_directory('static/uploads/playlist-cover', filename)

@app.route('/<filename>')
def genre_cover(filename):
    return send_from_directory('static/uploads/genre-cover', filename)

@app.route('/<filename>')
def profile_picture(filename):
    return send_from_directory('static/uploads/profile-picture', filename)

@app.route('/<filename>')
def barchart(filename):
    return send_from_directory('static/uploads/charts', filename)

@app.route('/home_album_song/<string:name>')
@login_required
def home_album_song(name):
    album_details = db.session.query(Album.album_cover_path,
                                     Album.name,
                                     Album.artist_username).filter(Album.name == name).first()

    songs_info = db.session.query(Song.name.label('song_name'),
                                    Song.artist_name.label('artist_name'),
                                    Song.duration).join(Album, Album.id == Song.album_id).filter(Album.name == name).all()
    
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all() 
    playlists_name = [playlist[0] for playlist in playlists_info]

    return render_template('album-song.html', album_details = album_details, songs_info = songs_info, playlists_info = playlists_info, playlists_name = playlists_name)

@app.route('/album/<string:name>')
@login_required
def album_song_cc(name):
    album_details = db.session.query(Album.album_cover_path,
                                     Album.name,
                                     Album.artist_username).filter(Album.name == name).first()

    songs_info = db.session.query(Song.name.label('song_name'),
                                    Song.artist_name.label('artist_name'),
                                    Song.duration).join(Album, Album.id == Song.album_id).filter(Album.name == name).all()
    
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all() 
    
    return render_template('album-song-CC.html', album_details = album_details, songs_info = songs_info, playlists_info = playlists_info)

@app.route('/delete/<string:song_name>')
@login_required
def delete(song_name):
    song = Song.query.filter_by(name = song_name).first()
    album_id = song.album_id
    album = Album.query.filter_by(id = album_id).first()
    album_name = album.name
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('album_song_cc', name = album_name))

@app.route('/delete_song/<string:song_name>')
@login_required
def delete_song(song_name):
    song = Song.query.filter_by(name = song_name).first()
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('content_creator'))

@app.route('/delete_album/<string:album_name>')
@login_required
def delete_album(album_name):
    album = Album.query.filter_by(name = album_name).first()
    album_id = album.id
    songs = Song.query.filter_by(album_id = album_id).all()
    
    for song in songs:
        db.session.delete(song)

    db.session.delete(album)
    db.session.commit()
    return redirect(url_for('content_creator'))

@app.route('/lyrics/<string:song_name>')
@login_required
def lyrics(song_name):
    song = Song.query.filter_by(name = song_name).first()
    song_name = song.name
    lyrics = song.lyrics
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all() 
    return render_template('lyrics.html', song_name = song_name, lyrics = lyrics, playlists_info = playlists_info)

@app.route('/new_playlist', methods = ['POST'])
@login_required
def new_playlist():
    if request.method == 'POST':
        playlist_name = request.form['playlist-name']
        playlist = Playlist(name = playlist_name, user_username = current_user.username)
        db.session.add(playlist)
        db.session.commit()
        return redirect(url_for('home'))

@app.route('/playlist/<string:playlist_name>')
@login_required
def playlist(playlist_name):
    playlist = Playlist.query.filter_by(name = playlist_name, user_username = current_user.username).first()
    songs = playlist.songs
    playlist_info = db.session.query(Playlist.name).filter(and_(Playlist.name == playlist_name, Playlist.user_username == current_user.username)).first()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all() 
    return render_template('playlist.html', playlist_info = playlist_info, username = current_user.username, playlists_info = playlists_info, songs = songs)

@app.route('/edit_album/<string:album_name>', methods = ['GET', 'POST'])
@login_required
def edit_album(album_name):
    if current_user.status != 1:
        return render_template('status-block.html')
    elif request.method == 'POST':
        print(album_name)
        album_cover = request.files['album-cover']
        album_name_updated = request.form['album-name']
        artist_name = request.form['artist-name']
        year = request.form['year']

        album_cover_filename = secure_filename(album_cover.filename)
        album_cover_path = os.path.join(app.config['UPLOAD_FOLDER_ALBUM_COVER'], album_cover_filename)
        album_cover.save(album_cover_path)

        album_details = Album.query.filter_by(name = album_name).first()

        album_details.album_cover_path = album_cover_path 
        album_details.name = album_name_updated
        album_details.artist_username = current_user.username
        album_details.artist_name = artist_name
        album_details.year = year

        db.session.commit()

        songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).limit(5).all()
        albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == current_user.username).limit(5).all()
        playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
        return render_template('CC-home.html', songs_info = songs_info, albums_info = albums_info, playlists_info = playlists_info)

    album_details = Album.query.filter_by(name = album_name).first()
    return render_template('edit-album.html', album_details = album_details) 

@app.route('/edit_song/<string:song_name>', methods = ['GET', 'POST'])
@login_required
def edit_song(song_name):
    if current_user.status != 1:
        return render_template('status-block.html')
    elif request.method == 'POST':
        song_cover = request.files['song-cover']
        song_mp3 = request.files['song']
        updated_song_name = request.form['song-name']
        artist_name = request.form['artist-name']
        year = request.form['year']
        lyrics = request.files['lyrics']
        duration = request.form['duration']
        genre = request.form['genre-select']

        cover_filename = secure_filename(song_cover.filename)
        song_filename = secure_filename(song_mp3.filename)
        
        cover_path = os.path.join(app.config['UPLOAD_FOLDER_COVER'], cover_filename)
        song_path = os.path.join(app.config['UPLOAD_FOLDER_MP3'], song_filename)

        song_cover.save(cover_path)
        song_mp3.save(song_path)

        lyrics_text = lyrics.read().decode('utf-8')

        song_details = Song.query.filter_by(name = song_name).first()

        song_details.cover_path = cover_path 
        song_details.audio_file_path = song_path
        song_details.name = updated_song_name
        song_details.artist_username = current_user.username
        song_details.artist_name = artist_name
        song_details.year = year
        song_details.lyrics = lyrics_text
        song_details.duration = duration
        song_details.genre = genre

        db.session.commit()

        songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == current_user.username).limit(5).all()
        albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == current_user.username).limit(5).all()
        playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
        return render_template('CC-home.html', songs_info = songs_info, albums_info = albums_info, playlists_info = playlists_info)

    song_details = Song.query.filter_by(name = song_name).first()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('edit-song.html', song_details = song_details, playlists_info = playlists_info) 

@app.route('/add_to_playlist/<string:playlist_name>/<string:song_name>')
@login_required
def add_to_playlist(playlist_name, song_name):
   playlist = Playlist.query.filter_by(name = playlist_name, user_username = current_user.username).first()
   song = Song.query.filter_by(name = song_name).first()

   if song not in playlist.songs:
       playlist.songs.append(song)
       db.session.commit()
       return redirect(url_for('home'))
   
   return render_template('login.html')

@app.route('/delete_playlist/<string:playlist_name>')
@login_required
def delete_playlist(playlist_name):
   playlist = Playlist.query.filter_by(name = playlist_name, user_username = current_user.username).first() 
   db.session.delete(playlist)
   db.session.commit()
   return redirect(url_for('home'))

@app.route('/delete_playlist_song/<string:playlist_name>/<string:song_name>')
@login_required
def delete_playlist_song(playlist_name, song_name):
   playlist = Playlist.query.filter_by(name = playlist_name, user_username = current_user.username).first()
   song = Song.query.filter_by(name = song_name).first()

   playlist.songs.remove(song)
   db.session.commit()
   return redirect(url_for('playlist', playlist_name = playlist.name))

@app.route('/rating_lyrics_1/<string:song_name>')
@login_required
def rating_lyrics_1(song_name):
   song = Song.query.filter_by(name = song_name).first() 
   song.lyrics_rating += 1
   song.lyrics_rating_count += 1
   song.total_lyrics_rating = song.lyrics_rating / song.lyrics_rating_count
   db.session.commit()
   return redirect(url_for('home'))

@app.route('/rating_lyrics_0/<string:song_name>')
@login_required
def rating_lyrics_0(song_name):
   song = Song.query.filter_by(name = song_name).first() 
   song.lyrics_rating -= 1
   song.lyrics_rating_count += 1
   song.total_lyrics_rating = song.lyrics_rating / song.lyrics_rating_count
   db.session.commit()
   return redirect(url_for('home'))

@app.route('/rate_song/<string:song_name>', methods = ['POST'])
@login_required
def rate_song(song_name):
    if request.method == 'POST':
        song = Song.query.filter_by(name = song_name).first()  
        song.song_rating += int(request.form['rating'])
        song.song_rating_count += 1
        song.total_song_rating = song.song_rating / song.song_rating_count
        db.session.commit()
        return redirect(url_for('home'))

@app.route('/play_song/<path:song_name>')
def play_song(song_name):
    song = Song.query.filter_by(name = song_name).first()  
    song.views += 1
    db.session.commit() 
    if song:
        return send_file(song.audio_file_path, as_attachment = True)
    else:
        return "Song not found", 404

@app.route('/user_profile')
@login_required
def user_profile():
    name, username = current_user.name, current_user.username
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    playlists_name = [playlist[0] for playlist in playlists_info]
    return render_template('user-profile.html', name = name, username = username, playlists_info = playlists_info, playlists_name = playlists_name)

@app.route('/search')
@login_required
def search():
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('search.html', playlists_info = playlists_info)

@app.route('/go_search', methods = ['POST'])
@login_required
def go_search():
    if request.method == 'POST':
        select_search = request.form['select-search']
        search_query = request.form['search-query']

        playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
        playlists_name = [playlist[0] for playlist in playlists_info]

        if select_search == 'song':
            song_name = search_query
            song = db.session.query(Song.cover_path, Song.name, Song.artist_name).filter_by(name = song_name).first()

            if song:
                return render_template('search.html', song = song, searching = 'song', playlists_info = playlists_info, playlists_name = playlists_name)
            return redirect(url_for('page_not_found'))
        
        elif select_search == 'album':
            album_name = search_query
            album = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).filter_by(name = album_name).first()

            if album:
                return render_template('search.html', album = album, searching = 'album', playlists_info = playlists_info, playlists_name = playlists_name)
            return redirect(url_for('page_not_found'))
        
        elif select_search == 'artist':
            artist_username = search_query
            songs = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == artist_username).all()
            albums = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == artist_username).all()

            if songs or albums:
               return render_template('search.html', songs = songs, 
                                                     albums = albums, 
                                                     artist_username = artist_username, 
                                                     searching = 'artist', 
                                                     playlists_info = playlists_info, 
                                                     playlists_name = playlists_name) 
            return redirect(url_for('page_not_found'))
     
        elif select_search == 'genre':
            genre = search_query
            genres = {'Hip-Hop':'Hip-Hop.jpg', 'Rap':'Rap.jpg', 'Rock':'Rock.jpg', 'No Genre':'No-Genre.jpg', 'Pop':'Pop.jpg'}
            genre_cover = genres[genre] 

            return render_template('search.html', genre = genre, genre_cover = genre_cover, searching = 'genre', playlists_info = playlists_info)

@app.route('/page_not_found')
@login_required
def page_not_found():
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('page-not-found.html', playlists_info = playlists_info)

@app.route('/artist_song/<string:artist_username>')
@login_required
def artist_song(artist_username):
    songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == artist_username).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('songs.html', songs_info = songs_info, playlists_info = playlists_info)

@app.route('/artist_album/<string:artist_username>')
@login_required
def artist_album(artist_username):
    albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == artist_username).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('albums.html', albums_info = albums_info, playlists_info = playlists_info)

#generate bar graph for top rated songs.
def generate_top_rated_song_graph():
    top_rated_song = db.session.query(Song.name, Song.total_song_rating).order_by(desc(Song.total_song_rating)).limit(5).all() 
    song_name, song_rating = [], []

    for song in top_rated_song:
       song_name.append(song[0])
       song_rating.append(song[1])

    plt.switch_backend('Agg')
    plt.figure()
    plt.bar(song_name, song_rating, color = 'skyblue')
    plt.title('Top 5 Rated Songs')

    image_stream = BytesIO()
    plt.savefig(image_stream, format = 'png')
    image_stream.seek(0)

    image_path = 'static/uploads/charts/top_rated_songs.png'
    with open(image_path, 'wb') as f:
        f.write(image_stream.read())

    return image_path

def generate_top_viewed_song_graph():
    top_viewed_song = db.session.query(Song.name, Song.views).order_by(desc(Song.views)).limit(5).all() 
    song_name, song_views = [], []

    for song in top_viewed_song:
       song_name.append(song[0])
       song_views.append(int(song[1]/2))

    plt.switch_backend('Agg')
    plt.figure()
    plt.bar(song_name, song_views, color = 'skyblue')
    plt.title('Top 5 Viewed Songs')

    image_stream = BytesIO()
    plt.savefig(image_stream, format = 'png')
    image_stream.seek(0)

    image_path = 'static/uploads/charts/top_viewed_songs.png'
    with open(image_path, 'wb') as f:
        f.write(image_stream.read())

    return image_path

@app.route('/admin_home', methods = ['POST'])
@login_required
def admin_home():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email = email).first()

        if email == 'admin@email.com':
            if check_password_hash(user.password, password):
                login_user(user, remember = True)
                top_rated_song_image_path = 'static/uploads/charts/top_rated_songs.png'
                top_viewed_song_image_path = 'static/uploads/charts/top_viewed_songs.png' 
                
                if os.path.exists(top_viewed_song_image_path):
                    os.remove(top_viewed_song_image_path)

                top_rated_song_image_path = generate_top_rated_song_graph()
                top_viewed_song_image_path = generate_top_viewed_song_graph()
                total_normal_users = len(db.session.query(User).filter(User.role == 0 or User.role == 1).all())
                total_content_creators = len(db.session.query(User).filter(User.role == 1).all()) 
                total_songs = len(db.session.query(Song).all())
                total_albums = len(db.session.query(Album).all()) 
                total_genres = 5
                top_rated_song = db.session.query(Song.name, Song.total_song_rating).order_by(desc(Song.total_song_rating)).limit(1).first()
                top_rated_song_name, rate_top_song = top_rated_song[0], round(top_rated_song[1], 2)
                artists_info = db.session.query(User.username).filter(User.role == 1).limit(3).all()
                songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).limit(3).all()
                albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).limit(3).all()
                return render_template('admin-home.html', top_rated_song_image_path = top_rated_song_image_path, 
                                                          top_viewed_song_image_path = top_viewed_song_image_path, 
                                                          total_normal_users = total_normal_users, 
                                                          total_content_creators = total_content_creators, 
                                                          total_songs = total_songs, 
                                                          total_albums = total_albums, 
                                                          total_genres = total_genres,
                                                          top_rated_song_name = top_rated_song_name, 
                                                          rate_top_song = rate_top_song, 
                                                          artists_info = artists_info, 
                                                          songs_info = songs_info, 
                                                          albums_info = albums_info)
            
    return render_template('admin_login.html')

@app.route('/artist-admin')
@login_required
def artist_admin(): 
    artists_info = db.session.query(User.username).filter(User.role == 1).all()
    return render_template('artist-admin.html', artists_info = artists_info)

@app.route('/songs_admin')
@login_required
def songs_admin():
   songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).all() 
   return render_template('songs-admin.html', songs_info = songs_info)

@app.route('/albums_admin')
@login_required
def albums_admin():
   albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).all() 
   return render_template('albums-admin.html', albums_info = albums_info)

@app.route('/lyrics_admin/<string:song_name>')
@login_required
def lyrics_admin(song_name):
    song = Song.query.filter_by(name = song_name).first()
    song_name = song.name
    lyrics = song.lyrics
    return render_template('lyrics-admin.html', song = song, lyrics = lyrics)

@app.route('/artist_details/<string:artist_username>')
@login_required
def artist_details (artist_username):
    name = db.session.query(User.name).filter(User.username == artist_username).first()
    songs = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == artist_username).limit(6).all()
    albums = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == artist_username).limit(6).all() 
    return render_template('artist-details.html', name = name, username = artist_username, songs = songs, albums = albums)

@app.route('/artist_songs_admin/<string:artist_username>')
@login_required
def artist_songs_admin(artist_username):
    songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == artist_username).all() 
    return render_template('songs-admin.html', songs_info = songs_info)

@app.route('/artist_albums_admin/<string:artist_username>')
@login_required
def artist_albums_admin(artist_username):
    name = db.session.query(User.username).filter(User.username == artist_username).first()
    albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == artist_username).all() 
    return render_template('albums-admin.html', name = name, albums_info = albums_info)

@app.route('/album_song_admin/<string:album_name>')
@login_required
def aalbum_song_admin(album_name):
    album_details = db.session.query(Album.album_cover_path,
                                     Album.name,
                                     Album.artist_username).filter(Album.name == album_name).first()

    songs_info = db.session.query(Song.name.label('song_name'),
                                    Song.artist_name.label('artist_name'),
                                    Song.duration).join(Album, Album.id == Song.album_id).filter(Album.name == album_name).all()
    return render_template('album-song-admin.html', album_details = album_details, songs_info = songs_info)

@app.route('/delete_song_admin/<string:song_name>')
def delete_song_admin(song_name):
    song = Song.query.filter_by(name = song_name).first()
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('admin_home'))

@app.route('/delete_album_admin/<string:album_name>')
@login_required
def delete_album_admin(album_name):
    album = Album.query.filter_by(name = album_name).first()
    album_id = album.id
    songs = Song.query.filter_by(album_id = album_id).all()
    
    for song in songs:
        db.session.delete(song)

    db.session.delete(album)
    db.session.commit()
    return redirect(url_for('admin_home'))

@app.route('/blacklist/<string:username>')
@login_required
def blacklist(username):
    user = db.session.query(User).filter(User.username == username).first()
    user.status = 0
    db.session.commit()
    return redirect(url_for('admin_home'))

@app.route('/whitelist/<string:username>')
@login_required
def whitelist(username):
    user = db.session.query(User).filter(User.username == username).first()
    user.status = 1
    db.session.commit()
    return redirect(url_for('admin_home'))

@app.route('/admin_search')
@login_required
def admin_search():
    return render_template('admin-search.html')

@app.route('/page_not_found_admin')
@login_required
def page_not_found_admin():
    return render_template('page-not-found-admin.html')

@app.route('/go_search_admin', methods = ['POST'])
@login_required
def go_search_admin():
    if request.method == 'POST':
        select_search = request.form['select-search']
        search_query = request.form['search-query']

        playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
        playlists_name = [playlist[0] for playlist in playlists_info]

        if select_search == 'song':
            song_name = search_query
            song = db.session.query(Song.cover_path, Song.name, Song.artist_name).filter_by(name = song_name).first()

            if song:
                return render_template('admin-search.html', song = song, 
                                                            searching = 'song', 
                                                            playlists_info = playlists_info, 
                                                            playlists_name = playlists_name)
            return redirect(url_for('page_not_found_admin'))
        
        elif select_search == 'album':
            album_name = search_query
            album = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).filter_by(name = album_name).first()

            if album:
                return render_template('admin-search.html', album = album, 
                                                            searching = 'album', 
                                                            playlists_info = playlists_info, 
                                                            playlists_name = playlists_name)
            return redirect(url_for('page_not_found_admin'))
        
        elif select_search == 'artist':
            artist_username = search_query
            songs = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == artist_username).all()
            albums = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == artist_username).all()

            if songs or albums:
               return render_template('admin-search.html', songs = songs, 
                                                           albums = albums, 
                                                           artist_username = artist_username, 
                                                           searching = 'artist', 
                                                           playlists_info = playlists_info, 
                                                           playlists_name = playlists_name) 
            return redirect(url_for('page_not_found_admin'))
     
        elif select_search == 'genre':
            genre = search_query
            genres = {'Hip-Hop':'Hip-Hop.jpg', 'Rap':'Rap.jpg', 'Rock':'Rock.jpg', 'No Genre':'No-Genre.jpg', 'Pop':'Pop.jpg'}

            if genre not in genres.keys():
                return render_template('page-not-found-admin.html')
            
            genre_cover = genres[genre] 
            return render_template('admin-search.html', genre = genre, 
                                                        genre_cover = genre_cover, 
                                                        searching = 'genre', 
                                                        playlists_info = playlists_info)

@app.route('/admin_artist_song/<string:artist_username>')
@login_required
def admin_artist_song(artist_username):
    songs_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).join(User, Song.artist_username == User.username).filter(Song.artist_username == artist_username).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('songs-search-admin.html', songs_info = songs_info, playlists_info = playlists_info)

@app.route('/admin_artist_album/<string:artist_username>')
@login_required
def admin_artist_album(artist_username):
    albums_info = db.session.query(Album.album_cover_path, Album.name, Album.artist_name).join(User, Album.artist_username == User.username).filter(Album.artist_username == artist_username).all()
    playlists_info = db.session.query(Playlist.name).filter(Playlist.user_username == current_user.username).all()
    return render_template('album-search-admin.html', albums_info = albums_info, playlists_info = playlists_info)

@app.route('/genre_admin/<string:genre>')
@login_required
def genre_admin(genre):
    genres = {'Hip-Hop':'Hip-Hop.jpg', 'Rap':'Rap.jpg', 'Rock':'Rock.jpg', 'No Genre':'No-Genre.jpg', 'Pop':'Pop.jpg'}
    genres_info = db.session.query(Song.cover_path, Song.name, Song.artist_name).filter(Song.genre == genre).all()
    return render_template('genre-admin.html', genre = genre, genres = genres, genres_info = genres_info)


if __name__ == '__main__':
    app.run(debug=True)