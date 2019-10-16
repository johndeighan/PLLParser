# PLLParser.py

"""
parse a 'Python-like language'
"""

import sys, io, re, pytest
from more_itertools import ilen
from pprint import pprint

from parserUtils import (
		rmPrefix, reLeadWS, isAllWhiteSpace,
		traceStr, cleanup_testcode, firstWordOf)
from TreeNode import TreeNode

# --- Some pre-compiled regular expressions

hDefOptions = {
	'hereDocStr': '<<<',
	'markStr':    '*',
	'reAttr':     re.compile(r'^(\S+)\s*\=\s*(.*)$'),
	}

# ---------------------------------------------------------------------------

def parsePLL(fh, hOptions={},
                 *,
                 constructor=TreeNode,
                 debug=False):

	return PLLParser(constructor, hOptions, debug).parse(fh)

# ---------------------------------------------------------------------------

class PLLParser():

	# --- We want to compile these just once, so make them class fields
	reLine     = re.compile(r'^(\s*)')
	hDefOptions = {
		# --- These become attributes of the PLLParser object
		'hereDocStr': '<<<',
		'markStr':    '*',
		'reComment':  re.compile(r'(?<!\\)#.*$'),  # ignore escaped '#' char
		'reAttr':     re.compile(r'^(\S+)\s*\=\s*(.*)$'),
		}

	# ------------------------------------------------------------------------

	def __init__(self, constructor=TreeNode,
	                   hOptions={},
	                   debug=False):

		self.setOptions(hOptions)
		self.constructor = constructor or TreeNode
		self.debug = debug

	# ------------------------------------------------------------------------

	def setOptions(self, hOptions):

		for name in self.hDefOptions.keys():
			if name in hOptions:
				value = hOptions[name]
			else:
				value = self.hDefOptions[name]
			setattr(self, name, value)

	# ------------------------------------------------------------------------

	def parse(self, fh):
		# --- Returns (rootNode, hSubTrees)

		self.numLines = 0

		rootNode = curNode = None
		hSubTrees = {}

		curLevel = None
		debug = self.debug

		# --- Putting this in a separate variable
		#     allows us to get HEREDOC lines
		gen = self._generator(fh)
		for line in gen:
			if debug:
				print(f"LINE {self.numLines}: '{traceStr(line)}'", end='')

			(newLevel, label, marked, numHereDoc) = self.splitLine(line)

			if debug:
				print(f" [{newLevel},{numHereDoc}] '{label}'")

			# --- Extract HEREDOC strings, if any
			lHereDoc = None
			if numHereDoc > 0:
				lHereDoc = []
				try:
					text = ''
					for i in range(numHereDoc):
						hereLine = gen.send('any')
						while not isAllWhiteSpace(hereLine):
							text += hereLine
							hereLine = gen.send('any')
						lHereDoc.append(rmPrefix(text))
						numHereDoc -= 1
				except:
					raise SyntaxError("Unexpected EOF in HEREDOC string")

			# --- process first non-empty line
			if rootNode == None:
				rootNode = curNode = self.constructor(label)
				if lHereDoc:
					rootNode['lHereDoc'] = lHereDoc

				# --- This wouldn't make any sense, but in case someone does it
				if marked:
					hSubTrees[firstWordOf(label)] = curNode

				curLevel = newLevel
				if debug:
					print(f"   - root node set to '{label}'")
				continue

			diff = newLevel - curLevel

			if diff > 1:
				# --- continuation line - append to current node's label
				if debug:
					print('   - continuation')

				curNode['label'] += ' ' + label

				# --- Don't change curLevel
			elif diff == 1:
				assert curNode and isinstance(curNode, self.constructor)

				# --- Check for attributes
				if self.reAttr:
					result = self.reAttr.search(label)
					if result:
						(name, value) = (result.group(1), result.group(2))
						if 'hAttr' in curNode:
							curNode['hAttr'][name] = value
						else:
							curNode['hAttr'] = { name: value }
						continue

				# --- create new child node
				if debug:
					print(f"   - new child of {curNode.asDebugString()}")
				assert not curNode.firstChild
				curNode = self.constructor(label).makeChildOf(curNode)
				if lHereDoc:
					curNode['lHereDoc'] = lHereDoc
				if marked:
					hSubTrees[firstWordOf(label)] = curNode
				curLevel += 1

			elif diff < 0:    # i.e. newLevel < curLevel
				# --- Move up -diff levels, then create sibling node
				if debug:
					n = -diff
					desc = 'level' if n==1 else 'levels'
					print(f'   - go up {n} {desc}')
				while (curLevel > newLevel):
					curLevel -= 1
					curNode = curNode.parent
					assert curNode
				curNode = self.constructor(label).makeSiblingOf(curNode)
				if lHereDoc:
					curNode['lHereDoc'] = lHereDoc
				if marked:
					hSubTrees[firstWordOf(label)] = curNode
			elif diff == 0:
				# --- create new sibling node
				if debug:
					print(f"   - new sibling of {curNode.asDebugString()}")
				assert not curNode.nextSibling
				curNode = self.constructor(label).makeSiblingOf(curNode)
				if lHereDoc:
					curNode['lHereDoc'] = lHereDoc
				if marked:
					hSubTrees[firstWordOf(label)] = curNode

			else:
				raise Exception("What! This cannot happen")

		if self.numLines == 0:
			raise Exception("parsePLL(): No text to parse")

		if not rootNode:
			raise Exception("parsePLL(): rootNode is empty")

		assert isinstance(rootNode, self.constructor)
		return (rootNode, hSubTrees)

	# ------------------------------------------------------------------------

	def _generator(self, fh):

		# --- Allow passing in a string
		if isinstance(fh, str):
			fh = io.StringIO(fh)

		# --- We'll need the first line to determine
		#     if there's any leading whitespace, which will
		#     be stripped from ALL lines (and therefore must
		#     be there for every subsequent line)
		line = self.nextNonBlankLine(fh)
		if not line:
			return

		# --- Check if there's any leading whitespace
		leadWS = ''
		leadLen = 0
		result = reLeadWS.search(line)
		if result:
			leadWS = result.group(1)
			leadLen = len(leadWS)

		flag = None   # might become 'any'

		if leadWS:
			while line:
				# --- Check if the required leadWS is present
				if not flag and (line[:leadLen] != leadWS):
					raise SyntaxError("Missing leading whitespace")

				flag = yield line[leadLen:]

				if flag:
					line = self.nextAnyLine(fh)
				else:
					line = self.nextNonBlankLine(fh)
		else:
			while line:

				flag = yield line

				if flag:
					line = self.nextAnyLine(fh)
				else:
					line = self.nextNonBlankLine(fh)

	# ------------------------------------------------------------------------

	def splitLine(self, line):

		# --- All whitespace lines should never be passed to this function
		assert type(line) == str
		assert not isAllWhiteSpace(line)

		# --- returns (level, label, marked, numHereDoc)
		#     label will have markStr removed, but hereDocStr's will remain

		marked = False
		result = self.reLine.search(line)
		if result:

			# --- Get indentation, if any, to determine level
			indent = result.group(1)
			if ' ' in indent:
				raise SyntaxError(f"Indentation '{traceStr(indent)}'"
										 " cannot contain space chars")
			level = len(indent)

			# --- Check if the mark string is present
			#     If so, strip it to get label, then set key = label
			if self.markStr:
				if line.find(self.markStr, level) == level:
					label = line[level + len(self.markStr):].lstrip()
					if len(label) == 0:
						raise SyntaxError("Marked lines cannot be empty")
					marked = True
				else:
					label = line[level:]
			else:
				label = line[level:]

			# --- Check if there are any HereDoc strings
			numHereDoc = 0
			if self.hereDocStr:
				pos = label.find(self.hereDocStr, 0)
				while pos != -1:
					numHereDoc += 1
					pos += len(self.hereDocStr)
					pos = label.find(self.hereDocStr, pos)

			label = label.replace('\\#', '#')
			return (level, label, marked, numHereDoc)
		else:
			raise Exception("What! This cannot happen (reLine fails to match)")

	# ---------------------------------------------------------------------------

	def nextAnyLine(self, fh):

		line = fh.readline()
		self.numLines += 1
		if line:
			return line
		else:
			return None

	# ---------------------------------------------------------------------------

	def nextNonBlankLine(self, fh):

		line = fh.readline()
		self.numLines += 1
		if not line:
			return None
		line = re.sub(self.reComment, '', line)
		line = line.rstrip()
		while line == '':
			line = fh.readline()
			self.numLines += 1
			if not line: return None
			line = re.sub(self.reComment, '', line)
			line = line.rstrip()
		return line

