from flask import Flask, render_template, request, jsonify
import subprocess
import re
import os

app = Flask(__name__)

IPERF_PATH = os.path.join("tools", "iperf3.exe")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run_iperf():
    data = request.json
    print("Received request:", data)

    server = data.get("server")
    protocol = data.get("protocol")
    duration = data.get("duration", 10)
    bandwidth = data.get("bandwidth", "100M")

    cmd = [IPERF_PATH, "-c", server, "-t", str(duration)]

    if protocol == "udp":
        cmd += ["-u", "-b", bandwidth]

    print("Running command:", cmd)

    try:
        result = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            text=True,
            shell=False
        )
    except FileNotFoundError:
        return jsonify({
            "error": "iperf3.exe not found. Make sure it exists inside the tools folder."
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": e.output
        })

    # Extract per-second throughput values (for chart)
    intervals = re.findall(
        r"\[\s*\d+\]\s+\d+\.\d+-\d+\.\d+\s+sec\s+[\d.]+\s+\w+Bytes\s+([\d.]+)\s+Mbits/sec",
        result
    )

    throughput = intervals[-1] if intervals else "N/A"
    jitter = re.findall(r"([\d.]+)\s+ms", result)
    loss = re.findall(r"(\d+\.?\d*)%", result)

    return jsonify({
        "raw": result,
        "throughput": throughput,
        "jitter": jitter[-1] if jitter else "N/A",
        "loss": loss[-1] if loss else "0",
        "intervals": intervals
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
