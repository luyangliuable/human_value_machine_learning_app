import os
import git
import csv
import re
import tempfile
import linecache
import shutil
import tempfile
import chardet
from typing import TypeVar, Generic, List, NewType
from project.machine_learning.src.csv_file_modifier.modifier import csv_modifier

T = TypeVar("T")
###############################################################################
#                    Dictionaries for programming languages                   #
###############################################################################

WILDCARD_IDENTIFIER = '*'

languages = {
    "c": {
        "multiline_start": '\/\*',
        "multiline_end": '\*\/',
        "single_line": ['\/\/', '/*'],
        "strip": ['\/', '\*'],
        "format": 'c',
        "language": "c"
    },

    'kotlin': {
        "multiline_start": '\/\*',
        "multiline_end": '\*\/',
        "single_line": ['\/\/', '/*'],
        "strip": ['\/', '\*'],
        "format": 'kt',
        "language": "kotlin"
    },

    "c++": {
        "multiline_start": '\/\*',
        "multiline_end": '\*\/',
        "single_line": ['\/\/', '/*'],
        "strip": ['\/', '\*'],
        "format": 'cpp',
        "language": "c++"
    },

    "javascript": {
        "multiline_start": '\/\*',
        "multiline_end": '\*\/',
        "single_line": ['\/\/', '/*'],
        "format": 'js',
        "strip": ['\/', '\*'],
        "language": "javascript"
    },
    "ruby": {
        "multiline_start": '=begin',
        "multiline_end": '=end',
        "single_line": ["#"],
        "format": 'rb',
        "strip": ['=begin', '=end'],
        "language": "ruby"
    },
    "gradle": {
        "multiline_start": '/*',
        "multiline_end": '*/',
        "single_line": ['//'],
        "format": 'gradle',
        "language": "gradle"
    },
    "build": {
        "multiline_start": '▓',
        "multiline_end": '▓',
        "single_line": ['#'],
        "format": 'build',
        "language": "build"
    },

    "python": {
        "multiline_start": '"""',
        "multiline_end": '"""',
        "single_line": ['#', '"""'],
        "strip": ['"""'],
        "format": 'py',
        "language": "python"
    },

    "assembly": {
        "multiline_start": '"""',
        "multiline_end": '"""',
        "single_line": [';'],
        "strip": ['"""'],
        "format": 'asm',
        "language": "assembly"
    },
    "makefile": {
        "multiline_start": '▓',
        "multiline_end": '▓',
        "single_line": ['#'],
        "format": 'makefile',
        "language": "makefile"
    },
    "shell": {
        "multiline_start": '▓',
        "multiline_end": '▓',
        "single_line": ['#'],
        "format": 'sh',
        "language": "shell"
    },
    "perl": {
        "multiline_start": '=',
        "multiline_end": '=',
        "single_line": ['#', '='],
        "format": 'pl',
        "language": "perl"
    },
    "java": {
        "multiline_start": '\/\*',
        "multiline_end": '\*\/',
        "single_line": ['\/\/'],
        "strip": ['\/', '\*'],
        "format": 'java',
        "language": "java"
    },

    "html": {
        "multiline_start": '<!--',
        "multiline_end": '-->',
        "single_line": ['▓'],
        "strip": ["<", ">", "--", "!"],
        "format": 'html',
        "language": "html"
    },

    "css": {
        "multiline_start": '\/\*',
        "multiline_end": '\*\/',
        "single_line": ["▓"],
        "strip": ['\/', '\*'],
        "format": 'css',
        "language": "css"
    },

    "xml": {
        "multiline_start": '<!--',
        "multiline_end": '-->',
        "single_line": ['▓'],
        "strip": ["<", ">", "--", "!"],
        "format": 'xml',
        "language": "xml"
    },

    "batchscript": {
        "multiline_start": '▓',
        "multiline_end": '▓',
        "single_line": ['::'],
        "format": 'bat',
        "language": "batchscript"
    },

}

html_comment = languages['html']
batch_comment = languages['batchscript']
css_comment = languages['css']
xml_comment = languages['xml']
c_comment = languages['c']
kotlin_comment = languages['kotlin']
cpp_comment = languages['c++']
javascript_comment = languages['javascript']
gradle_comment = languages['gradle']
java_comment = languages['java']
build_comment = languages['build']
python_comment = languages['python']
asm_comment = languages['assembly']

