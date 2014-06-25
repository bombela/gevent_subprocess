# -*- coding: utf-8 -*-
# Open Source Initiative OSI - The MIT License (MIT):Licensing
#
# The MIT License (MIT)
# Copyright (c) 2012 François-Xavier Bourlet (bombela@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# everything that we don't have to redefine!
from subprocess import \
    CalledProcessError, PIPE, STDOUT

# a way to access original subprocess
import subprocess as _subprocess

import os
import fcntl
import errno
import gevent
from gevent.socket import wait_read, wait_write


class Pipe(object):

    def __init__(self, fd, open_mode=None, bufsize=None):
        self._fd = fd
        self._closed = False
        self._readline_buffer = ''

        # we want the non-blocking behaviour
        flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
        fcntl.fcntl(self._fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def __del__(self):
        self.close()

    def close(self):
        if not self._closed:
            os.close(self._fd)
            self._closed = True

    @property
    def closed(self):
        return self._closed

    def fileno(self):
        return self._fd

    def write(self, data):
        while len(data) > 0:
            try:
                bytes_written = os.write(self._fd, data)
                data = data[bytes_written:]
            except OSError as e:
                if e.errno == errno.EPIPE:
                    self.close()
                    raise IOError(e)
                if e.errno != errno.EAGAIN:
                    raise
                wait_write(self._fd)

    def writelines(self, sequence):
        for line in sequence:
            self.write(line)

    def _read(self, size=-1, greedy=True):
        data = ''
        while size != 0:
            try:
                buffer = os.read(self._fd, size if size > 0 else 64 * 1024)
                bytes_read = len(buffer)
                if bytes_read == 0:
                    self.close()
                    break
                if size > 0:
                    size -= bytes_read
                data += buffer
                if size < 0 and not greedy:
                    break
            except OSError as e:
                if e.errno != errno.EAGAIN:
                    raise
                wait_read(self._fd)
        return data

    def read(self, size=-1, greedy=True):
        data = self._read(size, greedy)
        if len(self._readline_buffer) != 0:
            data = self._readline_buffer + data
            self._readline_buffer = ''
        return data

    def readline(self, size=-1):
        line_end = self._readline_buffer.find('\n')
        while line_end == -1 and not self.closed and \
                (size < 0 or len(self._readline_buffer) < size):
            data = self._read(greedy=False)
            self._readline_buffer += data
            line_end = self._readline_buffer.find('\n')

        if line_end == -1 or (size >= 0 and line_end >= size):
            if size < 0:
                line = self._readline_buffer
                self._readline_buffer = ''
            else:
                line = self._readline_buffer[0:size]
                self._readline_buffer = self._readline_buffer[size:]
        else:
            line = self._readline_buffer[0:line_end+1]
            self._readline_buffer = self._readline_buffer[line_end+1:]
        return line

    def readlines(self, sizehint=-1):  # allowed to ignore sizehint
        lines = []
        while True:
            line = self.readline()
            if len(line) == 0:
                break
            lines.append(line)
        return lines

    def next(self):
        return self.readline()


class _PopenWithAsyncPipe(_subprocess.Popen):
    def __init__(self, args, bufsize=0, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=False, shell=False,
                 cwd=None, env=None, universal_newlines=False,
                 startupinfo=None, creationflags=0):
        """Create new Popen instance."""
        _subprocess._cleanup()

        self._child_created = False
        if not isinstance(bufsize, (int, long)):
            raise TypeError("bufsize must be an integer")

        if _subprocess.mswindows:
            if preexec_fn is not None:
                raise ValueError("preexec_fn is not supported on Windows "
                                 "platforms")
            if close_fds and (stdin is not None or stdout is not None or
                              stderr is not None):
                raise ValueError("close_fds is not supported on Windows "
                                 "platforms if you redirect stdin/stdout/stderr")
        else:
            # POSIX
            if startupinfo is not None:
                raise ValueError("startupinfo is only supported on Windows "
                                 "platforms")
            if creationflags != 0:
                raise ValueError("creationflags is only supported on Windows "
                                 "platforms")

        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.pid = None
        self.returncode = None
        self.universal_newlines = universal_newlines

        # Input and output objects. The general principle is like
        # this:
        #
        # Parent                   Child
        # ------                   -----
        # p2cwrite   ---stdin--->  p2cread
        # c2pread    <--stdout---  c2pwrite
        # errread    <--stderr---  errwrite
        #
        # On POSIX, the child objects are file descriptors.  On
        # Windows, these are Windows file handles.  The parent objects
        # are file descriptors on both platforms.  The parent objects
        # are None when not using PIPEs. The child objects are None
        # when not redirecting.

        handles = self._get_handles(stdin, stdout, stderr)
        to_close = None

        if len(handles) == 2:
            (p2cread, p2cwrite,
             c2pread, c2pwrite,
             errread, errwrite), to_close = handles
        else:
            (p2cread, p2cwrite,
             c2pread, c2pwrite,
             errread, errwrite) = handles

        exec_kwargs = {
            "p2cread": p2cread,
            "p2cwrite": p2cwrite,
            "c2pread": c2pread,
            "c2pwrite": c2pwrite,
            "errread": errread,
            "errwrite": errwrite,
        }
        if to_close is not None:
            exec_kwargs["to_close"] = to_close

        self._execute_child(args, executable, preexec_fn, close_fds,
                            cwd, env, universal_newlines,
                            startupinfo, creationflags, shell, **exec_kwargs)

        if _subprocess.mswindows:
            if p2cwrite is not None:
                p2cwrite = _subprocess.msvcrt.open_osfhandle(p2cwrite.Detach(), 0)
            if c2pread is not None:
                c2pread = _subprocess.msvcrt.open_osfhandle(c2pread.Detach(), 0)
            if errread is not None:
                errread = _subprocess.msvcrt.open_osfhandle(errread.Detach(), 0)

        if p2cwrite is not None:
            self.stdin = Pipe(p2cwrite, 'wb', bufsize)
        if c2pread is not None:
            if universal_newlines:
                self.stdout = Pipe(c2pread, 'rU', bufsize)
            else:
                self.stdout = Pipe(c2pread, 'rb', bufsize)
        if errread is not None:
            if universal_newlines:
                self.stderr = Pipe(errread, 'rU', bufsize)
            else:
                self.stderr = Pipe(errread, 'rb', bufsize)


class Popen(object):

        def __init__(self, args, bufsize=0, executable=None, stdin=None,
            stdout=None, stderr=None, preexec_fn=None,
            close_fds=True,  # Like in Python 3.2, close_fds is now True by default.
            shell=False, cwd=None, env=None, universal_newlines=False,
            startupinfo=None, creationflags=0):

            self._process = _PopenWithAsyncPipe(args, bufsize, executable, stdin,
                    stdout, stderr, preexec_fn, close_fds, shell, cwd, env,
                    universal_newlines, startupinfo, creationflags)

        def _set_return_code(self, value):
            self._process.returncode = value

        @property
        def pid(self):
            return self._process.pid

        @property
        def returncode(self):
            return self._process.returncode

        def poll(self):
            return self._process.poll()

        def wait(self):
            sleep_duration = 0.01
            while True:
                r = self._process.poll()
                if r is not None:
                    return self.returncode
                gevent.sleep(sleep_duration)
                if sleep_duration < 0.5:
                    sleep_duration *= 2

        def send_signal(self, signal):
            self._process.send_signal(signal)

        def terminate(self):
            self._process.terminate()

        def kill(self):
            self._process.kill()

        @property
        def stdin(self):
            return self._process.stdin

        @property
        def stdout(self):
            return self._process.stdout

        @property
        def stderr(self):
            return self._process.stderr

        def communicate(self, input=None):
            if self.stdin is not None:
                def _writer():
                    self.stdin.write(input)
                    self.stdin.close()
                writer = gevent.spawn(_writer)

            if self.stdout is not None:
                reader_stdout = gevent.spawn(self.stdout.read)

            if self.stderr is not None:
                reader_stderr = gevent.spawn(self.stderr.read)

            stdoutdata = None
            if self.stdout is not None:
                stdoutdata = reader_stdout.get()

            stderrdata = None
            if self.stderr is not None:
                stderrdata = reader_stderr.get()

            if self.stdin:
                writer.get()

            self.wait()
            return (stdoutdata, stderrdata)


def call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete, then
    return the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    retcode = call(["ls", "-l"])
    """
    return Popen(*popenargs, **kwargs).wait()


def check_call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete.  If
    the exit code was zero then return, otherwise raise
    CalledProcessError.  The CalledProcessError object will have the
    return code in the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    check_call(["ls", "-l"])
    """
    retcode = call(*popenargs, **kwargs)
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd)
    return 0


def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.

    The arguments are the same as for the Popen constructor.  Example:

    >>> check_output(["ls", "-l", "/dev/null"])
    'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c",
    ...               "ls -l non_existent_file ; exit 0"],
    ...              stderr=STDOUT)
    'ls: non_existent_file: No such file or directory\n'
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = Popen(stdout=PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output=output)
    return output
