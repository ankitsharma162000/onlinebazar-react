"""
Chatbot Brain — OnlineBazar
Rule-based engine + knowledge base lookup
"""
import re
from .models import ChatKnowledge

# ── Built-in rules (always available offline) ──────────────────────────────
RULES = [
    {
        "keywords": ["hello", "hi", "hey", "namaste", "good morning", "good evening"],
        "answer": "👋 Hello! Welcome to OnlineBazar support. How can I help you today?"
    },
    {
        "keywords": ["order", "track", "status", "where is my order", "delivery"],
        "answer": "📦 To track your order:\n1. Go to <b>My Account → My Orders</b>\n2. Click on the order to see live tracking status.\n\nIf your order is delayed beyond expected date, please share your Order ID and we'll escalate it."
    },
    {
        "keywords": ["return", "refund", "exchange", "send back", "money back"],
        "answer": "🔄 Our Return Policy:\n• Returns accepted within <b>7 days</b> of delivery\n• Item must be unused and in original packaging\n• Refund processed within <b>5-7 business days</b>\n\nTo initiate a return, go to <b>My Orders → Return Item</b>."
    },
    {
        "keywords": ["payment", "failed", "not deducted", "transaction", "upi", "razorpay"],
        "answer": "💳 Payment Issue?\n• If amount was deducted but order not placed — it will be <b>auto-refunded within 3-5 days</b>\n• If UPI failed — try again after 30 minutes\n• For Razorpay issues — check your bank app for transaction status\n\nNeed help? Share your transaction ID."
    },
    {
        "keywords": ["cancel", "cancellation", "cancel order"],
        "answer": "❌ To cancel an order:\n• Go to <b>My Orders</b> and click <b>Cancel</b>\n• Orders can be cancelled before they are shipped\n• Once shipped, cancellation is not possible — you can return after delivery."
    },
    {
        "keywords": ["login", "password", "forgot", "reset", "sign in", "account"],
        "answer": "🔐 Login Issues?\n• Click <b>Forgot Password</b> on the login page\n• Enter your registered email\n• Check your email for reset link\n\nStill facing issues? Contact support with your registered email."
    },
    {
        "keywords": ["register", "sign up", "create account", "new account"],
        "answer": "✅ To create an account:\n1. Click <b>Register</b> on the top right\n2. Fill in your details\n3. Verify your mobile via OTP\n4. Complete KYC if required\n\nRegistration is completely free!"
    },
    {
        "keywords": ["seller", "sell", "become seller", "vendor", "shop"],
        "answer": "🏪 Want to sell on OnlineBazar?\n1. Click <b>Seller Register</b>\n2. Complete KYC with Aadhaar & PAN\n3. Add your bank/UPI details\n4. Start listing products!\n\nSeller registration is free. We charge only a small commission per sale."
    },
    {
        "keywords": ["discount", "coupon", "offer", "promo", "code", "sale"],
        "answer": "🎁 Current Offers:\n• Check the <b>Offers</b> section on homepage\n• Apply coupon code at checkout\n• First order discount available for new users\n\nSubscribe to our newsletter to get exclusive deals!"
    },
    {
        "keywords": ["contact", "support", "help", "customer care", "phone", "email"],
        "answer": "📞 Contact OnlineBazar Support:\n• 📧 Email: support@onlinebazar.com\n• ⏰ Hours: Mon–Sat, 9 AM – 6 PM\n• 💬 You can also raise a ticket via this chat\n\nI'm here to help with most common issues instantly!"
    },
    {
        "keywords": ["shipping", "delivery time", "how long", "days"],
        "answer": "🚚 Delivery Information:\n• Standard delivery: <b>3–7 business days</b>\n• Express delivery: <b>1–2 business days</b> (extra charge)\n• Free shipping on orders above ₹499\n\nDelivery time may vary based on your location."
    },
    {
        "keywords": ["product", "quality", "damaged", "broken", "defective", "wrong item"],
        "answer": "😟 Received a damaged or wrong product?\n1. Take photos immediately\n2. Go to <b>My Orders → Report Issue</b>\n3. Upload photos and describe the problem\n\nWe'll arrange a free replacement or full refund within 48 hours."
    },
    {
        "keywords": ["cod", "cash on delivery", "pay on delivery"],
        "answer": "💵 Cash on Delivery (COD):\n• COD is available on select products and locations\n• Maximum COD order value: ₹10,000\n• Please keep exact change ready for delivery\n\nCheck product page to see if COD is available for your pincode."
    },
    {
        "keywords": ["wishlist", "favourite", "saved", "save product"],
        "answer": "❤️ To save products to wishlist:\n• Click the <b>Heart ❤️</b> icon on any product\n• View all saved items under <b>My Account → Wishlist</b>\n• You can move items from wishlist directly to cart"
    },
    {
        "keywords": ["bye", "thanks", "thank you", "goodbye", "ok thanks"],
        "answer": "😊 You're welcome! Have a great shopping experience on OnlineBazar. Feel free to chat anytime you need help! 🛒"
    },
]


def normalize(text: str) -> str:
    return re.sub(r'[^\w\s]', '', text.lower().strip())


def find_answer(user_message: str):
    """
    Returns (answer, source) where source is 'rule', 'knowledge', or None.
    """
    msg = normalize(user_message)
    words = set(msg.split())

    # 1️⃣ Check built-in rules
    best_rule = None
    best_score = 0
    for rule in RULES:
        score = sum(1 for kw in rule["keywords"] if kw in msg or kw in words)
        if score > best_score:
            best_score = score
            best_rule = rule
    if best_score >= 1 and best_rule:
        return best_rule["answer"], "rule"

    # 2️⃣ Check saved knowledge base
    try:
        knowledge_items = ChatKnowledge.objects.all()
        best_kb = None
        best_kb_score = 0
        for item in knowledge_items:
            kws = [k.strip().lower() for k in item.keywords.split(',') if k.strip()]
            score = sum(1 for kw in kws if kw in msg or kw in words)
            if score > best_kb_score:
                best_kb_score = score
                best_kb = item
        if best_kb_score >= 1 and best_kb:
            best_kb.hits += 1
            best_kb.save(update_fields=['hits'])
            return best_kb.answer, "knowledge"
    except Exception:
        pass

    return None, None
