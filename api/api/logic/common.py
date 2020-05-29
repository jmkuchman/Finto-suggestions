# -*- coding: utf-8 -*-
import os
import smtplib
import codecs
import json
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict

from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
# from sqlalchemy import __version__
# from sqlalchemy import Table, MetaData
# from sqlalchemy_views import CreateView, DropView
from ..models import db, Suggestion, Event, Tag, SuggestionTypes, SuggestionStatusTypes, SuggestionTag
from ..authentication import verify_user_access_to_resource
# from sqlalchemy import create_engine  
from sqlalchemy import Table, Column, String, MetaData, func, literal, select
from sqlalchemy.orm import defer, undefer, load_only



class InvalidFilterException(Exception):
    pass


def create_response(data: Dict, status_code: int, message: str = None, **kwargs) -> Dict:
    response_dict = {}
    data = data if data else {}

    if kwargs:
        response_dict.update(kwargs)
    if message:
        response_dict["message"] = message
    # if status_code:
    response_dict["code"] = status_code
    response_dict["data"] = data

    if isinstance(data, list):
        response_dict["items"] = len(data)

    return response_dict, status_code


def id_exists(model: object, object_id: int) -> bool:
    """
    Checks if the given id exists in the given model object.

    :param object_id: id to search
    :param model: model to search from
    :returns: True if id exists, or id is None. False if user was no__table__t found in the model.
    """

    if object_id is None:
        return False

    return db.session.query(exists().where(model.id == object_id)).scalar()


def get_all_or_400_custom(query) -> str:
    """
        A generic get all, with a custom query function

        :param query: query instance
        :returns: All columns matching the query or 400
    """

    try:
        db_objs = query.all()
    except InvalidFilterException as e:
        return create_response({}, 400, str(e))

    serialized_objects = []
    if db_objs:
        serialized_objects = [o.as_dict() for o in db_objs]

    return create_response(serialized_objects, 200)


def get_all_or_400(model: object, limit: int, offset: int) -> str:
    """
    Returns all queried objects.
    Request query can be limited with additional parameters `limit` and `offset`.

    :param limit: Cap the results to :limit: results
    :param offset: Start the query from offset (e.g. for paging)
    :returns: All columns matching the query in json format or 400 and error message as JSON
    """

    query = model.query
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    return get_all_or_400_custom(query)

def get_selected_or_400(model: object):
    """
    Todo: Must be fixed to read selected entities as an argument

    OR

    Must be in the new component for "special cases" joining to handling database tables and entities 

    Returns all queried objects.

    :returns: All columns matching the query or 400 and error message
    """
    db_selected_objs = model.query.with_entities(model.id, model.name, model.created, model.modified, model.meeting_date).all()

    serialized_objects = {}
    helper_dict = {}
    content_array = []
    if db_selected_objs:
        serialized_objects = [o for o in db_selected_objs]
        for val in serialized_objects:
            helper_dict["id"] = val[0]
            helper_dict["name"] = val[1]
            helper_dict["created"] = val[2]
            helper_dict["modified"] = val[3]
            helper_dict["meeting_date"] = val[4]
            content_array.append(helper_dict)
            helper_dict = {}
    
    error_msg = "Did not find any data"

    if db_selected_objs:
        return create_response(content_array, 200)
    return create_response(None, 404, error_msg)

