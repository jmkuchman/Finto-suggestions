from datetime import datetime
from collections import Counter
import enum
import json

from flask_sqlalchemy import SQLAlchemy as _NSQLAlc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from passlib.hash import pbkdf2_sha256 as hash_algorithm

class SQLAlchemy(_NSQLAlc):
    def apply_pool_defaults(self, app, options):
        super(SQLAlchemy, self).apply_pool_defaults(app, options)
        options["pool_pre_ping"] = True

def mDecoder(obj):
    '''
    This serializer prevents JSON from being encoded in ASCII
    and, thus, fixes issues with UTF-8 encoded search.
    '''
    return json.dumps(obj, ensure_ascii=False)

# If you want go switch a logging on, do it here: 'echo': False
db = SQLAlchemy(engine_options={'encoding': 'utf-8',
                                'echo': False, 'json_serializer': mDecoder})

class EventTypes(enum.IntEnum):
    ACTION = 0
    COMMENT = 1


class EventActionSubTypes(enum.IntEnum):
    STATUS = 0
    TAG = 1
    SYSTEM = 2


class SuggestionStatusTypes(enum.IntEnum):
    RECEIVED = 0,
    READ = 1,
    ACCEPTED = 2,
    REJECTED = 3,
    RETAINED = 4,
    ARCHIVED = 5


class SuggestionTypes(enum.IntEnum):
    NEW = 0
    MODIFY = 1


class UserRoles(enum.IntEnum):
    NORMAL = 0
    ADMIN = 1


class SerializableMixin():
    """
    Adds the method ´as_dict´ to an sqlalchemy model.
    Calling the method requires a special __public__ attribute,
    which acts as a whitelist for serializable columns.
    e.g. __public__ = ['id', 'created', 'modified']
    """

    def _serialize(self, obj):
        """
        A simple serializer override to handle Enums better.
        This could also be done on overriding flask_app.json_encoder.
        """
        if isinstance(obj, enum.Enum):
            return obj.name
        return obj

    def as_dict(self, strip=True):
        d = {c.name: self._serialize(getattr(self, c.name))
             for c in self.__table__.columns}
        if strip:  # strip hidden fields, such as meeting_id
            d = {k: v for k, v in d.items() if k in self.__public__}
        return d


class SuggestionTag(db.Model, SerializableMixin):
    __tablename__ = 'suggestion_tags_association'
    __public__ = ['tag_label', 'suggestion_id', 'event_id']

    tag_label = db.Column(db.String, db.ForeignKey(
        'tags.label'), primary_key=True)
    suggestion_id = db.Column(db.Integer, db.ForeignKey(
        'suggestions.id'), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))

    def __repr__(self):
        return '<SuggestionTag {}>'.format(self.code)


