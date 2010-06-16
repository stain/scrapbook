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
"""CTRNN basal ganglia, as of Prescott 2006
"""

import logging
import itertools
import Numeric
import ctrnn
from isplit import isplit
from sets import Set
import operator
import sys


DEBUG=1
STATS=1

def piecewise(a, theta=0.0):
    """Piecewise lineaer transfer as by Prescott et al. 2006"""
    # NOTE: This function SUCKS. And with negative theta, values of
    # 1+abs(theta) might be output, ie. this is not really limited to
    # 0..1
    if a < theta:
        return 0.0
    if a <= 1.0/(1.0+theta):
        return a-theta    
    if a > (1+theta):
        return 1
    logging.warning("Unknown piecewise value %s", a)
    return 1   


class Prescott(ctrnn.Layers):
    def __init__(self):
        # Logger
        self.log = logging.getLogger("prescott")
        if not self.log.handlers or logging.root.handlers:
            logging.basicConfig()
        # constants and initial weights/values
        self.seq = [0,1,2,3,1,4]
        self.inputs = max(self.seq)+1
        self.trainsteps = 20   # timesteps to train
        self.hintsteps = 1     # timesteps to hint in testing
        self.trialsteps = 0    # timesteps for trial 
        self.striatum_delta = 0.2
        self.timeconst = 3.3333
        # "The model was considered to have converged
        #  whenever the smallest delta a on two consecutive
        #  timesteps was less than 0.0001"
        # (We'll assume Prescott meant the LARGEST delta)
        self.stable_limit = 0.0001
        self.w = {
            # Unless otherwise noted, connections are 1-1 by channel
            ('ssc', 'd1'): (1+self.striatum_delta)*0.5,
            ('ssc', 'd2'): (1-self.striatum_delta)*0.5,
            ('ssc', 'mc'): 1,
            ('ssc', 'stn'): 0.5,
            ('mc', 'd1'): (1+self.striatum_delta)*0.5,
            ('mc', 'd2'): (1-self.striatum_delta)*0.5,
            ('mc', 'vl'): 1,
            ('mc', 'trn'): 1,
            ('mc', 'stn'): 0.5,
            ('d1', 'snr'): -1,
            ('d2', 'gp'): -1,
            ('stn*', 'snr'): 0.9, # all-to-all
            ('stn*', 'gp'): 0.9,  # all-to-all
            ('gp', 'stn'): -1,
            ('gp', 'snr'): -0.3,
            ('snr', 'trn'): -0.2,
            ('snr', 'vl'): -1,
            ('trn', 'vl'): -0.125,
            ('trn*', 'vl'): -0.4,  # all-to-all
            ('vl', 'mc'): 1,
            ('vl', 'trn'): 1,
        }

        # Build layers 
        ctrnn.Layers.__init__(self)
        layers = reduce(Set.union, map(Set, isplit(self.w)))
        for layer in layers:
            if "*" in layer: continue
            if layer == "ssc":
                self.add_input_layer(layer, self.inputs)
            else:    
                self.add_layer(layer, self.inputs)
        self.build_net(timeconst=self.timeconst)
        self.net.set_transfer(piecewise)
        # Otherwise ssc will also have piecewise
        self.ssc.fix()
        for n in range(self.inputs):
            for ((src_l,dest_l), weight) in self.w.items():
                dest = getattr(self, dest_l)[n]
                if src_l[-1] == "*":
                    # All of them are inputs
                    for m in range(self.inputs):
                        src = getattr(self, src_l.rstrip("*"))[m]
                        self.net.weight[src, dest] = weight
                else:   
                    src = getattr(self, src_l)[n]
                    self.net.weight[src, dest] = weight
            # Just make sure this weight is set after trn* -> vl
            self.vl.weight[self.trn[n], n] = self.w["trn", "vl"]    
            # And the biases
            self.d1.bias[n] = -0.2
            self.d2.bias[n] = -0.2
            self.stn.bias[n] = 0.25
            self.gp.bias[n] = 0.2
            self.snr.bias[n] = 0.2
        self.set_input()
        self.net.stabilize()
    
    def set_input(self, input=-1):
        # input is 0 or 1, depending on the selected channel
        inputs = [n == input for n in range(self.inputs)]    
        self.ssc.set_inputs(inputs)      
    
    def get_output(self, timestep=False):
        if timestep:
            self.net.calc_timestep()
        return self.gp.output    
    
    def winner(self):
        output = self.get_output()
        return list(output).index(min(output))
            
    
    def step(self, input=None):
        if input is not None:
            self.set_input(input) 
        self.net.stabilize(precision=self.stable_limit)
        self.log_stats()

    def train(self):
        for x in range(self.trainsteps/len(self.seq)):
            for number in self.seq:
                self.step(number)    
                for x in range(8):
                    self.step()   
                guess = self.winner()
                self.log.info("Train h=%s g=%s %s", number, guess, self.get_output())
    
    def reset(self):
        self.net.potential[:] = [0.0] * self.neurons

    def test(self):
        self.reset()
        seq = itertools.cycle(self.seq)
        for hint in itertools.islice(seq, self.hintsteps):
            self.step(hint)
            for x in range(8):
                self.step()   
            guess = self.winner()
            self.log.info("Hint h=%s g=%s %s", hint, guess, 
                       self.get_output())

        # Set no input
        self.set_input(-1)
        correct = 0
        answers = []
        for answer in itertools.islice(seq, self.trialsteps):
            self.step()    
            for x in range(8):
                self.step()   
            guess = self.winner()
            answers.append(guess)
            self.log.info("Test a=%s g=%s %s", answer, guess, 
                       self.get_output())
            correct += guess==answer
        return correct, answers

    def log_stats(self):
        if not STATS:
            return
        if not hasattr(self, "_f"):
            # Open files for writing        
            self._f = dict()
            for out,_ in self.layers:
                # Outputs
                self._f[out] = open("%s.txt" % out, "w")
                # Weights
                out = "w_" + out
                self._f[out] = open("%s.txt" % out, "w")
        
        # Log the stats 
        for name,_ in self.layers:
            # outputs
            out = self._f[name]
            layer = getattr(self, name)
            out.write(" ".join(map(str, layer.output)))
            out.write("\n")
            # weights
            out = self._f["w_" + name]
            for n in xrange(len(layer)):
                out.write(" ".join(map(str, layer.weight[:,n])))
                out.write(" ")
            out.write("\n")

        #print >>self._f["E"], self.error
        
    def salience(self):
        """Test salience space"""
        for s1 in xrange(100):
            s1 /= 100.0
            self.net.output[:] = [0.0]*len(self.net.output)
            for s2 in xrange(100):                
                s2 /= 100.0
                inputs = [s1, s2, 0.0, 0.0, 0.0] 
                self.ssc.set_inputs(inputs)
                self.step()
                sys.stdout.write(".")
                sys.stdout.flush()
            sys.stdout.write("\n")
            sys.stdout.flush()

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    prescott = Prescott()
    #prescott.train()     
    #prescott.test()     
    prescott.salience()

