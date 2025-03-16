# Canvas-Todoist Sync

A web application that synchronizes Canvas LMS assignments with Todoist tasks, helping students and educators keep track of their coursework efficiently.

## Features

- **Account Management**: Register, login, and manage your profile
- **API Integration**: Connect your Canvas LMS and Todoist accounts securely
- **Assignment Syncing**: One-click sync of Canvas assignments to Todoist tasks
- **Custom Mapping**: Map Canvas courses to specific Todoist projects
- **Automated Sync**: Premium feature for scheduled automatic synchronization
- **Sync History**: View a log of all past synchronization operations
- **Modern UI**: Clean, responsive interface that works on all devices

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite (configurable for other databases)
- **Task Scheduling**: Flask-APScheduler
- **API Integration**: Canvas LMS API and Todoist API
- **Caching**: Flask-Caching
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Frontend**: Bootstrap, JavaScript, jQuery

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/canvas-todoist-sync.git
   cd canvas-todoist-sync
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your-secret-key
   FLASK_ENV=development
   ```

5. Initialize the database:
   ```
   flask shell
   >>> from app import create_app, db
   >>> app = create_app()
   >>> with app.app_context():
   >>>     db.create_all()
   >>> exit()
   ```

6. Run the application:
   ```
   python run.py
   ```

7. Access the application at `http://localhost:5000`

## Production Setup Guide

For secure deployment in production, follow these additional steps:

1. Configure environment variables for production:
   ```
   SECRET_KEY=<strong-random-secret-key>
   FLASK_ENV=production
   DATABASE_URL=<your-production-database-url>
   ```

2. Stripe Integration (if using premium features):
   ```
   STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>
   STRIPE_SECRET_KEY=<your-stripe-secret-key>
   STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>
   STRIPE_PRODUCT_ID=<your-stripe-product-id>
   STRIPE_MONTHLY_PRICE_ID=<your-stripe-price-id-for-monthly>
   STRIPE_YEARLY_PRICE_ID=<your-stripe-price-id-for-yearly>
   DOMAIN=<your-production-domain>
   ```

3. Configure a proper database:
   - Production environments should use a robust database like PostgreSQL
   - Set up migrations for database changes:
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

4. Set up a production web server:
   - Use Gunicorn as WSGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 127.0.0.1:5000 run:app
   ```
   - Set up Nginx as a reverse proxy
   - Configure SSL certificates using Let's Encrypt

5. Security considerations:
   - Set `SESSION_COOKIE_SECURE=True` in your config
   - Set `REMEMBER_COOKIE_SECURE=True` in your config
   - Ensure sensitive environmental variables are properly restricted
   - Regularly update dependencies for security patches

6. Monitoring and logging:
   - Set up application monitoring using Sentry, New Relic, or similar
   - Configure proper logging to capture errors
   - Set up backup schedules for your database

7. Run production initialization:
   ```bash
   FLASK_ENV=production python run.py
   ```

## PythonAnywhere Deployment

For deploying on PythonAnywhere, the following specific configurations are recommended:

1. Set up a PostgreSQL database from the PythonAnywhere dashboard
   - Configure the database URL in your environment variables:
   ```
   DATABASE_URL=postgres://<username>:<password>@<hostname>/<dbname>
   ```

2. Use the PythonAnywhere-specific configuration:
   ```
   FLASK_ENV=production
   ```
   - The application will automatically detect PythonAnywhere and use the optimized configuration

3. Configure an "always-on task" for the scheduler:
   - Command: `cd ~/canvas_todoist_sync && python run.py`
   - This ensures that the automatic sync functionality works properly

4. File-based caching strategy:
   - The application uses FileSystemCache on PythonAnywhere instead of Redis
   - Cache files are stored in `/tmp/canvas_todoist_cache` by default
   - You can customize the location with the CACHE_DIR environment variable

5. Web app configuration:
   - Source code: `/home/<username>/canvas_todoist_sync`
   - Working directory: `/home/<username>/canvas_todoist_sync`
   - WSGI configuration file:
   ```python
   import sys
   path = '/home/<username>/canvas_todoist_sync'
   if path not in sys.path:
       sys.path.append(path)
   
   from run import app as application
   ```

## Usage

1. Register for an account
2. Add your Canvas LMS API URL and token
   - Get this from your Canvas settings page: Account → Settings → Approved Integrations → New Access Token
3. Add your Todoist API token
   - Get this from Todoist: Settings → Integrations → Developer → API token
4. Go to the Dashboard to view your Canvas courses
5. Click "Sync" on any course to create Todoist tasks for assignments

## Configuration

The application supports different environments:

- `development`: Debug mode enabled, simple caching
- `testing`: In-memory database, WTF-CSRF disabled
- `production`: Enhanced security features, Redis caching

Set the environment by changing the `FLASK_ENV` environment variable.

## Premium Features

- Automated synchronization (hourly, daily, or weekly)
- Priority-based task creation
- Advanced filtering options

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you have any questions or need help, please create an issue on this repository. 