// Навигация
document.addEventListener('DOMContentLoaded', function() {
    // Мобильное меню
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Автоматическое скрытие алертов
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // Предпросмотр изображений
    const imageInput = document.getElementById('images');
    const imagePreview = document.getElementById('imagePreview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function(e) {
            imagePreview.innerHTML = '';
            const files = Array.from(e.target.files);
            
            files.forEach((file, index) => {
                if (index >= 5) return; // Максимум 5 изображений
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const div = document.createElement('div');
                    div.className = 'image-preview-item';
                    div.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">
                        <button type="button" class="remove-btn" onclick="removeImage(${index})">×</button>
                    `;
                    imagePreview.appendChild(div);
                };
                reader.readAsDataURL(file);
            });
        });
    }
});

// Функции для формы создания путешествия
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lng;
                
                // Если используется Яндекс.Карты
                if (typeof setLocation === 'function') {
                    setLocation(lat, lng);
                }
                
                // Получение адреса через обратное геокодирование
                getAddressFromCoordinates(lat, lng);
            },
            function(error) {
                alert('Не удалось определить местоположение: ' + error.message);
            }
        );
    } else {
        alert('Геолокация не поддерживается вашим браузером');
    }
}

function getAddressFromCoordinates(lat, lng) {
    // Использование Nominatim (OpenStreetMap)
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(response => response.json())
        .then(data => {
            if (data.display_name) {
                document.getElementById('location_address').value = data.display_name;
            }
        })
        .catch(error => {
            console.log('Не удалось получить адрес:', error);
        });
}

// Добавление места культурного наследия
let culturalSiteCount = 0;

function addCulturalSite() {
    culturalSiteCount++;
    const container = document.getElementById('culturalSitesContainer');
    
    const div = document.createElement('div');
    div.className = 'dynamic-field';
    div.innerHTML = `
        <div class="form-group">
            <label>Название места культурного наследия</label>
            <input type="text" name="cultural_site_name_${culturalSiteCount}" required>
        </div>
        <div class="form-group">
            <label>Описание</label>
            <textarea name="cultural_site_description_${culturalSiteCount}" rows="2"></textarea>
        </div>
        <div class="form-group">
            <label class="checkbox-label">
                <input type="checkbox" name="cultural_site_visited_${culturalSiteCount}">
                Посещено
            </label>
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">
            Удалить
        </button>
    `;
    
    container.appendChild(div);
}

// Добавление места для посещения
let placeCount = 0;

function addPlaceToVisit() {
    placeCount++;
    const container = document.getElementById('placesToVisitContainer');
    
    const div = document.createElement('div');
    div.className = 'dynamic-field';
    div.innerHTML = `
        <div class="form-group">
            <label>Название места</label>
            <input type="text" name="place_name_${placeCount}" required>
        </div>
        <div class="form-group">
            <label>Описание</label>
            <textarea name="place_description_${placeCount}" rows="2"></textarea>
        </div>
        <div class="form-group">
            <label>Приоритет</label>
            <select name="place_priority_${placeCount}">
                <option value="low">Низкий</option>
                <option value="medium" selected>Средний</option>
                <option value="high">Высокий</option>
            </select>
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">
            Удалить
        </button>
    `;
    
    container.appendChild(div);
}

// Обновление значения рейтинга
function updateRatingValue(ratingName) {
    const slider = document.getElementById(ratingName);
    const valueSpan = document.getElementById(ratingName + '_value');
    if (slider && valueSpan) {
        valueSpan.textContent = slider.value;
    }
}

// Удаление изображения из предпросмотра
function removeImage(index) {
    const imageInput = document.getElementById('images');
    const dt = new DataTransfer();
    
    for (let i = 0; i < imageInput.files.length; i++) {
        if (i !== index) {
            dt.items.add(imageInput.files[i]);
        }
    }
    
    imageInput.files = dt.files;
    imageInput.dispatchEvent(new Event('change'));
}

// Валидация формы перед отправкой
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createTravelForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            const title = document.getElementById('title').value.trim();
            const description = document.getElementById('description').value.trim();
            const latitude = document.getElementById('latitude').value;
            const longitude = document.getElementById('longitude').value;
            
            if (!title || !description) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля');
                return;
            }
            
            if (!latitude || !longitude) {
                e.preventDefault();
                alert('Пожалуйста, укажите местоположение');
                return;
            }
        });
    }
});

// Поиск ближайших путешествий
function findNearbyTravels() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                fetch(`/api/nearby_travels?lat=${lat}&lng=${lng}&radius=50`)
                    .then(response => response.json())
                    .then(data => {
                        displayNearbyTravels(data);
                    })
                    .catch(error => {
                        console.error('Ошибка при поиске:', error);
                    });
            }
        );
    } else {
        alert('Геолокация не поддерживается');
    }
}

function displayNearbyTravels(travels) {
    // Реализация отображения ближайших путешествий
    console.log('Найденные путешествия:', travels);
}