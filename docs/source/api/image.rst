###########
flash.image
###########

.. contents::
    :depth: 1
    :local:
    :backlinks: top

.. currentmodule:: flash.image

Classification
______________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~classification.model.ImageClassifier
    ~classification.data.ImageClassificationFiftyOneInput
    ~classification.data.ImageClassificationData
    ~classification.input_transform.ImageClassificationInputTransform

    classification.data.MatplotlibVisualization

Object Detection
________________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~detection.model.ObjectDetector
    ~detection.data.ObjectDetectionData

    detection.input.FiftyOneParser
    detection.input.ObjectDetectionFiftyOneInput
    detection.output.FiftyOneDetectionLabelsOutput

Keypoint Detection
__________________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~keypoint_detection.model.KeypointDetector
    ~keypoint_detection.data.KeypointDetectionData


Instance Segmentation
_____________________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~instance_segmentation.model.InstanceSegmentation
    ~instance_segmentation.data.InstanceSegmentationData

Embedding
_________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~embedding.model.ImageEmbedder

Segmentation
____________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~segmentation.model.SemanticSegmentation
    ~segmentation.data.SemanticSegmentationData
    ~segmentation.input_transform.SemanticSegmentationInputTransform

    segmentation.data.SegmentationMatplotlibVisualization
    segmentation.input.SemanticSegmentationInput
    segmentation.input.SemanticSegmentationFilesInput
    segmentation.input.SemanticSegmentationFolderInput
    segmentation.input.SemanticSegmentationNumpyInput
    segmentation.input.SemanticSegmentationTensorInput
    segmentation.input.SemanticSegmentationFiftyOneInput
    segmentation.model.SemanticSegmentationOutputTransform
    segmentation.output.FiftyOneSegmentationLabelsOutput
    segmentation.output.SegmentationLabelsOutput

.. autosummary::
    :toctree: generated/
    :nosignatures:

    segmentation.input_transform.prepare_target

Style Transfer
______________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~style_transfer.model.StyleTransfer
    ~style_transfer.data.StyleTransferData
    ~style_transfer.input_transform.StyleTransferInputTransform

.. autosummary::
    :toctree: generated/
    :nosignatures:

    ~style_transfer.utils.raise_not_supported

flash.image.data
________________

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: classtemplate.rst

    ~data.ImageDeserializer
    ~data.ImageNumpyInput
    ~data.ImageTensorInput
