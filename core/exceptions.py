from rest_framework.exceptions import APIException
from rest_framework import status

class GoogleAuthError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid Google authentication token."
    default_code = 'google_auth_error'


class GmailIntegrationError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error connecting to Gmail API."
    default_code = 'gmail_error'


class GeminiAPIError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error calling Gemini API."
    default_code = 'gemini_error'
