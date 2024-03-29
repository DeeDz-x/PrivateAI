from Misc.JSONObjects import *
from Socket import Connection
import random


def main(game: Game):
    """ Main AI Logic
    """

    player = game.getCurrentPlayer()

    # Check if user is disqualified
    if not player.disqualified:
        playerCards = player.getCards()
        # topCard = game.getTopCard()

        topCard = checkTopCardForActionCards(game.getDiscardPile(), game, 0)
        print("current top card: " + topCard.name + " -- " + str(topCard.cardToDict()))

        cardMatches = matchCardsByColor(topCard, playerCards)
        actionCardsOnHand = checkForActionCards(cardMatches)

        # When turn starts check for matching pairs - discard matches or take a card
        makeMove(actionCardsOnHand, cardMatches, topCard, game)


def checkTopCardForActionCards(discardPile: list, game: Game, index: int) -> Card:

    topCard = discardPile[index]

    if len(discardPile) - index <= 1:
        print("INITIAL TOP CARD")
        match topCard.type:
            case "invisible":
                topCard.value = 1

            case "reset":
                topCard.value = 1
                topCard.colors = ["red", "green", "blue", "yellow"]

            case "nominate":
                if game.state == "nominate_flipped":
                    action = nominatePlayer(topCard, game)
                    Connection.playAction(action)

                else:
                    topCard.value = game.lastNominateAmount
                    if topCard.name == "multi nominate":
                        topCard.colors = [game.lastNominateColor]

            case "number":
                pass

        return topCard

    else:
        match topCard.type:
            case "invisible":
                for card in range(index, len(discardPile)):
                    index += 1
                    topCard = checkTopCardForActionCards(discardPile, game, index)
                    return topCard

            case "reset":
                topCard.value = 1
                topCard.colors = ["red", "green", "blue", "yellow"]

            case "nominate":
                topCard.value = game.lastNominateAmount
                if topCard.name == "multi nominate":
                    topCard.colors = [game.lastNominateColor]

            case "number":
                pass

        return topCard


def makeMove(actionCardsOnHand, cardMatches, topCard, game):
    # decide which cards are discarded
    if cardMatches:
        if actionCardsOnHand:
            discardActionCard = playActionCard(actionCardsOnHand, game)
            Connection.playAction(discardActionCard)
        else:
            discardAction = discardCardSet(topCard, cardMatches)
            Connection.playAction(discardAction)

    else:
        match game.state:
            case "turn_start":
                specifyActionType("take")
            case "card_drawn":
                specifyActionType("nope")


def playActionCard(actionCardsOnHand: list, game: Game) -> Action:
    """

    :param actionCardsOnHand:
    :return:
    """

    if len(actionCardsOnHand) > 1:

        order = ["nominate", "invisible", "reset"]
        orderList = []

        for item in order:
            for card in actionCardsOnHand:
                if card.type == item:
                    orderList.append(card)

        action = discardSingleCard(orderList[0], game)

    else:
        action = discardSingleCard(actionCardsOnHand[0], game)

    return action


def specifyActionType(actiontype):
    specificAction = Action(type=actiontype,
                            explanation="no cards to discard")
    Connection.playAction(specificAction)


def nominatePlayer(card: Card, game: Game) -> Action:

    nominatedPlayer = choosePlayerToNominate(game)

    # calculate nominated amount. If player has more cards a higher value gets nominated
    amount = nominatedPlayer.cardAmount // 3
    if amount < 1:
        amount = 1
    if amount > 3:
        amount = 3

    if card.name == "multi nominate":

        nominatedColor = nominateColor()

        parsedPlayer = nominatedPlayer.toDict()
        discardAction = Action(type="nominate",
                               explanation="random pick",
                               cards=None,
                               nominatedPlayer=parsedPlayer,
                               nominatedAmount=amount,
                               nominatedColor=nominatedColor)
        print("nominated player: " + nominatedPlayer.username + " - nominated Amount: " + str(amount) + " - nominated color:")

    else:
        parsedPlayer = nominatedPlayer.toDict()
        discardAction = Action(type="nominate",
                               explanation="random pick",
                               cards=None,
                               nominatedPlayer=parsedPlayer,
                               nominatedAmount=amount)
        print("nominated player: " + nominatedPlayer.username + " - nominated Amount: " + str(amount))

    return discardAction