# ---------------------------------------------------------------------------
#                   UNIT TESTS
# ---------------------------------------------------------------------------

def test_1():
	s = '''
		top
			peach
				fuzzy
						navel
				pink
			apple
				red
	'''
	(tree, hSubTrees) = parsePLL(s)

	n = ilen(tree.children())
	assert n == 2

	n = ilen(tree.descendents())
	assert n == 6

	assert ilen(tree.firstChild.children()) == 2

	assert tree['label'] == 'top'

	assert tree.firstChild['label'] == 'peach'

	node = tree.firstChild.firstChild
	node['label'] == 'fuzzy navel'

# ---------------------------------------------------------------------------
# Test some invalid input

def test_7():
	s = '''
		main
			  peach
			apple
	'''
	with pytest.raises(SyntaxError):
		parsePLL(s)

def test_8():
	s = '''
main
   peach
   apple
	'''
	with pytest.raises(SyntaxError):
		parsePLL(s)

# ---------------------------------------------------------------------------
# --- Test HEREDOC syntax

def test_3():
	s = '''
		menubar
			file
				new
					*handler <<<
						my $evt = $_[0];
						$evt.createNewFile();
						return undef;

				open
			edit
				undo
	'''
	(tree, hSubTrees) = parsePLL(s, debug=False)
	handler = hSubTrees['handler']

	label = tree['label']
	assert label == 'menubar'

	n = ilen(tree.children())
	assert n == 2

	n = ilen(tree.descendents())
	assert n == 7

	assert 'lHereDoc' in handler
	assert (handler['lHereDoc'][0]
		== 'my $evt = $_[0];\n$evt.createNewFile();\nreturn undef;\n')

