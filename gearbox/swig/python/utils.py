def file_get_contents(filename):
    with open(filename, 'r') as f:
        contents = f.read()
    return contents


def file_put_contents(filename, contents):
    with open(filename, 'w') as f:
        f.write(contents)
