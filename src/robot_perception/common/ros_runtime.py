from __future__ import annotations
import threading
import rclpy
class SharedRosContext:
    _lock = threading.Lock()
    _initialized = False
    @classmethod
    def ensure_initialized(cls) -> None:
        with cls._lock:
            if not cls._initialized:
                rclpy.init()
                cls._initialized = True
    @classmethod
    def shutdown(cls) -> None:
        with cls._lock:
            if cls._initialized:
                rclpy.shutdown()
                cls._initialized = False
