# This module provides a class that controls the serial servomotor manufactured by Pirkus.Inc
# Update 19/11/2012
# This module has been tested on python ver.2.6.6
# It is coded according to a PRS-DE07MS / PRS-S40M manual 4th edition.
# pySerial(http://pyserial.sourceforge.net/) is need to use.
# Please see the manual for how to use each of the methods and procedures.
# (C) 2012 Hiroaki Matsuda

import serial

class Prs(object):

        def __init__(self):
                self.myserial = serial.Serial()
                print('Generated the serial object')
	
        def open_port(self, port = 'COM1', baudrate = 115200, timeout = 1):
                self.myserial.port = port
                self.myserial.baudrate = baudrate
                self.myserial.timeout = timeout	
                try:
                        self.myserial.open()
                except IOError:
                        print('Failed to open port, check the device and port number')
                else:
                        print('Succeede to open port: ' + port)

        def close_port(self):
                self.myserial.close()

        def set_port(self, baudrate = 115200, timeout = 1):
                self.myserial.baudrate = baudrate
                self.myserial.timeout = timeout
                self.myserial._reconfigurePort()
                print('Succeede to set baudrate:%d, timeout:%d' %(baudrate, timeout)) 

# Read & Write Command

        def write_protect(self, id, command = 'unlock'):
                self._check_range(id, 0, 253, 'id')
                self._check_command(command, 'lock', 'unlock')

                if command is 'lock':
                        send = [id, 0x81, 0x55]
                        
                elif command is 'unlock':
                        send = [id, 0x81, 0xAA]

                send.append(self._calc_checksum(send)) 
                self._write_command(send)
                return self._check_ack(id)

        def offset_lock(self, id, command = 'unlock'):
                self._check_range(id, 0, 253, 'id')
                self._check_command(command, 'lock', 'unlock')

                if command is 'lock':
                        send = [id, 0x82, 0x55]
                        
                elif command is 'unlock':
                        send = [id, 0x82, 0xAA]

                send.append(self._calc_checksum(send)) 
                self._write_command(send)
                return self._check_ack(id)

        def version(self, id):
                self._check_range(id, 0, 253, 'id')
                
                send = [id, 0x03]    
                send.append(self._calc_checksum(send)) 
                self._write_command(send)
                return self._return_data(id, 4, command)

        def product_number(self, id):
                self._check_range(id, 0, 253, 'id')
                
                send = [id, 0x04]    
                send.append(self._calc_checksum(send)) 
                self._write_command(send)
                return self._return_data(id, 4, command)

        def status(self, id):
                self._check_range(id, 0, 253, 'id')
                
                send = [id, 0x05]
                self._write_command(send)
                receive = self._read_data(id, 4)
                
                if receive[1] is 'unReadable':
                        return id, 'unReadable'

                else:
                        data_binary = format(receive[1], 'b')
                        data_length = len(data_binary)
                        data_temp = ['0', '0', '0', '0', '0', '0', '0', '0']
                        for i in range(data_length):
                                data_temp[i + (8 - data_length)] = data_binary[i]
                                
                        data = []
                        if data_temp[7] is '0':
                                data.append('ServoOFF')
                        elif data_temp[7] is '1':
                                data.append('ServoON')
                        if data_temp[5] is '0':
                                data.append('SetNormal')
                        elif data_temp[5] is '1':
                                data.append('SetReverse')
                        if data_temp[4] is '0':
                                data.append('Normal')
                        elif data_temp[4] is '1':
                                data.append('Reverse')
                        if data_temp[3] is '0':
                                data.append('PID')
                        elif data_temp[3] is '1':
                                data.append('Digital')
                        if data_temp[1] is '0':
                                data.append('Unlimited')
                        elif data_temp[1] is '1':
                                data.append('Limited')
                        if data_temp[0] is '0':
                                data.append('Unlocked')
                        elif data_temp[0] is '1':
                                data.append('Locked')

                        return receive[0], data

        def id(self, id, new_id = 1, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_command(command, 'write', 'read')

                if command is 'read':
                        send = [id, 0x41]

                elif command is 'write':
                        send = [id, 0xC1, new_id]
                        send.append(self._calc_checksum(send))	

                self._write_command(send)
                return self._return_data(id, 4, command)

        def baudrate(self, id, baudrate = 115200, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_command(command, 'write', 'read', 'list')

                baudrate_dict = {4800:0, 9600:1, 19200:3, 38400:7, 57600:11, 115200:23,
                                384000:79, 624000:135, 1224000:254, 1250000:255}
                
                if baudrate not in baudrate_dict.keys():
                        list = baudrate_dict.keys()
                        list.sort()
                        raise ValueError('Value of the baudrate, select from the list below\n'
                                         + str(list))

                if command is 'list':
                        list = baudrate_dict.keys()
                        return list.sort()
                
                elif command is 'read':
                        send = [id, 0x42]
                        receive = self._read_data(id, 4)
                        self._write_command(send)
                        
                        if receive[1] is 'unReadable':
                                return id, 'unReadable'

                        else:
                                baudrate_dict = {0:4800, 1:9600, 3:19200, 7:38400, 11:57600, 23:115200,
                                        79:384000, 135:624000, 254:1224000, 255:1250000}
                                return receive[0], baudrate_dict[receive[1]]
                                
                elif command is 'write':
                        send = [id, 0xC2, baudrate_dict[baudrate]]
                        send.append(self._calc_checksum(send))
                        self._write_command(send)

        #If baudrate of the servo is change, return value will be unreadable.
        #The success or failure of rewriting, please check after changing the baudrate of the port.

                        return id, 'commandSent'

        def duty_offset(self, id, offset = 0, command = 'write'):
                self._check_range(id  , 0, 253, 'id')
                self._check_range(offset, 0, 255, 'offset')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x4F]

                elif command is 'write' or 'pass':
                        send = [id, 0xCF, offset]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 4, command)

        def d_gain(self, id, gain = 0, command = 'write'):
                self._check_range(id  , 0, 253, 'id')
                self._check_range(gain, 0, 255, 'gain')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x50]

                elif command is 'write' or 'pass':
                        send = [id, 0xD0, gain]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 4, command)

        def i_gain(self, id, gain = 0, command = 'write'):
                self._check_range(id  , 0, 253, 'id')
                self._check_range(gain, 0, 255, 'gain')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x51]

                elif command is 'write' or 'pass':
                        send = [id, 0xD1, gain]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 4, command)
                
        def p_gain(self, id, gain = 0, command = 'write'):
                self._check_range(id  , 0, 253, 'id')
                self._check_range(gain, 0, 255, 'gain')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x52]

                elif command is 'write' or 'pass':
                        send = [id, 0xD2, gain]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 4, command)
        
        def current_position(self, id):
                self._check_range(id, 0, 253, 'id')
                
                send = [id, 0x55]
                self._write_command(send)
                return self._read_data(id, 5)
                
        def temperature(self, id):
                self._check_range(id, 0, 253, 'id')
                
                send = [id, 0x56]
                self._write_command(send)
                return self._read_data(id, 5)

        def deadband(self, id, deadband = 0, command = 'write'):
                self._check_range(id      , 0, 253, 'id')
                self._check_range(deadband, 0, 900, 'deadBand')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x61]

                elif command is 'write' or 'pass':
                        send = [id, 0xE1, deadband >> 8, deadband & 0x00FF]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 5, command)
                
        def duty_limit(self, id, limit = 0, command = 'write'):
                self._check_range(id   , 0, 253 , 'id')
                self._check_range(limit, 0, 1000, 'limit')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x63]

                elif command is 'write' or 'pass':
                        send = [id, 0xE3, limit >> 8, limit & 0x00FF]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 5, command)

        def target_position(self, id, position = 900, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_range(position, -3600, 3600, 'position')
                self._check_command(command, 'write', 'read', 'pass')

                if command is 'read':
                        send = [id, 0x64]

                elif command is 'write' or 'pass':
                        send = self._set_send_position(id, 0xE4, position)

                self._write_command(send)
                return self._return_data(id, 5, command)

        def position_limiti_min(self, id, position = 900, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_range(position, -3600, 3600, 'position')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x65]

                elif command is 'write' or 'pass':
                        send = self._set_send_position(id, 0xE5, position)

                self._write_command(send)
                return self._return_data(id, 5, command)

        def initial_position(self, id, position = 900, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_range(position, -3600, 3600, 'position')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x66]

                elif command is 'write' or 'pass':
                        send = self._set_send_position(id, 0xE6, position)

                self._write_command(send)
                return self._return_data(id, 5, command)

        def set_target_position(self, id, position = 900, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_range(position, -3600, 3600, 'position')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x67]

                elif command is 'write' or 'pass':
                        send = self._set_send_position(id, 0xE7, position)	

                self._write_command(send)
                return self._return_data(id, 5, command)

        def offset_position(self, id, position = 900, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_range(position, 0, 2500, 'position')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x68]

                elif command is 'write' or 'pass':
                        send = [id, 0xE8, position >> 8, position & 0x00FF]
                        send.append(self._calc_checksum(send))	

                self._write_command(send)
                return self._return_data(id, 5, command)

        def i_limit(self, id, limit = 120, command = 'write'):
                self._check_range(id   , 0, 253 , 'id')
                self._check_range(limit, 0, 1225, 'limit')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x69]

                elif command is 'write' or 'pass':
                        send = [id, 0x69, limit >> 8, limit & 0x00FF]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 5, command)

        def speed_limit(self, id, limit = 120, command = 'write'):
                self._check_range(id   , 0 , 253 , 'id')
                self._check_range(limit, 31, 6018, 'limit')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x6A]

                elif command is 'write' or 'pass':
                        send = [id, 0xEA, limit >> 8, limit & 0x00FF]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 5, command)

        def acceleration_limit(self, id, limit = 6014, command = 'write'):
                self._check_range(id   , 0 , 253 , 'id')
                self._check_range(limit, 31, 6018, 'limit')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x6B]

                elif command is 'write' or 'pass':
                        send = [id, 0xEB, limit >> 8, limit & 0x00FF]
                        send.append(self._calc_checksum(send))

                self._write_command(send)
                return self._return_data(id, 5, command)

        def position_limiti_max(self, id, position = 900, command = 'write'):
                self._check_range(id, 0, 253, 'id')
                self._check_range(position, -3600, 3600, 'position')
                self._check_command(command, 'write', 'read', 'pass')
                
                if command is 'read':
                        send = [id, 0x75]

                elif command is 'write' or 'pass':
                        send = self._set_send_position(id, 0xF5, position)	

                self._write_command(send)
                return self._return_data(id, 5, command)

