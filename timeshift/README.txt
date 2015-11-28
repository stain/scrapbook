Timeshift
=========

:Authors: Stian Søiland <stian@soiland.no>,
          Marianne Lund Jacobsen <mariaj@stud.ntnu.no>
:Date:    2004-10-23

Requirements
============
This project requires Python 2.2. The module sets.py from Python 2.3 is
included.

Usage
=====

1) Create a seperate Python module creating the events and 
   a TimeNet to store the time relations between them:

    example.py::

        #!/usr/bin/env python

        from timeshift import *
        import relation

        E1 = Event("E1", "Mary went to the airport")
        E2 = Event("E2", "Peter bought a car")
        E3 = Event("E3", "Peter drove Mary to the airport")
        E4 = Event("E4", "Mary flew from Trondheim to Oslo")

        net = TimeNet()
        net.addrelation(relation.before, E1, E4) # went before flew
        net.addrelation(relation.before, E2, E3) # bought before drove
        net.addrelation(relation.equals, E1, E3) # drove and went at same time
        
        # Check one particular relation, what about her flight
        # and Peters car purchase?
        print E4, net.net[E4,E1], E1

        # Print all 'known' knowledge
        net.print_knowledge()

2) Run the module and examine the results::

        : stain@ozelot ~/timeshift;python example.py
        E4 Set([>]) E1
        Mary flew from Trondheim to Oslo is after Mary went to the airport
        Mary flew from Trondheim to Oslo is after Peter bought a car
        Mary flew from Trondheim to Oslo is after Peter drove Mary to the airport
        Mary went to the airport is before Mary flew from Trondheim to Oslo
        Mary went to the airport is after Peter bought a car
        Mary went to the airport equals Peter drove Mary to the airport
        Peter bought a car is before Mary flew from Trondheim to Oslo
        Peter bought a car is before Mary went to the airport
        Peter bought a car is before Peter drove Mary to the airport
        Peter drove Mary to the airport is before Mary flew from Trondheim to Oslo
        Peter drove Mary to the airport equals Mary went to the airport
        Peter drove Mary to the airport is after Peter bought a car

   The first outputted line shows that the only possible relation
   between E4 and E1 is > - meaning that E4 is after E1, Mary's flight
   was after Peter's car purchase

   The other output is all the knowledge that the system knows 'for
   sure'. Such knowledge is relations between nodes where there is only
   one possible relation.  Note that this includes the basic facts
   initially added and their inverse values.  (Ie both "E1 before E4"
   and "E4 after E1").

   Relations between other nodes (events) are not printed, as there
   is only partly or no knowledge on what relations might exist.
   In more advanced examples, this could be relations such that 
   'E1 is before, finishes, during or meeting E2'.


Included files
==============

These are the files included:

============  ========================================================
Filename      Description
============  ========================================================
sets.py       Basic sets operations from Python 2.3, included for 
              compatibility

trans.txt     transitivity matrix from [Allen]_, fig.4

trans.py      Simple parser for trans.txt

relation.py   Representation of relations such as 'before' and 'after.
              All time relations from [Allen]_, fig.2 are defined, including their
              inversion and possible transitions from trans.py
            
timeshift.py  Main engine for creating a net of events and their 
              relations. 

              Implements Constraints(R1,R2) and Add R(i,j) from [Allen]_.
              
              Includes a method print_knowledge for printing 'everything
              known for sure'.

example.py    Simple example from [it3706]_

trening.py    A slightly more complicated example representing the
              events during a training session for a person attending
              dance classes.
  
skole.py      A complex example representing a person starting his
              student career at the university.

skole.vsd     A graphical representation of the relations given
              in skole.py, format: Microsoft Visio

skole.svg     Exported version of skole.vsd, SVG (Vector graphics)

skole.png     Exported version of skole.vsd, PNG (Raster graphics)

skole.txt     Results of running skole.py, ie. all 'for sure'
              knowledge produced by timeshift.
============  ========================================================


Note
====

There is a (intended?) bug in the Add-algorithm in [Allen]_. Allen's first
for-loop finds new transitivity information for N(k,j), but then checks
R(k,i) for new information instead of R(k,j). The fix is to replace
(k,i) with (k,j) in the if-test::

    if R(k,j) ispropersubset N(k,j)
        then add <k,j> to ToDo;


References
==========

.. [Allen] James F. Allen, Maintaining Knowledge about Temporal Intervals
       Communications of the ACM, nov 1983, vol. 26, num 11

.. [it3706] Project descriptions for IT3706 Knowledge representation
       IDI, NTNU, 2004.
       http://www.idi.ntnu.no/emner/it3706/assignment/project.html      
