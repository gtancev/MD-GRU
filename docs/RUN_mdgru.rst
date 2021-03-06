Start script
============

.. automodule:: RUN_mdgru
    :members:
    :undoc-members:

Below is a sample start script with minimum inputs.

::

    python3 RUN_mdgru.py --datapath path/to/samplestructure --locationtraining train_data \
    --locationvalidation val_data --locationtesting test_data \
    --optionname bestsettingsever --modelname bestmodelever -w 64 64 64 -p 5 5 5 \
    -f t2.nii.gz flair.nii.gz -m mask1.nii.gz --iterations 100000 \
    --nclasses 2
    
Mandatory inputs
----------------

These are mandatory inputs for which no default values are set.

**path to folders with train/val/test data (dtype=str)**
::

    --datapath path

**name of folder with data for respective purpose (dtype=str)**
::
    
    --locationtraining foldernametrain --locationvalidation foldernameval --locationtesting foldernametest

**name of options/settings (dtype=str)**
::

    --optionname bestoptionsever

**name of model (dtype=str)**
::
    
    --modelname bestmodelever

**subvolume size (dtype=int) of shape (1, n_dims)**
::
    
    -w 64 64 64

**padding size (dtype=int) of shape (1, n_dims)**
::
    
    -p 5 5 5

**sequences to include (dtype=str)**
::
    
    -f t2.nii flair.nii
    
**masks to include (dtype=str)**
::
    
    -m mask1.nii

**iterations of training to perform (dtype=int); only possible if --epochs 1**
::
    
    --interations 100000

**number of classes (dtype=int)**
::

    --nclasses 2

Optional inputs
---------------

These are optional inputs for which the default values (listed in the commands below) can be changed manually. In the data loader module, you can learn about additional optional data augmentation methods.

**epochs to perform (dtype=int); does not work together with iterations**
::
    
    --epochs 1

**number of threads in data collection for data prefetching (dtype=int)**
::
    
    --num_threads 3
    
**use non-threaded data collection (dtype=bool)**
::
    
    --nonthreaded

**use PyTorch version (dtype=bool)**
::
    
    --use_pytorch

**set GPU IDs for usage, e.g. using GPUs with ID 0 (in total using 1 GPU) (dtype=int)**

::
    
    --gpu 0
    
**use only CPU (dtype=bool)**

::
    
    --only_cpu

**fraction of GPU memory to use (dtype=float) in [0,1]**
::    
    
    --gpubound 1.0
    

**probability for dropout (dtype=float) in [0,1]**
::  

    --dropout_rate 0.5

**use batch normalization (dtype=bool)**
::  

    --add_e_bn False
    
**use skip connections/residual learning; add a residual connection around a MDGRU block (dtype=bool)**
::  

    --resmdgru False

**perform only training without testing (dtype=bool)**
::  

    --only_train
    
**perform only testing without training, make sure to add a checkpoint (dtype=bool)**
::  

    --only_test --ckpt path/to/checkpoint/file
    
**application of dice loss to label i, by default turned off (dtype=int)**
::
    
    --dice_loss_label 0 1
    
**weights for dice loss, if label(s) are provided (dtype=float)**
::
    
    --dice_loss_weight 0.0
    
**weights for dice loss, automatized instead of manual (dtype=bool)**
::

    --dice_autoweighted # weights the label dices with the squared inverse gold standard area/volume - specify which labels with dice_loss_label, sum(dice_loss_weight) is used as a weighting between crossentropy and diceloss
    --dice_generalized # total intersections of all labels over total sums of all labels, instead of linearly combined class dices
    --dice_cc # dice loss for binary segmentation per true component
