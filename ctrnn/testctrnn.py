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
"""Tests for ctrnn.py
"""

import unittest
import random

import ctrnn
import numpy

class TestTransfers(unittest.TestCase):
    def testIdentity(self):
        self.assertEqual(ctrnn.identity(1.5), 1.5)
        self.assertEqual(ctrnn.identity(-0.9), -0.9)
        self.assertEqual(ctrnn.identity(0.0), 0.0)

    def testStep(self):
        self.assertEqual(ctrnn.step(-0.3), 0.0)
        self.assertEqual(ctrnn.step(0.2), 0.0)
        self.assertEqual(ctrnn.step(0.4), 1.0)
        self.assertEqual(ctrnn.step(0.8), 1.0)
        self.assertEqual(ctrnn.step(1.8), 1.0)

    def testSigmoid(self):
        self.assertEqual(ctrnn.sigmoid(1000), 1.0)
        self.assertEqual(ctrnn.sigmoid(-1000), 0.0) # Not OverflowError
        self.assertEqual(ctrnn.sigmoid(0), 0.5)
        self.assertEqual(ctrnn.sigmoid(0, gain=4), 0.5)
        # 0.401312339887548
        assert 0.401 < ctrnn.sigmoid(0, gain=4, bias=0.1) < 0.402 
        # 2.6503965530043108e-261
        assert 0.0 < ctrnn.sigmoid(-600) < 2.66e-261 

    def testSignum(self):
        self.assertEqual(ctrnn.signum(-0.3), -1.0)       
        self.assertEqual(ctrnn.signum(-4.3), -1.0)       
        self.assertEqual(ctrnn.signum(0.3), 1.0)       
        self.assertEqual(ctrnn.signum(2.3), 1.0)       
        self.assertEqual(ctrnn.signum(0.0), 1.0)       

    def testTanhPos(self):
        assert 0.995 < ctrnn.tanh_pos(3) < 0.996
        assert 0.761 < ctrnn.tanh_pos(1) < 0.762
        assert 0.0099 < ctrnn.tanh_pos(0.01) < 0.01
        self.assertEqual(ctrnn.tanh_pos(0), 0)
        self.assertEqual(ctrnn.tanh_pos(-0.5), 0)
    

class TestCTRNN(unittest.TestCase):
    def testConstruction(self):
        neurons = 5
        net = ctrnn.CTRNN(neurons)
        self.assertEqual(net.num_neurons, neurons)
        self.assertEqual(len(net.potential), neurons)
        self.assertEqual(len(net.bias), neurons)
        self.assertEqual(len(net.timeconst), neurons)
        self.assertEqual(len(net.transfer), neurons)
        self.assertEqual(len(net.output), neurons)
        self.assertEqual(net.weight.shape, (neurons, neurons))

        self.assertEqual(list(net.potential), [0.0]*neurons)
        self.assertEqual(list(net.output), [0.0]*neurons)
        self.assertEqual(list(net.bias), [0.0]*neurons)
        for row in net.weight:
            self.assertEqual(list(row), [0.0]*neurons)

    def testConstructionDefault(self):
        neurons = 5
        net = ctrnn.CTRNN(neurons)
        # Default timeconst should be 1.0
        self.assertEqual(list(net.timeconst), [1.0]*neurons)
        # Default transfer should be sigmoid()
        self.assertEqual(list(net.transfer), [ctrnn.sigmoid]*neurons)

    def testConstructionParameters(self):
        neurons = 5
        timeconst = 1.5
        transfer = ctrnn.step
        net = ctrnn.CTRNN(neurons, timeconst, transfer=transfer)
        self.assertEqual(list(net.timeconst), [timeconst]*neurons)
        self.assertEqual(list(net.transfer), [transfer]*neurons)
    
    def testConstructionTooLowTimeconst(self):
        neurons = 5
        invalid_timeconst = 0.499
        valid_timeconst = 0.501
        self.assertRaises(AssertionError, ctrnn.CTRNN, neurons, 
                          invalid_timeconst)
        ctrnn.CTRNN(neurons, valid_timeconst)
    
    def testConnectAll(self):
        neurons = 3
        net = ctrnn.CTRNN(neurons)    
        # Should not be allowed to call with too few or too many
        # parameters
        self.assertRaises(AssertionError, net.connect_all)
        self.assertRaises(AssertionError, net.connect_all, 1.5, random.random)

        weight = 0.5
        # All rows should be equal to weight if ref_self
        net.connect_all(weight, ref_self=True)               
        for row in net.weight:
            self.assertEqual(list(row), [weight]*neurons)

        # All except the x==y cells should now be equal
        net.connect_all(weight)
        for x,row in enumerate(net.weight):
            for y,w in enumerate(row):
                if x == y:
                    self.assertEqual(w, 0.0)
                else:
                    self.assertEqual(w, weight)    
        
        # And test by random()
        net.connect_all(func=random.random, ref_self=True)
        unique = set()
        for row in net.weight:
            for w in row:
                # All should be unique
                assert w not in unique
                unique.add(w)

    def testSetTransfer(self):    
        neurons = 5
        net = ctrnn.CTRNN(neurons)
        # Default is sigmoid
        matches = net.transfer == [ctrnn.sigmoid]*neurons
        self.assert_(matches.all())

        net.set_transfer(ctrnn.identity)
        matches = net.transfer == [ctrnn.identity]*neurons
        self.assert_(matches.all())

