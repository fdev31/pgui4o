import requests
# TODO: find a way to get the x,y,z position of the printer

BABY_STEPS_DELTA = 0.05 # in mm (firmware defaults)
MOVE_DELTA = 5 # in mm (firmware defaults)


class PrintCommands: # controller
    def __init__(self, prefix, api_key, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.base_url = prefix

        self.baby_offset = UnrangedValue('Z')
        self.bed_temp = RangedValue('S', 0, 120)
        self.e_temp = RangedValue('S', 0, 260)
        self.fan_speed = RangedValue('S', 0, 255)
        self.position_x = RangedValue('X', 0, 500)
        self.position_y = RangedValue('Y', 0, 500)
        self.position_z = RangedValue('Z', 0, 500)
        self.position_e = UnrangedValue('E')

        self.paused = False
        self.printing = False
        self.status_text = 'Unknown'

        self.req_opts = dict(headers={'X-Api-Key': api_key})
        self.http = requests # XXX: hack to easily disable http command

    def job(self, **params):
        try:
            d = self.http.post(self.base_url + 'api/job', json=params, **self.req_opts)
        except Exception as e:
            print("Err:", e)
        else:
            if d.status_code != 204:
                print(d.text)

    def fetch_status(self):
        try:
            d = self.http.get(self.base_url + 'api/printer', **self.req_opts).json()
            self.paused = d['state']['flags']['paused']
            self.printing = d['state']['flags']['printing']
            self.status_text = d['state']['text']
            self.temperatures = {
                    'extruder': (d['temperature']['tool0']['actual'], d['temperature']['tool0']['target']),
                    'bed': (d['temperature']['bed']['actual'], d['temperature']['bed']['target']),
                    }
        except Exception as e:
            self.offline = True
            self.temperatures = {
                    'extruder': (0, 0),
                    'bed': (0, 0),
                    }
        else:
            self.offline = False
            self.e_temp.value = int(d['temperature']['tool0']['target']+0.5)
            self.bed_temp.value = int(d['temperature']['bed']['target']+0.5)

        return self.temperatures

    def connect(self):
        d = dict(port=self.port, baudrate=self.baudrate, autoconnect=True, command='connect')
        try:
            r = self.http.post(self.base_url + 'api/connection', json=d, **self.req_opts)
        except Exception as e:
            print(e)

    def printer_command(self, command):
        if isinstance(command, str):
            js = {'command': command}
        else:
            js = {'commands': command}
        r = self.http.post(self.base_url + 'api/printer/command', json=js, **self.req_opts)
        return r.text

    def baby2zoffset(self):
        self.printer_command(['M206 Z%.3f'%(- (self.position_z.value + self.baby_offset.value)), 'M500'])

    def home_z(self):
        self.printer_command(['G28 Z'])
        self.position_z.value = 0
        self.baby_offset.value = 0
        self.paused = False

    def home_xy(self):
        self.printer_command('G28 X Y')
        self.position_x.value = 0
        self.position_y.value = 0
        self.paused = False

    def home(self):
        self.printer_command(['G28', 'G1 X0 Y0 Z0'])
        self.position_x.value = 0
        self.position_y.value = 0
        self.position_z.value = 0
        self.baby_offset.value = 0
        self.paused = False

    def halt(self):
        stop_count = getattr(self, '_stop_cnt', 0)
        if stop_count:
            self.printer_command('M112')
        stop_count += 1
        self._stop_cnt = stop_count

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            self.job(command="pause", action="pause")
        else:
            self.job(command="pause", action="resume")

    def _send_cmd(self, code, value, value_override=None, pfx='M'):
        self.printer_command('%s%d %s%s'%(
            pfx, code,
            value.name, value_override if value_override is not None else value.value))

    def e_temp_up(self):
        if self.e_temp.increment(5):
            self._send_cmd(104, self.e_temp)

    def e_temp_down(self):
        if self.e_temp.decrement(5):
            self._send_cmd(104, self.e_temp)

    def bed_temp_up(self):
        if self.bed_temp.increment(MOVE_DELTA):
            self._send_cmd(140, self.bed_temp)

    def bed_temp_down(self):
        if self.bed_temp.decrement(MOVE_DELTA):
            self._send_cmd(140, self.bed_temp)

    def fan_up(self):
        if self.fan_speed.increment(MOVE_DELTA):
            self._send_cmd(106, self.fan_speed)

    def fan_down(self):
        if self.fan_speed.decrement(MOVE_DELTA):
            self._send_cmd(106, self.fan_speed)

    def e_up(self):
        # Retract move, doesn't "unprint"
        self.printer_command([
            'G91',
            'G1 E%d'%MOVE_DELTA,
            'G90',
            ])

    def e_down(self):
        # extrude
        self.position_e.increment(MOVE_DELTA)
        self.printer_command([
            'G91',
            'G1 E%d'% -MOVE_DELTA,
            'G90',
            ])

    def baby_down(self):
        self.baby_offset.decrement(BABY_STEPS_DELTA)
        self._send_cmd(290, self.baby_offset, value_override=-BABY_STEPS_DELTA)

    def baby_up(self):
        self.baby_offset.increment(BABY_STEPS_DELTA)
        self._send_cmd(290, self.baby_offset, value_override=BABY_STEPS_DELTA)

    def _move(self, axis, value):
        if value < 0:
            r = axis.decrement(-value)
        else:
            r = axis.increment(value)
        if r:
            print(self.printer_command('G1 %s%s'%(axis.name, axis.value)))
        return r

    def z_down_small(self):
        return self._move(self.position_z, -MOVE_DELTA/10.0)

    def z_up_small(self):
        return self._move(self.position_z, MOVE_DELTA/10.0)

    def z_down(self):
        return self._move(self.position_z, -MOVE_DELTA)

    def z_up(self):
        return self._move(self.position_z, MOVE_DELTA)

    def x_down(self):
        return self._move(self.position_x, -MOVE_DELTA)

    def x_up(self):
        return self._move(self.position_x, MOVE_DELTA)

    def y_down(self):
        return self._move(self.position_y, -MOVE_DELTA)

    def y_up(self):
        return self._move(self.position_y, MOVE_DELTA)

    def quit(self):
        return {'quit'}


class UnrangedValue:
    def __init__(self, name, init=0):
        self.name = name
        self.value = init

    def decrement(self, val):
        self.value -= val
        return True

    def increment(self, val):
        self.value += val
        return True

    @property
    def percentage(self):
        return -1.0


class RangedValue:
    def __init__(self, name, min, max, init=0):
        self.name = name
        self.min = min
        self.max = max
        self.value = init

    def decrement(self, val):
        if self.value == self.min:
            return False
        if self.value - val < self.min:
            self.value = self.min
        else:
            self.value -= val
        return True

    def increment(self, val):
        if self.value == self.max:
            return False
        if self.value + val > self.max:
            self.value = self.max
        else:
            self.value += val
        return True

    @property
    def percentage(self):
        return (self.value - self.min) * 100.0 / self.max
