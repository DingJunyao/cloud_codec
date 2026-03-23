"""FFmpeg 转码执行器"""
import asyncio
import logging
import re
import subprocess
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.services.ffmpeg.command import build_ffmpeg_command

logger = logging.getLogger(__name__)


@dataclass
class ProgressInfo:
    """转码进度信息"""
    progress: float = 0.0
    frame: int = 0
    fps: float = 0.0
    speed: str = "0x"
    bitrate: str = ""
    time_us: int = 0
    duration: float = 0.0
    eta: int = 0


class FFmpegExecutor:
    """FFmpeg 转码执行器 - 使用同步 subprocess 以兼容 RQ worker"""

    def __init__(
        self,
        task_id: str,
        input_file: str,
        output_file: str,
        config: dict,
        ffprobe_path: str = "ffprobe",
    ):
        self.task_id = task_id
        self.input_file = input_file
        self.output_file = output_file
        self.config = config
        self.ffprobe_path = ffprobe_path

        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False
        self._progress = ProgressInfo()
        self._start_time: Optional[datetime] = None
        self._duration: float = 0.0
        self._return_code: Optional[int] = None  # FFmpeg 返回码

    def get_video_duration(self) -> float:
        """获取视频时长（秒）"""
        try:
            result = subprocess.run(
                [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", self.input_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"[{self.task_id}] 获取视频时长失败: {e}")
            return 0.0

    async def execute(
        self,
        on_progress: Optional[Callable[[ProgressInfo, asyncio.AbstractEventLoop], None]] = None,
        on_log: Optional[Callable[[str, asyncio.AbstractEventLoop], None]] = None,
    ) -> bool:
        """
        执行转码任务 - 使用同步 subprocess

        Args:
            on_progress: 进度回调，接收 ProgressInfo 和事件循环
            on_log: 日志回调，接收日志行和事件循环

        Returns:
            是否成功
        """
        if self._cancelled:
            return False

        # 获取当前事件循环，供子线程使用
        self._loop = asyncio.get_running_loop()

        # 获取视频时长
        self._duration = self.get_video_duration()
        self._progress.duration = self._duration

        # 构建命令
        cmd = build_ffmpeg_command(
            self.input_file,
            self.output_file,
            self.config,
            progress_pipe=True
        )

        logger.info(f"[{self.task_id}] 执行命令: {' '.join(cmd)}")
        self._start_time = datetime.now(timezone.utc)

        try:
            # 使用同步 subprocess 启动进程
            # start_new_session=True 确保 FFmpeg 在新会话中运行，避免与 RQ worker 信号冲突
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True
            )

            # 使用线程读取输出，传递事件循环
            progress_thread = threading.Thread(
                target=self._read_progress_sync,
                args=(on_progress, self._loop),
                daemon=True
            )
            log_thread = threading.Thread(
                target=self._read_stderr_sync,
                args=(on_log, self._loop),
                daemon=True
            )
            progress_thread.start()
            log_thread.start()

            # 等待进程结束
            return_code = self._process.wait()
            self._return_code = return_code  # 保存返回码

            # 等待线程结束
            progress_thread.join(timeout=2)
            log_thread.join(timeout=2)

            if self._cancelled:
                logger.info(f"[{self.task_id}] 任务已取消")
                return False

            if return_code == 0:
                logger.info(f"[{self.task_id}] 转码完成")
                return True
            else:
                logger.error(f"[{self.task_id}] 转码失败，返回码: {return_code}")
                return False

        except Exception as e:
            logger.error(f"[{self.task_id}] 转码异常: {e}")
            self._return_code = -1  # 异常情况
            self._terminate_sync()
            return False

    def _read_progress_sync(self, on_progress: Optional[Callable[[ProgressInfo, asyncio.AbstractEventLoop], None]], loop: asyncio.AbstractEventLoop):
        """同步读取进度输出"""
        if not self._process or not self._process.stdout:
            return

        buffer = ""
        try:
            while True:
                chunk = self._process.stdout.read(1024)
                if not chunk:
                    break

                buffer += chunk

                # 解析进度信息
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self._parse_progress_line(line)

                # 回调，传递事件循环
                if on_progress:
                    on_progress(self._progress, loop)

        except Exception as e:
            logger.debug(f"读取进度出错: {e}")

    def _read_stderr_sync(self, on_log: Optional[Callable[[str, asyncio.AbstractEventLoop], None]], loop: asyncio.AbstractEventLoop):
        """同步读取错误输出（日志）"""
        if not self._process or not self._process.stderr:
            return

        try:
            for line in self._process.stderr:
                line_str = line.strip()
                if line_str:
                    logger.debug(f"[{self.task_id}] FFmpeg: {line_str}")
                    if on_log:
                        on_log(line_str, loop)
        except Exception as e:
            logger.debug(f"读取日志出错: {e}")

    def _parse_progress_line(self, line: str):
        """解析进度行"""
        if '=' not in line:
            return

        key, value = line.split('=', 1)

        if key == 'frame':
            self._progress.frame = int(value)
        elif key == 'fps':
            self._progress.fps = float(value)
        elif key == 'speed':
            self._progress.speed = value
        elif key == 'bitrate':
            self._progress.bitrate = value
        elif key == 'out_time_us':
            try:
                us = int(value)
                self._progress.time_us = us
                if self._duration > 0:
                    seconds = us / 1_000_000
                    self._progress.progress = min(100, (seconds / self._duration) * 100)

                    if self._progress.speed and self._progress.speed != '0x':
                        speed_match = re.match(r'([\d.]+)x', self._progress.speed)
                        if speed_match:
                            speed_val = float(speed_match.group(1))
                            if speed_val > 0:
                                remaining = self._duration - seconds
                                self._progress.eta = max(0, int(remaining / speed_val))
            except ValueError:
                pass

    async def cancel(self):
        """取消转码"""
        self._cancelled = True
        self._terminate_sync()

    def _terminate_sync(self):
        """终止进程"""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            except Exception as e:
                logger.warning(f"终止进程时出错: {e}")

    @property
    def progress(self) -> ProgressInfo:
        """获取当前进度"""
        return self._progress

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._process is not None and self._process.poll() is None
