# Travel GPT Backend

This is the backend API server for [o~dyssey AI].

## System Architecture
- **AWS S3**
  - Stores generated images.

- **Supabase**
  - Serverless PostgreSQL for data storage.

- **OpenAI**
  - **GPT model**
    - Generates suggested mood messages.
  - **DALL·E model**
    - Creates images based on mood messages.

- **SerpAPI**
  - Enables Google Lens image searches.

- **Google APIs**
  - Powers Google Map related features such as finding nearby spots.

- **Sentry**
  - Monitors the backend server's health and performance.

- **Fly.io**
  - Serverless platform for backend API server deployment.

## Implementation

### Requirements
- **Python**
- **Pipenv**

### Tech Stack
- **FastAPI**
  - **Gunicorn**
    - WSGI HTTP server (supports multiple workers).
  - **Uvicorn**
    - ASGI web server (asynchronous).
    - [Running Uvicorn with Gunicorn]:
      > Uvicorn includes a Gunicorn worker class allowing you to run ASGI
      > applications, with all of Uvicorn's performance benefits, while also
      > giving you Gunicorn's fully-featured process management.

## Get Started

### Environment Variables
- Set up the environment variables file `.env` by referencing `.env.example`.
- Run the following command or use a plugin like `autoenv` to load the variables:
  ```bash
  source .env
  ```

### Python Packages
- Install the Python virtual environment management tool `Pipenv`:
  ```bash
  python -m pip install pipenv
  ```
- Install python packages with `Pipenv`
  ```bash
  python -m pipenv sync
  ```

### Backend API Server
- Start the server by running the following command:
  ```bash
  python src/servers/server.py
  ```
- Test the API server:
  ```bash
  curl -XGET 'http://APP_HOST:APP_PORT/healthz' -H 'Authorization: Basic APP_AUTH_TOKEN'
  ```


[o~dyssey AI]: https://travel-gpt.fly.dev/
[Uvicorn running with Gunicorn]: https://www.uvicorn.org/#running-with-gunicorn
