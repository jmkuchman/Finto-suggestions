"""
  Custom validator decorators for API endpoints.

  The decorator goes through the connexion payload and
  validates/converts the data passing it through to the
  actual api method.

  Swagger handles most of the parameter validation, but
  in some cases, it is necessary to make sure that
  a specific row exists in database before proceeding.

  Usage:

  @suggestions_validator
  def get_suggestion(suggestion_id):
      return get_one_or_404(Suggestion, suggestion_id)
"""

from functools import wraps
import connexion
from .common import create_response, id_exists
from ..models import db, Event, Meeting, Suggestion, Tag, User


def _error_messagify(model):
    msg = "Given {}_id does not exist."
    return msg.format(str(model.__table__)[:-1])


def suggestions_validator(f):
    """
    A custom validator decorator for Suggestions.
    """
    @wraps(f)
    def wrapper(*args, **kw):

        payload = connexion.request.json

        # We need to check that meeting_id is a present in request parameters
        # and only after that check that id exists.
        # We check it against None since id 0 is falsy.
        meeting_id = payload.get('meeting_id')
        if meeting_id is not None and not id_exists(Meeting, meeting_id):
            return create_response({}, 404, _error_messagify(Meeting))

        # tag strings need to be converted to actual tags
        # please note, that nonexisting tags are removed from the list here
        tag_labels = payload.get('tags')
        if tag_labels:
            tag_labels_upper = [label.upper() for label in tag_labels]
            payload['tags'] = db.session.query(
                Tag).filter(Tag.label.in_(tag_labels_upper)).all()

        return f(*args, **kw)

    return wrapper


def reactions_validator(f):
    """
    A custom validator decorator for Reactions.
    """

    @wraps(f)
    def wrapper(*args, **kw):
        payload = connexion.request.json

        # Connexion doesn't support OpenAPI v3.0 yetm so no oneOf in schema :(
        # https://github.com/zalando/connexion/issues/420
        # Let's do it here

        event_id = payload.get('event_id')
        suggestion_id = payload.get('suggestion_id')

        # only one of either is allowed
        if event_id is not None and suggestion_id is not None:
            return create_response({}, 404, "Only on of either event_id or suggestion_id is allowed.")

        if event_id is not None and not id_exists(Event, event_id):
            return create_response({}, 404, _error_messagify(Event))

        if suggestion_id is not None and not id_exists(Suggestion, suggestion_id):
            return create_response({}, 404, _error_messagify(Suggestion))

        user_id = payload.get('user_id')
        if not id_exists(User, user_id):
            return create_response({}, 404, _error_messagify(User))

        return f(*args, **kw)

    return wrapper
