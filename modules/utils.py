"""
Copyright 2021 - Filippo Guerranti <filippo.guerranti@student.unisi.it>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import cv2
import numpy as np
from .cnn import *
from .dataset import *
from .segmentation import *
import tkinter as tk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime



def webcam_capture() -> (np.ndarray, str):

    # opens a camera for video capturing
    cam = cv2.VideoCapture(0)

    # creates a window
    cv2.namedWindow("SPACE: snapshot | ESC: exit")

    # initializing output
    image = None

    while True:

        # grabs, decodes and returns the next video frame
        retval, frame = cam.read()

        if not retval:
            print("Unable to grab the frame!")
            break

        # show the countinously captured frame
        cv2.imshow("SPACE: snapshot | ESC: exit", frame)

        # waits for a pressed key
        k = cv2.waitKey(delay=1)

        # if the ESC is pressed
        if k % 256 == 27:
            print("Exiting...")
            break
        
        # if the SPACE is pressed 
        elif k % 256 == 32:
            image = frame
            break

    # release the capture
    cam.release()

    # destroy the opened windows
    cv2.destroyAllWindows()

    # Saving the image 
    if image is not None:
        now = datetime.now()
        image_name = "img-{}.png".format(now.strftime("%Y%m%d-%H%M%S"))
        image_dir = "img/webcam/"
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        image_path = os.path.join(image_dir, image_name)
        cv2.imwrite(image_path, image) 

    return image, image_path



def save_image_steps(image_path, segmented):

    # segmented image
    # ------------------------
    segmented_image = segmented.segmented_img
    segmented_path = '{}-segmented.png'.format(image_path[:-4])
    segmented_image.save(segmented_path)
    print("\n\nSegmented image saved: {}".format(segmented_path))
    # ------------------------

    # boxed image
    # ------------------------
    boxed_image = segmented.boxed_img
    boxed_path = '{}-boxed.png'.format(image_path[:-4])
    boxed_image.save(boxed_path)
    print("Boxed image saved: {}".format(boxed_path))
    # ------------------------

    # extracted digits image
    # ------------------------
    digits_path = '{}-digits.png'.format(image_path[:-4])
    fig = plt.figure(figsize=(30,15))
    for i in range(len(segmented.digits)):
        image = segmented.digits[i][0]
        sp = fig.add_subplot(3, len(segmented.digits), i+1)
        plt.axis('off')
        plt.imshow(image, cmap='gray')
    plt.savefig(digits_path)
    print("Digits image saved: {}\n".format(digits_path))
    # ------------------------



def main_args_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(description='Handwritten long number recognition')

    subparsers = parser.add_subparsers(dest='mode'
                                    , help='<required> program execution mode: classify with a pre-trained model or re-train the model'
                                    , required=True)

    # create the parser for the "CLASSIFY" command 
    # ------------------------
    parser_classify = subparsers.add_parser('classify'
                                            , help='classify an input image using the pre-trained model'
                                            , description='CLASSIFY mode: classify an input image using a pre-trained model')

    image_from = parser_classify.add_mutually_exclusive_group()

    image_from.add_argument('-f', '--folder'
                            , type=str
                            , help='input image from folder, if not specified from webcam'
                            , metavar='PATH_TO_IMAGE'
                            , default=None)

    which_model = parser_classify.add_mutually_exclusive_group()

    which_model.add_argument('-a', '--augmentation'
                            , action='store_true'
                            , help='use model trained WITH data augmentation')

    which_model.add_argument('-m', '--model'
                            , type=str
                            , help='user custom model from path'
                            , metavar='PATH_TO_MODEL')

    parser_classify.add_argument('-d', '--device'
                                , type=str
                                , help='(default=cpu) device to be used for computations {cpu, cuda:0, cuda:1, ...}'
                                , default='cpu')
    # ------------------------

    # create the parser for the "TRAIN" command
    # ------------------------
    parser_train = subparsers.add_parser('train'
                                        , help='re-train the model in your machine and save it to reuse in classify phase'
                                        , description='TRAIN mode: re-train the model in your machine and save it to reuse in classify phase')
    
    parser_train.add_argument('-a', '--augmentation'
                            , action='store_true'
                            , help='set data-augmentation procedure ON (RandomRotation and RandomResizedCrop)')
    
    parser_train.add_argument('-s', '--splits'
                            , nargs=2
                            , type=float
                            , help='(default=[0.7,0.3]) proportions for the dataset split into training and validation set'
                            , default=[0.7,0.3]
                            , metavar=('TRAIN', 'VAL'))
    
    parser_train.add_argument('-b', '--batch_size'
                            , type=int
                            , help='(default=64) mini-batch size'
                            , default=64)
    
    parser_train.add_argument('-e', '--epochs'
                            , type=int
                            , help='(default=10) number of training epochs'
                            , default=10)
    
    parser_train.add_argument('-l', '--learning_rate'
                            , type=float
                            , help='(default=10) learning rate'
                            , default=0.001)
    
    parser_train.add_argument('-w', '--num_workers'
                            , type=int
                            , help='(default=3) number of workers'
                            , default=3)

    parser_train.add_argument('-d', '--device'
                            , type=str
                            , help='(default=cpu) device to be used for computations {cpu, cuda:0, cuda:1, ...}'
                            , default='cpu')
    # ------------------------
    
    # create the parser for the "EVAL" command
    # ------------------------
    parser_eval = subparsers.add_parser('eval'
                                        , help='evaluate the model accuracy on the test set of MNIST'
                                        , description='EVAL mode: evaluate the model accuracy on the test set of MNIST')

    parser_eval.add_argument('model'
                            , type=str
                            , help='<required> path to the model to be evaluated'
                            , metavar='PATH_TO_MODEL')

    parser_eval.add_argument('-d', '--device'
                            , type=str
                            , help='(default=cpu) device to be used for computations {cpu, cuda:0, cuda:1, ...}'
                            , default='cpu')
    # ------------------------
    
    args = parser.parse_args()

    return args



def classify(image_path, augmentation, model, device):
    
    # load an image from user folder
    # ------------------------
    if image_path is not None:
        if os.path.exists(image_path) and os.path.isfile(image_path):
            image = image_path
        else:
            raise ValueError("Wrong image path.")
    # ------------------------
    # take a webcam image
    # ------------------------
    else:
        image, image_path = webcam_capture()
        if image is None:
            raise RuntimeError("Unable to take webcam image. When window appears press SPACE to take a snapshot.")
    # ------------------------

    # create a new classifier
    # ------------------------
    classifier = CNN(device)
    # ------------------------

    # load user model
    # ------------------------
    if model is not None:
        classifier.load(model)
    else:
        # load pre-trained model
        # ------------------------
        if augmentation:
            classifier.load('models/CNN-128b-60e-0.0001l-a.pth')
        else:
            classifier.load('models/CNN-128b-60e-0.0001l.pth')
        # ------------------------
    # ------------------------

    # graph-based segmentation and digits extraction
    # ------------------------
    segmented = GraphBasedSegmentation(image)
    segmented.segment(
                      k=4500
                    , min_size=100
                    , preprocessing=True)

    segmented.generate_image()
    segmented.draw_boxes()
    segmented.extract_digits()

    save_image_steps(image_path, segmented)
    # ------------------------

    output = classifier.classify(segmented.digits)
    output = ''.join(str(digit.item()) for digit in output)
    print('\n\nThe recognize number is: {}\n\n'.format(output))



def train(augmentation, splits, batch_size, epochs, lr, num_workers, device):

    # creating a new classifier
    # ------------------------
    classifier = CNN(
                  data_augmentation=augmentation
                , device=device)
    # ------------------------

    print("\n\nDataset preparation ...\n")

    basedir = os.path.dirname(sys._getframe(1).f_globals['__file__'])
    dataset_folder = os.path.join(basedir, 'data/')
    print("Dataset folder: {}".format(dataset_folder))

    # preparing training and validation dataset
    # ------------------------
    training_validation_set = MNIST(
                              folder=dataset_folder
                            , train=True
                            , download_dataset=True
                            , empty=False
                            )
    # ------------------------

    # preparing test dataset
    # ------------------------
    test_set = MNIST(
                  folder=dataset_folder
                , train=False
                , download_dataset=True
                , empty=False
                )
    # ------------------------

    # splitting dataset into training and validation set
    # ------------------------
    training_set, validation_set = training_validation_set.splits(
                                                  proportions=splits
                                                , shuffle=True
                                                )
    # ------------------------
  
    # setting preprocessing operations if enabled
    # ------------------------
    training_set.set_preprocess(classifier.preprocess)
    # ------------------------


    # print some statistics
    # ------------------------
    print("\n\nStatistics: training set\n")
    training_set.statistics()
    print("\n\nStatistics: validation set\n")
    validation_set.statistics()
    print("\n\nStatistics: test set\n")
    test_set.statistics()
    # ------------------------

    # defining model path (in which models will be saved)
    # ------------------------
    model_path = os.path.join(basedir, 'models/')
    # ------------------------


    # training the classifier
    # ------------------------
    print("\n\nTraining phase...\n")
    classifier.train_cnn(
                  training_set=training_set
                , validation_set=validation_set
                , batch_size=batch_size
                , lr=lr
                , epochs=epochs
                , num_workers=num_workers
                , model_path=model_path
                )
    # ------------------------
    
    # computing the performance of the final model in the prepared data splits
    # ------------------------
    print("\n\nValidation phase...\n")

    # load the best classifier model
    model_name = '{}CNN-{}b-{}e-{}l{}.pth'.format\
                    (model_path, batch_size, epochs, lr, '-a' if augmentation else '')
    classifier.load(model_name)

    training_acc = classifier.eval_cnn(training_set)
    validation_acc = classifier.eval_cnn(validation_set)
    test_acc = classifier.eval_cnn(test_set)

    print("\n\nAccuracies\n")

    print("training set:\t{:.2f}".format(training_acc))
    print("validation set:\t{:.2f}".format(validation_acc))
    print("test set:\t{:.2f}".format(test_acc))
    # ------------------------

    print("\n\nModel path: {}\n".format(model_name))



def eval(model_name, device):

    # creating a new classifier
    # ------------------------
    classifier = CNN(device=device)
    # ------------------------

    print("\n\nDataset preparation ...\n")

    basedir = os.path.dirname(sys._getframe(1).f_globals['__file__'])
    dataset_folder = os.path.join(basedir, 'data/')
    print("Dataset folder: {}".format(dataset_folder))

    # preparing test dataset
    # ------------------------
    test_set = MNIST(
                  folder=dataset_folder
                , train=False
                , download_dataset=True
                , empty=False
                )
    # ------------------------

    # computing the performance of the model
    # ------------------------
    print("\n\nEvaluation phase...\n")

    # load the classifier model
    classifier.load(model_name)

    test_acc = classifier.eval_cnn(test_set)

    print("\ntest set accuracy:\t{:.2f}\n\n".format(test_acc))
    # ------------------------