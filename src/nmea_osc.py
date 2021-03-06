import pynmea2, serial, os, time, sys, glob, datetime, requests

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

def osc_setup():
    captm = requests.post('http://192.168.43.1:6624/osc/commands/execute', json={
        "name": "camera.setOptions",
        "parameters": {
            "options": {
                "captureMode": "interval",
                "captureInterval": 2
            }
        }
    }, timeout=1)
    print(repr(captm.json()))

    sndset = requests.post('http://192.168.43.1:6624/settings/set', json={
        "parameters": [
            {"_sound": "1"}
        ]
    }, timeout=1)
    print(repr(sndset.json()))

def osc_start_capture():
    captm = requests.post('http://192.168.43.1:6624/osc/commands/execute', json={
        "name": "camera.startCapture"
    }, timeout=1)
    print(repr(captm.json()))

def logfilename():
    now = datetime.datetime.now()
    return 'NMEA_%0.4d-%0.2d-%0.2d_%0.2d-%0.2d-%0.2d.nmea' % \
                (now.year, now.month, now.day,
                 now.hour, now.minute, now.second)

try:
    sent_dtm = False
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

                        if not line.startswith('$G'):
                            continue

                        try:
                            msg = pynmea2.parse(line)
                            print(repr(msg))

                            if isinstance(msg, pynmea2.types.talker.GGA):
                                sys.stderr.write('Coords: lat %.7f, lon %.7f\n' % (msg.latitude, msg.longitude))
                                r = requests.post('http://192.168.43.1:6624/osc/commands/execute', json={
                                    "name": "camera.setOptions",
                                    "parameters": {
                                        "options": {
                                            "gpsInfo": {
                                                "lat": msg.latitude,
                                                "lng": msg.longitude,
                                                "_altitude": 0
                                            }
                                        }
                                    }
                                }, timeout=1)
                                print(repr(r.json()))
                            if isinstance(msg, pynmea2.types.talker.ZDA):
                                dtm = datetime.datetime(msg.year, msg.month, msg.day, hour=msg.timestamp.hour, minute=msg.timestamp.minute, second=msg.timestamp.second, tzinfo=datetime.timezone.utc)
                                oscdtm = dtm.strftime("%Y:%m:%d %H:%M:%S+00:00")
                                sys.stderr.write('Dtm: %s\n' % (dtm.isoformat()))
                                sys.stderr.write('OSC Format: %s\n' % (oscdtm))
                                if not sent_dtm:
                                    sent_dtm = True
                                    r = requests.post('http://192.168.43.1:6624/osc/commands/execute', json={
                                        "name": "camera.setOptions",
                                        "parameters": {
                                            "options": {
                                                "dateTimeZone": oscdtm
                                            }
                                        }
                                    }, timeout=1)
                                    
                                    print(repr(r.json()))

                                    osc_setup()
                                    osc_start_capture()
                        except Exception as e:
                            sys.stderr.write('Exception: %s\n' % (e))
                            pass
            except Exception as e:
                sys.stderr.write('Error reading serial port %s: %s\n' % (type(e).__name__, e))
            except KeyboardInterrupt as e:
                sys.stderr.write('Ctrl-C pressed, exiting log of %s to %s\n' % (port, outfname))

        sys.stderr.write('Scanned all ports, waiting 10 seconds...press Ctrl-C to quit...\n')
        time.sleep(10)
except KeyboardInterrupt:
    sys.stderr.write('Ctrl-C pressed, exiting port scanner\n')