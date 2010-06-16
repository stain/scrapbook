#!/usr/bin/env python

"""
Generates OmniGraffle graphics of paths to different
tile puzzles.


Copyright (c) 2005 Stian Soiland

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Author: Stian Soiland <stian@soiland.no>
URL: http://soiland.no/software
License: MIT

"""


import sys
from sets import Set

import cPickle as pickle
import tilesgraffle

# constants
SIZE=3
LEN=SIZE*SIZE
_ = "_" # The space
N = "north"
S = "south"
W = "west"
E = "east"
solution = tuple(map(str, range(LEN-1)) + [_,])
# ('0', '1', '2', '3', '4', '5', '6', '7', '_')

opposite = { N: S, S: N, W: E, E: W}

# global variables

#  (board, direction) -> board
mappings = {}
visited = Set()

def move(board, direction):
    # Convert to mutable list
    board = list(board)
    pos = board.index(_)
    if direction == N:
        # Substract -SIZE (one row up), but never lower than
        # pos%SIZE (ie. 0, 1, or 2)
        newpos = max(pos-SIZE, pos%SIZE)
    elif direction == S:
        # Highest pos is 3*2 + colpos pos%SIZE
        # (ie. 6,7 or 8)
        newpos = min(pos+SIZE, SIZE*(SIZE-1)+pos%SIZE)
    elif direction == W:
        # Lefmost pos before flippint to previous row
        # is pos//SIZE (rownum) * SIZE, 
        # (ie. 0, 3 or 6)
        newpos = max(pos-1, pos//SIZE*SIZE)
    elif direction == E:            
        newpos = min(pos+1, (pos//SIZE+1)*SIZE-1)
    else:
        raise "Unknown direction", direction
    # Space moves to newpos, while pos gets the old
    # value from newpos
    board[pos] = board[newpos]
    board[newpos] = _    
    return tuple(board)


def print_board(board):
    out = []
    while board:
        out.append( " ".join(board[:SIZE]))
        board = board[SIZE:]
    return "\n".join(out)

def visit(board, steps):
    queue = [(board,0, None)]
    while queue:
        board,step,not_dir = queue.pop(0)
        if step > steps:
            continue
        visited.add(board)
        for dir in (N,W,S,E):
            if dir == not_dir:
                continue
            child = move(board, dir)
            if child not in visited:
                mappings[board, dir] = child
                g.draw(print_board(board), dir, print_board(child), step)
                queue.append((child, step+1, opposite[dir]))


def main(steps=3):
    global g
    g = tilesgraffle.Graffle()
    steps = int(steps)
    visit(solution, steps)
    print len(visited), len(mappings)
    g.close()
    

if __name__ == "__main__":
    main(*sys.argv[1:])

