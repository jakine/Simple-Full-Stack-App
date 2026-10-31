from rest_framework.exceptions import APIException


class Conflict(APIException):
    status_code = 409
    default_detail = "This conflicts with an existing record."
    default_code = "conflict"
