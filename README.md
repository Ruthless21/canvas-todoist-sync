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