""" assume (no comment like this for makefile and shell):
# This is the first line of a comment \
and this is still part of the comment \
as is this, since I keep ending each line \
with a backslash character
"""
makefile_comment = languages['makefile']
shell_comment = languages['shell']
perl_comment = languages['perl']


def get_comment_from_repo_using_all_languages(repo: str, branch: str, output_dir: str) -> list:
    """
    Keyword arguments:
    repo --
    branch --
    output_dir --
    """
    files = []
    for key in languages:
        files.append(extract_comment_from_repo(repo, branch, languages[key], output_dir))

    return files

def get_comment_from_path_using_all_languages(directory: str, output_dir: str):
    for key in languages:
        extract_comment_from_path(directory, languages[key], output_dir)


def save_in_dict(line: str, location: str, language: str) -> dict:
    return {'line': line, 'location': location, 'language': language}


def iterate_dictionary_for_header(dictionary: dict) -> List[T]:
    res = []
    for key in dictionary:
        res.append(key)

    return res


def get_snapshot_from_git(git_repo_link: str, branch: str, depth: int) -> str:
  location = tempfile.mkdtemp() # Create temporary dir
  git.Repo.clone_from(git_repo_link, location, branch=branch, depth=depth)
  return location
  # Copy desired file from temporary dir
  # shutil.move(os.path.join(t, 'setup.py'), '.')
  # # Remove temporary dir
  # shutil.rmtree(t)


def extract_comment_from_path(directory: str, language: dict, output_dir: str):
    """Extracts all comments from file contained inside a path

    Keyword Arguments:

    directory -- the root directory to search from
    language

    language -- the programming language to search in
    """
    files = []
    comment_dir = create_comment_file(language)

    files = files + search_file('*' + language["format"], directory)

    line_counter = 0

    # The maximum line of code for each csv file ###############################
    max_line_per_file = 50000
    for file in files:
        if line_counter > max_line_per_file:
            comment_dir = create_comment_file(language)
            line_counter = 0

        lines_in_file = get_every_line_from_file(file)
        comments_in_file = extract_comment_from_line_list(lines_in_file, language)

        write_comment_file(comments_in_file, comment_dir)
        line_counter += len(comments_in_file)


def extract_comment_from_repo(repo: str, branch: str, language: dict, tmpdirname: str) -> str:
    """Extracts all comments from file contained inside a path

    Keyword Arguments:

    directory -- the root directory to search from
    language

    language -- the programming language to search in
    """
    depth = 1
    line_counter = 0

    tmp_directory = get_snapshot_from_git(repo, branch, depth)

    files = []

    comment_dir = create_comment_file(language, tmpdirname)

    files = files + search_file('*' + language["format"], tmp_directory)

    # The maximum line of code for each csv file ###############################
    max_line_per_file = 50000
    for file in files:
        if line_counter > max_line_per_file:
            comment_dir = create_comment_file(language, tmpdirname)
            line_counter = 0

        # lines_in_file = get_every_line_from_file(file)
        # comments_in_file = extract_comment_from_line_list(lines_in_file, language)

        comments_in_file = extract_all_comment_from_file(file, language)

        write_comment_file(comments_in_file, comment_dir)
        line_counter += len(comments_in_file)


    return comment_dir


def get_every_multiline(filename: str, language: dict):
    res = []
    try:
        with open(filename, "r") as f:
            a = f.read()
            raw_multiline = re.findall(language["multiline_start"] + ".*?" + language["multiline_end"], a, flags=re.DOTALL)

            for item in language['strip']:
                raw_multiline = [re.sub(item, ' ', s) for s in raw_multiline]

            c = [re.sub('\n', ' ', s) for s in raw_multiline]
            c = [re.sub('\s+', ' ', s) for s in c]
            final_multiline = [s.strip() for s in c]

        f.close()

        res = transform_list_to_dict_line(filename, final_multiline, language['language'])
    except:
        pass

    return res


