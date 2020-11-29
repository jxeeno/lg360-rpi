import pynmea2, serial, os, time, sys, glob, datetime

def _scan_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        patterns = ('/dev/tty[A-Za-z]*', '/dev/ttyUSB*')
        ports = [glob.glob(pattern) for pattern in patterns]
        ports = [item for sublist in ports for item in sublist]  # flatten
    elif sys.platform.startswith('darwin'):
        patterns = ('/dev/*serial*', '/dev/ttyUSB*', '/dev/ttyS*')
        ports = [glob.glob(pattern) for pattern in patterns]
        ports = [item for sublist in ports for item in sublist]  # flatten
    else:
        raise EnvironmentError('Unsupported platform')
    return ports

_scan_ports()

def logfilename():
    now = datetime.datetime.now()
    return 'NMEA_%0.4d-%0.2d-%0.2d_%0.2d-%0.2d-%0.2d.nmea' % \
                (now.year, now.month, now.day,
                 now.hour, now.minute, now.second)

try:
    while True:
        ports = ['/dev/ttyACM0'] # _scan_ports()
        if len(ports) == 0:
            sys.stderr.write('No ports found, waiting 10 seconds...press Ctrl-C to quit...\n')
            time.sleep(10)
            continue

        for port in ports:
            # try to open serial port
            sys.stderr.write('Trying port %s\n' % port)
            try:
                # try to read a line of data from the serial port and parse
                with serial.Serial(port, 4800, timeout=1) as ser:
                    # try to parse (will throw an exception if input is not valid NMEA)
                    while True:
                        line = ser.readline().decode('ascii', errors='replace')

                        if not line.startswith('$'):
                            continue

                        try:
                            msg = pynmea2.parse(line)
                            print(repr(msg))

                            if isinstance(msg, pynmea2.types.talker.GGA):
                                sys.stderr.write('Coords: lat %.7f, lon %.7f\n' % (msg.latitude, msg.longitude))
                            if isinstance(msg, pynmea2.types.talker.ZDA):
                                dtm = datetime.datetime(msg.year, msg.month, msg.day, hour=msg.timestamp.hour, minute=msg.timestamp.minute, second=msg.timestamp.second, microsecond=msg.timestamp.microsecond, tzinfo=timezone.utc)
                                sys.stderr.write('Dtm: %s\n' % (dtm.isoformat()))
                        except Exception as e:
                            pass
            except Exception as e:
                sys.stderr.write('Error reading serial port %s: %s\n' % (type(e).__name__, e))
            except KeyboardInterrupt as e:
                sys.stderr.write('Ctrl-C pressed, exiting log of %s to %s\n' % (port, outfname))

        sys.stderr.write('Scanned all ports, waiting 10 seconds...press Ctrl-C to quit...\n')
        time.sleep(10)
except KeyboardInterrupt:
    sys.stderr.write('Ctrl-C pressed, exiting port scanner\n')