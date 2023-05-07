import os


def load_environment_variables():

    """load all environment variables"""

    # flask
    app_name  = os.getenv("FLASK_APP", "server")
    app_host  = os.getenv("FLASK_HOST", "0.0.0.0")
    app_port  = os.getenv("FLASK_PORT", "5000")
    app_debug = os.getenv("FLASK_DEBUG", "").lower() == "true"

    # aws
    aws_access_id     = os.getenv("AWS_ACCESS_KEY_ID")
    aws_access_key    = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_access_region = os.getenv("AWS_DEFAULT_REGION")

    aws_s3_bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    aws_s3_file_path   = os.getenv("AWS_S3_FILE_PATH")

    # db
    db_dsn = os.getenv("DB_DSN")

    # google
    google_api_key = os.getenv("GOOGLE_API_KEY")

    # openai
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_org = os.getenv("OPENAI_API_ORG")

    mood_message_model = os.getenv("MOOD_MESSAGE_MODEL")
    mood_image_size    = os.getenv("MOOD_IMAGE_SIZE")

    # serpapi
    serpapi_api_key = os.getenv("SERPAPI_API_KEY")

    envs = {
        'app_debug':          app_debug,
        'app_host':           app_host,
        'app_name':           app_name,
        'app_port':           app_port,
        'aws_access_id':      aws_access_id,
        'aws_access_key':     aws_access_key,
        'aws_access_region':  aws_access_region,
        'aws_s3_bucket_name': aws_s3_bucket_name,
        'aws_s3_file_path':   aws_s3_file_path,
        'db_dsn':             db_dsn,
        'google_api_key':     google_api_key,
        'openai_api_key':     openai_api_key,
        'openai_api_org':     openai_api_org,
        'mood_message_model': mood_message_model,
        'mood_image_size':    mood_image_size,
        'serpapi_api_key':    serpapi_api_key,
    }

    return envs
