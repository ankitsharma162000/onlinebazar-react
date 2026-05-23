"""
OnlineBazar — Dummy Data Seeder with Auto-Generated Images
Run: python seed_data.py
"""
import os, sys, io, django, random
from datetime import timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

print("\n🌱 OnlineBazar Dummy Data Seeder")
print("=" * 45)

CATEGORY_COLORS = {
    'Electronics': ('#1565C0', '#E3F2FD'),
    'Clothing':    ('#6A1B9A', '#F3E5F5'),
    'Food':        ('#E65100', '#FFF3E0'),
    'Beauty':      ('#AD1457', '#FCE4EC'),
    'Sports':      ('#2E7D32', '#E8F5E9'),
    'Home':        ('#F57F17', '#FFFDE7'),
    'Books':       ('#4E342E', '#EFEBE9'),
    'Toys':        ('#E53935', '#FFEBEE'),
    'Health':      ('#00695C', '#E0F2F1'),
    'Other':       ('#37474F', '#ECEFF1'),
}

def make_image(name, category):
    bg, light = CATEGORY_COLORS.get(category, ('#2874F0', '#E3F2FD'))
    img = Image.new('RGB', (400, 400), color=light)
    draw = ImageDraw.Draw(img)
    draw.rectangle([20,20,380,380], fill='white', outline=bg, width=3)
    draw.rectangle([20,20,380,100], fill=bg)
    try:
        fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except:
        fb = fs = ImageFont.load_default()
    draw.text((200, 60), category, fill='white', font=fb, anchor='mm')
    draw.ellipse([150,110,250,210], fill=light, outline=bg, width=3)
    words = name.split(); lines=[]; cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if len(t)>22 and cur: lines.append(cur); cur=w
        else: cur=t
    if cur: lines.append(cur)
    y=240
    for line in lines[:3]:
        draw.text((200,y), line, fill='#212121', font=fs, anchor='mm'); y+=26
    draw.text((200,375), 'OnlineBazar', fill=bg, font=fs, anchor='mm')
    buf=io.BytesIO(); img.save(buf, format='JPEG', quality=85); buf.seek(0)
    return buf.read()

# SuperAdmin
from superadmin.models import SuperAdmin
if not SuperAdmin.objects.filter(email='admin@onlinebazar.com').exists():
    SuperAdmin.objects.create(email='admin@onlinebazar.com', password=make_password('Admin@123'), name='Super Admin')
    print("✅ SuperAdmin: admin@onlinebazar.com / Admin@123")
else:
    print("ℹ️  SuperAdmin already exists")

# Sellers
from seller.models import Seller
sellers_data = [
    {'name':'Rahul Enterprises','email':'rahul@seller.com','phone_number':'9876543210','password':make_password('Seller@123'),'address_line':'12 MG Road','district':'New Delhi','state':'Delhi','pincode':'110001'},
    {'name':'Priya Electronics','email':'priya@seller.com','phone_number':'9812345678','password':make_password('Seller@123'),'address_line':'45 Brigade Road','district':'Bangalore','state':'Karnataka','pincode':'560001'},
    {'name':'Mumbai Fashion Hub','email':'mumbai@seller.com','phone_number':'9823456789','password':make_password('Seller@123'),'address_line':'78 Linking Road','district':'Mumbai','state':'Maharashtra','pincode':'400050'},
]
sellers = []
for s in sellers_data:
    obj, created = Seller.objects.get_or_create(email=s['email'], defaults=s)
    sellers.append(obj)
    print(f"{'✅' if created else 'ℹ️ '} Seller: {obj.name}")

# Products
from store.models import Product
products_data = [
    ('Samsung Galaxy M34 5G','Electronics',18999,sellers[1],50),
    ('boAt Rockerz 450 Headphones','Electronics',1299,sellers[1],120),
    ('Redmi 12C Smartphone','Electronics',8999,sellers[1],75),
    ('HP 14 Core i3 Laptop','Electronics',32999,sellers[1],20),
    ('JBL Go 3 Bluetooth Speaker','Electronics',2499,sellers[1],60),
    ('Noise ColorFit Pro Smartwatch','Electronics',3499,sellers[1],45),
    ('Mens Cotton Casual T-Shirt','Clothing',399,sellers[2],200),
    ('Womens Kurti Set Blue','Clothing',899,sellers[2],150),
    ('Levis 511 Slim Fit Jeans','Clothing',2499,sellers[2],80),
    ('Kids School Uniform Set','Clothing',599,sellers[2],100),
    ('Winter Jacket Fleece Navy','Clothing',1499,sellers[2],60),
    ('Dr Trust Digital Thermometer','Health',303,sellers[0],80),
    ('Omron BP Monitor HEM-7120','Health',2199,sellers[0],40),
    ('Dettol Hand Sanitizer 500ml','Health',189,sellers[0],300),
    ('Patanjali Ashwagandha Tablet','Health',249,sellers[0],150),
    ('Prestige Pressure Cooker 5L','Home',1299,sellers[0],40),
    ('Milton Thermosteel Bottle 1L','Home',699,sellers[0],90),
    ('Pigeon Non-Stick Tawa 28cm','Home',449,sellers[0],70),
    ('Philips Air Fryer HD9200','Home',6999,sellers[1],25),
    ('Godrej Aer Spray Fresh Linen','Home',149,sellers[0],200),
    ('Tata Tea Premium 500g','Food',225,sellers[0],180),
    ('Maggi Noodles 12 Pack','Food',132,sellers[0],250),
    ('Amul Butter 500g','Food',275,sellers[0],100),
    ('Basmati Rice 5kg Premium','Food',499,sellers[0],120),
    ('Lakme 9 to 5 Foundation','Beauty',499,sellers[2],80),
    ('Dove Body Wash 250ml','Beauty',299,sellers[2],150),
    ('Mamaearth Vitamin C Serum','Beauty',599,sellers[2],90),
    ('Cosco Football Size 5','Sports',699,sellers[0],50),
    ('Skipping Rope Steel Ball','Sports',349,sellers[0],100),
    ('Python Programming Guide','Books',399,sellers[0],60),
]

