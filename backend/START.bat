@echo off
echo ================================================
echo   OnlineBazar — Auto Setup Script
echo   Founders: Ankit Sharma and Niraj Kumar
echo ================================================
echo.

echo [1/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo.
echo [2/5] Installing dependencies...
pip install django==5.0.6 Pillow python-decouple razorpay scikit-learn pandas numpy joblib crispy-bootstrap5 django-crispy-forms reportlab
pip install -r requirements.txt

echo.
echo [3/5] Running migrations...
python manage.py makemigrations users
python manage.py makemigrations store
python manage.py makemigrations seller
python manage.py makemigrations superadmin
python manage.py makemigrations payments
python manage.py makemigrations chatbot
python manage.py migrate

echo.
echo [4/5] Creating superadmin...
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@onlinebazar.com', 'Admin@123')"

echo.
echo [5/5] Starting server...
echo.
echo ================================================
echo   Server running at: http://127.0.0.1:8000/
echo   Superadmin login:  http://127.0.0.1:8000/superadmin/login/
echo   Email:    admin@ecommerce.com
echo   Password: Admin@123
echo ================================================
echo.
python manage.py runserver
