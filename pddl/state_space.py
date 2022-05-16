import sys
import pathlib

parent_path = str((pathlib.Path() / "..").resolve().absolute())
if not parent_path in sys.path and parent_path[-18:] == "hr_task_allocation":
    sys.path.append(parent_path)

from importlib import reload
import pddl.action

reload(pddl.action)
from pddl.action import Bin_Action

from heapq import heappush, heappop
import itertools


class State_Space(object):
    """
    """

    def __init__(self, predicates, objects, static_predicates, init_state):
        """
        Arguments:
        - `predicates`:
        - `actions`:
        - `objects`:
        """
        self._predicates = predicates
        self._objects = objects

        count = 0
        predicate_dict = {}
        predicate_variation_dict = {}
        bin2predicate_dict = {}
        for predicate in self._predicates:
            if predicate.name in static_predicates:
                predicate_variation = []
                for init_predicate in init_state:
                    if init_predicate[0] == predicate.name:
                        predicate_dict[init_predicate] = count
                        bin2predicate_dict[1 << count] = init_predicate
                        predicate_variation.append(init_predicate)
                        count += 1
            else:
                args = []
                for parameter in predicate.parameters:
                    args.append(self._objects[parameter[-1]])
                predicate_variation = []
                for comb in itertools.product(*args):
                    comb = (predicate.name,) + comb
                    predicate_dict[comb] = count
                    bin2predicate_dict[1 << count] = comb
                    predicate_variation.append(comb)
                    count += 1
            predicate_variation_dict[predicate] = predicate_variation
        self._state_num = count
        self._predicate_dict = predicate_dict
        self._bin2predicate_dict = bin2predicate_dict
        # print(self._state_num)

    def convert_actions(self, actions):
        bin_actions = []
        for action in actions:
            no_predicate_flg = False
            positive_precondition = 0
            for precondition in list(action.positive_preconditions):
                if precondition in self._predicate_dict:
                    positive_precondition = positive_precondition | (1 << self._predicate_dict[precondition])
                else:
                    no_predicate_flg = True

            negative_precondition = 0
            for precondition in list(action.negative_preconditions):
                if precondition in self._predicate_dict:
                    negative_precondition = negative_precondition | (1 << self._predicate_dict[precondition])
                else:
                    no_predicate_flg = True

            add_effect = 0
            for effect in list(action.add_effects):
                if effect in self._predicate_dict:
                    add_effect = add_effect | (1 << self._predicate_dict[effect])
                else:
                    no_predicate_flg = True

            del_effect = 0
            for effect in list(action.del_effects):
                if effect in self._predicate_dict:
                    del_effect = del_effect | (1 << self._predicate_dict[effect])
                else:
                    no_predicate_flg = True
            if not no_predicate_flg:
                bin_actions.append(Bin_Action(action.name, action.parameters, positive_precondition, negative_precondition, add_effect, del_effect, action.parameter_type, positive_preconditions=action.positive_preconditions, negative_preconditions=action.negative_preconditions, add_effects=action.add_effects, del_effects=action.del_effects))
        return bin_actions

    def get_state(self, positive_predicates, reference_state=0):
        state = reference_state
        for positive_predicate in positive_predicates:
            state = state | (1 << self._predicate_dict[positive_predicate])
        return state

    def is_satisfied(self, state, positive_condition, negative_condition=None):
        if negative_condition:
            if (state & positive_condition) == positive_condition and (~state & negative_condition) == negative_condition:
                return True
            else:
                return False
        else:
            if (state & positive_condition) == positive_condition:
                return True
            else:
                return False

    def apply_effect(self, state, effect, del_effect=None, delete=False):
        if delete:
            state = state & ~effect
        else:
            state = state | effect
        if del_effect:
            state = state & ~del_effect
        return state

    def bin_h(self, actions, state, positive_goal, negative_goal):
        steps = 0
        while steps < 10000:
            if self.is_satisfied(state, positive_goal, negative_goal):
                return steps
            steps += 1
            for action in actions:
                if not self.is_satisfied(state, action._positive_precondition):
                    continue
                state = self.change(state, action._add_effect)
                negative_goal = self.change(negative_goal, action._del_effect, delete=True)
        return float("inf")
