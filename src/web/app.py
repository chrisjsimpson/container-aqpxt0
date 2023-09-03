from flask import Flask, render_template, request
from db import get_db, close_db
import sqlalchemy
from logger import log
import tempfile
import subprocess

app = Flask(__name__)
app.teardown_appcontext(close_db)


@app.route("/health")
def health():
    log.info("Checking /health")
    db = get_db()
    health = "BAD"
    try:
        result = db.execute("SELECT NOW()")
        result = result.one()
        health = "OK"
        log.info(f"/health reported OK including database connection: {result}")
    except sqlalchemy.exc.OperationalError as e:
        msg = f"sqlalchemy.exc.OperationalError: {e}"
        log.error(msg)
    except Exception as e:
        msg = f"Error performing healthcheck: {e}"
        log.error(msg)

    return health

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Retrieve data from the form using request.form
        secret_name = request.form.get("secretName")
        vault_password = request.form.get("vaultPassword")
        secret_value = request.form.get("secretValue")
        # Save vault_password to a temporary file called 'password' (mktemp)
        # Run:
        # ansible-vault encrypt_string \
        # --vault-password-file password 'secret_value --name 'secret_name'
        # Save vault_password to a temporary file called 'password' (mktemp)
        with tempfile.NamedTemporaryFile(
            mode="w+t", delete=False
        ) as temp_file:  # noqa: E501
            temp_file.write(vault_password)
            temp_file_path = temp_file.name

        cmd = [
            "ansible-vault",
            "encrypt_string",
            "--vault-password-file",
            temp_file_path,
            secret_value,
            "--name",
            secret_name,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Deleting the temporary password file
        subprocess.run(["rm", temp_file_path])

        return "Encrypted result: <pre>{}</pre>".format(result.stdout)
    return render_template("index.html")