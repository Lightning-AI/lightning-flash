# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from functools import partial
from typing import Any, Callable, Dict, Hashable, Optional, Sequence, Tuple, TYPE_CHECKING

from flash.core.data.data_module import DataModule
from flash.core.data.io.input import DataKeys, InputFormat
from flash.core.data.io.input_transform import InputTransform
from flash.core.integrations.fiftyone.utils import FiftyOneLabelUtilities
from flash.core.integrations.icevision.data import IceVisionInput
from flash.core.integrations.icevision.transforms import default_transforms
from flash.core.utilities.imports import _FIFTYONE_AVAILABLE, _ICEVISION_AVAILABLE, lazy_import, requires
from flash.core.utilities.stages import RunningStage

SampleCollection = None
if _FIFTYONE_AVAILABLE:
    fol = lazy_import("fiftyone.core.labels")
    if TYPE_CHECKING:
        from fiftyone.core.collections import SampleCollection
else:
    foc, fol = None, None

if _ICEVISION_AVAILABLE:
    from icevision.core import BBox, ClassMap, IsCrowdsRecordComponent, ObjectDetectionRecord
    from icevision.data import SingleSplitSplitter
    from icevision.parsers import COCOBBoxParser, Parser, VIABBoxParser, VOCBBoxParser
    from icevision.utils import ImgSize
else:
    COCOBBoxParser = object
    VIABBoxParser = object
    VOCBBoxParser = object
    Parser = object


class FiftyOneParser(Parser):
    def __init__(self, data, class_map, label_field, iscrowd):
        template_record = ObjectDetectionRecord()
        template_record.add_component(IsCrowdsRecordComponent())
        super().__init__(template_record=template_record)

        data = data
        label_field = label_field
        iscrowd = iscrowd

        self.data = []
        self.class_map = class_map

        for fp, w, h, sample_labs, sample_boxes, sample_iscrowd in zip(
            data.values("filepath"),
            data.values("metadata.width"),
            data.values("metadata.height"),
            data.values(label_field + ".detections.label"),
            data.values(label_field + ".detections.bounding_box"),
            data.values(label_field + ".detections." + iscrowd),
        ):
            for lab, box, iscrowd in zip(sample_labs, sample_boxes, sample_iscrowd):
                self.data.append((fp, w, h, lab, box, iscrowd))

    def __iter__(self) -> Any:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def record_id(self, o) -> Hashable:
        return o[0]

    def parse_fields(self, o, record, is_new):
        fp, w, h, lab, box, iscrowd = o

        if iscrowd is None:
            iscrowd = 0

        if is_new:
            record.set_filepath(fp)
            record.set_img_size(ImgSize(width=w, height=h))
            record.detection.set_class_map(self.class_map)

        box = self._reformat_bbox(*box, w, h)

        record.detection.add_bboxes([BBox.from_xyxy(*box)])
        record.detection.add_labels([lab])
        record.detection.add_iscrowds([iscrowd])

    @staticmethod
    def _reformat_bbox(xmin, ymin, box_w, box_h, img_w, img_h):
        xmin *= img_w
        ymin *= img_h
        box_w *= img_w
        box_h *= img_h
        xmax = xmin + box_w
        ymax = ymin + box_h
        output_bbox = [xmin, ymin, xmax, ymax]
        return output_bbox


class ObjectDetectionFiftyOneInput(IceVisionInput):
    @requires("fiftyone")
    def load_data(
        self,
        sample_collection: SampleCollection,
        label_field: str = "ground_truth",
        iscrowd: str = "iscrowd",
    ) -> Sequence[Dict[str, Any]]:
        label_utilities = FiftyOneLabelUtilities(label_field, fol.Detections)
        label_utilities.validate(sample_collection)
        classes = label_utilities.get_classes(sample_collection)
        class_map = ClassMap(classes)
        self.num_classes = len(class_map)

        parser = FiftyOneParser(sample_collection, class_map, label_field, iscrowd)
        records = parser.parse(data_splitter=SingleSplitSplitter())
        return [{DataKeys.INPUT: record} for record in records[0]]

    @staticmethod
    @requires("fiftyone")
    def predict_load_data(sample_collection: SampleCollection) -> Sequence[Dict[str, Any]]:
        return [{DataKeys.INPUT: f} for f in sample_collection.values("filepath")]


