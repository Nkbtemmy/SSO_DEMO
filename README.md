# Django REST Framework Project with PostgreSQL & SSO

## 📌 Overview
This project is a **Django REST Framework (DRF)** backend that uses **PostgreSQL** as its database and integrates with enterprise-level authentication systems for **Single Sign-On (SSO)**.  
It supports multiple authentication providers, including **Azure Active Directory (Azure AD)**, **Active Directory Federation Services (ADFS)**, and **LDAP**.

---

## 🚀 Features
- RESTful API built with **Django REST Framework**
- Database powered by **PostgreSQL**
- **Custom User Model** with organization support
- **Single Sign-On (SSO)** integration:
  - 🔹 **Azure AD** (cloud-based identity & access management)
  - 🔹 **ADFS** (on-premises Active Directory authentication with token-based federation)
  - 🔹 **LDAP** (lightweight directory access protocol for directory-based authentication)

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/nkbtemmy/sso_demo.git
cd sso_demo
```

### 2️⃣ Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure PostgreSQL
Create a database and user in PostgreSQL:
```sql
CREATE DATABASE drf_project;
CREATE USER drf_user WITH PASSWORD 'your_password';
ALTER ROLE drf_user SET client_encoding TO 'utf8';
ALTER ROLE drf_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE drf_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE drf_project TO drf_user;
```

Update your **settings.py** with:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'drf_project',
        'USER': 'drf_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5️⃣ Run migrations
```bash
python manage.py migrate
```

### 6️⃣ Start the server
```bash
python manage.py runserver
```

---

## 🔐 Authentication Options

### 🔹 Azure AD
- Cloud-based identity provider
- Uses OAuth2 & OpenID Connect for authentication
- Best suited for cloud-first organizations

### 🔹 ADFS
- On-premises Active Directory Federation Services
- Provides SAML/OAuth2-based federation
- Often used in hybrid environments

### 🔹 LDAP
- Lightweight Directory Access Protocol
- Directly queries the organization’s directory service (like Active Directory or OpenLDAP)
- Best for internal corporate networks

---

## 📖 API Documentation
Once the server is running, visit:
```
http://127.0.0.1:8000/api/
```

---

## 🛠 Tech Stack
- **Python** 3.10+
- **Django** 4.x
- **Django REST Framework**
- **PostgreSQL**
- **Azure AD / ADFS / LDAP** (for SSO)

---

## 🤝 Contributing
1. Fork the repo
2. Create a new branch (`feature/your-feature`)
3. Commit your changes
4. Push and create a Pull Request

---

## 📜 License
This project is licensed under the **MIT License**.
