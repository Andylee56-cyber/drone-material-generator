from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT / "data" / "raw" / "images"
COCO_JSON = ROOT / "data" / "processed" / "annotations_coco.json"
CLASSES = ["person","people","bicycle","car","van","truck","tricycle","awning-tricycle","bus","motor","others"]
