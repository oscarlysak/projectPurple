from random import randint
from .models import User, Adventure, LootBox, PrizeType, Prize
from . import db

from datetime import datetime, timedelta

class AdventureManager:

    def __init__(self, user):
        self.user = user
   
    @staticmethod
    def is_eligible(user):
        last_adventure = Adventure.query.filter_by(user_id=user.id).order_by(Adventure.timestamp.desc()).first()
        if last_adventure:
            now = datetime.utcnow()
            time_since_last_adventure = now - last_adventure.timestamp
            return time_since_last_adventure > timedelta(days=1)
        return True

    def create(self):
        rng_score = self._generate_random_number()
        material = self._determine_material(rng_score)
        self._update_user_threshold(material)
        
        new_adventure = Adventure(rng_score=rng_score, material=material, user_id=self.user.id, status="In Progress")
        db.session.add(new_adventure)
        
        if material == "None":
            new_adventure.status = "No Material"
        else:
            new_adventure.status = "Unused Material"

        db.session.commit()
        return new_adventure

    def _generate_random_number(self):
        return randint(1, self.user.current_threshold)
    
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
        
    def _update_user_threshold(self, material):
        if material in ["Uncommon", "Common", "None"]:
            self.user.current_threshold -= 10
        else:
            self.user.current_threshold = self.user.reset_threshold
            if self.user.reset_threshold > 400:
                self.user.reset_threshold -= 5
            self.user.current_threshold = max(self.user.current_threshold, 400)


class LootBoxManager:
    
    def __init__(self, user, material_ids):
        self.user = user
        self.material_ids = material_ids

    def create(self):
        # Validate material IDs and update their statuses
        adventures = Adventure.query.filter(Adventure.id.in_(self.material_ids)).all()
        sum_rng_scores = 0  # Initialize sum of rng_scores

        for adventure in adventures:
            if adventure.status != "Unused Material":
                return "Error: Cannot use already used or ineligible material"
            sum_rng_scores += adventure.rng_score  # Summing up the rng_scores

        # Determine the rarity based on the sum of rng_scores
        rarity = self._determine_lootbox_rarity(sum_rng_scores)

        for adventure in adventures:
            adventure.status = "Used Material"

        # Create new lootbox
        new_lootbox = LootBox(rarity=rarity, user_id=self.user.id)
        db.session.add(new_lootbox)

        # Create a new prize based on the lootbox's rarity
        prize_manager = PrizeManager(self.user, new_lootbox)
        new_prize = prize_manager.create()

        # Commit all changes to the database
        db.session.commit()

        return new_lootbox, new_prize  # Return both the new lootbox and the new prize

    # Additional method to determine lootbox rarity
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
    
class PrizeManager:
    
    def __init__(self, user, lootbox):
        self.user = user
        self.lootbox = lootbox

    def create(self):
        # Fetch a prize based on the lootbox's rarity
        prize_type = PrizeType.query.filter_by(rarity=self.lootbox.rarity).filter(PrizeType.number_claimed < PrizeType.quanity).first()

        if not prize_type:
            return "Error: No available prize for this rarity"

        # Create a new Prize record
        new_prize = Prize(user_id=self.user.id, prize_type_id=prize_type.id)
        db.session.add(new_prize)

        # Update the number_claimed for the prize type
        prize_type.number_claimed += 1

        return new_prize  # Return the new prize