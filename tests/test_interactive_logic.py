import os
import pytest
import logging
import re
from logical.tasks import tasks
from unittest.mock import patch, call
from invoke.context import Context

# Configure logger for test output
logger = logging.getLogger('test_logger')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# test_cases is a list of tuples where each tuple contains an English statement and its expected Prolog translation.
# This list is used throughout the tests to simulate the OpenAI API responses for converting English to Prolog.
test_cases = [
    ("Cows cannot fly.", "assertz(not(fly(cow)))."),
    ("Birds can fly.", "assertz(fly(bird))."),
    ("All humans are mortal.", "assertz(mortal(human))."),
    ("Socrates is a human.", "assertz(human(socrates))."),
    ("The sky is blue.", "assertz(blue(sky))."),
    ("Sugar is sweet.", "assertz(sweet(sugar))."),
    ("Water is wet.", "assertz(wet(water))."),
    ("Fire is hot.", "assertz(hot(fire))."),
    ("Snow is cold.", "assertz(cold(snow))."),
    ("Grass is green.", "assertz(green(grass))."),
    # Additional test cases can be added here as needed.
    # Ensure no duplicate English statements and that each has a valid Prolog translation.
]

def mock_openai_wrapper_response(input_statement, **kwargs):
    """
    Simulate the OpenAI API response for converting English statements to Prolog code.

    This function takes an input statement and searches for a matching
    statement in the test_cases list. If a match is found, it returns the expected Prolog
    code in the same format as the _openai_wrapper function would. If no match is found,
    it returns None to simulate the behavior of the _openai_wrapper function when it does
    not find a match. This allows us to test the interactive_logic function's response
    handling without making actual API calls. The None return value is used to test the
    interactive_logic function's ability to handle cases where the OpenAI API does not
    provide a Prolog translation for a given English statement.

    Args:
        input_statement (str): The English statement to be converted to Prolog code.
        **kwargs: Additional keyword arguments, not used but included for compatibility.

    Returns:
        str: The expected Prolog code or None if no match is found.
    """
    # Check if input_statement is None and return None immediately if it is
    if input_statement is None:
        return None
    # Search for the expected Prolog code for the given input statement
    for stmt, code in test_cases:
        if stmt == input_statement:
            # Return the expected Prolog code directly
            return code
    # Return None to indicate no match found
    return None

def mock_openai_wrapper_side_effect(**kwargs):
    """
    Side effect function for the _openai_wrapper mock.

    This function is used to simulate the behavior of the _openai_wrapper function
    during testing. It delegates to the mock_openai_wrapper_response function,
    passing the provided system_message and user_message and any additional keyword arguments.

    The function has been updated to use 'system_message' and 'user_message' to match the
    updated _openai_wrapper function signature. This change ensures that the mock function
    correctly simulates the behavior of the _openai_wrapper function during testing.

    Args:
        **kwargs: Keyword arguments for the _openai_wrapper function, including 'system_message' and 'user_message'.

    Returns:
        dict: A simulated OpenAI API response with the expected Prolog code.
    """
    # Extract the 'system_message' and 'user_message' keyword arguments
    system_message = kwargs.get('system_message')
    user_message = kwargs.get('user_message')
    # Call the mock_openai_wrapper_response function with the extracted messages
    prolog_code = mock_openai_wrapper_response(user_message, **kwargs)
    # Log the user message and the Prolog code for debugging purposes
    logger.debug(f"User message: {user_message}")
    logger.debug(f"Prolog code returned: {prolog_code}")
    # Return the response in the expected format, with the 'prolog' key at the top level
    if prolog_code is not None:
        response = {'prolog': prolog_code}
    else:
        # If no Prolog code is found, simulate the actual _openai_wrapper behavior
        response = {'prolog': None, 'error': "No Prolog code generated for the given English statement."}
    # Log the mock response for debugging purposes
    logger.debug(f"Mock OpenAI API response: {response}")
    return response

