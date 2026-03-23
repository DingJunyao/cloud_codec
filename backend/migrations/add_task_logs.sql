-- 任务日志表迁移脚本
-- 用于存储转码任务的持久化日志

-- =====================================================
-- SQLite 版本
-- =====================================================
-- 如果表已存在且类型不对，先删除
DROP TABLE IF EXISTS task_logs;

CREATE TABLE IF NOT EXISTS task_logs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    log_type VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_task_logs_task_id ON task_logs(task_id);
CREATE INDEX IF NOT EXISTS ix_task_logs_task_id_created_at ON task_logs(task_id, created_at);

-- =====================================================
-- MySQL 版本
-- =====================================================
-- DROP TABLE IF EXISTS task_logs;
-- CREATE TABLE IF NOT EXISTS task_logs (
--     id CHAR(36) PRIMARY KEY,
--     task_id CHAR(36) NOT NULL,
--     log_type VARCHAR(20) NOT NULL DEFAULT 'info',
--     message TEXT NOT NULL,
--     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
--     INDEX ix_task_logs_task_id (task_id),
--     INDEX ix_task_logs_task_id_created_at (task_id, created_at)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- PostgreSQL 版本
-- =====================================================
-- DROP TABLE IF EXISTS task_logs;
-- CREATE TABLE IF NOT EXISTS task_logs (
--     id UUID PRIMARY KEY,
--     task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
--     log_type VARCHAR(20) NOT NULL DEFAULT 'info',
--     message TEXT NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
-- );
-- CREATE INDEX IF NOT EXISTS ix_task_logs_task_id ON task_logs(task_id);
-- CREATE INDEX IF NOT EXISTS ix_task_logs_task_id_created_at ON task_logs(task_id, created_at);
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = CURRENT_TIMESTAMP;
--     RETURN NEW;
-- END;
-- $$ language 'plpgsql';
-- CREATE OR REPLACE TRIGGER update_task_logs_updated_at BEFORE UPDATE ON task_logs
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
