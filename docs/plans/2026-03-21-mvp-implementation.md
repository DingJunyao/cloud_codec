# MVP 实施计划

> 创建日期：2026-03-21
> 状态：待实施

## 一、当前完成状态

### 已完成

| 模块 | 功能 | 状态 |
|------|------|------|
| 后端 | 用户认证（登录/注册/JWT） | ✅ |
| 后端 | 用户/用户组/权限模型 | ✅ |
| 后端 | 任务模型及基础 API | ✅ |
| 后端 | 预设模型及基础 API | ✅ |
| 后端 | 文件上传/下载 API | ✅ |
| 后端 | WebSocket 框架 | ✅ |
| 后端 | RQ 任务队列框架 | ✅ |
| 后端 | 存储抽象层 | ✅ |
| 前端 | 登录/注册页面 | ✅ |
| 前端 | 任务列表/创建/详情页面 | ✅ |
| 前端 | 预设列表页面（框架） | ✅ |
| 前端 | 路由守卫 | ✅ |

### 待完成

| 模块 | 功能 | 优先级 |
|------|------|--------|
| 后端 | FFmpeg 实际转码 | 🔴 关键 |
| 后端 | 硬件加速检测 | 🔴 关键 |
| 后端 | 进度解析 + 实时推送 | 🔴 关键 |
| 后端 | 用户预设 API（CRUD + 克隆） | 🟡 重要 |
| 后端 | 系统预设初始化 | 🟡 重要 |
| 后端 | 管理员 API | 🟡 重要 |
| 前端 | 转码配置表单组件 | 🟡 重要 |
| 前端 | 预设选择器（含克隆保存） | 🟡 重要 |
| 前端 | 任务进度优化 | 🟡 重要 |
| 前端 | 日志查看组件 | 🟡 重要 |
| 前端 | 管理员界面 | 🟡 重要 |
| 前端 | 预设管理页面 | 🟢 次要 |

---

## 二、转码配置 Schema

### 数据结构

```json
{
  "video": {
    "codec": "h264",
    "codec_options": {
      "preset": "medium",
      "crf": 23,
      "profile": "high",
      "level": "4.1"
    },
    "resolution": {
      "mode": "auto",
      "width": null,
      "height": 1080,
      "keep_aspect": true
    },
    "fps": null,
    "hw_accel": "auto"
  },
  "audio": {
    "codec": "aac",
    "bitrate": "128k",
    "channels": 2,
    "sample_rate": 48000
  },
  "container": "mp4",
  "filters": [],
  "custom_params": ""
}
```

### 参数说明

#### 视频参数

| 参数 | 类型 | 说明 | 可选值 |
|------|------|------|--------|
| codec | string | 视频编解码器 | h264, h265, vp9, av1 |
| codec_options.preset | string | 编码预设 | ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow |
| codec_options.crf | int | 质量因子 | 0-51（H.264/H.265）|
| codec_options.profile | string | 编码配置 | baseline, main, high |
| codec_options.level | string | 编码级别 | 3.0, 3.1, 4.0, 4.1, 5.0, 5.1 |
| resolution.mode | string | 分辨率模式 | auto, custom, scale |
| resolution.width | int | 宽度 | null 或正整数 |
| resolution.height | int | 高度 | null 或正整数 |
| resolution.keep_aspect | bool | 保持宽高比 | true, false |
| fps | int | 帧率 | null（保持原始）或正整数 |
| hw_accel | string | 硬件加速 | auto, none, nvenc, qsv, vaapi, videotoolbox, amf |

#### 音频参数

| 参数 | 类型 | 说明 | 可选值 |
|------|------|------|--------|
| codec | string | 音频编解码器 | aac, mp3, opus, ac3, copy |
| bitrate | string | 码率 | 64k, 96k, 128k, 192k, 256k, 320k |
| channels | int | 声道数 | 1, 2, 6 |
| sample_rate | int | 采样率 | 22050, 44100, 48000 |

#### 容器和滤镜

| 参数 | 类型 | 说明 |
|------|------|------|
| container | string | 容器格式（mp4, mkv, webm） |
| filters | array | 滤镜链数组 |
| custom_params | string | 自定义 FFmpeg 参数 |

---

## 三、预设系统设计

### 独立快照原则

- 预设之间无继承关系
- 克隆操作仅复制当前状态
- 系统预设更新不影响个人预设
- 任务创建时配置复制到任务记录

### 权限规则

| 预设类型 | 查看权限 | 修改权限 | 删除权限 |
|----------|----------|----------|----------|
| 系统预设 | 所有用户 | 仅管理员 | 仅管理员 |
| 个人预设 | 仅创建者 | 仅创建者 | 仅创建者 |

### 系统内置预设（6个）

| 名称 | 视频编码 | 音频编码 | 分辨率 | 用途 |
|------|----------|----------|--------|------|
| 通用兼容 | H.264 | AAC | 原始 | 最大兼容性 |
| Web 优化 | H.264 | AAC | 1080p | 网页播放 |
| 移动设备 | H.264 | AAC | 720p | 手机平板 |
| 压缩存储 | H.265 | AAC | 原始 | 节省空间 |
| 快速转码 | H.264 | AAC | 原始 | 速度优先 |
| 4K 优化 | H.265 | AAC | 2160p | 4K 视频 |

