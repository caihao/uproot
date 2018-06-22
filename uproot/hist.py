#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import numbers
import math

import numpy

import uproot.rootio

class TH1Methods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __repr__(self):
        if self.fName is None:
            return "<{0} at 0x{1:012x}>".format(self._classname, id(self))
        else:
            return "<{0} {1} 0x{2:012x}>".format(self._classname, repr(self.fName), id(self))

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numbins(self):
        return self.fXaxis.fNbins

    @property
    def low(self):
        return self.fXaxis.fXmin

    @property
    def high(self):
        return self.fXaxis.fXmax

    @property
    def underflows(self):
        return self[0]

    @property
    def overflows(self):
        return self[-1]

    @property
    def values(self):
        return self[1:-1]

    @property
    def allvalues(self):
        return self[:]

    @property
    def numpy(self):
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        norm = (high - low) / self.fXaxis.fNbins
        freq = numpy.array(self.values, dtype=self._dtype.newbyteorder("="))
        edges = numpy.array([i*norm + low for i in range(self.numbins + 1)])
        return freq, edges

    def interval(self, index):
        if index < 0:
            index += len(self)

        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if index == 0:
            return (float("-inf"), low)
        elif index == len(self) - 1:
            return (high, float("inf"))
        else:
            norm = (high - low) / self.fXaxis.fNbins
            return (index - 1)*norm + low, index*norm + low

    def index(self, data):
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if data < low:
            return 0
        elif data >= high:
            return len(self) - 1
        elif not math.isnan(data):
            return int(math.floor(self.fXaxis.fNbins * (data - low) / (high - low))) + 1

    def fill(self, datum):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if datum < low:
            self[0] += 1
        elif datum >= high:
            self[-1] += 1
        else:
            self[int(math.floor(numbins * (datum - low) / (high - low))) + 1] += 1

    def fillw(self, datum, weight):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if datum < low:
            self[0] += weight
        elif datum >= high:
            self[-1] += weight
        else:
            self[int(math.floor(numbins * (datum - low) / (high - low))) + 1] += weight

    def fillall(self, data):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax

        if not isinstance(data, numpy.ndarray):
            data = numpy.array(data)

        freq, edges = numpy.histogram(data, bins=numbins, range=(low, high), density=False)
        for i, x in enumerate(freq):
            self[i + 1] += x

        self[0] += (data < low).sum()
        self[-1] += (data >= high).sum()

    def fillallw(self, data, weights):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax

        if not isinstance(data, numpy.ndarray):
            data = numpy.array(data)

        if isinstance(weights, numbers.Real):
            weights = numpy.empty_like(data)

        freq, edges = numpy.histogram(data, bins=numbins, range=(low, high), weights=weights, density=False)
        for i, x in enumerate(freq):
            self[i + 1] += x

        self[0] += weights[data < low].sum()
        self[-1] += weights[data >= high].sum()

    def __add__(self, other):
        if not isinstance(other, TH1Methods) or self.numbins != other.numbins or self.low != other.low or self.high != other.high:
            raise TypeError("TH1 histograms can only be combined with other TH1 histograms")
        return hist(self.numbins, self.low, self.high, name=(self.name if self.name is not None else other.name), title=(self.title if self.title is not None else other.title), values=[x + y for x, y in zip(self.values, other.values)])

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if not isinstance(other, TH1Methods) or self.numbins != other.numbins or self.low != other.low or self.high != other.high:
            raise TypeError("TH1 histograms can only be combined with other TH1 histograms")
        for i in range(len(self)):
            self[i] = other[i]
        return self

    @property
    def xlabels(self):
        if self.fXaxis.fLabels is None:
            return None
        else:
            return [str(x) for x in self.fXaxis.fLabels]

    def show(self, width=80, minimum=None, maximum=None, stream=sys.stdout):
        if minimum is None:
            minimum = min(self)
            if minimum < 0:
                minimum *= 1.05
            else:
                minimum = 0

        if maximum is None:
            maximum = max(self) * 1.05

        if maximum <= minimum:
            average = (minimum + maximum) / 2.0
            minimum = average - 0.5
            maximum = average + 0.5

        if self.xlabels is None:
            intervals = ["[{0:<.5g}, {1:<.5g})".format(l, h) for l, h in [self.interval(i) for i in range(len(self))]]
            intervals[-1] = intervals[-1][:-1] + "]"   # last interval is closed on top edge
        else:
            intervals = ["(underflow)"] + [self.xlabels[i] if i < len(self.xlabels) else self.interval(i+1) for i in range(self.numbins)] + ["(overflow)"]

        intervalswidth = max(len(x) for x in intervals)

        values = ["{0:<.5g}".format(float(x)) for x in self]
        valueswidth = max(len(x) for x in values)

        minimumtext = "{0:<.5g}".format(minimum)
        maximumtext = "{0:<.5g}".format(maximum)

        plotwidth = max(len(minimumtext) + len(maximumtext), width - (intervalswidth + 1 + valueswidth + 1 + 2))
        scale = minimumtext + " "*(plotwidth + 2 - len(minimumtext) - len(maximumtext)) + maximumtext

        norm = float(plotwidth) / float(maximum - minimum)
        zero = int(round((0.0 - minimum)*norm))
        line = numpy.empty(plotwidth, dtype=numpy.uint8)

        formatter = "{0:<%s} {1:<%s} |{2}|" % (intervalswidth, valueswidth)
        line[:] = ord("-")
        if minimum != 0 and 0 <= zero < plotwidth:
            line[zero] = ord("+")
        capstone = " " * (intervalswidth + 1 + valueswidth + 1) + "+" + str(line.tostring().decode("ascii")) + "+"

        out = [" "*(intervalswidth + valueswidth + 2) + scale]
        out.append(capstone)
        for interval, value, x in zip(intervals, values, self):
            line[:] = ord(" ")

            pos = int(round((x - minimum)*norm))
            if x < 0:
                line[pos:zero] = ord("*")
            else:
                line[zero:pos] = ord("*")

            if minimum != 0 and 0 <= zero < plotwidth:
                line[zero] = ord("|")

            out.append(formatter.format(interval, value, str(line.tostring().decode("ascii"))))

        out.append(capstone)
        out = "\n".join(out)
        if stream is None:
            return out
        else:
            stream.write(out)
            stream.write("\n")

