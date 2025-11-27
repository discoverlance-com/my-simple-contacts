# Simple Contacts

> **⚠️ IMPORTANT NOTICE: AI-GENERATED PROJECT**
>
> **This project was created with AI assistance and is intended for educational and demonstration purposes. Before using in production or any critical environment, please:**
>
> - **Thoroughly review and validate all code**
> - **Conduct comprehensive security testing**
> - **Verify database configurations and connection handling**
> - **Test all functionality in your specific environment**
> - **Consider this a starting point, not a production-ready solution**

A modern Flask web application for managing personal contacts with database persistence and production-ready deployment options.

## 🌟 Features

- **Contact Management**: Create, view, and delete contacts
- **Form Validation**: Client and server-side validation with error feedback
- **Database Integration**: SQLAlchemy ORM with automatic Cloud SQL/SQLite switching
- **Responsive Design**: Clean, mobile-friendly interface
- **Production Ready**: Docker support with Gunicorn WSGI server
- **Environment Flexibility**: Automatic development/production database detection
- **Comprehensive Testing**: Full test suite with coverage reporting
- **Session Management**: Robust database connection handling

## 📁 Project Structure

```
my-simple-contacts/
├── pyproject.toml            # Project configuration and dependencies
├── main.py                    # Main Flask application
├── models.py                  # SQLAlchemy models and database setup
├── requirements.txt           # Production dependencies (legacy)
├── requirements-dev.txt       # Development dependencies (legacy)
├── run_tests.py              # Test runner script
├── Dockerfile                # Production container configuration
├── .dockerignore             # Docker build exclusions
├── .gitignore                # Git exclusions
├── database/
│   └── connector.py          # Google Cloud SQL connector
├── templates/
│   ├── homepage.html         # Main contact listing page
│   └── create_contact.html   # Contact creation form
├── tests/
│   ├── conftest.py          # Test configuration and fixtures
│   ├── test_routes.py       # Flask route tests
│   ├── test_models.py       # Database model tests
│   └── test_integration.py  # End-to-end integration tests
└── contacts.db              # SQLite database (development only)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip package manager

### Local Development

1. **Clone the repository**

   ```bash
   git clone git@github.com:discoverlance-com/my-simple-contacts.git
   cd my-simple-contacts
   ```

2. **Install dependencies**

   **Using uv (recommended):**

   ```bash
   # Install production dependencies
   uv sync

   # Install with development dependencies
   uv sync --extra dev
   ```

   **Using pip:**

   ````bash
   # Production dependencies
   pip install -r requirements.txt

   # Development dependencies
   pip install -r requirements-dev.txt
   ```3. **Run the application**

   ```bash
   # Using uv
   uv run python main.py

   # Using python directly
   python main.py
   ````

3. **Access the application**

   Open your browser and navigate to `http://localhost:8000`

### First Run

- The application will automatically create a SQLite database (`contacts.db`)
- Sample contacts will be seeded for demonstration
- All data is persisted between runs

## ⚙️ Project Configuration

This project uses modern Python packaging with `pyproject.toml`:

- **Dependencies**: Managed through `pyproject.toml` with optional dev dependencies
- **Testing**: Configured with pytest settings and coverage
- **uv support**: Optimized for the uv package manager
- **Legacy support**: Still supports pip with requirements.txt files

### Development Dependencies

The project includes optional development dependencies defined in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0"
]
```

## 🗄️ Database Configuration

The application supports two database modes:

### Development Mode (SQLite)

- **Automatic**: Used when no Cloud SQL environment variables are set
- **File**: `contacts.db` (automatically created)
- **Benefits**: Zero configuration, perfect for local development

### Production Mode (Google Cloud SQL)

Set these environment variables to enable Cloud SQL:

```bash
export CONTACTS_INSTANCE_CONNECTION_NAME=\"your-project:region:instance\"
export CONTACTS_DB_USER=\"your-username\"
export CONTACTS_DB_PASS=\"your-password\"
export CONTACTS_DB_NAME=\"your-database\"
```

## 📋 API Endpoints

| Method | Endpoint               | Description                |
| ------ | ---------------------- | -------------------------- |
| GET    | `/`                    | Homepage with contact list |
| GET    | `/create-contact`      | Contact creation form      |
| POST   | `/create-contact`      | Submit new contact         |
| POST   | `/delete-contact/<id>` | Delete specific contact    |

## 🧪 Testing

The application includes a comprehensive test suite covering routes, models, and integration scenarios.

### Running Tests

````bash
# Using uv (recommended)
uv run python run_tests.py --coverage
uv run python run_tests.py --quick
uv run pytest tests/ -v

# Using python directly
python run_tests.py --coverage
python run_tests.py --quick
python -m pytest tests/ -v

# Run specific test categories
uv run pytest tests/test_routes.py      # Route tests
uv run pytest tests/test_models.py      # Model tests
uv run pytest tests/test_integration.py # Integration tests
```### Test Coverage

