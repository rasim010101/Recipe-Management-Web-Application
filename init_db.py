from app import create_app
from models import db, Recipe

app = create_app()
with app.app_context():
    db.create_all()

    sample = [
        Recipe(title="Tomato Omelette", ingredients="egg, tomato, salt, pepper", instructions="Beat eggs, chop tomato, fry together."),
        Recipe(title="Pasta with Tomato", ingredients="pasta, tomato, salt, olive oil", instructions="Boil pasta, make sauce from tomatoes, mix."),
        Recipe(title="Fried Rice", ingredients="rice, egg, carrot, peas, soy sauce", instructions="Cook rice, stir-fry vegetables, add egg."),
        Recipe(title="Grilled Cheese", ingredients="bread, cheese, butter", instructions="Butter bread, put cheese, grill until golden."),
        Recipe(title="Vegetable Soup", ingredients="carrot, potato, onion, salt, water", instructions="Boil vegetables until soft."),
        Recipe(title="Pancakes", ingredients="flour, milk, egg, sugar", instructions="Mix and fry batter on pan."),
        Recipe(title="Chicken Salad", ingredients="chicken, lettuce, tomato, salt, olive oil", instructions="Mix cooked chicken with veggies."),
        Recipe(title="Omelette with Cheese", ingredients="egg, cheese, salt, pepper", instructions="Beat eggs with cheese and fry.")
    ]

    # Только если таблица пустая — добавляем
    if Recipe.query.count() == 0:
        db.session.bulk_save_objects(sample)
        db.session.commit()
        print("Sample recipes inserted.")
    else:
        print("DB already has data.")
