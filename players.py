import random
import logging
import csv
from abc import ABC, abstractmethod
from typing import Tuple, Optional, List
from model_manager import ModelManager
from generate_image_caption import ImageCaptionGenerator
from abstractor import Abstractor
from text_processor import TextProcessor
from similarity import ImageTextSimilarity

logger = logging.getLogger('game_logic')

class Player(ABC):
    def __init__(self, name: str, player_id: int, model_manager=None):
        self.name = name
        self.player_id = player_id
        self.hand = []
        self.score = 0
        self._model_manager = model_manager

    @abstractmethod
    def storyteller_turn(self) -> Tuple[str, str]:
        pass

    @abstractmethod
    def choose_card(self) -> Optional[str]:
        pass

    @abstractmethod
    def vote(self, table: List[Tuple[int, str]], clue: str) -> int:
        pass


class Human(Player):
    def storyteller_turn(self) -> Tuple[str, str]:
        logger.info(f"{self.name} (Storyteller) is choosing a card and inputting a clue.")
        chosen_card = self.choose_card()
        clue = self.input_clue()
        return chosen_card, clue

    def choose_card(self) -> Optional[str]:
        if not self.hand:
            logger.error("No cards left to choose from.")
            return None

        print("Your hand:")
        for index, card in enumerate(self.hand):
            print(f"{index + 1}: {card}")

        while True:
            try:
                choice = int(input("Choose a card by entering its number: ")) - 1
                if 0 <= choice < len(self.hand):
                    chosen_card = self.hand.pop(choice)
                    logger.info(f"Card chosen: {chosen_card}")
                    return chosen_card
                else:
                    print("Invalid choice. Please select a valid card number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    def input_clue(self) -> str:
        clue = input("Enter a clue for your card: ").strip()
        logger.info(f"Clue entered: {clue}")
        return clue

    def choose_card_based_on_clue(self, clue: str) -> str:
        return self.choose_card()

    def vote(self, table, clue) -> int:
        if not table:
            logger.error("No cards on the table to vote on.")
            return None

        print("Cards on the table:")
        for index, (card) in enumerate(table):
            print(f"{index + 1}: {card}")

        while True:
            try:
                vote = int(input("Vote for the card you think belongs to the storyteller by entering its number: ")) - 1
                if 0 <= vote < len(table):
                    logger.info(f"Vote chosen: {vote}")
                    return vote
                else:
                    print("Invalid choice. Please select a valid card number.")
            except ValueError:
                print("Invalid input. Please enter a number.")


class Bot(Player):
    def __init__(self, name: str, model_manager: ModelManager):
        super().__init__(name=name, player_id=None, model_manager=model_manager)
        self._caption_generator = ImageCaptionGenerator(self._model_manager)
        self._similarity_checker = ImageTextSimilarity(self._model_manager)
        self._abstractor = Abstractor()
        self._text_processor = TextProcessor()
        self.storyteller_card = ""

    def storyteller_turn(self) -> Tuple[str, str]:
        card = random.choice(self.hand)
        self.storyteller_card = card
        clue = self.generate_clue(card)
        # line for debugging, players shouldn't see the card the storyteller picks
        # print(f"{self.name} (Storyteller) selected card: {card} with clue: '{clue}'")
        print(f"{self.name} (Storyteller) selected card and provided the clue: '{clue}'")
        return card, clue

    def generate_clue(self, card: str) -> str:
        caption = ""
        with open("cache.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                cur_card = row[0].strip()
                description = row[1].strip()
                if (cur_card == card):
                    caption = description
                    break
        obfuscated_caption = self._text_processor.obfuscate_description(caption, self._abstractor)
        return obfuscated_caption

    def choose_card_based_on_clue(self, clue) -> Optional[str]:
        selected = []
        if not self.hand:
            logger.error(f"{self.name} has no cards left to choose from based on the clue.")
            return None

        similarities = [
            (self._similarity_checker.compare_image_and_text(card, clue), card)
            for card in self.hand
        ]

        if not similarities:
            logger.error(f"{self.name} could not find any matching cards based on the clue.")
            return None
        
        similarities.sort(reverse=True, key=lambda x: x[0])
        x = 0 
        while x < 5:
            selected.append(similarities.pop(0))
            x += 1
        return selected

    def vote(self, table, clue) -> int:
        similarities = [
            (self._similarity_checker.compare_image_and_text(card, clue), card)
            for card in table
        ]
        similarities.sort(reverse=True, key=lambda x: x[0])
        return similarities[0][1]

    def choose_card(self) -> Optional[str]:
        if not self.hand:
            logger.error("Bot has no cards left to choose from.")
            return None

        chosen_card = random.choice(self.hand)
        self.hand.remove(chosen_card)
        logger.info(f"Bot {self.name} chose card: {chosen_card}")
        return chosen_card
