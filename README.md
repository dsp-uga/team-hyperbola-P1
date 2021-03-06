# Malware Classification
## Team-Hyperbola 
Team hyperbola is the team that built models to predict the Malwares for the <a href = https://www.kaggle.com/c/malware-classification/> Microsoft Malware Classification Challenge</a>. This project is done over the course of three weeks for the CSCI 8360 Data Science Practicum at University of Georgia during Spring 2019.
## Introduction to Problem:
The each instance of Malwares belong to one among the 9 classes of Malware categories
<ul><li><i>Ramnit</i></li>
<li><i>Lollipop</i></li>
<li><i>Kelihos_ver3</i></li>
<li><i>Vundo</i></li>
<li><i>Simda</i></li>
<li><i>Tracur</i></li>
<li><i>Kelihos_verl</i></li>
<li><i>Obfuscator.ACY</i></li>  
<li><i>Gatak</i></li></ul>

The data consists of 8421 instances of Malware in training set and and the features are to be extracted from byte files consists of hexadecimal data or asm files consisting of assembly language files or both. The crux of the problem is to build the models that can predict the malwares on about 2700 instances of testing data.

## Approach to problem:
The project is done using the Random Forest, Naive Bayes and Logistic Regression Models. Attempts were also made to build Convolutional Neural Networks and Custom Naive Bayes Models which were succesful to small_parts of data. The steps followed in doing this project are
1) Data Preprocessing:
   The byte files are selected to extract the features and the line id from the byte code is removed and remaining data is converted into lowercase after adding label to corresponding byte file. The words like '??','00' and 'CC' are dropped from dataset as they are most repeated words across the documents or instances of Malware.
2) Models Used:
   The models like Logistic Regression, Naive Bayes, Random Forest, Custom Naive Bayes and CNN are implemented where as the latter two are succesful on the small datasets, and are in development for the large datasets. The Logistic Regression gave the best accuracy of 94.96 on big data.

## Platform:
The Logistic Regression, Naive Bayes and RandomForest are built using Pyspark on GCP cluster with the specifications as following.
<ul><li><i>1 master node with 4 CPU's and 15 gb memory</i></li>
<li><i>4 worker nodes with 16 CPU's and 104 gb memory</i></li></ul>

Each of the models can be tested using `spark-submit [model].py -arguments ` on the GCP cluster. The arguments given are `-d=big/small for selecting dataset on which models are to be constructed` and `-h for help`.

## Future Scope:
<ul><li>
The features are to be extracted from the `.asm` files and integrate them with features from `.byte` files
   </li>
   <li> The Custom Naive Bayes and CNN are to be extended to perform on large dataset and study the performance of these classifiers in comparison to the attempted classifiers</li>
</ul>

## Credits:
<ul> <li><a href= "https://github.com/Anirudh-Kakarlapudi">Anirudh Kumar Maurya Kakarlpudi</a></li>
<li><a href = "https://github.com/a-farahani">Abolfazl Farahani</a></li>
<li><a href ="https://github.com/ng04111uga" > Narinder S Ghumman</a></li></ul>

see the <a href="https://github.com/dsp-uga/team-hyperbola-p1/blob/contibutor/Contributors.md">Contributors</a> for more information.

## License:
This project is licensed under the MIT License - see the <a href="https://github.com/dsp-uga/team-hyperbola-p1/blob/master/LICENSE">LICENSE</a> file for the details.
