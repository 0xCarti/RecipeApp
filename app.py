from collections import defaultdict
from datetime import date
from calendar import monthcalendar, month_name, monthrange

import pint
from flask import render_template, url_for, flash, redirect, abort, request, jsonify
from pint import UnitRegistry

from config import app, db, login_manager
from models import User, Ingredient, Recipe, RecipeIngredient, PrepStep, CookStep, Meal  # Ensure User model is imported here
from forms import RegistrationForm, LoginForm, IngredientForm, RecipeForm, StepForm, RecipeIngredientForm, MealForm, ShoppingListForm, SettingsForm
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

ureg = UnitRegistry()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return redirect(url_for('calendar'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/ingredients', methods=['GET', 'POST'])
@login_required
def ingredients():
    form = IngredientForm()
    if form.validate_on_submit():
        ingredient = Ingredient(name=form.name.data, user_id=current_user.id, category=form.category.data)
        db.session.add(ingredient)
        db.session.commit()
        flash('Ingredient added!', 'success')
        return redirect(url_for('ingredients'))
    ingredients = Ingredient.query.filter_by(user_id=current_user.id).all()
    return render_template('ingredients.html', title='Ingredients', form=form, ingredients=ingredients)


@app.route('/ingredients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    if ingredient.user_id != current_user.id:
        abort(403)
    form = IngredientForm()

    if form.validate_on_submit():
        ingredient.name = form.name.data
        ingredient.category = form.category.data
        db.session.commit()
        flash('Ingredient updated!', 'success')
        return redirect(url_for('ingredients'))
    elif request.method == 'GET':
        form.name.data = ingredient.name
        form.category.data = ingredient.category  # Set the default value for the category field here

    return render_template('edit_ingredient.html', title='Edit Ingredient', form=form)


@app.route('/ingredients/delete/<int:id>', methods=['POST'])
@login_required
def delete_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    if ingredient.user_id != current_user.id:
        abort(403)
    db.session.delete(ingredient)
    db.session.commit()
    flash('Ingredient deleted!', 'success')
    return redirect(url_for('ingredients'))


@app.route('/recipes', methods=['GET'])
@login_required
def recipes():
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('recipes.html', title='Recipes', recipes=recipes)


@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(name=form.name.data, prep_time=form.prep_time.data, cook_time=form.cook_time.data, user_id=current_user.id)
        db.session.add(recipe)
        db.session.commit()
        flash('Your recipe has been created!', 'success')
        return redirect(url_for('recipes'))
    return render_template('create_recipe.html', title='New Recipe', form=form)


@app.route('/recipe/<int:id>', methods=['GET', 'POST'])
@login_required
def recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if recipe.user_id != current_user.id:
        abort(403)

    ingredient_form = RecipeIngredientForm()
    ingredient_form.ingredient_id.choices = [(i.id, i.name) for i in Ingredient.query.filter_by(user_id=current_user.id).all()]

    step_form = StepForm()

    if request.method == 'POST' and 'Add Ingredient' in request.form.values():
        # Get the selected ingredient
        selected_ingredient_id = ingredient_form.ingredient_id.data
        selected_ingredient = Ingredient.query.get(selected_ingredient_id)

        # Get the correct units for the selected ingredient category
        if selected_ingredient.category == 'dry':
            units = ['grams', 'kilograms', 'milligrams', 'cups', 'tablespoons', 'teaspoons']
        elif selected_ingredient.category == 'liquid':
            units = ['milliliters', 'liters', 'fluid ounces', 'cups', 'tablespoons', 'teaspoons']
        else:  # category is 'weight'
            units = ['grams', 'kilograms', 'milligrams', 'ounces', 'pounds']

        # Update the choices for the unit field with the correct units
        ingredient_form.unit.choices = [(unit, unit) for unit in units]

    if ingredient_form.validate_on_submit() and request.form['submit'] == 'Add Ingredient':
        quantity = float(ingredient_form.quantity.data)
        ingredient = RecipeIngredient(ingredient_id=ingredient_form.ingredient_id.data, quantity=quantity, unit=ingredient_form.unit.data, recipe_id=id)
        db.session.add(ingredient)
        db.session.commit()
        flash('Ingredient added to recipe!', 'success')
        return redirect(url_for('recipe', id=id))
    else:
        print(ingredient_form.errors)

    if step_form.validate_on_submit():
        step_type = request.form.get('step_type')
        if request.form['submit'] == 'Add Prep Step':
            step_class = PrepStep
        elif request.form['submit'] == 'Add Cook Step':
            step_class = CookStep
        else:
            step_class = None
        if step_class:
            step = step_class(step_text=step_form.step_text.data, recipe_id=id)
            db.session.add(step)
            db.session.commit()
            flash('Step added to recipe!', 'success')
            return redirect(url_for('recipe', id=id))

    ingredients = RecipeIngredient.query.filter_by(recipe_id=id).all()
    prep_steps = PrepStep.query.filter_by(recipe_id=id).all()
    cook_steps = CookStep.query.filter_by(recipe_id=id).all()

    return render_template('recipe.html', title=recipe.name, recipe=recipe, ingredients=ingredients, prep_steps=prep_steps, cook_steps=cook_steps, ingredient_form=ingredient_form, step_form=step_form)


@app.route('/recipe/<int:recipe_id>/ingredient/<int:id>/edit', methods=['GET', 'POST'])
@app.route('/recipe/<int:recipe_id>/ingredient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe_ingredient(recipe_id, id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        abort(403)
    ingredient = RecipeIngredient.query.get_or_404(id)
    if ingredient.recipe_id != recipe.id:
        abort(403)

    form = RecipeIngredientForm(obj=ingredient)
    # Get all ingredients available to the user and set them as choices for the ingredient_id field
    ingredients = Ingredient.query.filter_by(user_id=current_user.id).all()
    form.ingredient_id.choices = [(ing.id, ing.name) for ing in ingredients]

    if form.validate_on_submit():
        ingredient.ingredient_id = form.ingredient_id.data
        ingredient.quantity = form.quantity.data
        ingredient.unit = form.unit.data
        db.session.commit()
        flash('Ingredient updated!', 'success')
        return redirect(url_for('recipe', id=recipe_id))
    return render_template('edit_recipe_ingredient.html', title='Edit Ingredient', form=form, recipe=recipe)


@app.route('/recipe/<int:recipe_id>/ingredient/<int:id>/delete', methods=['POST'])
@login_required
def delete_recipe_ingredient(recipe_id, id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        abort(403)
    ingredient = RecipeIngredient.query.get_or_404(id)
    if ingredient.recipe_id != recipe.id:
        abort(403)
    db.session.delete(ingredient)
    db.session.commit()
    flash('Ingredient deleted!', 'success')
    return redirect(url_for('recipe', id=recipe_id))


@app.route('/recipe/<int:recipe_id>/step/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe_step(recipe_id, id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        abort(403)

    step_type = request.args.get('type')
    step_class = PrepStep if step_type == 'prep' else CookStep if step_type == 'cook' else None
    if not step_class:
        abort(400)

    step = step_class.query.get_or_404(id)
    if step.recipe_id != recipe.id:
        abort(403)

    form = StepForm(obj=step)
    if form.validate_on_submit():
        step.step_text = form.step_text.data
        db.session.commit()
        flash('Step updated!', 'success')
        return redirect(url_for('recipe', id=recipe_id))
    return render_template('edit_recipe_step.html', title='Edit Step', form=form, recipe=recipe, step_type=step_type)


@app.route('/recipe/<int:recipe_id>/step/<int:id>/delete', methods=['POST'])
@login_required
def delete_recipe_step(recipe_id, id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        abort(403)

    step_type = request.args.get('type')
    step_class = PrepStep if step_type == 'prep' else CookStep if step_type == 'cook' else None
    if not step_class:
        abort(400)

    step = step_class.query.get_or_404(id)
    if step.recipe_id != recipe.id:
        abort(403)

    db.session.delete(step)
    db.session.commit()
    flash('Step deleted!', 'success')
    return redirect(url_for('recipe', id=recipe_id))


@app.route('/calendar', methods=['GET'])
@login_required
def calendar():
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)

    # Get the calendar data for the specified month
    calendar_data = monthcalendar(year, month)

    # Formatting the date strings for each day
    formatted_calendar_data = [
        [
            (date(year, month, day).isoformat() if day != 0 else 0)
            for day in week
        ]
        for week in calendar_data
    ]

    # Get the month name
    month_name_str = month_name[month]

    # Calculate the previous and next month
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    # Get the meals for the current month
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    meals = Meal.query.filter(Meal.date.between(start_date, end_date), Meal.user_id == current_user.id).all()

    # Create a dictionary with dates as keys and lists of meals as values
    meals_by_date = defaultdict(list)
    for meal in meals:
        meals_by_date[meal.date.isoformat()].append(meal)

    return render_template('calendar.html', year=year, month=month, calendar_data=formatted_calendar_data, month_name=month_name_str, prev_year=prev_year, prev_month=prev_month, next_year=next_year,
                           next_month=next_month, meals_by_date=meals_by_date)


@app.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    date_str = request.args.get('date')
    date_obj = date.fromisoformat(date_str) if date_str else date.today()

    form = MealForm()
    form.date.data = date_obj  # Pre-fill the date field
    if form.validate_on_submit():
        meal = Meal(date=form.date.data, name=form.name.data, meal_type=form.meal_type.data, recipe_id=form.recipe_id.data.id if form.recipe_id.data else None, user_id=current_user.id)
        db.session.add(meal)
        db.session.commit()
        flash('Meal added!', 'success')
        return redirect(url_for('calendar'))
    return render_template('add_meal.html', title='Add Meal', form=form)


@app.route('/delete_meal/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_meal(id):
    meal = Meal.query.get_or_404(id)
    if meal.user_id != current_user.id:
        abort(403)  # Forbidden, user does not own this meal
    db.session.delete(meal)
    db.session.commit()
    flash(f'Meal "{meal.name}" on {meal.date} has been deleted.', 'success')
    return redirect(url_for('calendar'))


@app.route('/day_view', methods=['GET', 'POST'])
@login_required
def day_view():
    date_str = request.args.get('date')
    if date_str:
        selected_date = date.fromisoformat(date_str)
    else:
        selected_date = date.today()

    # Fetch meals for the selected date
    meals = Meal.query.filter(Meal.date == selected_date, Meal.user_id == current_user.id).all()

    # Get the URL for the shopping list button
    shopping_list_url = url_for('shopping_list', date=selected_date)

    return render_template('day_view.html', meals=meals, date=selected_date, shopping_list_url=shopping_list_url)


@app.route('/shopping_list', methods=['GET', 'POST'])
@login_required
def shopping_list():
    date_str = request.args.get('date')
    if date_str:
        selected_date = date.fromisoformat(date_str)
    else:
        selected_date = date.today()

    # Fetch meals from the current date up to the selected date
    today = date.today()
    meals = Meal.query.filter(Meal.date.between(today, selected_date), Meal.user_id == current_user.id).all()

    # Retrieve the user's preferred units
    preferred_dry_unit = current_user.preferred_dry_unit
    preferred_liquid_unit = current_user.preferred_liquid_unit
    preferred_weight_unit = current_user.preferred_weight_unit

    # Step 1: Get all recipe ingredients for the meals
    ingredient_quantities = defaultdict(lambda: defaultdict(list))
    for meal in meals:
        recipe = Recipe.query.get(meal.recipe_id)
        for recipe_ingredient in recipe.ingredients:
            ingredient = Ingredient.query.get(recipe_ingredient.ingredient_id)
            ingredient_quantities[ingredient.name][recipe_ingredient.unit].append(recipe_ingredient.quantity)

    # Step 2: Aggregate quantities using Pint library
    aggregated_ingredients = {}
    for ingredient_name, units in ingredient_quantities.items():
        for unit, quantities in units.items():
            # Get the category of the ingredient from the database
            ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
            category = ingredient.category

            # Determine the preferred unit based on the category
            if category == 'dry':
                preferred_unit = preferred_dry_unit
            elif category == 'liquid':
                preferred_unit = preferred_liquid_unit
            else:  # category == 'weight'
                preferred_unit = preferred_weight_unit

            try:
                # Convert all quantities to the preferred unit
                total_quantity = sum((ureg.Quantity(q, unit).to(preferred_unit) for q in quantities))
            except pint.errors.DimensionalityError:
                # If there's a dimensionality error, just sum the quantities without unit conversion
                total_quantity = sum(quantities)

            if ingredient_name not in aggregated_ingredients:
                aggregated_ingredients[ingredient_name] = total_quantity
            else:
                try:
                    aggregated_ingredients[ingredient_name] += total_quantity
                except pint.errors.DimensionalityError:
                    # If there's a dimensionality error during addition, store the quantities separately
                    aggregated_ingredients[ingredient_name] = [aggregated_ingredients[ingredient_name], total_quantity]

    return render_template('shopping_list.html', today=today, selected_date=selected_date, aggregated_ingredients=aggregated_ingredients)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()

    # Pre-populate the form with the current user's settings
    if request.method == 'GET':
        form.preferred_dry_unit.data = current_user.preferred_dry_unit
        form.preferred_liquid_unit.data = current_user.preferred_liquid_unit
        form.preferred_weight_unit.data = current_user.preferred_weight_unit

    # Save the new settings when the form is submitted
    if form.validate_on_submit():
        current_user.preferred_dry_unit = form.preferred_dry_unit.data
        current_user.preferred_liquid_unit = form.preferred_liquid_unit.data
        current_user.preferred_weight_unit = form.preferred_weight_unit.data

        db.session.commit()

        flash('Your settings have been updated!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', form=form)


@app.route('/get_units/<int:ingredient_id>', methods=['GET'])
def get_units(ingredient_id):
    ingredient = Ingredient.query.get(ingredient_id)
    if ingredient.category == 'dry':
        units = ['grams', 'kilograms', 'milligrams', 'cups', 'tablespoons', 'teaspoons']
    elif ingredient.category == 'liquid':
        units = ['milliliters', 'liters', 'fluid ounces', 'cups', 'tablespoons', 'teaspoons']
    else:  # category is 'weight'
        units = ['grams', 'kilograms', 'milligrams', 'ounces', 'pounds']

    return jsonify(units)


@app.route('/recipe/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if recipe.user_id != current_user.id:
        abort(403)

    db.session.delete(recipe)
    db.session.commit()
    flash('Your recipe has been deleted!', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
