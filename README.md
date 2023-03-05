# logical

ChatGPT logic engine

## install

    brew install pyenv pyenv-virtualenv git git-crypt gpg docker-compose
    pyenv install 3.11.2
    pyenv virtualenv 3.11.2 logical
    pip install --upgrade pip

Then copy the `.env-example` to `.env`

## usage

    inv dev.run

Commands:

    - help
    - exit
    - parse: input text to extract logic from
    - ask: : ask a logical question


## see also

https://github.com/klaudiosinani/awesome-prolog