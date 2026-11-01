# Backend Architecture

The backend provides REST APIs for government scheme
discovery and explainable eligibility assessment.

## Architecture

User
  ↓
FastAPI
  ↓
Service Layer
  ↓
Database
  ↓
Eligibility Engine
  ↓
Explanation Generator
  ↓
JSON Response

## API Endpoints

### GET /

Returns API status.

### GET /health

Checks backend health.

### GET /schemes

Returns schemes stored in the SQLite database.

### GET /schemes/{scheme_id}

Returns scheme details and eligibility rules.

### POST /schemes/{scheme_id}/eligibility

Evaluates a user profile against the eligibility rules
of a scheme.

## Technologies

- Python
- FastAPI
- Uvicorn
- SQLite
- Pydantic

## Architecture Layers

### API Layer

Handles HTTP requests and responses.

### Service Layer

Connects the API with database and eligibility modules.

### Database Layer

Stores schemes and eligibility rules.

### Eligibility Layer

Evaluates applicant profiles against deterministic rules.

### Explanation Layer

Generates understandable explanations for eligibility decisions.