import dataclasses


@dataclasses.dataclass
class RateLimit:
    """
    Represents the rate limit information of the Docker Registry API.

    Attributes:
        limit (int): The rate limit.
        remaining (int): The remaining requests.
        interval_seconds (int): Base interval that the rate limit is calculated, by example, if you receive `limit`
            as 100 and `interval_seconds` as 3600, you can make 100 requests per hour.
        source_ip (str): The source IP address of the request.
    """

    limit: int
    remaining: int
    interval_seconds: int
    source_ip: str
