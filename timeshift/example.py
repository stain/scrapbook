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

# Check one particular knowledge
print E4, net.net[E4,E1], E1

# Print all 'known' knowledge
net.print_knowledge()


