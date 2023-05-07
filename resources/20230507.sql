-- DROP TABLE IF EXISTS "mood_messages";
CREATE TABLE IF NOT EXISTS "mood_messages" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content text,
    model varchar(16),
    prompt text
);

-- DROP TABLE IF EXISTS "mood_pictures";
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

-- DROP TABLE IF EXISTS "pictures";
CREATE TABLE IF NOT EXISTS "pictures" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filename text,
    size varchar(16),
    url text,
    reference_type varchar(16) CHECK (reference_type IN ('mood_pic')),
    reference_id uuid
);

-- DROP TABLE IF EXISTS "spot_images";
CREATE TABLE IF NOT EXISTS "spot_images" (
    id uuid PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    thumbnail text,
    url text,
    title text,
    reference_id uuid,
    meta_data jsonb
);

-- DROP TABLE IF EXISTS "spots";
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
