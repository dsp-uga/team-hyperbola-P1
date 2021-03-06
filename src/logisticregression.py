from pyspark.sql import SparkSession
from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext
from pyspark.sql import functions as fn
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import HashingTF, RegexTokenizer, IDF, NGram
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.sql.types import *
from pyspark.ml import Pipeline
import requests
import re
import argparse
sc = SparkContext.getOrCreate()
spark = SparkSession(sc)


def dataclean(dataframe):
    '''
    Takes the argument as a dataframe and adds the text from byte files and
    converts them into lower and line id is removed as it is redundant.
    Several User defined functions are created in the process.
    Args:
        dataframe:
            -The dataframe should consist of the columns,'filename'
            and 'givenorder'

        DataFrame['Filename': string, given_order: bigint,
                  'text_full': string,'text without line id': string,
                  'text': string] for big dataset

        DataFrame['Filename': string, given_order: bigint,
                  'text_full': string,'text without line id': string,
                  'text': string, 'label': string]  for small dataset
    '''
    byte_path = 'https://storage.googleapis.com/uga-dsp/project1/data/bytes/'
    remove_id = fn.udf(lambda x: re.sub('\\w{3,20}', '', x))
    text_lower = fn.udf(lambda x: x.lower())
    get_byte_file = fn.udf(lambda x: requests.get(byte_path+x+'.bytes').text)
    data_df = dataframe.withColumnRenamed('value', 'Filename')\
        .repartition(96)\
        .withColumn('text_full', get_byte_file('Filename'))\
        .withColumn('text without line id', remove_id('text_full'))\
        .withColumn('text', text_lower('text without line id'))
    return data_df


def addlabel(X_datadf, y_datadf):
    '''
    Takes the argument as a dataframe and adds  the text from byte files an
    converts them into lower and line id is removed as it is redundant.
    Several User defined functions are created in the process.
    Args:
        dataframe:
            -The dataframe should consist of the columns,'filename'
            and 'label'
    Returns:
        DataFrame['value: string, given_order: bigint, 'label': string,
        'id': bigint]

    '''
    X_data_id = X_datadf.withColumn('id', fn.monotonically_increasing_id())
    y_data_id = y_datadf.withColumn('id', fn.monotonically_increasing_id())\
        .withColumnRenamed('value', 'label')
    df_joined = X_data_id\
        .join(y_data_id, X_data_id.id == y_data_id.id, "left")\
        .drop('id')
    return df_joined


def LR_Model(train_dataframe, test_dataframe):
    '''
    Takes the argument as a train_dataframe, test_dataframe implements the
    pipeline of RegexTokenizer,    NGrams =3 , HashingTF, IDF and
    LogisticRegression and predicts the label based on features of
    test_dataframe.

    The Pattern RegexTokenizer is set to "\\W|\b(00|CC)\b" because it removes
    all nonwords that is extra spaces or punctuations, '??', '00' and 'CC' are
    removed as these are most repeated words and accuracy is significantly
    improved.
    Args:
        dataframe:
            -The train_dataframe should consist of the columns, 'label'
            and 'text'.
            -The test_dataframe should consist of the column 'text'.
    Returns:
        DataFrame['prediction': double, given_order: bigint, label: string]
        iff data read initially is a small dataset
        else DataFrame['prediction': double, given_order: bigint]
        data read initially is a big dataset
    '''
    train_dataframe = train_dataframe.repartition(96)\
        .withColumn('label', train_dataframe['label'].cast(IntegerType()))
    regexTokenizer = RegexTokenizer(inputCol="text", outputCol="words",
                                    pattern="\\W|\b(00|CC)\b")
    ngram = NGram(n=3, inputCol="words", outputCol="ngrams")
    hashingTF = HashingTF(inputCol="ngrams", outputCol="TF")
    idf = IDF(inputCol="TF", outputCol="features")
    lr = LogisticRegression(maxIter=20, regParam=0.001)
    pipeline = Pipeline(stages=[regexTokenizer, ngram, hashingTF, idf, lr])
    model = pipeline.fit(train_dataframe)
    predictions_df = model.transform(test_dataframe)
    return predictions_df\
        .drop('rawfeatures', 'n_grams', 'TF', 'text', 'words', 'features')


