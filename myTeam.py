from pacai.core.directions import Directions
from pacai.agents.capture.capture import CaptureAgent
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

    firstAgent = OffensiveFeatureAgent
    secondAgent = DefensiveFeatureAgent

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


class DefensiveFeatureAgent(InitialFeatureAgent):
    """
    A reflex agent that tries to keep its side Pacman-free.
    This is to give you an idea of what a defensive agent could be like.
    It is not the best or only way to make such an agent.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index)

    def getFeatures(self, gameState, action):
        features = {}

        successor = self.getSuccessor(gameState, action)
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0).
        features['onDefense'] = 1
        if (myState.isPacman()):
            features['onDefense'] = 0

        # team = [successor.getAgentState(i)
        #         for i in self.getTeam(successor)]
        # teamDistance = self.getMazeDistance(
        #     team[0].getPosition(), team[1].getPosition())
        # features['teamDistance'] = teamDistance

        # Computes distance to invaders we can see.
        enemies = [successor.getAgentState(i)
                   for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman(
        ) and a.getPosition() is not None]
        features['numInvaders'] = len(invaders)

        # incentivize pacman to stay close to invaders
        if (len(invaders) > 0):
            dists = [self.getMazeDistance(
                myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = 1/min(dists)

        # incentivize pacman to stay close to enemies,
        # even when they aren't invading;
        # should help defense stay in middle as opposed
        # to wander randomly otherwise
        if (len(enemies) > 0):
            dists = [self.getMazeDistance(
                myPos, a.getPosition()) for a in enemies]
            features['stayCloseToEnemies'] = 1/min(dists)

        if (action == Directions.STOP):
            features['stop'] = 1

        rev = Directions.REVERSE[gameState.getAgentState(
            self.index).getDirection()]
        if (action == rev):
            features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return {
            'numInvaders': -1000,
            'onDefense': 20,
            'invaderDistance': 15,
            'stop': -100,
            'reverse': -2,
            'stayCloseToEnemies': 10,
            # 'teamDistance': 5,
        }


class OffensiveFeatureAgent(InitialFeatureAgent):
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
        features['successorScore'] = self.getScore(successor)

        # Compute distance to the nearest food.
        foodList = self.getFood(successor).asList()

        # This should always be True, but better safe than sorry.
        if (len(foodList) > 0):
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food)
                              for food in foodList])
            features['distanceToFood'] = minDistance

        # team = [successor.getAgentState(i)
        #         for i in self.getTeam(successor)]
        # teamDistance = self.getMazeDistance(
        #     team[0].getPosition(), team[1].getPosition())
        # features['teamDistance'] = teamDistance

        # Computes distance to invaders we can see.
        enemies = [successor.getAgentState(i)
                   for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman(
        ) and a.getPosition() is not None]
        features['numInvaders'] = len(invaders)

        if (len(invaders) > 0):
            invaderDists = [self.getMazeDistance(
                myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(invaderDists)

        # If the defender is within 3 units of distance, run back to defense
        enemyDefenders = [a for a in enemies if not a.isPacman()]
        if (len(enemyDefenders) > 0):
            enemyDefenderDistances = [self.getMazeDistance(
                myPos, a.getPosition()) for a in enemyDefenders]
            enemyDefenderDistances = [
                a for a in enemyDefenderDistances]
            if enemyDefenderDistances:
                features['enemyDefenderDistance'] = (
                    1 / min(enemyDefenderDistances))

        scaredEnemies = [a for a in enemies if a._scaredTimer > 1]

        scaredEnemies = [a for a in enemies if a._scaredTimer > 1]
        # get scared enemies in current state
        cur_enemies = [gameState.getAgentState(
            i) for i in self.getOpponents(successor)]  # gets current enemies
        # gets current enemies that are scared
        cur_scared = [a for a in cur_enemies if a._scaredTimer > 1]

        # if the current scared enemies are greater than
        # scared enemies in successor
        # should check if ghost will be eaten

        # 0 if not set, 1 if set; set to 1 if no enemy eaten,
        if len(cur_scared) > len(scaredEnemies):
            val = features.get('enemiesEaten', 0) + 1
            # increment to 2 if this is 2nd enemy being eaten
            features['enemiesEaten'] = val

        if (len(scaredEnemies) > 0):
            scaredDists = [self.getMazeDistance(myPos, a.getPosition())
                           for a in scaredEnemies]
            features['scaredEnemiesDistance'] = min(scaredDists)
            # if min(scaredDists) == 0:
            #     features['scaredEnemyEatten'] = 1
            features['enemyDefenderDistance'] = -10
            features['enemiesAreScared'] = 1
        # features['numScaredEnemies'] = len(scaredEnemies)

        capsulesDistances = [self.getMazeDistance(
            myPos, a) for a in self.getCapsules(successor)]
        if len(capsulesDistances) > 0:
            features['capsuleDistance'] = min(capsulesDistances)

        return features

    def getWeights(self, gameState, action):
        return {
            'successorScore': 100,
            'distanceToFood': -1,
            'numInvaders': -100,
            'invaderDistance': -2,
            # 'numScaredEnemies': 1000,
            'enemiesAreScared': 10,
            'scaredEnemiesDistance': -2,
            # 'teamDistance': 5,
            'enemyDefenderDistance': -2,
            'capsuleDistance': -1,
            'scaredEnemyEatten': 100,
            'enemiesEaten': 100,

        }
