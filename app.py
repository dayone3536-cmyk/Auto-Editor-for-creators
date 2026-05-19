from flask import Flask, render_template, send_file, request, jsonify
import os

import threading

import subprocess

import uuid
from google import genai

from dotenv import load_dotenv

load_dotenv("api_key.env")


API_KEY = os.getenv("key")

app = Flask(__name__)



@app.route("/")
def welcoming_page():
    return render_template("index.html")

@app.route("/display", methods =["POST"])
def displaying():
    try:
        niche = request.form["niche"]

        client = genai.Client(api_key = API_KEY)

        response = client.models.generate_content(model = "gemini-2.5-flash",   
                                                contents= f"Generate 10 viral video ideas for {niche}. Output format: Topic | Hook \n Topic | hook \n Topic | hook \n  Rules: \n  10 words max per line total,  Topic is the video concept, Hook is the first attention-grabbing sentence, Separate Topic and Hook with ' | '  One idea per line No numbering, no explanations"
                                                )
        
        return render_template("display.html", output = response.text)
    
    except Exception:
        return render_template("error.html")
    
    
@app.route("/edit-form", methods = ["POST"])
def sumbitting_the_video():
    return render_template("video-edit.html")


video_status_db = {}
def background_video_editor(input_path, output_path, unique_id):

    try:
        # Update status to processing
        video_status_db[unique_id] = "Processing: Running auto-editor..."
        
        command = f"auto-editor {input_path} --output {output_path} --margin 0.4s --video_codec h264 --audio_codec aac --no_open"
        
        # Run the auto-editor (this takes time, but it's okay because it's in the background!)
        subprocess.run(command, shell=True, check=True)
        
        # Once finished, update the status
        video_status_db[unique_id] = "Completed"

        print(f"Successfully processed video for ID: {unique_id}")
        
    except Exception as e:
        video_status_db[unique_id] = f"Failed: {str(e)}"
        print(f"Error processing video {unique_id}: {e}")


@app.route("/upload", methods=["POST"])
def upload_video():
    try:
        # 1. Grab the uploaded file
        video = request.files["file"]

        # 2. Setup folders
        os.makedirs("/data/uploads", exist_ok=True)
        os.makedirs("/data/output", exist_ok=True)

        # 3. Create unique file paths
        unique_id = str(uuid.uuid4())
        
        input_path = f"/data/uploads/{unique_id}.mp4"
        
        output_path = f"/data/output/{unique_id}.mp4"

        # 4. Save the raw uploaded file
        video.save(input_path)


        video_status_db[unique_id] = "Uploaded. Waiting to start..."

        thread = threading.Thread(
            target=background_video_editor,

            args=(input_path, output_path, unique_id)

        )

        thread.start()

        # 7. Instantly return a response! The user's browser won't crash.
        return render_template("progress.html", video_id = unique_id)

    except Exception as e:
        print(f"Upload error: {e}")
        # If you have an upload-error.html file, you can keep using it:
        return render_template("upload-error.html")



@app.route("/download/<unique_id>", methods=["GET"])
def download_video(unique_id):
    try:
        output_path = f"/data/output/{unique_id}.mp4"

        # Check the database status safely
        status = video_status_db.get(unique_id, "Unknown")

        if status == "Completed":
            if os.path.exists(output_path):
                return send_file(output_path, as_attachment=True)
                
            else:
                return render_template("upload-error.html")
                
        else:
            return render_template("progress.html", video_id=unique_id)

    except Exception as e:
        print(f"Download route error: {e}")
        return render_template("upload-error.html")


