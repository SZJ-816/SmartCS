CREATE DATABASE IF NOT EXISTS smartcs DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smartcs;

CREATE TABLE IF NOT EXISTS tenant (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    contact_name VARCHAR(50),
    contact_phone VARCHAR(20),
    plan VARCHAR(20) DEFAULT 'free',
    plan_expire_at TIMESTAMP NULL,
    max_agents INT DEFAULT 1,
    max_knowledge INT DEFAULT 100,
    max_conversations INT DEFAULT 500,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'agent',
    avatar_url VARCHAR(500) DEFAULT NULL,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tenant_username (tenant_id, username),
    UNIQUE KEY uk_tenant_email (tenant_id, email),
    FOREIGN KEY (tenant_id) REFERENCES tenant(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS knowledge (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    question VARCHAR(500) NOT NULL,
    answer TEXT NOT NULL,
    keywords VARCHAR(500),
    view_count INT DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id),
    INDEX idx_tenant_cat (tenant_id, category)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS conversation (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    visitor_id VARCHAR(100),
    visitor_name VARCHAR(50) DEFAULT 'visitor',
    agent_id BIGINT DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'bot',
    rating TINYINT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id),
    INDEX idx_tenant_status (tenant_id, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    sender_type VARCHAR(20) NOT NULL,
    sender_id BIGINT DEFAULT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversation(id),
    INDEX idx_conv (conversation_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subscription (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    order_no VARCHAR(32) NOT NULL UNIQUE,
    plan VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id)
) ENGINE=InnoDB;

INSERT IGNORE INTO tenant (name, code, plan, max_agents, max_knowledge, max_conversations) VALUES
('Demo Company', 'demo', 'pro', 10, 1000, 5000);