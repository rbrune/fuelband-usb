
# requires hidapi:
# https://github.com/trezor/cython-hidapi

import sys
import hid
import time


class Fuelband():
    def __init__(self):

        fuelband_vendor = 0x11ac
        fuelband_product = 0x6565

        try:
            #print('Opening fuelband')
            self.device = hid.device()
            self.device.open(fuelband_vendor, fuelband_product)

            self.device.set_nonblocking(1)

        except IOError as ex:
            print('Error opening fuelband hid device!')
            exit()

        self.log = ''

        self.firmware_version = ''
        self.firmware_version_raw = []
        self.network_version = ''
        self.network_version_raw = []
        self.protocol_version = 'None'
        self.status_bytes = []
        self.model_number = ''
        self.serial_number = ''
        self.hardware_revision = ''



    def print_hex(self, buf, newline=True):
        for i in buf:
            print('%02x ' % i, end='')
        if newline: print('')

    def to_hex(self, buf):
        t_buf = ''
        for i in buf:
            if t_buf != '': t_buf = t_buf + ' '
            t_buf = t_buf + '%02x' % i
        return t_buf


    def print_ascii(self, buf, newline=False):
        for i in buf:
            print('%c' % i, end='')
        if newline: print('')

    def to_ascii(self, buf):
        t_buf = ''
        for i in buf:
            if i != 0x00:
                t_buf = t_buf + '%c' % i
        return t_buf

    def intFromLittleEndian(self, buf):
        t_num = 0
        for i in range(len(buf)):
            t_num += buf[len(buf) - i - 1] * 0xff**i
        return t_num


    def send(self, cmd, verbose=False):

        cmd_prefix = [0x01, len(cmd) + 1, 0x07]
        cmd = cmd_prefix + cmd

        if verbose: self.print_hex(cmd)
        res = self.device.send_feature_report(cmd)
        if res <= 0: print('Error sending feature report')

        #time.sleep(0.05)

        buf = self.device.get_feature_report(0x01, 64)
        if verbose: self.print_hex(buf)

        if len(buf) > 3:
            buf = buf[3:]
        else:
            buf = []
        return buf


    def doVersion(self):
        buf = self.send([0x08])
        if len(buf) != 7:
            print('Error getting firmware version: ', end='')
            self.print_hex(buf)
        else:
            self.firmware_version = '%c%d.%d' % (buf[0], buf[2], buf[1])
            self.firmware_version_raw = buf
            #print('Firmware Version: %c%d.%d (%02x%02x%02x%02x)' % (buf[0], buf[2], buf[1], buf[3], buf[4], buf[5], buf[6]))

    def doNetworkVersion(self):
        buf = self.send([0x06])
        if len(buf) != 2:
            print('Error getting firmware version: ', end='')
            self.print_hex(buf)
        else:
            self.network_version = '%d.%d' % (buf[1], buf[0])
            #print('Network Firmware Version: %d.%d' % (buf[1], buf[0]))

    def protocolVersion(self):
        buf = self.send([0x60])
        if len(buf) > 1:
            print('Error getting protocol version: ', end='')
            self.print_hex(buf)
        if len(buf) == 1:
            self.protocol_version = '%d' % buf[0]
        else:
            self.protocol_version = 'None'

    def doStatus(self):
        buf = self.send([0xdf])
        if len(buf) != 8:
            print('Error getting status: ', end='')
            self.print_hex(buf)
        else:
            self.status_bytes = buf


    def doModelNumber(self):
        buf = self.send([0xe0])
        if len(buf) <= 0:
            print('Error getting model number: ', end='')
            self.print_hex(buf)
        else:
            self.model_number = self.to_ascii(buf)


    def doSerialNumber(self):
        buf = self.send([0xe1])
        if len(buf) <= 0:
            print('Error getting serial number: ', end='')
            self.print_hex(buf)
        else:
            self.serial_number = self.to_ascii(buf)

    def doHWRevision(self):
        buf = self.send([0xe2])
        if len(buf) <= 0:
            print('Error getting hardware revision: ', end='')
            self.print_hex(buf)
        else:
            self.hardware_revision = '%d' % buf[0]

    def doBattery(self):
        buf = self.send([0x13])
        if len(buf) <= 0:
            print('Error getting battery status: ', end='')
            self.print_hex(buf)
        else:
            self.battery_percent = self.intFromLittleEndian(buf[0:1])
            self.battery_mv = self.intFromLittleEndian(buf[2:4])
            if   buf[1] == 0x59:
                self.battery_mode = 'charging'
            elif buf[1] == 0x4e:
                self.battery_mode = 'idle'
            else:
                self.battery_mode = 'unknown %s' % self.to_hex(buf[1])



    def doTimeStampDeviceInit(self):
        buf = self.send([0x42, 0x01])
        self.timestamp_deviceinit_raw = buf[0:4]
        self.timestamp_deviceinit = self.intFromLittleEndian(buf[0:4])

    def doTimeStampAssessmentStart(self):
        buf = self.send([0x42, 0x02])
        self.timestamp_assessmentstart_raw = buf[0:4]
        self.timestamp_assessmentstart = self.intFromLittleEndian(buf[0:4])

    def doTimeStampLastFuelReset(self):
        buf = self.send([0x42, 0x03])
        self.timestamp_lastfuelreset_raw = buf[0:4]
        self.timestamp_lastfuelreset = self.intFromLittleEndian(buf[0:4])

    def doTimeStampLastGoalReset(self):
        buf = self.send([0x42, 0x04])
        self.timestamp_lastgoalreset_raw = buf[0:4]
        self.timestamp_lastgoalreset = self.intFromLittleEndian(buf[0:4])

    def dumpLog(self):

        buf = [0]
        while len(buf) > 0:
            buf = self.send([0xf6, 0x00], False)
            for t_char in buf:
                self.log = self.log + '%c' % t_char


    def dumpMemory(self, command, max_bytes=0xFFFFFF):
        dump = []
        status = 0x01
        offset = [0x00, 0x00, 0x00]
        while status == 0x01:
            buf = self.send(command + offset)
            #self.print_hex(buf)
            status = buf[0]
            offset = buf[1:4]
            dump = dump + buf[4:]
            if len(dump) >= max_bytes: status = 0xFF
            self.print_hex([status] + offset)
        return dump




