# PLLParser.py

"""
parse a 'Python-like language'
"""

import sys, io, re, pytest
from more_itertools import ilen
from pprint import pprint

from TreeNode import TreeNode
sys.path.append('.')   # for some reason, unit tests fail without this
from parserUtils import (
		rmPrefix, reLeadWS, isAllWhiteSpace,
		traceStr, firstWordOf
		)

# ---------------------------------------------------------------------------

def parsePLL(fh, constructor=TreeNode, *,
             debug=False,
             **kwargs):

	assert isinstance(constructor('label'), TreeNode)
	return PLLParser(constructor,
	                 debug=debug,
	                 **kwargs
	                 ).parse(fh)

# ---------------------------------------------------------------------------

class PLLParser():

	# --- We want to compile these just once, so make them class fields
	reLine = re.compile(r'^(\s*)')

	# --- These are the only recognized options
	hDefOptions = {
		# --- These become attributes of the PLLParser object
		'markStr':    '*',
		'reComment':  None,
		'reAttr':     None,
		}

	# ------------------------------------------------------------------------

	def __init__(self, constructor=TreeNode, *,
                debug=False,
                **kwargs):

		self.setOptions(kwargs)
		self.constructor = constructor or TreeNode
		self.debug = debug

	# ------------------------------------------------------------------------

	def setOptions(self, hOptions):

		# --- Make sure only valid options were passed
		for name in hOptions.keys():
			if name not in self.hDefOptions:
				raise Exception(f"Invalid option: '{name}'")

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
		reAttr = self.reAttr

		rootNode = curNode = None
		hSubTrees = {}

		curLevel = None
		debug = self.debug

		gen = self._generator(fh)
		for line in gen:
			if debug:
				print(f"LINE {self.numLines}: '{traceStr(line)}'", end='')

			(newLevel, label, marked) = self.splitLine(line)

			if debug:
				print(f" [{newLevel}] '{label}'")

			# --- process first non-empty line
			if rootNode == None:
				rootNode = curNode = self.constructor(label)

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
				if reAttr:
					result = reAttr.search(label)
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
				if marked:
					hSubTrees[firstWordOf(label)] = curNode
			elif diff == 0:
				# --- create new sibling node
				if debug:
					print(f"   - new sibling of {curNode.asDebugString()}")
				assert not curNode.nextSibling
				curNode = self.constructor(label).makeSiblingOf(curNode)
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

		# --- returns (level, label, marked)
		#     label will have markStr removed

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

			label = label.replace('\\#', '#')
			return (level, label, marked)
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

		reComment = self.reComment

		line = fh.readline()
		self.numLines += 1
		if not line:
			return None
		if reComment:
			line = re.sub(reComment, '', line)
		line = line.rstrip()
		while line == '':
			line = fh.readline()
			self.numLines += 1
			if not line:
				return None
			if reComment:
				line = re.sub(reComment, '', line)
			line = line.rstrip()
		return line

# ---------------------------------------------------------------------------
#                   UNIT TESTS
# ---------------------------------------------------------------------------

