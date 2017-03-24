import tensorflow as tf
import socket
import json
import numpy as np
import matplotlib.pyplot as plt
import random

# vvv - Socket Magic -------------
TCP_IP = '127.0.0.1'
TCP_PORT = 50005
BUFFER_SIZE = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
# ^^^ - Socket Magic -------------

# ************Set Parameters*******************
lr = 0.85 # learning rate
y = 0.99 # discount factor
verbose = True

# Initial values
Q = [] # stores the state / action pairs
rL = [] # stores the Q list rewards
pPip = 167
oPip = 167
board = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0 -3, 0, -5, 0, 0, 0, 0, 0]
pBar = 0
oBar = 0
double = 0 # no one has doubled
ncOwner = -1

# Create initial state list
st = board
st.append(pBar)
st.append(oBar)
st.append(double)
st.append(ncOwner)

iSt = st
ipPip = pPip
ioPip = oPip

# Add the two initial pairs to the Q and reward lists
Q.append([st, 0])
Qindex0 = Q.index([st, 0])
rL.append(0)
Q.append([st, 1])
Qindex1 = Q.index([st, 1])
rL.append(0)
# *********************************************

def calc_reward(pPip, oPip, cube):
    if pPip > oPip:
        r = cube
    elif pPip < oPip:
        r = -1 * cube
    else:
        r = 0
    return r

# Run the Loop. This is a server so we will just kill it violently if needed
while 1:
    try:
        # Accept any requesting connection
        conn, addr = s.accept()
        print('Connection address:', addr)

        # Receive the incoming request
        request = conn.recv(BUFFER_SIZE)

        # If the incoming request isn't null, convert it to our Dict
        if request != None:
            inputs = json.loads(request.decode())
            if verbose: print("I received: ", inputs)

            # Pull information out of received dictionary
            nBoard = inputs['board']
            npPip = inputs['player_pip']
            noPip = inputs['opponent_pip']
            npBar = inputs['player_bar_count']
            noBar = inputs['opponent_bar_count']
            cube = inputs['cube_value']
            ncOwner = inputs['cube_owner']
            nDouble = inputs['double']
            winProb = inputs['player_wins_prob']
            gameOver = inputs['game_over']
            pWins = inputs['player_wins']
            epochs = inputs['epochs']
            cEpochs = inputs['current_epochs']

            if not gameOver:
                # Decide whether or not to take the action
                Qindex0 = Q.index([st, 0])
                Qindex1 = Q.index([st, 1])

                if verbose: print("Current state reward (no double): " + str(rL[Qindex0]))
                if verbose: print("Current state reward (double): " + str(rL[Qindex1]))

                # Random exploration, decreases over time
                diffEpochs = cEpochs + 1 / epochs
                if random.random() > diffEpochs:
                    if random.random() > 0.5:
                        Qindex = Qindex1
                        if verbose: print("Random action: Double!")
                        rs = {'RsSuccess': True, 'Payload': True}
                    else:
                        Qindex = Qindex0
                        if verbose: print("Random action: Don't Double!")
                        rs = {'RsSuccess': True, 'Payload': False}
                else:
                    if rL[Qindex1] > rL[Qindex0]:
                        Qindex = Qindex1
                        if verbose: print("Q-Table action: Double!")
                        rs = {'RsSuccess': True, 'Payload': True}
                    else:
                        Qindex = Qindex0
                        if verbose: print("Q-Table action: Don't Double!")
                        rs = {'RsSuccess': True, 'Payload': False}

                # Create state list
                nSt = nBoard
                nSt.append(npBar)
                nSt.append(noBar)
                nSt.append(nDouble)
                nSt.append(ncOwner)

                # Add the next states to the Q and reward list if they don't exist
                # Sets the index values for the two possible actions
                if not [nSt, 0] in Q:
                    Q.append([nSt, 0])
                    rL.append(0)
                nQindex0 = Q.index([nSt, 0])

                if not [nSt, 1] in Q:
                    Q.append([nSt, 1])
                    rL.append(0)
                nQindex1 = Q.index([nSt, 1])

                #---- TQL ----#
                # Determine max of next action
                if rL[nQindex0] >= rL[nQindex1]:
                    nQindex = nQindex0
                else:
                    nQindex = nQindex1
                #-------------#

                r = calc_reward(pPip, oPip, cube)
                if verbose: print("Calculated reward: " + str(r))

                rL[Qindex] = rL[Qindex] + lr * (r + y * rL[nQindex] - rL[Qindex])
                if verbose: print("Learned reward: " + str(rL[Qindex]))

                pPip = npPip
                oPip = noPip
                st = nSt
            else:
                if verbose: print("Game has ended!")
                Qindex = nQindex
                r = calc_reward(pPip, oPip, cube)
                if pWins:
                    if verbose: print("Player has won!")
                    nR = cube + 1000
                else:
                    if verbose: print("Player has lost...")
                    nR = -1 * (cube + 1000)

                rL[Qindex] = rL[Qindex] + lr * (r + y * nR - rL[Qindex])
                if verbose: print("Match reward is " + str(rL[Qindex]))

                pPip = ipPip
                oPip = ioPip
                st = iSt
        else:
            rs = {'RsSuccess': False}

        # Convert our response to a json string
        strResponse = json.dumps(rs)

        # Convert our response to Bytes
        response = strResponse.encode()

        # Publish the response and close the connection, then start over
        conn.send(response)  # Response
        conn.close()
    except Exception as ex:
        print(ex)


#toString
#s=json.dumps(variables)

#toDict
#variables2=json.loads(s)

##import tensorflow as tf
#hello = tf.constant('Hello, TensorFlow!')
#sess = tf.Session()
#print(sess.run(hello))

#x = tf.placeholder(tf.float32, [None, 784])
#W = tf.Variable(tf.zeros([784, 10]))
#b = tf.Variable(tf.zeros([10]))

#y = tf.nn.softmax(tf.matmul(x, W) + b)
