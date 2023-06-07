from pacai.core.directions import Directions
from pacai.agents.capture.capture import CaptureAgent
# from pacai.core import distanceCalculator
# from pacai.util import reflection
# from pacai.core import distance

import logging
import random
import time

# from pacai.agents.capture.capture import CaptureAgent
from pacai.util import util


def createTeam(firstIndex, secondIndex, isRed,
               # first='pacai.agents.capture.dummy.DummyAgent',
               # second='pacai.agents.capture.dummy.DummyAgent'
               ):
    """
    This function should return a list of two agents that will form the
    capture team,
    initialized using firstIndex and secondIndex as their agent indexed.
    isRed is True if the red team is being created,
    and will be False if the blue team is being created.
    """

    # firstAgent = reflection.qualifiedImport(first)
    # secondAgent = reflection.qualifiedImport(second)
    firstAgent = offensiveAgent
    secondAgent = paxman
    # secondAgent = DefensiveFeatureAgent
    # secondAgent = BallsToWall

    return [
        firstAgent(firstIndex),
        secondAgent(secondIndex),
    ]


class InitialFeatureAgent(CaptureAgent):
    """
    An initial reflex agent with default features and
    weights to be overwritten.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest return from
        `ReflexCaptureAgent.evaluate`.
        """

        actions = gameState.getLegalActions(self.index)

        start = time.time()
        values = [self.evaluate(gameState, a) for a in actions]
        logging.debug('evaluate() time for agent %d: %.4f' %
                      (self.index, time.time() - start))

        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()

        if (pos != util.nearestPoint(pos)):
            # Only half a grid position was covered.
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights.
        """

        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        stateEval = sum(features[feature] * weights[feature]
                        for feature in features)
        # for feature in features:
        # print(stateEval)

        return stateEval

    def getFeatures(self, gameState, action):
        """
        Returns a dict of features for the state.
        The keys match up with the return from
        `self.getWeights`.
        """

        successor = self.getSuccessor(gameState, action)

        return {
            'successorScore': self.getScore(successor)
        }

    def getWeights(self, gameState, action):
        """
        Returns a dict of weights for the state.
        The keys match up with the return from
        `self.getFeatures`.
        """

        return {
            'successorScore': 1.0
        }

class paxman(InitialFeatureAgent):
    """
    A reflex agent that tries to keep its side Pacman-free.
    This is to give you an idea of what a defensive agent could be like.
    It is not the best or only way to make such an agent.
    """
    def __init__(self, index, **kwargs):
        super().__init__(index)

    def getFeatures(self, gameState, action):
        features = {}

        # print("comp: ", self.timeForComputing)
        successor = self.getSuccessor(gameState, action)
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0).
        features['onDefense'] = 1
        if (myState.isPacman()):
            features['onDefense'] = 0

        # Computes distance to invaders we can see.
        enemies = [successor.getAgentState(i)
                   for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman(
        ) and a.getPosition() is not None]
        features['numInvaders'] = len(invaders)

        # incentive pacman to stay close to invaders
        if (len(invaders) > 0):
            dists = [self.getMazeDistance(
                myPos, a.getPosition()) for a in invaders]
            min_dist = min(dists)
            features['invaderDistance'] = 1 / min_dist

            # INVADER TO CAPSULE DISTANCE
            min_cap_dist = 99999
            for c in self.getCapsulesYouAreDefending(successor):
                # print("caps: ", c)
                cap_dist = min([self.getMazeDistance(
                    c, a.getPosition()) for a in invaders])
                min_cap_dist = min(cap_dist, min_cap_dist)
            features['invader2Capsule'] = 1 / min_cap_dist

        # incentivize pacman to stay close to enemies, even when they aren't invading;
        # should help defense stay in middle as opposed to wander randomly otherwise
        if (len(invaders) == 0):
            dists = [self.getMazeDistance(
                myPos, a.getPosition()) for a in enemies]
            features['enemyDefenderDistance'] = 1 / min(dists)

        # decentivize pacman from stopping
        if (action == Directions.STOP):
            features['stop'] = 1

        rev = Directions.REVERSE[gameState.getAgentState(
            self.index).getDirection()]
        if (action == rev):
            features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return {
            'numInvaders': -100,
            'onDefense': 50,
            'invaderDistance': 50,
            'stop': -100,
            'reverse': -2,
            'enemyDefenderDistance': 10,
            'invader2Capsule': -50,
            'invader2Food': -30
            # 'teamDistance': 5,
        }

class offensiveAgent(InitialFeatureAgent):
    """
    A reflex agent that seeks food.
    This agent will give you an idea of what an offensive agent might look like
    but it is by no means the best or only way to build an offensive agent.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index)

    def getFeatures(self, gameState, action):
        features = {}
        successor = self.getSuccessor(gameState, action)
        myState = successor.getAgentState(self.index)
        features['successorScore'] = self.getScore(successor)

        # Compute distance to the nearest food.
        foodList = self.getFood(successor).asList()

        # This should always be True, but better safe than sorry.
        if (len(foodList) > 0):
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food)
                              for food in foodList])
            features['distanceToFood'] = 1 / minDistance

        enemies = [successor.getAgentState(i)
                   for i in self.getOpponents(successor)]

        enemyDefenders = [a for a in enemies if a.isGhost() and a._scaredTimer <= 1]
        if (len(enemyDefenders) > 0):
            enemyDefenderDistances = [self.getMazeDistance(
                myPos, a.getPosition()) for a in enemyDefenders]
            if min(enemyDefenderDistances) < 2:
                # print("RUN")
                features['enemyDefenderDistance'] = 333
            else:
                features['enemyDefenderDistance'] = (
                    1 / min(enemyDefenderDistances))

            if min(enemyDefenderDistances) < 4 and len(foodList) > 4:
                # Don't get stuck in a corner
                walls = gameState.getWalls()
                x, y = myPos
                # Count number of walls next to us in successor state
                wallCount = 0
                if walls[int(x + 1)][int(y)]:
                    wallCount += 1
                if walls[int(x - 1)][int(y)]:
                    wallCount += 1
                if walls[int(x)][int(y + 1)]:
                    wallCount += 1
                if walls[int(x)][int(y - 1)]:
                    wallCount += 1
                if wallCount > 2:
                    features['wallCount'] = wallCount

        scaredEnemies = [a for a in enemies if a._scaredTimer > 1]

        # get capsule only if there's enemy ghosts or if there is not much food left
        if len(enemyDefenders) > 0 and len(scaredEnemies) == 0:
            capsulesDistances = [self.getMazeDistance(
                myPos, a) for a in self.getCapsules(successor)]
            if len(capsulesDistances) > 0:
                features['capsuleDistance'] = len(enemyDefenders) / min(capsulesDistances)

        if len(self.getCapsules(gameState)) > len(self.getCapsules(successor)):
            # print("ATE CAPSULE")
            features['capsuleEaten'] = 1

        # get scared enemies in current state:
        #   - gets current enemies
        cur_enemies = [gameState.getAgentState(
            i) for i in self.getOpponents(successor)]
        #   - gets current enemies that are scared
        cur_scared = [a for a in cur_enemies if a._scaredTimer > 1]

        # if the current scared enemies are greater than scared enemies in successor
        # should check if ghost will be eaten
        if len(cur_scared) > len(scaredEnemies):  # should essentially check if an enemy is eaten
            val = features.get('enemiesEaten', 0) + 1  # 0 if not set, 1 if set;
            # set to 1 if no enemy eaten increment to 2 if this is 2nd enemy being eaten
            features['enemiesEaten'] = val

        if (len(scaredEnemies) > 0):
            scaredDists = [self.getMazeDistance(myPos, a.getPosition())
                           for a in scaredEnemies]
            features['scaredEnemiesDistance'] = 1 / min(scaredDists)

            # features['numScaredEnemies'] = len(scaredEnemies)

        features['onOffense'] = 1
        if (myState.isGhost()):
            features['onOffense'] = 0
            enemies = [successor.getAgentState(i)
                       for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if a.isPacman(
            ) and a.getPosition() is not None]
            # features['numInvaders'] = len(invaders)

            if (len(invaders) > 0):
                invaderDists = [self.getMazeDistance(
                    myPos, a.getPosition()) for a in invaders]
                features['invaderDistance'] = 1 / min(invaderDists)

        if (action == Directions.STOP):
            features['stop'] = 1

        return features

    def getWeights(self, gameState, action):
        return {
            'successorScore': 100,
            'distanceToFood': 10,
            'enemyDefenderDistance': -3,
            'capsuleDistance': 8,
            'wallCount': -100,
            'enemiesEaten': 20,
            'scaredEnemiesDistance': 3,
            'invaderDistance': 2,
            'onOffense': 50,
            # 'numScaredEnemies': 10,
            'capsuleEaten': 50,
            'stop': -100,
        }