class Event(db.Model, SerializableMixin):
    """
    An object representing a single event in a suggestion's event stream.
    It can be an action, or a comment by a user, for example.
    """

    __tablename__ = 'events'
    __public__ = ['id', 'event_type', 'sub_type', 'text', 'value',
                  'reactions', 'user_id', 'suggestion_id', 'created', 'modified', 'tags']

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    event_type = db.Column(db.Enum(EventTypes), nullable=False)
    sub_type = db.Column(db.Enum(EventActionSubTypes), nullable=True)
    text = db.Column(db.Text)
    value = db.Column(db.Text, nullable=True)

    reactions = db.relationship('Reaction', backref='event', lazy='joined')

    # user: backref
    # suggestion: backref

    suggestion_id = db.Column(db.Integer, db.ForeignKey('suggestions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    tags = db.relationship(
        'Tag',
        secondary='suggestion_tags_association',
        backref=db.backref('events'),
        lazy='joined')

    def __repr__(self):
        msg = self.text if len(self.text) <= 16 else (self.text[:16] + '...')
        return '<Event {} | \'{}\'>'.format(self.event_type.name, msg)

    def as_dict(self, strip=True):
        serialized = super(Event, self).as_dict()
        serialized['reactions'] = [e.id for e in self.reactions]  # only ids
        serialized['tags'] = [e.as_dict(strip=strip) for e in self.tags]
        return serialized


class Reaction(db.Model, SerializableMixin):
    __tablename__ = 'reactions'
    __public__ = ['id', 'code', 'event_id', 'suggestion_id', 'user_id']

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship(
        "User",
        backref=db.backref("user", uselist=False),
        lazy='joined'
    )

    # suggestion: backref
    # event: backref

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    suggestion_id = db.Column(db.Integer, db.ForeignKey('suggestions.id'))

    def __repr__(self):
        return '<Emoji {}>'.format(self.code)


class Meeting(db.Model, SerializableMixin):
    __tablename__ = 'meetings'
    __public__ = ['id', 'name', 'created', 'modified', 'meeting_date']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    meeting_date = db.Column(db.DateTime, index=True)

    suggestions = db.relationship(
        'Suggestion',
        backref='meeting',
        lazy='joined'
    )

    def __repr__(self):
        return '<Meeting {}>'.format(self.id)

    def as_dict(self, strip=True):
        serialized = super(Meeting, self).as_dict()
        serialized['suggestions'] = [
            e.id for e in self.suggestions]  # only ids

        serialized['processed'] = Counter(
            [s.status.name.upper() for s in self.suggestions if s is not None and s.status not in ['READ', 'RECEIVED']])

        return serialized


class Suggestion(db.Model, SerializableMixin):
    __tablename__ = 'suggestions'
    __public__ = ["alternative_labels", "broader_labels", "created", "description", "groups", "id", "created", "modified",
                  "narrower_labels", "organization", "preferred_label", "reason", "related_labels", "status", "suggestion_type",
                  "uri", "scopeNote", "exactMatches", "neededFor", "yse_term", "meeting_id", "user_id"]

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # meeting: backref

    suggestion_type = db.Column(db.Enum(SuggestionTypes))
    status = db.Column(db.Enum(SuggestionStatusTypes), nullable=True)
    uri = db.Column(db.String(256))

    organization = db.Column(db.String(256))
    description = db.Column(db.Text)
    reason = db.Column(db.Text)

    preferred_label = db.Column(db.JSON)
    alternative_labels = db.Column(db.JSON)

    broader_labels = db.Column(db.JSON)
    narrower_labels = db.Column(db.JSON)
    related_labels = db.Column(db.JSON)
    groups = db.Column(db.JSON)
    scopeNote = db.Column(db.Text)
    exactMatches = db.Column(db.JSON)
    neededFor = db.Column(db.String(500))
    yse_term = db.Column(db.JSON)

    events = db.relationship('Event', backref='suggestion', lazy='joined')
    reactions = db.relationship(
        'Reaction', backref='suggestion', lazy='joined')

    tags = db.relationship('Tag',
                           secondary='suggestion_tags_association',
                           backref=db.backref('suggestions'),
                           cascade_backrefs=False,
                           lazy='joined')

    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        label = self.preferred_label.get('fi')
        return '<Suggestion \'{}\'>'.format(label)

    def as_dict(self, strip=True):
        # relationships (joins) should be expanded carefully
        serialized = super(Suggestion, self).as_dict()
        serialized['events'] = [e.as_dict() for e in self.events]
        serialized['reactions'] = [e.id for e in self.reactions]  # only ids
        serialized['tags'] = [e.as_dict(strip=strip) for e in self.tags]
        return serialized


class Tag(db.Model, SerializableMixin):
    __tablename__ = "tags"
    __public__ = ['label', 'color']

    label = db.Column(db.String(128), index=True, primary_key=True)
    color = db.Column(db.String(7), nullable=True)
    # suggestions: backref

    # convert tag always to uppercase
    @validates('label')
    def convert_upper(self, key, value):
        return value.upper()

    def __repr__(self):
        return '<Tag {}>'.format(self.label)

    def as_dict(self, strip=True):
        serialized = super(Tag, self).as_dict()
        return serialized


class User(db.Model, SerializableMixin):
    __tablename__ = 'users'
    __public__ = ['id', 'name', 'role', 'title', 'organization', 'imageUrl']

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64), index=True, nullable=False)
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    role = db.Column(db.Enum(UserRoles), default=UserRoles.NORMAL)
    password_hash = db.Column(db.String(128), nullable=True)
    title = db.Column(db.String(128), nullable=True)
    organization = db.Column(db.String(128), nullable=True)
    imageUrl = db.Column(db.Text, nullable=True)

    events = db.relationship('Event', backref='user', lazy='joined')

    @hybrid_property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, value):
        if value is not None:
            self.password_hash = hash_algorithm.hash(value)

    def validate_password(self, password):
        if password is not None:
            return hash_algorithm.verify(password, self.password_hash)

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def as_dict(self, strip=True):
        # relationships (joins) should be expanded carefully
        serialized = super(User, self).as_dict()
        # serialized['events'] = [e.as_dict(strip=strip) for e in self.events]  # whole events
        serialized['events'] = [e.id for e in self.events]  # only ids
        return serialized


class TokenBlacklist(db.Model, SerializableMixin):
    """
    JSON Web Token blacklist for logouts and user bans.
    """

    __tablename__ = 'tokens_blacklist'
    __public__ = ['id', 'jti', 'token_type', 'revoked', 'expires']  # as_dict

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)
