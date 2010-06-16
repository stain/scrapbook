#!/usr/bin/env python
"""
A huffman encoder/decoder written in Python. Extremely slow, scales up
to about 16kB input text before runtimes hit the roof.  """

import warnings,struct,compiler

VALUE=0
WEIGHT=1
CHARS=2

# the dict is stored as char-unsignedShort
# we'll need to use little-endian to get \001 or more in
# the first byte, so that we may use \000 to end the
# dictionary with a single byte
DICTFMT = '<Hc'
DICTFMTSIZE = struct.calcsize(DICTFMT)

## Data structures:
## A node in a huffman tree:
##   (value, freq, chars)
##   chars are the characters in this node or it's children
##   freq is the total frequency of these chars
##   value is either None (if len(chars) == 1) or a 
##         tupple (left, right), where left and right
##         both are a node of this definition.
## 
## Example:
##   ((  
##     (None, 6, "a"),     # left, single char
##     ((                 # right, subtree
##        (None, 3, "b"),  # right-left, single char 
##        (None, 2, "g")),   # right-right, single char
##      5, "bg"),)        # freq/chars of right  
##   11, "abg") # freq/chars of the hole tree   
##
## This tree is stored within the generated output as
## pairs of char-weight, so that it may be regenerated.
## This is probably not the most space efficient way to 
## store the tree, and it has a weird limit, there can't
## be more than 65535 instances of a given letter in the
## data to be encoded - since this number is stored as an 
## unsigned short.
        

def freqSort(charFreq):
    """Sorts a charFreq list according to their frequency"""
    charFreq.sort(lambda a,b: cmp(a[1], b[1]))

def freqAnalysis(input):
    """Analyzes input, returns list of characters present
       in string among with it's frequency, To be compatible
       with nodes in the huffmantree, a first column is added, 
       so the result is a list of tuples (None, freq, char)"""
    freqs = {}
    for char in input:
        count = freqs.get(char, 0)
        freqs[char] = count + 1
    # Ok, but to be nice to generateTree, include a third position
    # with the symbol itself
    charFreqs = [(None,freq,char) for (char,freq) in freqs.items() ]
    return charFreqs

def merge(node1, node2):
    """Merges node1 and node2 to a common node"""
    weight = node1[WEIGHT] + node2[WEIGHT]
    chars = node1[CHARS] + node2[CHARS]
    # left/right
    value = (node1, node2)
    return (value, weight, chars)

def generateTree(tree):
    """Rearranges tree inplace (ie. destructive) so that it is a nice
       huffman tree. Input should be from freqAnalysis()"""
    while len(tree) <> 1:
        freqSort(tree)
        # Select the two with smallest frequency
        (min1, min2) = tree[:2]
        # merge them..
        merged = merge(min1, min2)
        # and replace min1, min2 in list
        del tree[:2]
        tree.append(merged)
    return tree[0]           


def freqs2bin(freqs):
    """Returns the binary version of freqs"""
    bin = ""
    for (_,freq,char) in freqs:
        # This is nice, maximum 64k for freq.. hihi
        bin += struct.pack(DICTFMT, freq, char) 
    # note that by having freq first, and since freq can't 
    # be 0, we can use a single \0 as end-of-dict.
    bin += '\0' # end-of-dict    
    return bin
    
def bin2freqs(binary):
    """Returns the python version of the freqlist binary, among with the
       rest of the string binary"""
    freqs = []
    while binary and binary[0] <> '\0':
        packed = binary[:DICTFMTSIZE]
        binary = binary[DICTFMTSIZE:]
        (freq, char) = struct.unpack(DICTFMT, packed)
        freqs.append((None, freq, char))
    return freqs, binary[1:] # skip the \0       

def huffman(char, tree):
    if tree[CHARS] == char:
        return ""
    if not char in tree[CHARS]:
        raise "Can't encode unknown char %s, regenerate tree" % char
    # ok, this is not a leave, search the appropriate subtree
    for subtree, side in zip(tree[VALUE], "01"):
        if char in subtree[CHARS]:
            return side + huffman(char, subtree)
    # It SHOULD SHOULD SHOULD have returned        
    raise "Reality error, corrupted tree, etc."      

def decodeWithTree(input, tree):
    result = ""
    subtree = tree
    bits = bindec(input)
    for side in bits:
        # Choose side
        side = int(side)
        subtree = subtree[VALUE][side]
        if len(subtree[CHARS]) == 1:
            result += subtree[CHARS][0]
            subtree = tree # start from top again
    return result            

def decode(input):
    charFreqs, binary = bin2freqs(input)
    tree = generateTree(charFreqs)
    return decodeWithTree(binary, tree)