class TestCalcTimestep(unittest.TestCase):
    def setUp(self):
        self.neurons = 3
        self.net = ctrnn.CTRNN(self.neurons)

    def testNeutral(self):
        self.assertEqual(list(self.net.output), [0.0]*self.neurons)
        self.net.calc_timestep() 
        self.assertEqual(list(self.net.output), [0.5]*self.neurons)
        self.assertEqual(list(self.net.potential), [0.0]*self.neurons)
    
    def testBias(self):    
        self.net.bias[0] = 1.0
        self.net.calc_timestep() 
        self.assertEqual(list(self.net.potential), [1.0, 0.0, 0.0])
        #0.7310585786300049 
        output0 = self.net.output[0]
        assert 0.730 < output0 < 0.732
        self.assertEqual(self.net.output[1], 0.5)
        self.assertEqual(self.net.output[2], 0.5)
        self.net.calc_timestep() 
        # Should not change (timeconst=1)
        self.assertEqual(output0, self.net.output[0]) 
    
    def testTimeconst(self):     
        self.net.bias[0] = 1.0
        self.net.calc_timestep() 
        output0 = self.net.output[0]
        self.net.timeconst[0] = 1.5 
        self.net.calc_timestep() 
        # Should not change as we have reached the bias
        self.assertEqual(output0, self.net.output[0]) 
        self.net.bias[0] = 0.0
        # should now drop gradually towards 0.5
        self.net.calc_timestep() 
        # 0.58257020646231472
        assert 0.582 < self.net.output[0] < 0.583
        self.net.calc_timestep() 
        # 0.527749235055
        assert 0.527 < self.net.output[0] < 0.528
    
    def testWeights(self):
        self.net.bias[0] = 1.0
        # from 0 to 1    
        self.net.weight[0,1] = 1.0
        self.net.calc_timestep() 
        # Does not reach it on this timestep
        self.assertEqual(self.net.potential[1], 0.0)
        self.assertEqual(self.net.output[1], 0.5)
        self.net.calc_timestep() 
        # Should be the only input, and therefore set the potential
        self.assertEqual(self.net.potential[1], self.net.output[0])
        # 0.67503752737682365 
        assert 0.675 < self.net.output[1] < 0.676
    
    def testSlice(self):
        self.net.bias[0] = 1.0 
        self.net.bias[2] = 1.0         
        self.net.calc_timestep(slice(0,1)) # ie. only 0
        # Updated
        self.assertEqual(self.net.potential[0], 1.0)
        # 0.7310585786300049 
        assert 0.730 < self.net.output[0] < 0.732
        # Unchanged
        self.assertEqual(self.net.potential[1], 0.0)
        self.assertEqual(self.net.potential[2], 0.0)
        self.assertEqual(self.net.output[1], 0.0)
        self.assertEqual(self.net.output[2], 0.0)

        # Update it all
        self.net.calc_timestep()
        self.assertEqual(self.net.output[1], 0.5)
        assert 0.730 < self.net.output[0] < 0.732
        self.net.weight[1,0] = 1.0
        self.net.calc_timestep(slice(0,1)) # ie. only 0
        # Now, even though we only updated neuron 0, he should
        # include the input from the previous calculation of 1.
        #0.817574476194
        assert 0.817 < self.net.output[0] < 0.818
    