created_products = []; img_count = 0
for name, cat, price, seller, stock in products_data:
    obj, created = Product.objects.get_or_create(
        product_name=name, seller=seller,
        defaults={'category':cat,'price':Decimal(str(price)),'stock_quantity':stock,
                  'description':f'High quality {name}. Best in class on OnlineBazar. Category: {cat}.',
                  'manufacturing_date':None,'expiry_date':None,'is_active':True}
    )
    if created or not obj.product_image:
        try:
            img_bytes = make_image(name, cat)
            safe = name.lower().replace(' ','_')[:25]
            obj.product_image.save(f'{safe}.jpg', ContentFile(img_bytes), save=True)
            img_count += 1
        except Exception as e:
            print(f"  ⚠️ Image failed: {e}")
    created_products.append(obj)
    if created: print(f"  ✅ {name} — ₹{price} 🖼️")

print(f"\n📦 Products: {Product.objects.count()} | Images: {img_count}")

# Users
from users.models import UserProfile
users_data = [
    {'name':'Ankit Sharma','email':'ankit@user.com','phone_number':'9876512345','password':make_password('User@123'),'house_no':'101','address_line':'Shastri Nagar','district':'Jaipur','state':'Rajasthan','pincode':'302016'},
    {'name':'Niraj Kumar','email':'niraj@user.com','phone_number':'9812367890','password':make_password('User@123'),'house_no':'22B','address_line':'Civil Lines','district':'Patna','state':'Bihar','pincode':'800001'},
    {'name':'Priya Singh','email':'priya@user.com','phone_number':'9823412345','password':make_password('User@123'),'house_no':'Flat 5','address_line':'Koramangala','district':'Bangalore','state':'Karnataka','pincode':'560034'},
    {'name':'Rahul Verma','email':'rahulv@user.com','phone_number':'9834567890','password':make_password('User@123'),'house_no':'H-45','address_line':'Sector 18','district':'Noida','state':'Uttar Pradesh','pincode':'201301'},
    {'name':'Sneha Patel','email':'sneha@user.com','phone_number':'9845678901','password':make_password('User@123'),'house_no':'302','address_line':'Navrangpura','district':'Ahmedabad','state':'Gujarat','pincode':'380009'},
]
created_users = []
for u in users_data:
    obj, created = UserProfile.objects.get_or_create(email=u['email'], defaults=u)
    created_users.append(obj)
    print(f"{'✅' if created else 'ℹ️ '} User: {obj.name}")

# Orders
from store.models import Order, OrderItem
for i in range(15):
    user  = random.choice(created_users)
    prods = random.sample(created_products, random.randint(1,3))
    method= random.choice(['COD','UPI','Card','NetBanking'])
    status= random.choice(['Placed','Confirmed','Shipped','Delivered','Delivered'])
    sub   = sum(float(p.price) for p in prods)
    deliv = 0.0 if sub>=500 else 50.0
    total = sub + deliv + 5.0
    order = Order.objects.create(
        user=user, subtotal=round(sub,2), delivery_charge=deliv,
        platform_fee=5.0, is_bazar_member=False, total_amount=round(total,2),
        payment_method=method, payment_status='Paid' if method!='COD' else 'Pending',
        order_status=status, delivery_address=user.get_full_address(),
        order_date=timezone.now()-timedelta(days=random.randint(1,60)),
    )
    for p in prods:
        OrderItem.objects.create(order=order, product=p, quantity=random.randint(1,2), price_at_purchase=p.price)
print(f"✅ Orders: {Order.objects.count()}")

# Reviews
from store.models import Review
texts = ["Excellent product!","Good quality, fast delivery!","Value for money.","Amazing! 5 stars!","Best purchase this year!","Super fast delivery.","Nice product, will buy again.","Great quality at this price!","Satisfied with purchase.","Highly recommended!"]
rev_count = 0
for product in random.sample(created_products, min(20, len(created_products))):
    for user in random.sample(created_users, random.randint(1,3)):
        if not Review.objects.filter(product=product, user=user).exists():
            Review.objects.create(product=product, user=user, rating=random.randint(3,5), review_text=random.choice(texts))
            rev_count += 1
print(f"✅ Reviews: {rev_count}")

print("\n" + "="*45)
print("🎉 ALL DONE!")
print("="*45)
print("  SuperAdmin : admin@onlinebazar.com / Admin@123")
print("  Sellers    : rahul@seller.com / priya@seller.com / mumbai@seller.com / Seller@123")
print("  Users      : ankit@user.com / niraj@user.com / User@123")
print(f"  Products   : {Product.objects.count()} with images ✅")
print(f"  Orders     : {Order.objects.count()}")
print("="*45)
print("▶️  python manage.py runserver\n")
