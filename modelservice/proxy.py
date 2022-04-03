from flask import Flask, request

app = Flask(__name__)


# Main entrypoint
def run(master_hostname="localhost", master_port=50051, flask_port=5000):
    print("Running flask server...")
    app.config["MASTER_HOSTNAME"] = master_hostname
    app.config["MASTER_PORT"] = master_port
    app.run(host="0.0.0.0", port=flask_port)  # Entrypoint


@app.route("/model", methods=["GET"])
def get_model():
    return "At some point, your model will be returned from this endpoint"


@app.route("/model", methods=["POST"])
def submit_job():
    request_data: str = request.json
    print(f"request_data: {request_data}")

    return "At some point, your job will be submitted"
