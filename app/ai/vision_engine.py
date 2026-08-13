import cv2

class VisionEngine:
    @staticmethod
    def detect_faces(frame_path: str) -> bool:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        image = cv2.imread(frame_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0
      
