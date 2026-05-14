import os
import asyncio
import edge_tts
import numpy as np

from PIL import Image, ImageDraw, ImageFont

from faster_whisper import WhisperModel

from moviepy.video.io.VideoFileClip import VideoFileClip

from moviepy.audio.io.AudioFileClip import AudioFileClip

from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from moviepy.video.VideoClip import ImageClip

from moviepy.audio.AudioClip import concatenate_audioclips

# ========================================
# SETTINGS
# ========================================

FONT_SIZE = 80

TEXT_COLOR = "yellow"

STROKE_COLOR = "black"

STROKE_WIDTH = 6

BOTTOM_MARGIN = 250

WORDS_PER_CHUNK = 2

QUESTION_VOICE = "en-US-GuyNeural"

STORY_VOICE = "en-US-ChristopherNeural"

FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"

# ========================================
# CREATE TEXT IMAGE
# ========================================

def create_text_image(
    text,
    width=900,
    height=220,
    intro=False
):

    img = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(
        FONT_PATH,
        FONT_SIZE
    )

    color = "cyan" if intro else TEXT_COLOR

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=STROKE_WIDTH
    )

    text_width = bbox[2] - bbox[0]

    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2

    y = (height - text_height) / 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=color,
        stroke_width=STROKE_WIDTH,
        stroke_fill=STROKE_COLOR
    )

    return np.array(img)

# ========================================
# GENERATE TTS
# ========================================

async def generate_tts(text, voice, output_file):

    communicate = edge_tts.Communicate(
        text,
        voice,
        rate="+25%"
    )

    await communicate.save(output_file)

# ========================================
# MAIN FUNCTION
# ========================================

def generate_video(video_path, story, question):

    os.makedirs("static/output", exist_ok=True)

    # ========================================
    # INTRO TEXT
    # ========================================

    intro_text = "Reddit Stories"

    # ========================================
    # GENERATE AUDIO
    # ========================================

    asyncio.run(
        generate_tts(
            intro_text,
            QUESTION_VOICE,
            "static/output/intro.mp3"
        )
    )

    asyncio.run(
        generate_tts(
            story,
            STORY_VOICE,
            "static/output/story.mp3"
        )
    )

    print("TTS generated!")

    # ========================================
    # LOAD AUDIO
    # ========================================

    intro_audio = AudioFileClip(
        "static/output/intro.mp3"
    )

    story_audio = AudioFileClip(
        "static/output/story.mp3"
    )

    final_audio = concatenate_audioclips([
        intro_audio,
        story_audio
    ])

    audio_path = "static/output/voice.mp3"

    final_audio.write_audiofile(audio_path)

    print("Audio combined!")

    # ========================================
    # TRANSCRIBE
    # ========================================

    model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )

    segments, _ = model.transcribe(
        audio_path,
        word_timestamps=True
    )

    print("Word timestamps generated!")

    words = []

    for segment in segments:

        for word in segment.words:

            words.append({
                "word": word.word.strip(),
                "start": word.start,
                "end": word.end
            })

    # ========================================
    # GROUP WORDS
    # ========================================

    caption_chunks = []

    current_chunk = []

    for word in words:

        current_chunk.append(word)

        if len(current_chunk) >= WORDS_PER_CHUNK:

            caption_chunks.append({
                "text": " ".join(
                    w["word"] for w in current_chunk
                ),
                "start": current_chunk[0]["start"],
                "end": current_chunk[-1]["end"]
            })

            current_chunk = []

    if current_chunk:

        caption_chunks.append({
            "text": " ".join(
                w["word"] for w in current_chunk
            ),
            "start": current_chunk[0]["start"],
            "end": current_chunk[-1]["end"]
        })

    print("Caption chunks created!")

    # ========================================
    # LOAD VIDEO
    # ========================================

    video = VideoFileClip(video_path)

    video = video.subclipped(
        0,
        min(
            video.duration,
            final_audio.duration
        )
    )

    video = video.with_audio(final_audio)

    # ========================================
    # CREATE CAPTIONS
    # ========================================

    caption_clips = []

    # INTRO CAPTION

    intro_img = create_text_image(
        intro_text,
        intro=True
    )

    intro_clip = (
        ImageClip(intro_img)
        .with_duration(intro_audio.duration)
        .with_position(
            (
                "center",
                video.h - BOTTOM_MARGIN
            )
        )
    )

    caption_clips.append(intro_clip)

    # NORMAL CAPTIONS

    for chunk in caption_chunks:

        img_array = create_text_image(
            chunk["text"]
        )

        txt_clip = (
            ImageClip(img_array)
            .with_start(chunk["start"])
            .with_duration(
                chunk["end"] - chunk["start"]
            )
            .with_position(
                (
                    "center",
                    video.h - BOTTOM_MARGIN
                )
            )
        )

        caption_clips.append(txt_clip)

    # ========================================
    # FINAL VIDEO
    # ========================================

    final_video = CompositeVideoClip(
        [video] + caption_clips
    )

    output_path = "static/output/final_video.mp4"

    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=24,
        preset="ultrafast"
    )

    print("FINAL VIDEO CREATED!")

    return output_path