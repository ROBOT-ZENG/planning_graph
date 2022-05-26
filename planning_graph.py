import sys
import pathlib

parent_path = str((pathlib.Path() / "..").resolve().absolute())
if not parent_path in sys.path and parent_path[-18:] == "hr_task_allocation":
    sys.path.append(parent_path)
from pddl.pddl import PDDL
import time


class PlanningGraph:

    def __init__(self):
        self.readpddl = PDDL()
        self.states = {}
        self.actions = {}
        self.goal = {}
        self.action_state = {}

        # http://planning.cs.uiuc.edu/node66.html to see what mutex(mutual exclusive) is.

        # Negated Literal: a proposition and its negation are mutex
        self.nl_mutex = {}
        # Inconsistent Effects: the effect of one action is the negation of another action's effect.
        self.ie_mutex = {}
        # Interference: one action deletes a precondition of another
        self.i_mutex = {}
        # Competing Needs: the actions have preconditions that are mutex.
        self.cn_mutex = {}
        # Inconsistent Support: all the ways of achieving the propositions are pairwise mutex.
        self.is_mutex = {}

    def check_possibility(self, static_pred, agent_ability, agent_track):
        ground_act = []
        for action in self.readpddl.actions:
            for act in action.instantiate(self.readpddl.objects):
                if act.name in agent_ability and (not act.parameters[0] in agent_ability[act.name]):
                    continue
                # if act.name in forbid_pair and forbid_pair[act.name] == act.parameters[0]:
                #     continue
                # if act.name == 'move':
                #     if act.parameters[0] == 'human1' and not (act.parameters[1][-1] == 'b' and act.parameters[2][-1] == 'b'):
                #         continue
                #     if act.parameters[0] == 'robot1' and not (act.parameters[1][-1] == 'b' and act.parameters[2][-1] == 'b'):
                #         continue
                #     if act.parameters[0] == 'cart' and not (act.parameters[1][-1] == 'c' and act.parameters[2][-1] == 'c'):
                #         continue
                # elif act.name == 'assemble':
                #     if act.parameters[0] == 'cart':
                #         continue
                # elif act.name == 'pass':
                #     if act.parameters[0] == act.parameters[1] or act.parameters[0] == 'cart' or act.parameters[2][-1] != 'b' or act.parameters[3][-1] == 'a':
                #         continue
                #     if (act.parameters[1] == 'cart'):
                #         holder_owner = {'part1abcd': 'part1abcd_holder', 'part2': 'part2_holder', 'part3': 'part3_holder', 'part4': 'part4_holder'}
                #         if act.parameters[3][-1] != 'c' or act.parameters[4] in ['part1a', 'part1b', 'part1c', 'part1d', 'part1ab', 'part1abc']:
                #             continue
                #         if act.parameters[4] in holder_owner and holder_owner[act.parameters[4]] != act.parameters[-1]:
                #             continue

                all_predicates = set(act.positive_preconditions) | set(act.negative_preconditions) | set(act.add_effects) | set(act.del_effects)
                static_predicates = set()
                for predicate in all_predicates:
                    if predicate[0] in static_pred:
                        static_predicates.add(predicate)
                if static_predicates.issubset(self.readpddl.state):
                    ground_act.append(act)
        return ground_act

    def solve_file(self, domainfile, problemfile):

        self.readpddl.read_domain(domainfile)
        self.readpddl.read_problem(problemfile)
        static_pred = ['neighbor', 'belong', 'getnew', 'locate']
        agent_ability = {'pick': ['human1', 'robot1'], 'move': ['human1', 'robot1', 'cart'], 'assemble': ['human1', 'robot1'], 'pass': ['human1', 'robot1']}
        agent_track = {'human1': 'b', 'robot1': 'b', 'cart': 'c'}
        # forbid_pair={'pick':'cart'}
        # ground_actions = self.check_possibility(static_pred, forbid_pair)
        ground_actions = self.check_possibility(static_pred, agent_ability, agent_track)
        state_temp = {}
        for s in self.readpddl.init_state:
            state_temp[str(s)] = 1
        self.states[1] = state_temp

        # ------------------------------problem to be solved------------------------------
        # self.states[1]["('occupied', 'location2c')"] = -1
        # according to the fluent in goal state, reason the precondition of action with this fluent, and add it to the initial state.
        # Sometimes even the applicable actions had been detected in step i, it appeared in step i+1 again.
        # Some actions are still meaningless impossible, such as move('cart', 'location1c', 'location2b'), delete them.
        # ------------------------------problem to be solved------------------------------

        for p in self.readpddl.positive_goal:
            self.goal[str(p)] = 1
        for p in self.readpddl.negative_goal:
            self.goal[str(p)] = -1
        for g in ground_actions:
            pre = {}
            eff = {}
            temp_action_data = []
            action_name = g.name + str(g.parameters)
            for p in g.positive_preconditions:
                pre[str(p)] = 1
            for p in g.negative_preconditions:
                pre[str(p)] = -1
            temp_action_data.append(pre)
            for p in g.add_effects:
                eff[str(p)] = 1
            for p in g.del_effects:
                eff[str(p)] = -1
            temp_action_data.append(eff)
            self.actions[action_name] = temp_action_data
        fd = open("./data.txt", "w")
        string = str(self.actions)
        fd.write(string)
        fd.close()
        print('Action Generation Completed!', len(self.actions))

    def extendGraph(self):
        current_state = 1
        # check if the goal state exist in the graph plan otherwise extend the graph
        while self.checkGoal(current_state):
            temp_state = self.states[current_state].copy()
            action_state = []
            for action in self.actions:
                action_flag = True
                pre_cond = self.actions[action][0]
                for fluent in pre_cond:
                    if fluent in self.states[current_state]:
                        # 当self.states[current_state][fluent] = 2，是不是也应该是FALSE。
                        if pre_cond[fluent] != self.states[current_state][fluent] and self.states[current_state][fluent] != 2:
                            action_flag = False
                    else:
                        if pre_cond[fluent] == 1:
                            action_flag = False
                if action_flag:
                    action_state.append(action)
                    effects = self.actions[action][1]
                    for fluent in effects:
                        if fluent in self.states[current_state]:
                            if self.states[current_state][fluent] + effects[fluent] == 0:
                                temp_state[fluent] = 2
                        elif fluent not in self.states[current_state] and effects[fluent] == 1:
                            temp_state[fluent] = effects[fluent]

            self.states[current_state + 1] = temp_state
            self.action_state[current_state] = action_state
            self.printStates(current_state)
            # print("------------")
            current_state += 1
            self.printAction(current_state - 1)
            # print("------------")
            self.printStates(current_state)
            # print("------------")
            # self.mutexes(current_state)

    def checkGoal(self, state):
        goals_pos = []
        goals_neg = []
        state_goal = []
        for goal in self.goal:
            if (self.goal[goal] == 1):
                goals_pos.append(goal)
            else:
                goals_neg.append(goal)
        goal_act = {}
        # state_goal = ["('at', 'robot1', 'location2b')", "('at', 'cart', 'location2c')", "('on', 'part2', 'robothand1')"]
        for s in self.states[1]:
            if self.states[1][s] == 1:
                state_goal.append(s)
            elif self.states[1][s] == -1:
                state_goal.append("not" + s)
        current_state = self.states[state]
        for goal in self.goal:
            if goal in current_state:
                if self.goal[goal] != current_state[goal] and current_state[goal] != 2:
                    return True
            else:
                if self.goal[goal] == 1:
                    return True
        if self.is_mutex[state]:
            return True

        # c_st = 1
        # actions = self.action_state
        # while c_st < state:
        #     for action in actions:
        #         for lit in actions[action]:
        #             i_mutex = self.i_mutex[c_st]
        #             # there are mutex actions in current action state
        #             # why lit must be in i_mutex?
        #             if lit in i_mutex and set(i_mutex[lit]).issubset(actions[action]):
        #                 # if goal_act is empty
        #                 if not goal_act:
        #                     goal_act[c_st] = lit
        #                     effects = self.actions[lit][1]
        #                     for eff in effects:
        #                         if (effects[eff] == -1):
        #                             if eff in state_goal:
        #                                 state_goal.remove(eff)
        #                             # if not ("not" + eff) in state_goal:
        #                             #     state_goal.append("not" + eff)
        #                         elif (effects[eff] == 1):
        #                             if ("not" + eff) in state_goal:
        #                                 state_goal.remove("not" + eff)
        #                             if not eff in state_goal:
        #                                 state_goal.append(eff)
        #
        #                     # for eff in effects:
        #                     #     if (effects[eff] == -1):
        #                     #         state_goal.remove(eff)
        #                     #         state_goal.append("not" + eff)
        #                     #     else:
        #                     #         state_goal.remove("not" + eff)
        #                     #         state_goal.append(eff)
        #                 elif c_st != 1:
        #                     # goal_act[c_st] = None
        #                     if not (lit in goal_act.values()):
        #                         # for key in list(goal_act.keys()):
        #                         #     if goal_act[key] != lit:
        #                         pre_cond = self.actions[lit][0]
        #                         temp_pre_pos = []
        #                         temp_pre_neg = []
        #                         for eff in pre_cond:
        #                             # if (pre_cond[eff] == -1):
        #                             #     temp_pre.append("not" + eff)
        #                             # else:
        #                             #     temp_pre.append(eff)
        #                             if (pre_cond[eff] == -1):
        #                                 temp_pre_neg.append(eff)
        #                             else:
        #                                 temp_pre_pos.append(eff)
        #
        #                         if set(temp_pre_pos).issubset(state_goal) and (not set(temp_pre_neg).intersection(state_goal)):
        #                             if not c_st in goal_act:
        #                                 goal_act[c_st] = lit
        #                                 effects = self.actions[lit][1]
        #                                 for eff in effects:
        #                                     if (effects[eff] == -1):
        #                                         if eff in state_goal:
        #                                             state_goal.remove(eff)
        #                                         # if not ("not" + eff) in state_goal:
        #                                         #     state_goal.append("not" + eff)
        #                                     else:
        #                                         if ("not" + eff) in state_goal:
        #                                             state_goal.remove("not" + eff)
        #                                         if not eff in state_goal:
        #                                             state_goal.append(eff)
        #                                     # if (effects[eff] == -1):
        #                                     #     state_goal.remove(eff)
        #                                     #     state_goal.append("not" + eff)
        #                                     # else:
        #                                     #     state_goal.remove("not" + eff)
        #                                     #     state_goal.append(eff)
        #
        #         c_st += 1
        # # print('goal_act', goal_act)
        # # print('goals', goals_pos, goals_neg)
        # # print('state_goal', state_goal)
        # # print("-------------------------------------------------------------------------------------------------------------------")
        # if not (set(goals_pos).issubset(state_goal) and (not set(goals_neg).intersection(state_goal))):
        #     return True
        # else:
        #     print("Solution Path", goal_act)

    def mutexes(self, state):
        self.negatedLiteral(state)
        self.inconsistentEffect(state - 1)
        self.interference(state - 1)
        self.comptetingNeeds(state - 1)
        self.inconsistentSupport(state)
        # print("------------")

    def negatedLiteral(self, state):
        nl_mutex = []
        current_state = self.states[state]
        for key in current_state:
            if current_state[key] == 2:
                nl_mutex.append([key, "not" + key])
        self.nl_mutex[state] = nl_mutex
        # print("NL mutex at literal state", state, "--", nl_mutex)

    # Inconsistent Effects: the effect of one action is the negation of another action's effect.
    def inconsistentEffect(self, state):
        ie_mutexes = {}
        current_action = self.action_state[state]
        next_state = self.states[state + 1]
        for action in current_action:
            temp_ie = []
            effects = self.actions[action][1]
            for effect in effects:
                # if the mutex action exists at current actions state, then there must be positive and negative of same predicate in the next state.
                if next_state[effect] == 2:
                    for i_action in current_action:
                        if i_action != action:
                            i_effects = self.actions[i_action][1]
                            if effect in i_effects and i_effects[effect] + effects[effect] == 0:
                                temp_ie.append(i_action)
                    if (effects[effect] == 1):
                        temp_ie.append("no-op(not" + effect + ")")
                    else:
                        temp_ie.append("no-op(" + effect + ")")
            ie_mutexes[action] = temp_ie

        self.ie_mutex[state] = ie_mutexes
        # print("IE mutex at action state", state, "--", ie_mutexes)

    # Interference: one action deletes a precondition of another
    def interference(self, state):
        i_mutexes = {}
        current_action = self.action_state[state]
        for action in current_action:
            temp_i = []
            effects = self.actions[action][1]
            for effect in effects:
                for i_action in current_action:
                    if i_action != action:
                        pre_cond = self.actions[i_action][0]
                        if effect in pre_cond and pre_cond[effect] + effects[effect] == 0:
                            temp_i.append(i_action)
            i_mutexes[action] = temp_i

        self.i_mutex[state] = i_mutexes
        # print("I mutex at action state", state, "--", i_mutexes)

    # Competing Needs: the actions have preconditions that are mutex.
    def comptetingNeeds(self, state):
        cn_mutexes = {}
        current_action = self.action_state[state]
        for action in current_action:
            temp_i = []
            pre_conds = self.actions[action][0]
            for pre in pre_conds:
                for i_action in current_action:
                    if i_action != action:
                        pre_cond = self.actions[i_action][0]
                        if pre in pre_cond and pre_cond[pre] + pre_conds[pre] == 0:
                            temp_i.append(i_action)
            cn_mutexes[action] = temp_i
        self.cn_mutex[state] = cn_mutexes
        # print("CN mutex at action state", state, "--", cn_mutexes)

    # Inconsistent Support: all the ways of achieving the propositions are pairwise mutex.
    def inconsistentSupport(self, c_state):
        states = self.states[c_state]
        # self.actionEffet(c_state,{"FriedEggs":1, "BoiledVegetables":1})
        for state in states:
            for p_state in states:
                if p_state != state:
                    if states[state] == 2:
                        if states[p_state] == 1:
                            self.actionEffet(c_state, {state: 1, p_state: 1})
                            self.actionEffet(c_state, {state: -1, p_state: 1})
                        elif states[p_state] == -1:
                            self.actionEffet(c_state, {state: 1, p_state: -1})
                            self.actionEffet(c_state, {state: -1, p_state: -1})
                        else:
                            self.actionEffet(c_state, {state: 1, p_state: 1})
                            self.actionEffet(c_state, {state: -1, p_state: 1})
                            self.actionEffet(c_state, {state: 1, p_state: -1})
                            self.actionEffet(c_state, {state: -1, p_state: -1})
                    elif states[state] == 1:
                        if states[p_state] == 1:
                            self.actionEffet(c_state, {state: 1, p_state: 1})
                        elif states[p_state] == -1:
                            self.actionEffet(c_state, {state: 1, p_state: -1})
                        else:
                            self.actionEffet(c_state, {state: 1, p_state: 1})
                            self.actionEffet(c_state, {state: 1, p_state: -1})
                    else:
                        if states[p_state] == 1:
                            self.actionEffet(c_state, {state: -1, p_state: 1})
                        elif states[p_state] == -1:
                            self.actionEffet(c_state, {state: -1, p_state: -1})
                        else:
                            self.actionEffet(c_state, {state: -1, p_state: 1})
                            self.actionEffet(c_state, {state: -1, p_state: -1})
        # print("IS mutex at literal state", c_state, "--", self.is_mutex[c_state])

    def actionEffet(self, state, literal):
        is_mutexes = []
        actions = self.action_state[state - 1]
        pair_action = []
        # if one predicate exists in current state and last state, and have same value, this means that no actions operate on this predicate from
        # last state to this state, we are discussing about real actions which can realize the predicate.
        for key in literal:
            if key in self.states[state - 1]:
                if self.states[state - 1][key] == literal[key]:
                    return
        for action in actions:
            effect = self.actions[action][1]
            for key, value in effect.items():
                if key in literal and literal[key] == value:
                    # 把能够实现这两个literal的所有actions放到pair_actions里面
                    # 这个地方有问题，应该仔细区分以下不同的情况
                    # 有可能会有多个actions能够实现同一个literal，也有可能有一个action可以同时实现这两个literals。
                    # 有没有可能会把同一个action添加两次
                    pair_action.append(action)
        for action in pair_action:
            # 不仅仅需要考虑i_mutex,ie_mutex和cn_mutex也需要考虑
            if action in self.i_mutex[state - 1]:
                for i in self.i_mutex[state - 1][action]:
                    # 检查，如果这些pair actions里面存在互斥的actions对，则删除这些actions
                    if i in pair_action:
                        pair_action.remove(i)
                        if action in pair_action:
                            pair_action.remove(action)
                        # 如果pair_action是空的
                        if not pair_action:
                            temp = []
                            for key in literal:
                                if literal[key] == -1:
                                    temp.append("not" + key)
                                elif literal[key] == 1:
                                    temp.append(key)
                            is_mutexes.append(temp)
        self.is_mutex[state] = is_mutexes

    def printAction(self, state):
        print("Action at state -", state, ":")
        c_actions = self.action_state[state]
        states = self.states[state]
        for state in states:
            if (states[state] == 2):
                print(state, "--> no-op -->", state)
                state = "not" + state
                print(state, "--> no-op -->", state)
            elif states[state] == -1:
                state = "not" + state
                print(state, "--> no-op -->", state)
            # else:
            print(state, "--> no-op -->", state)
        for action in c_actions:
            pre_cond = []
            effects = []
            for x in self.actions[action][0]:
                if self.actions[action][0][x] == -1:
                    pre_cond.append("not" + x)
                else:
                    pre_cond.append(x)
            for x in self.actions[action][1]:
                if self.actions[action][1][x] == -1:
                    effects.append("not" + x)
                else:
                    effects.append(x)

            print(pre_cond, "-->", action, "-->", effects)

    def printStates(self, state):
        print("Literals at state -", state, ":")
        c_states = self.states[state]
        st = []
        for x in c_states:
            if c_states[x] == 2:
                st.append("not" + x)
                st.append(x)
            elif c_states[x] == -1:
                st.append("not" + x)
            else:
                st.append(x)
        print(st)


if __name__ == '__main__':
    time_start = time.time()
    domain_SPS = "examples/domain_SPS.pddl"
    problem_SPS = "examples/problem_SPS.pddl"
    planner = PlanningGraph()
    planner.solve_file(domain_SPS, problem_SPS)
    planner.extendGraph()
    time_period = time.time() - time_start
    print('Running cost:', time_period)

    # print(len(ground_actions))
    # for ga in ground_actions:
    #     if ga.name == 'pick':
    #         print(ga)
