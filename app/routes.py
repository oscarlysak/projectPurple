from flask import Blueprint, jsonify, request
from collections import Counter
from .models import User, Adventure, LootBox  
from .game_logic import AdventureManager, LootBoxManager  

main = Blueprint('main', __name__)

@main.route('/adventure', methods=['POST'])
def adventure_endpoint():
    user_data = request.get_json()
    user_id = user_data['user_id']
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if not AdventureManager.is_eligible(user):
        return jsonify({'message': 'You can only go on one adventure per day'}), 403
    
    adventure_manager = AdventureManager(user)
    new_adventure = adventure_manager.create()
    
    return jsonify({'message': 'Adventure complete', 'material': new_adventure.material}), 201

@main.route('/materials_summary', methods=['GET'])
def get_materials_summary():
    user_data = request.args
    user_id = user_data.get('user_id', None)
    
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    all_adventures = Adventure.query.filter_by(user_id=user.id).all()

    # Separate the adventures into used and unused based on their status
    used_adventures = [adv for adv in all_adventures if adv.status == "Used Material"]
    unused_adventures = [adv for adv in all_adventures if adv.status == "Unused Material"]

    # Count the occurrences of each type of material
    used_material_counts = Counter([adv.material for adv in used_adventures])
    unused_material_counts = Counter([adv.material for adv in unused_adventures])

    return jsonify({
        'used_materials_summary': used_material_counts,
        'unused_materials_summary': unused_material_counts
    }), 200


@main.route('/adventure_history', methods=['GET'])
def get_adventure_history():
    user_data = request.args
    user_id = user_data.get('user_id', None)
    
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    adventures = Adventure.query.filter_by(user_id=user.id).order_by(Adventure.timestamp.desc()).all()
    
    adventure_history = [
        {
            'id': adventure.id,
            'timestamp': adventure.timestamp.isoformat(),
            'material': adventure.material,
        }
        for adventure in adventures
    ]
    
    return jsonify({'adventure_history': adventure_history}), 200



@main.route('/forge_lootbox', methods=['POST'])
def create_lootbox():
    data = request.get_json()
    user_id = data['user_id']
    material_ids = data['material_ids']  # An array of 5 material (adventure) IDs

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if len(material_ids) != 5:
        return jsonify({'message': 'Exactly 5 materials are required to forge a LootBox'}), 400

    lootbox_manager = LootBoxManager(user, material_ids)
    new_lootbox = lootbox_manager.create()

    if new_lootbox == "Error: Cannot use already used or ineligible material":
        return jsonify({'message': new_lootbox}), 400
    
    return jsonify({'message': 'New LootBox created', 'rarity': new_lootbox.rarity}), 201