uproot.rootio.methods["TH1"] = TH1Methods

class TH2Methods(TH1Methods):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (TH1Methods.__metaclass__,), {})

    @property
    def numbins(self):
        return self.numXbins * self.numYbins

    @property
    def numXbins(self):
        return self.fXaxis.fNbins

    @property
    def numYbins(self):
        return self.fYaxis.fNbins

    @property
    def low(self):
        return (self.xlow,self.ylow)

    @property
    def high(self):
        return (self.xhigh,self.yhigh)

    @property
    def xlow(self):
        return self.fXaxis.fXmin

    @property
    def xhigh(self):
        return self.fXaxis.fXmax

    @property
    def ylow(self):
        return self.fYaxis.fXmin

    @property
    def yhigh(self):
        return self.fYaxis.fXmax

    @property
    def underflows(self):
        """Underflow values for (x,y) :: xuf[0] == yuf[0] """
        uf = numpy.array(self.allvalues)
        xuf = uf[:,0]
        yuf = uf[0]
        return (xuf,yuf)

    @property
    def overflows(self):
        """Overflow values for (x,y) :: xof[-1] == yof[-1] """
        of = numpy.array(self.allvalues)
        xof = of[:,-1]
        yof = of[-1]
        return (xof,yof)

    @property
    def values(self):
        """Return all values that aren't overflow/underflow"""
        va = numpy.array(self.allvalues)
        va = va[1:self.numYbins+1,1:self.numXbins+1]
        return va.tolist()

    @property
    def allvalues(self):
        """Return all values"""
        v = numpy.array(self[:])
        v = v.reshape( self.numYbins+2,self.numXbins+2 )
        return v.tolist()

    @property
    def numpy(self):
        xlow  = self.xlow
        xhigh = self.xhigh
        xbins = self.fXaxis.fXbins
        if not xbins:
            norm   = (xhigh-xlow) / self.numXbins
            xedges = numpy.array([i*norm + xlow for i in range(self.numXbins + 1)])
        else:
            xedges = numpy.array(xbins)

        ylow  = self.ylow
        yhigh = self.yhigh
        ybins = self.fYaxis.fXbins
        if not ybins:
            norm   = (yhigh-ylow) / self.numYbins
            yedges = numpy.array([i*norm + ylow for i in range(self.numYbins + 1)])
        else:
            yedges = numpy.array(ybins)

        freq = numpy.array(self.values, dtype=self._dtype.newbyteorder("="))

        return freq,(xedges,yedges)


    def interval(self,ind,axis='x'):
        if axis=='x':
            low   = self.xlow
            high  = self.xhigh
            nbins = self.numXbins
            bins  = self.fXaxis.fXbins
        else:
            low   = self.ylow
            high  = self.yhigh
            nbins = self.numYbins
            bins  = self.fYaxis.fXbins

        if ind<0:
            ind += nbins

        if ind==0:
            return (float("-inf"), low)
        elif ind==nbins+2:
            return (high, float("inf"))
        else:
            if not bins:
                norm   = (high-low) / nbins
                xedges = (ind-1)*norm + low, ind*norm + low
            else:
                xedges = bins[ind-1],bins[ind]
            return xedges


    def index(self,data,axis='x'):
        if axis=='x':
            ind = 0
            nbins = self.numXbins
        elif axis=='y':
            ind = 1
            nbins = self.numYbins
        else:
            raise TypeError("Axis must be either 'x' or 'y' to obtain an index.")

        low  = self.low[ind]
        high = self.high[ind]

        if data < low:
            return 0
        elif data >= high:
            return nbins+1
        elif not math.isnan(data):
            return int(math.floor(nbins*(data-low) / (high-low))) + 1

    def fill(self,datumx,datumy):
        self.fillw(datumx,datumy,1.0)

    def fillw(self,datumx,datumy,weight):
        numXbins = self.numXbins
        xlow     = self.xlow
        xhigh    = self.xhigh
        numYbins = self.numYbins
        ylow     = self.ylow
        yhigh    = self.yhigh

        binx = self.index(datumx,'x')    # get the x bin
        biny = self.index(datumy,'y')    # get the y bin

        # translate biny,binx into index for self[index]
        bin = biny*(numXbins+2) + binx
        self[bin] += weight

    def fillall(self,datax,datay):
        self.fillallw(datax,datay,weights=None)

    def fillallw(self,datax,datay,weights):
        xbins    = self.fXaxis.fXbins
        xlow     = self.xlow
        xhigh    = self.xhigh
        ybins    = self.fYaxis.fXbins
        ylow     = self.ylow
        yhigh    = self.yhigh

        if not xbins: xbins = self.numXbins
        if not ybins: ybins = self.numYbins

        if not isinstance(datax, numpy.ndarray):
            datax = numpy.array(datax)
        if not isinstance(datay, numpy.ndarray):
            datay = numpy.array(datay)

        if isinstance(weights, numbers.Real):
            tmp_weight = weights
            weights = numpy.empty_like(datax)
            weights.fill(tmp_weight)            # assign all elements of the array to the initial value

        freq,xedges,yedges = numpy.histogram2d(datax,datay, bins=[xbins,ybins],
                                               range=[[xlow,xhigh],[ylow,yhigh]],
                                               weights=weights, density=False)
        freq = freq.flatten().tolist()
        for i, x in enumerate(freq):
            self[i+1] += x

        # get all values for underflow
        data_xlow = numpy.where(datax<xlow)
        data_ylow = numpy.where(datay<ylow)
        data_low  = numpy.unique(numpy.concatenate((data_xlow,data_ylow),0)) # indices for underflow

        # get all values for overflow
        data_xhigh = numpy.where(datax>xhigh)
        data_yhigh = numpy.where(datax>yhigh)
        data_high  = numpy.unique(numpy.concatenate((data_xhigh,data_yhigh),0)) # indices for overflow

        # put all (unique) underflow and overflow values into an area 
        data_uo    = numpy.unique(numpy.concatenate((data_low,data_high),0)) # indices for under/overflow

        if weights is None:
            for d in data_uo:
                binx = self.index(datax[d],'x')    # get the x bin
                biny = self.index(datay[d],'y')    # get the y bin

                # translate biny,binx into index for self[index]
                bin = biny*(numXbins+2) + binx
                self[bin] += 1
        else:
            for d in data_uo:
                binx = self.index(datax[d],'x')    # get the x bin
                biny = self.index(datay[d],'y')    # get the y bin

                # translate biny,binx into index for self[index]
                bin = biny*(numXbins+2) + binx
                self[bin] += weights[d]

    def __add__(self, other):
        if not isinstance(other, TH2Methods) or self.numbins != other.numbins or self.low != other.low or self.high != other.high:
            raise TypeError("TH2 histograms can only be combined with other similar TH2 histograms")
        return hist(self.numbins, self.low, self.high, name=(self.name if self.name is not None else other.name), title=(self.title if self.title is not None else other.title), values=[x + y for x, y in zip(self.values, other.values)])

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if not isinstance(other, TH2Methods) or self.numbins != other.numbins or self.low != other.low or self.high != other.high:
            raise TypeError("TH2 histograms can only be combined with other similar TH2 histograms")
        for i,s in enumerate(self):
            self[i] = other[i]
        return self


    @property
    def ylabels(self):
        if self.fYaxis.fLabels is None:
            return None
        else:
            return [str(x) for x in self.fYaxis.fLabels]


    def show(self, width=80, minimum=None, maximum=None, stream=sys.stdout):
        if minimum is None:
            minimum = min(self.values)
            if minimum < 0:
                minimum *= 1.05
            else:
                minimum = 0

        if maximum is None:
            maximum = max(self) * 1.05

        if maximum <= minimum:
            average = (minimum + maximum) / 2.0
            minimum = average - 0.5
            maximum = average + 0.5

        minimumtext = "{0:<.5g}".format(minimum)
        maximumtext = "{0:<.5g}".format(maximum)

        # Determine the necessary formatting
        allvals = numpy.array(self.allvalues)
        intervalswidth = 0
        valueswidth    = 0
        all_intervals  = []
        all_values     = []
        for y in allvals:
            if self.xlabels is None:
                intervals = ["[{0:<.5g}, {1:<.5g})".format(l,h) for l,h in [self.interval(i) for i,s in enumerate(y)]]
                intervals[-1] = intervals[-1][:-1] + "]"   # last interval is closed on top edge
            else:
                intervals = ["(underflow)"] + [self.xlabels[i] if i < len(self.xlabels) else self.interval(i+1) for i in range(self.numbins)] + ["(overflow)"]
            tmp_intervalswidth = max(len(x) for x in intervals)
            if tmp_intervalswidth > intervalswidth: intervalswidth = tmp_intervalswidth
            values = ["{0:<.5g}".format(float(x)) for x in y]
            tmp_valueswidth = max(len(x) for x in values)
            if tmp_valueswidth > valueswidth: valueswidth = tmp_valueswidth

            all_intervals.append(intervals)
            all_values.append(values)

        plotwidth = max(len(minimumtext) + len(maximumtext), width - (intervalswidth + 1 + valueswidth + 1 + 2))
        scale = minimumtext + " "*(plotwidth + 2 - len(minimumtext) - len(maximumtext)) + maximumtext
        norm  = float(plotwidth) / float(maximum - minimum)
        zero  = int(round((0.0 - minimum)*norm))
        line  = numpy.empty(plotwidth, dtype=numpy.uint8)

        formatter = "{0:<%s} {1:<%s} |{2}|" % (intervalswidth, valueswidth)
        line[:] = ord("-")
        if minimum != 0 and 0 <= zero < plotwidth:
            line[zero] = ord("+")

        capstone  = " " * (intervalswidth + 1 + valueswidth + 1) + "+" + str(line.tostring().decode("ascii")) + "+"
        out = [" "*(intervalswidth + valueswidth + 2) + scale]
        out.append(capstone)

        # Make the drawing
        for j,y in enumerate(allvals):

            values = all_values[j]
            y_interval = self.interval(j,axis='y')
            y_int_text = " y : [{0:<.5g}, {1:<.5g})".format(y_interval[0],y_interval[1])
            if j==len(allvals)-1:
                y_int_text = y_int_text[:-1]+']'
            out.append( y_int_text )

            for interval,value,x in zip(all_intervals[j], values, y):
                line[:] = ord(" ")

                pos = int(round((x - minimum)*norm))
                if x < 0:
                    line[pos:zero] = ord("*")
                else:
                    line[zero:pos] = ord("*")

                if minimum != 0 and 0 <= zero < plotwidth:
                    line[zero] = ord("|")

                out.append(formatter.format(interval, value, str(line.tostring().decode("ascii"))))

        out.append(capstone)
        out = "\n".join(out)
        if stream is None:
            return out
        else:
            stream.write(out)
            stream.write("\n")






