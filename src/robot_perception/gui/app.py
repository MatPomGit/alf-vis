from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from common.ros_runtime import SharedRosContext
from common.utils import load_config
from common.versioning import get_app_metadata


class App:
    """Minimalne GUI do uruchamiania programów oraz podglądu stanu maszyny stanów."""

    def __init__(self, root: tk.Tk) -> None:
        # Importy ROS2 dopiero tutaj, bo GUI samo w sobie nie powinno wysypywać się
        # podczas importu modułu, jeśli użytkownik tylko analizuje kod.
        from perception.ros2_node import PerceptionRosNode
        from perception.state_machine import RobotPerceptionStateMachine
        from slam.ros2_node import SlamRosNode
        from slam.slam_runtime import SlamRuntime

        self.PerceptionRosNode = PerceptionRosNode
        self.RobotPerceptionStateMachine = RobotPerceptionStateMachine
        self.SlamRosNode = SlamRosNode
        self.SlamRuntime = SlamRuntime

        self.root = root
        self.app_meta = get_app_metadata()
        self.app_version = self.app_meta["version"]
        self.app_author = self.app_meta["author"]
        self.root.title(
            f"Robot Perception Control Panel v{self.app_version} ({self.app_author})",
        )
        self.root.geometry("1100x750")

        self.config = load_config("config/settings.yaml")
        self.perception_machine = None
        self.perception_node = None
        self.slam_runtime = None
        self.slam_node = None
        self.running_perception = False
        self.running_slam = False

        SharedRosContext.ensure_initialized()
        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Źródło kamer:").pack(side=tk.LEFT)
        self.source_var = tk.StringVar(value="rgbd")
        ttk.Combobox(
            top,
            textvariable=self.source_var,
            values=["rgbd", "rgb"],
            width=10,
            state="readonly",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            top,
            text="Uruchom percepcję",
            command=self.start_perception,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Zatrzymaj percepcję",
            command=self.stop_perception,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Uruchom SLAM bridge",
            command=self.start_slam,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Zatrzymaj SLAM bridge",
            command=self.stop_slam,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Wykonaj jeden krok FSM",
            command=self.step_once,
        ).pack(side=tk.LEFT, padx=5)

        middle = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        middle.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(middle)
        right = ttk.Frame(middle)
        middle.add(left, weight=1)
        middle.add(right, weight=1)

        ttk.Label(left, text="Podgląd maszyny stanów").pack(anchor=tk.W)
        self.state_text = scrolledtext.ScrolledText(left, wrap=tk.WORD, height=30)
        self.state_text.pack(fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Parametry uruchamiania modułów").pack(anchor=tk.W)
        self.modules_text = scrolledtext.ScrolledText(right, wrap=tk.WORD, height=30)
        self.modules_text.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(
            value=f"GUI gotowe. Wersja: {self.app_version}. Autor: {self.app_author}",
        )
        ttk.Label(self.root, textvariable=self.status_var).pack(fill=tk.X, padx=10, pady=(0, 10))

    def _ensure_perception(self) -> None:
        if self.perception_machine is None:
            self.perception_node = self.PerceptionRosNode(self.config)
            self.perception_machine = self.RobotPerceptionStateMachine(
                self.config,
                self.perception_node,
                selected_source=self.source_var.get(),
            )

    def _ensure_slam(self) -> None:
        if self.slam_runtime is None:
            self.slam_node = self.SlamRosNode(self.config)
            self.slam_runtime = self.SlamRuntime(self.config, self.slam_node)

    def refresh_debug(self) -> None:
        if self.perception_machine is not None:
            debug = self.perception_machine.get_debug_view()
            self.state_text.delete("1.0", tk.END)
            self.state_text.insert(tk.END, json.dumps(debug, indent=2, ensure_ascii=False))

            self.modules_text.delete("1.0", tk.END)
            self.modules_text.insert(
                tk.END,
                json.dumps(
                    self.perception_machine.last_module_inputs,
                    indent=2,
                    ensure_ascii=False,
                ),
            )

        self.root.after(500, self.refresh_debug)

    def step_once(self) -> None:
        import rclpy

        self._ensure_perception()
        self.perception_machine.run_once()
        rclpy.spin_once(self.perception_node, timeout_sec=0.01)
        self.status_var.set("Wykonano jeden krok maszyny stanów.")

    def _perception_loop(self) -> None:
        import rclpy

        while (
            self.running_perception
            and self.perception_machine is not None
            and self.perception_node is not None
        ):
            self.perception_machine.run_once()
            rclpy.spin_once(self.perception_node, timeout_sec=0.01)

    def _slam_loop(self) -> None:
        import rclpy

        while self.running_slam and self.slam_runtime is not None and self.slam_node is not None:
            rclpy.spin_once(self.slam_node, timeout_sec=0.05)
            self.slam_runtime.step()

    def start_perception(self) -> None:
        self._ensure_perception()
        if not self.running_perception:
            self.running_perception = True
            threading.Thread(target=self._perception_loop, daemon=True).start()
            self.status_var.set("Uruchomiono percepcję.")

    def stop_perception(self) -> None:
        self.running_perception = False
        self.status_var.set("Zatrzymano percepcję.")

    def start_slam(self) -> None:
        self._ensure_slam()
        if not self.running_slam:
            self.running_slam = True
            threading.Thread(target=self._slam_loop, daemon=True).start()
            self.status_var.set("Uruchomiono SLAM bridge.")

    def stop_slam(self) -> None:
        self.running_slam = False
        self.status_var.set("Zatrzymano SLAM bridge.")

    def shutdown(self) -> None:
        self.running_perception = False
        self.running_slam = False

        if self.perception_machine is not None:
            self.perception_machine.shutdown()
        if self.perception_node is not None:
            self.perception_node.destroy_node()
        if self.slam_node is not None:
            self.slam_node.destroy_node()

        SharedRosContext.shutdown()


def main() -> None:
    root = tk.Tk()
    app = App(root)
    app.refresh_debug()

    def on_close() -> None:
        app.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
