import json
import subprocess
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = PROJECT_ROOT
ENGINE = PROJECT_ROOT / "engine"
OUTPUT = PROJECT_ROOT / "output"

BOUTIQUE_REPO = Path(
    r"D:\CyberSecurityProject\microservices-demo"
)

EXPERIMENTS = {
    "E1": {
        "base": "fc7f9d0",
        "head": "616368f",
        "name": "Authorization Regression",
    },
    "E2": {
        "base": "616368f",
        "head": "8af0ef3",
        "name": "Transaction Validation",
    },
    "E3": {
        "base": "8af0ef3",
        "head": "fcf2781",
        "name": "API Contract Evolution",
    },
    "E4": {
        "base": "fcf2781",
        "head": "c5135fa",
        "name": "Documentation Evolution",
    },
}


class SecurityVerificationHandler(SimpleHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(
            data,
            indent=2
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)

    def do_POST(self):

        if self.path != "/api/run":
            self.send_json(
                {"error": "Endpoint not found"},
                404
            )
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(length)

            request_data = json.loads(
                body.decode("utf-8")
            )

            experiment_id = request_data.get(
                "experiment"
            )

            if experiment_id not in EXPERIMENTS:
                self.send_json(
                    {
                        "error": (
                            "Invalid experiment. "
                            "Use E1, E2, E3 or E4."
                        )
                    },
                    400
                )
                return

            experiment = EXPERIMENTS[
                experiment_id
            ]

            command = [
                sys.executable,
                str(
                    ENGINE /
                    "pipeline.py"
                ),
                "--repo",
                str(BOUTIQUE_REPO),
                "--base",
                experiment["base"],
                "--head",
                experiment["head"],
            ]

            result = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )

            if result.returncode != 0:
                self.send_json(
                    {
                        "status": "error",
                        "experiment": experiment_id,
                        "message": (
                            "Verification pipeline failed."
                        ),
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    },
                    500
                )
                return

            rule_report_path = (
                OUTPUT /
                "security_rule_report.json"
            )

            verification_report_path = (
                OUTPUT /
                "verification_report.json"
            )

            impact_report_path = (
                OUTPUT /
                "security_impact_report.json"
            )

            rule_report = json.loads(
                rule_report_path.read_text(
                    encoding="utf-8"
                )
            )

            verification_report = json.loads(
                verification_report_path.read_text(
                    encoding="utf-8"
                )
            )

            impact_report = json.loads(
                impact_report_path.read_text(
                    encoding="utf-8"
                )
            )

            self.send_json(
                {
                    "status": "success",
                    "experiment": experiment_id,
                    "experiment_name": experiment[
                        "name"
                    ],
                    "base": experiment["base"],
                    "head": experiment["head"],
                    "security_rules": rule_report,
                    "verification": verification_report,
                    "security_impact": impact_report,
                    "pipeline_output": result.stdout,
                }
            )

        except subprocess.TimeoutExpired:

            self.send_json(
                {
                    "status": "error",
                    "message": (
                        "Verification pipeline timed out."
                    ),
                },
                500
            )

        except Exception as error:

            self.send_json(
                {
                    "status": "error",
                    "message": str(error),
                },
                500
            )


def main():

    if not BOUTIQUE_REPO.exists():
        print(
            "ERROR: Online Boutique repository "
            "was not found:"
        )
        print(BOUTIQUE_REPO)
        return

    server_address = (
        "127.0.0.1",
        8000
    )

    server = ThreadingHTTPServer(
        server_address,
        SecurityVerificationHandler
    )

    print()
    print(
        "=========================================="
    )
    print(
        " CONTINUOUS SECURITY VERIFICATION SERVER "
    )
    print(
        "=========================================="
    )
    print()
    print(
        "Framework:",
        PROJECT_ROOT
    )
    print(
        "Subject system:",
        BOUTIQUE_REPO
    )
    print()
    print(
        "Dashboard:"
    )
    print(
        "http://localhost:8000/web/"
    )
    print()
    print(
        "API endpoint:"
    )
    print(
        "POST /api/run"
    )
    print()
    print(
        "Press CTRL+C to stop."
    )
    print()

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nSecurity verification server stopped."
        )

    finally:
        server.server_close()


if __name__ == "__main__":
    main()