def transform_list_to_dict_line(filename: str, arr: list[str], language: str) -> dict:
    lines = []
    for i, line in enumerate(arr):
        lines.append(save_in_dict(line, filename, language))

    return lines


def get_every_singleline(filename: str, language: dict):
    linecache.clearcache()
    modifier = csv_modifier()
    num_of_lines = modifier.get_number_of_lines_in_file(filename)
    res = []
    count = 0
    prev = False
    for i in range(num_of_lines):
        try:
            a = linecache.getline(filename, i)
            b =  re.findall("(?<=" + language['single_line'][0] + ").+?[\n\r]", a)
            if b != []:
                b[0] = b[0].strip()
                if b[0] != '':
                    prev = True
                    if len(res) <= count:
                        res.append("")
                        res[count] += b[0] + " "
                    else:
                        res[count] += b[0] + " "
            else:
                if prev == True:
                    count += 1
                prev = False
        except:
            pass

    res = transform_list_to_dict_line(filename, res, language['language'])
    return res


def get_every_comment_from_file(filename: str, language: dict):
    singleline = get_every_singleline(filename, language)
    multiline = get_every_multiline(filename, language)
    res = singleline + multiline
    return res


def get_every_line_from_file(filename: str) -> List[T]:
    ###############################################################################
    #                         getting encoding of the file                        #
    ###############################################################################

    lines = []
    with open(filename, 'rb') as thefile:
        encoding = chardet.detect(bytes(thefile.read()))['encoding']

    try:
        thefile = open(filename, 'r', encoding=encoding)
        lines = thefile.readlines()
    except:
        try:
            print("Trouble decoding file " + filename + " now attempting to use utf-8")
            with open(filename, 'r', encoding="utf-8" ) as thefile:
                lines = thefile.readlines()
        except:  # UnsupportEncodingException:
            print("failed to decode file" + filename)

    if len(lines) != 0:
        for line_number in range(len(lines)):  # enumerate(line)
            lines[line_number] = {
                'line': lines[line_number].strip('\n'),
                'location': filename + ": " + str(line_number+1)
            }
    print(lines)
    return lines


def extract_all_comment_from_file(filename:str, language: str):
    singleline_comments = get_every_singleline(filename, language)
    multiline_comments = get_every_multiline(filename, language)
    res = singleline_comments + multiline_comments
    return res

