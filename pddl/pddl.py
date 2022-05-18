# -----------------------------------------------
# This file is used to read input files(domain files and problem files).
# -----------------------------------------------
import re
from pddl.action import Action
from pddl.predicate import Predicate
import importlib
import pddl.state_space

importlib.reload(pddl.state_space)
from pddl.state_space import State_Space


class PDDL:
    def __init__(self):
        self.domain_name = 'unknown'
        self.actions = []
        self.formal_actions = []
        self.action_name_dict = {}
        self.predicates = []

        self.problem_name = 'unknown'
        self.objects = dict()
        self.init_state = frozenset()
        self.state = frozenset()
        self.positive_goal = frozenset()
        self.negative_goal = frozenset()

    # ------------------------------------------
    # Read the files, delete comments, translate the arguments into lists.
    # ------------------------------------------

    def read_files(self, filename):
        with open(filename, 'r') as f:
            str = re.sub(r';.*$', '', f.read(), flags=re.MULTILINE).lower()
        stack = []
        lines = []
        for t in re.findall(r'[()]|[^\s()]+', str):
            if t == '(':
                stack.append(lines)
                lines = []
            elif t == ')':
                if stack:
                    l = lines
                    lines = stack.pop()
                    lines.append(l)
                else:
                    raise Exception('Missing open parentheses')
            else:
                lines.append(t)
        if stack:
            raise Exception('Missing close parentheses')
        if len(lines) != 1:
            raise Exception('Wrong expression')
        return lines[0]

    # -----------------------------------------------
    # Read domain file, extract the domain name and actions.
    # -----------------------------------------------
    def read_domain(self, domain_filename):
        files2list = self.read_files(domain_filename)
        if type(files2list) is list:
            while files2list:
                group = files2list.pop(0)
                t = group.pop(0)
                if t == 'domain':
                    self.domain_name = group[0]
                elif t == ':requirements':
                    pass
                elif t == ':predicates':
                    self.read_predicate(group)
                elif t == ':types':
                    pass
                elif t == ':action':
                    self.read_action(group)
                else:
                    print(str(t) + ' could not recognized in domain')
        else:
            raise 'File ' + domain_filename + ' does not match the domain'

    # -----------------------------------------------
    # Read actions, extract their names, parameters,
    # positive preconditions, negative preconditions, positive effects, and negative effects
    # -----------------------------------------------
    def read_action(self, group):
        name = group.pop(0)
        if not type(name) is str:
            raise Exception('Action without name definition')
        for act in self.actions:
            if act.name == name:
                raise Exception('Action ' + name + ' redefined')
        parameters = []
        positive_preconditions = []
        negative_preconditions = []
        add_effects = []
        del_effects = []
        while group:
            t = group.pop(0)
            if t == ':parameters':
                if not type(group) is list:
                    raise Exception('Error with ' + name + ' parameters')
                parameters = []
                p = group.pop(0)
                while p:
                    variable = p.pop(0)
                    if p and p[0] == '-':
                        p.pop(0)
                        parameters.append([variable, p.pop(0)])
                    else:
                        parameters.append([variable, 'object'])
            elif t == ':precondition':
                self.split_propositions(group.pop(0), positive_preconditions, negative_preconditions, name, ' preconditions')
            elif t == ':effect':
                self.split_propositions(group.pop(0), add_effects, del_effects, name, ' effects')
            else:
                print(str(t) + ' is not recognized in action')
        self.actions.append(Action(name, parameters, frozenset(positive_preconditions), frozenset(negative_preconditions), frozenset(add_effects), frozenset(del_effects)))
        self.formal_actions.append(self.actions[-1])
        self.action_name_dict[name] = self.actions[-1]

    # -----------------------------------------------
    # Read predicates, extract their names, parameters
    # -----------------------------------------------
    def read_predicate(self, group):
        for g in group:
            name = g.pop(0)
            if not type(name) is str:
                raise Exception('Predicate without name definition')
            for predicate in self.predicates:
                if predicate.name == name:
                    raise Exception('Predicate ' + name + ' redefined')
            parameters = []
            while g:

                variable = g.pop(0)
                if g and g[0] == '-':
                    g.pop(0)
                    parameters.append([variable, g.pop(0)])
                else:
                    parameters.append([variable, 'object'])
            self.predicates.append(Predicate(name, parameters))

    # -----------------------------------------------
    # Read problem file, extract objects, initial states, and goal states.
    # -----------------------------------------------

    def read_problem(self, problem_filename):
        if isinstance(problem_filename, str):
            files2list = self.read_files(problem_filename)
        elif isinstance(problem_filename, list):
            files2list = problem_filename
        else:
            raise Exception("File type error.")
        while files2list:
            group = files2list.pop(0)
            t = group[0]
            if t == 'problem':
                self.problem_name = group[-1]
            elif t == ':domain':
                pass
            elif t == ':objects':
                group.pop(0)
                object_list = []
                while group:
                    if group[0] == '-':
                        group.pop(0)
                        self.objects[group.pop(0)] = object_list
                        object_list = []
                    else:
                        object_list.append(group.pop(0))

                if object_list:
                    if not 'object' in self.objects:
                        self.objects['object'] = []
                    self.objects['object'] += object_list

            elif t == ':init':
                group.pop(0)
                self.init_state = self.state_to_tuple(group)
                self.state = self.init_state
            elif t == ':goal':
                pos = []
                neg = []
                self.split_propositions(group[1], pos, neg, '', 'goals')
                self.positive_goal = frozenset(pos)
                self.negative_goal = frozenset(neg)
            else:
                print(str(t) + ' could not recognized in problem')

    # -----------------------------------------------
    # Split propositions
    # -----------------------------------------------
    def split_propositions(self, group, pos, neg, name, part):
        """
        get all kinds of candidates
        """
        if not type(group) is list:
            raise Exception('Error with ' + name + part)
        if group[0] == 'and':
            group.pop(0)
        else:
            group = [group]
        for proposition in group:
            if proposition[0] == 'not':
                if len(proposition) != 2:
                    raise Exception('Unexpected not in ' + name + part)
                neg.append(tuple(proposition[-1]))
            else:
                pos.append(tuple(proposition))

    # -----------------------------------------------
    # State to tuple
    # -----------------------------------------------

    def state_to_tuple(self, state):
        return set(tuple(fact) for fact in state)

    def is_satisfied(self, state, positive_condition, negative_condition=None):
        raise Exception("Pleaase define non-binary vertion command.")

    def apply_effect(self, state, effect, del_effect=None, delete=False):
        raise Exception("Pleaase define non-binary vertion command.")

    def add_objects(self, additional_objects_dict):
        for key, value in additional_objects_dict.items():
            self.objects[key] = self.objects[key] + value

    def add_init_state(self, additional_init_state):
        self.init_state = self.init_state | set(additional_init_state)
        self.state = self.init_state


