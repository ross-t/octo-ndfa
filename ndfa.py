# Represents an NDFA given a start state and a set of final states
class NDFA:

    def __init__(self, start, final):
        self.state = set({start})
        self.start = start
        self.final = final

    def consume(self, string):
        # Consume a string, printing state changes along the way
        # Recursive base case: the string is empty
        if len(string) == 0:
            return

        next_char = string[0]
        next_states = set()

        # The next set of states we're in is calculated by iterating over the states we're currently in and seeing which states our input
        # makes them transition to. If a state doesn't have any transitions with that input, it returns the empty set, so by doing this
        # the NDFA "magically" finds the right path.
        for state in self.state:
            next_states = next_states.union(state.transition(next_char))

        print '%s: %s -> %s' % (next_char, str(self.state), str(next_states))

        self.state = next_states
        # Recursively consume the next character in the string
        self.consume(string[1:])



    def accepts(self, string):
        self.state = set({self.start})  # Reset the current state
        self.consume(string)
        # A string is accepted if we can reach an accept state using epsilon transitions after consuming the entire input
        final_eps = set()
        for state in self.state:
            final_eps = final_eps.union(state.transition(''))
            if len(self.final.intersection(final_eps)) > 0:
                return True

        # ...or if the set of states the NDFA is in contains at
        # least one final state.
        return len(self.final.intersection(self.state)) > 0

# A node is just a node on our graph that represents a state
class Node:
    def __init__(self, label, transitions=None):
        #Epsilon transitions are transitions from the empty string
        self.label = label
        # Transitions are just a mapping from characters to sets of states
        if transitions == None:
            self.transitions = dict()
        else:
            self.transitions = transitions
        self.calculated_epsilon_transitions = None

    def transition(self, char):
        '''Returns the set of all states reachable from this state when consuming char, including epsilon transitions'''
        eps = {}
        if '' in self.transitions:
            #If we haven't already calculated our epsilon transitions, do so now
            if self.calculated_epsilon_transitions == None: 
                self.calculated_epsilon_transitions = self.epsilon_transitions()
            eps = self.calculated_epsilon_transitions

        if char in self.transitions:
            return self.transitions[char].union(eps)
        return eps

    def epsilon_transitions(self, node=None, visited_nodes=None):
        #Returns the set of all nodes reachable by taking epsilon transitions from this node (recursive)
        if visited_nodes == None:
            visited_nodes = set()
        if node == None:
            node = self
        if '' not in node.transitions or node in visited_nodes: #Base case: The node we arrive at has no epsilon transitions
            return visited_nodes.union([node])
        eps_reachable = set()
        visited_nodes.add(node) #We can reach the node we're at now
        for state in node.transitions['']: #...and every node reachable by recursively taking epsilon transitions from it
            eps_reachable = eps_reachable.union(self.epsilon_transitions(state, visited_nodes))

        return eps_reachable 

    def add_transition(self, char, states):
        states = set(states)
        if char in self.transitions:
            self.transitions[char] = self.transitions[char].union(states)
        else:
            self.transitions[char] = states

    def __repr__(self):
        # Just so that Node objects can be formatted as strings
        return self.label

# Stored as
# label:character.transitions|character.transitions|character.transitions
# where transitions are labels of other states separated by commas
# if the line starts with $, it's the start node
# any whose lines begin with a * are final/accept nodes
# e.g. apple:a.banana,split,fruit is a node labeled apple that has edges to the nodes
# labeled banana, split, and fruit. it'll change state to the set of those states when
# it consumes 'a'


def from_file(filename):
    with open(filename) as infile:
        start_node = None
        final_nodes = set()
        labels = dict()
        nodelines = infile.readlines()

        for line in nodelines:
            is_final = False
            is_start = False
            existed = False

            #At this point, line is the entire line, so we're checking the 0th character and slicing it off
            if line[0] == '*':
                line = line[1:]
                is_final = True

            if line[0] == '$':
                line = line[1:]
                is_start = True

            #line now consists of the whole line minus the 0th character
            #Extract the label by splitting the line on : and stripping whitespace from the 0th result
            label = line.split(':')[0].strip()
            node = None

            if label in labels:
                existed = True
                node = labels[label]
            else:
                node = Node(label)

            print 'Found state %s' % (label)
            if is_final:
                final_nodes.add(node)
                print '\t...and it\'s a final state'
            if is_start:
                print '\t...and it\'s a/the start state'
                start_node = node
            if existed:
                print '\t...and it had already been implicitly or explicitly defined'

            labels[label] = node

            transitions = line.split(':')[1].split('|')
            for i, transition in enumerate(transitions):
                if (i == len(transitions) - 1) and (transition.find('.') == -1):
                    #If we're reading the last | and there's no ., it's a list of nodes that there are epsilon transitions to
                        to = transition.split(',')
                        for to_node in to:
                            to_node = to_node.strip()
                            if to_node not in labels:
                                print '\tFound eps to implicitly defined state %s' % to_node
                                labels[to_node] = Node(to_node)
                            else:
                                print '\tFound eps to previously defined state %s' % to_node
                            node.add_transition('', {labels[to_node]})
                            print '\tHas an epsilon transition to %s' % (to_node)
                        continue

                definition = transition.split('.')
                char = definition[0]
                to = definition[1].split(',')

                for to_node in to:
                    to_node = to_node.strip()
                    if to_node not in labels:
                        labels[to_node] = Node(to_node)
                    node.add_transition(char, {labels[to_node]})
                    print "\t%s -> %s" % (char, to_node)

        result = NDFA(start_node, final_nodes)
        print "NDFA successfully created"
        return result

def test_accepts(input, filename):
	nd = from_file(filename)
	for x in input:
		print "Accepts %s? %s\n" % (x, nd.accepts(x))