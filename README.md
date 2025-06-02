# Surestrat Pineapple Integration API

This API service provides integration between Surestrat and Pineapple Insurance, enabling quote requests and lead transfers with email notifications.

## Features

- Quote request handling with Pineapple API integration
- Lead transfer to Pineapple with confirmation
- Email notifications for quotes and transfers
- Data storage using Appwrite
- Containerized deployment with Docker

## Requirements

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)
- Appwrite instance
- SMTP server access for email notifications
- Pineapple API credentials

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Application Settings
IS_PRODUCTION=false
PORT=4001
LOG_LEVEL=info
DEBUG=false

# Email Settings
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=your_username@example.com
SMTP_PASSWORD=your_password
EMAIL_FROM=noreply@yourdomain.com
ADMIN_EMAILS=admin1@example.com,admin2@example.com

# Appwrite Settings
APPWRITE_ENDPOINT=https://appwrite.yourdomain.com/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_API_KEY=your_api_key
DATABASE_ID=your_database_id
TRANSFER_COL_ID=your_transfer_collection_id
QUOTE_COL_ID=your_quote_collection_id

# Pineapple API Settings
PINEAPPLE_API_KEY=your_pineapple_api_key
PINEAPPLE_API_SECRET=your_pineapple_api_secret
PINEAPPLE_TRANSFER_API_URL=https://api.pineapple.co.za/transfer
PINEAPPLE_QUOTE_API_URL=https://api.pineapple.co.za/quote
```

## Installation

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the required environment variables
5. Run the application:
   ```
   python run.py
   ```

### Docker Deployment

1. Make sure Docker and Docker Compose are installed
2. Clone the repository
3. Create a `.env` file with the required environment variables
4. Build and start the containers:
   ```
   docker-compose up -d --build
   ```
5. To stop the application:
   ```
   docker-compose down
   ```

## API Endpoints

### Quote Request

```
POST /api/v1/quote
```

See [Frontend.md](Frontend.md) for detailed request/response formats and examples.

### Lead Transfer

```
POST /api/v1/transfer
```

See [Frontend.md](Frontend.md) for detailed request/response formats and examples.

## Appwrite Setup

1. Create a new Appwrite project
2. Create a database with two collections:
   - Quote collection
   - Transfer collection
3. Run the Appwrite schema initialization script:
   ```
   python scripts/appwrite_schema.py
   ```

## Troubleshooting

### Email Sending Issues

If emails are not being sent correctly:
1. Check SMTP credentials in your environment variables
2. Verify that the recipient email addresses are correctly formatted
3. Check the application logs for any SMTP-related errors

### API Connection Issues

If you're having trouble connecting to the Pineapple API:
1. Verify your API credentials
2. Check network connectivity
3. Ensure you're using the correct API URLs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
