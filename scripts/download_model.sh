#!/bin/bash

# Create models directory if it doesn't exist
mkdir -p models

# Download YuNet model from OpenCV Zoo
echo "Downloading YuNet face detection model..."
wget -O models/yunet.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

# Verify download
if [ -f models/yunet.onnx ]; then
    FILE_SIZE=$(stat -c%s models/yunet.onnx)
    echo "✓ Download complete!"
    echo "✓ Model size: $(numfmt --to=iec-i --suffix=B $FILE_SIZE)"
    
    if [ $FILE_SIZE -lt 200000 ]; then
        echo "⚠ Warning: File seems too small. Download may have failed."
        exit 1
    fi
else
    echo "✗ Download failed!"
    exit 1
fi

echo "✓ YuNet model ready at models/yunet.onnx"
