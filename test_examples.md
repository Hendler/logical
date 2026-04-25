the sky is red. the sky is blue. a sky can only be one color. the sky is the same color.


% Facts
color(red).
color(blue).

% Predicates
sky_color(Sky, Color) :-
    color(Color),
    Sky = sky.

% Rules
one_color(Sky, Color) :-
    sky_color(Sky, Color),
    \+ (sky_color(Sky, OtherColor), OtherColor \= Color).

same_color(Sky1, Sky2, Color) :-
    one_color(Sky1, Color),
    one_color(Sky2, Color).
