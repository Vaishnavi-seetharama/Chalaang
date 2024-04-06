from quart import Quart
from quart_cors import cors
from routes import bp as routes_bp

app = Quart(__name__)
cors(app)

app.register_blueprint(routes_bp)

if __name__ == "__main__":
    app.run()
