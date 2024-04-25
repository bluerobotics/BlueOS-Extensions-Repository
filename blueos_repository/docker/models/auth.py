import dataclasses
import datetime
from typing import Optional


@dataclasses.dataclass
class AuthToken:
    """
    Data structure to store the authorization token information

    Attributes:
        token (str): An opaque Bearer token that clients should supply to subsequent requests in the Authorization header.
        access_token (str): A token used for OAuth 2.0 compatibility. Equivalent to the `token` attribute.
        expires_in (Optional[int]): The duration in seconds since the token was issued that it will remain valid. Defaults to 60 seconds.
        issued_at (Optional[datetime.datetime]): The UTC time at which the token was issued, in RFC3339 format.
        refresh_token (Optional[str]): A token that can be used to obtain new access tokens for different scopes.
    """

    token: Optional[str] = None
    access_token: Optional[str] = None
    expires_in: int = 60
    issued_at: Optional[datetime.datetime] = None
    refresh_token: Optional[str] = None

    def __post_init__(self) -> None:
        # Ensure that at least one of `token` or `access_token` is provided.
        if not self.token and not self.access_token:
            raise ValueError("Either 'token' or 'access_token' must be specified.")

        self.issued_at = (
            datetime.datetime.fromisoformat(str(self.issued_at))
            if self.issued_at
            else datetime.datetime.now(datetime.timezone.utc)
        )

    @property
    def is_expired(self) -> bool:
        """
        Check if the token is expired.

        Returns:
            bool: True if the token is expired, False otherwise.
        """

        if not self.issued_at:
            return True

        return (datetime.datetime.now(datetime.timezone.utc) - self.issued_at).total_seconds() > self.expires_in
