

## EpicSplitter

1 chunks

#### Split 1
465 tokens, line: 1 - 69

```python
import os

from django.core.exceptions import SuspiciousFileOperation


def validate_file_name(name):
    if name != os.path.basename(name):
        raise SuspiciousFileOperation("File name '%s' includes path elements" % name)

    # Remove potentially dangerous names
    if name in {'', '.', '..'}:
        raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)

    return name


class FileProxyMixin:
    """
    A mixin class used to forward file methods to an underlaying file
    object.  The internal file object has to be called "file"::

        class FileProxy(FileProxyMixin):
            def __init__(self, file):
                self.file = file
    """

    encoding = property(lambda self: self.file.encoding)
    fileno = property(lambda self: self.file.fileno)
    flush = property(lambda self: self.file.flush)
    isatty = property(lambda self: self.file.isatty)
    newlines = property(lambda self: self.file.newlines)
    read = property(lambda self: self.file.read)
    readinto = property(lambda self: self.file.readinto)
    readline = property(lambda self: self.file.readline)
    readlines = property(lambda self: self.file.readlines)
    seek = property(lambda self: self.file.seek)
    tell = property(lambda self: self.file.tell)
    truncate = property(lambda self: self.file.truncate)
    write = property(lambda self: self.file.write)
    writelines = property(lambda self: self.file.writelines)

    @property
    def closed(self):
        return not self.file or self.file.closed

    def readable(self):
        if self.closed:
            return False
        if hasattr(self.file, 'readable'):
            return self.file.readable()
        return True

    def writable(self):
        if self.closed:
            return False
        if hasattr(self.file, 'writable'):
            return self.file.writable()
        return 'w' in getattr(self.file, 'mode', '')

    def seekable(self):
        if self.closed:
            return False
        if hasattr(self.file, 'seekable'):
            return self.file.seekable()
        return True

    def __iter__(self):
        return iter(self.file)
```
