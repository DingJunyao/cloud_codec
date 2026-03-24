-- 添加用户组新字段
-- 执行时间: 2026-03-23

-- 添加最大存储空间字段
ALTER TABLE user_groups ADD COLUMN max_storage BIGINT;

-- 添加允许的预设ID列表字段
ALTER TABLE user_groups ADD COLUMN allowed_preset_ids JSON;

-- 添加默认预设ID字段
ALTER TABLE user_groups ADD COLUMN default_preset_id VARCHAR(36);

-- 添加API访问权限字段（默认为FALSE）
ALTER TABLE user_groups ADD COLUMN api_access_enabled BOOLEAN NOT NULL DEFAULT 0;

-- 添加邮件通知字段（默认为FALSE）
ALTER TABLE user_groups ADD COLUMN email_enabled BOOLEAN NOT NULL DEFAULT 0;
