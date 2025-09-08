#!/bin/bash

echo "🧪 Testing Pine Transfer Form API Email Notifications with cURL"
echo "============================================================="
echo ""

# Check if server is running
echo "📡 Checking if server is running..."
if ! curl -s http://localhost:4000/health > /dev/null; then
    echo "❌ Server is not running on localhost:4000"
    echo "Please start the server first: python run.py"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Generate unique identifiers
TIMESTAMP=$(date +%s)
QUOTE_ID="TEST-CURL-QUOTE-${TIMESTAMP}"
PHONE_NUMBER="071234${TIMESTAMP: -4}"
ID_NUMBER="90010112345${TIMESTAMP: -2}"

echo "🔍 Test Details:"
echo "  Quote ID: $QUOTE_ID"
echo "  Phone: $PHONE_NUMBER"
echo "  ID Number: $ID_NUMBER"
echo ""

# Test 1: Quote API
echo "📋 TEST 1: Quote API Email Notification"
echo "========================================"
echo ""

echo "🔄 Sending quote request..."
QUOTE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST http://localhost:4000/api/v1/quote \
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
  }")

# Extract HTTP code and response
HTTP_CODE=$(echo "$QUOTE_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$QUOTE_RESPONSE" | sed '/HTTP_CODE:/d')

echo "📊 Quote Response:"
echo "  HTTP Code: $HTTP_CODE"
echo "  Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "201" ]; then
    echo "✅ Quote request successful!"
    echo "📧 Check your email for quote notification"
else
    echo "❌ Quote request failed"
fi

echo ""
echo "⏱️  Waiting 3 seconds before next test..."
sleep 3
echo ""

# Test 2: Transfer API
echo "🔄 TEST 2: Transfer API Email Notification"
echo "=========================================="
echo ""

echo "🔄 Sending transfer request..."
TRANSFER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST http://localhost:4000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_info\": {
      \"first_name\": \"John\",
      \"last_name\": \"Doe\",
      \"email\": \"john.doe@example.com\",
      \"contact_number\": \"$PHONE_NUMBER\",
      \"id_number\": \"$ID_NUMBER\",
      \"quote_id\": \"$QUOTE_ID\"
    },
    \"agent_info\": {
      \"agent_email\": \"test@surestrat.co.za\",
      \"branch_name\": \"Test Branch\"
    }
  }")

# Extract HTTP code and response
HTTP_CODE=$(echo "$TRANSFER_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$TRANSFER_RESPONSE" | sed '/HTTP_CODE:/d')

echo "📊 Transfer Response:"
echo "  HTTP Code: $HTTP_CODE"
echo "  Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "201" ]; then
    echo "✅ Transfer request successful!"
    echo "📧 Check your email for transfer notification"
else
    echo "❌ Transfer request failed"
fi

echo ""
echo "🎯 SUMMARY"
echo "=========="
echo "📧 If both requests were successful (HTTP 201), you should receive:"
echo "   1. Quote notification email"
echo "   2. Transfer notification email"
echo ""
echo "📬 Check your email inbox for notifications sent to:"
echo "   • Primary: zalisiles@surestrat.co.za"
echo "   • BCC: zalisiles@surestrat.co.za"
echo ""
echo "📊 Monitor the server terminal for detailed email logs"
echo "🔍 If no emails arrive, check the server logs for SMTP errors"
