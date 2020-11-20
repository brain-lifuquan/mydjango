import pandas


def read_csv(file):
    if hasattr(file, 'read'):
        return _read_file_like_csv(file)
    else:
        return _read_other_csv(file)


def _read_file_like_csv(file_like):
    try:
        file_like.seek(0)
        return pandas.read_csv(file_like, encoding='gbk', memory_map=True)
    except UnicodeDecodeError:
        file_like.seek(0)
        return pandas.read_csv(file_like, encoding='utf-8', memory_map=True)


def _read_other_csv(other_csv):
    try:
        return pandas.read_csv(other_csv, encoding='gbk')
    except UnicodeDecodeError:
        return pandas.read_csv(other_csv, encoding='utf-8')
