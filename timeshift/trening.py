#!/usr/bin/env python

from timeshift import *
import relation

A = Event("A", "Trening")
B = Event("B", "Oppvarming")
C = Event("C", "Uttøying")
D = Event("D", "Dansing")
E = Event("E", "Skifte til treningstøy")
F = Event("F", "Dusjer")

net = TimeNet()
net.addrelation(relation.starts, B, A) 
net.addrelation(relation.finishes, C, A)
net.addrelation(relation.met_by, A, E)
net.addrelation(relation.after, D, B)
net.addrelation(relation.before, D, C)
net.addrelation(relation.meets, A, F)
net.print_knowledge()