def extract_comment_from_line_list(lines: List[T], language: dict) -> List[T]:
    """extracts the comment from a list of lines

    if is a multiline comment, accumulate the multiline comment and return as a single line
    if is a single line comment, return as a single line, record previous line is a single line comment.
    if previous line is a single line comment, treat as single_multiline comment.

    Keyword Arguments:

    lines -- list of lines to extract the comment from. It contains the line as well as the file location
    languages -- the language the lines are written in
    """

    max_comment_length = 100
    res = []
    multiline_comment = False
    next_line_is_comment = False
    single_multiline_comment = ""
    multiple_singleline_comment = ""
    if len(lines) > 0:
        nextline_singleline_comment = find_text_enclosed_inside(lines[0]['line'] , language["single_line"])
        nextline_singleline_comment = strip_comment_of_symbols(nextline_singleline_comment, language)
        nextline_singleline_comment = remove_starting_whitespace(nextline_singleline_comment)

    for line_num in range(len( lines )):
        comment = ""
        line = lines[line_num]
        ###############################################################################
        #                     sliding window algorithm with lines                     #
        ###############################################################################


        if line_num + 1 < len(lines):
            current_singleline_comment = nextline_singleline_comment
            nextline = lines[line_num + 1]['line']
            nextline_singleline_comment = find_text_enclosed_inside(nextline, language["single_line"])
            nextline_singleline_comment = strip_comment_of_symbols(nextline_singleline_comment, language)
            nextline_singleline_comment = remove_starting_whitespace(nextline_singleline_comment)
            if nextline_singleline_comment != "":
                next_line_is_comment = True
                multiple_singleline_comment += current_singleline_comment + " "
            elif next_line_is_comment:
                next_line_is_comment = False
                multiple_singleline_comment += current_singleline_comment
                comment = save_in_dict(multiple_singleline_comment, line['location'], language['language'])
                multiple_singleline_comment = ""

        if check_triggers_multiline_comment(line['line'], language["multiline_start"], language["multiline_end"]):
            if not multiline_comment:
                multiline_comment = True
            elif not next_line_is_comment: # Code when there is online one singleline comment using multiline
                single_multiline_comment += remove_starting_whitespace(strip_comment_of_symbols(line['line'].strip("\n"), language ))
                comment = save_in_dict(single_multiline_comment, line['location'], language['language'])
                single_multiline_comment = ""
                multiline_comment = False

        if multiline_comment:
                single_multiline_comment += remove_starting_whitespace( strip_comment_of_symbols( line['line'].strip("\n"), language)) + " "
        elif comment == "" and not next_line_is_comment: # adjusted
            comment = save_in_dict(find_text_enclosed_inside(line['line'], language["single_line"]), line['location'], language['language'])

        if comment != "":
            comment['line'] = strip_comment_of_symbols(comment['line'], language)
            comment['line'] = remove_starting_whitespace(comment['line'])
            if comment['line'] != "" and not check_if_comment_is_empty(comment, language):
                assert comment.__class__ is dict, "class of comment must be stored in dictionary"
                previous_line_is_comment = True
                leng = len(re.findall(r'\w+', comment['line']))
                if leng <= max_comment_length:
                    res.append(comment)
                    if leng >= 70:
                        print(comment['line'])

    if next_line_is_comment:
        multiple_singleline_comment += nextline_singleline_comment + " "
        comment = save_in_dict(multiple_singleline_comment, line['location'], language['language'])
        comment['line'] = strip_comment_of_symbols(comment['line'], language)
        comment['line'] = remove_starting_whitespace(comment['line'])
        assert comment['line'][0] != " ", "no starting whitespace allowed"
        leng = len(re.findall(r'\w+', comment['line']))
        if leng <= max_comment_length:
            res.append(comment)
            if leng >= 70:
                print(comment['line'])
        next_line_is_comment = False
        multiple_singleline_comment = ""

    return res


def search_file(file_name: str, path: str) -> List[T]:
    """Search a root directory for a particular file

    Keyboard Arguments:
    file_name -- name of the file to search for
    path -- path from which to search the file
    """
    # print("Searching in path: " + path + " for " + file_name)
    res = []
    for root, dirs, files in os.walk(path):
        if file_name[0] == WILDCARD_IDENTIFIER:
            for file in files:
                same_format = check_file_is_same_format(file_name, file)
                if same_format:
                    if root[-1] != "/" and file[0] != "/":
                        res.append(root + "/" + file)
                    else:
                        res.append(root + file)
        else:
            for file in files:
                if file == file_name:
                    if root[-1] != "/" and file[0] != "/":
                        res.append(root + "/" + file)
                    else:
                        res.append(root + file)

            found = file.find(file_name)

            if found != -1:
                break
    return res


def check_file_is_same_format(file_one: str, file_two:str) -> bool:
    """Checks if file1 and file2 are of the same format

    Keyword Arguments:
    file_one -- the first file in the comparison
    file_two -- the second file in the comparison
    """

    # Get the file format of first file ###########################################
    counter = 1
    first_fileformat = ""
    while file_one[-counter] != "." and counter < len(file_one):
        first_fileformat = first_fileformat + file_one[-counter]
        counter += 1

    # Get the file format of second file ###########################################
    counter = 1
    second_fileformat = ""
    while file_two[-counter] != "." and counter < len(file_two):
        second_fileformat = second_fileformat + file_two[-counter]
        counter += 1

    if second_fileformat == first_fileformat:
        return True

    return False


