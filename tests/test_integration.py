import pytest
import sys
import unittest.mock as mock
import openai
import os
# Adjust path for importing the logical package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logical import _openai_wrapper

# Set the OPENAI_API_KEY environment variable for the test
os.environ["OPENAI_API_KEY"] = "fake-api-key"

def test_openai_wrapper():
    # Define a system message and user message for the test
    system_message = "This is a test system message."
    user_message = "This is a test user message."

    # Mock the OpenAI client's method to prevent actual instantiation
    with mock.patch('openai.ChatCompletion.create', return_value={"choices": [{"message": {"content": "Mocked response"}}]}):
        # Call the _openai_wrapper function with the test messages
        response = _openai_wrapper(system_message=system_message, user_message=user_message)

        # Assert that the response is not empty
        assert response != "", "The response from the OpenAI API should not be empty."

        # Assert that the response is a dictionary
        assert isinstance(response, dict), "The response from the OpenAI API should be a dictionary."

        # Assert that the response contains the expected keys
        assert "prolog" in response, "The response should contain the 'prolog' key."
        assert "notes" in response, "The response should contain the 'notes' key."

        # Additional assertions to check the expected format of the response
        # Since the response is mocked, we check for the mocked content
        assert "Mocked response" in response["prolog"], "The 'prolog' key should contain the mocked content."
