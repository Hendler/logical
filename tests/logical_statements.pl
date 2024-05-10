% Prolog representation of logical statements with their truth values

% Define facts for testing
human(socrates).
bird(tweety).
penguin(opus).
dog(fido).
mammal(whale).
mammal(bear). % Added fact to define bear as a mammal
car(herbie).
has_wings(opus). % Adding this fact to define has_wings for opus

% True statements
mortal(X) :- human(X).
has_hair(X) :- mammal(X), X \= whale. % Modified rule to correctly exclude whales from having hair

% False statements
has_fur(X) :- mammal(X), X \= whale.

% True and False statements for can_fly
can_fly(X) :- bird(X), not(penguin(X)).
can_fly(X) :- car(X), has_wings(X).

% Queries for testing false statements
% Query: "No dogs have wings." This should fail as no fact defines dogs with wings.
query_dog_wings :- dog(X), has_wings(X), fail.

% Define even/1 predicate
even(X) :- 0 is X mod 2.

% Define divisible_by_fourteen/1 predicate as dynamic to allow runtime modifications
:- dynamic divisible_by_fourteen/1.
divisible_by_fourteen(X) :- 0 is X mod 14.
