# myutils.py

import sys, re, io, pytest

reAllWS      = re.compile(r'^\s*$')
reLeadWS     = re.compile(r'^([\t\ ]+)')   # don't consider '\n'
reLeadTabs   = re.compile(r'^(\t*)')
reTrailWS    = re.compile(r'\s+$')
reTrailNL    = re.compile(r'\n$')
reNonSepChar = re.compile(r'^[A-Za-z0-9_\s]')
reFirstWord  = re.compile(r'^\s*(\S+)')
reAssign     = re.compile(r'^\s*(\S+)\s*\=\s*(.*)$')
hSpecial = {
	"\t": "\\t",
	"\n": "\\n",
	" " : "\\s",
	}

# ---------------------------------------------------------------------------

def splitAssignment(s):

	assert type(s) == str
	result = reAssign.search(s)
	if result:
		return (result.group(1), result.group(2))
	else:
		raise Exception(f"String '{s}' is not an assignment statement")

# ---------------------------------------------------------------------------

def rmPrefix(lLines, *, debug=False, skipEmptyLines=True):
	# --- Normally lLines is a list of strings, but you can pass in
	#        a string with internal '\n' characters
	#
	# --- A  line consisting of only whitespace, is considered empty
	#     leading and trailing empty lines don't appear in output
	#     internal empty lines appear as empty lines, but
	#        no exception for the missing prefix

	# --- Check the type of the parameter ---
	if isinstance(lLines, str):
		if debug:
			print(f"DEBUG: String passed, splitting into lines")
		lNewLines = rmPrefix(io.StringIO(lLines).readlines())
		return ''.join(lNewLines)
	elif type(lLines) is not list:
		typ = type(lLines)
		raise TypeError(f"rmPrefix(): Invalid parameter, type = {typ}")

	if len(lLines) == 0:
		if debug:
			print(f"DEBUG: Zero lines - return empty list")
		return []

	firstLine = lLines[0]             # first line
	nextPos = 1
	if debug:
		print(f"DEBUG:    firstLine set to '{traceStr(firstLine)}'")

	lNewLines = []     # this will be returned

	# --- Skip past any empty lines
	#     NOTE: If skipEmptyLines is False, the empty lines are
	#           included, but not considered for determining the prefix

	while isAllWhiteSpace(firstLine) and (nextPos < len(lLines)):
		if skipEmptyLines:
			if debug:
				print(f"DEBUG: Line at pos {nextPos-1} '{traceStr(firstLine)}'"
						 " is empty - skipping")
		else:
			if line[-1] == '\n':
				lNewLines.append('\n')
				if debug:
					print(f"DEBUG: Add line at pos {nextPos-1} '\\n'")
			else:
				lNewLines.append('')
				if debug:
					print(f"DEBUG: Add line at pos {nextPos-1} ''")

		firstLine = lLines[nextPos]
		if debug:
			print(f"DEBUG:    firstLine reset to '{traceStr(firstLine)}'")
		nextPos += 1

	if (isAllWhiteSpace(firstLine)):
		if debug:
			print(f"DEBUG: All lines empty - return empty list")
		return []

	if debug:
		print(f"DEBUG: First non-empty line '{traceStr(firstLine)}'"
		      f" found at pos {nextPos-1}")

	result = reLeadWS.match(firstLine)
	if not result:
		if debug:
			print(f"DEBUG: No prefix found - return remaining lines,"
			      f" sripping trailing empty lines")
		lNewLines = lLines[nextPos:]
		while (len(lNewLines) > 0) and isAllWhiteSpace(lNewLines[-1]):
			del lNewLines[-1]
		return lNewLines             # nothing to strip off

	leadWS = result.group(1)
	nChars = len(leadWS)
	assert nChars > 0    # due to regexp used
	if debug:
		print(f"DEBUG: Prefix '{traceStr(leadWS)}'"
		      f" consists of {nChars} chars")

	# --- Create an entirely new array
	#     Add first line, with prefix stripped off
	lNewLines.append(firstLine[nChars:])
	if debug:
		print(f"DEBUG: Add line '{traceStr(firstLine[nChars:])}'")

	for line in lLines[nextPos:]:
		if isAllWhiteSpace(line):
			if skipEmptyLines:
				if debug:
					print(f"DEBUG: Skip empty line")
			else:
				if line[-1] == '\n':
					lNewLines.append('\n')
					if debug:
						print(f"DEBUG: Add line '\\n'")
				else:
					lNewLines.append('')
					if debug:
						print(f"DEBUG: Add line ''")
		else:
			pos = line.find(leadWS)
			if pos == 0:
				# --- remove the prefix
				lNewLines.append(line[nChars:])
				if debug:
					print(f"DEBUG: Add line '{traceStr(line[nChars:])}'")
			else:
				raise SyntaxError("rmPrefix(): Bad indentation")

	if skipEmptyLines:
		# --- Strip off trailing WS lines
		while (len(lNewLines) > 0) and isAllWhiteSpace(lNewLines[-1]):
			del lNewLines[-1]
			if debug:
				print(f"DEBUG: Remove last line")

	if debug:
		print(lNewLines)

	return lNewLines

