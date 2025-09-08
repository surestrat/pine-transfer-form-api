#!/bin/bash

echo "🧪 Manual Email Test - Single Quote Request"
echo "==========================================="
echo ""
echo "This will send ONE quote request and show you exactly what happens."
echo "Monitor your server terminal for email logs while running this."
echo ""

# Generate unique identifier
TIMESTAMP=$(date +%s)
QUOTE_ID="MANUAL-TEST-${TIMESTAMP}"

echo "📋 Sending quote request with ID: $QUOTE_ID"
echo ""

# Show the exact curl command
echo "🔧 cURL Command:"
echo "curl -X POST http://localhost:4000/api/v1/quote \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{...quote data...}'"
echo ""

# Execute the request
echo "🚀 Executing request..."
curl -X POST http://localhost:4000/api/v1/quote \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"SureStrat\",
    \"externalReferenceId\": \"$QUOTE_ID\",
    \"agentEmail\": \"test@surestrat.co.za\",
    \"agentBranch\": \"Test Branch\",
    \"vehicles\": [
      {
        \"year\": 2020,
        \"make\": \"Toyota\",
        \"model\": \"Corolla\",
        \"retailValue\": 250000,
        \"marketValue\": 220000,
        \"address\": {
          \"addressLine\": \"123 Test Street\",
          \"postalCode\": 7700,
          \"suburb\": \"Test Suburb\"
        },
        \"regularDriver\": {
          \"maritalStatus\": \"Single\",
          \"currentlyInsured\": true,
          \"yearsWithoutClaims\": 5,
          \"relationToPolicyHolder\": \"Self\",
          \"emailAddress\": \"driver@example.com\",
          \"mobileNumber\": \"0712345678\",
          \"idNumber\": \"9001011234567\",
          \"dateOfBirth\": \"1990-01-01\",
          \"licenseIssueDate\": \"2008-01-01\"
        }
      }
    ]
  }"

echo ""
echo ""
echo "✅ Request completed!"
echo ""
echo "🔍 What to look for in your server terminal:"
echo "   • 'Queuing email notification...'"
echo "   • 'Quote notification email queued'"
echo "   • SMTP connection logs"
echo "   • 'Email sent successfully to zalisiles@surestrat.co.za'"
echo ""
echo "📧 Check your email inbox for the notification"
