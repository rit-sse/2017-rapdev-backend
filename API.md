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
