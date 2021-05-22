class StateMachine:
    """A generic state machine to run through states.

    Args:
        initial_state: The initial state object to start on.

    Attributes:
        current_state: The current state that the state machine is on.
    """
    def __init__(self, initial_state):
        self.current_state = initial_state
        self.current_state.run()

    def run(self, input):
        self.current_state = self.current_state.next(input)
        self.current_state.run()
        
    def run_all(self, inputs):
        """Runs a list of inputs in succession"""
        for i in inputs:
            self.run(i)
            
class State:
    """An abstract base class that helps describe classes that inherit from it.
    """
    def run(self):
        assert 0

    def next(self, input):
        assert 0
