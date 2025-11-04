from rest_framework.exceptions import APIException

class ForbiddenActiveStatusChange(APIException):
    status_code = 403
    default_code = 'role_change_forbidden'
    default_detail = 'forbidden_role_change'