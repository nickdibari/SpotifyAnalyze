import config
from app import app


if __name__ == '__main__':
    app.run(debug=config.DEBUG)