# Execute Command

        def reverse_change(self, id):
                self._check_range(id  , 0, 253, 'id')
               
                send = [id, 0x20]
                self._write_command(send)
                return self._check_ack(id)

        def digital_servo_mode(self, id):
                self._check_range(id  , 0, 253, 'id')

                send = [id, 0x21]
                self._write_command(send)
                return self._check_ack(id)

        def pid_mode(self, id):
                self._check_range(id  , 0, 253, 'id')

                send = [id, 0x22]
                self._write_command(send)
                return self._check_ack(id)

        def home_position(self, id, command = 'write'):
                self._check_range(id  , 0, 254, 'id')
                self._check_command(command, 'write', 'pass')

                send = [id, 0x53]
                self._write_command(send)
                return self._return_all_execute_command(id, command)

        def rom_initialize(self, id):
                self._check_range(id  , 0, 253, 'id')
                
                send = [id, 0x54]
                self._write_command(send)
                return self._check_ack(id)

        def rom_save(self, id):
                self._check_range(id, 0, 253, 'id')
                                
                send = [id, 0x57]
                self._write_command(send)
                return self._check_ack(id)

        def servo_move(self, id, command = 'write'):
                self._check_range(id, 0, 254, 'id')
                self._check_command(command, 'write', 'pass')
                
                send = [id, 0x58]
                self._write_command(send)
                return self._return_all_execute_command(id, command)

        def servo_on(self, id = 0xFE, command = 'write'):
                self._check_range(id, 0, 254, 'id')
                self._check_command(command, 'write', 'pass')
                
                send = [id, 0x59]
                self._write_command(send)
                return self._return_all_execute_command(id, command)
                
        def servo_off(self, id = 0xFE, command = 'write'):
                self._check_range(id, 0, 254, 'id')
                self._check_command(command, 'write', 'pass')

                send = [id, 0x5A]
                self._write_command(send)
                return self._return_all_execute_command(id, command)
                
