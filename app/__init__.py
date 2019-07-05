import os

from flask import Flask


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="thisisasecretkey",
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # apply the blueprints to the app
    from app import developer, developer_auth, blog, auth

    app.register_blueprint(developer.bp)
    app.register_blueprint(developer_auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(auth.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="sign_in")

    # running locally... fro developmental purposes
    # please disable before deployment
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    return app
