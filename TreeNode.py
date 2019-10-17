# TreeNode.py

import sys, re, pytest, collections
from more_itertools import ilen

from parserUtils import (
	rmPrefix, isAllWhiteSpace, runningUnitTests, getVersion, traceStr
	)
from RETokenizer import RETokenizer

reAssign = re.compile(r'^(\S+)\s*\=\s*(.*)$')
__version__ = getVersion()

class TreeNode(collections.abc.MutableMapping):
	# --- These are a Class variables -------------------

	#     Modify this to affect how indentation is printed
	#     NOTE: Does NOT affect parsing

	indent = "\t"

	#     labels matching this are NOT quoted

	reSimpleLabel = re.compile(r'^[A-Za-z0-9_]+$')

	# ------------------------------------------------------------------------

	def __init__(self, label, tokenizer=None):
		super().__init__()

		if tokenizer:
			assert isinstance(tokenizer, RETokenizer)

		# --- label cannot be all whitespace nor start with whitespace
		if isAllWhiteSpace(label):
			raise Exception(f"Label '{traceStr(label)}' is all whitespace")
		if (label.lstrip() != label):
			raise Exception(f"Label '{traceStr(label)}' has leading whitespace")

		self.hData = {
			'label': label,
			}
		if tokenizer:
			self.hData['tokenizer'] = tokenizer
		self.parent = None
		self.nextSibling = None
		self.firstChild = None

	# ------------------------------------------------------------------------

	def tokens(self):

		if 'lTokens' in self:
			yield from self['lTokens']
		elif 'tokenizer' in self:
			assert 'label' in self
			label = self['label']
			tokenizer = self['tokenizer']

			assert isinstance(tokenizer, RETokenizer)
			yield from tokenizer.tokens(label)

	# ------------------------------------------------------------------------
	#    Multiple ways to build up a tree structure
	# ------------------------------------------------------------------------

	def makeChildOf(self, node):
		assert isinstance(node, TreeNode)

		self.parent = node

		lastChild = node.firstChild
		if lastChild != None:
			while lastChild.nextSibling:
				lastChild = lastChild.nextSibling

			# --- Now, lastChild has no nextSibling
			lastChild.nextSibling = self
		else:
			node.firstChild = self
		return self    # allow chaining

	def makeSiblingOf(self, node):
		assert isinstance(node, TreeNode)
		assert not self.parent
		# assert node.parent

		parent = node.parent
		cur = node
		while cur.nextSibling:
			cur = cur.nextSibling
			assert cur.parent == parent
		cur.nextSibling = self
		self.parent = parent
		return self    # allow chaining

	def appendNode(self, newNode):
		node = self
		while node.nextSibling:
			node = node.nextSibling
		node.nextSibling = newNode
		return self    # allow chaining

	def appendChildNode(self, newNode):
		if self.firstChild:
			self.firstChild.appendNode(newNode)
		else:
			self.firstChild = newNode
		return self    # allow chaining

	def append(self, label):
		self.appendNode(TreeNode(label))
		return self    # allow chaining

	def appendChild(self, label):
		self.appendChildNode(TreeNode(label))
		return self    # allow chaining

	# ------------------------------------------------------------------------
	# --- These methods allow us to treat a TreeNode object as a dict

	def __getitem__(self, key):
		return self.hData[key]

	def __setitem__(self, key, value):
		self.hData[key] = value

	def __delitem__(self, key):
		del self.hData[key]

	def __len__(self):
		return len(self.hData)

	def __iter__(self):
		return iter(self.hData)

	# ------------------------------------------------------------------------
	# --- These methods allow us to iterate over all of a
	#     TreeNode's children or descendents

	def hasChildren(self):

		return self.firstChild != None

	def children(self):

		child = self.firstChild
		while (child):
			yield child
			child = child.nextSibling

	def numChildren(self):

		n = 0
		node = self.firstChild
		while node:
			n += 1
			node = node.nextSibling
		return n

	def hasSiblings(self):

		return self.nextSibling != None

	def siblings(self):

		sibling = self.nextSibling
		while (sibling):
			yield sibling
			sibling = sibling.nextSibling

	def numSiblings(self):

		n = 0
		node = self.nextSibling
		while node:
			n += 1
			node = node.nextSibling
		return n

	def descendents(self, level=0):

		# --- First, visit the node itself
		yield (level, self)

		# --- Next, visit all of the node's descendents
		child = self.firstChild
		while (child):
			yield from child.descendents(level+1)
			child = child.nextSibling

	def followingNodes(self, level=0):

		# --- First, visit the node itself
		yield (level, self)

		# --- Next, visit all of the node's descendents
		child = self.firstChild
		while (child):
			yield from child.descendents(level+1)
			child = child.nextSibling

		# --- Next, visit siblings and their descendents
		node = self.nextSibling
		while node:
			yield (level, node)
			child = node.firstChild
			while (child):
				yield from child.descendents(level+1)
				child = child.nextSibling
			node = node.nextSibling

	def numNodes(self):

		return ilen(self.descendents())

	def asString(self, level=0, indent='\t'):

		s = ''
		cur = self
		while cur:
			for (level,node) in cur.descendents():
				s += (indent * level) + node.hData['label'] + '\n'
			cur = cur.nextSibling
		return s

	# ------------------------------------------------------------------------
	#      Utility Methods
	# ------------------------------------------------------------------------

	def printTree(self, desc=None, *,
	                    level=0, debug=False, indent=None):
		print()
		print('='*50)
		if desc:
			print('-'*6 + ' Tree \'' + desc + '\'')
			print('-'*50)
		for (level,node) in self.descendents():
			node.printNode(level, debug, indent)
		print('='*50)

	def printFragment(self, desc=None, *,
	                    level=0, debug=False, indent=None):
		print()
		print('='*50)
		if desc:
			print('-'*6 + ' Tree \'' + desc + '\'')
			print('-'*50)
		cur = self
		while cur:
			for (level,node) in cur.descendents():
				node.printNode(level, debug, indent)
			cur = cur.nextSibling
		print('='*50)

	def printNode(self, level=0, debug=True, indent=None):
		indentStr = (indent or self.indent) * level
		if debug:
			print('-' * 50)
		print(f"{indentStr}{self.asDebugString()}")
		if debug:
			print(f"{indentStr} -parent      = {nodeStr(self.parent)}")
			print(f"{indentStr} -nextSibling = {nodeStr(self.nextSibling)}")
			print(f"{indentStr} -firstChild  = {nodeStr(self.firstChild)}")
			print('-' * 50)
		return

	def asDebugString(self):
		label = self['label']
		if self.reSimpleLabel.match(label):
			s = label
		else:
			s = "'" + traceStr(label) + "'"
		if self.firstChild:
			fc = self.firstChild['label']
			s += f" FC = '{fc}'"
		if self.nextSibling:
			ns = self.nextSibling['label']
			s += f" NS = '{ns}'"
		return s