def encode(input):
    """Compresses the inputstring by using huffman encoding, 
       returns a string which includes the dictionary and
       the compressed string"""
    charFreqs = freqAnalysis(input)
    dict = freqs2bin(charFreqs)
    tree = generateTree(charFreqs)
    encoded = ""
    for char in input:
        code = huffman(char, tree)
        encoded += code
    binary = binenc(encoded)    
    return dict + binary

## Both binenc and bindec could be implemented in different ways. 
## One suggestion is to use struct.unpack and pack for the
## binary-integer convertion, one to use a dictionary to loopup
## patterns (each way or just one of the ways), etc. etc.

def binenc(bitstring):
    """Converts a bitstring like '1010110101010' to a binary string"""
    # pad at the END with 0-s
    padding = 8 - (len(bitstring) % 8)
    bitstring += '0' * padding
    # Store the padding, so we can remove it afterwards
    binary = struct.pack("B", padding)
    while bitstring:
        number = bitstring[:8]
        number = int(number, 2)
        binary += chr(number)
        bitstring = bitstring[8:]
    return binary      

def bindec(binary):
    """Converts a binary string to a bitstring like '10101010010101'"""
    bitstring = ""
    # first char is the padding
    (padding,) = struct.unpack("B", binary[0])
    binary = binary[1:]
    for char in binary:
        number = ord(char)
        # oh noooooooooo, what is this? 
        # dirty 'high level'-code to do low level stuff!
        for bit in 128,64,32,16,8,4,2,1:
            bitstring += number & bit and '1' or '0'
    if padding:
        # Remove the padding
        bitstring = bitstring[:-padding]
    return bitstring            

