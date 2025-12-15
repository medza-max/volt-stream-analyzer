from flask import Flask, request, jsonify
from playlist_analyzer import analyze_playlist_sync
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>⚡ Volt Stream Analyzer API</h1>
    <p>Working! Use POST /analyze to analyze playlists</p>
    """

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'playlist' not in request.files:
        return jsonify({'error': 'No playlist file'}), 400
    
    file = request.files['playlist']
    file.save('temp.m3u')
    
    report = analyze_playlist_sync('temp.m3u', check_links=True)
    os.remove('temp.m3u')
    
    return jsonify(report)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
