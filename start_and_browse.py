from app import create_app
import webbrowser
import threading
import time

app = create_app()

def open_browser():
    time.sleep(1)
    webbrowser.open('http://localhost:5000/events')

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=True, port=5000)
