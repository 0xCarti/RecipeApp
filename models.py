from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from config import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    preferred_dry_unit = db.Column(db.String(50), default='gram')
    preferred_liquid_unit = db.Column(db.String(50), default='milliliter')
    preferred_weight_unit = db.Column(db.String(50), default='gram')


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_ingredients = db.relationship('RecipeIngredient', back_populates='ingredient')
    category = db.Column(db.String(50), nullable=False, default='dry')

    def __repr__(self):
        return f"Ingredient('{self.name}')"


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prep_time = db.Column(db.String(100), nullable=False)
    cook_time = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy=True, cascade="all,delete")
    prep_steps = db.relationship('PrepStep', backref='recipe', lazy=True, cascade="all,delete")
    cook_steps = db.relationship('CookStep', backref='recipe', lazy=True, cascade="all,delete")
    meals = db.relationship('Meal', backref='recipe', lazy=True, cascade="all,delete")


class RecipeIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(100), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    ingredient = db.relationship('Ingredient', back_populates='recipe_ingredients')


class PrepStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    step_text = db.Column(db.Text, nullable=False)


class CookStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    step_text = db.Column(db.Text, nullable=False)


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    meal_type = db.Column(db.String(100), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Meal(name='{self.name}', date='{self.date}', meal_type='{self.meal_type}', user_id='{self.user_id}')>"
