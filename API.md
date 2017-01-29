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

## Reservations

### POST `/api/v1/reservation`

Creates a new reservation.

#### Body

```json
{
    "team_id": 203,
    "room_id": 102,
    "start": "2017-01-29T16:02:23.913000",
    "end": "2017-01-29T17:02:56.301000",
    "override": true
}
```

Property `override` is optional. If present, will attempt to remove any lower-priority reservations which exist within this time slot for this room.

#### Response

On success, returns status code `201 Created` and no body.

On conflict, returns status code `409 Conflict` and the following body indicating whether retrying with `override`
set to `true` will help.

```json
{
    "overridable": true
}
```

### GET `/api/v1/reservation/:id`

Reads a reservation.

#### Response

If the user has permission to see the reservation's team information, returns:

```json
{
    "id": 102,
    "team": {
        "id": 300,
        "name": "teamname",
        "type": "teamtype",
        "advance_time": 14,
        "members": [
            {
                "id": 201,
                "name": "John"
            }
        ]
    },
    "room": {
        "id": 401,
        "number": "1655"
    },
    "start": "2017-01-29T16:02:23.913000",
    "end": "2017-01-29T17:02:56.301000"
}
```

Otherwise, returns:

```json
{
    "id": 102,
    "team": {
        "id": 300,
        "type": "teamtype",
    },
    "room": {
        "id": 401,
        "number": "1655"
    },
    "start": "2017-01-29T16:02:23.913000",
    "end": "2017-01-29T17:02:56.301000"
}
```
