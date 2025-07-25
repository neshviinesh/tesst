import os
import cv2
import torch
import numpy as np
from PIL import Image
from collections import defaultdict
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
import torchvision.transforms as transforms
import torch.nn.functional as F

# Load models
facenet = InceptionResnetV1(pretrained='vggface2').eval()
yolo = YOLO("yolov11n-face.pt")

# Transform
transform = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5])
])

# Load known faces
known_embeddings = defaultdict(list)

for filename in os.listdir("known_faces"):
    if filename.startswith('.') or not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        continue

    name = os.path.splitext(filename)[0].rsplit('_', 1)[0]
    path = os.path.join("known_faces", filename)

    image = Image.open(path).convert('RGB')
    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        embedding = facenet(img_tensor)

    known_embeddings[name].append(embedding[0])

print(f"[INFO] Loaded known identities: {list(known_embeddings.keys())}")

def recognize_faces_yolo(frame):
    """
    Input: OpenCV BGR frame
    Output: List of tuples (x1, y1, x2, y2, name)
    """
    results = yolo(frame)
    detections = []

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            margin = 0.1
            w, h = x2 - x1, y2 - y1
            x1_adj = int(x1 + margin * w)
            y1_adj = int(y1 + margin * h)
            x2_adj = int(x2 - margin * w)
            y2_adj = int(y2 - margin * h)

            face_crop = frame[y1_adj:y2_adj, x1_adj:x2_adj]
            if face_crop.size == 0:
                continue

            face_pil = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)).resize((160, 160))
            face_tensor = transform(face_pil).unsqueeze(0)

            with torch.no_grad():
                embedding = facenet(face_tensor)

            name = "Unknown"
            best_sim = 0.0

            for person_name, embeddings in known_embeddings.items():
                for ref_embedding in embeddings:
                    sim = F.cosine_similarity(embedding, ref_embedding.unsqueeze(0)).item()
                    if sim > 0.5 and sim > best_sim:
                        name = person_name
                        best_sim = sim

            detections.append((x1, y1, x2, y2, name))

    return detections
