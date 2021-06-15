##############
Style Transfer
##############

********
The task
********

The Neural Style Transfer Task is an optimization method which extract the style from an image and apply it another image while preserving its content.
The goal is that the output image looks like the content image, but “painted” in the style of the style reference image.

.. image:: https://raw.githubusercontent.com/pystiche/pystiche/master/docs/source/graphics/banner/banner.jpg
    :alt: style_transfer_example

Lightning Flash :class:`~flash.image.style_transfer.StyleTransfer` and
:class:`~flash.image.style_transfer.StyleTransferData` internally rely on `pystiche <https://pystiche.org>`_ as
backend.

------

***
Fit
***

First, you would have to import the :class:`~flash.image.style_transfer.StyleTransfer`
and :class:`~flash.image.style_transfer.StyleTransferData` from Flash.

.. testcode:: style_transfer

    import flash
    from flash.core.data.utils import download_data
    from flash.image.style_transfer import StyleTransfer, StyleTransferData
    import pystiche


Then, download some content images and create a :class:`~flash.image.style_transfer.StyleTransferData` DataModule.

.. testcode:: style_transfer

    download_data("https://github.com/zhiqwang/yolov5-rt-stack/releases/download/v0.3.0/coco128.zip", "data/")

    data_module = StyleTransferData.from_folders(train_folder="data/coco128/images", batch_size=4)


Select a style image and pass it to the `StyleTransfer` task.

.. testcode:: style_transfer

    style_image = pystiche.demo.images()["paint"].read(size=256)

    model = StyleTransfer(style_image)

Finally, create a Flash :class:`flash.core.trainer.Trainer` and pass it the model and datamodule.

.. testcode:: style_transfer

    trainer = flash.Trainer(max_epochs=2)
    trainer.fit(model, data_module)

.. testoutput:: style_transfer
    :hide:

    ...
