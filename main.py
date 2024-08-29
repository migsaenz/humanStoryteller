import os 
import sys
import random
import csv
from model_manager import ModelManager
from players import Player, Human, Bot
from typing import List, Tuple

### locked in ###
def load_images_from_directory(directory):
    initial_deck = []
    for filename in os.listdir(directory):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            name = os.path.join(directory, filename)
            initial_deck.append(name)
    return initial_deck


def setup_players(model_manager: ModelManager) -> List[Player]:
    player_name = input("\nEnter player name: ")
    human = (Human(name=player_name, player_id=1))
    storyBot = (Bot(name = "\nBot #1", model_manager=model_manager))
    guessBot = (Bot(name = "\nBot #2", model_manager=model_manager))

    return human, storyBot, guessBot


def collect_cards_from_player(player, storytellerCard, clue):
    table = [storytellerCard]
    selected = player.choose_card_based_on_clue(clue)
    x = 0 
    while x < 5:
        table.append(selected.pop(0)[1])
        x += 1
    random.shuffle(table)
    return table

def collect_votes_from_players(bot, human, table, clue):
    votes = []
    botVote = bot.vote(table, clue)
    humanVote = human.vote(table, clue)
    votes.append(botVote)
    votes.append(humanVote)
    return votes

### locked in ###


def main():
    #print('running main')
    roundNums = int(sys.argv[1])
    botCards = int(sys.argv[2])
    model_manager = ModelManager()
    
    i = 0
    while i < roundNums:
        print("\n\n --- STARTING NEW ROUND ---")
        print("\n...players being initialized...")
        human, storyBot, guessBot = setup_players(model_manager)
        print("\n...deck being made and shuffled...")
        deck = load_images_from_directory("data/images/cards")
        random.shuffle(deck)
        print("\n...bot selecting storyteller card...")
        cur_card = deck.pop(0)
        storyBot.hand.append(cur_card)
        storyTellerCard, clue = storyBot.storyteller_turn()

        j = 0
        print("\n...bot getting cards added to hand...")
        while j < botCards:
            #add cards to bot hand 
            bot_cur = deck.pop(0)
            guessBot.hand.append(bot_cur)
            j += 1
        print("\n...bot picking cards to play for clue...")
        table = collect_cards_from_player(guessBot, storyTellerCard, clue)
        print("\n...voting phase commencing...")
        votes = collect_votes_from_players(guessBot, human, table, clue)
        
        print("\n...finding which card was storyteller's...")
        correctIndex = 0
        k = 0 
        while k < len(table):
            if (table[k] == storyBot.storyteller_card):
                correctIndex = k
                break
            k += 1     
        
        print("\n...checking if human or bot got correct...")
        humanCorrect = 0 
        botCorrect = 0 
        storyTellerSuccess = 0 
        print(" XXXXXX temp test XXXXXX")
        print(votes[0])
        print(correctIndex)
        print(votes[1])
        if (votes[0] == storyBot.storyteller_card):
            botCorrect = 1
        if (votes[1] == correctIndex):
            humanCorrect = 1    
        storyTellerSuccess = abs(humanCorrect-botCorrect)

        print("\n...writing results to csv...")
        with open(f'resultsRounds{roundNums}botCards{botCards}.csv','a', newline='') as csvfile:
            resultWriter = csv.writer(csvfile, delimiter=' ')
            resultWriter.writerow(["human guesser", ",", "round in game", ",", "storyteller success (binary)", ",", "bot correct (binary)", ",", "human correct (binary)"])
            resultWriter.writerow([human.name, ",",  i+1, ",", storyTellerSuccess, ",", botCorrect, ",", humanCorrect])

        
        i += 1 
print(" --- ROUND LIMIT REACHED TERMINATING PROGRAM----")
if __name__ == "__main__":
    main()