#http://python-3-patterns-idioms-test.readthedocs.io/en/latest/StateMachine.html
#http://karn.io/post/163553561848/python-state-machine
#https://github.com/pytransitions/transitions
#https://github.com/reorx/fysom2
#https://www.ibm.com/developerworks/library/l-python-state/index.html
#https://github.com/smontanaro/python-bits/blob/master/fsm.py


class State(object):
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self):
        print('Processing current state:', str(self))

    def on_event(self, event, param = None):
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

class DistSensorErrorState(State):
    """
    State of Sensor in error
    """
    def on_event(self, event,  param = None):
        if event == 'set_level':
            return DistSensorNormalState(param)
        return self

class DistSensorNormalState(State):
    """
    State of Sensor in Level
    """
    _level = 0
    def __init__(self, level = 0):
        super().__init__()
        self._level = level

    def __cmp__(self, other):
        return cmp(self._level, other._level)

    # Necessary when __cmp__ or __eq__ is defined
    # in order to make this class usable as a
    # dictionary key:
    def __hash__(self):
        return self._level

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__ + " # " + str(self._level)
        
    def on_event(self, event,  param = None):
        if event == 'device_error':
            return DistSensorErrorState()
        if (event == 'set_level') and (self._level != param):
            return DistSensorNormalState(param)
        return self

DistSensorNormalState.level_0 = DistSensorNormalState(0)
DistSensorNormalState.level_1 = DistSensorNormalState(1)
DistSensorNormalState.level_2 = DistSensorNormalState(2)



        
        
