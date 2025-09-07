# X-Scheduler

A Python-based application to schedule and manage posts for X (formerly Twitter).

## Features

- Schedule X posts and threads via CSV upload
- Monitor scheduled posts through a user-friendly dashboard
- Support for media attachments
- Thread scheduling support
- Timezone support
- Built with FastAPI, APScheduler, and Tweepy

## Installation

### Using Docker (Recommended)

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/x-scheduler.git
   cd x-scheduler
   ```

2. Create an `.env` file based on the example:

   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your X API credentials and settings

4. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Manual Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/x-scheduler.git
   cd x-scheduler
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install .
   ```

3. Create an `.env` file based on the example:

   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your X API credentials and settings

5. Run the application:
   ```bash
   uvicorn app.main:app --reload --port 8002
   ```

## Usage

1. Access the application at `http://localhost:8002`

2. Navigate to the Dashboard

3. Upload a CSV file with your posts data

4. Monitor the status of your scheduled posts on the dashboard

## CSV Format

Your CSV file should have the following columns:

| Column          | Description                                  | Required |
| --------------- | -------------------------------------------- | -------- |
| content         | The text content of the post (max 280 chars) | Yes      |
| date            | Date in YYYY-MM-DD format                    | Yes      |
| time            | Time in HH:MM:SS format                      | Yes      |
| timezone        | Timezone (e.g., UTC, America/New_York)       | Yes      |
| thread_id       | ID to group posts as a thread                | No       |
| thread_position | Position of the post in the thread           | No       |
| thread_title    | Title of the thread                          | No       |
| media_urls      | Comma-separated URLs to media files          | No       |

Example:

```
content,date,time,timezone,thread_id,thread_position,thread_title,media_urls
"This is my first post!",2023-01-01,09:00:00,UTC,,,,"https://example.com/image.jpg"
"First post in a thread",2023-01-02,10:00:00,UTC,thread1,1,"My Thread",""
"Second post in the thread",2023-01-02,10:00:00,UTC,thread1,2,"My Thread",""
```

## X API Access

To use this application, you need to obtain API credentials from the X Developer Portal:

1. Sign up for a developer account at [developer.x.com](https://developer.x.com)
2. Create a new Project and App
3. Apply for Elevated access if needed
4. Generate consumer keys and access tokens
5. Add these credentials to your `.env` file

## Development

This project uses:

- FastAPI for the backend API
- APScheduler for post scheduling
- Tweepy for X API integration
- Jinja2 and DaisyUI for the frontend
- Docker and Docker Compose for containerization

## License

[License information]
