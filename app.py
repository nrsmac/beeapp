import cv2
from flask import Flask, render_template, Response

app = Flask(__name__)

# Set up path routing. Avoids 404.
@app.route('/', methods=['POST', 'GET'])  # will we need post?
def index():
    return render_template('viewer.html') # Handle get, just view page


def gen():
    """Video streaming generator function."""
    img = cv2.imread("bee.jpg")
    img = cv2.resize(img, (0,0), fx=1, fy=1) 
    frame = cv2.imencode('.jpg', img)[1].tobytes()
    yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)

