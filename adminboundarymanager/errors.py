class Error(Exception):

    def __init__(self, message):
        self.message = message

    @property
    def serialize(self):
        return {
            'message': self.message
        }


class InvalidFile(Error):
    pass


class NoShpFound(Error):
    pass


class NoShxFound(Error):
    pass


class NoDbfFound(Error):
    pass


class UnsupportedBoundaryLevel(Error):
    pass


class MissingBoundaryField(Error):
    pass


class NoMatchingBoundaryLayer(Error):
    pass


class NoMatchingBoundaryData(Error):
    pass


class InvalidBoundaryGeomType(Error):
    pass
