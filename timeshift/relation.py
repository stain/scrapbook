from trans import get_trans
from sets import Set

class Relation:
    """Represents a time relation"""
    # All relations created so far, using shortnames as keys and
    # Relation objects as values. 
    relations = {}
    # The transitivity matrix, indexed by and contains shortnames
    _trans = get_trans()
    def __init__(self, short, long):
        """Creates a new relation"""
        self.short = short
        self.long = long
        # Register in the class
        self.relations[short] = self
    
    def __repr__(self):
        #return "<Relation %s >" % self.short    
        return self.short
    
    def __str__(self):
        return self.long    

    def all(cls):
        """All possible relations created so far (ie. the wildcard)"""
        return Set(cls.relations.values())
    all = classmethod(all)    

    def inverse(self):
        """Returns the inverse of this relation
        if    A r B  
        then  B r.inverse() A
        """
        if self.short == "=":
            return self
        if self.short == "<":
            return self.relations['>']    
        if self.short == ">":
            return self.relations['<']    
        if self.short.isupper():
            return self.relations[self.short.lower()]    
        else:
            return self.relations[self.short.upper()]    
                
    
    def trans(self, relation):
        """Returns the Set of possible relations in transitivity
           Given the relations:
               A r1 B
               B r2 C
           r1.trans(r2) returns possible relations for:
               A r C    
        """
        # Look up short-names in the transitivitiy matrix 
        relations = self._trans[self.short][relation.short]
        if "*" in relations:
            return self.all()
        result = Set()
        for r in relations:
            relation = self.relations[r]
            result.add(relation)        
        return result     

equals = Relation("=", "equals")
before = Relation("<", "is before")
after = Relation(">", "is after")
during = Relation("d", "is during")
contains = Relation("D", "contains")
overlaps = Relation("o", "overlaps")
overlapped_by = Relation("O", "is overlapped by")
meets = Relation("m", "meets")
met_by = Relation("M", "is met by")
starts = Relation("s", "starts")
started_by = Relation("S", "is started by")
finishes = Relation("f", "finishes")
finished_by = Relation("F", "is finished by")

