from datetime import datetime


def create_response(action):
    response = {}
    response['action'] = action
    response['datetime'] = datetime.utcnow().isoformat()
    return response


def add_result(response, result):
    response['results'] = response.get('results') or []
    response['results'].append(result)


def add_error(response, error_msg, error_code):
    response['error'] = error_msg
    response['error_code'] = error_code
    response['datetime'] = datetime.utcnow().isoformat()
    return response


def add_exception(response, exception):
    response['exception'] = str(type(exception))
    response['exception_msg'] = str(exception)
    response['datetime'] = datetime.utcnow().isoformat()
    return response