def check_triggers_multiline_comment(line: str, multiline_sexp: str, multiline_closing_sexp: str) -> bool:
    """checks if a particular line triggers the start of a multi-line comment

    Keyword Arguments:
    line -- the line to examine
    multiline_sexp -- the sexp that dictates the start of multi-line comment
    """

    triggers_multiline = False
    # triggers_closing_multiline = False
    multiline_sexp_length = len(multiline_sexp)
    # res = ""
    # start_of_comment = None
    for which_line_column in range(len(line)):
        sliding_window = ""
        for which_sexp_column in range(multiline_sexp_length):
            if which_sexp_column + which_line_column < len(line):
                sliding_window += line[which_line_column + which_sexp_column]

        if multiline_sexp != multiline_closing_sexp:
            if sliding_window == multiline_sexp:
                triggers_multiline = not triggers_multiline

            if sliding_window == multiline_closing_sexp:
                triggers_multiline = not triggers_multiline

        elif multiline_sexp == multiline_closing_sexp:
            if sliding_window == multiline_sexp:
                triggers_multiline = not triggers_multiline

    return triggers_multiline


def find_text_enclosed_inside(line: str, sexpressions: List[str]) -> str:
    """Find a text contained inside a sexp (s-expression)

    Keyword Arguments:
    line: the line from which to find string enclosed inside the s-expression
    sexp: s-expression that opens a multi-line comment incl. for example ({})[]
    """
    line_comment_active = False
    res = ""

    for sexp in sexpressions:
        sexp_length = len(sexp)
        start_of_comment = None
        for which_line_column in range(len(line)):
            sliding_window = ""
            for which_sexp_column in range(sexp_length):
                if which_sexp_column + which_line_column < len(line):
                    assert which_line_column + which_sexp_column >= 0
                    assert which_line_column + which_sexp_column < len(line)
                    sliding_window += line[which_line_column + which_sexp_column]

            if sliding_window == sexp:
                line_comment_active = not line_comment_active
                start_of_comment = which_line_column + sexp_length

            not_over_end_of_line = False
            if start_of_comment is not None:
                current_line_in_word = which_line_column - start_of_comment + sexp_length
                not_over_end_of_line = current_line_in_word <= len(line)

            if line_comment_active and not_over_end_of_line:
                if sliding_window not in sexp:
                    res += line[which_line_column]

    res = remove_starting_whitespace(res)
    return res


def create_comment_file(language, tmpdirname) -> str:
    """Create a comment file in the target directory

    Keyword Arguments:

    target -- the target directory
    """
    print("creating_comment_file!")

    counter = 0
    res = ""
    modifier = csv_modifier()

    fieldnames = ['line', 'location', 'language']
    # with tempfile.TemporaryDirectory() as tmpdirname:
    filename = modifier.find_next_filename(base_file_name="commentfile", savedir=tmpdirname)
    print("creating new comment file", filename, "for language", language['language'])
    res = os.path.join(tmpdirname, filename)
    with open(res, "w", encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    f.close()

    return res


def strip_comment_of_symbols(comment: str, language: dict) -> str:
    """Strip the comment of all programming language symbols

    Keyword Arguments:

    comment -- A string of comment

    language -- the programming language to search in
    """
    res = ""
    comment = comment.strip("\n")
    for char in comment:

        if char not in language["multiline_start"] and char not in language["multiline_end"]:

            res = res + char

    return res


def remove_starting_whitespace(comment: str) -> str:
    """Remove all the whitespace before the actual comment

    Keyword Arguments:

    comment -- A string of comment
    """
    whitespace = True
    res = ""

    for char in comment:
        if char != " ":
            whitespace = False

        if not whitespace:
            res += char

    return res


def check_if_comment_is_empty(comment: dict, language: dict) -> bool:
    """Check if the comment inside the comment is empty

    Keyword Arguments:

    comment -- A dictionary containing the comment as well as the location the comment is from
    language -- The language the comment is written in
    """
    if comment.__class__ is dict:
        Exception("class of comment must be stored in dictionary")
    comment = comment['line']
    assert comment.__class__ is str, "comment must be in string form to be processed: " + str(comment)
    comment = strip_comment_of_symbols(comment, language)
    for symbol in language["single_line"]:
        comment = comment.strip(symbol)
        comment = comment.strip(" ")
    if comment in ('', '\n'):
        return True

    return False


def write_comment_file(lines_of_comment: List[T], target: str):
    """Append a list comments to a file
    Keyword Arguments:

    lines_of_comment -- A list containing comment dictionaries
    target -- the target directory """

    fieldnames = ['line', 'location', 'language']

    with open(target, "a", encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerows(lines_of_comment)
    file.close()
