#!/usr/bin/env python
'''
This script demonstrates programming an FPGA and configuring a wideband Pocket correlator using the Python KATCP library along with the katcp_wrapper distributed in the corr package. Designed for use with TUT4 at the 2010 CASPER workshop.
\n\n 
Author: Jason Manley, August 2010.
Modified: May 2012, Medicina; Tyrone van Balla, November 2015
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


katcp_port=7147
bitstream = 'tut4_update.fpg'

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


if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('poco_init.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=(2**28)/1024,
        help='Set the number of vectors to accumulate between dumps. default is (2^28)/1024.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=1000,
        help='Set the digital gain (4bit quantisation scalar). default is 1000.')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-f', '--fpg', dest='fpgfile', type='str', default='',
        help='Specify the bof file to load')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. \nExiting.'
        exit()
    else:
        roach = args[0]

    if opts.fpgfile != '':
        bitstream = opts.fpgfile
    else:
        bitstream = bitstream

try:
    loggers = []
    lh=DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s ... ' %(roach)),
    fpga = casperfpga.katcp_fpga.KatcpFpga(roach)    
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s.\n'%(roach)
        exit_fail()

    print '------------------------'
    print 'Programming FPGA...',
    if not opts.skip:
        sys.stdout.flush()
        fpga.upload_to_ram_and_program(bitstream)
        time.sleep(10)
        print 'done'
    else:
        print 'Skipped.'

    print 'Configuring fft_shift...',
    fpga.write_int('fft_shift',(2**32)-1)
    print 'done'

    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'

    print 'Resetting board, software triggering and resetting error counters...',
    fpga.write_int('ctrl',0) 
    fpga.write_int('ctrl',1<<17) #arm
    fpga.write_int('ctrl',0) 
    fpga.write_int('ctrl',1<<18) #software trigger
    fpga.write_int('ctrl',0) 
    fpga.write_int('ctrl',1<<18) #issue a second trigger
    print 'done'

    #EQ SCALING!
    # writes only occur when the addr line changes value. 
    # write blindly - don't bother checking if write was successful. Trust in TCP!
    print 'Setting gains of all channels on all inputs to %i...'%opts.gain,
    fpga.write_int('quant0_gain',opts.gain) #write the same gain for all inputs, all channels
    fpga.write_int('quant1_gain',opts.gain) #write the same gain for all inputs, all channels
    fpga.write_int('quant2_gain',opts.gain) #write the same gain for all inputs, all channels
    fpga.write_int('quant3_gain',opts.gain) #write the same gain for all inputs, all channels
    for chan in range(1024):
        #print '%i...'%chan,
        sys.stdout.flush()
        for input in range(4):
            fpga.blindwrite('quant%i_addr'%input,struct.pack('>I',chan))
    print 'done'

    print "ok, all set up. Try plotting using poco_plot_autos.py or poco_plot_cross.py"

#    time.sleep(2)
#
#   prev_integration = fpga.read_uint('acc_num')
#   while(1):
#       current_integration = fpga.read_uint('acc_num')
#       diff=current_integration - prev_integration
#       if diff==0:
#           time.sleep(0.01)
#       else:
#           if diff > 1:
#               print 'WARN: We lost %i integrations!'%(current_integration - prev_integration)
#           prev_integration = fpga.read_uint('acc_num')
#           print 'Grabbing integration number %i'%prev_integration
#           
#           if opts.auto:
#               plot_autos()
#           else:
#               plot_cross(opts.cross)
#
except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

