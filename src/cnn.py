import pyspark
from pyspark import SparkConf, SparkContext
import matplotlib as plt
import os
import argparse
import numpy as np
import png
from PIL import Image
import scipy
import re
import binascii
import matplotlib.image as mpimg 
import matplotlib as plt
from sklearn.model_selection import train_test_split
import keras
import tensorflow as tf
from keras.utils import to_categorical
from keras.datasets import fashion_mnist
from keras.models import Sequential,Input,Model
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import LeakyReLU
from sklearn.metrics import classification_report
from keras.models import load_model
from sklearn.metrics import classification_report


#-----spark configuration-----
conf = SparkConf().setAppName("MlvClassification")
conf = (conf.setMaster('local[*]')
        .set('spark.executor.memory', '4g')
        .set('spark.driver.memory', '4G')
        .set('spark.driver.maxResultSize', '10G'))
sc = SparkContext(conf=conf)
#-----functions-------

#----assigning each filename its corresponding label----
def fname_label_assign(fnames, labels):
    filename_label_dict = {}
    for filename, label in zip(fnames.value, labels.value):
        filename_label_dict[filename] = label
    return filename_label_dict

#----making the list of words form byte files----
def pre_process(x, fname_label_dict):
    fname = x[0].split('/')[-1][:-6]
    label = int(fname_label_dict.value[fname])
    word_list = list(filter(lambda x: len(x)==2 and x!='??' and x!='00' and x!='CC', re.split('\r\n| ', x[1])))
    
    return ((fname,label), word_list)


#----making image out of byte files----
def makeImage(rdd, input_type):
    img_w = 448
    img_h = 448
    row = 0
    col = 0
    image = []
    image.append([])
    for i in rdd[1]:
        intrdd = int(i, 16)
        if col <= img_w-1:
            image[row].append(intrdd)
            col += 1
        else:
            row += 1
            col = 0
            image.append([])
            image[row].append(intrdd)
            col += 1      
    if col <= img_w-1:
        for j in range(col, img_w):
            image[row].append('0')

    #------This part save the byte files as gray scale images-----
    # image_output = Image.fromarray(np.asarray(image).astype(np.uint8))
                              
    # if input_type == 'train':
    #     imagefile = ('images/train/'+rdd[0][0]+'_'+str(rdd[0][1])+'.png')
    # else:
    #     imagefile = ('images/test/'+rdd[0][0]+'_'+str(rdd[0][1])+'.png')
    # image_output.save(imagefile) 

#----making all images the same size (640x750), reshape and normalize----    
    image_np = np.array(image).astype(np.float32)
    image_np.resize(img_w,img_h)
    image_np.reshape(img_w,img_h)
    image_np = image_np.reshape(img_w, img_h, 1)
    image_np = image_np/255
    
    new_labels = []
    
    return (image_np, int(rdd[0][1])-1)



#----loading file names and their corresponding labels-----
train_fnames = open('dataset/files/X_train.txt').read().split('\n')
train_labels = open('dataset/files/y_train.txt').read().split('\n')

test_fnames = open('dataset/files/X_small_train.txt').read().split('\n')
test_labels = open('dataset/files/y_small_train.txt').read().split('\n')

#----Broadcasting the file names and labels
train_fnames_broad = sc.broadcast(train_fnames)
train_labels_broad = sc.broadcast(train_labels)

train_fname_label_dict = fname_label_assign(train_fnames_broad, train_labels_broad)
train_fname_label_dict_broad = sc.broadcast(train_fname_label_dict)

test_fnames_broad = sc.broadcast(test_fnames)
test_labels_broad = sc.broadcast(test_labels)

test_fname_label_dict = fname_label_assign(test_fnames_broad, test_labels_broad)
test_fname_label_dict_broad = sc.broadcast(test_fname_label_dict)

train_rdd_files  = sc.wholeTextFiles("/run/media/afarahani/dataset/train").repartition(30)
test_rdd_files = sc.wholeTextFiles("dataset/bytes/train").repartition(30)

