"""This is a (very much WIP) Winterbloom Sol script.

It's meant to enable a user to switch between various modes using
MIDI CC messages. There is a companion max4live application that wraps
all the mode and parameter changes.

TODO: include summary of what everything does...
"""
import winterbloom_sol as sol
from collections import namedtuple

class CV:
    def __init__(self, select_cc):
        self._mode = 1
        self.env = Envelope(n=select_cc)
        self.voct = VOct()
        self.cc = select_cc
    
    @property
    def mode(self):
        if self._mode == 0:
            return self.voct
        if self._mode == 1:
            return self.env
        return self.voct # default to voct if unsupported midi message comes through
        
    @property
    def output(self):
        return self.mode.output

    def tick(self, last, state):
        if int(state.cc(self.cc) * 128) != self._mode:
            self._mode = int(state.cc(self.cc) * 128)
            print(self.mode)
        self.mode.tick(last, state)
    
class VOct:
    def __init__(self):
        self.output = 0

    def tick(self, last, state):
        if state.note:
            self.output = sol.voct(state)

env_ccs = namedtuple('EnvCCs', ['atk', 'dcy', 'sus', 'rel', 'amp'])

class Envelope:
    def __init__(self, n):
        self.adsr = sol.ADSR(
            attack=0.0,   # Seconds
            decay=0.0,    # Seconds
            sustain=0.7,  # Percentage - 0.0 to 1.0
            release=2.0   # Seconds
        )
        self.slew = sol.SlewLimiter(rate=0.09)
        self.cc = env_ccs(n+1, n+2, n+3, n+4, n+5)
        self.amplitude = 8

    def read_ccs(self, last, state):

        if self.changed(last, state, self.cc.amp):
            self.amplitude = state.cc(self.cc.amp) * 8
            print(self.amplitude)

        if self.changed(last, state, self.cc.atk):
            self.adsr.attack = state.cc(self.cc.atk) * 5
            print(self.adsr.attack)

        if self.changed(last, state, self.cc.dcy):
            self.adsr.decay = state.cc(self.cc.dcy) * 5
            print(self.adsr.decay)
        if self.changed(last, state, self.cc.sus):
            self.adsr.sustain = state.cc(self.cc.sus)
            print(self.adsr.sustain)

        if self.changed(last, state, self.cc.rel):
            self.adsr.release = state.cc(self.cc.rel) * 5
            print(self.adsr.release)

    def changed(self, last, state, cc):
        return last.cc(cc) != state.cc(cc)

    def start(self):
        self.adsr.start()

    def stop(self):
        self.adsr.stop()

    def tick(self, last, state):
        self.read_ccs(last, state)

        if sol.was_key_pressed(state):
            self.adsr.start()

        if not state.note:
            self.adsr.stop()

    @property
    def output(self):
        self.slew.target = self.adsr.output * self.amplitude
        # print(self.slew.output)
        return self.slew.output

class Gate:
    def __init__(self, output):
        self.n = output
        self._mode = 1
        self.cc = 80 + output # selector for gate mode
        self._output = output
        self.trigger = Trigger()
        self.clock = MIDIClock(n=output)

    @property
    def mode(self):
        if self._mode == 0:
            return self.trigger
        if self._mode == 1:
            return self.clock
     
    def tick(self, last, state):
        if last.cc(self.cc) != state.cc(self.cc):
            self._mode = int(state.cc(self.cc) * 128)
            print(self._mode)
        self.mode.tick(last, state)
    
    def set_gate(self, outputs):
        self.mode.trigger(outputs, self.n)

class MIDIClock:
    def __init__(self, n):
        self.division = 8
        self.cc = 70 + n
    
    def read_ccs(self, last, state):
        
        if last.cc(self.cc) != state.cc(self.cc) and self.division != int(state.cc(self.cc) * 128):
            self.division = int(state.cc(self.cc) * 128) or 1 # fall through to 1 if 0

    def tick(self, last, state):
        self.read_ccs(last, state)
        self.on = sol.should_trigger_clock(state, self.division)
    
    def trigger(self, outputs, n):
        if self.on:
            outputs.__dict__[f'_gate_{n}_trigger'].trigger(duration_ms=50)

class Trigger:
    def __init__(self):
        self.on = False
    
    def tick(self, last, state):
        if sol.was_key_pressed(state):
            self.on = True
        if not state.note:
            self.on = False
    
    def trigger(self, outputs, n):
        outputs.__dict__[f'_gate_{n}'].value = self.on

CV_A = CV(select_cc=30)
CV_B = CV(select_cc=40)
CV_C = CV(select_cc=50)
CV_D = CV(select_cc=60)

GATE_1 = Gate(1)
GATE_2 = Gate(2)
GATE_3 = Gate(3)
GATE_4 = Gate(4)

def loop(last, state, outputs):
    """The loop is run over and over to process MIDI information
    and translate it to outputs.

    "last" holds the previous state, "state" holds the current state,
    and "outputs" lets you control the output jacks.

    The code currently depends on having a CV or Gate class with multiple modes
    that each implement a "tick" and "trigger" function. 

    "tick" is where you want to implement any CC handling or mode switching, 
    and "trigger" is where you want to set the output for a given gate.
    """
    CV_A.tick(last, state)
    outputs.cv_a = CV_A.output

    CV_B.tick(last, state)
    outputs.cv_b = CV_B.output

    CV_C.tick(last, state)
    outputs.cv_c = CV_C.output

    CV_D.tick(last, state)
    outputs.cv_d = CV_D.output

    GATE_1.tick(last, state)
    GATE_1.set_gate(outputs)

    GATE_2.tick(last, state)
    GATE_2.set_gate(outputs)

    GATE_3.tick(last, state)
    GATE_3.set_gate(outputs)

    GATE_4.tick(last, state)
    GATE_4.set_gate(outputs)

sol.run(loop)