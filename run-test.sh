#!/bin/bash

# Simple load test script to generate requests to Flask app endpoints

set -e

# Configuration
BASE_URL="http://localhost:9000"
DURATION=60  # 1 minute

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting load test for ${DURATION} seconds...${NC}"
echo -e "${BLUE}Base URL: ${BASE_URL}${NC}"
echo ""

# Function to test GET /
test_hello() {
    while [ $SECONDS -lt $DURATION ]; do
        curl -s "${BASE_URL}/" > /dev/null
        sleep 0.1
    done
    echo "Hello endpoint completed"
}

# Function to test POST /items
test_add_item() {
    while [ $SECONDS -lt $DURATION ]; do
        key="test_key_$(date +%s)_$$"
        value="test_value_$(date +%s)"
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "{\"key\":\"$key\",\"value\":\"$value\"}" \
            "${BASE_URL}/items" > /dev/null
        sleep 0.2
    done
    echo "Add item endpoint completed"
}

# Function to test GET /items/<key>
test_get_item() {
    # First, add some test items
    for i in {1..5}; do
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "{\"key\":\"load_test_key_$i\",\"value\":\"load_test_value_$i\"}" \
            "${BASE_URL}/items" > /dev/null
    done
    
    while [ $SECONDS -lt $DURATION ]; do
        key_num=$((RANDOM % 5 + 1))
        curl -s "${BASE_URL}/items/load_test_key_$key_num" > /dev/null
        sleep 0.1
    done
    echo "Get item endpoint completed"
}

# Function to test GET /items
test_list_items() {
    while [ $SECONDS -lt $DURATION ]; do
        curl -s "${BASE_URL}/items" > /dev/null
        sleep 0.3
    done
    echo "List items endpoint completed"
}

# Function to test cache miss scenarios
test_cache_miss() {
    while [ $SECONDS -lt $DURATION ]; do
        # Generate random keys that likely don't exist (cache miss)
        random_key="cache_miss_$(date +%s)_$$_$RANDOM"
        curl -s "${BASE_URL}/items/$random_key" > /dev/null
        sleep 0.5
    done
    echo "Cache miss endpoint completed"
}

# Check if the app is running
echo -e "${BLUE}Checking if the Flask app is running...${NC}"
if ! curl -s "${BASE_URL}/" > /dev/null; then
    echo -e "${RED}Error: Flask app is not running at ${BASE_URL}${NC}"
    echo -e "Please start the app first with: docker-compose up"
    exit 1
fi

echo -e "${GREEN}Flask app is running!${NC}"

# Start the timer
SECONDS=0

echo -e "\n${BLUE}Starting parallel load test...${NC}"

# Start all test functions in parallel
test_hello &
test_add_item &
test_get_item &
test_list_items &
test_cache_miss &

# Wait for all background jobs to complete
wait

echo -e "\n${GREEN}Load test completed!${NC}"
