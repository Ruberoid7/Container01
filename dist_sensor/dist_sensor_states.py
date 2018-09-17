from states import State


class DistSensorErrorState(State):
    """
    State of Sensor in error
    """

    def on_event(self, event, param=None):
        if event == 'set_level':
            return DistSensorNormalState.levels[param]
        return self

    def __str__(self):
        return 'Error'

    def is_error(self):
        return True

DistSensorErrorState.error = DistSensorErrorState()

class DistSensorNormalState(State):
    """
    State of Sensor in Level
    """
    _level = 0

    def __init__(self, level=0):
        super().__init__()
        self._level = level

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.level == other.level
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    # Necessary when __cmp__ or __eq__ is defined
    # in order to make this class usable as a
    # dictionary key:
    def __hash__(self):
        return self.level

    def __str__(self):
        """
        Returns the name of the State.
        """
        return 'level {}'.format(self.level)

    @property
    def level(self):
        return self._level

    def is_error(self):
        return False

    def on_event(self, event, param=None):
        if event == 'device_error':
            return DistSensorErrorState.error
        if (event == 'set_level') and (self._level != param):
            return DistSensorNormalState.levels[param]
        return self


DistSensorNormalState.levels = [DistSensorNormalState(0), DistSensorNormalState(1), DistSensorNormalState(2)]

