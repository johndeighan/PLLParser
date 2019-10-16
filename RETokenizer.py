# RETokenizer.py

import os, sys, re, pytest
from typing import Pattern

from parserUtils import runningUnitTests, getVersion

__version__ = getVersion()

class RETokenizer():

	def __init__(self, skipWS=True):
		# --- Entries are ( <tokenType>, <regexp>, <groupNum> )
		self.lTokenTypes = []
		self.skipWS = skipWS

	# ------------------------------------------------------------------------

	def add(self, tokenType, regexp, groupNum=0, func=None):
		# --- func, if set, should be a function to convert the
		#     found string into whatever you want

		assert type(tokenType) == str
		assert tokenType != 'OTHER'
		if func:
			assert callable(func)
		if type(regexp) == str:
			regexp = re.compile(regexp)
		else:
			assert isinstance(regexp, Pattern)
		self.lTokenTypes.append( [tokenType, regexp, groupNum, func] )
		return self    # allow chaining

	# ------------------------------------------------------------------------

	def dumpTokenDefs(self):

		print('-' * 50)
		print(' ' * 10 + 'Token Definitions')
		print('-' * 50)
		for (tokenType, regexp, groupNum) in self.lTokenTypes:
			print(f"{tokenType}: '{regexp.pattern}' (group {groupNum})")
		print('-' * 50)

	# ------------------------------------------------------------------------

	def tokens(self, line, *, debug=False):

		assert type(line) == str
		if debug:
			print(f"STRING: '{line}'")
		(pos, end) = (0, len(line))
		while pos < end:
			if debug:
				print(f"pos: {pos}")
			match = None
			for (tokenType, regexp, groupNum, func) in self.lTokenTypes:
				match = regexp.match(line, pos)
				if match:
					matched = match[groupNum]
					if debug:
						print(f"...{tokenType}: found '{matched}'")
					matchLen = len(match[0])
					if matchLen == 0:
						raise Exception("Zero length string matched")
					pos += matchLen
					if func:
						yield [tokenType, func(matched)]
					else:
						yield [tokenType, matched]
					break
				else:
					if debug:
						print(f"...{tokenType}: match failed")

			if not match:
				# --- No match
				#     Get next char. If whitespace, inc pos and continue
				#     else yield as a single character token
				ch = line[pos]
				pos += 1
				if((ch == ' ') or (ch == '\t')) and self.skipWS:
					if debug:
						print(f"...skipping whitespace")
				else:
					if debug:
						print(f"...OTHER: found '{ch}'")
					yield ['OTHER', ch]

# ---------------------------------------------------------------------------
#                   UNIT TESTS
# ---------------------------------------------------------------------------

if runningUnitTests:

	def test_1():

		tokzr = RETokenizer()

		# --- No tokens added, so match single characters
		lTokens = list(tokzr.tokens('abc'))
		assert lTokens == [
			['OTHER', 'a'],
			['OTHER', 'b'],
			['OTHER', 'c'],
			]

		# --- No tokens added, so match single characters, skipping whitespace
		lTokens = list(tokzr.tokens('a b\tc'))
		assert lTokens == [
			['OTHER', 'a'],
			['OTHER', 'b'],
			['OTHER', 'c'],
			]

	def test_2():

		tokzr = RETokenizer(skipWS=False)

		# --- No tokens added, so match single characters,
		#     but NOT skipping whitespace
		lTokens = list(tokzr.tokens('a b\tc'))
		assert lTokens == [
			['OTHER', 'a'],
			['OTHER', ' '],
			['OTHER', 'b'],
			['OTHER', '\t'],
			['OTHER', 'c'],
			]

	def test_3():

		tokzr = RETokenizer()
		tokzr.add('INTEGER', r'\d+')
		tokzr.add('STRING', r'"([^"]*)"', 1)
		lTokens = list(tokzr.tokens('"mystring" * 23'))
		assert lTokens == [
			['STRING', 'mystring'],
			['OTHER',   '*'],
			['INTEGER', '23'],
			]

	def test_4():

		tokzr = RETokenizer(skipWS=False)
		tokzr.add('INTEGER', r'\d+')
		tokzr.add('STRING',  r'"([^"]*)"', 1)
		lTokens = list(tokzr.tokens('"mystring" * 23'))
		assert lTokens == [
			['STRING', 'mystring'],
			['OTHER',  ' '],
			['OTHER',   '*'],
			['OTHER',  ' '],
			['INTEGER', '23'],
			]

	def test_5():

		tokzr = RETokenizer()
		tokzr.add('INTEGER', r'\d+')
		tokzr.add('STRING',  r'"([^"]*)"', 1)
		tokzr.add('STRING',  r"'([^']*)'", 1)

		lTokens = list(tokzr.tokens('"mystring"'
											 ' + '
											 "'other'"))
		assert lTokens == [
			['STRING', 'mystring'],
			['OTHER',  '+'],
			['STRING', 'other'],
			]

	def test_6():

		tokzr = RETokenizer()
		tokzr.add('INTEGER', r'\d+')
		tokzr.add('STRING',  r'"([^"]*)"', 1)
		tokzr.add('STRING',  r"'([^']*)'", 1)
		tokzr.add('HEREDOC', r'<<<')
		tokzr.add('OP',      r'\+|-|\*|\/')

		lTokens = list(tokzr.tokens('<<< + 23 % 5'))
		assert lTokens == [
			['HEREDOC', '<<<'],
			['OP',  '+'],
			['INTEGER', '23'],
			['OTHER', '%'],
			['INTEGER', '5'],
			]

	def test_7():
		# --- Test converting integers to true Python integer

		tokzr = RETokenizer()
		tokzr.add('INTEGER', r'\d+', 0, int)
		tokzr.add('STRING',  r'"([^"]*)"', 1)
		tokzr.add('STRING',  r"'([^']*)'", 1)
		tokzr.add('HEREDOC', r'<<<')
		tokzr.add('OP',      r'\+|-|\*|\/')

		lTokens = list(tokzr.tokens('<<< + 23 % 5'))
		assert lTokens == [
			['HEREDOC', '<<<'],
			['OP',  '+'],
			['INTEGER', 23],
			['OTHER', '%'],
			['INTEGER', 5],
			]

	def test_8():
		# --- Test chaining calls to add

		tokzr = (RETokenizer()
			.add('INTEGER', r'\d+', 0, int)
			.add('STRING',  r'"([^"]*)"', 1)
			.add('STRING',  r"'([^']*)'", 1)
			.add('HEREDOC', r'<<<')
			.add('OP',      r'\+|-|\*|\/')
			)

		lTokens = list(tokzr.tokens('<<< + 23 % 5'))
		assert lTokens == [
			['HEREDOC', '<<<'],
			['OP',  '+'],
			['INTEGER', 23],
			['OTHER', '%'],
			['INTEGER', 5],
			]
