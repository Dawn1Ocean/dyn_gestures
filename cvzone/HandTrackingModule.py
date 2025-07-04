import math
import time
import cv2
import mediapipe as mp
import numpy as np

# 导入新的 Task API 模块
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

class HandDetector:
    """
    使用新的 MediaPipe Task API 进行手部检测。
    支持 GPU Delegate 设置。
    """

    def __init__(self, staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.5, minTrackCon=0.5):
        """
        :param staticMode: 对于视频流，推荐为 False。这会影响 running_mode。
        :param maxHands: 要检测的最大手数。
        :param modelComplexity: 模型复杂度，在 Task API 中通过选择不同模型实现（例如 lite vs full）。
                                这里我们使用一个标准模型，这个参数不再直接使用。
        :param detectionCon: 最低检测置信度。
        :param minTrackCon: 最低跟踪置信度。
        """
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.minTrackCon = minTrackCon

        # 1. 设置基础选项 (BaseOptions)，这是启用 GPU 的关键
        base_options = python.BaseOptions(
            model_asset_path='cvzone/hand_landmarker.task', # 指定下载的模型文件
            delegate=python.BaseOptions.Delegate.GPU
        )

        # 2. 根据是处理静态图片还是视频流，设置不同的 running_mode
        # 您的代码是处理视频流，所以使用 VIDEO 或 LIVE_STREAM 模式
        running_mode = vision.RunningMode.VIDEO
        
        # 3. 创建 HandLandmarkerOptions
        # 注意参数名称的变化 (e.g., max_num_hands -> num_hands)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=running_mode,
            num_hands=self.maxHands,
            min_hand_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.minTrackCon
        )

        # 4. 创建检测器实例
        self.detector = vision.HandLandmarker.create_from_options(options)

        self.tipIds = [4, 8, 12, 16, 20]
        self.results = None # 用于存储最新的检测结果

    def findHands(self, img, draw=True, flipType=True):
        """
        在 BGR 图像中找到手部。
        :param img: 要查找手的图像。
        :param draw: 是否在图像上绘制结果的标志。
        :return: 包含所有手部信息的列表，以及绘制了结果的图像。
        """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape
        
        # 将 OpenCV 图像转换为 MediaPipe Image 对象
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        
        # 为视频模式生成时间戳
        timestamp_ms = int(time.time() * 1000)
        
        # 使用新的检测器进行检测
        self.results = self.detector.detect_for_video(mp_image, timestamp_ms)

        allHands = []
        if self.results.hand_landmarks:
            # 新的 API 返回结果结构不同
            for handedness, hand_landmarks in zip(self.results.handedness, self.results.hand_landmarks):
                myHand = {}
                # lmList
                mylmList = []
                xList = []
                yList = []
                for id, lm in enumerate(hand_landmarks):
                    px, py, pz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                    mylmList.append([px, py, pz])
                    xList.append(px)
                    yList.append(py)

                # bbox
                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                boxW, boxH = xmax - xmin, ymax - ymin
                bbox = xmin, ymin, boxW, boxH
                cx, cy = bbox[0] + (bbox[2] // 2), bbox[1] + (bbox[3] // 2)

                myHand["lmList"] = mylmList
                myHand["bbox"] = bbox
                myHand["center"] = (cx, cy)
                
                # 获取手的类型（左/右）
                hand_type_label = handedness[0].category_name
                if flipType:
                    myHand["type"] = "Right" if hand_type_label == "Left" else "Left"
                else:
                    myHand["type"] = hand_type_label
                
                allHands.append(myHand)

                # draw
                if draw:
                    # 使用新的绘图方式
                    self.draw_landmarks(img, hand_landmarks)
                    cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                                  (bbox[0] + bbox[2] + 20, bbox[1] + bbox[3] + 20),
                                  (255, 0, 255), 2)
                    cv2.putText(img, myHand["type"], (bbox[0] - 30, bbox[1] - 30), cv2.FONT_HERSHEY_PLAIN,
                                2, (255, 0, 255), 2)
        
        return allHands, img

    def draw_landmarks(self, rgb_image, hand_landmarks):
        """辅助函数，用于在新版 API 上绘制关键点"""
        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
        ])
        mp.solutions.drawing_utils.draw_landmarks(
            rgb_image,
            hand_landmarks_proto,
            mp.solutions.hands.HAND_CONNECTIONS,
            mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
            mp.solutions.drawing_styles.get_default_hand_connections_style())

    def fingersUp(self, myHand):
        fingers = []
        myHandType = myHand["type"]
        myLmList = myHand["lmList"]
        if myLmList: # 确保列表不为空
            # Thumb
            if myHandType == "Right":
                if myLmList[self.tipIds[0]][0] > myLmList[self.tipIds[0] - 1][0]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            else: # Left Hand
                if myLmList[self.tipIds[0]][0] < myLmList[self.tipIds[0] - 1][0]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            # 4 Fingers
            for id in range(1, 5):
                if myLmList[self.tipIds[id]][1] < myLmList[self.tipIds[id] - 2][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img=None, color=(255, 0, 255), scale=5):
        x1, y1 = p1
        x2, y2 = p2
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        info = (x1, y1, x2, y2, cx, cy)
        if img is not None:
            cv2.circle(img, (x1, y1), scale, color, cv2.FILLED)
            cv2.circle(img, (x2, y2), scale, color, cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), color, max(1, scale // 3))
            cv2.circle(img, (cx, cy), scale, color, cv2.FILLED)
        return length, info, img

def main():
    cap = cv2.VideoCapture(0)
    # 确保模型文件 'hand_landmarker.task' 存在
    try:
        detector = HandDetector(staticMode=False, maxHands=2, detectionCon=0.5, minTrackCon=0.5)
        print("HandDetector 初始化成功，正在使用 GPU...")
    except Exception as e:
        print(f"初始化 HandDetector 失败: {e}")
        print("请确保 'hand_landmarker.task' 模型文件已下载并与脚本在同一目录。")
        return

    while True:
        success, img = cap.read()
        if not success:
            break

        hands, img = detector.findHands(img, draw=True, flipType=True)

        if hands:
            hand1 = hands[0]
            lmList1 = hand1["lmList"]
            fingers1 = detector.fingersUp(hand1)
            print(f'H1 = {fingers1.count(1)}', end=" ")

            length, info, img = detector.findDistance(lmList1[8][0:2], lmList1[12][0:2], img, color=(255, 0, 255),
                                                      scale=10)
            if len(hands) == 2:
                hand2 = hands[1]
                lmList2 = hand2["lmList"]
                fingers2 = detector.fingersUp(hand2)
                print(f'H2 = {fingers2.count(1)}', end=" ")

                length, info, img = detector.findDistance(lmList1[8][0:2], lmList2[8][0:2], img, color=(255, 0, 0),
                                                          scale=10)
            print(" ")

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()