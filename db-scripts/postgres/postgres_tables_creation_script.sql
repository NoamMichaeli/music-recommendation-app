CREATE TABLE public.tracks (
    track_id         VARCHAR PRIMARY KEY,
    id               INTEGER,
    artist_name      VARCHAR,
    track_name       VARCHAR,
    popularity       DOUBLE PRECISION,
    year             INTEGER,
    genre            VARCHAR,
    danceability     DOUBLE PRECISION,
    energy           DOUBLE PRECISION,
    key              INTEGER,
    loudness         DOUBLE PRECISION,
    mode             INTEGER,
    speechiness      DOUBLE PRECISION,
    acousticness     DOUBLE PRECISION,
    instrumentalness DOUBLE PRECISION,
    liveness         DOUBLE PRECISION,
    valence          DOUBLE PRECISION,
    tempo            DOUBLE PRECISION,
    duration_ms      VARCHAR
);

CREATE TABLE public.users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL
);

CREATE TABLE public.likes (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    track_id         VARCHAR(255) NOT NULL,
    update_timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT unique_user_likes UNIQUE (user_id, track_id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
);

CREATE TABLE public.dislikes (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    track_id         VARCHAR(255) NOT NULL,
    update_timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT unique_user_dislikes UNIQUE (user_id, track_id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
);
