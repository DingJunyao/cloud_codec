"""初始化数据库：创建默认权限和用户组"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import UserGroup, Permission


async def init_permissions():
    """初始化系统权限"""
    permissions_data = [
        ("task:create", "创建转码任务", "创建新的转码任务"),
        ("task:batch", "批量转码", "批量创建转码任务"),
        ("task:api", "自动化API访问", "使用API Key访问自动化接口"),
        ("task:view_all", "查看所有任务", "查看所有用户的转码任务"),
        ("file:upload", "上传文件", "上传视频文件"),
        ("file:local", "本地文件访问", "访问本地文件系统"),
        ("file:local_write", "本地文件写入", "写入本地文件系统"),
        ("preset:custom", "自定义预设", "创建自定义转码预设"),
        ("admin:users", "用户管理", "管理用户账号"),
        ("admin:groups", "用户组管理", "管理用户组"),
        ("admin:presets", "系统预设管理", "管理系统预设配置"),
        ("admin:system", "系统设置", "管理系统配置"),
    ]

    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Permission))
        if existing.scalars().first():
            print("权限已存在，跳过初始化")
            return

        for code, name, description in permissions_data:
            perm = Permission(code=code, name=name, description=description)
            session.add(perm)

        await session.commit()
        print(f"创建 {len(permissions_data)} 个权限")


async def init_groups():
    """初始化默认用户组"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在
        result = await session.execute(select(UserGroup))
        if result.scalars().first():
            print("用户组已存在，跳过初始化")
            return

        # 普通用户组
        normal_group = UserGroup(
            name="普通用户",
            description="默认用户组，具有基本转码功能",
            max_file_size=1073741824,  # 1GB
            result_retention_days=7,
            local_paths=None,
        )
        session.add(normal_group)

        # 等待保存以获取ID
        await session.flush()

        # 分配权限
        result = await session.execute(select(Permission))
        all_permissions = result.scalars().all()

        permission_map = {p.code: p for p in all_permissions}

        normal_permissions = [
            "task:create", "file:upload", "preset:custom"
        ]
        for code in normal_permissions:
            if code in permission_map:
                normal_group.permissions.append(permission_map[code])

        await session.commit()
        print("创建默认用户组")


async def main():
    """主函数"""
    print("开始初始化数据库...")
    await init_permissions()
    await init_groups()
    print("数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(main())
