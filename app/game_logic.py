from random import randint
from .models import User, Adventure, LootBox, PrizeType, Prize
from . import db
from datetime import datetime, timedelta

# The AdventureManager manages the logic for user adventures.
class AdventureManager:
    # The constructor initializes the manager with a user.
    def __init__(self, user):
        self.user = user

    # Static method to check if a user is eligible for an adventure.
    @staticmethod
    def is_eligible(user):
        # Fetch the last adventure of the user.
        last_adventure = Adventure.query.filter_by(user_id=user.id).order_by(Adventure.timestamp.desc()).first()
        # If there's a last adventure, check if it's been more than a day since the last adventure.
        if last_adventure:
            now = datetime.utcnow()
            time_since_last_adventure = now - last_adventure.timestamp
            return time_since_last_adventure > timedelta(days=1)
        # If no previous adventure, the user is eligible.
        return True

    # Create a new adventure for the user.
    def create(self):
        rng_score = self._generate_random_number()
        material = self._determine_material(rng_score)
        self._update_user_threshold(material)
        
        # Create a new adventure record and add it to the session.
        new_adventure = Adventure(rng_score=rng_score, material=material, user_id=self.user.id, status="In Progress")
        db.session.add(new_adventure)

        # Update the status based on the material.
        if material == "None":
            new_adventure.status = "No Material"
        else:
            new_adventure.status = "Unused Material"

        # Commit the changes to the database.
        db.session.commit()
        return new_adventure

    # Generate a random number between 1 and the user's current threshold.
    def _generate_random_number(self):
        return randint(1, self.user.current_threshold)

    # Determine the material based on the generated random number.
    def _determine_material(self, rng_score):
        if rng_score < 5:
            return "Legendary"
        elif rng_score < 20:
            return "Elite"
        elif rng_score < 50:
            return "Rare"
        elif rng_score < 100:
            return "Uncommon"
        elif rng_score < 175:
            return "Common"
        else:
            return "None"

    # Update the user's threshold based on the material.
    def _update_user_threshold(self, material):
        if material in ["Uncommon", "Common", "None"]:
            self.user.current_threshold -= 10
        else:
            self.user.current_threshold = self.user.reset_threshold
            if self.user.reset_threshold > 400:
                self.user.reset_threshold -= 5
            self.user.current_threshold = max(self.user.current_threshold, 400)

# The LootBoxManager manages the logic for creating lootboxes.
class LootBoxManager:
    # The constructor initializes the manager with a user and material IDs.
    def __init__(self, user, material_ids):
        self.user = user
        self.material_ids = material_ids

    # Create a lootbox.
    def create(self):
        # Fetch the adventures corresponding to the material IDs.
        adventures = Adventure.query.filter(Adventure.id.in_(self.material_ids)).all()
        sum_rng_scores = 0
        # Validate the adventures and sum up their rng_scores.
        for adventure in adventures:
            if adventure.status != "Unused Material":
                return "Error: Cannot use already used or ineligible material"
            sum_rng_scores += adventure.rng_score

        # Determine the lootbox rarity based on the summed rng_scores.
        rarity = self._determine_lootbox_rarity(sum_rng_scores)

        # Update the adventure statuses to "Used Material".
        for adventure in adventures:
            adventure.status = "Used Material"

        # Create a new lootbox record and add it to the session.
        new_lootbox = LootBox(rarity=rarity, user_id=self.user.id)
        db.session.add(new_lootbox)

        # Create a new prize for the user based on the lootbox's rarity.
        prize_manager = PrizeManager(self.user, new_lootbox)
        new_prize = prize_manager.create()

        # Commit the changes to the database.
        db.session.commit()

        return new_lootbox, new_prize

    # Determine lootbox rarity based on the summed rng_scores.
    def _determine_lootbox_rarity(self, sum_rng_scores):
        scaled_sum = sum_rng_scores / 5
        if scaled_sum < 5:
            return "Legendary"
        elif scaled_sum < 20:
            return "Elite"
        elif scaled_sum < 50:
            return "Rare"
        elif scaled_sum < 100:
            return "Uncommon"
        else:
            return "Common"

# The PrizeManager manages the logic for awarding prizes.
class PrizeManager:
    # The constructor initializes the manager with a user and a lootbox.
    def __init__(self, user, lootbox):
        self.user = user
        self.lootbox = lootbox

    # Create a prize for the user.
    def create(self):
        # Fetch a prize type based on the lootbox's rarity that hasn't been fully claimed yet.
        prize_type = PrizeType.query.filter_by(rarity=self.lootbox.rarity).filter(PrizeType.number_claimed < PrizeType.quanity).first()

        if not prize_type:
            return "Error: No available prize for this rarity"

        # Create a new prize record for the user and add it to the session.
        new_prize = Prize(user_id=self.user.id, prize_type_id=prize_type.id)
        db.session.add(new_prize)

        # Increment the number_claimed counter for the prize type.
        prize_type.number_claimed += 1

        return new_prize
