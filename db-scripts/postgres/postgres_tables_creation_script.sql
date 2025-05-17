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

-- Stats Tables

CREATE TABLE public.events_definitions (
    event_id INT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL
);

CREATE TABLE public.user_events (
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    track_id VARCHAR(255) DEFAULT NULL,
    recommendation_type VARCHAR(255) DEFAULT NULL,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events_definitions(event_id) ON DELETE CASCADE
);

-- Inserting event definitions
INSERT INTO public.events_definitions (event_id, event_name) VALUES
(1, 'user_signed_up'),
(2, 'user_logged_in'),
(3, 'user_added_track'),
(4, 'user_liked_recommended_track'),
(5, 'user_disliked_recommended_track'),
(6, 'user_requested_recommendations'),
(7, 'user_ignored_recommendations');


