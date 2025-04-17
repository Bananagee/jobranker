import io
import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# only allow Excel or CSV uploads
ALLOWED_EXT = ('.xls', '.xlsx', '.csv')

def allowed_file(filename):
    return bool(filename) and filename.lower().endswith(ALLOWED_EXT)

def process_file(file_storage):
    # reject if missing or wrong extension
    if not (file_storage and allowed_file(file_storage.filename)):
        return None, "Unsupported file type"
    # read entire upload into memory
    data = file_storage.read()
    buf = io.BytesIO(data)
    try:
        # parse with pandas directly from BytesIO
        if file_storage.filename.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(buf)
        else:
            df = pd.read_csv(buf)
        # return just an HTML preview of the first few rows
        return df.head().to_html(index=False), None
    except Exception as e:
        return None, f"Failed to process file: {e}"

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def ajax_upload():
    preview, err = process_file(request.files.get("file"))
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"preview": preview})

if __name__ == "__main__":
    app.run(debug=True)