uproot.rootio.methods["TH2"] = TH2Methods

class TH1(TH1Methods, list):
    def _type(self):
        if all(isinstance(x, numbers.Integral) for x in self):
            return int
        elif all(isinstance(x, numbers.Real) for x in self):
            return float
        else:
            raise TypeError("histogram bin values must be integers or floats")

    @property
    def _classname(self):
        if self._type() is int:
            return "TH1I"
        else:
            return "TH1D"

    @property
    def _dtype(self):
        if self._type() is int:
            return numpy.dtype(">i4")
        else:
            return numpy.dtype(">f8")

class TAxis(object):
    _classname = "TAxis"

def hist(numbins, low, high, name=None, title=None, values=None, allvalues=None, filldata=None):
    out = TH1()
    out.fXaxis = TAxis()
    out.fXaxis.fNbins = int(numbins)
    out.fXaxis.fXmin = float(low)
    out.fXaxis.fXmax = float(high)
    out.fName = name
    out.fTitle = title

    if values is None and allvalues is None:
        out.extend([0] * (numbins + 2))

    if values is not None:
        try:
            assert len(values) == numbins and all(isinstance(x, numbers.Real) for x in values)
        except (TypeError, AssertionError):
            raise ValueError("values must be an iterable of numbers with length numbins")
        out.extend([0] + values + [0])

    # allvalues takes precedence
    if allvalues is not None:
        try:
            assert len(allvalues) == numbins + 2 and all(isinstance(x, numbers.Real) for x in allvalues)
        except (TypeError, AssertionError):
            raise ValueError("allvalues must be an iterable of numbers with length numbins")
        out.extend(allvalues)

    # and filldata is accumulated on top of any values/allvalues
    if filldata is not None:
        out.fillall(filldata)

    return out
