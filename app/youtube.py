from io import BytesIO
from flask import Blueprint, redirect, render_template, request, flash, send_file, url_for, session
from youtubesearchpython import *
from pytube import YouTube
import mutagen

youtube = Blueprint("youtube", __name__)

@youtube.route("/")
def home():
    session.clear()
    return '<h1>Hello Youtube</h1>'

@youtube.route("/search", methods=["GET", "POST"])
def search():
    # Check if post request
    session.clear()
    if request.method == "POST":
        print(request.form)
        # If either the search video or search playlist buttons were pressed
        if request.form["search"] == "video":
            title = request.form.get("title")
            if title == "":
                flash("Empty URL", category="warning")
                return render_template("search.html")
            
            if 'playlist?' in  title:
                playlist = Playlist(title)

                while playlist.hasMoreVideos:
                    playlist.getNextVideos()

                results = playlist.videos
            else:
                results = Video.get(title, mode = ResultMode.json)
                results["videoType"]="video"
            
            return render_template("search.html", results=results, title=title)
        elif 'mp4' in request.form["search"]:
            res = request.form["search"].strip('][').split(', ')
            link = res[0]
            try:
                yt = YouTube(link)
            except Exception:
                flash("Video URL is not valid.", category="error")
                return render_template("search.html")

            try:
                buffer = BytesIO()
                video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                video.stream_to_buffer(buffer)
                buffer.seek(0)
                return send_file(buffer, as_attachment=True, download_name='video.mp4', mimetype='video/mp4')
            except Exception:
                flash("Video could not be downloaded.", category="error")
                return render_template("search.html")
        elif 'mp3' in request.form["search"]:
            res = request.form["search"].strip('][').split(', ')
            link = res[0]
            try:
                yt = YouTube(link)
            except Exception:
                flash("Video URL is not valid.", category="error")
                return render_template("search.html")

            try:
                buffer = BytesIO()
                video = yt.streams.filter(only_audio=True).get_audio_only()
                video.stream_to_buffer(buffer)
                buffer.seek(0)
                return send_file(buffer, as_attachment=True, download_name='audio.mp3', mimetype='audio/mpeg')
            except Exception:
                flash("Audio could not be downloaded.", category="error")
                return render_template("search.html")
        else: # If the button pressed was a convert button
            redirect_page = convert_video_redirect("search")
            return redirect(url_for(redirect_page))

    # Clear the session data
    session.clear()
    return render_template("search.html")

def convert_video_redirect(form_name: str) -> str:
    # Save video url in session data and redirect to corresponding page
    conversion_info = request.form.get(form_name)
    url, r_type = conversion_info.split()[0], conversion_info.split()[1]
    if r_type == "video":
        session["video_url"] = url
        redirect_page = "views.video"
    else:
        session["playlist_url"] = url
        redirect_page = "views.playlist"
    return redirect_page

def download_video(yt: YouTube, file_type: str, downloads_path: str, debug: bool=False):
    # Download a video and debug progress
    if file_type == "mp4":
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    else:
        video = yt.streams.filter(only_audio=True).get_audio_only()

    if debug:
        debug_video_progress(yt, video, file_type)

    #video.download(downloads_path)
    return video

def debug_video_progress(yt: YouTube, video, file_type: str, extra_info: str=""):
    highest_res = f", Highest Resolution: {video.resolution}" if file_type == "mp4" else ""
    print(f"Fetching {extra_info}\"{video.title}\"")
    print(f"[File size: {round(video.filesize * 0.000001, 2)} MB{highest_res}, Author: {yt.author}]\n")

def update_metadata(file_path: str, title: str, artist: str, album: str="") -> None:
    # Update the file metadata according to YouTube video details
    with open(file_path, 'r+b') as file:
        media_file = mutagen.File(file, easy=True)
        media_file["title"] = title
        if album: media_file["album"] = album
        media_file["artist"] = artist
        media_file.save(file)