class ObjectDetectionInputTransform(InputTransform):
    def __init__(
        self,
        train_transform: Optional[Dict[str, Callable]] = None,
        val_transform: Optional[Dict[str, Callable]] = None,
        test_transform: Optional[Dict[str, Callable]] = None,
        predict_transform: Optional[Dict[str, Callable]] = None,
        image_size: Tuple[int, int] = (128, 128),
        parser: Optional[Callable] = None,
        **_kwargs: Any,
    ):
        self.image_size = image_size

        super().__init__(
            train_transform=train_transform,
            val_transform=val_transform,
            test_transform=test_transform,
            predict_transform=predict_transform,
            inputs={
                "coco": partial(IceVisionInput, parser=COCOBBoxParser),
                "via": partial(IceVisionInput, parser=VIABBoxParser),
                "voc": partial(IceVisionInput, parser=VOCBBoxParser),
                InputFormat.FILES: IceVisionInput,
                InputFormat.FOLDERS: partial(IceVisionInput, parser=parser),
                InputFormat.FIFTYONE: ObjectDetectionFiftyOneInput,
            },
            default_input=InputFormat.FILES,
        )

        self._default_collate = self._identity

    def get_state_dict(self) -> Dict[str, Any]:
        return {**self.transforms}

    @classmethod
    def load_state_dict(cls, state_dict: Dict[str, Any], strict: bool = False):
        return cls(**state_dict)

    def default_transforms(self) -> Optional[Dict[str, Callable]]:
        return default_transforms(self.image_size)

    def train_default_transforms(self) -> Optional[Dict[str, Callable]]:
        return default_transforms(self.image_size)