@pytest.mark.parametrize("input_statement, expected_prolog_code", test_cases)
def test_interactive_logic_conversion_and_appending(input_statement, expected_prolog_code, mock_open, mock_append_to_world):
    context = Context()
    with patch('logical.tasks.tasks._openai_wrapper', side_effect=mock_openai_wrapper_side_effect) as mock_wrapper, \
         patch('logical.tasks.tasks.append_to_world', mock_append_to_world), \
         patch('builtins.open', mock_open):
        actual_prolog_code = tasks.interactive_logic(context, input_statement, test_mode=False)
        # Normalize the Prolog code by removing all forms of whitespace for comparison
        expected_prolog_code_normalized = re.sub(r'\s+', '', expected_prolog_code)
        actual_prolog_code_normalized = re.sub(r'\s+', '', actual_prolog_code) if actual_prolog_code else ""
        # Log the normalized Prolog code for debugging purposes
        logger.debug(f"Normalized expected Prolog code: {expected_prolog_code_normalized}")
        logger.debug(f"Normalized actual Prolog code returned by interactive_logic: {actual_prolog_code_normalized}")
        # Assert that the normalized actual Prolog code matches the normalized expected Prolog code
        assert actual_prolog_code_normalized == expected_prolog_code_normalized, f"Expected Prolog code {expected_prolog_code_normalized}, but got {actual_prolog_code_normalized}"
        if expected_prolog_code is not None:
            # Ensure the mock_append_to_world is called with the normalized Prolog code
            mock_append_to_world.assert_called_once_with(expected_prolog_code_normalized)
            world_pl_path = os.path.join(tasks.ROOT_REPO_DIR, "world.pl")
            # Ensure the mock_open is called with the correct file path and mode
            mock_open.assert_called_once_with(world_pl_path, 'a')
            # Ensure the mock_open().write is called with the normalized Prolog code
            mock_open().write.assert_called_with(expected_prolog_code_normalized)
        else:
            mock_append_to_world.assert_not_called()
            mock_open.assert_not_called()

# Test the interactive_logic function for handling queries against world.pl
def test_interactive_logic_querying(mock_open, mock_run_logic_task):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', side_effect=['Is the sky blue?', 'Do cows fly?', 'exit']):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open(read_data='sky_is_blue.\ncows_cannot_fly.\n')) as mocked_file:
            # Mock the run_logic_task to simulate Prolog code execution
            with patch('logical.tasks.run_logic_task', mock_run_logic_task):
                # Call the interactive_logic function with test_mode set to False to simulate actual appending behavior
                tasks.interactive_logic(context, statement='', test_mode=False)
                # Verify that the file is opened in append mode when test_mode is False
                mocked_file.assert_called_once_with('/home/ubuntu/logical/logical/world.pl', 'a')
                # Verify that the run_logic_task is called for each query with the correct Prolog statements
                expected_calls = [call(context, 'sky_is_blue.'), call(context, 'cows_cannot_fly.')]
                mock_run_logic_task.assert_has_calls(expected_calls, any_order=True)

# Test the interactive_logic function for accumulation of Prolog statements in world.pl
def test_interactive_logic_accumulation(mock_open, mock_run_logic_task):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', side_effect=['Cows cannot fly.', 'Birds can fly.', 'exit']):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            # Mock the run_logic_task to simulate Prolog code execution
            with patch('logical.tasks.run_logic_task', mock_run_logic_task):
                tasks.interactive_logic(context, statement='')
                # Verify that multiple Prolog statements are appended to world.pl without clearing previous content
                calls = [call('/home/ubuntu/logical/logical/world.pl', 'a'), call().write('cows_cannot_fly.\n'), call().write('birds_can_fly.\n')]
                mocked_file.assert_has_calls(calls, any_order=False)
                # Verify that the run_logic_task is called for each valid Prolog statement
                expected_calls = [call(context, 'cows_cannot_fly.'), call(context, 'birds_can_fly.')]
                mock_run_logic_task.assert_has_calls(expected_calls, any_order=True)

# Test the interactive_logic function for handling invalid input gracefully
def test_interactive_logic_invalid_input(mock_open):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of invalid English statements
    with patch('builtins.input', return_value='This is not a logical statement.'):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            tasks.interactive_logic(context, statement='This is not a logical statement.')
            # Verify that invalid input does not result in appending to world.pl
            mocked_file.assert_not_called()

