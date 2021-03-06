# -*- coding: utf-8 -*-
"""
Output server for the attodry800's piezos. See the physical manual from the
attodry for more information about how we're communicating with the piezos
and how the piezos work physically. The axes are numeric, with x:1, y:2, z:3.

Created on Tue Dec 29 2020

@author: mccambria

### BEGIN NODE INFO
[info]
name = cryo_piezos
version = 1.0
description =

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 
### END NODE INFO
"""

from labrad.server import LabradServer
from labrad.server import setting
from twisted.internet.defer import ensureDeferred
import socket
import logging
# telnetlib is a package for connecting to networked device over the telnet
# protocol. See the ANC150 section of the cryostat manual for more details on
# this connection
from telnetlib import Telnet  


class CryoPiezos(LabradServer):
    name = 'cryo_piezos'
    pc_name = socket.gethostname()
    logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%y-%m-%d_%H-%M-%S',
                filename='E:/Shared drives/Kolkowitz Lab Group/nvdata/pc_{}/labrad_logging/{}.log'.format(pc_name, name))


    def initServer(self):
        self.task = None
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)


    async def get_config(self):
        p = self.client.registry.packet()
        p.cd('Config')
        p.get('cryo_piezos_ip')
        result = await p.send()
        return result


    def on_get_config(self, config):
        ip_address = config['get']
        # Connect via telnet
        try:
            self.piezos = Telnet(ip_address, 7230)
        except Exception as e:
            logging.debug(e)
            del self.piezos
        # Read until we're prompted for a password
        self.piezos.read_until(b'Authorization code: ')
        # Enter the default password
        self.piezos.write(b'123456\r\n')
        # Read until we're prompted for a command
        self.piezos.read_until(b'> ')
        # Make sure all the axis modes are set to ground, with default 
        # frequency and voltage of 1000 Hz and 30 V
        self.send_cmd_all('setm', 'gnd')
        self.send_cmd_all('setf', 1000)
        self.send_cmd_all('setv', 30)
        # Initialize positions to 0 steps
        self.pos = [0,0,0]
        # Done
        logging.debug('Init complete')


    @setting(2, pos_in_steps='i')
    def write_z(self, c, pos_in_steps):
        """
        Specify the absolute position in steps relative to 0. There will be 
        hysteresis on this value, but it's repeatable enough for the 
        common and important routines (eg optimize)
        """
        
        # Set to step mode
        self.send_cmd('setm', 3, 'stp')
        
        # Calculate the differential number of steps from where we're at
        steps_to_move = pos_in_steps - self.pos[2]
        abs_steps_to_move = abs(steps_to_move)
        if steps_to_move > 0: 
            self.send_cmd('stepu', 3, abs_steps_to_move)
        else:
            self.send_cmd('stepd', 3, abs_steps_to_move)
        self.pos[2] = pos_in_steps
        
        # Set to ground mode once we're done stepping
        self.send_cmd('stepw', 3, 'gnd')
        self.send_cmd('setm', 3, 'gnd')

    
    @setting(6)
    def has_load_z_scan(self, c):
        """Check if the server has a z scan feature"""
        return False

    
    # @setting(3, center='v[]', scan_range='v[]',
    #          num_steps='i', period='i', returns='*v[]')
    # def load_z_scan(self, c, center, scan_range, num_steps, period):
    #     """Load a linear sweep"""

    #     half_scan_range = scan_range / 2
    #     low = center - half_scan_range
    #     high = center + half_scan_range
    #     voltages = numpy.linspace(low, high, num_steps)
    #     # self.load_stream_writer(c, 'ObjectivePiezo-load_z_scan',
    #     #                         voltages, period)
    #     return voltages


    # @setting(4)
    # def set_ground_all(self, c):
    #     """Set the axes to ground mode. Should be done for cooldown/warmup"""
    #     self.send_cmd_all('setm', 'gnd')


    # @setting(5)
    # def set_step_all(self, c):
    #     """Set the axes to step mode. Necessary for positioning"""
    #     self.send_cmd_all('setm', 'stp')
    
            
    def send_cmd(self, cmd, axis, arg=None):
        """
        Set attribute to value for the specified axis. See the manual for 
        command details
        """
        
        # Make sure this is a valid command
        if cmd not in ['setm', 'setf', 'setv', 'seta', 
                       'stepw', 'stepu', 'stepd']:
            msg = 'Attempted to perform invalid command: {}'.format(cmd)
            logging.debug(msg)
            return
        
        # Encode to ascii
        cmd_enc = cmd.encode('ascii')
        axis_enc = str(axis).encode('ascii')
        
        if arg is not None:
            arg_enc = str(arg).encode('ascii')
            self.piezos.write(cmd_enc + b' ' + axis_enc + b' ' + arg_enc + b'\r\n')
        else:
            self.piezos.write(cmd_enc + b' ' + axis_enc + b'\r\n')
        self.piezos.read_until(b'> ')
            
            
    def send_cmd_all(self, cmd, arg=None):
        """Send a command to all three axes"""
        for axis in range(3):
            self.send_cmd(cmd, axis, arg)
        


__server__ = CryoPiezos()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
