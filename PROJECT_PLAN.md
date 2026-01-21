# GAN - Gaming Arena Network
## Complete Project Plan & Architecture

---

## 📋 Project Overview

A gaming tournament web platform where users:
- Sign up via Google OAuth
- Complete profile with WhatsApp verification
- Purchase virtual tokens using mobile wallets (Easypaisa/JazzCash)
- Register for tournaments using tokens
- Win reward tokens that can be shared or used in-app

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  (HTML5 + CSS + JavaScript)                                     │
│  - Landing/Login Page                                           │
│  - Profile Builder Page                                         │
│  - Main Dashboard (Tournaments List)                            │
│  - Tournament Details Page                                      │
│  - Token Purchase Page                                          │
│  - Wallet/Profile Page                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Auth       │  │  Tournaments │  │   Payments   │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Wallet     │  │   WhatsApp   │  │   User       │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Google     │  │  Easypaisa/  │  │   WhatsApp   │          │
│  │   OAuth2     │  │  JazzCash    │  │   Business   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                           │
│                    (DigitalOcean)                                │
│  Tables: users, wallets, transactions, tournaments,             │
│          registrations, token_bundles, rewards                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
GAN/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection
│   │   │
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── wallet.py
│   │   │   ├── tournament.py
│   │   │   ├── transaction.py
│   │   │   └── registration.py
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── wallet.py
│   │   │   ├── tournament.py
│   │   │   └── payment.py
│   │   │
│   │   ├── routers/                # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Google OAuth
│   │   │   ├── users.py
│   │   │   ├── wallets.py
│   │   │   ├── tournaments.py
│   │   │   ├── payments.py
│   │   │   └── whatsapp.py
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── wallet_service.py
│   │   │   ├── tournament_service.py
│   │   │   ├── payment_service.py
│   │   │   └── whatsapp_service.py
│   │   │
│   │   └── utils/                  # Utilities
│   │       ├── __init__.py
│   │       ├── security.py
│   │       └── helpers.py
│   │
│   ├── requirements.txt
│   ├── alembic.ini                 # Database migrations
│   └── alembic/
│       └── versions/
│
├── frontend/
│   ├── index.html                  # Landing/Login page
│   ├── profile.html                # Profile builder
│   ├── dashboard.html              # Main page with tournaments
│   ├── tournament.html             # Tournament details
│   ├── wallet.html                 # Token purchase page
│   │
│   ├── css/
│   │   └── styles.css
│   │
│   ├── js/
│   │   ├── app.js                  # Main JS
│   │   ├── auth.js                 # Google OAuth handling
│   │   ├── api.js                  # API calls
│   │   └── wallet.js               # Wallet operations
│   │
│   └── assets/
│       └── images/
│
├── .env.example                    # Environment variables template
├── .gitignore
├── docker-compose.yml              # For local development
└── README.md
```

---

## 🗄️ Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| google_id | VARCHAR | Google OAuth ID |
| email | VARCHAR | User email |
| full_name | VARCHAR | Full name |
| age | INTEGER | User age |
| city | VARCHAR | City |
| country | VARCHAR | Country |
| whatsapp_number | VARCHAR | WhatsApp number |
| whatsapp_verified | BOOLEAN | Verification status |
| player_id | VARCHAR | Gaming ID (FreeFire/PUBG etc) |
| preferred_payment | VARCHAR | easypaisa/jazzcash/stripe |
| profile_completed | BOOLEAN | Profile completion status |
| created_at | TIMESTAMP | Account creation date |
| updated_at | TIMESTAMP | Last update |

### Wallets Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| virtual_tokens | INTEGER | Purchased tokens balance |
| reward_tokens | INTEGER | Earned tokens balance |
| total_spent_pkr | DECIMAL | Total money spent |
| created_at | TIMESTAMP | Creation date |

### Transactions Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| type | ENUM | purchase/spend/reward/transfer |
| amount | INTEGER | Token amount |
| payment_method | VARCHAR | easypaisa/jazzcash/stripe |
| payment_ref | VARCHAR | External payment reference |
| status | ENUM | pending/completed/failed |
| created_at | TIMESTAMP | Transaction date |

### Tournaments Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | VARCHAR | Tournament name |
| game | VARCHAR | Game name |
| description | TEXT | Tournament details |
| rules | TEXT | Tournament rules |
| entry_fee | INTEGER | Required tokens |
| prize_pool | INTEGER | Total reward tokens |
| max_participants | INTEGER | Max entries |
| current_participants | INTEGER | Current entries |
| start_date | TIMESTAMP | Start date/time |
| end_date | TIMESTAMP | End date/time |
| status | ENUM | upcoming/active/completed |
| banner_url | VARCHAR | Tournament image |
| created_at | TIMESTAMP | Creation date |

### Registrations Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| tournament_id | UUID | Foreign key to tournaments |
| tokens_paid | INTEGER | Tokens paid for entry |
| position | INTEGER | Final position (null until finished) |
| reward_earned | INTEGER | Tokens earned (winners) |
| registered_at | TIMESTAMP | Registration date |

### Token Bundles Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| tokens | INTEGER | Number of tokens |
| price_pkr | DECIMAL | Price in PKR |
| price_usd | DECIMAL | Price in USD |
| bonus_tokens | INTEGER | Bonus tokens |
| is_active | BOOLEAN | Bundle availability |

---

## 🔄 User Flow

### 1. First Time User
```
Landing Page → Google Sign In → Profile Builder → WhatsApp Verify → Dashboard
```

### 2. Returning User
```
Landing Page → Google Sign In → Dashboard (if profile complete)
                              → Profile Builder (if incomplete)
