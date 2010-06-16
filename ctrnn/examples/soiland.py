#!/usr/bin/env python
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
"""CTRNN basal ganglia, by Stian Soiland
"""

import logging
import itertools
import Numeric
import ctrnn


def sigmoid_bias(x):
    """Sigmoid with gain and bias set according to Soiland."""
    return ctrnn.sigmoid(x, gain=1, bias=-0.1)


DEBUG=1
STATS=1


class Soiland(ctrnn.Layers):
    def __init__(self):
        # Logger
        self.log = logging.getLogger("soiland")
        if not self.log.handlers or logging.root.handlers:
            logging.basicConfig()
        # constants and initial weights/values
        self.seq = [0,1,2,3,1,4]
        self.inputs = max(self.seq)+1
        self.trainsteps = 300   # timesteps to train
        self.hintsteps = 1     # timesteps to hint in testing
        self.trialsteps = 30   # timesteps for trial 
        self.long =  4 # 40 msec
        self.short = 1.1 # 11 msec
        self.effect = -10
        self.w_learning = 0.05
        self.v_learning = 0.1
        self.v = [1.0 for x in range(self.inputs)]
        # Build layers 
        ctrnn.Layers.__init__(self)
        self.add_layer("str", self.inputs)
        self.add_layer("gp", self.inputs)
        self.add_layer("stn_l", self.inputs)
        self.add_layer("stn_s", self.inputs)
        self.build_net()
        self.net.transfer = sigmoid_bias
        for n in range(self.inputs):
            # 1-1 mappings
            self.gp.weight[self.str[n], n] = -10.0
            self.stn_l.weight[self.gp[n], n] = self.effect
            self.stn_s.weight[self.gp[n], n] = self.effect
            for m in range(self.inputs):
            #    # And STNs connect to all GPs
                self.gp.weight[self.stn_l[n], n] = 0.4
                self.gp.weight[self.stn_s[n], n] = 0.4
            
            # Only STN has timeconsts != 1
            self.stn_l.timeconst[n] = self.long
            self.stn_s.timeconst[n] = self.short
        self.set_input()
        self.net.stabilize()
    
    def set_input(self, input=-1):
        # input is 0 or 1
        for n in range(self.inputs):
            self.str.bias[n] = (n == input) and 1000 or -1000
        self.str.calc_timestep()      
    
    def get_output(self, timestep=False):
        if timestep:
            self.net.calc_timestep()
        return self.gp.output    
    
    def winner(self):
        output = self.get_output()
        return list(output).index(min(output))
            
    def calc_error(self):
        self.error = Numeric.sum(self.v*self.str.output - 
                                 self.gp.output) + self.inputs
        print self.error
    
    def calc_v_change(self, i):
        return self.v_learning * self.error * self.str.output[i]
    
    def calc_w_change(self, i, stn):
        # Calculates the change between input i and 
        # (globally indexed) STN unit
        r = (self.w_learning * (self.error * self.gp.output[i] - 
                               self.str.output[i]) *
             self.net.output[stn])
        return r
    
    def calc_STN(self):
        self.stn_l.calc_timestep()
        self.stn_s.calc_timestep()

    def calc_GP(self):
        self.gp.calc_timestep()
    
    def normalize_weight(self, source, dest, lower=0.0, upper=1.0):
        w = self.net.weight[source][dest]    
        if min < w < max:
            return
        self.net.weight[source][dest] = max(lower, min(upper, w))
    
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
        for n,gp in enumerate(self.gp):
            for m in range(self.inputs):
                stn_l = self.stn_l[m]
                stn_s = self.stn_s[m]
                self.net.weight[stn_l][gp] += self.calc_w_change(n, stn_l)
                self.net.weight[stn_s][gp] += self.calc_w_change(n, stn_s)
                self.normalize_weight(stn_l, gp)
                self.normalize_weight(stn_s, gp)
            self.v[n] += self.calc_v_change(n)
            self.v[n] = max(0.0, min(1.0, self.v[n]))
        self.log_stats()

    def train(self):
        for x in range(self.trainsteps/len(self.seq)):
            for number in self.seq:
                self.step(number)    
                guess = self.winner()
                self.log.info("Train h=%s g=%s %s", number, guess, self.get_output())
    
    def reset(self):
        self.net.potential[:] = [0.0] * self.neurons

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

    def log_stats(self):
        if not STATS:
            return
        if not hasattr(self, "_f"):
            self._f = dict()
            for out in ("str", "gp", "stn_l_p", "stn_l", "stn_s", "E", "v", "w_stn_l", "w_stn_s"):
                self._f[out] = open("%s.txt" % out, "w")
        
        layers = ("str", "gp", "stn_l", "stn_s")
        for name in layers:
            out = self._f[name]
            layer = getattr(self, name)
            out.write(" ".join(map(str, layer.output)))
            out.write("\n")

        self._f["stn_l_p"].write(" ".join(map(str, self.stn_l.potential)))
        self._f["stn_l_p"].write("\n")

        print >>self._f["E"], self.error
        print >>self._f["v"], " ".join(map(str, self.v))
        
        # And the GP weights
        for gp in self.gp:
            for stn_s in self.stn_s:
                self._f["w_stn_s"].write("%s " % self.net.weight[stn_s][gp])
            for stn_l in self.stn_l:
                self._f["w_stn_l"].write("%s " % self.net.weight[stn_l][gp])
        self._f["w_stn_s"].write("\n")      
        self._f["w_stn_l"].write("\n")      
             

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    soiland = Soiland()
    soiland.train()     
    soiland.log
    soiland.test()
