# logical

ChatGPT logic engine using [Prolog](https://en.wikipedia.org/wiki/Prolog).

First developed at the [OpenAI emergency hackathon on 3/5/2023](https://twitter.com/nonmayorpete/status/1632456433102098434).

<img alt="Bertrand Russell" src="./russell.png" />

## Usage

To set up and use this logic engine, follow these steps:

1. Set up the environment variables in a `.env` file. Use the provided `.env-example` as a template.
2. Ensure the `OPENAI_API_KEY` is set to your actual OpenAI API key.
3. Configure the `OPEN_AI_MODEL_TYPE` environment variable to specify the desired model, such as "gpt-4o".

The `ASSISTANT_PARSING_PROMPT` has been updated with detailed examples to facilitate the conversion of English statements into Prolog syntax. The logic engine can process any English logical statements, using OpenAI to generate the corresponding Prolog code. The generated code is then parsed to ensure both syntactical and semantical correctness before execution.

Example usage:
```
$ inv logic.run
$ parse
$ Men are mortal. Men are human. I am human.
$ ask
$ Am I mortal?
```

To run tests and verify the correctness of the Prolog statements generated, use the following command:
```
$ pytest
```

The `analyze_invalid_prolog.py` script now includes a dynamic file naming feature, which appends a timestamp to the output file name to ensure uniqueness. This script summarizes common error patterns found in invalid Prolog statements and helps in identifying areas for improvement in the logic engine.

Logging of OpenAI API requests and responses is done through `openai_requests.log`, which can be found in the project's root directory. This log file is useful for auditing and debugging purposes.

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



## install

To install the necessary dependencies for this project on a Linux system, follow the steps below:

```
sudo apt update
sudo apt install python3.11 python3-pip swi-prolog -y
python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt
chmod +x main.pl
```

Note: Python 3.11 is currently a release candidate. For a more stable version, you may consider using Python 3.10.

Then copy the `.env-example` to `.env` and configure the necessary environment variables as described in the usage section.

## Commands:

    - help
    - exit
    - parse: input text to extract logic from
    - ask: ask a logical question


## debug

To debug the logic engine and test the generated Prolog code, you can load the Prolog file in the SWI-Prolog interpreter:

```
$ swipl
?- ['myprolog.pl'].
```

This will allow you to interact with the Prolog code and verify its correctness.

## updates

The `parse_logic` function prompts have been refined to guide the OpenAI model more explicitly in avoiding common error patterns in Prolog code generation, such as incorrect implications, conditionals without proper predicates, and ensuring proper use of quantifiers.

The `run_parser` function has been enhanced to handle a wider range of logical constructs, including conjunctions, disjunctions, implications, biconditionals, and quantifications. This allows for more complex English statements to be accurately translated into Prolog syntax.

The `analyze_invalid_prolog.py` script now includes a feature to summarize common error patterns found in invalid Prolog statements, such as implication errors, conditional errors, predicate errors, quantifier errors, and chained predicate errors. This helps in identifying and addressing the types of errors that are occurring during the Prolog generation process.

Additionally, new error handling mechanisms have been implemented to provide informative messages for common issues such as authentication failures and rate limits when interfacing with the OpenAI API. This ensures a smoother experience during both testing and production use.

The `parse_logic` function now includes additional validation steps to ensure the semantic validity of the Prolog code generated from the OpenAI API responses. This helps in maintaining the integrity of the logic engine's output and ensures that the generated Prolog code is not only syntactically correct but also semantically meaningful.

## see also

https://github.com/klaudiosinani/awesome-prolog