if sys.argv[0].find('pytest') > -1:

	def test_1():
		(tree, hSubTrees) = parsePLL('''
			top
				peach
					fuzzy
							navel

					pink
				apple
					red
			''')

		n = ilen(tree.children())
		assert n == 2

		n = ilen(tree.siblings())
		assert n == 0

		# --- descendents() includes the node itself
		n = ilen(tree.descendents())
		assert n == 6

		assert ilen(tree.firstChild.children()) == 2

		assert tree['label'] == 'top'

		assert tree.firstChild['label'] == 'peach'

		node = tree.firstChild.firstChild
		node['label'] == 'fuzzy navel'

	# ------------------------------------------------------------------------

	def test_2():
		# --- Root node can have siblings, i.e. input does not
		#     need to be a true tree

		(tree, hSubTrees) = parsePLL('''
			top
				peach
					fuzzy
							navel
					pink
				apple
					red
			next
				child of next
			''')

		n = ilen(tree.children())
		assert n == 2

		n = ilen(tree.siblings())
		assert n == 1

		# --- descendents() includes the node itself
		n = ilen(tree.descendents())
		assert n == 6

		assert tree['label'] == 'top'

		assert tree.firstChild['label'] == 'peach'
		assert tree.nextSibling['label'] == 'next'
		assert tree.nextSibling.firstChild['label'] == 'child of next'

	# ------------------------------------------------------------------------
	# Test some invalid input

	def test_3():
		s = '''
			main
				  peach
				apple
		'''
		with pytest.raises(SyntaxError):
			parsePLL(s)

	# ------------------------------------------------------------------------

	def test_4():
		# --- No support for indenting with spaces yet
		#     Below, both 'peach' and 'apple' are indented with spaces
		s = '''
	main
	   peach
	   apple
		'''
		with pytest.raises(SyntaxError):
			parsePLL(s)

	# ------------------------------------------------------------------------

	def test_5():
		# --- By default, neither comments or attributes are recognized
		(tree, hSubTrees) = parsePLL('''
			top
				number = 5 # not an attribute
				peach # not a comment
				apple
			''')
		assert tree['label'] == 'top'
		child1 = tree.firstChild
		child2 = tree.firstChild.nextSibling
		assert child1['label'] == 'number = 5 # not an attribute'
		assert child2['label'] == 'peach # not a comment'

	# ------------------------------------------------------------------------
	#     Test if it will parse fragments

	def test_5():
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

	# ------------------------------------------------------------------------
	#     Test marked subtrees

	def test_6():
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

	# ------------------------------------------------------------------------
	# --- Test stripping comments

	def test_7():

		(tree, hSubTrees) = parsePLL('''
			bg  # a comment
				color = \\#abcdef   # not a comment
				graph
			''',
			reComment=re.compile(r'(?<!\\)#.*$'),  # ignore escaped '#' char
			)

		n = ilen(tree.descendents())
		assert n == 3

		assert tree['label'] == 'bg'
		assert tree.firstChild['label'] == 'color = #abcdef'
		assert tree.firstChild.nextSibling['label'] == 'graph'

	# ------------------------------------------------------------------------
	# --- test hAttr key

	def test_8():
		(node,h) = parsePLL('''
				mainWindow
					*menubar
						align=left
						flow  =  99
						--------------
						not an option
					*layout
						life=  42
						meaning   =42
				''',
				reAttr=re.compile(r'^(\S+)\s*\=\s*(.*)$'),
				)

		menubar = h['menubar']
		assert menubar
		assert isinstance(menubar, TreeNode)
		hOptions1 = menubar.get('hAttr')
		assert hOptions1 == {
				'align': 'left',
				'flow': '99',
				}

		layout = h['layout']
		assert layout
		assert isinstance(layout, TreeNode)
		hOptions2 = layout.get('hAttr')
		assert hOptions2 == {
				'life': '42',
				'meaning': '42',
				}

	# ------------------------------------------------------------------------

	def test_9():
		# --- Note that this regexp allows no space before the colon
		#     and requires at least one space after the colon
		reWithColon = re.compile(r'^(\S+):\s+(.*)$')
		(node,h) = parsePLL('''
				mainWindow
					*menubar
						align: left
						flow:    99
						notAnOption : text
						notAnOption:moretext
						--------------
						not an option
					*layout
						life:  42
						meaning:   42
				''',
				reAttr=reWithColon,
				)

		menubar = h['menubar']
		assert menubar
		assert isinstance(menubar, TreeNode)
		hOptions1 = menubar.get('hAttr')
		assert hOptions1 == {
				'align': 'left',
				'flow': '99',
				}

		layout = h['layout']
		assert layout
		assert isinstance(layout, TreeNode)
		hOptions2 = layout.get('hAttr')
		assert hOptions2 == {
				'life': '42',
				'meaning': '42',
				}

# ---------------------------------------------------------------------------

# To Do:
#    1. Allow spaces for indentation
