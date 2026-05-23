#!/bin/bash
echo "============================================"
echo " OnlineBazar E-Commerce — MCA Project Setup"
echo " Ankit Sharma (34) and Niraj Kumar (8)"
echo "============================================"

echo ""
echo "[1/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "[2/5] Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "[3/5] Running database migrations..."
python manage.py makemigrations users
python manage.py makemigrations seller
python manage.py makemigrations store
python manage.py migrate

echo ""
echo "[4/5] Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "[5/5] Starting development server..."
echo ""
echo "============================================"
echo " Open: http://127.0.0.1:8000/"
echo " SuperAdmin: admin@ecommerce.com / Admin@123"
echo "============================================"
python manage.py runserver
