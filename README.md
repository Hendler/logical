# logical

ChatGPT logic engine using [Prolog](https://en.wikipedia.org/wiki/Prolog)

First developed for the [OpenAI emergency hackathon on 3/5/2023](https://twitter.com/nonmayorpete/status/1632456433102098434).

[<img alt="Bertrand Russell"   src="./russell.png" />]



One of the promises of logic is that it can give formal grounding for truth.
As LLMs develop more sophisicated responses, we will be more challenged to detect truth. With logic we can

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


Example phrases to parse

  1.  Men are mortal. Men are human. I am human.


## debug

    $ swipl
    ?- ['myprolog.pl'].

## see also

https://github.com/klaudiosinani/awesome-prolog