

from timeshift import *
import relation

A = Event("A", "Søker om studieplass")
B = Event("B", "Får studieplass")
C = Event("C", "Studentrabatt på bussen") 
D = Event("D", "Får semesterkort")
E = Event("E", "Melde til eksamen")
F = Event("F", "Betale semesteravgift")
G = Event("G", "Søke om studielån")
H = Event("H", "Hente studielån")
I = Event("I", "Kjøpe bøker")
J = Event("J", "Studerer")
K = Event("K", "Finne hybel")
L = Event("L", "Flytte")
M = Event("M", "Prosjekt")
N = Event("N", "Eksamen")


net = TimeNet()


net.addrelation(relation.before, A, B)
net.addrelation(relation.before, B, F)
net.addrelation(relation.meets, F, E)
net.addrelation(relation.before, E, D)
net.addrelation(relation.after, C, D)
net.addrelation(relation.before, G, H)
net.addrelation(relation.before, F, H)
net.addrelation(relation.before, H, I)
net.addrelation(relation.during, I, J)
net.addrelation(relation.contains, J, M)
net.addrelation(relation.after, J, L)
net.addrelation(relation.before, K, L)
net.addrelation(relation.before, M, N)
net.addrelation(relation.finishes, N, J)

net.print_knowledge()

