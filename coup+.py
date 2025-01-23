import random
import time

class Card:
    def __init__(self, name):
        self.name = name
        self.alive = True

    def display_name(self, reveal=False):
        if self.alive:
            return self.name if reveal else "Unknown"
        else:
            # ANSI escape code for strikethrough
            return f"\x1b[9m{self.name}\x1b[0m"

class Player:
    def __init__(self, name, is_bot=False):
        self.name = name
        self.coins = 2
        self.cards = []
        self.in_game = True
        self.influences = 2
        self.is_bot = is_bot

    def lose_influence(self):
        alive_cards = [card for card in self.cards if card.alive]
        if alive_cards:
            print(f"{self.name}, choose a card to lose:")
            for idx, card in enumerate(alive_cards):
                # Reveal the actual card names for human players
                if self.is_bot:
                    print(f"{idx + 1}. {card.display_name(reveal=False)}")
                else:
                    print(f"{idx + 1}. {card.display_name(reveal=True)}")  # Changed reveal to True
            while True:
                try:
                    if self.is_bot:
                        choice = random.randint(0, len(alive_cards) - 1)
                        print(f"{self.name} chooses to lose card {choice + 1}.")
                    else:
                        choice = int(input("> ")) - 1
                    if 0 <= choice < len(alive_cards):
                        break
                    else:
                        print("Invalid choice. Please enter a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            chosen_card = alive_cards[choice]
            chosen_card.alive = False
            print(f"{self.name} has lost influence: {chosen_card.display_name(reveal=True)}")
            if all(not card.alive for card in self.cards):
                self.in_game = False
                print(f"{self.name} has been eliminated.")

    def choose_action(self, players, deck):
        time.sleep(2)  # Delay for bot action
        if self.coins >= 10:
            return "Coup"
        elif self.coins >= 7:
            action = random.choices(
                ["Coup", "Assassinate"], weights=[70, 30], k=1
            )[0]
            return action
        elif self.coins >= 3:
            action = random.choices(
                ["Assassinate", "Exchange", "Steal", "Foreign Aid", "Income"], weights=[40, 10, 10, 20, 20], k=1
            )[0]
            return action
        else:
            return random.choice(["Exchange", "Steal", "Foreign Aid", "Income"])

def initialize_deck():
    characters = ['Duke', 'Assassin', 'Captain', 'Ambassador', 'Contessa']
    deck = [Card(name) for name in characters for _ in range(3)]
    random.shuffle(deck)
    return deck

def get_players():
    while True:
        try:
            num_players = int(input("Enter number of players (2-6): "))
            if 2 <= num_players <= 6:
                break
            else:
                print("Please enter a number between 2 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    players = []
    human_name = input("Enter your name: ")
    players.append(Player(human_name, is_bot=False))
    for i in range(1, num_players):
        bot_name = input(f"Enter name for Bot {i}: ")
        players.append(Player(bot_name, is_bot=True))
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
    if player.is_bot:
        return player.choose_action(players, deck)
    actions = get_available_actions(player)
    print("Choose an action:")
    for idx, action in enumerate(actions):
        print(f"{idx + 1}. {action}")
    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(actions):
                print()
                return actions[choice - 1]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(actions)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def draw_unique_card(deck, existing_cards):
    while True:
        if not deck:
            print("The deck is out of cards. Cannot draw a new card.")
            return None
        card = deck.pop()
        if card not in existing_cards:
            return card

def swap_card(player, deck, players):
    # Find the card that was bluffed and replace it
    for card in player.cards:
        if card.alive:
            # Remove the card and add a new unique card from the deck
            player.cards.remove(card)
            new_card = draw_unique_card(deck, player.cards + [c for p in players if p != player for c in p.cards])
            if new_card:
                player.cards.append(new_card)
                print(f"{player.name} has received a new card: {new_card.display_name(reveal=True)}")
            break

def action_challenge(player, action, players, deck):
    """
    Handles challenges to a player's claim to perform an action.

    Returns:
        True if the action was successful (either not challenged or successfully defended),
        False if the action failed due to a failed challenge.
    """
    challengers = [p for p in players if p != player and p.in_game]
    for challenger in challengers:
        if challenger.is_bot:
            # Bot decides to challenge based on random probability
            challenge_decision = random.choices(["yes", "no"], weights=[30, 70], k=1)[0]
            response = challenge_decision
            print(f"{challenger.name} has decided to {'challenge' if response == 'yes' else 'not challenge'} {player.name}'s claim to perform {action}.")
        else:
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
                if new_card:
                    player.cards.append(new_card)
                    if player.is_bot:
                        # Do not reveal the new card for bots
                        print(f"{player.name} swaps out {truthful_card.name} for a new card.")
                    else:
                        # Reveal the new card for human players
                        print(f"{player.name} swaps out {truthful_card.name} for a new card: {new_card.display_name(reveal=True)}")
                
                return True  # Action succeeds
            else:
                print(f"{player.name} was bluffing!")
                player.lose_influence()
                return False  # Action fails
    # No one challenged the action
    return True  # Action succeeds

def block_action(player, action, players, deck):
    """
    Handles the blocking of specific actions, such as using Contessa to block an assassination.
    """
    challengers = [p for p in players if p != player and p.in_game]
    for challenger in challengers:
        if challenger.is_bot:
            # Bot decides to challenge based on random probability
            challenge_decision = random.choices(["yes", "no"], weights=[20, 80], k=1)[0]
            response = challenge_decision
            print(f"{challenger.name} has decided to {'challenge' if response == 'yes' else 'not challenge'} {player.name}'s claim to block with {action}.")
        else:
            print(f"{challenger.name}, do you want to challenge {player.name}'s claim to block with {action}? (yes/no)")
            response = input("> ").lower()
        if response == "yes":
            if any(card.name == action and card.alive for card in player.cards):
                print(f"{player.name} was truthful and blocked the action with {action}!")
                challenger.lose_influence()
            else:
                print(f"{player.name} was bluffing about having {action}!")
                player.lose_influence()
                return False  # Block fails if the player was bluffing
            return True  # Block succeeds if not challenged or truthful
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
            available_targets = [p for p in players if p.in_game and p != player]
            if not available_targets:
                print("No available players to Coup.")
                current_player_idx = (current_player_idx + 1) % len(players)
                continue
            if player.is_bot:
                target = random.choice(available_targets)
                print(f"{player.name} performs a Coup against {target.name}.")
            else:
                while True:
                    target_name = input("Choose a player to Coup: ")
                    target = next((p for p in available_targets if p.name == target_name), None)
                    if target:
                        print(f"{player.name} performs a Coup against {target.name}.")
                        break
                    else:
                        print("Invalid target. Please choose a different player.")
            target.lose_influence()

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
        if not player.is_bot:
            print("Cards:", ", ".join(card.display_name(reveal=True) for card in player.cards))
        else:
            # Hide bots' cards unless a card has been lost
            alive_cards = [card.display_name(reveal=False) for card in player.cards if card.alive]
            lost_cards = [card.display_name(reveal=True) for card in player.cards if not card.alive]
            displayed_cards = alive_cards + lost_cards
            print("Cards:", ", ".join(displayed_cards))
        print()
        
        actions = get_available_actions(player)
        action = get_action(player)
        
        if action.startswith("Income"):
            player.coins += 1
            print(f"{player.name} takes Income.")
        elif action.startswith("Foreign Aid"):
            print(f"{player.name} attempts to take Foreign Aid.")
            blockers = [p for p in players if p != player and p.in_game]
            blocked_successfully = False  # Flag to track successful block

            for blocker in blockers:
                if blocker.is_bot:
                    # Bot decides to block with Duke based on some probability
                    block_decision = random.choices(["yes", "no"], weights=[30, 70], k=1)[0]
                    response = block_decision
                    print(f"{blocker.name} has decided to {'block' if response == 'yes' else 'not block'} Foreign Aid with Duke.")
                else:
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
                    current_player_idx = (current_player_idx + 1) % len(players)
                    continue
                if player.is_bot:
                    target = random.choice(available_targets)
                    print(f"{player.name} performs a Coup against {target.name}.")
                else:
                    while True:
                        target_name = input("Choose a player to Coup: ")
                        target = next((p for p in available_targets if p.name == target_name), None)
                        if target:
                            print(f"{player.name} performs a Coup against {target.name}.")
                            break
                        else:
                            print("Invalid target. Please choose a different player.")
                target.lose_influence()
        elif action.startswith("Tax"):
            if action_challenge(player, "Duke", players, deck):
                player.coins += 3
                print(f"{player.name} takes Tax.")
            else:
                print(f"{player.name} failed to take Tax.")
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
                    if player.is_bot:
                        target = random.choice(available_targets)
                        print(f"{player.name} attempts to assassinate {target.name}.")
                    else:
                        while True:
                            target_name = input("Choose a player to assassinate: ")
                            target = next((p for p in available_targets if p.name == target_name), None)
                            if target:
                                break
                            else:
                                print("Invalid target. Please choose a different player.")
                    if target.is_bot:
                        contessa = any(card.name == "Contessa" and card.alive for card in target.cards)
                        if contessa:
                            print(f"{target.name} blocks the assassination with Contessa.")
                            if block_action(target, "Contessa", players, deck):
                                print(f"{target.name}'s block with Contessa was successful. Assassination blocked.")
                            else:
                                target.lose_influence()
                                print(f"{player.name} successfully assassinates {target.name}.")
                        else:
                            # Bot decides to bluff or not bluff Contessa
                            bluff = random.choices([True, False], weights=[30, 70], k=1)[0]
                            if bluff:
                                print(f"{target.name} attempts to block the assassination by claiming Contessa.")
                                if block_action(target, "Contessa", players, deck):
                                    print(f"{target.name}'s block with Contessa was successful (bluffed). Assassination blocked.")
                                else:
                                    target.lose_influence()
                                    print(f"{player.name} successfully assassinates {target.name}.")
                            else:
                                target.lose_influence()
                                print(f"{player.name} successfully assassinates {target.name}.")
                    else:
                        print(f"{target.name}, do you want to block the assassination with Contessa? (yes/no)")
                        block_response = input("> ").lower()
                        if block_response == "yes":
                            if block_action(target, "Contessa", players, deck):
                                print(f"{target.name}'s block with Contessa was successful. Assassination blocked.")
                            else:
                                target.lose_influence()
                                print(f"{player.name} successfully assassinates {target.name}.")
                        else:
                            target.lose_influence()
                            print(f"{player.name} successfully assassinates {target.name}.")
        elif action.startswith("Exchange"):
            # Handle challenges to the Ambassador action before proceeding
            if action_challenge(player, "Ambassador", players, deck):
                print(f"{player.name} chooses to use the Ambassador to exchange cards.")

                if len(deck) < 2:
                    print("Not enough cards in the deck to perform an exchange.\n")
                    continue  # Skip exchange if not enough cards

                # Draw two cards from the deck
                if player.is_bot:
                    # For bots, draw two cards without revealing them
                    drawn_cards = [deck.pop(), deck.pop()]
                    print(f"{player.name} has exchanged cards with the deck.")
                else:
                    # For human players, reveal the drawn cards
                    drawn_cards = [deck.pop(), deck.pop()]
                    print(f"Drawn cards: {drawn_cards[0].display_name(reveal=True)}, {drawn_cards[1].display_name(reveal=True)}\n")

                # Display player's current cards (only for human players)
                if not player.is_bot:
                    print("Your current cards:")
                    for idx, card in enumerate(player.cards, 1):
                        print(f"{idx}. {card.display_name(reveal=True)}")
                    print()

                # Combine current and drawn cards
                all_cards = player.cards + drawn_cards

                if not player.is_bot:
                    print("Choose two different cards to keep from your hand and the drawn cards.\n")
                    # Display all available cards to human players
                    for idx, card in enumerate(all_cards, 1):
                        print(f"{idx}. {card.display_name(reveal=True)}")
                    print()

                if player.is_bot:
                    # Bot selects two unique indices from available cards without revealing them
                    chosen_indices = random.sample(range(len(all_cards)), 2)
                    chosen_cards = [all_cards[i] for i in chosen_indices]
                    # No need to print the chosen cards
                else:
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
                            chosen_cards = [all_cards[i - 1] for i in indices]
                            break
                        except ValueError:
                            print("Invalid input. Please enter numbers only.\n")

                    # Determine unused cards based on user-chosen indices
                    unused_cards = [all_cards[i - 1] for i in range(1, len(all_cards)+1) if i not in indices]

                if player.is_bot:
                    # Return the unused cards to the deck without revealing them
                    unused_cards = [all_cards[i] for i in range(len(all_cards)) if i not in chosen_indices]
                    deck.extend(unused_cards)
                    random.shuffle(deck)
                    print()
                else:
                    # Return the unused cards to the deck
                    deck.extend(unused_cards)
                    random.shuffle(deck)
                    print()

                # Update player's hand
                player.cards = chosen_cards
                if not player.is_bot:
                    print("Your cards have been updated.\n")
            else:
                # Action was challenged and failed; do not perform the exchange
                print(f"{player.name}'s Exchange action was unsuccessful due to a failed challenge.")
        elif action.startswith("Steal"):
            target_name = None
            target = None
            if player.is_bot:
                available_targets = [p for p in players if p.in_game and p != player]
                target = random.choice(available_targets)
                target_name = target.name
                print(f"{player.name} attempts to steal from {target.name}.")
            else:
                target_name = input("Choose a player to steal from: ")
                target = next((p for p in players if p.name == target_name and p.in_game), None)
                if not target:
                    print("Invalid target. Steal failed.")
                    current_player_idx = (current_player_idx + 1) % len(players)
                    continue

            # First, handle challenges to the Captain claim
            action_success = action_challenge(player, "Captain", players, deck)

            if action_success:
                # Proceed to target's decision to allow or block
                if target.is_bot:
                    # Bot decides randomly to allow or block
                    block_choice = random.choices([1, 2, 3], weights=[50, 25, 25], k=1)[0]
                    print(f"{target.name} chooses option {block_choice}.")
                else:
                    print(f"{target.name}, choose an option:")
                    print("1. Allow the steal.")
                    print("2. Block with Captain.")
                    print("3. Block with Ambassador.")
                    while True:
                        try:
                            block_choice = int(input("> "))
                            if block_choice in [1, 2, 3]:
                                break
                            else:
                                print("Invalid choice. Please select 1, 2, or 3.")
                        except ValueError:
                            print("Invalid input. Please enter a number (1, 2, or 3).")

                if block_choice == 1:
                    amount = min(2, target.coins)
                    target.coins -= amount
                    player.coins += amount
                    print(f"{player.name} steals {amount} coins from {target.name}.")
                elif block_choice in [2, 3]:
                    block_role = "Captain" if block_choice == 2 else "Ambassador"
                    print(f"{target.name} attempts to block the steal with {block_role}.")
                    if target.is_bot:
                        # Bot decides to challenge the block based on having the role
                        if any(card.name == block_role and card.alive for card in target.cards):
                            challenge_decision = random.choices(["yes", "no"], weights=[60, 40], k=1)[0]
                            response = challenge_decision
                            print(f"{target.name} has decided to {'challenge' if response == 'yes' else 'not challenge'} the block.")
                        else:
                            response = "no"
                            print(f"{target.name} does not have {block_role} and cannot block.")
                    else:
                        response = "yes"  # Assume player chooses to block if option 2 or 3 selected

                    if response == "yes":
                        if block_action(target, block_role, players, deck):
                            print(f"{target.name}'s block with {block_role} was successful. Steal is blocked.")
                        else:
                            amount = min(2, target.coins)
                            target.coins -= amount
                            player.coins += amount
                            print(f"{player.name} steals {amount} coins from {target.name}.")
                    else:
                        amount = min(2, target.coins)
                        target.coins -= amount
                        player.coins += amount
                        print(f"{player.name} steals {amount} coins from {target.name}.")
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
    global deck, players
    deck = initialize_deck()
    players = get_players()
    deal_cards(players, deck)
    main_game_loop(players, deck)

if __name__ == "__main__":
    main()