```

### 3. Token Purchase Flow
```
Wallet Icon → Bundle Selection → Payment Method → 
Easypaisa/JazzCash Request → User Confirms on Phone → 
Backend Receives Callback → Credit Tokens → Show Success
```

### 4. Tournament Registration Flow
```
Tournament Card → Tournament Details → Register Button →
Check Balance → (Sufficient) Deduct Tokens → Confirm Entry
              → (Insufficient) Prompt Buy Tokens → Bundle Page
```

### 5. Reward Distribution Flow
```
Tournament Ends → Admin/System Sets Winners →
Calculate Rewards → Credit Reward Tokens → Notify Users
```

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/auth/google | Initiate Google OAuth |
| GET | /api/auth/google/callback | OAuth callback |
| GET | /api/auth/me | Get current user |
| POST | /api/auth/logout | Logout user |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users/profile | Get user profile |
| PUT | /api/users/profile | Update profile |
| POST | /api/users/verify-whatsapp | Send verification code |
| POST | /api/users/confirm-whatsapp | Confirm code |

### Wallets
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/wallets/balance | Get token balance |
| GET | /api/wallets/transactions | Get transaction history |
| POST | /api/wallets/transfer | Transfer tokens to friend |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/payments/bundles | Get available bundles |
| POST | /api/payments/initiate | Start payment |
| POST | /api/payments/easypaisa/callback | Easypaisa webhook |
| POST | /api/payments/jazzcash/callback | JazzCash webhook |

### Tournaments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/tournaments | List all tournaments |
| GET | /api/tournaments/{id} | Get tournament details |
| POST | /api/tournaments/{id}/register | Register for tournament |
| GET | /api/tournaments/{id}/participants | List participants |
| GET | /api/tournaments/my-registrations | User's registrations |

---

## 🔐 Security Measures

1. **JWT Authentication** - Secure token-based auth
2. **HTTPS Only** - All traffic encrypted
3. **Rate Limiting** - Prevent API abuse
4. **Input Validation** - Pydantic schemas
5. **CORS Configuration** - Restrict origins
6. **Password-less** - Google OAuth only (more secure)
7. **Webhook Signatures** - Verify payment callbacks

---

## 🚀 Deployment Plan

### Phase 1: Development (Local)
1. Set up project structure ✓
2. Implement database models
3. Create API endpoints
4. Build frontend pages
5. Integrate Google OAuth
6. Test with mock payments

### Phase 2: Staging
1. Deploy backend to Namecheap server
2. Connect DigitalOcean PostgreSQL
3. Configure domain/SSL
4. Test payment sandbox (Easypaisa/JazzCash)
5. Test WhatsApp Business API

### Phase 3: Production
1. Switch to production payment APIs
2. Enable WhatsApp verification
3. Monitor and scale
4. Add Stripe (future)

---

## 📦 Required API Keys & Credentials

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Database
DATABASE_URL=postgresql://user:pass@host:5432/gan_db

# Easypaisa
EASYPAISA_STORE_ID=your_store_id
EASYPAISA_HASH_KEY=your_hash_key
EASYPAISA_API_URL=https://easypaisa.com.pk/api

# JazzCash
JAZZCASH_MERCHANT_ID=your_merchant_id
JAZZCASH_PASSWORD=your_password
JAZZCASH_HASH_KEY=your_hash_key

# WhatsApp Business
WHATSAPP_API_URL=https://graph.facebook.com
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token

# App
SECRET_KEY=your_super_secret_key
FRONTEND_URL=https://yourdomain.com
```

---

## 💰 Token Bundle Pricing (Suggested)

| Bundle | Tokens | Price (PKR) | Price (USD) | Bonus |
|--------|--------|-------------|-------------|-------|
| Starter | 100 | ₨1,399 | $4.99 | 0 |
| Popular | 200 | ₨2,239 | $7.99 | 10 |
| Value | 500 | ₨5,039 | $17.99 | 50 |
| Pro | 1000 | ₨8,399 | $29.99 | 150 |
| Ultimate | 2500 | ₨19,599 | $69.99 | 500 |

---

## ⏭️ Next Steps

1. **Immediately**: Set up project folder structure
2. **Today**: Create database models and FastAPI skeleton
3. **This Week**: 
   - Implement Google OAuth
   - Build frontend pages
   - Create wallet system
4. **Next Week**:
   - Integrate Easypaisa/JazzCash sandbox
   - WhatsApp verification
   - Tournament registration flow
5. **Week 3**:
   - Testing and bug fixes
   - Deployment to staging
   - Production preparation

---

## ❓ Questions Before We Proceed

1. Do you have Easypaisa/JazzCash merchant accounts ready?
2. Do you have a WhatsApp Business API account?
3. Do you have Google Cloud Console access for OAuth?
4. What games will be supported initially?
5. Should reward tokens be transferable or only usable?

---

Let me know if you want me to start building this! 🚀
