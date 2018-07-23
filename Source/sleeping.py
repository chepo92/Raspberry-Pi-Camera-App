from state_machine import State
from state_machine import StateMachine

import time

class MouseState:
    """A simple state machine for keeping track of when the animal is "asleep".

    An object for making spleeping states to use in a state machine.

    Args:
        state: The state that this object represents.
    
    Attributes:
        state: The state that this object represents.
    """
    def __init__(self, state):
        self.state = state

    def __str__(self):
        return self.state

    def __cmp__(self, other):
        return cmp(self.state, other)

    def __hash__(self):
        return hash(self.state)

# Enumerated states of a mouse
MouseState.moving = MouseState('Moving')
MouseState.still = MouseState('Still')


class Awake(State):
    def run(self):
        pass

    def next(self, input):
        if input == MouseState.moving:
            return SleepState.awake
        elif input == MouseState.still:
            SleepState.still.initialize()
            return SleepState.still

class Still(State):
    def initialize(self):
        self._time = time.time()
        
    def run(self):
        pass

    def next(self, input):
        if input == MouseState.moving:
            return SleepState.awake
        elif input == MouseState.still:
            if time.time() - self._time >= 10:
                SleepState.sleeping.initialize()
                return SleepState.sleeping
            else:
                return SleepState.still

class Sleeping(State):
    def initialize(self):
        self._time = time.time()

    def run(self):
        pass

    def next(self, input):
        if input == MouseState.moving:
            return SleepState.awake
        elif input == MouseState.still:
            if time.time() - self._time >= 30:
                SleepState.snooze.initialize()
                return SleepState.snooze
            else:
                return SleepState.sleeping

class Snooze(State):
    def initialize(self):
        self._time = time.time()
        self._has_moved = False
        
    def run(self):
        pass

    def next(self, input):
        if input == MouseState.moving:
            self._has_moved = True
        if time.time() - self._time >= 120 and self._has_moved is True:
            return SleepState.awake
        else:
            return SleepState.snooze
        
class SleepState(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, SleepState.awake)
        
SleepState.awake = Awake()
SleepState.still = Still()
SleepState.sleeping = Sleeping()
SleepState.snooze = Snooze()
