from flask import Flask, render_template, request, send_file

import os

from flask import jsonify

from processing.make_video import generate_video

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/output"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)

@app.route("/")
def home():

    return render_template(
        "index.html"
    )

@app.route("/generate", methods=["POST"])
def generate():

    # GET FORM DATA

    video = request.files["video"]

    question = request.form["question"]

    story = request.form["story"]

    # SAVE VIDEO

    video_path = os.path.join(
        UPLOAD_FOLDER,
        video.filename
    )

    video.save(video_path)

    # GENERATE FINAL VIDEO

    output_path = generate_video(
        video_path,
        question,
        story
    )

    # RETURN VIDEO

    return jsonify({
    "success": True,
    "download_url": "/static/output/final_reel.mp4"
})

if __name__ == "__main__":

    app.run(debug=True)