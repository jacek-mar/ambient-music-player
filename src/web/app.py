from flask import Flask, jsonify, request
from typing import Dict, Any

from ..state import StateManager

app = Flask(__name__, template_folder='templates')
state_manager: StateManager = None


def init_app(sm: StateManager):
    global state_manager
    state_manager = sm


@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')


@app.route('/api/state')
def get_state():
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    return jsonify(state_manager.get_state_dict())


@app.route('/api/play', methods=['POST'])
def play():
    if state_manager:
        state_manager.play()
    return jsonify({'success': True})


@app.route('/api/pause', methods=['POST'])
def pause():
    if state_manager:
        state_manager.pause()
    return jsonify({'success': True})


@app.route('/api/stop', methods=['POST'])
def stop():
    if state_manager:
        state_manager.stop()
    return jsonify({'success': True})


@app.route('/api/toggle', methods=['POST'])
def toggle():
    if state_manager:
        state_manager.toggle_play_pause()
    return jsonify({'success': True})


@app.route('/api/volume', methods=['POST'])
def set_volume():
    if state_manager:
        volume = request.json.get('volume', 0.7)
        state_manager.set_volume(volume)
    return jsonify({'success': True})


@app.route('/api/next', methods=['POST'])
def next_track():
    if state_manager:
        state_manager.next_track()
    return jsonify({'success': True})


@app.route('/api/prev', methods=['POST'])
def prev_track():
    if state_manager:
        state_manager.prev_track()
    return jsonify({'success': True})


@app.route('/api/shuffle', methods=['POST'])
def toggle_shuffle():
    if state_manager:
        state_manager.toggle_shuffle()
    return jsonify({'success': True})


@app.route('/api/playlist', methods=['POST'])
def set_playlist():
    if state_manager:
        playlist_id = request.json.get('playlist_id')
        if playlist_id:
            state_manager.set_playlist(playlist_id)
    return jsonify({'success': True})


@app.route('/api/track', methods=['POST'])
def play_track():
    if state_manager:
        track_id = request.json.get('track_id')
        if track_id:
            state_manager.play_track(track_id)
    return jsonify({'success': True})


@app.route('/api/position', methods=['POST'])
def set_position():
    if state_manager:
        position = request.json.get('position', 0)
        state_manager.set_position(position)
    return jsonify({'success': True})


@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    from ..database import get_all_playlists
    return jsonify(get_all_playlists())


@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    name = request.json.get('name')
    if not name:
        return jsonify({'error': 'Name required'}), 400
    from ..database import create_playlist
    playlist_id = create_playlist(name)
    return jsonify({'success': True, 'id': playlist_id})


@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    from ..database import delete_playlist
    delete_playlist(playlist_id)
    return jsonify({'success': True})


@app.route('/api/playlists/<int:playlist_id>/rename', methods=['PUT'])
def rename_playlist(playlist_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    name = request.json.get('name')
    if not name:
        return jsonify({'error': 'Name required'}), 400
    from ..database import rename_playlist
    rename_playlist(playlist_id, name)
    return jsonify({'success': True})


@app.route('/api/playlists/<int:playlist_id>/tracks', methods=['GET'])
def get_playlist_tracks_api(playlist_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    from ..database import get_playlist_tracks
    return jsonify(get_playlist_tracks(playlist_id))


@app.route('/api/playlists/<int:playlist_id>/tracks/<int:track_id>', methods=['DELETE'])
def remove_track_from_playlist(playlist_id, track_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    from ..database import remove_track_from_playlist
    remove_track_from_playlist(playlist_id, track_id)
    return jsonify({'success': True})


@app.route('/api/tracks', methods=['GET'])
def get_all_tracks_api():
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    from ..database import get_all_tracks
    return jsonify(get_all_tracks())


@app.route('/api/tracks/<int:track_id>', methods=['PUT'])
def update_track(track_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    title = request.json.get('title')
    artist = request.json.get('artist')
    from ..database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET title = ?, artist = ? WHERE id = ?", 
                  (title, artist, track_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/tracks/<int:track_id>', methods=['DELETE'])
def delete_track_api(track_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    from ..database import delete_track
    delete_track(track_id)
    return jsonify({'success': True})


@app.route('/api/playlists/<int:playlist_id>/tracks/<int:track_id>/move', methods=['POST'])
def move_track(playlist_id, track_id):
    if state_manager is None:
        return jsonify({'error': 'State manager not initialized'}), 500
    new_position = request.json.get('position')
    if new_position is None:
        return jsonify({'error': 'Position required'}), 400
    from ..database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE playlist_tracks SET position = ? WHERE playlist_id = ? AND track_id = ?",
                  (new_position, playlist_id, track_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


def run_server(port: int):
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
