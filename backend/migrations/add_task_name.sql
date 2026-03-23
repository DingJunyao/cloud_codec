-- 任务表添加 name 字段
-- 任务日志表迁移脚本（修复类型问题）

-- =====================================================
-- SQLite 版本
-- =====================================================

-- 1. 给 tasks 表添加 name 字段
ALTER TABLE tasks ADD COLUMN name VARCHAR(200) NOT NULL DEFAULT '';

-- 2. 删除旧的 task_logs 表（如果存在类型不对）
DROP TABLE IF EXISTS task_logs;

-- 3. 重新创建 task_logs 表
CREATE TABLE task_logs (
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
-- ALTER TABLE tasks ADD COLUMN name VARCHAR(200) NOT NULL DEFAULT '' AFTER user_id;
-- DROP TABLE IF EXISTS task_logs;
-- CREATE TABLE task_logs (
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
-- ALTER TABLE tasks ADD COLUMN name VARCHAR(200) NOT NULL DEFAULT '';
-- DROP TABLE IF EXISTS task_logs;
-- CREATE TABLE task_logs (
--     id UUID PRIMARY KEY,
--     task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
--     log_type VARCHAR(20) NOT NULL DEFAULT 'info',
--     message TEXT NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
-- );
-- CREATE INDEX ix_task_logs_task_id ON task_logs(task_id);
-- CREATE INDEX ix_task_logs_task_id_created_at ON task_logs(task_id, created_at);
