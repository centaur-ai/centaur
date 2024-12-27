from flask import Flask
from flask_cors import CORS
from routes.evaluate import blueprint

app = Flask(__name__)
CORS(app)
app.register_blueprint(blueprint)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
