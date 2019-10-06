# PLLParser

Parse a Python-like language

This package includes the following modules:

## TreeNode.py

SYNOPSIS

	node = TreeNode('menubar')

	# --- A node can be used like a dictionary
	#     It will, by default, have a key 'label' set
	#        to the string provided

	print(node['label'])

	# menubar

	node['mykey'] = 'myvalue'
	print(f"node has {len(node)} keys")

	# node has 2 keys

	firstChild = TreeNode('firstchild')
	node.appendChildNode(firstChild)

	secondChild = TreeNode('secondchild')
	node.appendChildNode(secondChild)

	thirdChild = TreeNode('thirdchild')
	node.appendChildNode(secondChild)

	print(f"node has {node.numChildren()} children")

	# node has 3 children

	print(f"node has {node.numSiblings()} siblings")
	print(f"firstChild has {firstChild.numSiblings()} siblings")

	# node has 0 siblings
	# firstChild has 2 siblings

## RETokenizer.py

SYNOPSIS

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

## PLLParser.py

SYNOPSIS

	s = '''
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
	(tree, hSubTrees) = parsePLL(s)

	assert len(hSubTrees) == 2

