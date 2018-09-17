# http://python-3-patterns-idioms-test.readthedocs.io/en/latest/StateMachine.html
# http://karn.io/post/163553561848/python-state-machine
# https://github.com/pytransitions/transitions
# https://github.com/reorx/fysom2
# https://www.ibm.com/developerworks/library/l-python-state/index.html
# https://github.com/smontanaro/python-bits/blob/master/fsm.py


class State(object):
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self):
        print('Processing current state:', str(self))

    def on_event(self, event, param=None):
        """
        Handle events that are delegated to this State.
        """
        pass

    def __repr__(self):
        """
        Leverages the __str__ method to describe the State.
        """
        return self.__str__()

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__

    def is_error(self):
        pass