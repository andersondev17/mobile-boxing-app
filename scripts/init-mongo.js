// Initial MongoDB indexes for boxing-api
// Run automatically by mongo image via docker-entrypoint-initdb.d

// boxing_sessions collection (raw landmark storage)
db.boxing_sessions.createIndex({ session_id: 1 }, { unique: true });
db.boxing_sessions.createIndex({ user_id: 1, created_at: -1 });

// auth_codes collection (temporary OAuth codes)
db.auth_codes.createIndex({ code: 1 }, { unique: true });
db.auth_codes.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });
