
class Z(object):
    def __init__(self, string):
        self.string = string
        self.z = {}
        self._calc_z()
    
    def _calc_z(self):
        left = right = 0
        for pos in xrange(1, len(self.string)):
            if pos > right:
                length = 0
                for startpos,char in enumerate(self.string[pos:]):
                    if char != self.string[startpos]:
                        break
                    length += 1
                #print pos, "#1"   
                self.z[pos] = length      
                if length > 0:
                    right = pos+length
                    left = pos
            else: # k <= r
                # We are inside a Z-box
                # string[pos] is in string[left:right]

                # string[pos] is also in string[pos-left]
                # as such, string[pos:right] should match
                # string[pos-left : z[left] ]

                lbeta = right-pos
                Zkmark = self.z[pos-left]
                if (Zkmark < lbeta):
                    #print pos, "#2a"   
                    self.z[pos] = self.z[pos-left]
                else: # Zmark >= lbeta
                    # string[pos:right] matches, but beyond?
                    extra = 0
                    try:
                        while (self.string[right-pos+extra] ==
                            self.string[right+extra]):
                            extra += 1
                    except IndexError:
                        pass    

                    left = pos     
                    right = right + extra
                    self.z[pos] = right - left
        #print self.z            
    
    def __getitem__(self, i):    
        return self.z[i]
        


def findall(pattern, text, escape="\000"):
    z = Z(pattern + escape + text)
    pat_len = len(pattern)
    for (pos, length) in z.z.items():
        if pos < len(pattern):
            continue
        if length == len(pattern):
            yield pos - length - len(escape)

