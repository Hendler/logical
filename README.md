# logical

ChatGPT logic engine using [Prolog](https://en.wikipedia.org/wiki/Prolog).

First developed at the [OpenAI emergency hackathon on 3/5/2023](https://twitter.com/nonmayorpete/status/1632456433102098434).

<img alt="Bertrand Russell" src="./russell.png" />

## Usage

To use the logical engine, follow these steps:

1. Install the package and its dependencies.
2. Set up the required environment variables, including your OpenAI API key.
3. Use the `interactive_logic` task to input English statements and receive Prolog queries or truth values interactively.

Example interactive session:
```
$ logical interactive-logic
Enter an English statement: All humans are mortal. Socrates is a human.
The truth value of the statement 'All humans are mortal. Socrates is a human.' is: True
Enter an English statement: (or type 'exit' to quit): exit
Exiting interactive logic mode.
```
This session demonstrates adding Prolog code to `world.pl` and querying its truth value. The `world.pl` file accumulates knowledge without overwriting previous facts and is not tracked in the repository.

The `myprolog.csv` file contains 1000 logical English examples with truth values and corresponding Prolog statements, serving as a test and validation dataset.

## background

One of the promises of logic is that it can give formal grounding for truth.
As LLMs develop more sophisticated responses, we will be more challenged to detect truth.

Via ChatGPT:

    "Logic is the beginning of wisdom, not the end." - Leonard Nimoy

    "Logic will get you from A to B. Imagination will take you everywhere." - Albert Einstein

    "Formal logic is the science of the necessary laws of thought, and, as such, is a fundamental branch of knowledge." - Bertrand Russell

    "Logic is the anatomy of thought." - John Locke

    "Logic is the art of thinking well; the mind, like the body, requires to be trained before it can use its powers in the most advantageous way." - Alfred North Whitehead

    "Logic is the foundation of the certainty we enjoy in our knowledge of the external world." - Gottlob Frege

    "The study of logic should not be limited to the ability to reason well; it should also be concerned with the nature of reason and its limitations." - Immanuel Kant

    "Logic, like whiskey, loses its beneficial effect when taken in too large quantities." - Lord Dunsany

    "Logic is the supreme arbiter; the power that defines and controls all things." - Cicero

    "Logic is the backbone of reason, and reason is the greatest of all virtues." - Francis Bacon



## Installation

To install the logical package and all necessary dependencies, use the following command:

```bash
$ poetry install
```

After installation, create a `.env` file based on the `.env-example` template and set the necessary environment variables, including your `OPENAI_API_KEY`.

## Quick Start

1. Clone the repository using `git clone https://github.com/your-username/logical.git` and navigate to the project directory.
2. Run `poetry install` to install dependencies, including `folpy`.
3. Copy `.env-example` to `.env` and configure your environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key.
   - `OPEN_AI_MODEL_TYPE`: Set to "gpt-4o" or another model type as required.
4. Start an interactive logic session with `logical interactive-logic` to input English statements and receive Prolog queries or truth values interactively.

## Commands

- `help`: Display help information about the available commands.
- `exit`: Exit the interactive logic session safely.
- `parse`: Input text to extract logical statements and convert them into Prolog syntax.
- `ask`: Pose a question to the logic engine and receive a logical answer.
- `validate`: Check the syntax and validity of Prolog code using the Prolog interpreter.

## Debugging

To debug the logic engine and test the generated Prolog code, follow these steps:

1. Load the Prolog file in the SWI-Prolog interpreter to test the logic engine's output:
   ```
   $ swipl
   ?- ['world.pl'].
   ```
2. Run tests to validate the Prolog code by executing:
   ```
   $ poetry run pytest
   ```
3. If you encounter any issues, refer to the error messages and consult the `analyze_invalid_prolog.py` script to identify common error patterns.

## updates

The `parse_logic` function prompts have been refined to guide the OpenAI model more explicitly in avoiding common error patterns in Prolog code generation.

The `run_parser` function has been enhanced to handle a wider range of logical constructs, allowing for more complex English statements to be accurately translated into Prolog syntax.

The `analyze_invalid_prolog.py` script now includes a feature to summarize common error patterns found in invalid Prolog statements.

New error handling mechanisms have been implemented to provide informative messages for common issues such as authentication failures and rate limits when interfacing with the OpenAI API.

The `parse_logic` function now includes additional validation steps to ensure the semantic validity of the Prolog code generated from the OpenAI API responses.

## myprolog.csv

The `myprolog.csv` file is used to store logical English examples with their truth values and corresponding Prolog statements. This file is generated by the `parse` task and is utilized for testing and validation purposes. To generate this file, use the `logical parse` command with your English statements.

## see also

https://github.com/klaudiosinani/awesome-prolog
