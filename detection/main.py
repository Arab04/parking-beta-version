from ultralytics import YOLO
import cv2
import cvzone
from sort.sort import *
from utils import get_car, read_license_plate, write_csv, draw_licence_plate

results = {}

mot_tracker = Sort()

# load models
coco_model = YOLO('../models/yolov8n.pt')
license_plate_detector = YOLO('../models/license_plate_detector.pt')
mask = cv2.imread("../masks/mask1.png")
# load video
cap = cv2.VideoCapture('../videos/720.mp4')

vehicles = [2, 3, 5, 7]

# read frames
frame_nmr = -1
ret = True
while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret:
        results[frame_nmr] = {}
        #image_region = cv2.bitwise_and(frame, mask)
        # detect vehicles
        detections = coco_model(frame)[0]
        detections_ = np.empty((0, 5))
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                currentArray = np.array([x1, y1, x2, y2, score])
                detections_ = np.vstack((detections_, currentArray))

        # track vehicles
        track_ids = mot_tracker.update(np.asarray(detections_))

        # detect license plates
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate
            if int(class_id) == 0:
                # assign license plate to car
                xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

                if car_id != -1:
                    # crop license plate
                    license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]

                    # draw_licence_plate(license_plate_crop)

                    # process license plate
                    license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                    _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255,
                                                                 cv2.THRESH_BINARY_INV)

                    # read license plate number
                    license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)
                    print(license_plate_text)

                    if license_plate_text is not None:
                        results[frame_nmr][car_id] = {'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                                                      'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                        'text': license_plate_text,
                                                                        'bbox_score': score,
                                                                        'text_score': license_plate_text_score}}

    cv2.imshow("license_plate", frame)
    cv2.waitKey(1)

# write results
write_csv(results, './test.csv')