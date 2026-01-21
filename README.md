# GAN - Gaming Arena Network

A web-based gaming tournament platform with virtual token economy, mobile wallet payments (Easypaisa/JazzCash), Google OAuth authentication, and WhatsApp verification.

## Features

- 🎮 **Tournament System**: Create and manage gaming tournaments with registration, check-in, and rewards
- 💰 **Virtual Token Economy**: Players purchase tokens with PKR via mobile wallets
- 🏆 **Reward System**: Winners earn reward tokens that can be shared with friends
- 🔐 **Google OAuth**: Secure authentication with Google accounts
- 📱 **WhatsApp Verification**: Phone number verification via WhatsApp Business API
- 💳 **Mobile Payments**: Integration with Easypaisa and JazzCash

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Database (DigitalOcean managed)
- **JWT** - Token-based authentication

### Frontend
- **HTML5 + CSS3** - Responsive gaming-themed design
- **Vanilla JavaScript** - No framework dependencies
- **Google Fonts** - Orbitron & Rajdhani fonts

## Project Structure

```
GAN/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── config.py         # Settings & environment variables
│       ├── database.py       # SQLAlchemy setup
│       ├── main.py          # FastAPI application
│       ├── models/          # Database models
│       │   ├── user.py
│       │   ├── wallet.py
│       │   ├── tournament.py
│       │   ├── transaction.py
│       │   └── registration.py
│       ├── schemas/         # Pydantic schemas
│       │   ├── user.py
│       │   ├── wallet.py
│       │   ├── tournament.py
│       │   └── payment.py
│       ├── routers/         # API routes
│       │   ├── auth.py
│       │   ├── users.py
│       │   ├── wallets.py
│       │   ├── tournaments.py
│       │   ├── payments.py
│       │   └── whatsapp.py
│       ├── services/        # Business logic
│       │   ├── auth_service.py
│       │   ├── wallet_service.py
│       │   ├── tournament_service.py
│       │   ├── payment_service.py
│       │   └── whatsapp_service.py
│       └── utils/           # Utilities
│           ├── security.py
│           └── helpers.py
├── frontend/
│   ├── index.html          # Login page
│   ├── profile.html        # Profile builder
│   ├── dashboard.html      # Main dashboard
│   ├── tournament.html     # Tournament details
│   ├── wallet.html         # Wallet & payments
│   ├── css/
│   │   └── styles.css      # Gaming-themed styles
│   └── js/
│       ├── config.js       # Configuration
│       ├── api.js          # API client
│       ├── auth.js         # Authentication
│       ├── profile.js      # Profile handling
│       ├── dashboard.js    # Dashboard logic
│       ├── tournament.js   # Tournament details
│       └── wallet.js       # Wallet & payments
├── .env.example            # Environment template
├── PROJECT_PLAN.md         # Detailed project plan
└── README.md               # This file
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL database (DigitalOcean)
- Google Cloud Console account (for OAuth)
- Easypaisa/JazzCash developer accounts
- WhatsApp Business API access

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy example env file
   cp ../.env.example ../.env
   # Edit .env with your credentials
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Serve the frontend** (you can use any static server)
   ```bash
   # Using Python
   cd frontend
   python -m http.server 3000
   
   # Or using Node.js
   npx serve -l 3000
   ```

2. **Update API URL** in `frontend/js/config.js` for production

### Database Setup

The application will automatically create tables on first run. For production:

1. Run database migrations with Alembic
2. Configure SSL connection to DigitalOcean

## API Endpoints

### Authentication
- `GET /api/auth/google` - Initiate Google OAuth
- `GET /api/auth/callback` - OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Users
- `GET /api/users/profile` - Get profile
- `PUT /api/users/profile` - Update profile
- `GET /api/users/check-profile-status` - Check completion

### WhatsApp
- `POST /api/whatsapp/send-code` - Send verification code
- `POST /api/whatsapp/verify-code` - Verify code

### Wallets
- `GET /api/wallets/balance` - Get balance
- `GET /api/wallets/transactions` - Transaction history
- `POST /api/wallets/transfer` - Transfer reward tokens

### Payments
- `GET /api/payments/bundles` - Get token bundles
- `POST /api/payments/initiate` - Start payment
- `GET /api/payments/status/{tx_id}` - Check status
- `POST /api/payments/easypaisa/callback` - Easypaisa webhook
- `POST /api/payments/jazzcash/callback` - JazzCash webhook

### Tournaments
- `GET /api/tournaments` - List tournaments
- `GET /api/tournaments/{id}` - Get tournament
- `POST /api/tournaments/{id}/register` - Register
- `GET /api/tournaments/{id}/participants` - Get participants
- `POST /api/tournaments/{id}/check-in` - Check in

## Deployment

### Namecheap Server

1. SSH into your server
2. Install Python 3.10+ and PostgreSQL client
3. Clone repository
4. Setup systemd service for uvicorn
5. Configure Nginx as reverse proxy
6. Setup SSL with Let's Encrypt

### Environment Variables

Ensure all variables in `.env.example` are configured:
- Database connection
- JWT secret (generate a strong key)
- Google OAuth credentials
- Easypaisa/JazzCash API keys
- WhatsApp Business API tokens

## Security Considerations

- Store secrets in environment variables, never commit `.env`
- Use HTTPS in production
- Implement rate limiting
- Enable CORS only for your domain
- Validate all user inputs
- Use prepared statements (SQLAlchemy handles this)

## License

Private - All rights reserved

## Support

For issues or questions, contact the development team.
