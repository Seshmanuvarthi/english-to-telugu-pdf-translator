from flask import Flask, render_template, request, send_file, Response, jsonify
import os
import uuid
import threading
import json
import time
from utils.translate import translate_batch
from utils.pdf_processor import process_pdf

print("Flask app is starting...")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Store translation job progress
jobs = {}


def run_translation(job_id, input_path, output_path):
    """Run translation in a background thread, updating job progress."""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Starting translation...'

        process_pdf(input_path, output_path, translate_batch,
                    progress_callback=lambda data: update_progress(job_id, data))

        jobs[job_id]['status'] = 'done'
        jobs[job_id]['percent'] = 100
        jobs[job_id]['message'] = 'Translation complete!'

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f'Error: {str(e)}'
        print(f"Translation error for job {job_id}: {e}")
        import traceback
        traceback.print_exc()


def update_progress(job_id, data):
    """Callback to update job progress from pdf_processor."""
    if job_id in jobs:
        jobs[job_id].update(data)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/translate', methods=['POST'])
def translate():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    uploaded_file = request.files['pdf']
    if uploaded_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not uploaded_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Please upload a PDF file'}), 400

    filename = uploaded_file.filename
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_filename = f'telugu_{filename}'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    uploaded_file.save(input_path)

    # Create a job
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        'status': 'queued',
        'current_page': 0,
        'total_pages': 0,
        'percent': 0,
        'message': 'Queued for translation...',
        'output_path': output_path,
        'output_filename': output_filename,
    }

    # Start translation in background thread
    thread = threading.Thread(target=run_translation, args=(job_id, input_path, output_path))
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/progress/<job_id>')
def progress(job_id):
    """SSE endpoint streaming real-time translation progress."""
    def generate():
        while True:
            if job_id not in jobs:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Job not found'})}\n\n"
                break

            job = dict(jobs[job_id])  # Copy to avoid race conditions
            yield f"data: {json.dumps(job, default=str)}\n\n"

            if job['status'] in ('done', 'error'):
                break

            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                        'Connection': 'keep-alive',
                    })


@app.route('/status/<job_id>')
def status(job_id):
    """Polling fallback — returns current job status as JSON."""
    if job_id not in jobs:
        return jsonify({'status': 'error', 'message': 'Job not found'}), 404
    return jsonify(jobs[job_id])


@app.route('/download/<job_id>')
def download(job_id):
    """Download the translated PDF."""
    if job_id not in jobs:
        return "Job not found", 404

    job = jobs[job_id]
    if job['status'] != 'done':
        return "Translation not complete", 400

    file_path = os.path.abspath(job['output_path'])
    if not os.path.exists(file_path):
        return "Output file not found", 404

    return send_file(file_path, as_attachment=True,
                     download_name=job['output_filename'])


if __name__ == '__main__':
    app.run(debug=True, port=5001, use_reloader=False)
