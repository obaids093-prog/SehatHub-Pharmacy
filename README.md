# SehatHub - Project Folder Guide

Yeh tumhara Flask project structure hai. Neeche har folder ka kaam likha hai.

## Folder Structure

```
sehathub/
├── app.py                  -> Main file - yahin se app start hota hai
├── .env                    -> SECRET credentials (DB password etc.) - kabhi GitHub pe upload na karna
├── .gitignore              -> Git ko batata hai kya files ignore karni hain
├── requirements.txt        -> Saari Python libraries ki list
│
├── config/
│   └── database.py         -> MySQL se connection banane wala code
│
├── routes/                 -> Yahan hum har module ke alag routes (pages ka logic) likhenge
│                               (auth.py, customer.py, pharmacist.py, admin.py - baad mein banayenge)
│
├── templates/               -> Saare HTML pages (Jinja2 templates) yahan aayenge
│   ├── index.html          -> Test homepage (already bana hua hai)
│   ├── auth/                -> Login, Signup, Forgot Password pages
│   ├── customer/             -> Catalog, Cart, Checkout, Orders, Profile pages
│   ├── pharmacist/           -> Pharmacist dashboard, stock management
│   ├── admin/                -> Admin console, reports, user management
│   └── delivery/              -> Delivery management pages
│
├── static/
│   ├── css/                 -> Custom stylesheets
│   ├── js/                  -> JavaScript files (cart logic, AJAX, etc.)
│   └── images/                -> Logo, medicine images, icons
│
├── utils/                   -> Helper code (password hashing, security functions, etc.)
│
└── uploads/
    └── prescriptions/        -> Jab customers prescription upload karenge, yahan save hongi
```

## Setup Karne Ke Steps

1. **Yeh folder VS Code mein open karo** (File -> Open Folder)

2. **Terminal kholo** (Terminal -> New Terminal) aur libraries install karo:
   ```
   pip install -r requirements.txt
   ```

3. **`.env` file check karo** - usme `DB_NAME=sehathub_db` already likha hai (yeh tumhare phpMyAdmin wale database ka sahi naam hai). `DB_PASSWORD=` empty hai kyunki XAMPP ka default MySQL root user ka koi password nahi hota.

4. **App run karo:**
   ```
   python app.py
   ```

5. **Browser mein kholo:**
   ```
   http://127.0.0.1:5000
   ```
   Agar "Flask is working correctly!" wala message dikhe, matlab sab sahi setup ho gaya hai.

## ⚠️ Important: Is Folder Ko Mehfooz Rakho
Pehli baar yeh folder accidentally delete ho gaya tha. Ab jab yeh dobara extract karo, **isko kisi permanent jagah rakho** (e.g. Desktop ya Documents mein ek fixed folder), aur baar baar backup bhi lete raho (Google Drive, USB, ya GitHub pe push karna sabse acha tareeka hai).

## Next Steps (hum yeh mil ke karenge)
- Stitch AI designs ko `templates/` ke andar daalna
- `routes/` mein actual pages ka logic likhna (login, catalog, cart, etc.)
- Database se real data connect karna
