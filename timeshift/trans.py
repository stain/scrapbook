from sets import Set

def get_trans(filename="trans.txt"):
    """Reads the transitivity matrix from the text file
       The tab seperated content is parsed into a 2d dictionary
       containing sets of letters (shortnames for relations).
    """
    headers = open(filename).readline()
    headers = headers.split()
    trans = {}
    for line in open("trans.txt"):
        transes = line.split()
        relation = transes[0]
        r1 = transes[0]
        row = {}
        trans[r1] = row
        for (r2, t) in zip(headers, transes):
            row[r2] = Set(t)
    return trans            

         
