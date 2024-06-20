from flask import Flask, request, send_file, render_template
from pydub import AudioSegment
import os
from werkzeug.utils import secure_filename
from pydub.utils import which

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
COMPRESSED_FOLDER = 'static/compressed/'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'aac'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESSED_FOLDER'] = COMPRESSED_FOLDER

# Check if FFmpeg is found in PATH
ffmpeg_path = which("ffmpeg")
ffprobe_path = which("ffprobe")

# Ensure that FFmpeg is found
if not ffmpeg_path or not os.path.isfile(ffmpeg_path):
    raise EnvironmentError("FFmpeg binary not found. Please ensure FFmpeg is installed and added to your PATH.")
if not ffprobe_path or not os.path.isfile(ffprobe_path):
    raise EnvironmentError("FFprobe binary not found. Please ensure FFmpeg is installed and added to your PATH.")

AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress_audio():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        output_filename = filename.rsplit('.', 1)[0] + "_compressed.aac"
        output_path = os.path.join(app.config['COMPRESSED_FOLDER'], output_filename)

        try:
            compress_audio_to_aac(upload_path, output_path, normalize=True, target_dBFS=-20.0)
        except Exception as e:
            return f"An error occurred while compressing the audio file: {e}"

        return send_file(output_path, as_attachment=True)
    
    return "Invalid file format"

def compress_audio_to_aac(input_file, output_file, bitrate="128k", normalize=False, target_dBFS=-20.0):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
        
        # Apply normalization if requested
        if normalize:
            change_in_dBFS = target_dBFS - audio.dBFS
            audio = audio.apply_gain(change_in_dBFS)
        
        # Export as ADTS (AAC) with the specified bitrate
        audio.export(output_file, format="adts", bitrate=bitrate)
        
        print(f"Audio file compressed and saved as {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    app.run(debug=True)
