"""
Authentication helpers for reading JWTs from HttpOnly cookies.

`CookieJWTAuthentication` extends DRF SimpleJWT's `JWTAuthentication`
to first try the Authorization header (standard behavior) and then
fall back to the `access_token` cookie. This allows "cookie-based"
auth on the API without exposing tokens to JavaScript.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that supports HttpOnly cookie fallback.

    Order of precedence:
      1) Authorization header (Bearer <token>)
      2) `access_token` cookie
    """

    def authenticate(self, request):
        """
        Attempt to authenticate the request.

        Returns:
            (user, validated_token) on success, or None if no token is provided.
        Raises:
            AuthenticationFailed if token is present but invalid/expired.
        """

        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get('access_token')

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token