"""Read-only TF2 diagnostic for the SLAM application."""
import argparse
import json
import logging
from types import SimpleNamespace

from lib_ros import MockBackend, RosClient


def pose(ros: RosClient, target: str, source: str, timeout: float) -> dict[str, object]:
    """Return original ROS translation in metres and quaternion in xyzw order."""
    transform = ros.transform(target, source, timeout=timeout)
    t = transform.transform.translation
    q = transform.transform.rotation
    return {"target": target, "source": source, "translation_m": [t.x, t.y, t.z],
            "quaternion_xyzw": [q.x, q.y, q.z, q.w]}


def self_test() -> None:
    """Check the application's independent spatial contract with a mock backend."""
    sample = SimpleNamespace(
        transform=SimpleNamespace(
            translation=SimpleNamespace(x=1.0, y=2.0, z=3.0),
            rotation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
        )
    )
    backend = MockBackend(transforms={("map", "base_link", None): sample})
    with RosClient(backend=backend) as ros:
        result = pose(ros, "map", "base_link", 0.1)
        assert result["translation_m"] == [1.0, 2.0, 3.0]
        assert result["quaternion_xyzw"] == [0.0, 0.0, 0.0, 1.0]
        assert ros.health().ready


def main() -> None:
    """Run the optional diagnostic without modifying the SLAM node."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--target", default="map")
    parser.add_argument("--source", default="base_link")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    with RosClient(node_name="alf_vis_tf_probe") as ros:
        logging.info(json.dumps(pose(ros, args.target, args.source, args.timeout)))


if __name__ == "__main__":
    main()
