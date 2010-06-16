
def map(function, *sequences):
    return [function(*args) for args in izip(sequences)]

def filter(predicate, sequence):   
    """Return all items of sequence of which predicate(item) is true.

    If predicate is None instead of a callable, return items which
    themselves are true. 
    """
    if predicate is None:
        return [x for x in sequence if x]
    return [x for x in sequence if predicate(x)]

# dummy obj for initial
__none = obj()
def reduce(function, sequence, initial=__none):
    if initial is not __none:
        sum = initial       
    seq_iter = iter(sequence)    
    sum = seq_iter.next()
    for elem in seq_iter:
        sum = function(sum, elem)
    return sum
    