# ---------------------------------------------------------------------------

def isAllWhiteSpace(s):

	assert type(s) == str
	if reAllWS.match(s):
		return True
	else:
		return False

# ---------------------------------------------------------------------------

def isSeparator(s, testch=None):
	# --- a string is a separator if:
	#        1. string is not empty
	#        2. all chars are the same
	#        3. the char is not a letter, digit, '_' or whitespace
	#     return value is the character - of length 1
	#     If testch is provided, return value will be None
	#        unless the separator char matches it

	assert type(s) == str
	if (len(s) == 0):
		return None
	ch0 = s[0]
	if reNonSepChar.search(ch0):
		return None
	for ch in s[1:]:
		if ch != ch0:
			return None
	if testch:
		assert len(testch) == 1
		if (ch0 != testch):
			return None
	return ch0

# ---------------------------------------------------------------------------

def firstWordOf(s):

	assert type(s) == str
	result = reFirstWord.search(s)
	if result:
		return result.group(1)
	else:
		return None

# ---------------------------------------------------------------------------

def getHereDoc(fh):

	# --- Allow passing in a string
	if isinstance(fh, str):
		fh = io.StringIO(fh)

	lLines = []
	line = fh.readline()
	while line and not reAllWS.match(line):
		lLines.append(line)
		line = fh.readline()
	return rmPrefix(lLines)

# ---------------------------------------------------------------------------

def getMethod(aClass, methodName):

	try:
		return getattr(aClass, methodName)
	except AttributeError:
		return None

# ---------------------------------------------------------------------------

def getFunc(aModule, funcName):

	try:
		return getattr(aModule, funcName)
	except AttributeError:
		return None

# ---------------------------------------------------------------------------

def traceStr(str, *, maxchars=0, detailed=False):

	nTabs = 0
	nChars = 0
	outstr = ''
	result = reLeadTabs.search(str)
	totTabs = len(result.group(1))
	for ch in str:
		if (maxchars > 0) and (nChars >= maxchars): break
		if ch in hSpecial:
			outch = hSpecial[ch]
		else:
			i = ord(ch)
			if (i < 32) or (i > 126):
				outch = f"ASCII{i}"
			else:
				outch = ch
		if detailed:
			print(f"CHAR: '{outch}'")
		outstr += outch
		nChars += 1
	return outstr

# ---------------------------------------------------------------------------

def cleanup_testcode(glob, *, debug=False):

	# --- If not running unit tests, remove unneeded functions and data
	#     to save memory
	if sys.argv[0].find('pytest') == -1:
		if debug:
			print(f"Running normally - clean up {glob['__file__']} test functions/data")
		reTest = re.compile(r'^(?:test|init)_')
		for name in [name for name in glob.keys() if reTest.match(name)]:
			if debug:
				print(f"Clean up {name}")
			globals()[name] = None
	else:
		if debug:
			print("Running unit tests")

# ---------------------------------------------------------------------------
#                  UNIT TESTS
# ---------------------------------------------------------------------------

