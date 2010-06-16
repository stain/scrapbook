mapappstr = lambda a,l: [a+s for s in l]
def grey(n):
  if n == 0: return [""]
  p = grey(n-1)
  return mapappstr("0", p) + mapappstr("1", reversed(p))
