import math


COCO_BONES = ((0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9),
              (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13),
              (13, 15), (12, 14), (14, 16))


def resolve_classes(names, class_id):
    names = dict(enumerate(names)) if isinstance(names, list) else names
    if class_id >= 0:
        if class_id not in names:
            raise ValueError(f"Klasse {class_id} fehlt. Verfügbare Klassen: {names}")
        return [class_id]
    classes = [index for index, name in names.items()
               if str(name).strip().casefold() in {"person", "player", "players", "human", "enemy", "opponent"}]
    if not classes:
        raise ValueError(f"Keine Personenklasse automatisch gefunden. Klassen-ID manuell wählen: {names}")
    return classes


def regions(width, height, tiled):
    result = [(0, 0, width, height)]
    if tiled:
        tile_w, tile_h = math.ceil(width * .60), math.ceil(height * .60)
        result += [(x, y, x + tile_w, y + tile_h)
                   for y in (0, height - tile_h) for x in (0, width - tile_w)]
    return list(dict.fromkeys(result))


def iou(first, second):
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    area_a = max(0, first[2] - first[0]) * max(0, first[3] - first[1])
    area_b = max(0, second[2] - second[0]) * max(0, second[3] - second[1])
    return intersection / max(area_a + area_b - intersection, 1e-9)


def merge_detections(items, threshold=.5, limit=150):
    retained = []
    for item in sorted(items, key=lambda item: item["box"][4], reverse=True):
        box = item["box"]
        if (len(box) != 6 or not all(math.isfinite(value) for value in box)
                or box[2] <= box[0] or box[3] <= box[1]):
            continue
        if any(int(box[5]) == int(other["box"][5]) and iou(box, other["box"]) > threshold
               for other in retained):
            continue
        retained.append(item)
        if len(retained) >= limit:
            break
    return retained


def translated_detections(boxes, poses, left, top, width, height):
    items = []
    for index, raw in enumerate(boxes):
        x1, y1, x2, y2, score, class_id = raw
        box = [max(0, min(width, x1 + left)), max(0, min(height, y1 + top)),
               max(0, min(width, x2 + left)), max(0, min(height, y2 + top)), score, class_id]
        points = poses[index] if index < len(poses) and len(poses[index]) == 17 else []
        points = [[point[0] + left, point[1] + top, point[2]] for point in points if len(point) == 3]
        items.append({"box": box, "keypoints": points if len(points) == 17 else []})
    return items


def infer_frame(model, image, config, classes, device, stop, allow_pose=True):
    height, width = image.shape[:2]
    detections = []
    for left, top, right, bottom in regions(width, height, config.tiled):
        if stop():
            return []
        result = model.predict(image[top:bottom, left:right], classes=classes,
                               conf=config.confidence, imgsz=config.image_size,
                               iou=.5, max_det=150, device=device, half=device != "cpu",
                               verbose=False)[0]
        boxes = result.boxes.data.cpu().tolist() if result.boxes is not None else []
        keypoints = getattr(result, "keypoints", None)
        poses = keypoints.data.cpu().tolist() if allow_pose and keypoints is not None else []
        detections.extend(translated_detections(boxes, poses, left, top, width, height))
    return merge_detections(detections)


def attach_poses(detections, poses):
    matches = sorted(((iou(item["box"], pose["box"]), i, j)
                      for i, item in enumerate(detections) for j, pose in enumerate(poses)
                      if pose["keypoints"]), reverse=True)
    used_detections, used_poses = set(), set()
    for overlap, i, j in matches:
        if overlap < .3:
            break
        if i not in used_detections and j not in used_poses:
            detections[i]["keypoints"] = poses[j]["keypoints"]
            used_detections.add(i)
            used_poses.add(j)
    return detections


def skeleton_segments(points, threshold):
    if len(points) != 17:
        return []
    def valid(point):
        return (len(point) == 3 and all(math.isfinite(value) for value in point)
                and point[2] >= threshold and point[0] > 0 and point[1] > 0)
    return [(points[a], points[b]) for a, b in COCO_BONES if valid(points[a]) and valid(points[b])]
