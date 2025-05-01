# Pine API

A FastAPI application that receives form data, integrates with Appwrite for storage, communicates with an external API, and sends email notifications.

## Features

- Accepts form data submissions
- Stores data in Appwrite database
- Communicates with external API services with bearer token authentication
- Sends email notifications to administrators
- CORS middleware to allow specific origins

## External API Integration

The application integrates with the Pineapple Motor Lead API:

```
Endpoint: POST http://gw-test.pineapple.co.za/users/motor_lead
```

### API Request Format

```json
{
	"source": "SureStrat",
	"first_name": "Peter",
	"last_name": "Smith",
	"email": "PeterSmith007@gmail.com",
	"id_number": "9510025800086",
	"quote_id": "679765d8cdfba62ff342d2ef",
	"contact_number": "0737111119"
}
```

### API Response Format

```json
{
	"success": true,
	"data": {
		"uuid": "66e1894aa137e938de5a76c5",
		"redirect_url": "https://test-pineapple-claims.herokuapp.com/car-insurance/get-started?uuid=66e1894aa137e938de5a76c5&ref=serithi"
	}
}
```

The application stores both the UUID and redirect URL from the API response in the Appwrite database.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with the following variables:

```
# Appwrite Configuration
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_API_KEY=your_api_key
APPWRITE_DATABASE_ID=your_database_id
APPWRITE_COLLECTION_ID=your_collection_id

# CORS Configuration
ALLOWED_ORIGIN=https://yourdomain.com

# Email Configuration
SMTP_SERVER=your_cpanel_smtp_server
SMTP_PORT=465
SMTP_USERNAME=your_email@yourdomain.com
SMTP_PASSWORD=your_email_password
ADMIN_EMAILS=admin1@yourdomain.com,admin2@yourdomain.com

# External API
EXTERNAL_API_URL=http://gw-test.pineapple.co.za/users/motor_lead
EXTERNAL_API_KEY=your_api_key
EXTERNAL_API_SECRET=your_api_secret
```

## Running the API

Development mode:

```bash
python run.py
```

or

```bash
uvicorn app.main:app --reload
```

Production mode:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /submit-form`: Submit form data as JSON (recommended)
- `GET /health`: Health check endpoint
- `GET /ping`: API status endpoint

## JSON Submission Format

The `/submit-form` endpoint accepts JSON data in the following format:

```json
{
	"formData": {
		"first_name": "John",
		"last_name": "Doe",
		"email": "john@example.com",
		"id_number": "1234567890123",
		"quote_id": "Q12345",
		"contact_number": "0123456789"
	},
	"agentInfo": {
		"agent": "Agent Name",
		"branch": "Branch Office"
	}
}
```

## API Response

The API responds with:

```json
{
	"message": "Form submitted successfully",
	"document_id": "unique_document_id",
	"api_response": {
		"success": true,
		"data": {
			"uuid": "unique_uuid",
			"redirect_url": "https://redirect-url-from-api"
		}
	},
	"redirect_url": "https://redirect-url-from-api"
}
```

The `redirect_url` is included at the top level for easier access by clients.

## Appwrite Schema

The application uses an Appwrite schema defined in `appwrite-schema.json`. This schema determines the fields that are stored in the Appwrite database. The schema includes:

- Customer information (first_name, last_name, email, etc.)
- Agent information (agent, branch)
- API response data (uuid, redirect_url)
- Error handling fields (api_error)

Make sure your Appwrite collection matches this schema. You can create the collection using the Appwrite Console or the Appwrite API.
