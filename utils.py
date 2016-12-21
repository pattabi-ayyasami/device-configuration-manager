


def read_file_as_lines(file_name):
    with open(file_name) as data_file:
        return data_file.readlines()

def read_file(file_name):
    with open(file_name) as data_file:
        data = data_file.read()
        return data

def write_to_file(data, file_name):
    with open(file_name, "wb") as text_file:
        text_file.write(data)