# The following functions are provided for use in Prs class
        
        def _calc_checksum(self, send):
                checksum = 0
                for i in range(len(send)):
                                checksum += send[i]               
                checksum &= 0xFF
                return checksum

        def _set_send_position(self, id, cmd, position):
                send = [id, cmd]
                if position >= 0:
                        send.append(position >> 8)
                        send.append(position & 0x00FF)

                elif position < 0:
                        send.append((-position ^ 0xFFFF) + 1 >> 8)
                        send.append(((-position ^ 0xFFFF) + 1)  & 0x00FF)
                        
                send.append(self._calc_checksum(send))
                return send

        def _write_command(self, send):
                self.myserial.flushOutput()
                self.myserial.flushInput()
                
                self.myserial.parity = serial.PARITY_MARK
                self.myserial._reconfigurePort()
                self.myserial.write(bytearray([send[0]]))
                self.myserial.parity = serial.PARITY_SPACE
                self.myserial._reconfigurePort()
                self.myserial.write(bytearray(send[1:]))

        def _read_data(self, id, data_length):
                receive = self.myserial.read(data_length)
                length = len(receive)

                if length == data_length:
                        if data_length == 4:
                                return ord(receive[0]), ord(receive[2])

                        elif data_length == 5:
                                data = (ord(receive[2]) << 8) | ord(receive[3])
                                if data > 3600:
                                        data = -((data - 1) ^ 0xFFFF)
                                return ord(receive[0]), data

                elif length != data_length:
                        return id, 'unReadable'

        def _check_ack(self, id):
                receive = self.myserial.read(2)
                length = len(receive)
                
                if length == 2:
                        ack = ord(receive[1])
                        if ack == 0x06:
                                return ord(receive[0]), 'ACK'
                        elif ack == 0x15:
                                return ord(receive[0]), 'NACK'
                        else:
                                return ord(receive[0]), 'unKnown'
                elif length != 2:
                        return id, 'unReadable'

        def _return_data(self, id, data_length, command):
                if command is 'pass': 
                        return id, 'pass'
                                
                elif command is 'read':
                        return self._read_data(id, data_length)
                        
                elif command is 'write':
                        return self._check_ack(id)

        def _return_all_execute_command(self, id, command):
                if id is 0xFE:
                        return id, 'all'

                else:
                        return self._return_data(id, 0, command)

        def _check_command(self, command, *command_set):
                if command not in command_set:
                        raise ValueError('command must be choose in' + repr(command_set))
                                
        def _check_range(self, value, lower_range, upper_range, name = 'value'):
                if value < lower_range or value > upper_range:
                        raise ValueError(name + ' must be set in the range from ' + str(lower_range) + ' to ' + str(upper_range))