if __name__ == "__main__":
    # Here's /store/bin/hello encoded
    data = '_\x00\n\x02\x00!\xef\x01 \x05\x00#8\x00"\x04\x00%'
    data += '\x02\x00$\x1f\x00\'*\x00)*\x00(\x01\x00+ \x00-'
    data += '\x11\x00,\x03\x00/$\x00.\x01\x001\n\x000\x02\x003'
    data += '\x05\x002\x02\x005\x01\x004\x1c\x00:"\x00=\x02\x00<'
    data += '\x01\x00?\x02\x00>\x07\x00A\x02\x00@\x07\x00C\x08\x00E'
    data += '\x01\x00D\x0b\x00G\x08\x00I\x04\x00H\x06\x00M\x05\x00L'
    data += '\x0b\x00O\x04\x00N\r\x00P\x0b\x00S\x15\x00R\x01\x00U'
    data += '\x03\x00T\n\x00W\x02\x00V\x02\x00Y\x06\x00[\x06\x00]'
    data += '\x01\x00\\\x0c\x00_L\x00a\x18\x00c\x02\x00b\x8e\x00e'
    data += 'E\x00d\x1a\x00g$\x00fA\x00i$\x00h\x01\x00j'
    data += '\x14\x00m4\x00lz\x00oF\x00n0\x00pZ\x00s'
    data += 'w\x00r\r\x00u_\x00t&\x00w\x10\x00v\x0e\x00y'
    data += '\x05\x00x\x01\x00z\x00\x01\xc0\xfa}\x8f\xf3C\xb1\xc0\xc7\xa6'
    data += '\xc74\n\xef\xfb\xdb\n\x9c\x00\x00\x10\xe8\xb0\xcd\xb6_\xad\n'
    data += '\x86tN\x14\xf7\xf9\xb2~\xf8\x9bH~\x8b\xb8\x97\xb1\xbe\x1e'
    data += '+\xc5s\xf1\x93\xb7\xd3\xde\x8e\xd9\x1f\xeb\xd2,\x03\xae\xdc\xf4'
    data += "\x80\xe8\x17\xddD>\xe0'\x15\x83\x83\x8a3\x04\xdf3\x06\x00"
    data += '\xe7\x15\xc5\x9f\xc4\xd3S\x17\xf2\x91\x91v}qu;s/'
    data += 'l\x96\xb3\xfd(1f\xa1&\x86\xed\xb3@5\x90\xb1\x9e\xdc'
    data += '\xffj\xaeq\\]\xf5\xd7\xc5\x97\xa7\xb9\xd7\xfe*ob\xcb'
    data += '\xd9\xbd\xc0\x00\x1c\xe1\xf0\xeeC\xd4oH\x96\x18=\xfd\xdeu'
    data += '\x07_\xba\x82Z\x83\xeez[\xf7\x9c\xe4\x08i\x8fl\xd7h'
    data += '\xdd\x080j\xc0\x00\xe0N\xd7\xac\x0b\x8c\xd7d\xdb\xe9B\r'
    data += '\xbe\x9e\xf4v\xc8\xff^\x91`\x1dv\xe7\xa4\x07@\xbe\xea!'
    data += '\xf7\x018\xac\x1c\x1cQ\x98&\xf9\x980\x009\xeb\x8fkg'
    data += '\x18G\x9a\x10\x03\x9d\x1f\xdf\xfc_\\{[8\xc2<\xd0\x96'
    data += '\xaa\xde\xfd\xb2\xa8\x1a\xfa\x9a_\x0c\xe7\xaf\xddUq\xf6\x17\xcf'
    data += '\x83\xe8\xcb\x93\xb0\xf1;\xf7\xff\x17{\xeb\\=y\xfa\xe3\xda'
    data += '\xd9\xc6\x11\xe6\x86\x10\x03/\xfc_\\{[8\xc2<\xd0\x82'
    data += '\xc9\xfb\xe2\x079\xe3\xeb\xebN!\x0c\x7f\xf1@\x00\x04\xfd}'
    data += 'i\x19\xdcgSN\x9e\x9e\xdb\xb6\x90\xc4\x00\x07\x163[\xe5'
    data += '\xe4z\x1f\xbe^Y\xea~\xae\x0bi\x0ca\x0c<\xbf\xf1T'
    data += '\x00\x01\xad\x0f\xd3\xdf\xb3\xa7\xb6Ki\x0c[O\xdb\x1e\xd9/'
    data += '\xb3\x85\x9a!o\xf7\xe4\xd4\x00\x03\x8a\xba\x9f\xab\xaa\xd2\x18\xc3'
    data += 'i\x0cx\xb1\x9a\xd1.\xdf\xb3\x9e\xa7\xea\xf2\xff\xc5P\x00\x18'
    data += '\xcb\xb7\xec\xe9\xed\x92\xdaC\x1a\x93Y\xa9\x0f\xd6D4\xfaz'
    data += '7\xa6\xbe\xbff/I\x0cg\xd40\x00\x1cU\xbb\x0b\xf1\xf5'
    data += '\xdc\xf5?WU\xa41\xc9\xc0\xa1%@\xb2=zO\xc7\xd7'
    data += 'x\xabz\x86B\xc8\xeas\xc9\xc0\xb5\xfc}\xda\xfe\xbe\xfe\x9f'
    data += '\x8a\xba\x9f\xab\xaa\xd2\x18\xb0\xa1\x87V\xc5#\xd3;\xe4\xe0\\'
    data += 'K\t\xd5\xcf\x17\xf4\xbf\x1f\x17\xa0}m\x13\xf6_\xcf\x7f~'
    data += '\xbe\xbf\xbd\xb0\xa8\xf8(\xce\x01\xe2\xc6kF\xf4\x89a\t\xbe'
    data += '\xa7=O\xd5\xe5\xff\x8a\xb4\x9bq\x08b\xc2\x86\x1f\x15k!'
    data += '|Yq\xbf\x8e\xc8\xa7\xa3\xa9\xfa\xba\xad!\x8f\xfe*\xad&'
    data += '\xdcB\x18\xb0:\x14oH\x96\x1a\xbcXG\xf19\xe7\xe2\xcb'
    data += '\x8d\xfcvF\xaf\x8a\xd9\x1c\xf2\x82\xf8\xb2\xe3\x7f\x1d\x91\xab\xf3'
    data += '}\xe4s\xcb,\xb8\xab\xa9\xfa\xba\xad!\x8b\x0bI\xb7\x10\x86'
    data += '<X\xcdi~w\x7f\xce\xe7\xa9\xfa\xbc\xbf\xf1Wq=:'
    data += '\xea~\xae\xabHc\x07\x9c\x8c\xd6\xd9?o\x9e_\xf8\xbb\x89'
    data += '\xe9\xd4\x00\x01\xa6\xc3\xb3H\xccSl\xfd\xf18\x84?E\x0b'
    data += 'Q\xb3N~2M\x9a\xe76Fg\xba{d\xbf\x9a\x91m'
    data += "?ln\xd6'\x9aG\xef\xd6\xc9\xfb\xe2p\xce\xb5\x7fsW"
    data += '9\x80\xf5\x7fs\xfd6i\xf3\xedz\xfaF\xbbF\xed\xbfC'
    data += '\xe7\xf3\x1am\xed\x84l\x9az8\xa6X\xa9\x86Y?n\xaa'
    data += '\xaa\xb8\x08\xfa\xdf\xeb\xfe\xe9\xed\x87\xd3d\xfd\xbb\x86u\xab\xfb'
    data += '\x9e)\x82\xa9\x86\x0c\x85\x91\xd4\xaa\xab\x8eB\xc8\xea^\xd9)'
    data += '\x0cdOOiV\xf6\xc9m!\x8e\xb8\xa6cT\xc3\x04\xbb'
    data += '~\xca\xaa\xae2\xed\xfb/l\x96\xd2\x18\xeb\x8ag\x85L0'
    data += 'oH\x96\x13<_R\xae;\xd2%\x84\xfe\x9a^\xd9/\x8b'
    data += '\xe8\xf4\xf7\xc0\x00\t\xb1\xce\x044\xc7\xb6k\xb4n\x82\x84\xed'
    data += 'z\xc0\xb8\xcdvM\xbe\x94\x17\xd7\x1e\xd6\xce0\x8f6\\\xe4'
    data += 'f\xb7\r\xcfL\xf2\xff\xc5\xe8\xfe\xff\xe2\xaee\xbfu\x05\xb8'
    data += '\xfb\xd6L/\xb9\xe9o\xda\xbd\xcfK~\xe7\xaf\xddUq\xf6'
    data += '\x17\xcf\x03\xff\xfa \xbcUUUUUUUT\x16\x0e?'
    data += '\x00\x83\xc5UUUUUUU|\xe0\xb2~\xdc\x10P\x0c'
    data += '\x85\x91\xd4\x82\x0b\xc5UUUUUUUP\tv\xfd\x90'
    data += 'A@7\xa4K\t\x9e/\xa9\x07\xa3.,\xec<N\xfd}'
    data += '\xcfK~\xd5\xb3=-\xfah"C\xff\x8a\xb6O\xdb\xe7\x97'
    data += '\x15u\xfb\xaa\xa7`~\xe7\x8a\xcb\x9c^-\xa41\xd3\x0b\xe7'
    data += '\xf4qO^w\x1fz\xcb\xff\x15k!m!\x8az7\x1f'
    data += 'z\xff\xc5U\xb4\x86:\xaa\xfb\xef4\x8ex\x841\xce\xd2\x18'
    data += '\xe5\x97\x16~\xd4\xff\xe2\xae\x05\xf5\x19\xd4\xd3\xafl\x963]'
    data += '\xff>\xeb\x86u\xab\xfb\x9e*\xdaC\x1dU}\xf7\x9aG<'
    data += 'B\x18\xe6\x19\xb6~\xf8\x83\xcb.*\xdaC\x1dU}\xf7\x9a'
    data += 'G<B\x18\xe6\x1e!\x0f\xd1\x0f,\xb9\xce-d.e\xbf'
    data += 'NT\x82\xdc}\xfea\x9aw$\xf4K~\xeb\xff\x15O^'
    data += 'e\xbfNT\x86\x10\xcc\xb04\x85-\xfar\xa3\x0c(f\x19'
    data += 'd\xfd\xb8y\x7f\xe2\xaa\xd9?o\x9e\\U]~\xea\xa9\xd8'
    data += '\x1f\xb9\xe5\xc5Y\xf8\xf5\xe6[\xf4\xe5Ha\x0c\xc1\r!K'
    data += '~\x9c\xa9\x0c!\x98`\xc8Y\x1dHy\x7f\xe2\xaa\xdaC\x1d'
    data += 'T2\x16GS\x9e\\U\x9f\x8f^e\xbfNT\x86\x10\xcc'
    data += '\xc6\x1aB\x96\xfd9R\x18C0\xc1.\xdf\xb2\x1e_\xf8\xaa'
    data += '\xb5\x90\xb6\x90\xc5=\x1bHc\xaf\xfcUU\xb4\x865\tv'
    data += '\xfd\x9c\xf2\xe2\xac\xfcz\xf3-\xfar\xa40\x86g\x80\xd2\x14'
    data += '\xb7\xe9\xca\x90\xc2\x19\x86\r\xe9\x12\xc2g\x8b\xeaC\xcb\xff\x15'
    data += 'V\xb2\x16\xd2\x18\xa7\xa3i\x0cu\xff\x8a\xaa\xb6\x90\xc6\xa1\xbd'
    data += '"XBo\xa9\xcf.qk!m!\x8az6\x90\xc7_'
    data += "\xf8\xabi\x0cj/\xce\xef\xf9\xdc\xf2\xe2\xee'\xa7PlJ"
    data += '\x02\x0f8z\xf3\xf2\xf2\xa5\xf0\xcf\x97\x93\x0c(<\xbc\xb0\xdc'
    data += '\xf4\xf2\xf2\x06_\xf8\xb8nzg\x978'
    decoded = decode(data)
    encoded = encode(decoded)
    again = decode(encoded)
    assert again == decoded   # note - the encoded ones might differ =)
    org = len(decoded)
    comp = len(encoded)
    ratio = float(comp) / org
    print "Original %s, compressed %s, ratio %0.3f%%" %  (org, comp, ratio)
    # ok - some fun 
    hello = compiler.compile(decoded, 'hello', 'exec')
    exec(hello)
    
