import os
from dotenv import load_dotenv

load_dotenv()

from django.core.exceptions import ImproperlyConfigured


def get_env_variable(env_variable, default=None, required=False):
    """Helper function to fetch env variables

    Args:
        env_variable (str): Env variable to be fetched
        default (str, optional): Default value of the env variable. Defaults to None.
        required (bool, optional): Defines whether or not the variable is required. Defaults to False.

    Raises:
        ImproperlyConfigured: Exception raised when a variable is required but not set

    Returns:
        [type]: Set value of the env variable
    """
    value = os.getenv(env_variable, default)
    if required and not value:
        error_msg = f"Set the {env_variable} environment variable"
        raise ImproperlyConfigured(error_msg)
    return value