class TestStabilize(unittest.TestCase):
    def setUp(self):
        self.neurons = 3
        self.net = ctrnn.CTRNN(self.neurons)    

    def testWeights(self):
        # Should be stable in 1 step with no connections
        self.assertEqual(self.net.stabilize(), 1)    
        self.net.weight[0,1] = 1.0
        self.net.weight[1,2] = 1.0
        # Should be stable in 2 steps to propagate
        # 0->1 and 1->2
        self.assertEqual(self.net.stabilize(), 2)
        # Let's introduce some fun
        self.net.weight[2,0] = 1.0
        steps = self.net.stabilize()
        # Should be about 24
        assert 10 < steps < 100
        # And now, let's also check that it IS stable
        output = list(self.net.output)
        self.net.calc_timestep()
        output_2 = list(self.net.output)
        self.assertEqual(output, output_2)
        # And actually, all values should be the same since our weights
        # are the same
        self.assertEqual(output[0], output[1])
        self.assertEqual(output[1], output[2])
  
    def testTimeConstant(self):
        self.net.bias[0] = 1.0
        self.net.timeconst[0] = 1.5 
        steps = self.net.stabilize()
        # Should be about 33
        assert 10 < steps < 100
        # Almost almost almost 1.0 
        assert 0.99999 < self.net.potential[0] < 1.00001
    
    def testMaxSteps(self):
        self.net.bias[0] = 1.0
        # NOTE: Illegal timeconstant < 0.5 -> unstable network    
        self.net.timeconst[0] = 0.4
        steps = self.net.stabilize()
        self.assertEqual(steps, None)

        self.net.timeconst[0] = 0.95 # stable again, in about 40 steps
        steps = self.net.stabilize(max_steps=5) # but 5 is not enough
        self.assertEqual(steps, None)
        steps = self.net.stabilize()
        # about 35
        assert 2 < steps < 100
   
    def testPrecision(self):
        precision = 0.01
        self.net.bias[0] = 1.0
        self.net.timeconst[0] = 0.6
        #steps = self.net.stabilize(precision=precision)
        steps = self.net.stabilize(precision=precision)
        # Would take about 88 steps with precision=None
        assert 7 < steps < 11

        # And check that we actually are within precision
        prev = self.net.output
        self.net.calc_timestep()
        now = self.net.output
        diff = now - prev
        assert numpy.absolute(diff).max() < precision



class TestLayers(unittest.TestCase):
    def testAdd(self):
        layers = ctrnn.Layers()
        hid_neurons = 5
        out_neurons = 2
        layers.add_layer("hidden", hid_neurons)
        layers.add_layer("output", out_neurons)
        self.assertEqual(layers.neurons, hid_neurons+out_neurons)
    
    def testAddInput(self):
        layers = ctrnn.Layers()
        in_neurons = 4
        layers.add_input_layer("input", in_neurons)
        self.assertEqual(layers.neurons, in_neurons)
        assert "input" in layers.input_layers
    
    def testBuild(self):
        hid_neurons = 5
        out_neurons = 2
        in_neurons = 4
        neurons = hid_neurons+out_neurons+in_neurons
        layers = ctrnn.Layers()
        layers.add_input_layer("input", in_neurons)
        layers.add_layer("hidden", hid_neurons)
        layers.add_layer("output", out_neurons)
        # Name already in use
        self.assertRaises(Exception, layers.add_layer, "hidden",
                          hid_neurons)
        self.assertEqual(layers.neurons, neurons)
        layers.build_net()
        self.assertEqual(layers.net.num_neurons, neurons)
        assert isinstance(layers.input, ctrnn._Layer)
        assert isinstance(layers.hidden, ctrnn._Layer)
        assert isinstance(layers.output, ctrnn._Layer)
        assert isinstance(layers.input, ctrnn._InputLayer)
        assert not isinstance(layers.hidden, ctrnn._InputLayer)
        assert not isinstance(layers.output, ctrnn._InputLayer)
   
        # Make sure they are separate 
        layers.input.bias[:] = [0,1,2,3]
        layers.hidden.bias[:] = [4,5,6,7,8]
        layers.output.bias[:] = [9,10]
        self.assertEqual(list(layers.input.bias), [0,1,2,3])
        self.assertEqual(list(layers.hidden.bias), [4,5,6,7,8])
        self.assertEqual(list(layers.output.bias), [9,10])
        # And that they are added in order, and that changes to layers
        # are reflected back in the actual net
        self.assertEqual(list(layers.net.bias), range(11)) 
        