# Test the parse function for correct Prolog code generation
def test_parse_prolog_generation(mock_open):
    # Create a Context object to pass to the task
    context = Context()
    # Test each case
    for english_statement, expected_prolog in test_cases:
        with patch('logical.tasks.functions._openai_wrapper', return_value={'prolog': expected_prolog}):
            tasks.parse(context, english_statement)
            # Verify that the Prolog code is generated correctly
            mock_open.assert_called_once_with('/home/ubuntu/logical/logical/world.pl', 'a')
            mock_open().write.assert_called_with(f"\n{expected_prolog}\n")
            mock_open.reset_mock()

# Integration test for the full workflow from English statement input to Prolog code generation, validation, and execution
def test_full_workflow_integration(mock_open, mock_run_logic_task):
    # Create a Context object to pass to the task
    context = Context()
    # Define a set of English statements and their expected Prolog translations
    test_cases = [
        ("Cows cannot fly.", "cows_cannot_fly.", True),
        ("Birds can fly.", "birds_can_fly.", True),
        ("All humans are mortal. Socrates is a human.", "mortal(socrates).", True),
        ("This is not a logical statement.", None, False),
        # Add more test cases as needed
    ]
    # Test each case
    for english_statement, expected_prolog, is_valid in test_cases:
        with patch('logical.tasks.functions._openai_wrapper', return_value={'prolog': expected_prolog}):
            with patch('logical.tasks.tasks.validate_prolog_code', return_value=(is_valid, "")):
                with patch('logical.tasks.run_logic_task', mock_run_logic_task):
                    tasks.interactive_logic(context, statement=english_statement)
                    # Verify that the Prolog code is generated, validated, and executed correctly
                    if is_valid:
                        mock_open.assert_called_once_with('/home/ubuntu/logical/logical/world.pl', 'a')
                        mock_open().write.assert_called_with(f"\n{expected_prolog}\n")
                    else:
                        mock_open.assert_not_called()
                    mock_run_logic_task.assert_called_with(context, expected_prolog)
                    mock_open.reset_mock()
                    mock_run_logic_task.reset_mock()

# Test the interactive_logic function for handling incomplete English statements
def test_interactive_logic_incomplete_input(mock_open, mock_run_logic_task):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of incomplete English statements
    with patch('builtins.input', side_effect=['Cows', 'Birds can', 'exit']):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            # Mock the run_logic_task to simulate Prolog code execution
            with patch('logical.tasks.run_logic_task', mock_run_logic_task):
                tasks.interactive_logic(context, statement='')
                # Verify that incomplete inputs do not result in appending to world.pl
                mocked_file.assert_not_called()

# Test the interactive_logic function for handling nonsensical English statements
def test_interactive_logic_nonsensical_input(mock_open, mock_run_logic_task):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of nonsensical English statements
    with patch('builtins.input', side_effect=['Colorless green ideas sleep furiously.', 'exit']):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            # Mock the run_logic_task to simulate Prolog code execution
            with patch('logical.tasks.run_logic_task', mock_run_logic_task):
                tasks.interactive_logic(context, statement='')
                # Verify that nonsensical inputs do not result in appending to world.pl
                mocked_file.assert_not_called()

# Test the interactive_logic function for handling invalid Prolog code returned by OpenAI
def test_interactive_logic_invalid_prolog_generation(mock_open, mock_run_logic_task):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', return_value='Cows cannot fly.'):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            # Mock the _openai_wrapper to simulate invalid Prolog code generation
            with patch('logical.tasks.functions._openai_wrapper', return_value={'prolog': 'invalid_prolog_code'}):
                tasks.interactive_logic(context, statement='Cows cannot fly.')
                # Verify that invalid Prolog code does not result in appending to world.pl
                mocked_file.assert_not_called()

@pytest.fixture
def mock_open(mocker):
    """Fixture for mocking open calls."""
    return mocker.mock_open()

@pytest.fixture
def mock_append_to_world(mocker):
    """Fixture for mocking the append_to_world function."""
    return mocker.Mock()

@pytest.fixture
def mock_run_logic_task(mocker):
    """Fixture for mocking the run_logic_task function."""
    return mocker.Mock()
