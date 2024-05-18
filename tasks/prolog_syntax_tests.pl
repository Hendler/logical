% Correct syntax
parent(john, doe).
sibling(X, Y) :- parent(Z, X), parent(Z, Y).

% Unbalanced parentheses
parent(john, doe).
sibling(X, Y :- parent(Z, X), parent(Z, Y).

% Missing period at the end of a statement
parent(john, doe)
sibling(X, Y) :- parent(Z, X), parent(Z, Y).

% Incorrectly capitalized variables
Parent(john, doe).
sibling(x, Y) :- parent(Z, x), parent(Z, Y).

% Unbalanced single quotes in string literals
likes(john, 'Soccer).
hates('Alice, basketball).

% Missing or incorrect usage of operators
likes(john, soccer) sibling(X, Y) :- parent(Z, X), parent(Z, Y).

% Directives should start with :- followed by an uppercase letter or underscore
:- dynamic 'cow'/1.

% Facts should not contain variables and rules should have a head and a body
animal(X) :- mammal(X), 'lives on land'.

% Incorrect use of quantifiers
forall X in humans, mortal(X).

% Unbalanced nested parentheses
ancestor(X, Y) :- (parent(X, Z) (parent(Z, Y))).

% Multi-line comments using correct Prolog syntax
/* This is a comment that
spans multiple lines */
parent(jane, doe).