# ---------------------------------------------------------------------------

def nodeStr(node):
	# --- Cannot be a method because node can be None
	#     e.g. nodeStr(somenode.nextSibling)
	if node:
		assert isinstance(node, TreeNode)
		return node.asDebugString()
	else:
		return '(None)'

# ---------------------------------------------------------------------------
#                   UNIT TESTS
# ---------------------------------------------------------------------------

if runningUnitTests:

	# --- test tree ---
	#	top
	#		peach
	#			fuzzy navel
	#			pink
	#		apple
	#			red

	test_tree = TreeNode('top')

	peach = TreeNode('peach').makeChildOf(test_tree)
	TreeNode('fuzzy navel').makeChildOf(peach)
	TreeNode('pink').makeChildOf(peach)

	apple = TreeNode('apple').makeChildOf(test_tree)
	TreeNode('red').makeChildOf(apple)

	def test_0():
		# --- Test asString()
		mystr = test_tree.asString()
		assert mystr == rmPrefix('''
			top
				peach
					fuzzy navel
					pink
				apple
					red
			''')

	def test_1():
		n = ilen(test_tree.children())
		assert n == 2

	def test_2():
		n = ilen(test_tree.descendents())
		assert n == 6

	def test_3():
		assert ilen(test_tree.firstChild.children()) == 2

	def test_4():
		assert test_tree['label'] == 'top'

	def test_5():
		assert test_tree.firstChild['label'] == 'peach'

	def test_6():
		node = test_tree.firstChild.firstChild
		node['label'] == 'fuzzy navel'

	def test_7():
		from TreeNode import TreeNode
		with pytest.raises(TypeError):
			s = rmPrefix(TreeNode('label'))

