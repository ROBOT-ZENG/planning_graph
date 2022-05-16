# -----------------------------------------------
# This file is used to generate all candidate actions.
# Return candidate actions with their names, parameters, preconditions, and effects.
# -----------------------------------------------
import itertools


class Bin_Action(object):
    """
    """

    def __init__(self, name="none", parameters=None, positive_precondition=None, negative_precondition=None, add_effect=None, del_effect=None, parameter_type=None, positive_preconditions=None, negative_preconditions=None, add_effects=None, del_effects=None):
        """
        
        Arguments:
        - `name`:
        - `parameter`:
        - `positive_precondition`:
        - `negative_precondition`:
        
        """
        self.name = name
        self.parameters = parameters
        self._positive_precondition = positive_precondition
        self._negative_precondition = negative_precondition
        self._add_effect = add_effect
        self._del_effect = del_effect
        self.positive_preconditions = positive_preconditions
        self.negative_preconditions = negative_preconditions
        self.add_effects = add_effects
        self.del_effects = del_effects
        self._parameter_type = parameter_type
        self.p_variable_dict = {}
        self.p_type_dict = {}
        self.variables = []
        if parameter_type:
            for p, pt in zip(parameters, parameter_type):
                pt = tuple(pt)
                if pt[1] in self.p_type_dict:
                    self.p_type_dict[pt[1]].append(p)
                else:
                    self.p_type_dict[pt[1]] = [p, ]
                self.p_variable_dict[pt[0]] = p
                self.variables.append(pt[0])

    def __str__(self):
        # s = 'action: ' + self.name
        # if self.parameters:
        #     s += '\n  parameters: ' + str(self.parameters)
        # if self._parameter_type:
        #     s += '\n  type: ' + str(self._parameter_type)
        # s += '\n'
        # return s[:-1]
        return 'action: ' + self.name + str(self.parameters)

    def __lt__(self, other):
        return self.name < other.name

    def can_precede(self, other):
        # if pre(a) has predicate A, and A also belongs to the eff(b), if a precede b, logic error
        condition1 = not (other._add_effect & self._positive_precondition)
        condition2 = not (other._del_effect & self._negative_precondition)
        condition3 = not (self._add_effect & other._negative_precondition)
        condition4 = not (self._del_effect & other._positive_precondition)
        return all((condition1, condition2, condition3, condition4))


class Action:

    def __init__(self, name, parameters, positive_preconditions, negative_preconditions, add_effects, del_effects, parameter_type=None):
        self.name = name
        self.parameters = parameters
        self.positive_preconditions = positive_preconditions
        self.negative_preconditions = negative_preconditions
        self.add_effects = add_effects
        self.del_effects = del_effects
        self.parameter_type = parameter_type
        self.p_type_dict = {}
        if parameter_type:
            for p, pt in zip(parameters, parameter_type):
                pt = tuple(pt)
                if pt in self.p_type_dict:
                    self.p_type_dict[pt].append(p)
                else:
                    self.p_type_dict[pt] = [p, ]

    def __str__(self):
        s = 'action: ' + self.name
        if self.parameters:
            s += '\n  parameters: ' + str(self.parameters)
        if self.positive_preconditions:
            s += '\n  positive_preconditions: ' + str(list(self.positive_preconditions))
        if self.negative_preconditions:
            s += '\n  negative_preconditions: ' + str(list(self.negative_preconditions))
        if self.add_effects:
            s += '\n  add_effects: ' + str(list(self.add_effects))
        if self.del_effects:
            s += '\n  del_effects: ' + str(list(self.del_effects))
        s += '\n'
        return s

    # def __eq__(self, other):
    #     return self.__dict__ == other.__dict__

    def instantiate(self, objects):
        if not self.parameters:
            yield self
            return
        type_map = []
        variables = []
        for var, typ in self.parameters:
            type_map.append(objects[typ])
            variables.append(var)
        for assignment in itertools.product(*type_map):
            positive_preconditions = self.replace(self.positive_preconditions, variables, assignment)
            negative_preconditions = self.replace(self.negative_preconditions, variables, assignment)
            add_effects = self.replace(self.add_effects, variables, assignment)
            del_effects = self.replace(self.del_effects, variables, assignment)
            yield Action(self.name, assignment, positive_preconditions, negative_preconditions, add_effects, del_effects, self.parameters)

    def replace(self, group, variables, assignment):
        g = []
        for pred in group:
            a = pred
            iv = 0
            for v in variables:
                while v in a:
                    i = a.index(v)
                    a = a[:i] + tuple([assignment[iv]]) + a[i + 1:]
                iv += 1
            g.append(a)
        return frozenset(g)

    def substitute(self, parameters):
        arg_dict = {}
        for variable, parameter in zip(self.parameters, parameters):
            arg_dict[variable[0]] = parameter
        positive_preconditions = []
        for p_precon in self.positive_preconditions:
            positive_preconditions.append(tuple([p_precon[0]] + [arg_dict[predicate] for predicate in p_precon[1:]]))
        negative_preconditions = []
        for n_precon in self.negative_preconditions:
            negative_preconditions.append(tuple([n_precon[0]] + [arg_dict[predicate] for predicate in n_precon[1:]]))
        add_effects = []
        for add_effect in self.add_effects:
            add_effects.append(tuple([add_effect[0]] + [arg_dict[predicate] for predicate in add_effect[1:]]))
        del_effects = []
        for del_effect in self.del_effects:
            del_effects.append(tuple([del_effect[0]] + [arg_dict[predicate] for predicate in del_effect[1:]]))
        return Action(self.name, parameters, frozenset(positive_preconditions), frozenset(negative_preconditions), frozenset(add_effects), frozenset(del_effects), self.parameters)


# -----------------------------------------------
# test
# -----------------------------------------------
if __name__ == '__main__':
    a = Action('move', [['?ag', 'agent'], ['?from', 'pos'], ['?to', 'pos']],
               frozenset([tuple(['at', '?ag', '?from']), tuple(['adjacent', '?from', '?to'])]),
               frozenset([tuple(['at', '?ag', '?to'])]),
               frozenset([tuple(['at', '?ag', '?to'])]),
               frozenset([tuple(['at', '?ag', '?from'])])
               )
    print(a)

    objects = {
        'agent': ['worker1', 'worker2'],
        'pos': ['p1', 'p2']
    }
    for act in a.instantiate(objects):
        print(act)