# def get_selected_from_model_or_400(model: object, fieldNameArray: []):
# def get_selected_from_model_or_400(model: object, jotain: str) -> str: # toimii
def get_selected_from_model_or_400(sugg_id: 0, limit: int, offset: int) -> str:
    """
    Todo: Must be fixed to read selected entities as an argument

    OR

    Must be in the new component for "special cases" joining to handling database tables and entities 

    Returns all queried objects.

    :returns: All columns matching the query or 400 and error message
    """
    # aaa


    # print("||||||||||||||||||||||||||||||")
    # print(__version__)

    result_to_be_finalised = {}

    # s_id = 5979
    s_id = sugg_id
    if s_id > 0:
        result_to_be_finalised["id"] = s_id

    s_created = True
    if s_created:
        # # 0.1)  palauttaa ehdotuksen luontihetken
        valueArray = []
        iterHelper = {r for r in Suggestion.query.options(load_only("created")).with_entities(Suggestion.created).\
            filter(Suggestion.id == sugg_id)}
        # For-loopista eroon - muotoile {(datetime.datetime(2016, 4, 28, 10, 16, 43),)}
        for tempItem in iterHelper:
            tempItem_substring = str(tempItem[0]).split(".", 1)[0]
            tempItem_substring = tempItem_substring[1:-1] 
            valueArray.append(tempItem_substring)
        result_to_be_finalised["created"] = valueArray
        valueArray = []

    s_modified = True
    if s_modified:
    # 0.2)  palauttaa ehdotuksen muokkaushetken
        valueArray = []
        iterHelper = {r for r in Suggestion.query.options(load_only("modified")).with_entities(Suggestion.modified).\
            filter(Suggestion.id == sugg_id)}
        # For-loopista eroon - muotoile {(datetime.datetime(2016, 4, 28, 10, 16, 43),)} paremmaksi
        for tempItem in iterHelper:
            tempItem_substring = str(tempItem[0]).split(".", 1)[0]
            tempItem_substring = tempItem_substring[1:-1] 
            valueArray.append(tempItem_substring)
        result_to_be_finalised["modified"] = valueArray
        valueArray = []

    s_tags = True
    if s_tags:
    # 1)
    #  TAGS Palauttaa yhden suggestionin kaikkien tagien labelit
        valueArray = []
        iterHelper = {r for r in SuggestionTag.query.options(load_only("tag_label")).\
            filter(SuggestionTag.suggestion_id == sugg_id)}
        for tempItem in iterHelper:
            valueArray.append(str(tempItem).split(" ", 1)[1][:-1])
        result_to_be_finalised["tags"] = valueArray
        valueArray = []

    s_status = True
    if s_status:
    # 2)
    #  Palauttaa yhden suggestionin statuksen
        valueArray = []
        iterHelper = {r for r in Suggestion.query.options(load_only("status")).with_entities(Suggestion.status).filter(Suggestion.id == sugg_id)}
        # Poista for-looppi ja muotoile {(<SuggestionStatusTypes.RECEIVED: 0>,)} oikein
        for tempItem in iterHelper:
            valueArray.append(str(tempItem[0]).rsplit('.', 1)[1])
        result_to_be_finalised["status"] = valueArray[0]
        valueArray = []
    # ------
    s_type = True
    if s_type:
    # 3)
    #  Palauttaa yhden suggestionin tyypin
        iterHelper = {r for r in Suggestion.query.options(load_only("suggestion_type")).with_entities(Suggestion.suggestion_type).filter(Suggestion.id == sugg_id)}
        # Muotoile {(<SuggestionTypes.NEW: 0>,)} ilman for-loopia
        for tempItem in iterHelper:
            result_to_be_finalised["suggestion_type"] = str(tempItem[0]).rsplit('.', 1)[1]
    s_comments_counted = True
    if s_comments_counted:
    # 4)
    #  palauttaa kommenttien lukumäärän ehdotukselle x
        result_to_be_finalised['comments_counted'] = Event.query.options(load_only("event_type")).filter(Event.event_type == 'COMMENT').filter(Event.suggestion_id == sugg_id).count()

    s_preferred_label = True
    if s_preferred_label:
    # 5)
    #  palauttaa preferred_labelin oikein (Saadaan ehdotuksen nimi id:llä oikein frontissakin)
        valueArray = [r for r in Suggestion.query.options(load_only("id", "preferred_label")).filter(Suggestion.id == sugg_id)]
        for tempItem in valueArray:
            result_to_be_finalised["preferred_label"] = tempItem.preferred_label
        valueArray = []


    s_ids = False
    if s_ids:
    # 6)  palauttaa ehdotusten haun offsetin ja limitin mukaisesti id-listan
        iterHelper = []
        valueArray = []
        iterHelper = [r for r in Suggestion.query.options(load_only("id")).with_entities(Suggestion.id).limit(limit).offset(offset)]
        for tempItem in iterHelper:
            valueArray.append(tempItem[0]) 
        result_to_be_finalised["ids"] = valueArray
        valueArray = []

    s_count = False
    if s_count:
    # 7)
    #  palauttaa suggestionien määrän
        result_to_be_finalised['suggestions_count'] = Suggestion.query.options(load_only("id")).with_entities(Suggestion.id).count()
    


    return result_to_be_finalised

# AAA https://docs.sqlalchemy.org/en/13/orm/tutorial.html
    

def get_one_or_404(model: object, primary_key: int) -> str:
    """
    Returns an object by primary_key.

    :param meeting_id: database column id
    :returns: success 200 with a serialized object or 404 and an error message as JSON
    """
    db_obj = model.query.get(primary_key)

    if db_obj:
        return create_response(db_obj.as_dict(), 200)

    msg = "Unable to find any {} with an id of {}.".format(
        model.__table__, primary_key)
    return create_response(None, 404, msg)


def get_count_or_400_custom(query) -> str:
    """
        Runs function count() on given query.

        :param query: query instance
        :returns: Row count of query or 400
    """
    try:
        db_count = query.count()
    except InvalidFilterException as e:
        return create_response(0, 400, str(e))

    return create_response({"count": db_count}, 200)


def create_or_400(model: object, payload: Dict, error_msg: str = None) -> str:
    """
    Creates a new object and commits it to the database.
    Checks if there is a need to send email. The sending depends always on Model
    :param model: database model to create
    :param payload: a single object
    :returns: the created user as json
    """
    db_obj = model(**payload)

    verify_user_access_to_resource(db_obj)

    try:
        db.session.add(db_obj)
        db.session.commit()
    except IntegrityError:
        msg = "Unable to create a new {}".format(str(model.__table__)[:-1])
        if error_msg:
            msg = error_msg
        db.session.rollback()
        return create_response(None, 400, msg)

    try:
        if db_obj.email:
            send_email_while_signing_up(db_obj.email)
    except Exception as exx:
        print("The object has no attribute --> " + str(exx))

    return create_response(db_obj.as_dict(), 201)


