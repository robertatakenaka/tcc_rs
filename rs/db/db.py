from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
)
from mongoengine.document import NotUniqueError
from mongoengine import (
    connect,
    Q,
)

from rs import exceptions


def mk_connection(host):
    try:
        if not host:
            raise ValueError("Missing host of mongodb")
        _db_connect_by_uri(host)
    except Exception as e:
        raise exceptions.DBConnectError(
            {"exception": type(e), "msg": str(e)}
        )


@retry(wait=wait_exponential(), stop=stop_after_attempt(10))
def _db_connect_by_uri(uri):
    """
    mongodb://{login}:{password}@{host}:{port}/{database}
    """
    conn = connect(host=uri)
    print("%s connected" % uri)
    return conn


@retry(wait=wait_exponential(), stop=stop_after_attempt(10))
def _db_connect(host, port, schema, login, password, **extra_dejson):
    uri = "mongodb://{creds}{host}{port}/{database}".format(
        creds="{}:{}@".format(login, password) if login else "",
        host=host,
        port="" if port is None else ":{}".format(port),
        database=schema,
    )

    return connect(host=uri, **extra_dejson)


def get_record_by__id(DataModelClass, _id):
    if not _id:
        raise ValueError("get_record_by__id requires `_id` argument")

    try:
        return DataModelClass.objects(pk=_id)[0]
    except IndexError:
        return None


def create_data_model(DataModelClass):
    try:
        return DataModelClass()
    except Exception as e:
        raise exceptions.DBCreateDocumentError(
            {"exception": type(e), "msg": str(e)}
        )


def save_record(data):
    if not hasattr(data, 'created'):
        data.created = None
    try:
        data.save()
    except NotUniqueError as e:
        raise exceptions.DBSaveNotUniqueError(e)
    else:
        return data


def get_records(DataModelClass, **kwargs):
    try:
        order_by = kwargs.pop("order_by")
    except KeyError:
        order_by = '-updated'

    try:
        items_per_page = kwargs.pop("items_per_page")
    except KeyError:
        items_per_page = 50

    try:
        page = kwargs.pop("page")
    except KeyError:
        page = 1

    skip = ((page - 1) * items_per_page)
    limit = items_per_page

    if kwargs.get("qs"):
        return DataModelClass.objects(
            kwargs.get("qs")).order_by(order_by).skip(skip).limit(limit)
    return DataModelClass.objects(
        **kwargs).order_by(order_by).skip(skip).limit(limit)


# def get_query_set_with_or(field_names, values):
#     qs = None
#     for name, value in zip(field_names, values):
#         if not value:
#             continue
#         _kwargs = {name: value}
#         if qs:
#             qs |= Q(**_kwargs)
#         else:
#             qs = Q(**_kwargs)
#     return qs


# def get_query_set_with_and(field_names, values):
#     qs = None
#     for name, value in zip(field_names, values):
#         if not value:
#             continue
#         _kwargs = {name: value}
#         if qs:
#             qs &= Q(**_kwargs)
#         else:
#             qs = Q(**_kwargs)
#     return qs


# def _get_kwargs(query_set, items_per_page, page, order_by):
#     arg_names = ['qs', 'items_per_page', 'page', 'order_by']
#     arg_values = [query_set, items_per_page, page, order_by]
#     return {
#         k: v for k, v in zip(arg_names, arg_values) if v
#     }