train_bag_of_docs = train_rdd_files.map(lambda x: pre_process(x, train_fname_label_dict_broad))
test_bag_of_docs = test_rdd_files.map(lambda x: pre_process(x ,test_fname_label_dict_broad))

train_rdd_image = train_bag_of_docs.map(lambda x: makeImage(x, 'train'))
test_rdd_image = test_bag_of_docs.map(lambda x: makeImage(x, 'test'))

train_x =train_rdd_image.map(lambda x: x[0])
train_rdd_image.map(lambda x: (x[0], tuple(np.array(_) for _ in zip(*x[1:]))))




train_x =train_rdd_image.map(lambda x: x[0])
test_x = test_rdd_image.map(lambda x: x[0])

train_x = np.array(train_x.collect())
test_x = np.array(test_x.collect())

train_labels = train_rdd_image.map(lambda x: x[1])
test_labels= test_rdd_image.map(lambda x: x[1])

train_labels = np.array(train_labels.collect())
test_labels = np.array(test_labels.collect())

#----Convolutional model ---------
classes = np.unique(np.array(train_labels))
nclasses = len(classes)

train_y_one_hot = to_categorical(np.array(train_labels))
test_y_one_hot = to_categorical(np.array(test_labels))

train_x,valid_x,train_label,valid_label = train_test_split(train_x, train_y_one_hot, test_size=0.2, random_state=13)

#---- convolutional neural network architecture -----

#----setting the parameters for the model----
batch_size = 64 #can be 128 or 256 which is better depending on memory
epochs = 100    #number of times that the model is trained on
alpha =0.001    #learning rate

fashion_model = Sequential()

fashion_model.add(Conv2D(64, kernel_size=(3, 3),activation='linear',padding='same',input_shape=(448,448,1)))
fashion_model.add(LeakyReLU(alpha))
fashion_model.add(MaxPooling2D((2, 2),padding='same'))
fashion_model.add(Dropout(0.25))

fashion_model.add(Conv2D(128, (3, 3), activation='linear',padding='same'))
fashion_model.add(LeakyReLU(alpha))                  
fashion_model.add(MaxPooling2D(pool_size=(2, 2),padding='same'))
fashion_model.add(Dropout(0.25))

fashion_model.add(Conv2D(256, (3, 3), activation='linear',padding='same'))
fashion_model.add(LeakyReLU(alpha))                  
fashion_model.add(MaxPooling2D(pool_size=(2, 2),padding='same'))
fashion_model.add(Dropout(0.25))

fashion_model.add(Conv2D(512, (3, 3), activation='linear',padding='same'))
fashion_model.add(LeakyReLU(alpha))                  
fashion_model.add(MaxPooling2D(pool_size=(2, 2),padding='same'))
fashion_model.add(Dropout(0.4))

fashion_model.add(Flatten())
fashion_model.add(Dense(512, activation='linear'))
fashion_model.add(LeakyReLU(alpha))           
fashion_model.add(Dropout(0.3))
fashion_model.add(Dense(nclasses, activation='softmax'))

fashion_model.compile(loss=keras.losses.categorical_crossentropy, optimizer=keras.optimizers.Adam(),metrics=['accuracy'])

fashion_train_dropout = fashion_model.fit(train_x, train_label, batch_size=batch_size,epochs=epochs,verbose=1,validation_data=(valid_x, valid_label))

fashion_model.save("fashion_model_dropout.h5py")

test_eval = fashion_model.evaluate(test_x, test_y_one_hot, verbose=1)

print('Test loss:', test_eval[0])
print('Test accuracy:', test_eval[1])

predicted_classes = fashion_model.predict(test_x)

predicted_classes = np.argmax(np.round(predicted_classes),axis=1)

print(predicted_classes.shape, test_labels.shape)

target_names = ["Class {}".format(i) for i in range(nclasses)]
print(classification_report(test_labels, predicted_classes, target_names=target_names))