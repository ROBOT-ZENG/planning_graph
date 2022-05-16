# -----------------------------------------------
# Applicable
# Check if the positive and negative preconditions are satisfied in a given state
# return bool(YES/NO)
# -----------------------------------------------

def applicable(state, positive, negative):
    return positive.issubset(state) and not negative.intersection(state)


# -----------------------------------------------
# Apply
# Apply the positive and negative effects to a given state
# return a new state
# -----------------------------------------------

def apply(state, positive, negative):
    return frozenset(state.union(positive).difference(negative))
