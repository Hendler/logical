# logical

ChatGPT logic engine

## install

    brew install pyenv pyenv-virtualenv git
    brew install swi-prolog --HEAD
    pyenv install 3.11.2
    pyenv virtualenv 3.11.2 logical
    pip install --upgrade pip
    chmod +x main.pl

Then copy the `.env-example` to `.env`

## usage

    inv dev.run

Commands:

    - help
    - exit
    - parse: input text to extract logic from
    - ask: : ask a logical question


## debug

    $ swipl
    ?- ['myprolog.pl'].

## see also

https://github.com/klaudiosinani/awesome-prolog