# airPen

Use an iPhone as an "air pen" by streaming IMU data to a Python WebSocket server.

## 1) Start server

From project root:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install websockets pygame-ce
python server/main.py
```

Server listens on `ws://0.0.0.0:8765`.

## 2) Open client page

Serve `index.html` on your Mac (required for iPhone Safari motion permissions):

```bash
python -m http.server 8000
```

Then open on iPhone:

`http://<YOUR-MAC-IP>:8000`

Both devices must be on the same Wi-Fi network.

## 3) Open pygame viewer on Mac

In a second terminal on your Mac:

```bash
source venv/bin/activate
python server/pygame_viewer.py
```

The viewer opens full-screen by default.

Controls:

- `C`: clear drawing
- `R`: reset motion tracker state on server
- `Esc`: quit viewer

## 4) Connect + stream

1. Open the page on laptop and phone.
2. On phone choose **Phone (Sender)**, set WebSocket URL to `ws://<YOUR-MAC-IP>:8765`, and tap **Connect**.
3. On phone tap **Start IMU** and allow motion permission.
4. Move the phone in the air; strokes are drawn in the pygame viewer on your Mac.
5. Use **Reset Stroke** to zero motion state.

## Notes

- iOS requires a user gesture before requesting motion permission.
- If `event.acceleration` is unavailable, the client derives linear acceleration from `accelerationIncludingGravity`.
- Position drifts over time (normal for IMU-only integration); use reset frequently.