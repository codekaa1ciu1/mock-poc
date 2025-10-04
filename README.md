# Mock Server with User Access Control

A Python-based mock server management system with user access control, built using Flask, SQLite, and WireMock integration.

## Features

- 🔐 **User Authentication & Access Control**
  - Admin and regular user roles
  - SQLite database for user management
  - Session-based authentication

- 👨‍💼 **Admin Portal**
  - User management (create, activate/deactivate, admin rights)
  - WireMock server status monitoring
  - Bulk sync all mappings to WireMock

- 👤 **User Portal**
  - Create and manage personal mock mappings
  - Configure HTTP method, URL path, response status, body, and headers
  - Priority-based mapping for conflict resolution
  - Activate/deactivate mappings
  - Auto-sync to WireMock server

- 🎭 **WireMock Integration**
  - Automatic synchronization of mock mappings
  - Support for all HTTP methods
  - Custom response headers and status codes
  - Priority-based request matching

## Prerequisites

- Python 3.7 or higher
- WireMock server (optional for development, required for actual mocking)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/codekaa1ciu1/mock-poc.git
cd mock-poc
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Download and start WireMock:
```bash
# Download WireMock standalone JAR
curl -O https://repo1.maven.org/maven2/org/wiremock/wiremock-standalone/3.3.1/wiremock-standalone-3.3.1.jar

# Start WireMock on port 8080
java -jar wiremock-standalone-3.3.1.jar --port 8080
```

## Usage

### Starting the Application

Run the Flask application:
```bash
python app.py
```

The web portal will be available at: `http://localhost:5000`

### Default Credentials

- **Username:** `admin`
- **Password:** `admin123`

⚠️ **Important:** Change the default admin password after first login!

### Configuration

You can configure the application using environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_PATH="mock_server.db"
export WIREMOCK_URL="http://localhost:8080"
```

Or modify `config.py` directly.

## Project Structure

```
mock-poc/
├── app.py                  # Main Flask application
├── config.py              # Configuration settings
├── database.py            # SQLite database operations
├── wiremock_service.py    # WireMock integration
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── admin/
│   │   └── dashboard.html # Admin dashboard
│   └── user/
│       ├── dashboard.html      # User dashboard
│       ├── create_mapping.html # Create mapping form
│       └── edit_mapping.html   # Edit mapping form
└── mock_server.db        # SQLite database (created on first run)
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: SHA-256 hashed password
- `is_admin`: Admin flag (0 or 1)
- `is_active`: Active status (0 or 1)
- `created_at`: Timestamp

### Mock Mappings Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `name`: Mapping name
- `request_method`: HTTP method (GET, POST, etc.)
- `request_url`: URL path to match
- `response_status`: HTTP response status code
- `response_body`: Response body content
- `response_headers`: JSON string of response headers
- `priority`: Priority for matching (1-10)
- `is_active`: Active status (0 or 1)
- `created_at`: Timestamp
- `updated_at`: Last update timestamp

## Admin Tasks

### Creating Users
1. Log in as admin
2. Navigate to Admin Dashboard
3. Click "Create New User"
4. Fill in username, password, and optionally check "Admin"
5. Click "Create"

### Managing Users
- **Toggle Admin Rights:** Click "Make Admin" or "Remove Admin"
- **Activate/Deactivate:** Click "Activate" or "Deactivate"
- **Delete User:** Click "Delete" (cannot delete yourself)

### Syncing to WireMock
Click "🔄 Sync All Mappings to WireMock" to push all active mappings to WireMock server.

## User Tasks

### Creating Mock Mappings
1. Log in as a user
2. Click "➕ Create New Mapping"
3. Fill in:
   - **Mapping Name:** Descriptive name for the mapping
   - **HTTP Method:** GET, POST, PUT, PATCH, DELETE, etc.
   - **Request URL Path:** Path to match (e.g., `/api/users/123`)
   - **Response Status Code:** HTTP status (e.g., 200, 404, 500)
   - **Response Body:** Response content (JSON, XML, text, etc.)
   - **Response Headers:** JSON format headers (e.g., `{"Content-Type": "application/json"}`)
   - **Priority:** 1-10, higher priority matches first
4. Click "Create Mapping"

### Managing Mappings
- **Edit:** Click "Edit" to modify mapping details
- **Activate/Deactivate:** Toggle mapping status
- **Delete:** Remove mapping permanently

## API Examples

### Example Mapping Configuration

**Mapping Name:** Get User Details  
**Method:** GET  
**URL Path:** `/api/users/123`  
**Status Code:** 200  
**Response Body:**
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin"
}
```
**Response Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Custom-Header": "Custom-Value"
}
```
**Priority:** 5

After creating this mapping and syncing to WireMock, a GET request to `http://localhost:8080/api/users/123` will return the configured response.

## Security Notes

- Passwords are hashed using SHA-256
- Session-based authentication
- Admin-only routes are protected
- Users can only manage their own mappings
- Change default credentials in production
- Use environment variables for sensitive configuration

## Development

### Running in Development Mode

The application runs in debug mode by default when started with `python app.py`:
```bash
python app.py
```

### Database Initialization

The SQLite database is automatically created on first run with:
- Users table
- Mock mappings table
- Default admin user (admin/admin123)

### Testing WireMock Integration

1. Start WireMock server
2. Create a mapping in the user portal
3. Test the mock endpoint:
```bash
curl http://localhost:8080/your-configured-path
```

## Troubleshooting

### WireMock Connection Issues
- Ensure WireMock is running: `java -jar wiremock-standalone-*.jar --port 8080`
- Check the WIREMOCK_URL configuration in `config.py`
- Verify firewall settings

### Database Issues
- Delete `mock_server.db` to reset the database
- Check file permissions for database file

### Login Issues
- Use default credentials: admin/admin123
- Check if user is active in the database

## License

Apache License 2.0 - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.