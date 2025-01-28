# Coup without bots

import random

class Card:
    def __init__(self, name):
        self.name = name
        self.alive = True

    def display_name(self):
        if self.alive:
            return self.name
        else:
            # ANSI escape code for strikethrough
            return f"\x1b[9m{self.name}\x1b[0m"

class Player:
    def __init__(self, name):
        self.name = name
        self.coins = 2
        self.cards = []
        self.in_game = True
        self.influences = 2

    def lose_influence(self):
        alive_cards = [card for card in self.cards if card.alive]
        if alive_cards:
            print(f"{self.name}, choose a card to lose:")
            for idx, card in enumerate(alive_cards):
                print(f"{idx + 1}. {card.display_name()}")
            while True:
                try:
                    choice = int(input("> ")) - 1
                    if 0 <= choice < len(alive_cards):
                        break
                    else:
                        print("Invalid choice. Please enter a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            alive_cards[choice].alive = False
            print(f"{self.name} has lost influence: {alive_cards[choice].display_name()}")
            if all(not card.alive for card in self.cards):
                self.in_game = False
                print(f"{self.name} has been eliminated.")

def initialize_deck():
    characters = ['Duke', 'Assassin', 'Captain', 'Ambassador', 'Contessa']
    deck = [Card(name) for name in characters for _ in range(3)]
    random.shuffle(deck)
    return deck

def get_players():
    num_players = int(input("Enter number of players (2-6): "))
    players = []
    for i in range(num_players):
        name = input(f"Enter name for player {i + 1}: ")
        players.append(Player(name))
    print()
    return players

def deal_cards(players, deck):
    for player in players:
        player.cards.extend([deck.pop(), deck.pop()])
        # Don't reveal cards here to keep them hidden from others

def get_available_actions(player):
    actions = [
        "Income (Take 1 coin)",
        "Foreign Aid (Take 2 coins)",
        "Coup (Pay 7 coins to eliminate another player)",
        "Tax (Duke - Take 3 coins)",
        "Assassinate (Assassin - Pay 3 coins to eliminate a player)",
        "Exchange (Ambassador - Exchange cards with the court deck)",
        "Steal (Captain - Take 2 coins from another player)"
    ]
    return actions

def get_action(player):
    actions = get_available_actions(player)
    print("Choose an action:")
    for idx, action in enumerate(actions):
        print(f"{idx + 1}. {action}")
    choice = int(input("> "))
    return choice

def draw_unique_card(deck, existing_cards):
    while True:
        card = deck.pop()
        if card not in existing_cards:
            return card

def swap_card(player, deck, players):
    # Find the card that was bluffed and replace it
    for card in player.cards:
        if card.alive:
            # Remove the card and add a new unique card from the deck
            player.cards.remove(card)
            new_card = draw_unique_card(deck, player.cards + [c for p in players for c in p.cards if p != player])
            player.cards.append(new_card)
            print(f"{player.name} has received a new card: {new_card.display_name()}")
            break

def action_challenge(player, action, players, deck):
    """
    Handles challenges to a player's claim to perform an action.

    Returns:
        True if the action was successful (either not challenged or successfully defended),
        False if the action failed due to a failed challenge.
    """
    for challenger in players:
        if challenger != player and challenger.in_game:
            print(f"{challenger.name}, do you want to challenge {player.name}'s claim to perform {action}? (yes/no)")
            response = input("> ").lower()
            if response == "yes":
                if any(card.name == action for card in player.cards if card.alive):
                    print(f"{player.name} was truthful!")
                    challenger.lose_influence()
                    
                    # Swap the truthful card with a new one from the deck
                    truthful_card = next(card for card in player.cards if card.name == action and card.alive)
                    player.cards.remove(truthful_card)
                    deck.append(truthful_card)
                    random.shuffle(deck)
                    
                    # Draw a new unique card for the player
                    new_card = draw_unique_card(deck, [c.name for c in player.cards if c.alive])
                    player.cards.append(new_card)
                    print(f"{player.name} swaps out {truthful_card.display_name()} for a new card: {new_card.display_name()}")
                    
                    return True  # Action succeeds
                else:
                    print(f"{player.name} was bluffing!")
                    player.lose_influence()
                    swap_card(player, deck, players)
                    return False  # Action fails
    # No one challenged the action
    return True  # Action succeeds

def block_action(player, action, players):
    """
    Handles the blocking of specific actions, such as using Contessa to block an assassination.
    """
    for challenger in players:
        if challenger != player and challenger.in_game:
            print(f"{challenger.name}, do you want to challenge {player.name}'s claim to block with {action}? (yes/no)")
            response = input("> ").lower()
            if response == "yes":
                if any(card.name == action and card.alive for card in player.cards):
                    print(f"{player.name} was truthful and blocked the assassination with {action}!")
                    challenger.lose_influence()
                else:
                    print(f"{player.name} was bluffing about having {action}!")
                    player.lose_influence()
                    return False  # Block fails if the player was bluffing
                return True  # Block succeeds if no one challenges or player was truthful
    return True  # Block succeeds if no one challenges

def main_game_loop(players, deck):
    current_player_idx = 0
    while sum(p.in_game for p in players) > 1:
        player = players[current_player_idx]
        if not player.in_game:
            current_player_idx = (current_player_idx + 1) % len(players)
            continue

        if player.coins >= 10:
            print(f"{player.name} has 10 or more coins and must perform a Coup.")
            player.coins -= 7
            target_name = input("Choose a player to Coup: ")
            target = next((p for p in players if p.name == target_name and p.in_game), None)
            if target:
                target.lose_influence()
                print(f"{player.name} has couped {target.name}.")
            else:
                print("Invalid target. Coup failed.")
            
            # Check for eliminated players
            for p in players:
                if p.in_game and p.influences <= 0:
                    p.in_game = False
                    print(f"{p.name} has been eliminated from the game.")

            # Check for winner
            active_players = [p for p in players if p.in_game]
            if len(active_players) == 1:
                winner = active_players[0]
                print(f"{winner.name} is the winner!")
                break

            current_player_idx = (current_player_idx + 1) % len(players)
            continue  # Skip the rest of the loop and proceed to the next player

        print(f"\n\n{player.name}'s Turn")
        print(f"Coins: {player.coins}")
        print("Cards:", ", ".join(card.display_name() for card in player.cards))
        print()
        
        actions = get_available_actions(player)
        while True:
            try:
                action_idx = get_action(player)
                if 1 <= action_idx <= len(actions):
                    break
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(actions)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        action = actions[action_idx - 1]
        
        if action.startswith("Income"):
            player.coins += 1
            print(f"{player.name} takes Income.")
        elif action.startswith("Foreign Aid"):
            print(f"{player.name} attempts to take Foreign Aid.")
            blockers = [p for p in players if p != player and p.in_game]
            blocked_successfully = False  # Flag to track successful block

            for blocker in blockers:
                print(f"{blocker.name}, do you want to block {player.name}'s Foreign Aid with Duke? (yes/no)")
                response = input("> ").lower()
                if response == "yes":
                    print(f"{blocker.name} attempts to block with Duke.")
                    if action_challenge(blocker, "Duke", players, deck):
                        print(f"{blocker.name}'s block with Duke was successful. Foreign Aid is blocked.")
                        blocked_successfully = True
                        break
                    else:
                        print(f"{blocker.name} failed to block Foreign Aid.")

            if not blocked_successfully:
                player.coins += 2
                print(f"{player.name} takes Foreign Aid and now has {player.coins} coins.")
        elif action.startswith("Coup"):
            if player.coins < 7:
                print("Not enough coins to perform a Coup.")
            else:
                player.coins -= 7
                available_targets = [p for p in players if p.in_game and p != player]
                if not available_targets:
                    print("No available players to Coup.")
                    continue
                while True:
                    target_name = input("Choose a player to Coup: ")
                    target = next((p for p in available_targets if p.name == target_name), None)
                    if target:
                        target.lose_influence()
                        print(f"{player.name} performs a Coup against {target.name}.")
                        break
                    else:
                        print("Invalid target. Please choose a different player.")
        elif action.startswith("Tax"):
            if not action_challenge(player, "Duke", players, deck):
                player.coins += 3
                print(f"{player.name} takes Tax.")
        elif action.startswith("Assassinate"):
            if player.coins < 3:
                print("Not enough coins to perform Assassination.")
            else:
                player.coins -= 3  # Pay the cost first
                if not action_challenge(player, "Assassin", players, deck):
                    print(f"{player.name}'s assassination claim was challenged and failed.")
                    # Player has already lost an influence in action_challenge
                else:
                    available_targets = [p for p in players if p.in_game and p != player]
                    if not available_targets:
                        print("No available players to assassinate.")
                        continue
                    while True:
                        target_name = input("Choose a player to assassinate: ")
                        target = next((p for p in available_targets if p.name == target_name), None)
                        if target:
                            # Give the target a chance to block with Contessa
                            print(f"{target.name}, do you want to block the assassination with Contessa? (yes/no)")
                            block_response = input("> ").lower()
                            if block_response == "yes":
                                if block_action(target, "Contessa", players):
                                    print(f"{target.name} blocked the assassination with Contessa.")
                                else:
                                    target.lose_influence()
                                    print(f"{player.name} successfully assassinates {target.name}.")
                            else:
                                target.lose_influence()
                                print(f"{player.name} successfully assassinates {target.name}.")
                            break
                        else:
                            print("Invalid target. Please choose a different player.")
        elif action.startswith("Exchange"):
            # Handle challenges to the Ambassador action before proceeding
            if action_challenge(player, "Ambassador", players, deck):
                print(f"{player.name} chooses to use the Ambassador to exchange cards.")

                if len(deck) < 2:
                    print("Not enough cards in the deck to perform an exchange.\n")
                    continue  # Skip exchange if not enough cards

                # Draw two cards from the deck
                drawn_cards = [deck.pop(), deck.pop()]
                print(f"Drawn cards: {drawn_cards[0].name}, {drawn_cards[1].name}\n")

                # Display player's current cards
                print("Your current cards:")
                for idx, card in enumerate(player.cards, 1):
                    print(f"{idx}. {card.display_name()}")
                print()

                # Prompt player to choose which cards to keep
                print("Choose two different cards to keep from your hand and the drawn cards.\n")
                
                all_cards = player.cards + drawn_cards
                for idx, card in enumerate(all_cards, 1):
                    print(f"{idx}. {card.display_name()}")
                print()

                # Get player's selection
                while True:
                    try:
                        choices = input("Enter the numbers of the two cards you want to keep, separated by space: ").strip()
                        indices = list(map(int, choices.split()))
                        
                        if (
                            len(indices) != 2 or
                            not all(1 <= i <= len(all_cards) for i in indices) or
                            len(set(indices)) != 2
                        ):
                            print(f"Invalid input. Please enter two different numbers between 1 and {len(all_cards)}.\n")
                            continue
                        break
                    except ValueError:
                        print("Invalid input. Please enter numbers only.\n")

                # Select the chosen cards
                chosen_cards = [all_cards[i - 1] for i in indices]

                # Return the unused cards to the deck
                unused_cards = [card for idx, card in enumerate(all_cards, 1) if idx not in indices]
                deck.extend(unused_cards)
                random.shuffle(deck)
                print()

                # Update player's hand
                player.cards = chosen_cards
                print("Your cards have been updated.\n")
            else:
                # Action was challenged and failed; do not perform the exchange
                print(f"{player.name}'s Exchange action was unsuccessful due to a failed challenge.")
        elif action.startswith("Steal"):
            target_name = input("Choose a player to steal from: ")
            target = next((p for p in players if p.name == target_name and p.in_game), None)
            if not target:
                print("Invalid target. Steal failed.")
                continue

            # Player attempts to Steal and claims to have Captain
            if action_challenge(player, "Captain", players, deck):
                # Action was successful; proceed to target's choice
                print(f"{target.name}, choose an option:")
                print("1. Allow the steal.")
                print("2. Block with Captain.")
                print("3. Block with Ambassador.")
                while True:
                    try:
                        block_choice = int(input("> "))
                        if block_choice == 1:
                            amount = min(2, target.coins)
                            target.coins -= amount
                            player.coins += amount
                            print(f"{player.name} steals {amount} coins from {target.name}.")
                            break
                        elif block_choice in [2, 3]:
                            block_role = "Captain" if block_choice == 2 else "Ambassador"
                            print(f"{target.name} attempts to block the steal with {block_role}.")
                            if action_challenge(target, block_role, players, deck):
                                print(f"{target.name}'s block with {block_role} was successful. Steal is blocked.")
                            else:
                                amount = min(2, target.coins)
                                target.coins -= amount
                                player.coins += amount
                                print(f"{player.name} steals {amount} coins from {target.name}.")
                            break
                        else:
                            print("Invalid choice. Please select 1, 2, or 3.")
                    except ValueError:
                        print("Invalid input. Please enter a number (1, 2, or 3).")
            else:
                # Action was challenged and failed
                print(f"{player.name}'s steal action was unsuccessful.")

        # Check for eliminated players
        for p in players:
            if p.in_game and p.influences <= 0:
                p.in_game = False
                print(f"{p.name} has been eliminated from the game.")

        # Check for winner
        active_players = [p for p in players if p.in_game]
        if len(active_players) == 1:
            winner = active_players[0]
            print(f"{winner.name} is the winner!")
            break

        current_player_idx = (current_player_idx + 1) % len(players)


def main():
    deck = initialize_deck()
    players = get_players()
    deal_cards(players, deck)
    main_game_loop(players, deck)

if __name__ == "__main__":
    main()
