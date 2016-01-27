#!/usr/bin/env python
'''
This script demonstrates grabbing data from a wideband Pocket correlator and plotting it using numpy/pylab. Designed for use with TUT4 at the 2009 CASPER workshop.
\n\n 
Author: Jason Manley, August 2009.
Modified: Tyrone van Balla, November 2015
'''

#TODO: add support for coarse delay change
#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level 

import casperfpga
import time
import numpy
import struct
import sys
import logging
import pylab
import matplotlib

katcp_port=7147

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def get_data(baseline):

    acc_n = fpga.read_uint('acc_num')
    print 'Grabbing integration number %i'%acc_n

    #get the data...    
    a_0r=struct.unpack('>512l',fpga.read('dir_x0_%s_real'%baseline,2048,0))
    a_1r=struct.unpack('>512l',fpga.read('dir_x1_%s_real'%baseline,2048,0))
    b_0r=struct.unpack('>512l',fpga.read('dir_x0_%s_real'%baseline,2048,0))
    b_1r=struct.unpack('>512l',fpga.read('dir_x1_%s_real'%baseline,2048,0))
    a_0i=struct.unpack('>512l',fpga.read('dir_x0_%s_imag'%baseline,2048,0))
    a_1i=struct.unpack('>512l',fpga.read('dir_x1_%s_imag'%baseline,2048,0))
    b_0i=struct.unpack('>512l',fpga.read('dir_x0_%s_imag'%baseline,2048,0))
    b_1i=struct.unpack('>512l',fpga.read('dir_x1_%s_imag'%baseline,2048,0))

    interleave_a=[]
    interleave_b=[]

    for i in range(512):
        interleave_a.append(complex(a_0r[i], a_0i[i]))
        interleave_a.append(complex(a_1r[i], a_1i[i]))
        interleave_b.append(complex(b_0r[i], b_0i[i]))
        interleave_b.append(complex(b_1r[i], b_1i[i]))

    return acc_n,interleave_a,interleave_b


def drawDataCallback(baseline):
    matplotlib.pyplot.clf()
    acc_n,interleave_a,interleave_b = get_data(baseline)

    matplotlib.pyplot.subplot(211)
    matplotlib.pyplot.semilogy(numpy.abs(interleave_a))
    matplotlib.pyplot.xlim(0,1024)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.title('Integration number %i \n%s'%(acc_n,baseline))
    matplotlib.pyplot.ylabel('Power (arbitrary units)')

    matplotlib.pyplot.subplot(212)
    matplotlib.pyplot.plot(numpy.unwrap(numpy.angle(interleave_b)))
    matplotlib.pyplot.ylabel('Phase')
    matplotlib.pyplot.ylim(-180,180)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.xlabel('FFT Channel')
    matplotlib.pyplot.xlim(0,1024)

    fig.canvas.manager.window.after(100, drawDataCallback,baseline)

# debug log handler
class DebugLogHandler(logging.Handler):
    """A logger for KATCP tests."""

    def __init__(self,max_len=100):
        """Create a TestLogHandler.
            @param max_len Integer: The maximum number of log entries
                                    to store. After this, will wrap.
        """
        logging.Handler.__init__(self)
        self._max_len = max_len
        self._records = []

    def emit(self, record):
        """Handle the arrival of a log message."""
        if len(self._records) >= self._max_len: self._records.pop(0)
        self._records.append(record)

    def clear(self):
        """Clear the list of remembered logs."""
        self._records = []

    def setMaxLen(self,max_len):
        self._max_len=max_len

    def printMessages(self):
        for i in self._records:
            if i.exc_info:
                print '%s: %s Exception: '%(i.name,i.msg),i.exc_info[0:-1]
            else:    
                if i.levelno < logging.WARNING: 
                    print '%s: %s'%(i.name,i.msg)
                elif (i.levelno >= logging.WARNING) and (i.levelno < logging.ERROR):
                    print '%s: %s'%(i.name,i.msg)
                elif i.levelno >= logging.ERROR: 
                    print '%s: %s'%(i.name,i.msg)
                else:
                    print '%s: %s'%(i.name,i.msg)
#START OF MAIN:

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('poco_plot_cross.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-c', '--cross', dest='cross', type='str',default='ab',
        help='Plot this cross correlation magnitude and phase. default: ab')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. \nExiting.'
        exit()
    else:
        roach = args[0]

    baseline=opts.cross

try:
    loggers = []
    lh=DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s ... '%(roach)),
    fpga = casperfpga.katcp_fpga.KatcpFpga(roach)
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s.\n'%(roach)
        exit_fail()


    # set up the figure with a subplot for each polarisation to be plotted
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(2,1,1)

    # start the process
    fig.canvas.manager.window.after(100, drawDataCallback,baseline)
    matplotlib.pyplot.show()
    print 'Plotting complete. Exiting...'


except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()