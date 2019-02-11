import pyspark
from pyspark import SparkConf, SparkContext
import matplotlib as plt
import os
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

#-----spark configuration-----
conf = SparkConf().setAppName("MlvClassification")
conf = (conf.setMaster('local[*]')
        .set('spark.executor.memory', '4G')
        .set('spark.driver.memory', '45G')
        .set('spark.driver.maxResultSize', '10G'))
sc = SparkContext(conf=conf)
#-----functions-------

#----assigning each filename its corresponding label----
def fname_label_assign(fnames, labels):
    filename_label_dict = {}
    for filename, label in zip(fnames.value, labels.value):
        filename_label_dict[filename] = label
    return filename_label_dict

#----labels should start from zero---
def label_normalize (labels):
    new_labels = []
    np_labels = np.array(labels)
    if np.amin(np_labels > 0):
    	for i in labels:
        	new_labels.append((int(i)-np.amin(np_labels)))
    return new_labels

#----making the list of words form byte files----
def pre_process(x, fname_label_dict):
    fname = x[0].split('/')[-1][:-6]
    label = int(fname_label_dict.value[fname])
    word_list = list(filter(lambda x: len(x)==2 and x!='??' and x!='00', re.split('\r\n| ', x[1])))
    
    return ((fname,label), word_list)


#----making image out of byte files----
def makeImage(rdd, input_type):
    img_w = 224
    img_h = 224
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

    # image_output = Image.fromarray(np.asarray(image).astype(np.uint8))
                              
    # if input_type == 'train':
    #     imagefile = ('images/train/'+rdd[0][0]+'.png')
    # else:
    #     imagefile = ('images/test/'+rdd[0][0]+'.png')
    # image_output.save(imagefile) 

#----making all images the same size (640x750), reshape and normalize----    
    image_sized = np.array(image).astype(np.float32)
    image_sized.resize(img_w,img_h)
    image_sized.reshape(img_w,img_h)
    image_reshaped = image_sized.reshape(img_w, img_h, 1)
    image_normalized = image_reshaped/255
    
    new_labels = []
    
    return (image_normalized, int(rdd[0][1])-1)



#----loading file names and their corresponding labels-----
train_fnames = open('dataset/files/X_small_train.txt').read().split('\n')
train_labels = open('dataset/files/y_small_train.txt').read().split('\n')

test_fnames = open('dataset/files/X_small_test.txt').read().split('\n')
test_labels = open('dataset/files/y_small_test.txt').read().split('\n')

# train_labels = label_normalize(train_labels)
# test_labels = label_normalize(test_labels)

train_fnames_broad = sc.broadcast(train_fnames)
train_labels_broad = sc.broadcast(train_labels)

train_fname_label_dict = fname_label_assign(train_fnames_broad, train_labels_broad)

train_fname_label_dict_broad = sc.broadcast(train_fname_label_dict)

test_fnames_broad = sc.broadcast(test_fnames)
test_labels_broad = sc.broadcast(test_labels)

test_fname_label_dict = fname_label_assign(test_fnames_broad, test_labels_broad)

test_fname_label_dict_broad = sc.broadcast(test_fname_label_dict)

train_rdd_files  = sc.wholeTextFiles("dataset/bytes/train")
test_rdd_files = sc.wholeTextFiles("dataset/bytes/test")

train_bag_of_docs = train_rdd_files.map(lambda x: pre_process(x, train_fname_label_dict_broad))
test_bag_of_docs = test_rdd_files.map(lambda x: pre_process(x ,test_fname_label_dict_broad))

train_rdd_image = train_bag_of_docs.map(lambda x: makeImage(x, 'train'))
test_rdd_image = test_bag_of_docs.map(lambda x: makeImage(x, 'test'))

train_x =train_rdd_image.map(lambda x: x[0])
test_x = test_rdd_image.map(lambda x: x[0])

train_x = np.array(train_x.collect())
test_x = np.array(test_x.collect())

train_labels = train_rdd_image.map(lambda x: x[1])
test_labels= test_rdd_image.map(lambda x: x[1])

train_labels = np.array(train_labels.collect())
test_labels = np.array(test_labels.collect())
#----Convolutional model ---------
#def cnn(train_labels, test_labels, train_x, train_y):

classes = np.unique(np.array(train_labels))
nclasses = len(classes)

train_y_one_hot = to_categorical(np.array(train_labels))
test_y_one_hot = to_categorical(np.array(test_labels))

train_x,valid_x,train_label,valid_label = train_test_split(train_x, train_y_one_hot, test_size=0.2, random_state=13)

#---- convolutional neural network architecture -----



config = tf.ConfigProto( device_count = {'GPU': 1 , 'CPU': 56} ) 
sess = tf.Session(config=config) 
keras.backend.set_session(sess)


batch_size = 128 #can be 128 or 256 which is better depending on memory
epochs = 40
alpha =0.001

fashion_model = Sequential()

fashion_model.add(Conv2D(64, kernel_size=(3, 3),activation='linear',padding='same',input_shape=(224,224,1)))
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
