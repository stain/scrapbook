flight('Oslo','Frankfurt','SK111',21,3,1800).
flight('Oslo','Frankfurt','LH122',16,2.5,1500).
flight('Oslo','Copenhagen','SK145',6,2,1150).
flight('Oslo','Copenhagen','SK123',14,2,1250).
flight('Copenhagen','Frankfurt','SK455',15,1.5,1150).
flight('Copenhagen','NewYork','SK945',20,6,3050).
flight('Frankfurt','London','BA555',8,3,2050).
flight('Frankfurt','NewYork','LH333',19,5,2850).
flight('London','NewYork','BA156',10,4.5,2250).
airportclosed('Fran', 22,22).

airportopen(Airport, Start, End) :-
% over 24h, test to ganger.
   End < Start, !, airportopen(Airport, Start, 24), airportopen(Airport, 0, End).

airportopen(Airport, Comes, Leaves) :-
   airportclosed(Airport, Closes, Opens), Comes =< Opens, Leaves >= Closes, !, fail.
airportopen(_,_,_).

enough_time(Lands, TakeOff) :- TakeOff >= Lands + 1.
enough_time(Lands, TakeOff) :-
  TakeOff < Lands,
  NewTakeOff is TakeOff+24,
  enough_time(Lands, NewTakeOff).

connection(From,To,Dep,Price,Dur,[Flightnr],[From,To]) :-
   flight(From,To,Flightnr,Dep,Dur,Price),
   airportopen(From, Dep, Dep),
   airportopen(To, Dep+Dur, Dep+Dur).

connection(From,To,Dep,Price,Dur,[Flight|Flights],[From|Airports]) :-
   flight(From,Transit,Flight,Dep,Dur1,Price1),
   connection(Transit,To,Dep2,Price2,Dur2,Flights,Airports),
   airportopen(From, Dep, Dep),
   Must_start is Dep + Dur1,
   airportopen(Transit, Must_start, Dep2),
   enough_time(Must_start, Dep2),
   Dur is Dur1+Dur2,
   Price is Price1+Price2.

plus(X,Y,Z) :- Z is X+Y.

