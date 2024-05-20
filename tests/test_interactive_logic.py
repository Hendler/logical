import pytest
from logical.tasks import tasks
from unittest.mock import patch
from invoke.context import Context

# Test the interactive_logic function for proper handling of English to Prolog conversion and appending to world.pl
def test_interactive_logic_conversion_and_appending(mock_open):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', return_value='Cows cannot fly.'):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            tasks.interactive_logic(context, statement='Cows cannot fly.')
            # Verify that the Prolog statement is appended to world.pl
            mocked_file.assert_called_once_with('world.pl', 'a')
            mocked_file().write.assert_called_with('cows_cannot_fly.\n')

# Test the interactive_logic function for handling queries against world.pl
def test_interactive_logic_querying(mock_open):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', return_value='Can cows fly?'):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open(read_data='cows_cannot_fly.\n')) as mocked_file:
            tasks.interactive_logic(context, statement='Can cows fly?')
            # Verify that the query is run against the contents of world.pl
            mocked_file.assert_called_once_with('world.pl', 'r')
            # Assuming the run_logic_task function will handle the actual Prolog query execution

# Test the interactive_logic function for accumulation of Prolog statements in world.pl
def test_interactive_logic_accumulation(mock_open):
    # Create a Context object to pass to the task
    context = Context()
    # Mock the input to simulate user input of English statements
    with patch('builtins.input', side_effect=['Cows cannot fly.', 'Birds can fly.', 'exit']):
        # Mock the open function to simulate file operations on world.pl
        with patch('builtins.open', mock_open) as mocked_file:
            tasks.interactive_logic(context, statement='')
            # Verify that multiple Prolog statements are appended to world.pl without clearing previous content
            calls = [call('world.pl', 'a'), call().write('cows_cannot_fly.\n'), call().write('birds_can_fly.\n')]
            mocked_file.assert_has_calls(calls, any_order=False)

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

@pytest.fixture
def mock_open(mocker):
    """Fixture for mocking open calls."""
    return mocker.mock_open()
