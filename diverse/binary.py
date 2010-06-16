def binary(i):
    """Returns a binary string representation of number.

    Example:
    >>> binary(2)
    '10'
    >>> binary(1337) 
    '10100111001'
    >>> int(binary(1337), 2)
    1337
    """
    if not i: 
        return "" # finished, no more bits
    bit = i & 1   # front bit
    i = i >> 1    # shift away front bit
    if bit:    # bit was set
        return binary(i) + "1"
    else:
        return binary(i) + "0"

def _test():
    import doctest, binary
    doctest.testmod(binary)        

if __name__ == "__main__":
    _test()

