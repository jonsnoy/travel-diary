from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from database import db, User, Travel, TravelImage, CulturalSite, PlaceToVisit
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Инициализация базы данных
db.init_app(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Создание папки для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание таблиц
with app.app_context():
    db.create_all()

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главная страница
@app.route('/')
def index():
    travels = Travel.query.filter_by(is_public=True).order_by(Travel.created_at.desc()).limit(10).all()
    return render_template('index.html', travels=travels)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Валидация
        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return redirect(url_for('register'))

        # Создание пользователя
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Вы успешно вошли!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# Создание путешествия
@app.route('/create_travel', methods=['GET', 'POST'])
@login_required
def create_travel():
    if request.method == 'POST':
        try:
            # Основные данные
            title = request.form.get('title')
            description = request.form.get('description')
            
            # Местоположение
            latitude = float(request.form.get('latitude', 0))
            longitude = float(request.form.get('longitude', 0))
            location_address = request.form.get('location_address', '')
            
            # Стоимость
            cost_amount = float(request.form.get('cost_amount', 0))
            cost_currency = request.form.get('cost_currency', 'RUB')
            cost_details = request.form.get('cost_details', '')
            
            # Даты
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d') if request.form.get('start_date') else None
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None
            
            # Оценки
            transport_rating = int(request.form.get('transport_rating', 3))
            safety_rating = int(request.form.get('safety_rating', 3))
            population_rating = int(request.form.get('population_rating', 3))
            vegetation_rating = int(request.form.get('vegetation_rating', 3))
            
            is_public = 'is_public' in request.form

            # Создание путешествия
            travel = Travel(
                user_id=current_user.id,
                title=title,
                description=description,
                latitude=latitude,
                longitude=longitude,
                location_address=location_address,
                cost_amount=cost_amount,
                cost_currency=cost_currency,
                cost_details=cost_details,
                start_date=start_date,
                end_date=end_date,
                transport_rating=transport_rating,
                safety_rating=safety_rating,
                population_rating=population_rating,
                vegetation_rating=vegetation_rating,
                is_public=is_public
            )
            
            db.session.add(travel)
            db.session.flush()  # Получаем ID путешествия

            # Загрузка изображений
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        
                        image = TravelImage(
                            travel_id=travel.id,
                            filename=filename,
                            caption=file.filename
                        )
                        db.session.add(image)

            # Места культурного наследия
            cultural_sites_data = request.form.get('cultural_sites')
            if cultural_sites_data:
                cultural_sites = json.loads(cultural_sites_data)
                for site in cultural_sites:
                    if site.get('name'):
                        cultural_site = CulturalSite(
                            travel_id=travel.id,
                            name=site['name'],
                            description=site.get('description', ''),
                            visited=site.get('visited', False)
                        )
                        db.session.add(cultural_site)

            # Места для посещения
            places_data = request.form.get('places_to_visit')
            if places_data:
                places = json.loads(places_data)
                for place in places:
                    if place.get('name'):
                        place_to_visit = PlaceToVisit(
                            travel_id=travel.id,
                            name=place['name'],
                            description=place.get('description', ''),
                            priority=place.get('priority', 'medium')
                        )
                        db.session.add(place_to_visit)

            db.session.commit()
            flash('Путешествие успешно создано!', 'success')
            return redirect(url_for('my_travels'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании путешествия: {str(e)}', 'error')
            return redirect(url_for('create_travel'))

    return render_template('create_travel.html')

# Мои путешествия
@app.route('/my_travels')
@login_required
def my_travels():
    travels = Travel.query.filter_by(user_id=current_user.id).order_by(Travel.created_at.desc()).all()
    return render_template('my_travels.html', travels=travels)

# Все публичные путешествия
@app.route('/travels')
def travels():
    travels = Travel.query.filter_by(is_public=True).order_by(Travel.created_at.desc()).all()
    return render_template('travels.html', travels=travels)

# Детали путешествия
@app.route('/travel/<int:travel_id>')
def travel_detail(travel_id):
    travel = Travel.query.get_or_404(travel_id)
    
    # Проверка доступа
    if not travel.is_public and (not current_user.is_authenticated or travel.user_id != current_user.id):
        flash('У вас нет доступа к этому путешествию', 'error')
        return redirect(url_for('travels'))
    
    return render_template('travel_detail.html', travel=travel)

# Редактирование путешествия
@app.route('/travel/<int:travel_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_travel(travel_id):
    travel = Travel.query.get_or_404(travel_id)
    
    # Проверка прав
    if travel.user_id != current_user.id:
        flash('У вас нет прав на редактирование', 'error')
        return redirect(url_for('travel_detail', travel_id=travel_id))
    
    if request.method == 'POST':
        try:
            travel.title = request.form.get('title')
            travel.description = request.form.get('description')
            travel.latitude = float(request.form.get('latitude', 0))
            travel.longitude = float(request.form.get('longitude', 0))
            travel.location_address = request.form.get('location_address', '')
            travel.cost_amount = float(request.form.get('cost_amount', 0))
            travel.cost_currency = request.form.get('cost_currency', 'RUB')
            travel.cost_details = request.form.get('cost_details', '')
            
            travel.transport_rating = int(request.form.get('transport_rating', 3))
            travel.safety_rating = int(request.form.get('safety_rating', 3))
            travel.population_rating = int(request.form.get('population_rating', 3))
            travel.vegetation_rating = int(request.form.get('vegetation_rating', 3))
            
            travel.is_public = 'is_public' in request.form
            
            db.session.commit()
            flash('Путешествие обновлено!', 'success')
            return redirect(url_for('travel_detail', travel_id=travel_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'error')
    
    return render_template('edit_travel.html', travel=travel)

# Удаление путешествия
@app.route('/travel/<int:travel_id>/delete', methods=['POST'])
@login_required
def delete_travel(travel_id):
    travel = Travel.query.get_or_404(travel_id)
    
    if travel.user_id != current_user.id:
        flash('У вас нет прав на удаление', 'error')
        return redirect(url_for('travels'))
    
    # Удаление файлов изображений
    for image in travel.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        except:
            pass
    
    db.session.delete(travel)
    db.session.commit()
    
    flash('Путешествие удалено', 'success')
    return redirect(url_for('my_travels'))

# API для получения путешествий поблизости
@app.route('/api/nearby_travels')
def nearby_travels():
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
        radius = float(request.args.get('radius', 10))  # км
        
        travels = Travel.query.filter_by(is_public=True).all()
        
        nearby = []
        for travel in travels:
            # Простой расчет расстояния (для точного нужно использовать формулу гаверсинуса)
            distance = ((travel.latitude - lat) ** 2 + (travel.longitude - lng) ** 2) ** 0.5 * 111.32
            
            if distance <= radius:
                nearby.append({
                    'id': travel.id,
                    'title': travel.title,
                    'latitude': travel.latitude,
                    'longitude': travel.longitude,
                    'address': travel.location_address,
                    'distance': round(distance, 2)
                })
        
        return jsonify(nearby)
    except:
        return jsonify([])

# Отдача загруженных файлов
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)