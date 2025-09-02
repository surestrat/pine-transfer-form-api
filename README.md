# Surestrat Pineapple Integration API

A FastAPI-based REST API that integrates Surestrat with Pineapple Insurance, providing quote requests and lead transfer functionality with comprehensive email notifications.

## 🚀 Features

- **Quote Request Processing**: Handle vehicle insurance quote requests with Pineapple API integration
- **Lead Transfer**: Seamless transfer of customer leads to Pineapple with confirmation
- **Agent Tracking**: Full support for agent email and branch information
- **Email Notifications**: Automated email notifications for quotes and transfers
- **Data Persistence**: Appwrite-powered database storage with schema validation
- **Containerized Deployment**: Docker and Docker Compose support
- **Comprehensive Logging**: Rich logging with Rich library for better debugging
- **Health Checks**: Built-in health check endpoints
- **CORS Support**: Configurable CORS middleware for web integration

## 📋 Requirements

- Python 3.12+
- Docker and Docker Compose (for containerized deployment)
- Appwrite instance (Cloud or self-hosted)
- SMTP server access for email notifications
- Pineapple API credentials (test and production)

## ⚙️ Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Application Settings
ENVIRONMENT=test|production
PORT=4000
LOG_LEVEL=info
DEBUG=false

# Email Settings
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=465
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
EMAIL_FROM=noreply@yourdomain.com
ADMIN_EMAILS=admin1@yourdomain.com,admin2@yourdomain.com

# Appwrite Settings
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_API_KEY=your_api_key
DATABASE_ID=your-databse-id
QUOTE_COL_ID=quotes-collection-id
TRANSFER_COL_ID=transfers-collection-id

# Pineapple API Settings
PINEAPPLE_TEST_API_KEY=your_test_api_key
PINEAPPLE_TEST_API_SECRET=your_test_api_secret
PINEAPPLE_PROD_API_KEY=your_prod_api_key
PINEAPPLE_PROD_API_SECRET=your_prod_api_secret
```

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pine-transfer-form-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:4000`

### Docker Deployment

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd pine-transfer-form-api
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Build and start**
   ```bash
   docker-compose up -d --build
   ```

3. **Check logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop the application**
   ```bash
   docker-compose down
   ```

## 📡 API Endpoints

### Base URL
```
http://localhost:4000/api/v1
```

### Quote Request
```http
POST /api/v1/quote
```

**Request Body:**
```json
{
  "source": "SureStrat",
  "externalReferenceId": "12345678910",
  "agentEmail": "agent@surestrat.co.za",
  "agentBranch": "Sandton",
  "vehicles": [
    {
      "year": 2019,
      "make": "Volkswagen",
      "model": "Polo Tsi 1.2 Comfortline",
      "mmCode": "00815170",
      "category": "HB",
      "colour": "White",
      "engineSize": 1.2,
      "financed": "N",
      "owner": "Y",
      "status": "New",
      "partyIsRegularDriver": "Y",
      "accessories": "Y",
      "accessoriesAmount": 20000,
      "retailValue": 200000,
      "marketValue": 180000,
      "insuredValueType": "Retail",
      "useType": "Private",
      "overnightParkingSituation": "Garage",
      "coverCode": "Comprehensive",
      "address": {
        "addressLine": "123 Main Street",
        "postalCode": 2196,
        "suburb": "Sandton",
        "latitude": -26.10757,
        "longitude": 28.0567
      },
      "regularDriver": {
        "maritalStatus": "Married",
        "currentlyInsured": true,
        "yearsWithoutClaims": 0,
        "relationToPolicyHolder": "Self",
        "emailAddress": "driver@example.com",
        "mobileNumber": "0821234567",
        "idNumber": "9404054800086",
        "prvInsLosses": 0,
        "licenseIssueDate": "2018-10-02",
        "dateOfBirth": "1994-04-05"
      }
    }
  ]
}
```

**Response:**
```json
{
  "premium": 1149.34,
  "excess": 6200.0
}
```

### Lead Transfer
```http
POST /api/v1/transfer
```

