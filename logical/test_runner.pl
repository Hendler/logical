% Load the CSV file and parse each Prolog statement
:- use_module(library(csv)).

% Define the path to the CSV file containing the Prolog statements
prolog_storage_name('myprolog.csv').

% Load Prolog statements from the CSV file
load_prolog_statements(Statements) :-
    prolog_storage_name(FileName),
    csv_read_file(FileName, Rows, [functor(logical_row), arity(3)]),
    findall(Statement, member(logical_row(_, Statement, _), Rows), Statements).

% Run each Prolog statement and validate its truth value
run_tests :-
    load_prolog_statements(Statements),
    maplist(run_test, Statements).

% Helper predicate to run a single Prolog test
run_test(Statement) :-
    term_string(Term, Statement),
    (   call(Term)
    ->  format('Test passed: ~w~n', [Statement])
    ;   format('Test failed: ~w~n', [Statement])
    ).

% Entry point for the test runner
:- initialization(run_tests, main).
