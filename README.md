# 🛒 OnlineBazar — React + Django REST Framework

**MCA Project by Ankit Sharma (34) & Niraj Kumar (8)**

Full-stack e-commerce platform with React (Vite + Tailwind) frontend and Django REST Framework backend.

---

## 📁 Project Structure

```
OnlineBazar_React/
├── backend/          ← Django REST API
│   ├── api/          ← All REST endpoints
│   ├── store/        ← Product, Order, Cart models
│   ├── users/        ← User model
│   ├── seller/       ← Seller model
│   ├── ecommerce/    ← settings.py, urls.py
│   └── manage.py
│
└── frontend/         ← React (Vite + Tailwind)
    └── src/
        ├── api/      ← Axios client + API functions
        ├── context/  ← Auth, Cart context
        ├── components/  ← Navbar, ProductCard, UI components
        └── pages/    ← Home, ProductDetail, Cart, Orders, Seller…
```

---

## 🚀 Setup & Run

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# (Optional) Seed data
python seed_data.py

# Start server
python manage.py runserver
```

Backend runs at: **http://localhost:8000**
API base URL:    **http://localhost:8000/api/**

---

### Frontend

```bash
cd frontend

# Install packages
npm install

# Start dev server
npm run dev
```

Frontend runs at: **http://localhost:3000**

> The Vite dev server proxies `/api` and `/media` to `localhost:8000` automatically.

---

## 🌐 API Endpoints

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/user/register/` | Buyer register |
| POST | `/api/auth/user/login/` | Buyer login |
| POST | `/api/auth/seller/register/` | Seller register |
| POST | `/api/auth/seller/login/` | Seller login |
| GET  | `/api/auth/user/me/` | Get logged-in buyer |
| GET  | `/api/auth/seller/me/` | Get logged-in seller |

### Products
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/products/` | List products (search, filter, paginate) |
| GET | `/api/products/?q=phone` | Search |
| GET | `/api/products/?category=Electronics` | Filter by category |
| GET | `/api/products/?sort=price_asc` | Sort |
| GET | `/api/products/<id>/` | Product detail + reviews + related |
| POST | `/api/products/<id>/review/` | Add review |
| GET | `/api/products/featured/` | Featured products |
| GET | `/api/products/categories/` | All categories |

### Cart & Wishlist
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/cart/` | View cart |
| POST | `/api/cart/add/` | Add to cart |
| PATCH | `/api/cart/<id>/` | Update (increase/decrease/remove) |
| GET | `/api/wishlist/` | View wishlist |
| POST | `/api/wishlist/toggle/` | Toggle wishlist |

### Orders
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/orders/checkout/` | Place order |
| GET | `/api/orders/` | My orders |
| GET | `/api/orders/<id>/` | Order detail + tracking |

### Seller
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/seller/stats/` | Dashboard stats |
| GET | `/api/seller/products/` | My products |
| POST | `/api/seller/products/add/` | Add product |
| PATCH | `/api/seller/products/<id>/` | Edit product |
| DELETE | `/api/seller/products/<id>/` | Deactivate product |
| GET | `/api/seller/orders/` | Incoming orders |
| PATCH | `/api/seller/orders/<id>/action/` | Accept/Reject/Ship |

### Membership & Utility
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/membership/` | Membership status |
| POST | `/api/membership/join/` | Join (monthly/yearly) |
| POST | `/api/coupon/apply/` | Apply coupon code |
| GET | `/api/pincode/?pincode=800001` | Pincode lookup |

---

## 🔐 Authentication

JWT tokens are used. After login, tokens are stored in `localStorage`:
- `access_token` — sent as `Authorization: Bearer <token>` header
- `refresh_token` — for future refresh (30-day expiry)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, React Router v6 |
| State | React Context (Auth + Cart) |
| HTTP | Axios |
| Backend | Django 4.2, Django REST Framework |
| Auth | JWT (PyJWT — custom implementation) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| CORS | django-cors-headers |
| ML | scikit-learn (recommendations) |
| Deployment | Railway (backend) + Vercel/Netlify (frontend) |

---

## 🚢 Deploy to Railway (Backend)

1. Push `backend/` to GitHub
2. In Railway → New Project → Deploy from GitHub
3. Set environment variables:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-railway-domain.railway.app
   DATABASE_URL=postgresql://...
   ```
4. Railway auto-detects `requirements.txt` and `manage.py`

## 🚢 Deploy Frontend (Vercel/Netlify)

```bash
cd frontend
npm run build     # creates dist/ folder
```

Set environment variable:
```
VITE_API_BASE=https://your-railway-backend.railway.app/api
```

Update `vite.config.js` proxy target to your Railway URL for production.
