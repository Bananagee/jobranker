import io
import pandas as pd
from flask import Flask, render_template, request, jsonify

from utils import file_hash, get_index_entry, update_first_index

app = Flask(__name__)

# only allow Excel or CSV uploads
ALLOWED_EXT = (".xls", ".xlsx", ".csv")

def allowed_file(filename: str) -> bool:
    return bool(filename) and filename.lower().endswith(ALLOWED_EXT)

def process_file(file_storage) -> tuple[str|None, str|None, str|None]:
    """
    Returns: (preview_html, error_message, error_code)
    Only one of preview_html vs error_message+error_code will be non‑None.
    """
    if not (file_storage and allowed_file(file_storage.filename)):
        return None, "Invalid file type. Please upload a .xls, .xlsx or .csv.", "UNSUPPORTED_TYPE"

    data    = file_storage.read()
    hash_str= file_hash(data)
    fname   = file_storage.filename
    ip      = request.remote_addr or "unknown"

    # check if we've seen this broken before
    existing = get_index_entry(hash_str)
    if existing and existing.get("broken"):
        # log the repeat attempt
        update_first_index(hash_str, broken=True, filename=fname, ip=ip)
        return None, "This file was previously detected as invalid and was skipped.", "PREVIOUSLY_BROKEN"

    # try to parse a small preview
    buf = io.BytesIO(data)
    try:
        if fname.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(buf)
        else:
            df = pd.read_csv(buf)

        df_preview  = df.iloc[:5, :5]
        preview_html= df_preview.to_html(index=False)

        # record success
        update_first_index(hash_str, broken=False, filename=fname, ip=ip)
        return preview_html, None, None

    except Exception as e:
        # record failure
        update_first_index(hash_str, broken=True, filename=fname, ip=ip)
        return None, "Corrupted or malformed file. Please check your Excel/CSV.", "PARSE_ERROR"

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def ajax_upload():
    preview, err_msg, err_code = process_file(request.files.get("file"))

    if err_msg:
        # return both a human message and a code
        return jsonify({"error": err_msg, "code": err_code}), 400

    return jsonify({"preview": preview})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")