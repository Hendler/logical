import pytest
from logical import _openai_wrapper

def test_openai_wrapper():
    # Define a system message and user message for the test
    system_message = "This is a test system message."
    user_message = "This is a test user message."

    # Call the _openai_wrapper function with the test messages
    response = _openai_wrapper(system_message=system_message, user_message=user_message)

    # Assert that the response is not empty
    assert response != "", "The response from the OpenAI API should not be empty."

    # Assert that the response is a string
    assert isinstance(response, str), "The response from the OpenAI API should be a string."

    # TODO: Add more specific assertions based on the expected format of the response
