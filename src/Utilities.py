"""
				Module: Utilities.py		Project: 1				Course: Data Science Practicum
				Author: Narinder Singh		Date: 03-Feb-2018		Semester: Spring'19
					
The module contains methods and classes to make life easier.
"""

import os
import sys

class UtilitiesError(Exception): pass
class BadInputError(UtilitiesError): pass


from pyspark.context import SparkContext


class ProgressBar:
	"""
		A handrolled implementation of a progress bar. The bar displays the progress as a ratio like this: (1/360).
	"""

	def __init__(self, max = 100):
		"""
			Initialize the bar with the total number of units (scale).
		"""
		self.max = max
		self.current = 0
		print "Initiating download..... \n"

	def update(self, add = 1):
		"""
			Record progress.
		"""
		self.current += add
		self._clear()
		self._display()

	def _display(self):
		"""
			Print the completion ratio on the screen.
		"""
		print "(" + str(self.current) + "/" + str(self.max) + ")"

	def _clear(self):
		"""
			Erase the old ratio from the console.
		"""
		sys.stdout.write("\033[F")
		sys.stdout.flush()


def flen(filename):
	"""
		File LENgth computes and returns the number of lines in a file. @filename <string> is path to a file. This is an epensive method to call for the whole file is read to determine the number of lines.
		
		returns: <integer> line count
	"""
	# Read and count lines.
	with open(filename, 'r') as infile:
		return sum((1 for line in infile))


def dlen(dirname):
		"""
			This horribly named function computes the no. of (non-hidden) entries in the directory @dirname <string>.
			
			returns: <integer> line count
		"""
		contents = os.listdir(dirname)
		contents = [element for element in contents if not element.startswith(".")]
		return len(contents)
		

def readKeyValueCSV(filename):
	"""
		Reads a key-value csv file and returns the contents as a python dictionary. @filename is the path to the file.
		
		returns: file contents as <dictionary>
	"""
	# Resultant dictionary.
	result = {}
	
	# Read file and collect key-value pairs into result.
	with open(filename, "r") as infile:
		for line in infile:
			key, value = line.split(",")
			result[key.strip()] = value.strip()

	return result
	

def merge(first, second, outfile):
	"""
		The procedure merges the two text files line by line, separated by commas, into a new file. For instance, the files - A.txt and B.txt are merged to generate C.txt. All the arguments are paths to files passed as <string>s and the files to be merged must have equal number of lines.
		
			A.txt	|		B.txt	|		C.txt
		A			|	1			|	A, 1
		B			|	2			|	B, 2
		C			|	3			|	C, 3
					|				|
					
		returns: <True> on completion.
	"""
	# Make sure the files have equal number of lines.
	if not flen(first) == flen(second): raise BadInputError("The files: " + first + " and " + second + " must have equal number of lines.")

	# Read and merge.
	with open(first, 'r') as first, open(second, 'r') as second, open (outfile, 'w') as outfile:
		while True:
			try:
				# Read lines.
				a = first.next()
				b = second.next()
				# Write as: a, b
				outfile.write(a.strip() + ', ' + b.strip() + '\n')
			except StopIteration:
				break

	return True


def matchDictionaries(first, second):
	"""
		Match key value pairs in the first dictionary with the second and return the number of matches. Absence of a key in the second dictionary is counted as a mismatch and extraneous keys in the second dictionary are ignored.
	"""
	matches = 0
	for key in first:
		if key not in second: continue
		if first[key] == second[key]: matches += 1

	return matches


if __name__ == '__main__':
	pass






