#!/usr/bin/env python
"""A serviette program, probably useless
   (c) Stian Søiland 2003 """
if __name__=="__main__":
    print reduce(lambda x,y:
       x+chr(y), (66,69,69,82), '')
