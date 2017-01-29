API
===
This document contains definitions for the backend API.

## Authentication

### POST `/api/v1/auth`

Generates a token for the supplied user.

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

#### Notes

If a user is not found with the supplied username, a new one is created. Password is ignored.
Token is jwt-encoded, with a payload that contains the user's id in the `id` field, ex. `{"id": 1002}`.

## Users

### GET `/api/v1/user/:user_id`

Reads information about a supplied user.

#### Response
```json
{
    "id": 8675309,
    "name": "Jenny",
    "email": "jenny@example.com",
    "teams": [
        {
            ..
        }
    ],
    "permissions": [
        "team.create",
        "..."
    ]
}
```

## Teams

### POST `/api/v1/team`

Creates a team.

#### Body

```json
{
    "name": "teamname",
    "type": "student"
}
```

The value of `type` _must_ be either `"student"`, `"other_team"`, `"class"`, `"colab_class"`, or `"senior_project"`.

#### Response

On success, returns status code `201 Created` with no body.

On insufficient permissions, status code `403 Forbidden`.

### GET `/api/v1/team/:id`

Gets information about a team.

#### Response

If this user has `team.read.elevated` _or_ the user has `team.read` and the user is a member of this team.

```json
{
    "id": 100,
    "name": "teamname",
    "type": "teamtype",
    "advance_time": 14,
    "members": [
        {
            "id": 200,
            "name": "Joseph"
        }
    ]
}
```

Otherwise:

```json
{
    "id": 100,
    "type": "teamtype"
}
```

#### Notes

The property `advance_time` indicates the number of days in advance that a team
can book a reservation.

### PUT `/api/v1/team/:id`

Updates the team's name.

#### Body

```json
{
    "name": "newteamname"
}
```

#### Response

On success, returns status code `204 No Content` and no body.

### DELETE `/api/v1/team/:id`

Deletes a team.

#### Response

On success, returns status code `204 No Content` and no body.

## Team Members

### POST `/api/v1/team/:team_id/user/:user_id`

Adds a user to the given team

#### Response

On success, returns status code `204 No Content` and no body.

### DELETE `/api/v1/team/:team_id/user/:user_id`

Removes a user from the given team

#### Response

On success, returns status code `204 No Content` and no body.
