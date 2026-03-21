# 常见问题

## Vite `@` 别名无法解析

**症状**:
```
Error: The following dependencies are imported but could not be resolved:
  @/stores/auth
  @/views/Login.vue
```

**原因**: 存在 `vite.config.js` 和 `vite.config.ts` 冲突，Vite 优先加载 `.js` 文件（缺少别名配置）。

**解决**:
```bash
# 删除 .js 配置文件
rm frontend/vite.config.js

# 清除 Vite 缓存
rm -rf frontend/node_modules/.vite

# 重启开发服务器
npm run dev
```

## 导入错误：BigInteger 或 Optional 未定义

**症状**:
```python
NameError: name 'BigInteger' is not defined
# 或
NameError: name 'Optional' is not defined
```

**解决**:
```python
# 添加缺失的导入
from sqlalchemy import BigInteger  # models/group.py
from typing import Optional  # models/permission.py
```

## 函数参数顺序语法错误

**症状**:
```python
SyntaxError: parameter without a default follows parameter with a default
```

**原因**: Python 要求有默认值的参数必须在无默认值的参数之后。

**解决**:
```python
# 错误
async def update_me(
    email: str | None = None,
    current_user: User = Depends(get_current_user),  # 错误位置
):
    pass

# 正确
async def update_me(
    current_user: User = Depends(get_current_user),
    email: str | None = None,
):
    pass
```

## 邮箱验证器未安装

**症状**:
```python
ImportError: email-validator is not installed
```

**解决**:
```bash
pip install email-validator
```

## CORS 错误

**症状**: 前端请求被 CORS 策略阻止。

**检查**:
1. 后端 `.env` 中的 `CORS_ORIGINS` 包含前端地址
2. 前端代理配置正确（`vite.config.ts`）

## WebSocket 连接失败

**症状**: 任务详情页无法实时更新进度。

**检查**:
1. 后端 WebSocket 路由是否注册
2. 前端 WebSocket URL 格式：`ws://localhost:8000/api/tasks/ws/{task_id}?token=xxx`
3. Token 是否有效

## 数据库迁移问题

**症状**: Alembic 检测到模型变更但无法自动生成迁移。

**解决**:
```bash
# 手动创建迁移
alembic revision -m "manual migration"

# 编辑生成的迁移文件
# 然后应用
alembic upgrade head
```

## 前端构建失败

**症状**: `npm run build` 报错。

**检查**:
1. TypeScript 类型错误：运行 `vue-tsc --noEmit` 查看
2. Vue 模板错误：检查组件 `<template>` 语法
3. 依赖版本冲突：删除 `node_modules` 和 `package-lock.json` 重新安装

## 后端导入错误：group_permissions

**症状**:
```python
ImportError: cannot import name 'group_permissions' from 'app.models.group'
```

**原因**: `group_permissions` 在 `app.models.permission` 中定义，而非 `group`。

**解决**: 修改导入：
```python
# 错误
from app.models.group import group_permissions

# 正确
from app.models.permission import group_permissions
```

## RQ Worker 无法处理任务

**症状**: 任务状态一直为 `pending`。

**检查**:
1. Redis 是否运行：`redis-cli ping`
2. RQ worker 是否启动：`rq worker app.tasks.encode --url redis://localhost:6379/0`
3. 检查 worker 日志是否有错误
