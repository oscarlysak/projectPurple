from flask import Blueprint, jsonify, request
from collections import Counter
from .models import User, Adventure
from .game_logic import AdventureManager, LootBoxManager  


# 'main' is the Blueprint name which will be imported and registered in the Flask app.
main = Blueprint('main', __name__)

# Define an endpoint for the adventure creation functionality.
@main.route('/adventure', methods=['POST'])
def adventure_endpoint():
    # Extract the request data as JSON.
    user_data = request.get_json()
    
    # Extract the user ID from the incoming data.
    user_id = user_data['user_id']

    # Try to get the user from the database with the provided ID.
    user = User.query.get(user_id)
    
    # If the user is not found in the database, return an error message.
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if the user is eligible to go on an adventure.
    # The logic for eligibility is encapsulated within the AdventureManager class.
    if not AdventureManager.is_eligible(user):
        return jsonify({'message': 'You can only go on one adventure per day'}), 403

    # Create a new adventure for the user using the AdventureManager class.
    adventure_manager = AdventureManager(user)
    new_adventure = adventure_manager.create()

    # Return a success message along with the material the user got from the adventure.
    return jsonify({'message': 'Adventure complete', 'material': new_adventure.material}), 201

# Define an endpoint to retrieve a summary of the user's materials.
@main.route('/materials_summary', methods=['GET'])
def get_materials_summary():
    # Extract the user ID from the request arguments.
    user_data = request.args
    user_id = user_data.get('user_id', None)

    # Check if a user ID was provided.
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    # Try to get the user from the database with the provided ID.
    user = User.query.get(user_id)

    # If the user is not found in the database, return an error message.
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Get all adventures associated with the user from the database.
    all_adventures = Adventure.query.filter_by(user_id=user.id).all()

    # Separate the adventures based on whether the materials were used or not.
    used_adventures = [adv for adv in all_adventures if adv.status == "Used Material"]
    unused_adventures = [adv for adv in all_adventures if adv.status == "Unused Material"]

    # Count the occurrences of each type of material.
    used_material_counts = Counter([adv.material for adv in used_adventures])
    unused_material_counts = Counter([adv.material for adv in unused_adventures])

    # Return a summary of both used and unused materials.
    return jsonify({
        'used_materials_summary': used_material_counts,
        'unused_materials_summary': unused_material_counts
    }), 200

# Define an endpoint to retrieve a user's adventure history.
@main.route('/adventure_history', methods=['GET'])
def get_adventure_history():
    # Extract the user ID from the request arguments.
    user_data = request.args
    user_id = user_data.get('user_id', None)

    # Check if a user ID was provided.
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    # Try to get the user from the database with the provided ID.
    user = User.query.get(user_id)

    # If the user is not found in the database, return an error message.
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Get all adventures associated with the user from the database, ordered by timestamp.
    adventures = Adventure.query.filter_by(user_id=user.id).order_by(Adventure.timestamp.desc()).all()

    # Prepare a list of adventure history details to return.
    adventure_history = [
        {
            'id': adventure.id,
            'timestamp': adventure.timestamp.isoformat(),
            'material': adventure.material,
        }
        for adventure in adventures
    ]

    # Return the user's adventure history.
    return jsonify({'adventure_history': adventure_history}), 200

# Define an endpoint to create a lootbox.
@main.route('/forge_lootbox', methods=['POST'])
def create_lootbox():
    # Extract the request data as JSON.
    data = request.get_json()

    # Extract the user ID and material IDs from the incoming data.
    user_id = data['user_id']
    material_ids = data['material_ids']

    # Try to get the user from the database with the provided ID.
    user = User.query.get(user_id)

    # If the user is not found in the database, return an error message.
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if the correct number of materials (5) were provided.
    if len(material_ids) != 5:
        return jsonify({'message': 'Exactly 5 materials are required to forge a LootBox'}), 400

    # Create a new lootbox using the LootBoxManager class.
    lootbox_manager = LootBoxManager(user, material_ids)
    new_lootbox = lootbox_manager.create()

    # If there was an error in creating the lootbox (e.g., using already used materials), return an error message.
    if new_lootbox == "Error: Cannot use already used or ineligible material":
        return jsonify({'message': new_lootbox}), 400

    # Return a success message along with the rarity of the created lootbox.
    return jsonify({'message': 'New LootBox created', 'rarity': new_lootbox.rarity}), 201
