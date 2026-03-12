CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (
        status IN ('pending', 'in_review', 'spam', 'not_spam')
    ),
    assigned_to VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (
            status = 'pending'
            AND assigned_to IS NULL
        )
        OR (
            status = 'in_review'
            AND assigned_to IS NOT NULL
        )
        OR (status IN ('spam', 'not_spam'))
    )
);
CREATE TABLE IF NOT EXISTS video_logs (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    moderator_name VARCHAR(255),
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_video_logs_video_id FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_videos_status_created_at ON videos (status, created_at);
CREATE INDEX IF NOT EXISTS idx_videos_assigned_to ON videos (assigned_to);
CREATE INDEX IF NOT EXISTS idx_video_logs_video_id_created_at ON video_logs (video_id, created_at);
