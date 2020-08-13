def create_response(base_url, short_id, error_message=None):
    response = {"shorturl": base_url + short_id}
    if error_message is not None:
        response["error"] = error_message
    return response
