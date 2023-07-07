-- DROP TABLE IF EXISTS "users" CASCADE;
CREATE TABLE IF NOT EXISTS "users" (
    id uuid PRIMARY KEY,
    name varchar(256),
    email text unique,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- DROP TABLE IF EXISTS "user_sessions" CASCADE;
CREATE TABLE IF NOT EXISTS "user_sessions" (
    id uuid PRIMARY KEY,
    user_id uuid,
    mood_message_id uuid,
    mood_picture_id uuid,
    s3_picture_id uuid,
    spot_id uuid,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "user_fkey" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "mood_message_fkey" FOREIGN KEY ("mood_message_id") REFERENCES "mood_messages" ("id") ON DELETE CASCADE,
    CONSTRAINT "mood_picture_fkey" FOREIGN KEY ("mood_picture_id") REFERENCES "mood_pictures" ("id") ON DELETE CASCADE,
    CONSTRAINT "s3_picture_fkey" FOREIGN KEY ("s3_picture_id") REFERENCES "pictures" ("id") ON DELETE CASCADE,
    CONSTRAINT "spot_fkey" FOREIGN KEY ("spot_id") REFERENCES "spots" ("id") ON DELETE CASCADE
);

-- DROP TABLE IF EXISTS "mood_messages" CASCADE;
CREATE TABLE IF NOT EXISTS "mood_messages" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content text,
    model varchar(16),
    prompt text,
    cached boolean DEFAULT false
);

-- DROP TABLE IF EXISTS "mood_pictures" CASCADE;
CREATE TABLE IF NOT EXISTS "mood_pictures" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model varchar(16),
    prompt text,
    size varchar(16),
    url text,
    mood_message_id uuid,
    CONSTRAINT "mood_message_fkey" FOREIGN KEY ("mood_message_id") REFERENCES "mood_messages" ("id") ON DELETE CASCADE
);

-- DROP TABLE IF EXISTS "pictures" CASCADE;
CREATE TABLE IF NOT EXISTS "pictures" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filename text,
    size varchar(16),
    url text,
    reference_type varchar(16) CHECK (reference_type IN ('mood_pic')),
    reference_id uuid,
    found_spot boolean
);

-- DROP TABLE IF EXISTS "spot_images" CASCADE;
CREATE TABLE IF NOT EXISTS "spot_images" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    thumbnail text,
    url text,
    title text,
    reference_id uuid,
    meta_data jsonb
);

-- DROP TABLE IF EXISTS "spots" CASCADE;
CREATE TABLE IF NOT EXISTS "spots" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    address text,
    name text,
    rating real,
    rating_n integer,
    place_id varchar(64),
    reference varchar(64),
    types varchar(64)[],
    geometry jsonb,
    spot_image_id uuid,
    CONSTRAINT "spot_image_fkey" FOREIGN KEY ("spot_image_id") REFERENCES "spot_images" ("id") ON DELETE CASCADE
);