class TestLayer(unittest.TestCase):
    def setUp(self):
        self.in_neurons = 4
        self.hid_neurons = 5
        self.out_neurons = 2
        self.layers = ctrnn.Layers()
        self.layers.add_input_layer("input", self.in_neurons)
        self.layers.add_layer("hidden", self.hid_neurons)
        self.layers.add_layer("output", self.out_neurons)
        self.layers.build_net()
    
    def testLength(self):
        hidden = self.layers.hidden
        self.assertEqual(len(hidden), self.hid_neurons)
    
    def testGetItem(self):
        hidden = self.layers.hidden
        self.assertEqual(hidden[0], self.in_neurons)
        self.assertEqual(hidden[-1], self.in_neurons+self.hid_neurons-1)
        # Check that boundaries are enforced (This would be valid
        # indexes because they would cross into "input" or "output", but
        # are not supposed to be returned from the "hidden" layer.
        self.assertRaises(IndexError, lambda: hidden[self.hid_neurons])
        self.assertRaises(IndexError, lambda: hidden[-self.hid_neurons-1])
        self.assertEqual(self.layers.input[-1]+1, hidden[0])
        self.assertEqual(hidden[-1], self.layers.output[0] - 1)
    
    def testProperties(self):
        # Set weird values before and after hidden
        self.layers.input.bias[:] = [4.0]*self.in_neurons
        self.layers.output.bias[:] = [7.0]*self.out_neurons
        hidden = self.layers.hidden
        
        self.assertEqual(list(hidden.bias), [0.0]*self.hid_neurons)
        self.assertEqual(list(hidden.potential), [0.0]*self.hid_neurons)
        self.assertEqual(list(hidden.output), [0.0]*self.hid_neurons)
        self.assertEqual(list(hidden.timeconst), [1.0]*self.hid_neurons)
        self.assertEqual(list(hidden.transfer), [ctrnn.sigmoid]*self.hid_neurons)
    def testSetTransfer(self):    
        hidden = self.layers.hidden
        neurons = len(hidden)
        # Default is sigmoid
        matches = hidden.transfer == [ctrnn.sigmoid]*neurons
        self.assert_(matches.all())

        hidden.set_transfer(ctrnn.signum)
        matches = hidden.transfer == [ctrnn.signum]*neurons
        self.assert_(matches.all())

        # And that the other are untouched
        # (Note how the input layer has identity by default)
        self.assertEqual(list(self.layers.input.transfer),
                         [ctrnn.identity]*self.in_neurons)
        self.assertEqual(list(self.layers.output.transfer),
                         [ctrnn.sigmoid]*self.out_neurons)

    def testTimestep(self):
        hidden = self.layers.hidden
        hidden.calc_timestep()
        self.assertEqual(list(hidden.output), [0.5]*self.hid_neurons)
        self.assertEqual(list(hidden.potential), [0.0]*self.hid_neurons)
        hidden.bias[:] = [1.0] * self.hid_neurons
        hidden.calc_timestep()
        self.assertEqual(list(hidden.potential), [1.0]*self.hid_neurons)

        # Make sure nothing else changed 
        self.assertEqual(list(self.layers.input.bias), [0.0]*self.in_neurons)
        self.assertEqual(list(self.layers.input.potential), [0.0]*self.in_neurons)
        self.assertEqual(list(self.layers.input.output), [0.0]*self.in_neurons)
        self.assertEqual(list(self.layers.output.bias), [0.0]*self.out_neurons)
        self.assertEqual(list(self.layers.output.potential), [0.0]*self.out_neurons)
        self.assertEqual(list(self.layers.output.output), [0.0]*self.out_neurons)
    
    def testInput(self):
        input = self.layers.input
        values = [-0.5, -0.1, 0.1, 0.5]
        input.set_inputs(values)
        self.assertEqual(list(input.bias), values)
        self.assertEqual(list(input.potential), values)
        self.assertEqual(list(input.output), values)
        self.assertEqual(list(input.transfer),
                         [ctrnn.identity]*self.in_neurons)
        

        

if __name__ == "__main__":
    unittest.main()