def get_accuracy(dataframe):
    '''
    Takes the argument as a dataframe and evaluates the columns 'label' and
    'prediction' Using MulticlassClassificationEvaluator. Both 'label' and
    'prediction' are to be of numeric datatype. If not, those are converted
    into numeric datatype.
    Args:
        dataframe:
            -The dataframe should consist of the columns, 'label' and
            'prediction'.

    Returns:
        Prints the accuracy of the test set.
    '''
    # Convertion of 'label' Column into Double Type
    dataframe = dataframe.withColumn('label',
                                     dataframe['label'].cast(DoubleType()))
    evaluator = MulticlassClassificationEvaluator(labelCol="label",
                                                  predictionCol="prediction",
                                                  metricName="accuracy")
    accuracy = evaluator.evaluate(dataframe)
    print("Test set accuracy = " + str(accuracy))


def small_data_prediction():
    '''
    Loads the data into dataframes.
    Dataframes are then cleaned after adding byte text and label and
    then model is trained to give predictions.

    Returns:
        prints the accuracy of model on small test set
    '''

    # loading the data into dataframes
    X_train_df = spark.read\
        .text('gs://uga-dsp/project1/files/X_small_train.txt')
    y_train_df = spark.read\
        .text('gs://uga-dsp/project1/files/y_small_train.txt')
    X_test_df = spark.read\
        .text('gs://uga-dsp/project1/files/X_small_test.txt')
    y_test_df = spark.read\
        .text('gs://uga-dsp/project1/files/y_small_test.txt')
    X_test_df = X_test_df\
        .withColumn('given_order', fn.monotonically_increasing_id())
    X_train_df = X_train_df\
        .withColumn('given_order', fn.monotonically_increasing_id())
    train_data = addlabel(X_train_df, y_train_df).repartition(96)
    train_data_clean = dataclean(train_data).repartition(96)
    test_data = addlabel(X_test_df, y_test_df).repartition(96)
    test_data_clean = dataclean(test_data).repartition(96)
    predictions = LR_Model(train_data_clean, test_data_clean)
    get_accuracy(predictions)


def big_data_prediction():
    '''
    Loads the data into dataframes.
    Dataframes are then cleaned after adding byte text and label and then model
    is trained to give predictions.
    Returns:
        saves the file in the directory
    '''
    # loading the data into dataframes
    X_train_df = spark.read.text('gs://uga-dsp/project1/files/X_train.txt')
    y_train_df = spark.read.text('gs://uga-dsp/project1/files/y_train.txt')
    X_test_df = spark.read.text('gs://uga-dsp/project1/files/X_test.txt')
    X_test_df = X_test_df\
        .withColumn('given_order', fn.monotonically_increasing_id())
    X_train_df = X_train_df\
        .withColumn('given_order', fn.monotonically_increasing_id())
    train_data = addlabel(X_train_df, y_train_df).repartition(96)
    train_data_clean = dataclean(train_data).repartition(96)
    test_data_clean = dataclean(X_test_df).repartition(96)
    predictions = LR_Model(train_data_clean, test_data_clean)
    save_predictions_to_file('LogRegression', predictions)


def save_predictions_to_file(dataframe, filename):
    '''
    Takes the arguments 'dataframe' , 'filename', sorts the dataframe using
    'given_order' and saves the file with filename. Due to several repartitions
    of data, the whole data is shuffled, so does the predictions. So, the
    dataframe is sorted    using 'given_order' column which is a monotonically
    increasing id which is assigned to dataframe before repartitions.

    Args:
        dataframe:
        -The dataframe should consist of the columns 'prediction'
        and 'given_order'.

    Returns:
        Saves the file at particular location with the given filename
        and prints 'Saved!!'
    '''
    dataframe = dataframe.sort('given_order')
    dataframe = dataframe\
        .withColumn('pred_label', dataframe['prediction'].cast(IntegerType()))
    dataframe.select('pred_label')\
        .coalesce(1).write.mode('overwrite')\
        .csv('gs://team_hyperbola_p1/big_data/'+filename+'.csv')
    print('Saved')


def main():
    parser = argparse.ArgumentParser(description='Welcome to Team Hyperbola.')
    parser.add_argument("-d", '--data',
                        help="Data set to use: small or big",
                        required=True)
    args = parser.parse_args()
    print(args)

    if args.data == "small":
        small_data_prediction()
    else:
        big_data_prediction()


if __name__ == "__main__":
    main()
