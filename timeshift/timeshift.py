from Queue import Queue
import relation
from sets import Set

# Generate True/False symbols for old pythons
(True,False) = (1==1, 0==1)

def ispropersubset(setA, setB):
    """Checks if setA is a proper subset of setB. 
       A proper subset is a subset that isn't equal."""
    return setA.issubset(setB) and not setA == setB

class Event:
    """Representation of an event"""
    events = {}
    def __init__(self, short, long):
        self.short = short
        self.long = long
        self.events[short] = self
    def __repr__(self):
#        return "<Event %s>" % self.short     
        return self.short

class RelationNet(dict):
    """2d network of sets of Relations. 
       Returns default values for unknown positions (i,j):
            if i==j returns relation.equals
            if (j,i) is known, return (and store) the inverses of those
            relations
            else return all possible relations (wildcard)"""    
    def __getitem__(self, key):
        try:
            return super(RelationNet, self).__getitem__(key)
        except KeyError:
            (i,j) = key
            if i==j:
                return Set((relation.equals,))
            elif self.has_key((j,i)):
                # Ok, but it has to be the inverses
                inverses = self[j,i]
                inverses = Set([r.inverse() for r in inverses])
                # learn that 
                self[key] = inverses
                return inverses
            else:    
                # Return "ALL" instead
                return relation.Relation.all()
            
class TimeNet:
    """Collection of event nodes and relations between them"""
    def __init__(self):
        self.net = RelationNet()
        self.rnet = RelationNet()
        self.nodes = []
        
    def addnode(self, node):
        """Adds an Event node to the network. Events could have
        relations between them added with addrelation"""
        if not node in self.nodes:
            self.nodes.append(node)
        # Extend the network if needed
        # Since we use a dictionary with default values, this is not
        # needed. 
    
    def addrelation(self, rel, i, j):
        """Adds a new Relation rel from event i to j.
        The events doesn't have to be present in the network already, 
        they will be added if needed."""
        todo = Queue()
        todo.put((i, j))
        # Store as a set for future set operations
        self.rnet[i,j] = Set((rel,))
         
        # Make sure these are known nodes
        self.addnode(i)
        self.addnode(j)
        while not todo.empty():
            pair = todo.get()
            (i,j) = pair
            # transfer relations to the real net
            self.net[i,j] = self.rnet[i,j]
            # Check if any k of all nodes have something to say
            # about R(k,j)
            for k in self.nodes:
                if self.comparable(k, j):
                    constraints = self.constraints(self.net[k,i], self.rnet[i,j])
                    # limit the possibible relations for k,j
                    self.rnet[k,j] = self.net[k,j].intersection(constraints)
                    if ispropersubset(self.rnet[k,j], self.net[k,j]):
                        todo.put((k, j))
            # and vice versa for R(i,k)           
            for k in self.nodes:
                if self.comparable(i, k):
                    constraints = self.constraints(self.net[i,j], self.rnet[j,k])
                    # limit the possibible relations for k,j
                    self.rnet[i,k] = self.net[i,k].intersection(constraints)
                    if ispropersubset(self.rnet[i,k], self.net[k,i]):
                        todo.put((i, k))

    def constraints(self, R1, R2):
        """Find all possible relations in transitivitiy between the
           relations in R1 and R2"""
        c = Set();
        for r1 in R1:
            for r2 in R2:
                transes = r1.trans(r2)
                c = c.union(transes)
        return c

    def comparable(self, i, j):
        """Restricts the search by limiting which nodes to check"""
        # Not yet implemented :=) Search everything, we've got time
        return True
    
    def print_knowledge(self):
        """Prints all that is "known" for sure, ie. events that have
           only one possible relation."""
        solutions = []
        for ((a,b),relations) in self.net.items():    
            if len(relations) == 1:
                rel = tuple(relations)[0]
                # We know for sure that
                solutions.append((a.long, b.long, rel))
        solutions.sort()          
        for (a,b,rel) in solutions:
            print a, rel, b
                