def delete_or_404(model: object, primary_key: int) -> str:
    """
    Deletes an object by primary_key from the database.

    :param model: sqlalchemy database object (column) to delete from
    :param primary_key: primary_key
    :returns: 204, No Content on success, 404 on error
    """

    db_obj = model.query.get(primary_key)

    if not db_obj:
        msg = "No {} found with id {}.".format(model.__table__, primary_key)
        return create_response(None, 404, msg)

    verify_user_access_to_resource(db_obj)

    db.session.delete(db_obj)
    db.session.commit()
    return (None, 204)  # No Content


def update_or_404(model: object, primary_key: int, payload: Dict) -> str:
    """
    Updates a single sqlalchemy model by id.

    :param model: SQLAlchemy database model
    :param primary_key: updated primary_key
    :param payload: payload to update the object with
    :returns: the updated object as json, or 404
    """

    old_object = model.query.get(primary_key)
    if not old_object:
        msg = "{} with an id {} doesn't exist.".format(
            str(model.__table__)[:-1], primary_key)
        return create_response(None, 404, msg)

    verify_user_access_to_resource(old_object)

    # create a new model instance, but replace its id
    db_obj = model(**payload)
    db_obj.id = old_object.id
    if 'modified' in model.__table__.columns:
        db_obj.modified = datetime.utcnow()
    if 'created' in model.__table__.columns:
        db_obj.created = old_object.created

    db.session.merge(db_obj)
    db.session.commit()

    return create_response(db_obj.as_dict(), 200)


def update_or_404_custom(model: object, primary_key: int, payload: Dict) -> str:
    """
    Updates a single sqlalchemy model by label.

    :param model: SQLAlchemy database model
    :param primary_key: updated primary_key
    :param payload: payload to update the object with
    :returns: the updated object as json, or 404
    """

    old_object = model.query.get(primary_key)
    if not old_object:
        msg = "{} with an id {} doesn't exist.".format(
            str(model.__table__)[:-1], primary_key)
        return create_response(None, 404, msg)

    # create a new model instance, but replace its id
    db_obj = model(**payload)
    db_obj.label = old_object.label

    db.session.merge(db_obj)
    db.session.commit()

    return create_response(db_obj.as_dict(), 200)


def patch_or_404(model: object, primary_key: int, payload: Dict) -> str:
    """
    Patches a single sqlalchemy model by primary_key.

    :param model: SQLAlchemy database model
    :param primary_key: patched objects primary_key
    :param payload: payload to patch the object with
    :returns: the patched object as json, or 404
    """

    db_obj = model.query.get(primary_key)
    if not db_obj:
        msg = "{} with an id {} doesn't exist.".format(
            str(model.__table__)[:-1], primary_key)
        return create_response(None, 404, msg)

    verify_user_access_to_resource(db_obj)

    # make sure that the `id` and `created` fitempItemthing = model.query.with_entities(model.id).count()elds never get updated
    payload.pop("id", None)
    payload.pop("created", None)

    # update SQLAlchemy object with new attributes
    for key, value in payload.items():
        setattr(db_obj, key, value)

    # update the modified field, also
    if 'modified' in model.__table__.columns:
        db_obj.modified = datetime.utcnow()

    try:
        db.session.commit()
    except IntegrityError:
        msg = "Unable to patch the {}. Please check that all properties have valid values.".format(
            str(model.__table__)[:-1])
        return create_response(None, 404, msg)

    return create_response(db_obj.as_dict(), 200)


def send_email_while_signing_up(email: str) -> str:
    """
    Method for sending email messages
    """

    if email:
        email_server_address = os.environ.get('EMAIL_SERVER_ADDRESS')
        email_server_port = os.environ.get('EMAIL_SERVER_PORT')
        default_sender = os.environ.get('EMAIL_SERVER_DEFAULT_SENDER_EMAIL')
        email_server_username = os.environ.get('EMAIL_SERVER_USERNAME')
        email_server_password = os.environ.get('EMAIL_SERVER_PASSWORD')

        body_string_raw = os.environ.get('WELCOME_MESSAGE_BODY')
        subject_string_raw = os.environ.get('WELCOME_SUBJECT') 
        body = MIMEText(body_string_raw.encode("utf-8"), _charset='utf-8')
        subject_text = MIMEText(subject_string_raw.encode("utf-8"), _charset='utf-8')

        # body = body_string_raw.encode('ascii','ignore')
        # subject_text = subject_string_raw.encode('ascii','ignore')


        message = 'Subject: {}\n\n{}'.format(
            subject_text,
            body)

        try:
            mailserver = smtplib.SMTP(email_server_address, email_server_port)
            mailserver.ehlo()
            mailserver.starttls()

            if email_server_username and email_server_password:
                mailserver.login(email_server_username, email_server_password)

            mailserver.sendmail(default_sender, [email], message)
            mailserver.quit()
            return True
        except Exception as ex:
            print(str(ex))
    return False
