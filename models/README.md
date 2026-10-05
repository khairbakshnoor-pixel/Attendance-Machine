Run `python scripts/download_models.py` from the project root. It downloads the
2023mar YuNet and 2021dec SFace ONNX files from the official OpenCV Zoo repository
and checks the SHA-256 values against the published Git LFS object identifiers.
The binaries are intentionally excluded from version control.

Model sources and licenses (review before redistribution):
- https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
- https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface
