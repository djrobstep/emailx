import six

if six.PY3:
    unicode = str  # pragma: no cover


def listify(x):
    if is_textual(x):
        return x.split(',')
    else:
        return x


def is_textual(x):
    return isinstance(x, six.string_types) or isinstance(x, six.binary_type)


def to_text(x):
    if isinstance(x, six.text_type):
        return x

    elif isinstance(x, six.binary_type):
        return x.decode('utf-8')

    else:
        return unicode(x)


def to_bytes(x):
    if isinstance(x, six.text_type):
        return x.encode('utf-8')

    elif isinstance(x, six.binary_type):
        return x

    else:
        return unicode(x).encode('utf-8')


if six.PY3:
    to_str = to_text  # pragma: no cover
    from_str = to_bytes  # pragma: no cover
else:
    to_str = to_bytes  # pragma: no cover
    from_str = to_text  # pragma: no cover
