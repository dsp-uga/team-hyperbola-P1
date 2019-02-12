"""
				Module: Main.py				Project: 1				Course: Data Science Practicum
				Author: Narinder Singh		Date: 10-Feb-2018		Semester: Spring'19

The main script to submit to spark.
"""

from argparse import ArgumentParser
from pyspark.context import SparkContext


import Utilities

from NaiveBayes import NaiveBayes


if __name__ == '__main__':
	# Parse command line arguments
	parser = ArgumentParser("Naive Bayes Document Classifier")
	parser.add_argument("-d", "--data", help = "Data source directory containing documents to learn from.", required = True)
  	parser.add_argument("-l", "--labels", help = "Path to file containing learning labels as (filename, label) per line. ", required = True)
  	parser.add_argument("-p", "--pdata", help = "Data source directory containing documents to predict on.", required = True)
  	parser.add_argument("-n", "--gramsize", help = "The n in n-gram.")
  	parser.add_argument("-a", "--alpha", help = "The additive smoothing parameter.")
  	parser.add_argument("-r", "--results", help = "Path to file containing expected labels for pdata in (filename, label) format.")
  	parser.add_argument("-o", "--outfile", help = "The outfile to write predictions to.")
	args = parser.parse_args()
	
	# Get spark context and set console output to be succinct
	sc = SparkContext.getOrCreate()
	sc.setLogLevel("ERROR")

	# Retrieve gram size and compute the vocabulary size fromt it.
	n = int(args.gramsize) or 1
	vsize = 16**(2*n)
	
	# Alpha - The smoothing parameter
	alpha = float(args.alpha) or 1.0

	# New Naive Bayes documment classifier
	classifier = NaiveBayes(args.data, args.labels)

	# Set classifier to ignore irrelevant (non-feature) words
	filter = lambda word: word not in ['??', '00'] and len(word) == 2
	classifier.setWordFilter(filter)
	
	# Set smoothing parameters and gram size
	classifier.setSmoothingParameters(alpha, vsize)
	classifier.setN(n)
	
	# Learn!
	classifier.learn()
	
	# Predict (and save predictions to outfile, if passed)
	predictions = classifier.predict(args.pdata, outfile = args.outfile).collectAsMap()

	# Compute accuracy from results, if provided
	if args.results:
		explabels = Utilities.readKeyValueCSV(args.results)
		matches = Utilities.matchDictionaries(predictions, explabels)
		total = float(Utilities.dlen(args.pdata))
		accuracy = matches/total

		print "Matches: ", matches
		print "Total: ", total
		print "Accuracy: ", accuracy


