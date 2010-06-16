#!/usr/bin/env python2.4
# *-* encoding: utf8
# 
# Copyright (c) 2006 Stian Soiland
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Author: Stian Soiland <stian@soiland.no>
# URL: http://soiland.no/i/src/
# License: MIT
#
"""CTRNN basal ganglia, approaching Berns & Sejnowski 1998.
"""

import logging
import itertools
import ctrnn


def sigmoid_bias(x):
    """Sigmoid with gain and bias set according to Berns1998."""
    return ctrnn.sigmoid(x, gain=4, bias=0.0)


DEBUG=1
STATS=1


class Berns:
    def __init__(self):
        # Logger
        self.log = logging.getLogger("berns")
        if not self.log.handlers or logging.root.handlers:
            logging.basicConfig()
        # constants and initial weights/values
        self.seq = [0,1,2,3,1,4]
        self.inputs = max(self.seq)+1
        self.neurons = self.inputs * 4 # str, gp, stn_l, stn_s
        self.trainsteps = 300   # timesteps to train
        self.hintsteps = 1     # timesteps to hint in testing
        self.trialsteps = 30   # timesteps for trial 
        self.long =  4 # 20 msec
        self.short = 0.7 # 7 msec
        self.effect = 10
        self.w_learning = 0.5
        self.v_learning = 0.1
        self.v = [0.0 for x in range(self.inputs)]
        # By default, timeconst=1 (no ctrnn) and no weights
        self.net = ctrnn.CTRNN(self.neurons)
        self.net.transfer[:] = [sigmoid_bias for x in range(self.inputs)]
        for n in range(self.inputs):
            # 1-1 mappings
            self.net.weight[self.str(n), self.gp(n)] = -100.0 # inhib
            self.net.weight[self.gp(n), self.stn_l(n)] = self.effect
            self.net.weight[self.gp(n), self.stn_s(n)] = self.effect
            for m in range(self.inputs):
                # And STNs connect to all GPs
                self.net.weight[self.stn_l(n), self.gp(m)] = 0.0
                self.net.weight[self.stn_s(n), self.gp(m)] = 0.0
            
            # Only STN has timeconsts != 1
            self.net.timeconst[self.stn_l(n)] = self.long
            self.net.timeconst[self.stn_s(n)] = self.short
            #self.net.bias[self.stn_l(n)] = -0.9
        self.set_input()
        self.net.stabilize()
        

    def str(self, n):
        return n
        
    def gp(self, n):
        return n + self.inputs
        
    def stn_l(self, n):
        return n + self.inputs*2

    def stn_s(self, n):
        return n + self.inputs*3
    
    def set_input(self, input=-1):
        # input is 0 or 1
        for n in range(self.inputs):
            self.net.bias[self.str(n)] = (n == input) and 1000 or -1000
        # Update only those neurons
        self.net.calc_timestep(slice(self.str(0), self.str(self.inputs)))
        self.log.debug("set_input(%s) %s", input, [self.net.output[self.str(n)] for n in range(self.inputs)])
    
    def get_output(self):
        return [self.net.output[self.gp(n)] for n in range(self.inputs)]
    
    def winner(self):
        output = self.get_output()
        return output.index(min(output))
            
    def calc_error(self):
        sum = 0.0
        for n in range(self.inputs):
            sum += (1-self.net.output[self.gp(n)])
            sum -= self.v[n] * self.net.output[self.str(n)]
        self.error = sum     
    
    def calc_v_change(self, i):
        return self.v_learning * self.error * self.net.output[self.str(i)]
    
    def calc_w_change(self, i, stn):
        # Calculates the change between input i and STN unit stn
        r = (self.w_learning * (self.error * self.net.output[self.gp(i)] - 
                               self.net.output[self.str(i)]) *
             self.net.output[stn])
        return r
    
    def calc_STN(self):
        neurons = slice(self.stn_l(0), self.stn_l(self.inputs))
        self.net.calc_timestep(neurons)
        neurons = slice(self.stn_s(0), self.stn_s(self.inputs))
        self.net.calc_timestep(neurons)

    def calc_GP(self):
        neurons = slice(self.gp(0), self.gp(self.inputs))
        self.net.calc_timestep(neurons)
    
    def step(self, input=None):
        if input is not None:
            self.set_input(input) 
        # Calculated from previous GP values
        self.calc_STN() 
        # Calculated from new STNs, and new STRs
        self.calc_GP()
        # Compares new GPs with new STRs
        self.calc_error()

        # Update weights
        for n in range(self.inputs):
            gp = self.gp(n)
            for m in range(self.inputs):
                stn_l = self.stn_l(m)
                stn_s = self.stn_s(m)
                self.net.weight[stn_l, gp] += self.calc_w_change(n, stn_l)
                self.net.weight[stn_s, gp] += self.calc_w_change(n, stn_s)
            self.v[n] += self.calc_v_change(n)
            # FIXME: Add weight constraints
        self.log_stats()

    def train(self):
        for x in range(self.trainsteps/len(self.seq)):
            for number in self.seq:
                self.step(number)    
                guess = self.winner()
                self.log.info("Train h=%s g=%s %s", number, guess, self.get_output())
    
    def reset(self):
        self.net.potential[:] = [0] * self.neurons

    def log_stats(self):
        if not STATS:
            return
        if not hasattr(self, "_f"):
            self._f = dict()
            for out in ("str", "gp", "stn_l_p", "stn_l", "stn_s", "e", "f", "v", "w_stn_l", "w_stn_s"):
                self._f[out] = open("%s.txt" % out, "w")
        
        layers = ("str", "gp", "stn_l", "stn_s")
        for n in range(self.inputs):
            for layer in layers:
                mapper = getattr(self, layer)            
                self._f[layer].write("%s " % self.net.output[mapper(n)])
            self._f["stn_l_p"].write("%s " % self.net.potential[self.stn_l(n)])
        self._f["stn_l_p"].write("\n")

        # finished all log-lines
        for layer in layers:
            self._f[layer].write("\n")

        print >>self._f["e"], self.error
        print >>self._f["v"], " ".join(map(str, self.v))
        
        # And the GP weights
        for n in range(self.inputs):
            gp = self.gp(n)
            for m in range(self.inputs): 
                stn_s = self.stn_s(m)
                self._f["w_stn_s"].write("%s " % self.net.weight[stn_s][gp])
            for m in range(self.inputs): 
                stn_l = self.stn_l(m)
                self._f["w_stn_l"].write("%s " % self.net.weight[stn_l][gp])
        self._f["w_stn_s"].write("\n")      
        self._f["w_stn_l"].write("\n")      
         

    def test(self):
        self.reset()
        seq = itertools.cycle(self.seq)
        for hint in itertools.islice(seq, self.hintsteps):
            self.step(hint)
            guess = self.winner()
            self.log.info("Hint h=%s g=%s %s e=%s", hint, guess, 
                       self.get_output(), self.error)

        # Set no input
        self.set_input(-1)
        correct = 0
        answers = []
        for answer in itertools.islice(seq, self.trialsteps):
            self.step()    
            guess = self.winner()
            answers.append(guess)
            self.log.info("Test a=%s g=%s %s e=%s", answer, guess, 
                       self.get_output(), self.error)
            correct += guess==answer
        return correct, answers
             

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    berns = Berns()
    berns.train()     
    berns.log
    berns.test()
