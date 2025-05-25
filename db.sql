CREATE TABLE chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    session_id VARCHAR(100),
    role ENUM('user', 'bot'),
    message TEXT,
    search_query VARCHAR(100),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE chat_history MODIFY message TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;