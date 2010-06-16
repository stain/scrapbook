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
"""Continuous time recurrent neural network.

"""


from math import exp, sqrt, pi, tanh
import operator
import logging

try:
    import numpy
except ImportError:    
    # Try to go old-fashioned
    import Numeric as numpy


# Hackish, generate IEEE 754 special values
#inf = 1e300 * 1e300
#nan = inf - inf

def identity(x):
    """Identity transfer function"""
    return x
assert identity(1.5) == 1.5
assert identity(-0.9) == -0.9
assert identity(0.0) == 0.0


def step(x, limit=0.4):
    """Step transfer function"""
    if x < limit:
        return 0.0
    return 1.0
assert step(-0.3) == 0.0
assert step(0.2) == 0.0
assert step(0.4) == 1.0
assert step(0.8) == 1.0
assert step(1.8) == 1.0

def sigmoid(x, gain=1.0, bias=0.0):
    """Sigmoidal transfer function."""
    try:
        return 1.0 / (1.0 + exp(-gain * (x-bias)))
    except OverflowError:
        return 0.0
# sigmoid tests
assert sigmoid(1000) == 1.0
assert sigmoid(-1000) == 0.0 # Not OverflowError
assert sigmoid(0) == 0.5
assert sigmoid(0, gain=4) == 0.5
assert 0.401 < sigmoid(0, gain=4, bias=0.1) < 0.402 # 0.401312339887548
assert 0.0 < sigmoid(-600) < 2.66e-261 # 2.6503965530043108e-261

def dsigmoid(x):
    """Derivative of sigmoid()"""
    f = sigmoid(x)
    return f * (1-f)

def gaussian(x, mu=0.0, sigma=1.0):
    """Gaussian transfer function"""
    return  (1 / (sqrt(2*pi) * sigma)) * exp( -0.5 * ( (x-mu)/sigma ) ** 2 )

def dgaussian(x, *args, **kwargs):
    """Derivative of gaussian(), parameters as for gaussian()"""
    return -2 * gaussian(x, *args, **kwargs) * x

def signum(x):
    if x < 0.0:
        return -1.0
    return 1.0

# The same as math.tanh
#def tansig(x):
#    return ( 2/ (1+exp(-2*x)) ) -1

def dtansig(x):
    """Derivative of tanh()"""
    f = tanh(x)
    return 1-(f**2)

def tanh_pos(x):
    """tanh with lower limit of 0.0"""
    if x < 0.0:
        return 0.0
    return tanh(x)

assert 0.995 < tanh_pos(3) < 0.996
assert 0.761 < tanh_pos(1) < 0.762
assert 0.0099 < tanh_pos(0.01) < 0.01
assert tanh_pos(0) == 0
assert tanh_pos(-0.5) == 0
    


class Layers(object):
    """Layers for constructing and accessing a CTRNN.
    
    A layer is a set of neurons. A network is made of several layers.
    Note that compared to feed-forward networks, there are no rules that
    neurons in a layer cannot be interconnected. In addition,
    timestep calculation is done globally, not per layer. 
   
    These layers can be used to group neurons into different layers for
    easier access to their parameters. For instance, a network can
    consist of an input layer, a hidden layer, and an output layer,
    which can have different weights and time constants.  Instead of
    remembering that the hidden neurons are in the range 15 to 26 and
    using these offsets in all code, the layer can be accessed as the
    attribute "hidden".

    Construction work by adding layers using add_layers(). When all the
    layers are ready, build_net() is called. After this, no more layers
    can be added, the complete CTRNN network is available as attribute
    .net, and the different layers as attributes by .their_name.

    Example:
        layers = Layers()
        layers.add_layer("input", 3)
        layers.add_layer("hidden", 5)
        layers.add_layer("output", 2)
        layers.build_net()
        assert len(layers.net.potential) == 3+5+2
         
        layers.input.bias[0] = 10
        layers.input.bias[1] = -5
        layers.input.bias[2] = 15
        layers.hidden.timeconst[3] = 5
         
        layers.hidden.weight[0, 0] = 13
    """
    
    def __init__(self):
        self.layers = []
        self.neurons = 0
        self.net = None

    def add_layer(self, name, neurons):
        if self.net:
            raise "Cannot add layers after build_net()"
        if hasattr(self, name):    
            raise AttributeError, "already exists: %s" % name    
        # Placeholder until build_net   
        setattr(self, name, None)    
        min = self.neurons  # Inclusive
        self.neurons += neurons
        max = min + neurons # exclusive 
        self.layers.append((name, slice(min,max)))

    def build_net(self, timeconst=1.0):
        self.net = CTRNN(self.neurons, timeconst)
        for (name, slice) in self.layers:
            layer = _Layer(self.net, slice)
            setattr(self, name, layer)


class _Layer(object):
    """Proxy access to network parameters for the given layer.

    Properties such as bias, output, potential and timeconst are sliced
    out to refer to the current Layer only. Note that due to the use of
    numpy.array, these slices are also assignable, and changes are
    reflected in the grand network.

    The property ''weight'' is the part of the weight matrix for
    connections going *to* this layer, from *all* neurons. As thus, the
    matrix is sized with n rows and m columns, where n is the number of
    neurons in the whole network, and m is the number of neurons in this
    layer. 

    Examples:

        # Set the weight from network neuron number 14 (global indexes)
        # to neuron 2 in this layer.
        layer.weight[14,3] = 0.7

        # Get global index for usage in another layer.weight
        index = layer[2] 

        # Check the output of the layer
        print layer.output

        # Set all the biases at once (assumed layer size 4)
        layer.bias[:] = [0,1,2,3]

    """
    def __init__(self, net, slice):
        self.net = net
        self.slice = slice
    
    def __len__(self):
        step = self.slice.step or 1
        return (self.slice.stop - self.slice.start) / step
    
    def __getitem__(self, item):
        step = self.slice.step or 1
        index = item * step
        if index < 0:
            index = self.slice.stop + index
        else:    
            index = self.slice.start + index
        if index < self.slice.start:
            raise IndexError, item
        if index >= self.slice.stop:
            raise IndexError, item
        return index    
    
    def calc_timestep(self):
        self.net.calc_timestep(self.slice)
    
    def _slicer(self, array):
        # Note: This will only work for assignments if array is of
        # numpy.arraytype, where slices work as pointers instead of
        # making copied arrays
        assert isinstance(array, numpy.arraytype)
        return array[self.slice]    

    #@property
    def bias(self):
        return self._slicer(self.net.bias)
    bias = property(bias)
               
    #@property
    def output(self):
        return self._slicer(self.net.output)
    output = property(output)
            
    #@property
    def potential(self):
        return self._slicer(self.net.potential)
    potential = property(potential)
        
    #@property
    def timeconst(self):
        return self._slicer(self.net.timeconst)
    timeconst = property(timeconst)

    #@property
    def weight(self):
        # We return the weights pointing TO this neuron, 
        # ie. where second dimension is our slice
        return self.net.weight[:,self.slice]
    weight = property(weight)



class CTRNN(object):
    """Continuous time recurrent neural network.
    """

    def __init__(self, neurons, timeconst=1.0):
        """Construct a new CTRNN of the given number of neurons.

        Optional parameter timeconst is the time constant for neurons,
        by default 1.0.  Individual time constants can later be modified
        through self.timeconst.

        Optional parameter weight is the weight for connections between
        neurons. By default, the network is fully connected (except
        self-loops) with the given weight, which default value is 0.5
        """
        # Prepare logging
        self.log = logging.getLogger("ctrnn")
        if not self.log.handlers or logging.root.handlers:
            logging.basicConfig()

        self.num_neurons = neurons
        # internal state, membrane potential
        self.potential = numpy.zeros(neurons, numpy.Float)
        # Our timestep \Delta t is fixed at 1.0, which must be smaller
        # than twice the smallest timeconst
        assert timeconst > 0.5
        # By default, no bias
        self.bias = numpy.zeros(neurons, numpy.Float)
        self.timeconst = numpy.array([float(timeconst)] * neurons)
        self.weight = numpy.array(numpy.zeros((neurons, neurons)),  
                                    numpy.Float)
        # Output values as calulated by calc_timestep()    
        self.output = numpy.zeros(neurons, numpy.Float)
    
    def connect_all(self, weight=None, func=None, ref_self=False):
        """Connect all neurons using the specified weight or function.

        Either weight or func must be specified, but not both.

        If weight is specified, it is the scalar weight assigned to all
        connections.

        If func is specified, it is assumed to be a function taking no
        arguments. The function will be called for each connection, 
        and the result is assigned to the connection. No order can be
        assumed, so this function is normally something like
        random.random.

        If ref_self is set to True, self-looping weights will also be
        assigned between neuron n and neuron n.
        """
        assert ((weight is None and func) or 
                (weight is not None and not func))
        for n in range(self.num_neurons):
            for m in range(self.num_neurons):
                if n == m and not ref_self:
                    continue
                if func:
                    weight = func()    
                self.weight[n,m] = weight    
    
    def calc_timestep(self, slicing=None):
        """Calculate the next timestep.

        If slicing is given, it is assumed a slice object from which
        neurons are to be updated. Otherwise, all neurons are updated.
        """
        # We do this as nice matrix operations
        if not slicing:
            # ie. [:] - everything  FIXME: Undocumented in Python
            slicing = slice(None)
        inputs = numpy.matrixmultiply(self.output,
                                        self.weight[:,slicing]) 
        change = 1.0/self.timeconst[slicing] * (-self.potential[slicing] + 
                                                 inputs + self.bias[slicing])
        self.potential[slicing] += change
        self.output[slicing] = map(self.transfer, self.potential[slicing])

    def transfer(self, x):
        """Transfer function for generating output from potential.

        By default, sigmoid(x) will be called.
        
        To override, subclass or assign to ctrnn.transfer, for
        instance::

            >>> net = ctrnn.CTRNN(5)
            >>> net.transfer = lambda x: ctrnn.transfer(x, gain=4, 
            ...                                         bias=0.1)
        """
        return sigmoid(x) 
    
    def stabilize(self, max_steps=200):
        """Run the network until it stabilizes.

        A network is considered stable if the output does not change
        from one timestep to the next. (Note that depending on the
        transfer function, potentials can still change by this
        definition)

        If parameter max_steps is supplied, it is the maximum number of
        timesteps to run, by default 200.

        Return the number of time steps used to stabilize, or None
        if the network did not stabilize within the maxiumum steps.
        """
        
        for x in xrange(max_steps):
            # Make a copy that is not changed by calc_timestep
            prev = list(self.output)
            self.calc_timestep() 
            diff = numpy.subtract(prev, self.output)
            # All must be 0
            if not numpy.sometrue(diff):
                self.log.info("Stabilized in %s timesteps", x)
                return x
        return None
    
