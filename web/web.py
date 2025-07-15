from flask import Flask, render_template, request, redirect, url_for
from core.queue.queue import enqueue_download
from core.queue.db import SessionLocal
from core.queue.models import DownloadTask, TaskStatus

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            enqueue_download(url=url)
        return redirect(url_for('history'))
    return render_template('index.html')

@app.route('/history')
def history():
    session = SessionLocal()
    tasks = session.query(DownloadTask).all()
    current = session.query(DownloadTask).filter_by(status=TaskStatus.PROCESSING).first()
    session.close()
    return render_template('history.html', tasks=tasks, current=current)