# ---------------------------------------------------------------------------
#     Test if it will parse fragments

def test_4():
	s = '''
		menubar
			file
				new
				open
			edit
				undo
		layout
			row
				EditField
				SelectField
	'''
	(tree, hSubTrees) = parsePLL(s, debug=False)

	n = ilen(tree.descendents())
	assert n == 6

	n = ilen(tree.followingNodes())
	assert n == 10

# ---------------------------------------------------------------------------
#     Test marked subtrees

def test_5():
	s = '''
		App
			* menubar
				file
					new
					open
				edit
					undo
			* layout
				row
					EditField
					SelectField
	'''
	(tree, hSubTrees) = parsePLL(s, debug=False)
	subtree1 = hSubTrees['menubar']
	subtree2 = hSubTrees['layout']

	n = ilen(tree.descendents())
	assert n == 11

	assert (subtree1['label'] == 'menubar')
	n = ilen(subtree1.descendents())
	assert n == 6

	assert (subtree2['label'] == 'layout')
	n = ilen(subtree2.descendents())
	assert n == 4

	n = ilen(tree.followingNodes())
	assert n == 11

def test_6():
	s = '''
		bg  # a comment
			color = \\#abcdef   # not a comment
			graph
	'''
	(tree, hSubTrees) = parsePLL(s)

	n = ilen(tree.descendents())
	assert n == 2

	assert tree['label'] == 'bg'

	assert tree.firstChild['label'] == 'graph'

# ---------------------------------------------------------------------------

cleanup_testcode(globals())   # remove unit tests when not testing

# ---------------------------------------------------------------------------

# To Do:
#    1. Allow spaces for indentation
