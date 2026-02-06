# server.py
from flask import Flask, request, jsonify
import multiprocessing
import io
import os
import contextlib
import traceback
import dotenv
dotenv.load_dotenv()

# Load PORT env from .env
PORT = os.getenv("PORT")

app = Flask(__name__)

def _worker(code_string, event, return_queue):
    """
    Runs in a separate process.
    Captures stdout so we can return logs like CloudWatch.
    """
    local_scope = {}
    stdout_capture = io.StringIO()
    
    try:
        # Redirect stdout to capture print statements
        with contextlib.redirect_stdout(stdout_capture):
            # 1. compile/exec the string
            exec(code_string, {}, local_scope)
            
            # 2. Check for handler
            if "handler" not in local_scope:
                raise ValueError("Function 'handler(event, context)' not found.")
            
            # 3. Run the handler
            # We mock a simple context object
            context = {"memory_limit_mb": 128, "aws_request_id": "mock-id"}
            result = local_scope["handler"](event, context)
            
            return_queue.put({
                "status": "success", 
                "result": result,
                "logs": stdout_capture.getvalue()
            })
            
    except Exception:
        # Capture the full traceback for debugging
        return_queue.put({
            "status": "error", 
            "error": traceback.format_exc(),
            "logs": stdout_capture.getvalue()
        })

def execute_with_timeout(code_string, event, timeout_seconds):
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_worker, args=(code_string, event, q))
    p.start()
    p.join(timeout_seconds)
    
    if p.is_alive():
        p.terminate()
        p.join()
        return {"status": "error", "error": "Execution Timed Out (Limit Exceeded)"}
    
    if not q.empty():
        return q.get()
    
    return {"status": "error", "error": "Process crashed unexpectedly"}

@app.route('/invoke', methods=['POST'])
def invoke():
    """
    Endpoint mimicking AWS Lambda invocation URL structure.
    """
    data = request.json
    
    code = data.get('code', '')
    event = data.get('event', {})
    timeout = data.get('timeout', 3) # Default 3 seconds
    
    if not code:
        return jsonify({"error": "No code provided"}), 400

    response = execute_with_timeout(code, event, timeout)
    return jsonify(response)

if __name__ == '__main__':
    # Threaded=True allows handling multiple requests, 
    # though the heavy lifting is done by multiprocessing
    app.run(host='0.0.0.0', port=PORT)