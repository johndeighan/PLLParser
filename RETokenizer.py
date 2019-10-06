# RETokenizer.py

import os, sys, re, pytest
from typing import Pattern

class RETokenizer():

	def __init__(self):
		# --- Entries are ( <tokenType>, <regexp>, <groupNum> )
		self.lTokenTypes = []

	# ------------------------------------------------------------------------

	def add(self, tokenType, regexp, groupNum=0):

		assert type(tokenType) == str
		assert tokenType != 'OTHER'
		if type(regexp) == str:
			regexp = re.compile(regexp)
		else:
			assert isinstance(regexp, Pattern)
		self.lTokenTypes.append( (tokenType, regexp, groupNum) )

	# ------------------------------------------------------------------------

	def dumpTokenDefs(self):

		print('-' * 50)
		print(' ' * 10 + 'Token Definitions')
		print('-' * 50)
		for (tokenType, regexp, groupNum) in self.lTokenTypes:
			print(f"{tokenType}: '{regexp.pattern}' (group {groupNum})")
		print('-' * 50)

	# ------------------------------------------------------------------------

	def tokens(self, line, *, skipWS=True, debug=False):

		assert type(line) == str
		if debug:
			print(f"STRING: '{line}'")
		(pos, end) = (0, len(line))
		while pos < end:
			if debug:
				print(f"pos: {pos}")
			match = None
			for (tokenType, regexp, groupNum) in self.lTokenTypes:
				match = regexp.match(line, pos)
				if match:
					matched = match[groupNum]
					if debug:
						print(f"...{tokenType}: found '{matched}'")
					matchLen = len(match[0])
					if matchLen == 0:
						raise Exception("Zero length string matched")
					pos += matchLen
					yield (tokenType, matched)
					break
				else:
					if debug:
						print(f"...{tokenType}: failed")

			if not match:
				# --- No match
				#     Get next char. If whitespace, inc pos and continue
				#     else yield as a single character token
				ch = line[pos]
				pos += 1
				if skipWS and ((ch == ' ') or (ch == '\t')):
					if debug:
						print(f"...skipping whitespace")
				else:
					if debug:
						print(f"...OTHER: found '{ch}'")
					yield ('OTHER', ch)

# ---------------------------------------------------------------------------
#                   UNIT TESTS
# ---------------------------------------------------------------------------

def test_1():

	tokzr = RETokenizer()
	lTokens = list(tokzr.tokens('abc'))
	assert lTokens == [
		('OTHER', 'a'),
		('OTHER', 'b'),
		('OTHER', 'c'),
		]

def test_2():

	tokzr = RETokenizer()
	tokzr.add('INTEGER', r'\d+')
	tokzr.add('STRING', r'"([^"]*)"', 1)
	lTokens = list(tokzr.tokens('"mystring" * 23'))
	assert lTokens == [
		('STRING', 'mystring'),
		('OTHER',   '*'),
		('INTEGER', '23'),
		]

def test_3():

	tokzr = RETokenizer()
	tokzr.add('INTEGER', r'\d+')
	tokzr.add('STRING',  r'"([^"]*)"', 1)
	lTokens = list(tokzr.tokens('"mystring" * 23', skipWS=False))
	assert lTokens == [
		('STRING', 'mystring'),
		('OTHER',  ' '),
		('OTHER',   '*'),
		('OTHER',  ' '),
		('INTEGER', '23'),
		]

def test_4():

	tokzr = RETokenizer()
	tokzr.add('INTEGER', r'\d+')
	tokzr.add('STRING',  r'"([^"]*)"', 1)
	tokzr.add('STRING',  r"'([^']*)'", 1)

	lTokens = list(tokzr.tokens('"mystring"'
                               ' + '
                               "'other'"))
	assert lTokens == [
		('STRING', 'mystring'),
		('OTHER',  '+'),
		('STRING', 'other'),
		]
