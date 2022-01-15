def create_response(action):
    response = {}
    response['action'] = action
    return response


def add_result(response, result):
    try:
        response.update(result)
    except TypeError:
        response['result'] = result
    return response


def add_error(response, error_msg, error_code):
    response['error'] = error_msg
    response['error_code'] = error_code
    return response


def add_exception(response, exception):
    response['exception'] = str(type(exception))
    response['exception_msg'] = str(exception)
    return response
