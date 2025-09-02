import os
import subprocess
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify

app = Flask(__name__)

def download_partial_audio(url, output_path, duration=60):
    cmd = [
        'ffmpeg', '-y', '-ss', '0', '-t', str(duration),
        '-i', url,
        '-vn', '-ac', '1', '-ar', '16000',
        '-f', 'wav', output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr.decode()}")

def read_audio(file_path):
    y, sr = sf.read(file_path)
    if y.ndim > 1:
        y = y[:, 0]
    return y, sr

def fft_cross_correlation(ref_signal, target_signal, sr):
    n = len(ref_signal) + len(target_signal) - 1
    X = np.fft.fft(ref_signal, n=n)
    Y = np.fft.fft(target_signal, n=n)
    corr = np.fft.ifft(X * np.conj(Y)).real
    delay_index = np.argmax(corr)
    if delay_index > n // 2:
        delay_index -= n
    delay_sec = delay_index / sr
    return delay_sec * 1000  # ms

@app.route('/', methods=['GET'])
def get_delay():
    hindi_url = request.args.get('delay')
    english_url = request.args.get('videourl')

    if not hindi_url or not english_url:
        return jsonify({"error": "Missing query parameters: delay (audio URL) and videourl (video URL) required."}), 400

    try:
        download_partial_audio(hindi_url, "hindi.wav")
        download_partial_audio(english_url, "english.wav")
        hindi, sr1 = read_audio("hindi.wav")
        english, sr2 = read_audio("english.wav")

        if sr1 != sr2:
            return jsonify({"error": "Sample rates don't match."}), 400

        delay_ms = fft_cross_correlation(english, hindi, sr1)

        if delay_ms > 0:
            note = f"Hindi audio lags English by {delay_ms:.2f} ms"
        elif delay_ms < 0:
            note = f"Hindi audio leads English by {abs(delay_ms):.2f} ms"
        else:
            note = "Hindi audio is perfectly aligned with English"

        result = {
            "delay_ms": round(delay_ms, 2),
            "note": note
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
