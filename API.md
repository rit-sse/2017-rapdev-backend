API
===
This document contains definitions for the backend API.

## Authentication

### POST `/api/v1/auth`
#### Body
```json
{
    "username": "foobar",
    "password": "anything goes"
}
```
#### Response
```json
{
    "token": "..."
}
```

## Users

### GET `/api/v1/user/:user_id`

#### Response
```json
{
    "id": 8675309,
    "name": "Jenny",
    "email": "jenny@example.com",
    "teams": [
        ...
    ],
    "permissions": [
        ...
    ]
}
```