---

## 四、任务清单

### 后端任务

#### B1: 硬件加速检测服务

**文件**: `backend/app/services/hw_accel.py`

**功能**:
- 启动时检测可用硬件加速方案
- 检测 NVENC、QSV、VAAPI、VideoToolbox、AMF
- 提供编解码器映射（软件编码器 → 硬件编码器）
- 缓存检测结果

**接口**:
```python
class HardwareAccelService:
    def detect_available() -> list[str]
    def get_encoder(codec: str, hw_accel: str) -> str
    def is_available(hw_accel: str) -> bool
```

---

#### B2: 转码配置 Schema + 验证

**文件**: `backend/app/schemas/encode_config.py`

**功能**:
- 定义 EncodeConfig Pydantic 模型
- 参数范围验证
- 编解码器兼容性检查

---

#### B3: 用户预设 API

**文件**: `backend/app/api/presets.py`（扩展）

**端点**:
```
GET    /presets/           # 列表（系统 + 个人）
POST   /presets/           # 创建个人预设
POST   /presets/{id}/clone # 克隆预设
PUT    /presets/{id}       # 更新个人预设
DELETE /presets/{id}       # 删除个人预设
```

---

#### B4: 系统预设初始化

**文件**: `backend/app/services/preset_init.py`

**功能**:
- 首次启动时检查系统预设
- 创建 6 个内置预设
- 设置默认预设

---

#### B5: FFmpeg 转码执行器

**文件**: `backend/app/services/ffmpeg/executor.py`

**功能**:
- 根据配置构建 FFmpeg 命令
- 执行转码进程
- 解析进度输出
- 支持硬件加速

**接口**:
```python
class FFmpegExecutor:
    async def execute(task_id: str, config: EncodeConfig)
    def cancel()
    def get_progress() -> dict
```

---

#### B6: 进度解析 + WebSocket 推送

**文件**: `backend/app/tasks/encode.py`（重构）

**功能**:
- 解析 FFmpeg -progress 输出
- 实时推送进度、FPS、速度、ETA
- 推送日志行
- 任务状态更新

---

#### B7: 管理员 API

**文件**: `backend/app/api/admin.py`

**端点**:
```
GET  /admin/users          # 用户列表
GET  /admin/users/{id}     # 用户详情
GET  /admin/tasks          # 所有任务
GET  /admin/stats          # 系统统计
```

---

### 前端任务

#### F1: 转码配置表单组件

**文件**: `frontend/src/components/EncodeConfigForm.vue`

**功能**:
- 视频参数表单（编解码器、质量、分辨率、帧率）
- 音频参数表单（编解码器、码率、声道、采样率）
- 容器选择
- 高级选项（硬件加速、自定义参数）
- 表单验证

---

#### F2: 预设选择器

**文件**: `frontend/src/components/PresetSelector.vue`

**功能**:
- 下拉显示系统预设 + 个人预设
- 分组显示
- 选择后填充配置表单
- "保存为预设"按钮

---

#### F3: 任务创建页面重构

**文件**: `frontend/src/views/TaskCreate.vue`（重构）

**功能**:
- 集成预设选择器
- 集成配置表单
- 文件上传
- 提交创建任务

---

#### F4: 任务进度组件优化

**文件**: `frontend/src/components/TaskProgress.vue`

**功能**:
- 实时进度条
- FPS、速度、ETA 显示
- 状态徽章

---

#### F5: 日志查看组件

**文件**: `frontend/src/components/LogViewer.vue`

**功能**:
- 实时日志流（WebSocket）
- 历史日志查看
- 日志级别高亮
- 自动滚动

---

#### F6: 管理员界面

**文件**: `frontend/src/views/admin/`（新建）

**页面**:
- `UserList.vue` - 用户列表
- `TaskMonitor.vue` - 任务监控
- `Dashboard.vue` - 系统统计

---

#### F7: 预设管理页面

**文件**: `frontend/src/views/PresetList.vue`（完善）

**功能**:
- 系统预设列表（只读）
- 个人预设 CRUD
- 预设详情查看

---

## 五、执行计划

### 阶段一：核心转码（B1-B2-B5-B6 || F1-F4）

**目标**: 实现可用的转码功能

**后端**: B1 → B2 → B5 → B6
**前端**: F1 → F4（可与后端并行）

---

### 阶段二：预设系统（B3-B4 || F2-F3-F7）

**目标**: 完善预设管理

**后端**: B3 → B4
**前端**: F2 → F3 → F7

---

### 阶段三：管理功能（B7 || F5-F6）

**目标**: 管理员功能

**后端**: B7
**前端**: F5 → F6

---

## 六、验收标准

### MVP 完成标准

- [ ] 用户可以上传视频并选择预设转码
- [ ] 用户可以自定义转码参数
- [ ] 用户可以将配置保存为个人预设
- [ ] 转码过程显示实时进度（百分比、FPS、速度、ETA）
- [ ] 转码过程可以查看实时日志
- [ ] 转码完成后可以下载结果
- [ ] 管理员可以查看所有用户和任务
- [ ] 系统自动检测并使用硬件加速
