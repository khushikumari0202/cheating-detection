import cv2
import yaml
from datetime import datetime
from detection.face_detection import FaceDetector
from detection.eye_tracking import EyeTracker
from detection.mouth_detection import MouthMonitor
from detection.object_detection import ObjectDetector
from detection.multi_face import MultiFaceDetector
from detection.audio_detection import AudioMonitor
from utils.video_utils import VideoRecorder
from utils.screen_capture import ScreenRecorder
from utils.logging import AlertLogger
from utils.alert_system import AlertSystem
from utils.violation_logger import ViolationLogger
from utils.screenshot_utils import ViolationCapturer
from reporting.report_generator import ReportGenerator

import os
import tempfile
import time
import pdfkit  # Ensure wkhtmltopdf installed


def load_config():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, "config", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def display_detection_results(frame, results):
    y_offset = 30
    line_height = 30

    status_items = [
        f"Face: {'Present' if results['face_present'] else 'Absent'}",
        f"Gaze: {results['gaze_direction']}",
        f"Eyes: {'Open' if results['eye_ratio'] > 0.25 else 'Closed'}",
        f"Mouth: {'Moving' if results['mouth_moving'] else 'Still'}"
    ]

    alert_items = []
    if results['multiple_faces']:
        alert_items.append("Multiple Faces Detected!")
    if results['objects_detected']:
        alert_items.append("Suspicious Object Detected!")

    for item in status_items:
        cv2.putText(frame, item, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += line_height

    for item in alert_items:
        cv2.putText(frame, item, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y_offset += line_height

    cv2.putText(frame, results['timestamp'],
                (frame.shape[1] - 250, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def main():
    config = load_config()
    alert_logger = AlertLogger(config)
    alert_system = AlertSystem(config)
    violation_capturer = ViolationCapturer(config)
    violation_logger = ViolationLogger(config)
    report_generator = ReportGenerator(config)

    # Configure wkhtmltopdf path for PDF reports
    pdf_config = pdfkit.configuration(wkhtmltopdf=r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")

    student_info = {
        'id': 'STUDENT_001',
        'name': 'John Doe',
        'exam': 'Final Examination',
        'course': 'Computer Science 101'
    }

    # Initialize recorders
    video_recorder = VideoRecorder(config)
    screen_recorder = ScreenRecorder(config)

    # Initialize audio monitor
    audio_monitor = AudioMonitor(config)
    audio_monitor.alert_system = alert_system
    audio_monitor.alert_logger = alert_logger

    if config['detection']['audio_monitoring']:
        audio_monitor.start()

    try:
        if config['screen']['recording']:
            screen_recorder.start_recording()

        # Initialize detectors
        detectors = [
            FaceDetector(config),
            EyeTracker(config),
            MouthMonitor(config),
            MultiFaceDetector(config),
            ObjectDetector(config),
        ]

        for detector in detectors:
            if hasattr(detector, 'set_alert_logger'):
                detector.set_alert_logger(alert_logger)

        video_recorder.start_recording()
        cap = cv2.VideoCapture(config['video']['source'])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['video']['resolution'][0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['video']['resolution'][1])

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize frame for face detection to speed up
            frame_small = cv2.resize(frame, (320, 320))

            results = {
                'face_present': detectors[0].detect_face(frame_small),
                'gaze_direction': 'Center',
                'eye_ratio': 0.3,
                'mouth_moving': False,
                'multiple_faces': False,
                'objects_detected': False,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Run other detectors every frame (or you can skip every few frames)
            results['gaze_direction'], results['eye_ratio'] = detectors[1].track_eyes(frame_small)
            results['mouth_moving'] = detectors[2].monitor_mouth(frame_small)
            results['multiple_faces'] = detectors[3].detect_multiple_faces(frame_small)
            results['objects_detected'] = detectors[4].detect_objects(frame_small)

            # Handle violations
            violations_to_check = [
                ('FACE_DISAPPEARED', not results['face_present']),
                ('MULTIPLE_FACES', results['multiple_faces']),
                ('OBJECT_DETECTED', results['objects_detected']),
                ('MOUTH_MOVING', results['mouth_moving']),
            ]

            for violation_type, condition in violations_to_check:
                if condition:
                    # Speak alert safely with temp file
                    tts_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                    alert_system.speak_alert(violation_type)
                    tts_file.close()

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    violation_image = violation_capturer.capture_violation(frame, violation_type, timestamp)
                    violation_logger.log_violation(violation_type, timestamp,
                                                   {'duration': '5+ seconds', 'frame': results})
                    break  # Only handle one violation per frame

            display_detection_results(frame, results)
            video_recorder.record_frame(frame)
            cv2.imshow('Exam Proctoring', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            frame_count += 1

    finally:
        violations = violation_logger.get_violations()
        report_path = report_generator.generate_report(student_info, violations, pdf_config)
        print(f"Report generated: {report_path}")

        if config['screen']['recording']:
            screen_data = screen_recorder.stop_recording()
            print(f"Screen recording saved: {screen_data['filename']}")

        video_data = video_recorder.stop_recording()
        print(f"Webcam recording saved: {video_data['filename']}")

        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
