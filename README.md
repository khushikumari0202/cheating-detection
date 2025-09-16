# cheating-detection
Here is a sample README template for the "Focus & Object Detection in Video Interviews" project to help get started:

***

# Focus & Object Detection in Video Interviews

## Project Overview

This project implements a **video proctoring system** designed to monitor candidate focus and detect unauthorized items during online interviews. The system features real-time video capture, focus detection using face and gaze tracking, and object detection for items like phones, notes, or extra devices.

***

## Features

- Real-time candidate video streaming and recording
- Focus detection based on face presence and gaze direction
- Detection of multiple faces in the frame
- Object detection for phones, books, and electronic devices
- Event logging with timestamps (focus lost, suspicious items)
- Proctoring report generation with integrity scoring
- (Optional) Backend storage of events and video logs
- Bonus: Eye closure/drowsiness detection, real-time alerts, audio background voice detection (future work)

***

## Tech Stack

- Frontend: HTML, CSS, react-webcam
- Computer Vision: MediaPipe Face Detection, TensorFlow.js Object Detection
- Backend (optional): Node.js, Express.js, MongoDB/Firebase
- Reporting: PDF/html generation using Node.js libraries

***



## Usage

- Click “Start Interview” to open webcam stream
- The system starts detecting face presence and focus status in real time
- Suspicious events are logged and displayed on screen
- (Optional) Events are stored in backend database
- Generate and download proctoring reports after interview completes

***



## Future Enhancements

- Improved accuracy with advanced gaze estimation
- Real-time audio analysis for background noise detection
- Multi-face recognition and candidate verification
- Mobile-friendly responsive design
- Real-time alerts sent to interviewers

***

## License

This project is licensed under the MIT License.

***

## Contact & Support

For questions or feedback, please open an issue or contact:

- Email: your.email@example.com
- GitHub: [yourusername](https://github.com/khushikumari0202)

***

This README provides a clear setup guide and project understanding to support initial development and testing. Would you like help writing detailed setup or code explanations next?
