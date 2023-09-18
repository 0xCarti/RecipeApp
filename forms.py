from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from datetime import date

from models import User, Recipe


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class IngredientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    category = SelectField(
        'Category',
        choices=[
            ('dry', 'Dry'),
            ('liquid', 'Liquid'),
            ('weight', 'Weight'),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Add Ingredient')


class RecipeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    prep_time = StringField('Preparation Time', validators=[DataRequired(), Length(min=2, max=100)])
    cook_time = StringField('Cooking Time', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Save Recipe')


class RecipeIngredientForm(FlaskForm):
    ingredient_id = SelectField('Ingredient', coerce=int, validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired(), Length(min=1, max=100)])
    unit = SelectField('Unit of Measurement', choices=[], validators=[DataRequired()])
    submit = SubmitField('Add Ingredient')


class StepForm(FlaskForm):
    step_text = TextAreaField('Step', validators=[DataRequired()])
    submit = SubmitField('Add Step')


class MealForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    name = StringField('Meal Name', validators=[DataRequired()])
    meal_type = SelectField('Meal Type', validators=[DataRequired()], choices=[
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('other', 'Other')
    ])
    recipe_id = QuerySelectField('Recipe', query_factory=lambda: Recipe.query.filter_by(user_id=current_user.id).all(), get_label='name', allow_blank=True, blank_text='(No Recipe)')
    submit = SubmitField('Add Meal')


class ShoppingListForm(FlaskForm):
    date = DateField('Date', default=date.today)
    submit = SubmitField('Generate Shopping List')


class SettingsForm(FlaskForm):
    preferred_dry_unit = SelectField(
        'Preferred unit for dry ingredients',
        choices=[
            ('milligrams', 'Milligrams'),
            ('gram', 'Gram'),
            ('kilogram', 'Kilogram'),
            ('pound', 'Pound'),
            ('ounce', 'Ounce'),
            ('tablespoons', 'Tablespoons'),
            ('teaspoons', 'Teaspoons')
        ],
        validators=[DataRequired()]
    )
    preferred_liquid_unit = SelectField(
        'Preferred unit for liquid ingredients',
        choices=[
            ('milliliter', 'Milliliter'),
            ('liter', 'Liter'),
            ('cup', 'Cup'),
            ('fluid_ounce', 'Fluid Ounce'),
        ],
        validators=[DataRequired()]
    )
    preferred_weight_unit = SelectField(
        'Preferred unit for weight',
        choices=[
            ('milligrams', 'Milligrams'),
            ('gram', 'Gram'),
            ('kilogram', 'Kilogram'),
            ('pound', 'Pound'),
            ('ounce', 'Ounce'),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Save Settings')
