# Canvas-Todoist Sync

A Flask web application that synchronizes assignments between Canvas LMS and Todoist, helping students manage their academic tasks more effectively.

## Features

- **Canvas Integration**: Connect your Canvas LMS account to view courses and assignments
- **Todoist Integration**: Sync assignments to Todoist for better task management
- **User Authentication**: Secure login and registration system
- **Subscription Management**: Premium features with Stripe integration
- **API Testing**: Built-in tools to test API connections
- **Admin Dashboard**: Manage users and monitor system status
- **Sync History**: Track synchronization activities
- **Settings Management**: Customize sync preferences and notification settings

## Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Chart.js

### Backend
- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Login
- Flask-Migrate
- Flask-Caching
- Flask-WTF
- Flask-APScheduler

### Third-Party APIs
- Canvas LMS API
- Todoist API
- Stripe API

### Security
- Cryptography
- CSRF Protection
- Secure Session Management
- Password Hashing

### Development Tools
- Git
- pip
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/canvas-todoist-sync.git
cd canvas-todoist-sync
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
STRIPE_PRODUCT_ID=your-stripe-product-id
STRIPE_MONTHLY_PRICE_ID=your-stripe-monthly-price-id
STRIPE_YEARLY_PRICE_ID=your-stripe-yearly-price-id
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Usage

1. Register a new account or log in to an existing one
2. Configure your Canvas and Todoist API credentials
3. View your courses and assignments on the dashboard
4. Sync assignments to Todoist
5. Manage your subscription and settings

## API Credentials

### Canvas LMS
1. Log in to your Canvas account
2. Go to Account > Settings
3. Click on "New Access Token"
4. Generate a token with the necessary permissions
5. Copy the token and your Canvas instance URL

### Todoist
1. Log in to your Todoist account
2. Go to Settings > Integrations
3. Copy your API token

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 