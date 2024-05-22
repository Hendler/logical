import os
import pytest
from logical.tasks import tasks
from unittest.mock import patch, call
from invoke.context import Context

# Test the interactive_logic function for proper handling of English to Prolog conversion and appending to world.pl
@pytest.mark.parametrize("input_statement, expected_prolog_code", [
    ("Cows cannot fly.", "assertz(not(fly(cow)))."),
    ("Birds can fly.", "assertz(fly(bird))."),
    ("All humans are mortal.", "assertz(mortal(human))."),
    ("Socrates is a human.", "assertz(human(socrates))."),
    ("The sky is blue.", "assertz(blue(sky))."),
    ("Sugar is sweet.", "assertz(sweet(sugar))."),
    # Add more test cases as needed
])
def test_interactive_logic_conversion_and_appending(mock_open, mock_append_to_world, input_statement, expected_prolog_code):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', side_effect=[input_statement, 'exit']):
        # Mock the _openai_wrapper function to return the expected Prolog code for the input statement
        with patch('logical.tasks.functions._openai_wrapper', return_value={'prolog': expected_prolog_code}):
            # Mock the append_to_world function to track calls and ensure it's called with the expected Prolog code
            with patch('logical.tasks.tasks.append_to_world', mock_append_to_world), \
                 patch('builtins.open', mock_open):  # Mock the open function to ensure it's not called
                # Call the interactive_logic function with test_mode set to True
                formatted_prolog_code = tasks.interactive_logic(context, input_statement, test_mode=True)
                # Verify that the append_to_world function is called with the expected Prolog code when test_mode is True
                mock_append_to_world.assert_called_with(expected_prolog_code)
                # Verify that the open function is not called when test_mode is True
                mock_open.assert_not_called()
                # The assertion now checks if the formatted Prolog code exactly matches the expected Prolog code
                assert formatted_prolog_code == expected_prolog_code, f"Prolog code formatting error: Expected {expected_prolog_code}, got {formatted_prolog_code}"

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
                tasks.interactive_logic(context, statement='')
                # Verify that the queries are run against the contents of world.pl
                mocked_file.assert_called_once_with('/home/ubuntu/logical/logical/world.pl', 'r')
                # Verify that the run_logic_task is called for each query
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
    # Define a set of English statements and their expected Prolog translations
    test_cases = [
        ("Cows cannot fly.", "cows_cannot_fly."),
        ("Birds can fly.", "birds_can_fly."),
        ("All humans are mortal. Socrates is a human.", "mortal(socrates)."),
        # Add more test cases as needed
    ]
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
