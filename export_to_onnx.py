"""
Quick script to export your YOLO model to ONNX format
Run this ONCE before using the ONNX DirectML script
"""

from ultralytics import YOLO

print("Loading YOLO model...")
model = YOLO('best.pt')

print("Exporting to ONNX format...")
model.export(format='onnx', imgsz=640, simplify=True)

print("\nExport complete! You can now use onnx_directml_targeting.py")
print("Make sure to install: pip install onnxruntime-directml")