fb = Fuelband()

if len(sys.argv) > 1:
    if sys.argv[1] == 'log':
        fb.dumpLog()
        print(fb.log)

    elif sys.argv[1] == 'status':
        fb.doVersion()
        print('Firmware version: %s' % fb.firmware_version)
        fb.protocolVersion()
        print('Protocol version: %s' % fb.protocol_version)

        if (fb.protocol_version == 'None') or ('B' in fb.firmware_version):
            print('Fuelband in bootblock!')

        fb.doNetworkVersion()
        print('Network version: %s' % fb.network_version)

        fb.doStatus()
        print('Status bytes: ', end='')
        fb.print_hex(fb.status_bytes)

        fb.doBattery()
        print('Battery status: %d%% charged, %dmV, %s' % (fb.battery_percent, fb.battery_mv, fb.battery_mode))

        fb.doModelNumber()
        print('Model number: %s' % fb.model_number)

        fb.doSerialNumber()
        print('Serial number: %s' % fb.serial_number)

        fb.doHWRevision()
        print('Hardware revision: %s' % fb.hardware_revision)

        fb.doTimeStampDeviceInit()
        print('Timestamp device-init: %d (%s)' % (fb.timestamp_deviceinit, fb.to_hex(fb.timestamp_deviceinit_raw)))

        fb.doTimeStampAssessmentStart()
        print('Timestamp assessment-start: %d (%s)' % (fb.timestamp_assessmentstart, fb.to_hex(fb.timestamp_assessmentstart_raw)))

        fb.doTimeStampLastFuelReset()
        print('Timestamp fuel-reset: %d (%s)' % (fb.timestamp_lastfuelreset, fb.to_hex(fb.timestamp_lastfuelreset_raw)))

        fb.doTimeStampLastGoalReset()
        print('Timestamp goal-reset: %d (%s)' % (fb.timestamp_lastgoalreset, fb.to_hex(fb.timestamp_lastgoalreset_raw)))


    elif sys.argv[1] == 'desktopdata':
        if sys.argv[2] == 'get':
            if len(sys.argv) > 3:
                dump = fb.dumpMemory([0x50, 0x37, 0x36], 280)
                with open(sys.argv[3], "wb") as f:
                    #for t_byte in dump:
                    f.write(bytes(dump))
            #fb.print_hex(dump)
            #fb.print_ascii(dump)



else:
    #buf = fb.send([0xe4, 0x6d, 0x6d, 0x20, 0x6d, 0x00])
    #fb.print_hex(buf)
    #fb.print_ascii(buf, True)
    #fb.doVersion()
    #print(fb.firmware_version)
    #fb.doNetworkVersion()

    # desktop data
    dump = fb.dumpMemory([0x50, 0x37, 0x36], 280)

    # workout data
    #dump = fb.dumpMemory([0x19])

    #dump = fb.dumpMemory([0x54, 0x37, 0x03])
    fb.print_hex(dump)
    fb.print_ascii(dump)
    print('')
    print('%d bytes / %d kb dumped' % (len(dump), len(dump)//1024))


    print('')
    fb.dumpLog()
    fb.print_ascii(fb.log)