**Request Body:**
```json
{
  "customer_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "contact_number": "0821234567",
    "id_number": "1234567890123",
    "quote_id": "quote_123"
  },
  "agent_info": {
    "agent_email": "agent@surestrat.co.za",
    "branch_name": "Sandton"
  }
}
```

**Response:**
```json
{
  "uuid": "12345678-1234-5678-1234-567812345678",
  "redirect_url": "https://portal.pineapple.co.za/quote/12345678-1234-5678-1234-567812345678"
}
```

### Health Check Endpoints
```http
GET /                    # Basic health check
GET /health             # Detailed health check
GET /debug/cors         # CORS configuration debug
```

## 🗄️ Database Schema

### Appwrite Collections

#### Quotes Collection
```javascript
{
  "source": "string",           // Always "SureStrat"
  "internalReference": "string", // Unique reference ID
  "status": "string",           // "PENDING" initially
  "vehicles": "string[]",       // Array of JSON vehicle strings
  "premium": "string",          // Premium amount as string
  "excess": "string",           // Excess amount as string
  "agentEmail": "string",       // Agent's email address
  "agentBranch": "string",      // Agent's branch name
  "created_at": "string"        // ISO timestamp
}
```

#### Transfers Collection
```javascript
{
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "contact_number": "string",
  "id_number": "string",
  "quote_id": "string",
  "agent_email": "string",      // PRIMARY: Agent's email address
  "agent_name": "string",       // LEGACY: Copy for backward compatibility
  "branch_name": "string",
  "created_at": "string",
  "updated_at": "string",
  "uuid": "string",             // From Pineapple response
  "redirect_url": "string"      // From Pineapple response
}
```

## 🔧 Appwrite Setup

1. **Create Appwrite Project**
   ```bash
   # Use Appwrite Cloud or self-hosted instance
   # Get your project ID and API key
   ```

2. **Initialize Database Schema**
   ```bash
   python scripts/appwrite_schema.py
   ```

3. **Verify Collections**
   - Check that `quotes` and `transfers` collections exist
   - Verify all required attributes are created
   - Ensure proper permissions are set

## 📧 Email Templates

The API includes comprehensive email notifications:

- **Quote Notifications**: Sent when new quote requests are received
- **Transfer Notifications**: Sent when leads are successfully transferred

Templates are located in the `templates/` directory:
- `quote_notification.html`
- `transfer_notification.html`

## 🐛 Troubleshooting

### Common Issues

#### Email Sending Issues
```bash
# Check SMTP configuration
tail -f logs/app.log | grep -i smtp

# Verify email settings in .env
cat .env | grep -E "(SMTP|EMAIL)"
```

#### API Connection Issues
```bash
# Check Pineapple API connectivity
curl -X GET https://gw-test.pineapple.co.za/health

# Verify API credentials
python -c "import os; print('API Key:', os.getenv('PINEAPPLE_TEST_API_KEY')[:10] + '...')"
```

#### Database Connection Issues
```bash
# Test Appwrite connection
python scripts/appwrite_schema.py

# Check database permissions
# Ensure collections have proper read/write permissions
```

#### CORS Issues
```bash
# Test CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:4000/api/v1/quote
```

### Debug Mode
Enable debug logging by setting:
```bash
DEBUG=true
LOG_LEVEL=debug
```

### Health Checks
```bash
# Basic health check
curl http://localhost:4000/

# Detailed health check
curl http://localhost:4000/health

# CORS debug
curl http://localhost:4000/debug/cors
```

## 🏗️ Project Structure

```
pine-transfer-form-api/
├── app/
│   ├── api/v1/endpoints/     # FastAPI route handlers
│   ├── schemas/             # Pydantic data models
│   ├── services/            # Business logic layer
│   └── utils/               # Helper utilities
├── config/                  # Configuration management
├── scripts/                 # Database setup scripts
├── templates/               # Email notification templates
├── docker-compose.yaml      # Docker configuration
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── run.py                  # Application entry point
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Check the [Frontend.md](Frontend.md) for detailed API documentation
- Review the application logs for error details
- Ensure all environment variables are properly configured

---

**Built with ❤️ using FastAPI, Appwrite, and Pineapple Insurance API**
