import itertools


class Predicate:

    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        s = 'predicate: ' + self.name
        if self.parameters:
            s += '\n  parameters: ' + str(self.parameters)
        s += '\n'
        return s

    # def __eq__(self, other):
    #     return self.__dict__ == other.__dict__
