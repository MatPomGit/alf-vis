
# YOLO bbox -> 3D using depth
def bbox_to_3d(bbox, depth, rs):
    x1,y1,x2,y2 = bbox
    cx = (x1+x2)/2
    cy = (y1+y2)/2
    return rs.deproject(cx,cy,depth)