def nominateColor() -> str:
    possiblecolors = ["red", "green", "yellow", "blue"]
    randomColor = random.choice(possiblecolors)
    return randomColor


def discardSingleCard(card: Card, game: Game) -> Action:
    parsedCard = [card.cardToDict()]

    if card.type == "nominate":
        nominatedPlayer = choosePlayerToNominate(game)

        # calculate nominated amount. If player has more cards a higher value gets nominated
        amount = nominatedPlayer.cardAmount // 3
        if amount < 1:
            amount = 1
        if amount > 3:
            amount = 3

        if card.name == "multi nominate":
            parsedPlayer = nominatedPlayer.toDict()
            discardAction = Action(type="nominate",
                                   explanation="random pick",
                                   cards=parsedCard,
                                   nominatedPlayer=parsedPlayer,
                                   nominatedAmount=amount,
                                   nominatedColor="red") #TODO nominate a color
            print("played ActionCard: " + card.type + " - nominated Amount: " + str(amount) + " - nominated color:")

        else:
            parsedPlayer = nominatedPlayer.toDict()
            discardAction = Action(type="nominate",
                                   explanation="random pick",
                                   cards=parsedCard,
                                   nominatedPlayer=parsedPlayer,
                                   nominatedAmount=amount)
            print("played ActionCard: " + card.type + " - nominated Amount: " + str(amount))

    else:
        discardAction = Action(type="discard",
                               explanation="random pick",
                               cards=parsedCard)
        print("played ActionCard: " + card.type)

    return discardAction


def choosePlayerToNominate(game: Game) -> Player:
    playerlist = game.getPlayerList()
    currentPlayer = game.getCurrentPlayer()
    cardAmountList = []

    for player in playerlist:
        if player.username != currentPlayer.username:
            cardAmountList.append(int(player.cardAmount))

    maxCards = max(cardAmountList)

    for player in playerlist:
        if maxCards == player.cardAmount and player.username != currentPlayer.username:
            return player


def discardCardSet(topCard, matchedColors) -> Action:
    key = min(matchedColors)
    discardCardsList = []
    for i in range(topCard.value):
        discardCardsList.append(matchedColors[key][i])

    jsonCards = []
    for card in discardCardsList:
        parsedCard = card.cardToDict()
        jsonCards.append(parsedCard)

    discardAction = Action(type="discard",
                           explanation="random pick",
                           cards=jsonCards)
    return discardAction


def matchCardsByColor(topCard: Card, playerCards: list) -> dict:
    """ Check the players cards for completed sets, depending on the top card

    :param topCard: The current top card
    :param playerCards: The current players cards
    :return: Dictionary of matching cards which complete a required set - with colors as keys and a list of cards as value
    """

    # Save all matching cards to a dictionary
    matchedColors = {}
    for color in topCard.colors:
        matchedCards = []
        for card in playerCards:
            for cardcolor in card.colors:
                if color == cardcolor:
                    matchedCards.append(card)
        matchedColors[color] = matchedCards

    # Remove cards if they aren't enough to discard
    keysToRemove = []
    for key in matchedColors:
        if len(matchedColors[key]) < int(topCard.value):
            keysToRemove.append(key)

    for key in keysToRemove:
        del matchedColors[key]

    return matchedColors


def checkForActionCards(matchedCards: dict) -> list:
    """ Check if current player has any action cards that are valid to discard

    :param matchedCards: List of current players cards completing a set
    :return: list of valid action cards
    """

    actionCardsList = []
    uniqueActionCards = []

    for color in matchedCards:
        for card in matchedCards[color]:
            if not card.type == "number":
                actionCardsList.append(card)

    for card in actionCardsList:
        if card in uniqueActionCards:
            pass
        else:
            uniqueActionCards.append(card)

    return uniqueActionCards
