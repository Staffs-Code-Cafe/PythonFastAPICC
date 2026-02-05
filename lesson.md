# Code Cafe Interactive API!

This is a **FastAPI-based interactive platform** designed to teach how APIs work, including HTTP methods, authentication, protected endpoints, and interactive API challenges.

---

## Overview

The API provides several endpoints to illustrate fundamental API concepts in a hands-on way. Students can explore the endpoints using tools like **Swagger UI**, **Postman**, or **curl**.

> Recommended tool: **curl** (Git Bash on university PCs)

---

## Core Learning Endpoints

### 1. GET /lessons
**Purpose:** Demonstrates a public GET request.

**Description:** Returns a list of lessons. This is a public endpoint that does not require authentication.

**PLEASE USE GIT BASH ON UNI PCS**

**Example Request:**
```bash
curl http://{IP Address}/lessons
```

**Example Response:**
```json
[
  {
    "id": 1,
    "title": "GET Basics",
    "description": "Learn how GET requests work",
    "task": "Fetch this lesson using GET",
    "endpoint": "/lessons"
  }
]
```

---

### 2. POST /token
**Purpose:** Demonstrates authentication with JWT.

**Description:** Allows users to log in with a username and password. Returns a JWT token used for accessing protected routes.

**Example Request:**
```bash
curl -X POST http://{IP Address}/token \
  -F 'username=student' \
  -F 'password=demo123'
```

**Example Response:**
```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

**Note:** This token should be included in the `Authorization` header for protected endpoints.

---

### 3. GET /protected
**Purpose:** Demonstrates a protected endpoint using JWT authentication.

**Description:** Only accessible with a valid JWT token.

**Example Request:**
```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" http://{IP Address}/protected
```

**Example Response:**
```json
{
  "message": "You accessed a protected endpoint!",
  "user": "student",
  "lesson": "This demonstrates JWT authentication"
}
```

---

### 4. POST /lessons
**Purpose:** Demonstrates a POST request with authentication.

**Description:** Creates a new lesson. Requires a valid JWT token.

**Example Request:**
```bash
curl -X POST http://{IP Address}/lessons \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"id":4,"title":"New Lesson","description":"Learn POST","task":"Create a lesson","endpoint":"/lessons"}'
```

**Example Response:**
```json
{
  "id": 4,
  "title": "New Lesson",
  "description": "Learn POST",
  "task": "Create a lesson",
  "endpoint": "/lessons"
}
```

---

# 🎯 API Scavenger Hunt Challenge Mode

This mode turns the API into an **interactive learning game** where students must discover endpoints, extract values, combine results, and submit the correct answer to win a prize.

---

## Challenge Flow

### GET /challenge
**Purpose:** Entry point for the game.

**Description:** Provides instructions and hints.

```bash
curl http://{IP Address}/challenge
```

**Response Example:**
```json
{
  "challenge": "API Scavenger Hunt",
  "instructions": [
    "Find hidden endpoints.",
    "Each endpoint returns a number.",
    "Add all numbers together.",
    "Send the result to /challenge/submit to win the prize."
  ],
  "hint": "Look for endpoints with Greek names"
}
```

---

### Hidden Endpoints (Discovery Task)
Students must find and access these endpoints:

- `GET /challenge/...`
- `GET /challenge/...`
- `GET /challenge/...`

Each endpoint returns a numeric value:
```json
{ "value": int }
```

---

### POST /challenge/submit
**Purpose:** Submit the combined result.

**Description:** Students add the values from all discovered endpoints and submit the result.

**Example Request:**
```bash
curl -X POST http://{IP Address}/challenge/submit \
  -H "Content-Type: application/json" \
  -d '{"result": int}'
```

**Success Response:**
```json
{
  "status": "WIN",
  "message": "Congratulations! You solved the API challenge!",
  "prize": "Access granted to the second endpoint",
  "next": "{The next endpoint}"
}
```

**Failure Response:**
```json
{
  "detail": "Incorrect result. Try again."
}
```

---

### GET /challenge/key/start
**Purpose:** Begin key retrieval step.

**Description:** Returns a nonce and instructions to compute a SHA256 hash. The string to hash uses the numeric values you discovered:

```
"<alpha>-<beta>-<gamma>-<nonce>"
```

For the current challenge numbers, that means:
```
"7-13-21-<nonce>"
```

**Example Request:**
```bash
curl http://{IP Address}/{Secret second endpoint}
```

**Example Response:**
```json
{
  "step": "hash",
  "nonce": "<NONCE>",
  "instructions": "Compute SHA256 of 'alpha-beta-gamma-<nonce>' and POST to {Super secret endpoint}"
}
```

---

### POST /challenge/key/hash
**Purpose:** Submit the computed hash to receive a key.

**Description:** Compute SHA256 of the string "7-13-21-<nonce>" and submit both the nonce and the hex-encoded hash. If correct, you get a key bound to your IP.


**Use the helper script**

You can use the included helper tool to produce the hash and ready-to-send JSON:

```bash
python challenge_hash.py --alpha {Super secret number 1} --beta {Super secret number 2} --gamma {Super secret number 1} --nonce {Super secret nonce}
```

Copy the printed JSON into the POST request to /challenge/key/hash.

**Example Request:**
```bash
curl -X POST http://{IP Address}/challenge/key/hash \
  -H "Content-Type: application/json" \
  -d '{"nonce":"<NONCE>","hash":"<SHA256_HEX>"}'
```

**Success Response:**
```json
{
  "status": "OK",
  "next": "/challenge/prize",
  "key_hint": "Use query param ?key=...",
  "key": "<KEY>"
}
```

---

### GET /challenge/prize
**Purpose:** Reward endpoint.

**Description:** Requires the key provided after the hash step. The key is tied to your IP.

```bash
curl "http://{IP Address}/challenge/prize?key=<KEY>"
```

**Response Example:**
```json
{
  "Congrats": "You win!"
  "prize": "£10 giftcard of your choice",
}
```

---

## Learning notes for further development

- API endpoint discovery
- API documentation usage
- Request chaining
- Data extraction
- Logical data processing
- Authentication flows
- Real-world API usage patterns
- Problem-solving through APIs

---


## Security Notes

- Always use **HTTPS** in production
- Store `SECRET_KEY` in environment variables
- Use **hashed passwords** (bcrypt)
- Implement **rate limiting**
- Add **CORS restrictions**
- Use API gateways / reverse proxies
- Logging and monitoring

---
