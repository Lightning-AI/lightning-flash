.. _contributing_examples:

************
The Examples
************

Now you've implemented your task, it's time to add some examples showing how cool it is!
We usually provide one finetuning example in `flash_examples/finetuning <https://github.com/PyTorchLightning/lightning-flash/blob/master/flash_examples/finetuning/>`_ and one predict / inference example in `flash_examples/predict <https://github.com/PyTorchLightning/lightning-flash/blob/master/flash_examples/predict/>`_.
You can base these off of our ``template.py`` examples.
Let's take a closer look.

finetuning
==========

The finetuning example should:

#. download the data (we'll add the example to our CI later on, so choose a dataset small enough that it runs in reasonable time)
#. load the data into a :class:`~flash.core.data.data_module.DataModule`
#. create an instance of the :class:`~flash.core.model.Task`
#. create a :class:`~flash.core.trainer.Trainer`
#. call :meth:`~flash.core.trainer.Trainer.finetune` or :meth:`~flash.core.trainer.Trainer.fit` to train your model
#. save the checkpoint
#. generate predictions for a few examples *(optional)*

For our template example we don't have a pretrained backbone, so we can just call :meth:`~flash.core.trainer.Trainer.fit` rather than :meth:`~flash.core.trainer.Trainer.finetune`.
Here's the full example (`flash_examples/finetuning/template.py <https://github.com/PyTorchLightning/lightning-flash/blob/master/flash_examples/finetuning/template.py>`_):

.. literalinclude:: ../../../flash_examples/finetuning/template.py
    :language: python
    :lines: 14-

We get this output:

.. code-block::

    ['setosa', 'virginica', 'versicolor']

predict
=======

The predict example should:

#. download the data (this should be the data from the finetuning example)
#. load an instance of the :class:`~flash.core.model.Task` from a checkpoint stored on `S3` (speak with one of us about getting your checkpoint hosted)
#. generate predictions for a few examples
#. generate predictions for a whole dataset, folder, etc.

For our template example we don't have a pretrained backbone, so we can just call :meth:`~flash.core.trainer.Trainer.fit` rather than :meth:`~flash.core.trainer.Trainer.finetune`.
Here's the full example (`flash_examples/predict/template.py <https://github.com/PyTorchLightning/lightning-flash/blob/master/flash_examples/predict/template.py>`_):

.. literalinclude:: ../../../flash_examples/predict/template.py
    :language: python
    :lines: 14-

We get this output:

.. code-block::

    ['setosa', 'virginica', 'versicolor']
    [['setosa', 'setosa', 'setosa', 'setosa'], ..., ['virginica', 'virginica']]

------

Now that you've got some examples showing your awesome task in action, it's time to :ref:`write some tests! <contributing_tests>`
