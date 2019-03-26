class FlaskWarehouse:
    """
    Clean abstraction over several file storage backends (S3, Alicloud, local).
    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        '''Initalizes the application with the extension.
        :param app: The Flask application object.
        '''
        pass


__all__ = ["FlaskWarehouse"]