class BinaryPDDL(PDDL):
    def __init__(self):
        super().__init__()
        self.state_space = None
        self._static_predicates = None

        self._original_init_state = None

    def read_problem(self, problem_filename, static_predicates=[]):
        if static_predicates:
            predicate_names = [predicate.name for predicate in self.predicates]
            for static_predicate in static_predicates:
                if not static_predicate in predicate_names:
                    raise Exception("%s is not included in the predicates." % static_predicate)
        self._static_predicates = static_predicates
        if isinstance(problem_filename, str):
            files2list = self.read_files(problem_filename)
        elif isinstance(problem_filename, list):
            files2list = problem_filename
        else:
            raise Exception("File type error.")
        while files2list:
            group = files2list.pop(0)
            t = group[0]
            if t == 'problem':
                self.problem_name = group[-1]
            elif t == ':domain':
                pass
            elif t == ':objects':
                group.pop(0)
                object_list = []
                while group:
                    if group[0] == '-':
                        group.pop(0)
                        self.objects[group.pop(0)] = object_list
                        object_list = []
                    else:
                        object_list.append(group.pop(0))

                if object_list:
                    if not 'object' in self.objects:
                        self.objects['object'] = []
                    self.objects['object'] += object_list

            elif t == ':init':
                group.pop(0)
                self.init_state = self.state_to_tuple(group)
                self.state = self.init_state
            elif t == ':goal':
                pos = []
                neg = []
                self.split_propositions(group[1], pos, neg, '', 'goals')
                self.positive_goal = frozenset(pos)
                self.negative_goal = frozenset(neg)
            else:
                print(str(t) + ' could not recognized in problem')

    def gen_state_space(self):
        self.state_space = State_Space(self.predicates, self.objects, self._static_predicates, self.init_state)
        # self.state_space.gen_actions(self.actions)
        self.state = self.state_space.get_state(list(self.state))
        self._original_init_state = self.init_state
        self.init_state = self.state
        self.positive_goal_list = [self.state_space.get_state((positive_goal,)) for positive_goal in self.positive_goal]
        self.negative_goal_list = [self.state_space.get_state((negative_goal,)) for negative_goal in self.negative_goal]
        self.positive_goal = self.state_space.get_state(list(self.positive_goal))
        self.negative_goal = self.state_space.get_state(list(self.negative_goal))
        self.is_satisfied = self.state_space.is_satisfied
        self.apply_effect = self.state_space.apply_effect

    def gen_actions(self):
        ground_actions = []
        for action in self.actions:
            for act in action.instantiate(self.objects):
                ground_actions.append(act)
        self.actions = self.state_space.convert_actions(ground_actions)

    # def is_satisfied(self, state, positive_condition, negative_condition=None):
    #     return self.state_space.is_satisfied(state, positive_condition, negative_condition)

    # def apply_effect(self, state, effect, del_effect=None, delete=False):
    #     return self.state_space.apply_effect(state, effect, del_effect, delete)


# -----------------------------------------------
# test
# -----------------------------------------------
if __name__ == '__main__':
    domain_SPS = "examples/domain_SPS.pddl"
    problem_SPS = "examples/problem_SPS.pddl"
    readpddl = PDDL()
    readpddl.read_domain(domain_SPS)
    readpddl.read_problem(problem_SPS)
    # print('Domain name:' + readpddl.domain_name)
    # for act in readpddl.actions:
    #     print(act)
    # print('----------------------------')
    # print('Problem name: ' + readpddl.problem_name)
    # print('Objects: ' + str(readpddl.objects))
    # print('State: ' + str(readpddl.state))
    # print('Positive goals: ' + str(readpddl.positive_goal))
    # print('Negative goals: ' + str(readpddl.negative_goal))
    # print('----------------------------')
    #
    # for predicate in readpddl.predicates:
    #     print(predicate)

    # files2list = Gen.add_problem(['assemble', 'p1AB', 'human'], ['pick', 'p5', 'robot'])
    # print(files2list)
    # readpddl = Read_PDDL()
    # readpddl.read_problem(files2list)
