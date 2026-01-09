# Ghost Identity Protection System

A cybersecurity solution that leverages Microsoft AI services to detect death events and automatically manage digital assets according to user-defined policies.

## Project Structure

```
├── backend/                 # Python Flask backend
│   ├── app/                # Application package
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   └── api/           # API endpoints
│   ├── tests/             # Backend tests
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Environment variables
│   └── init_db.py        # Database initialization
├── frontend/              # React.js frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   └── App.js        # Main application
│   └── package.json      # Node.js dependencies
└── .kiro/specs/          # Feature specifications
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

5. Start the Flask development server:
   ```bash
   python app.py
   ```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## Environment Configuration

Copy `.env.example` to `.env` in the backend directory and configure the following:

- **Database**: Currently configured for SQLite (development)
- **Azure AI Vision**: Add your Azure AI Vision endpoint and API key
- **Azure OpenAI**: Add your Azure OpenAI endpoint, API key, and deployment name
- **Encryption**: Configure encryption key for sensitive data

## Features

- **Digital Asset Vault**: Secure registration and management of digital assets
- **Death Certificate Verification**: Azure AI Vision-powered OCR and validation
- **Policy Execution**: Azure OpenAI-powered natural language policy interpretation
- **Audit Logging**: Tamper-proof audit trail with hash verification
- **Multi-Role Dashboard**: Interfaces for users, trusted contacts, and administrators

## Technology Stack

### Backend
- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Azure AI Vision**: Death certificate OCR and analysis
- **Azure OpenAI**: Policy interpretation and notification generation
- **SQLite**: Development database (PostgreSQL for production)

### Frontend
- **React.js**: User interface framework
- **React Bootstrap**: UI components
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