class ObjectDetectionData(DataModule):

    input_transform_cls = ObjectDetectionInputTransform

    @classmethod
    def from_coco(
        cls,
        train_folder: Optional[str] = None,
        train_ann_file: Optional[str] = None,
        val_folder: Optional[str] = None,
        val_ann_file: Optional[str] = None,
        test_folder: Optional[str] = None,
        test_ann_file: Optional[str] = None,
        predict_folder: Optional[str] = None,
        train_transform: Optional[Dict[str, Callable]] = None,
        val_transform: Optional[Dict[str, Callable]] = None,
        test_transform: Optional[Dict[str, Callable]] = None,
        predict_transform: Optional[Dict[str, Callable]] = None,
        image_size: Tuple[int, int] = (128, 128),
        **data_module_kwargs: Any,
    ) -> "ObjectDetectionData":
        """Creates a :class:`~flash.image.detection.data.ObjectDetectionData` object from the given data folders
        and annotation files in the COCO format.

        Args:
            train_folder: The folder containing the train data.
            train_ann_file: The COCO format annotation file.
            val_folder: The folder containing the validation data.
            val_ann_file: The COCO format annotation file.
            test_folder: The folder containing the test data.
            test_ann_file: The COCO format annotation file.
            predict_folder: The folder containing the predict data.
            train_transform: The dictionary of transforms to use during training which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            val_transform: The dictionary of transforms to use during validation which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            test_transform: The dictionary of transforms to use during testing which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            predict_transform: The dictionary of transforms to use during predicting which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            image_size: The size to resize images (and their bounding boxes) to.
        """
        return cls(
            IceVisionInput(RunningStage.TRAINING, train_folder, train_ann_file, COCOBBoxParser),
            IceVisionInput(RunningStage.VALIDATING, val_folder, val_ann_file, COCOBBoxParser),
            IceVisionInput(RunningStage.TESTING, test_folder, test_ann_file, COCOBBoxParser),
            IceVisionInput(RunningStage.PREDICTING, predict_folder),
            input_transform=cls.input_transform_cls(
                train_transform,
                val_transform,
                test_transform,
                predict_transform,
                image_size=image_size,
            ),
            **data_module_kwargs,
        )

    @classmethod
    def from_voc(
        cls,
        train_folder: Optional[str] = None,
        train_ann_file: Optional[str] = None,
        val_folder: Optional[str] = None,
        val_ann_file: Optional[str] = None,
        test_folder: Optional[str] = None,
        test_ann_file: Optional[str] = None,
        predict_folder: Optional[str] = None,
        train_transform: Optional[Dict[str, Callable]] = None,
        val_transform: Optional[Dict[str, Callable]] = None,
        test_transform: Optional[Dict[str, Callable]] = None,
        predict_transform: Optional[Dict[str, Callable]] = None,
        image_size: Tuple[int, int] = (128, 128),
        **data_module_kwargs: Any,
    ) -> "ObjectDetectionData":
        """Creates a :class:`~flash.image.detection.data.ObjectDetectionData` object from the given data folders
        and annotation files in the VOC format.

        Args:
            train_folder: The folder containing the train data.
            train_ann_file: The COCO format annotation file.
            val_folder: The folder containing the validation data.
            val_ann_file: The COCO format annotation file.
            test_folder: The folder containing the test data.
            test_ann_file: The COCO format annotation file.
            predict_folder: The folder containing the predict data.
            train_transform: The dictionary of transforms to use during training which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            val_transform: The dictionary of transforms to use during validation which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            test_transform: The dictionary of transforms to use during testing which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            predict_transform: The dictionary of transforms to use during predicting which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            image_size: The size to resize images (and their bounding boxes) to.
        """
        return cls(
            IceVisionInput(RunningStage.TRAINING, train_folder, train_ann_file, VOCBBoxParser),
            IceVisionInput(RunningStage.VALIDATING, val_folder, val_ann_file, VOCBBoxParser),
            IceVisionInput(RunningStage.TESTING, test_folder, test_ann_file, VOCBBoxParser),
            IceVisionInput(RunningStage.PREDICTING, predict_folder),
            input_transform=cls.input_transform_cls(
                train_transform,
                val_transform,
                test_transform,
                predict_transform,
                image_size=image_size,
            ),
            **data_module_kwargs,
        )

    @classmethod
    def from_via(
        cls,
        train_folder: Optional[str] = None,
        train_ann_file: Optional[str] = None,
        val_folder: Optional[str] = None,
        val_ann_file: Optional[str] = None,
        test_folder: Optional[str] = None,
        test_ann_file: Optional[str] = None,
        predict_folder: Optional[str] = None,
        train_transform: Optional[Dict[str, Callable]] = None,
        val_transform: Optional[Dict[str, Callable]] = None,
        test_transform: Optional[Dict[str, Callable]] = None,
        predict_transform: Optional[Dict[str, Callable]] = None,
        image_size: Tuple[int, int] = (128, 128),
        **data_module_kwargs: Any,
    ) -> "ObjectDetectionData":
        """Creates a :class:`~flash.image.detection.data.ObjectDetectionData` object from the given data folders
        and annotation files in the VIA format.

        Args:
            train_folder: The folder containing the train data.
            train_ann_file: The COCO format annotation file.
            val_folder: The folder containing the validation data.
            val_ann_file: The COCO format annotation file.
            test_folder: The folder containing the test data.
            test_ann_file: The COCO format annotation file.
            predict_folder: The folder containing the predict data.
            train_transform: The dictionary of transforms to use during training which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            val_transform: The dictionary of transforms to use during validation which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            test_transform: The dictionary of transforms to use during testing which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            predict_transform: The dictionary of transforms to use during predicting which maps
                :class:`~flash.core.data.io.input_transform.InputTransform` hook names to callable transforms.
            image_size: The size to resize images (and their bounding boxes) to.
        """
        return cls(
            IceVisionInput(RunningStage.TRAINING, train_folder, train_ann_file, VIABBoxParser),
            IceVisionInput(RunningStage.VALIDATING, val_folder, val_ann_file, VIABBoxParser),
            IceVisionInput(RunningStage.TESTING, test_folder, test_ann_file, VIABBoxParser),
            IceVisionInput(RunningStage.PREDICTING, predict_folder),
            input_transform=cls.input_transform_cls(
                train_transform,
                val_transform,
                test_transform,
                predict_transform,
                image_size=image_size,
            ),
            **data_module_kwargs,
        )
