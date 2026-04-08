from sensor_msgs.msg import PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header, String
from common.models import PerceptionSnapshot, PointCloudData
class PublisherFactory:
    @staticmethod
    def snapshot_to_string(snapshot: PerceptionSnapshot) -> String:
        msg = String(); msg.data = snapshot.model_dump_json(); return msg
    @staticmethod
    def point_cloud_to_msg(cloud: PointCloudData, frame_id: str='map') -> PointCloud2:
        header = Header(); header.frame_id = frame_id
        fields = [PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1), PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1), PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1)]
        return point_cloud2.create_cloud(header, fields, [(float(x), float(y), float(z)) for x,y,z in cloud.points])