- **Routes**: HTTP endpoints, form validation, error handling
- **Models**: Database operations, session management, CRUD operations
- **Integration**: End-to-end scenarios, database initialization
- **Coverage**: Automated reporting with pytest-cov

### Test Dependencies

```bash
# Using uv with optional dev dependencies
uv sync --extra dev

# Using pip (legacy)
pip install -r requirements-dev.txt
````

## 🛠️ Development

### Running in Development Mode

```bash
# With debug mode (auto-reload on changes)
python main.py

# Using Flask CLI
export FLASK_APP=main.py
export FLASK_ENV=development
flask run --port 8000

# Modern Flask syntax
python -m flask --app main.py --debug run --port 8000
```

### Form Validation Rules

**Name Field:**

- Required
- Minimum 2 characters
- Trimmed whitespace

**Address Field:**

- Required
- Minimum 5 characters
- Trimmed whitespace

### Database Operations

**Contact Model:**

```python
class Contact(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(500), nullable=False)
```

**Key Functions:**

- `init_db()`: Create database tables
- `seed_database()`: Add sample data if empty
- `get_db_session()`: Get database session with error handling

## 🐳 Production Deployment

### Docker Deployment

1. **Build the container**

   ```bash
   docker build -t simple-contacts .
   ```

2. **Run the container**

   ```bash
   docker run -p 8000:8000 simple-contacts
   ```

3. **With environment variables**
   ```bash
   docker run -p 8000:8000 \
     -e SECRET_KEY=\"your-production-secret\" \
     -e CONTACTS_INSTANCE_CONNECTION_NAME=\"project:region:instance\" \
     -e CONTACTS_DB_USER=\"username\" \
     -e CONTACTS_DB_PASS=\"password\" \
     -e CONTACTS_DB_NAME=\"database\" \
     simple-contacts
   ```

### Production Features

- **Gunicorn WSGI Server**: 4 workers for better performance
- **Health Checks**: Built-in health monitoring
- **Security**: Non-root user, secure defaults
- **Logging**: Comprehensive application and access logs

## 🔧 Configuration

### Environment Variables

| Variable                            | Description                   | Default            |
| ----------------------------------- | ----------------------------- | ------------------ |
| `SECRET_KEY`                        | Flask secret key for sessions | `fallback-dev-key` |
| `CONTACTS_INSTANCE_CONNECTION_NAME` | Cloud SQL instance            | None (uses SQLite) |
| `CONTACTS_DB_USER`                  | Database username             | None               |
| `CONTACTS_DB_PASS`                  | Database password             | None               |
| `CONTACTS_DB_NAME`                  | Database name                 | None               |

### Port Configuration

The application runs on port 8000 by default to avoid Windows port 5000 conflicts. Change in `main.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Change port here
```

## 🧪 Testing

### Manual Testing

1. **Homepage**: Verify contacts display correctly
2. **Create Contact**:
   - Test validation with invalid data
   - Verify successful creation and redirect
3. **Delete Contact**:
   - Confirm deletion prompt
   - Verify contact removal from list

### Database Testing

```bash
# Check SQLite database
sqlite3 contacts.db
.tables
SELECT * FROM contacts;
.quit
```

## 🔒 Security Considerations

### Development

- Uses fallback secret key (acceptable for local development)
- SQLite database (local file access only)

### Production

- **Set strong `SECRET_KEY`**: Use cryptographically secure random string
- **Database Security**: Cloud SQL with proper authentication
- **Container Security**: Non-root user execution
- **Environment Variables**: Never commit secrets to version control

### Example Production Secret Key Generation

```python
import secrets
print(secrets.token_urlsafe(32))
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**

```
An attempt was made to access a socket in a way forbidden by its access permissions
```

**Solution**: Port 5000 is reserved on Windows. Application uses port 8000 by default.

**Database Errors**

- Check environment variables for Cloud SQL
- Verify `contacts.db` permissions for SQLite
- Review console logs for SQLAlchemy errors

**Template Errors**

```
jinja2.exceptions.UndefinedError: 'errors' is undefined
```

**Solution**: Ensure all template renders include required variables (already fixed).

### Debug Mode

Enable detailed error messages:

```python
app.run(debug=True, port=8000)
```

## 📦 Dependencies

### Production Dependencies

| Package                    | Version | Purpose                       |
| -------------------------- | ------- | ----------------------------- |
| flask                      | ~3.1.2  | Web framework                 |
| sqlalchemy                 | >=2.0.0 | Database ORM                  |
| cloud-sql-python-connector | ~1.18.5 | Google Cloud SQL connectivity |
| pymysql                    | ~1.1.2  | MySQL database driver         |

### Development Dependencies

| Package    | Version | Purpose                 |
| ---------- | ------- | ----------------------- |
| pytest     | >=7.0.0 | Testing framework       |
| pytest-cov | >=4.0.0 | Test coverage reporting |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 📞 Support

For questions or issues:

1. Check the troubleshooting section
2. Review the console logs for error details
3. Create an issue in the repository

---
