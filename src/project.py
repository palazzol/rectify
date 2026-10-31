
#
#  Rectify Project File (.rct)
#
# A project file is a zip archive containing two members:
#
#   project.json - format version, original image file name, and the markers
#   image.<fmt>  - the original image file, byte for byte, e.g. image.jpeg
#
# Example project.json:
#
#   {
#     "version": 1,
#     "image_name": "board.jpg",
#     "image": "image.jpeg",
#     "markers": [ {"id": 0, "x": 123.5, "y": 456.25}, ... ]
#   }
#

import json
import os
import zipfile
from dataclasses import dataclass, field

from PySide6 import QtCore, QtGui

PROJECT_EXTENSION = '.rct'
FORMAT_VERSION = 1

_JSON_MEMBER = 'project.json'
_IMAGE_MEMBER = 'image'

@dataclass
class MarkerData:
    mid: int
    x: float
    y: float

@dataclass
class ProjectFile:
    image_name: str
    image_data: bytes
    markers: list[MarkerData] = field(default_factory=list)

    def pixmap(self) -> QtGui.QPixmap:
        # Raises ValueError if the image data can not be decoded
        pixmap = QtGui.QPixmap()
        if not pixmap.loadFromData(self.image_data):
            raise ValueError('Project image could not be decoded')
        return pixmap

    def _imageMember(self) -> str:
        # Name the member after the actual format, as the file name may not match it
        data = QtCore.QByteArray(self.image_data)
        buffer = QtCore.QBuffer(data)
        buffer.open(QtCore.QIODevice.OpenModeFlag.ReadOnly)
        imageformat = bytes(QtGui.QImageReader.imageFormat(buffer).data()).decode()
        return f'{_IMAGE_MEMBER}.{imageformat}' if imageformat else _IMAGE_MEMBER

    def save(self, path: str) -> None:
        image_member = self._imageMember()
        doc = {
            'version': FORMAT_VERSION,
            'image_name': self.image_name,
            'image': image_member,
            'markers': [{'id': m.mid, 'x': m.x, 'y': m.y} for m in self.markers],
        }

        # Write to a temporary file first, so a failed save
        # never destroys an existing project file
        tmp_path = path + '.tmp'
        try:
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr(_JSON_MEMBER, json.dumps(doc, indent=2), compress_type=zipfile.ZIP_DEFLATED)
                # Not all image formats are compressed, e.g. BMP
                zf.writestr(image_member, self.image_data, compress_type=zipfile.ZIP_DEFLATED)
            os.replace(tmp_path, path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    @classmethod
    def load(cls, path: str) -> ProjectFile:
        # Raises ValueError if the file is not a valid project file
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                doc = json.loads(zf.read(_JSON_MEMBER))
                version = doc.get('version')
                if version != FORMAT_VERSION:
                    raise ValueError(f'Unsupported project version: {version}')
                image_data = zf.read(doc['image'])
                markers = [MarkerData(int(m['id']), float(m['x']), float(m['y']))
                           for m in doc.get('markers', [])]
                image_name = str(doc.get('image_name', ''))
        except (zipfile.BadZipFile, KeyError, TypeError, json.JSONDecodeError) as e:
            raise ValueError(f'Not a valid project file: {e}') from e
        return cls(image_name, image_data, markers)