def test_1():
	with pytest.raises(TypeError):
		s = rmPrefix(5)

def test_2():
	with pytest.raises(TypeError):
		s = rmPrefix((3,4,5))

def test_21():
	from TreeNode import TreeNode
	with pytest.raises(TypeError):
		s = rmPrefix(TreeNode('label'))

# --- Make sure these things are tested - for strings & lists of strings
#     1. By default, any whitespace lines are removed
#     2. Internal whitespace lines are included
#     3. Trailing newlines are untouched

def test_3():
	# --- Basic example - find leading whitespace in first line
	#                     and strip that from all other lines
	lNewLines = rmPrefix([
		"\t\tabc",
		"\t\t\tdef",
		"\t\t\t\tghi",
		])
	assert lNewLines == [
		"abc",
		"\tdef",
		"\t\tghi",
		]

def test_30():
	assert rmPrefix([]) == []

def test_31():
	# --- leading and trailing all-whitespace lines are removed
	lNewLines = rmPrefix([
		"",
		"\t \t",
		"\t\t\n",
		"\t\tabc",
		"\t\t\tdef",
		"\t\t\t\tghi",
		"\t\t",
		])
	assert lNewLines == [
		"abc",
		"\tdef",
		"\t\tghi",
		]

def test_4():
	s = '''
			abc
				def
					ghi
'''
	lNewStr = rmPrefix(s)
	assert lNewStr == 'abc\n\tdef\n\t\tghi\n'

def test_5():
	# --- test the utility function getHereDoc()
	s = '''
		menubar
			file
				new
					handler <<<
						my $evt = $_[0];
						$evt.createNewFile();
						return undef;

				open
			edit
				undo
'''
	fh = io.StringIO(s)
	line1 = fh.readline()   # a blank line
	line2 = fh.readline()   # menubar
	line3 = fh.readline()   # file
	line4 = fh.readline()   # new
	line5 = fh.readline()   # handler <<<
	assert line5.find('<<<') == 13
	lLines = getHereDoc(fh)
	assert len(lLines) == 3
	line6 = fh.readline()   # open
	assert(line6.find('open') == 4)

def test_6():
	assert not isSeparator('')
	assert not isSeparator('X')
	assert not isSeparator('x')
	assert not isSeparator('_')
	assert not isSeparator('4')
	assert not isSeparator(' ')
	assert not isSeparator('\t')

	assert isSeparator('-') == '-'
	assert isSeparator('-----') == '-'
	assert isSeparator('----------------') == '-'
	assert not isSeparator('abc')
	assert isSeparator('=====') == '='
	assert not isSeparator(' -')
	assert not isSeparator('- ')

	assert isSeparator('-', '-')
	assert isSeparator('-----', '-')
	assert isSeparator('----------------', '-')
	assert isSeparator('=====', '=')
	assert isSeparator('=====', '=')


def test_7():
	assert firstWordOf('abc def') == 'abc'
	assert firstWordOf('') == None
	assert firstWordOf('   ') == None
	assert firstWordOf('  abc  def  ghi') == 'abc'

def test_8():
	# --- Test my understanding of the split method
	assert ("abc xyz".split()[0] == 'abc')
	assert ("   abc xyz  ".split()[0] == 'abc')
	assert ("   abc xyz  ".split()[1] == 'xyz')
	assert ("   房子 窗口  ".split()[0] == '房子')
	assert ("   房子 窗口  ".split()[1] == '窗口')

def test_9():
	assert splitAssignment("x = 9") == ('x', '9')
	assert splitAssignment("xxx = 90") == ('xxx', '90')
	assert splitAssignment("  x   =   9") == ('x', '9')
	assert splitAssignment("x=9") == ('x', '9')

def test_10():
	with pytest.raises(Exception):
		result = splitAssignment("x9")

def test_11():
	try:
		(key, value) = splitAssignment('name = editor')
		assert key == 'name'
		assert value == 'editor'
	except:
		raise Exception("Very Bad")


cleanup_testcode(globals())
