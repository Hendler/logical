% Prolog representation of logical statements with their truth values

% Define facts for testing
human(socrates).
dog(fido).
car(herbie).

% Discontiguous predicates declaration
:- discontiguous bird/1.
:- discontiguous mammal/1.

% Define birds and their attributes
bird(tweety).
bird(opus).
bird(ostrich).
bird(penguin).

% Penguins are birds that cannot fly
penguin(X) :- bird(X), \+ can_fly(X).

% Birds can fly unless they are of a kind that cannot fly
can_fly(X) :- bird(X), \+ member(X, [penguin, ostrich]).

% Birds generally have wings unless specified otherwise
has_wings(X) :- bird(X), \+ member(X, [ostrich]).

% True statements
mortal(X) :- human(X).
vertebrate(X) :- mammal(X).
has_hair(X) :- mammal(X), not(cetacean(X)). % Whales and dolphins are cetaceans without hair

% False statements
has_fur(X) :- mammal(X), X \= whale.

% Queries for testing false statements
% Query: "No dogs have wings." This should fail as no fact defines dogs with wings.
query_dog_wings :- dog(X), has_wings(X), fail.

% Define even/1 predicate for numbers that are even
even(X) :- 0 is X mod 2.

% Define divisible_by_fourteen/1 predicate as dynamic to allow runtime modifications
:- dynamic divisible_by_fourteen/1.
divisible_by_fourteen(X) :- 0 is X mod 14.

% Define shapes with specific number of sides
hexadecagon(X) :- shape(X), has_sixteen_sides(X).
pentadecagon(X) :- shape(X), has_fifteen_sides(X).
icosikaioktogon(X) :- shape(X), has_eighty_eight_sides(X).
icosikaieihexagon(X) :- shape(X), has_thirty_six_sides(X).

% Define cetaceans and aquatic mammals
cetacean(dolphin).
cetacean(whale).
aquatic_mammal(X) :- cetacean(X).

% Define reptiles and their attributes
reptile(turtle).
reptile(snake).
% Reptiles and birds lay eggs
lays_eggs(X) :- reptile(X); bird(X).
cold_blooded(X) :- reptile(X).

% Define birds and their attributes
has_feathers(X) :- bird(X), X \= penguin(X).

% Define insects and their attributes
insect(bee).
has_six_legs(X) :- insect(X).

% Define amphibians and their attributes
amphibian(frog).
lives_on_land_and_water(X) :- amphibian(X).

% Define arachnids and their attributes
arachnid(spider).
has_eight_legs(X) :- arachnid(X).

% Define mammals and their attributes
:- discontiguous mammal/1.
mammal(whale).
mammal(bear). % Added fact to define bear as a mammal
mammal(kangaroo).
mammal(cow).
mammal(dolphin).
has_mammary_glands(X) :- mammal(X).
has_pouch(X) :- mammal(X), X = kangaroo.

% Define fish and their attributes
fish(goldfish).
lives_in_water(X) :- fish(X).

% Define dinosaurs and their extinction status
dinosaur(tyrannosaurus).
extinct(X) :- dinosaur(X).

% Define odd/1 predicate for numbers that are not even
odd(X) :- not(even(X)).

% Define shapes with specific number of sides
triacontatetragon(X) :- shape(X), has_thirty_four_sides(X).

% Helper predicates for shapes with a specific number of sides
has_sixteen_sides(X) :- shape(X), sides(X, 16).
has_fifteen_sides(X) :- shape(X), sides(X, 15).
has_eighty_eight_sides(X) :- shape(X), sides(X, 88).
has_thirty_six_sides(X) :- shape(X), sides(X, 36).
has_ten_sides(X) :- shape(X), sides(X, 10).
has_fourteen_sides(X) :- shape(X), sides(X, 14).
has_seventeen_sides(X) :- shape(X), sides(X, 17).
has_eighteen_sides(X) :- shape(X), sides(X, 18).
has_nineteen_sides(X) :- shape(X), sides(X, 19).
has_twenty_sides(X) :- shape(X), sides(X, 20).
has_twenty_one_sides(X) :- shape(X), sides(X, 21).
has_twenty_two_sides(X) :- shape(X), sides(X, 22).
has_twenty_three_sides(X) :- shape(X), sides(X, 23).
has_twenty_four_sides(X) :- shape(X), sides(X, 24).
has_twenty_five_sides(X) :- shape(X), sides(X, 25).
has_twenty_six_sides(X) :- shape(X), sides(X, 26).
has_twenty_seven_sides(X) :- shape(X), sides(X, 27).
has_twenty_eight_sides(X) :- shape(X), sides(X, 28).
has_thirty_four_sides(X) :- shape(X), sides(X, 34).

% Helper predicate to define the number of sides for a shape
sides(X, N) :- shape(X), side_count(X, N).

% Define dynamic predicate for side count to allow runtime modifications
:- dynamic side_count/2.

% Define what constitutes a shape
shape(circle).
shape(triangle).
shape(square).
shape(pentagon).
shape(hexagon).
shape(heptagon).
shape(octagon).
shape(nonagon).
shape(decagon).
shape(hendecagon).
shape(dodecagon).
shape(tridecagon).
shape(tetradecagon).
shape(pentadecagon).
shape(hexadecagon).
shape(heptadecagon).
shape(octadecagon).
shape(nonadecagon).
shape(icosagon).
shape(icosikaihenagon).
shape(icosikaidigon).
shape(icosikaitrigon).
shape(icosikaitetragon).
shape(icosikaipentagon).
shape(icosikaihexagon).
shape(icosikaiheptagon).
shape(icosikaioctagon).
shape(triacontatetragon).
shape(rectangle).

% Populate side_count with facts for the number of sides for each shape
side_count(circle, 0).
side_count(triangle, 3).
side_count(square, 4).
side_count(pentagon, 5).
side_count(hexagon, 6).
side_count(heptagon, 7).
side_count(octagon, 8).
side_count(nonagon, 9).
side_count(decagon, 10).
side_count(hendecagon, 11).
side_count(dodecagon, 12).
side_count(tridecagon, 13).
side_count(tetradecagon, 14).
side_count(pentadecagon, 15).
side_count(hexadecagon, 16).
side_count(heptadecagon, 17).
side_count(octadecagon, 18).
side_count(nonadecagon, 19).
side_count(icosagon, 20).
side_count(icosikaihenagon, 21).
side_count(icosikaidigon, 22).
side_count(icosikaitrigon, 23).
side_count(icosikaitetragon, 24).
side_count(icosikaipentagon, 25).
side_count(icosikaihexagon, 26).
side_count(icosikaiheptagon, 27).
side_count(icosikaioctagon, 28).
side_count(triacontatetragon, 34).
side_count(rectangle, 4).

% Define rectangle shape based on having four sides
rectangle(X) :- shape(X), side_count(X, 4).

% Define square shape based on having four sides of equal length
square(X) :- shape(X), side_count(X, 4).
