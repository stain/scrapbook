
def window(iterable):
    prev = curr = next = None
    for next in iterable:
        if curr is None:
            # first time 
            curr = next
            continue
        yield (prev, curr, next)
        prev = curr
        curr = next
    if next is None:
        # empty iterable
        return
    # Last item
    yield (prev, curr, None)


a = range(10)
for prev,curr,next in window(a):
    assert prev is None
    assert curr == 0
    assert next == 1
    break


for prev,curr,next in window(a):
    assert prev < curr
    if next is None:
        assert prev == 8
        assert curr == 9
    else:
        assert curr < next

assert next == None    

# empty list
for prev,curr,next in window([]):
    assert 1==0

