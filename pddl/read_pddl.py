# -----------------------------------------------
# This file is used to read input files(domain files and problem files).
# -----------------------------------------------
import re
from pddl.action import Action
from pddl.predicate import Predicate


# import pddl.add_state

class Read_PDDL:

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
            self.domain_name = 'unknown'
            self.actions = []
            self.predicates = []
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
        self.actions.append(
            Action(name, parameters, frozenset(positive_preconditions), frozenset(negative_preconditions),
                   frozenset(add_effects), frozenset(del_effects)))

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

        # def read_problem(self, problem_filename):
        if isinstance(problem_filename, str):
            files2list = self.read_files(problem_filename)
        elif isinstance(problem_filename, list):
            files2list = problem_filename
        else:
            raise Exception("File type error.")
        # Gen =Generator.Generator()
        # files2list = Gen.add_problem(action1,action2)

        self.problem_name = 'unknown'
        self.objects = dict()
        self.state = frozenset()
        self.positive_goals = frozenset()
        self.negative_goals = frozenset()
        while files2list:
            group = files2list.pop(0)
            t = group[0]
            if t == 'problem':
                self.problem_name = group[-1]
            elif t == ':domain':
                pass
                # if self.domain_name != group[-1]:
                #     raise Exception('Different domain specified in problem file')
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
                # self.objects['location'].append('l100')
                # print('object_list is:', self.objects['location'])

                if object_list:
                    if not 'object' in self.objects:
                        self.objects['object'] = []
                    self.objects['object'] += object_list

            elif t == ':init':
                group.pop(0)
                self.state = self.state_to_tuple(group)
            elif t == ':goal':
                pos = []
                neg = []
                self.split_propositions(group[1], pos, neg, '', 'goals')
                self.positive_goals = frozenset(pos)
                # print(self.positive_goals)
                self.negative_goals = frozenset(neg)

                # l = pddl.add_state.add_initial(pos[0])
                #
                # self.objects['location'].append(l[0][0])
                # self.objects['part'].append(l[1][0])
                # self.objects['switch'].append(l[2][0])
                #
                # state_begin = tuple(self.state) + tuple(l[3])
                # print('adding', set(state_begin))
                # print('object_list is:', self.objects)
            else:
                print(str(t) + ' could not recognized in problem')

    # -----------------------------------------------
    # Split propositions
    # -----------------------------------------------

    def split_propositions(self, group, pos, neg, name, part):
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


# -----------------------------------------------
# test
# -----------------------------------------------
if __name__ == '__main__':
    # domain_SPS = "examples/domain_SPS.pddl"
    # problem_SPS = "examples/problem_SPS.pddl"
    # readpddl = Read_PDDL()
    # readpddl.read_domain(domain_SPS)
    # readpddl.read_problem(problem_SPS)
    # print('Domain name:' + readpddl.domain_name)
    # for act in readpddl.actions:
    #     print(act)
    # print('----------------------------')
    # print('Problem name: ' + readpddl.problem_name)
    # print('Objects: ' + str(readpddl.objects))
    # print('State: ' + str(readpddl.state))
    # print('Positive goals: ' + str(readpddl.positive_goals))
    # print('Negative goals: ' + str(readpddl.negative_goals))
    # print('----------------------------')
    #
    # for predicate in readpddl.predicates:
    #     print(predicate)
    files2list = Gen.add_problem(['assemble', 'p1AB', 'human'], ['pick', 'p5', 'robot'])
    print(files2list)
    readpddl = Read_PDDL()
    readpddl.read_problem(files2list)
