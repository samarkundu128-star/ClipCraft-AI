"""Async subprocess execution layer handling execution, timeouts, and cancellation."""

import asyncio
import os
import signal
import time
import logging
from typing import List, Optional, Callable, Dict, Any
from app.media.exceptions import FFmpegProcessError, FFmpegTimeoutError, JobCancelledError

logger = logging.getLogger(__name__)


class AsyncSubprocessEngine:
    """Safely executes sub-processes with signal boundaries and cancellation tracking."""

    @staticmethod
    async def run_command(
        cmd: List[str],
        timeout: float,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancellation_event: Optional[asyncio.Event] = None,
    ) -> str:
        """Executes an FFmpeg command with progress tracking, timeouts, and process group containment."""
        logger.debug("Executing command: %s", " ".join(cmd))
        
        # Windows/Unix process isolation setup
        kwargs = {}
        if os.name == "posix":
            kwargs["preexec_fn"] = os.setsid
        elif os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

        process = await asyncio.create_subprocess_exec(
            cmd[0],
            *cmd[1:],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs
        )

        stderr_lines: List[str] = []
        start_time = time.time()

        async def read_stderr():
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                stderr_lines.append(decoded)
                
                # Simple progress parser logic looking for key=value pairs from -progress pipe
                if on_progress and "=" in decoded:
                    parts = decoded.split("=", 1)
                    if len(parts) == 2:
                        key, value = parts[0].strip(), parts[1].strip()
                        if key in ("out_time_us", "progress", "frame", "fps"):
                            on_progress({key: value})

        stderr_task = asyncio.create_task(read_stderr())

        try:
            while process.returncode is None:
                if cancellation_event and cancellation_event.is_set():
                    await AsyncSubprocessEngine._kill_process_group(process)
                    raise JobCancelledError("Media processing job was explicitly cancelled.")

                elapsed = time.time() - start_time
                if elapsed > timeout:
                    await AsyncSubprocessEngine._kill_process_group(process)
                    raise FFmpegTimeoutError(f"Process timed out after {timeout} seconds.")

                try:
                    await asyncio.wait_for(process.wait(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

            await stderr_task

            if process.returncode != 0:
                full_err = "\n".join(stderr_lines[-30:])  # Tail 30 lines
                raise FFmpegProcessError(
                    f"FFmpeg command failed with code {process.returncode}",
                    return_code=process.returncode,
                    stderr=full_err
                )

            return "\n".join(stderr_lines)

        except Exception:
            if process.returncode is None:
                await AsyncSubprocessEngine._kill_process_group(process)
            raise

    @staticmethod
    async def _kill_process_group(process: asyncio.subprocess.Process):
        """Terminates process and child processes across OS implementations."""
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                await asyncio.sleep(0.5)
                if process.returncode is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                process.terminate()
                await asyncio.sleep(0.5)
                if process.returncode is None:
                    process.kill()
        except ProcessLookupError:
            pass  # Process finished before signal sent
