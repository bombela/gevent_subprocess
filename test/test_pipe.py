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

from gevent.pool import Pool
import gevent_subprocess as subprocess
from gevent.queue import Queue
import gevent
import os

from nose.tools import assert_raises

def pipe():
    return tuple(subprocess.Pipe(fd) for fd in os.pipe())

def test_small_data():
    pr, pw = pipe()

    def writer():
        print 'writing...'
        for x in xrange(1000):
            pw.write('hello')
        print 'writer bye bye'

    def reader():
        print 'reading...'
        data = ''
        for x in xrange(len('hello') * 1000):
            data += pr.read(1)
        assert len(data) == len('hello') * 1000
        assert data[:len('hello')] == 'hello'
        assert data[-len('hello'):] == 'hello'
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_big_data():
    pr, pw = pipe()

    big = 'x' * 1024 * 962
    big += 'END'
    print 'big data size', len(big)

    def writer():
        print 'writing...'
        pw.write(big)
        print 'writer bye bye'

    def reader():
        print 'reading...'
        data = ''
        for x in xrange(len(big) / 4096):
            data += pr.read(4096)
        data += pr.read(len(big) % 4096)
        assert len(data) == len(big)
        assert data[-3:] == 'END'
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_close_writer():
    pr, pw = pipe()

    big = 'x' * 1024 * 50
    print 'big data size', len(big)

    def writer():
        print 'writing, first round...'
        pw.write(big)
        print 'writing, second round...'
        pw.write(big)
        print 'writing, end tag...'
        pw.write('END')
        print 'writter close'
        pw.close()
        print 'writer bye bye'

    def reader():
        print 'reading all...'
        data = pr.read()
        assert len(data) == len(big) * 2 + 3
        assert data[-3:] == 'END'
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_close_read():
    pr, pw = pipe()

    big = 'x' * 1024 * 5000
    print 'big data size', len(big)

    def writer():
        print 'writing...'
        with assert_raises(IOError):
            pw.write(big)
        print 'writer bye bye'

    def reader():
        print 'reading a bit...'
        for x in xrange(250):
            pr.read(777)
        print 'reader close'
        pr.close()
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_readline():
    pr, pw = pipe()

    def writer():
        try:
            print 'writing lines...'
            while True:
                pw.write('hello\n')
        except IOError:
            pass
        print 'writer bye bye'

    def reader():
        print 'reading 23 lines...'
        for x in range(23):
            line = pr.readline()
            print line.strip()
            assert line == 'hello\n'
        print 'reader close'
        pr.close()
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_readline_eof_exact():
    pr, pw = pipe()

    def writer():
        try:
            print 'writing some lines...'
            for x in xrange(10):
                pw.write('hello\n')
        except IOError:
            pass
        print 'writer close'
        pw.close()
        print 'writer bye bye'

    def reader():
        print 'reading 10 lines...'
        for x in range(10):
            line = pr.readline()
            print line.strip()
            assert line == 'hello\n'
        print 'checking eof...'
        assert pr.readline() == ''
        assert pr.readline() == ''
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_readline_eof_halfline():
    pr, pw = pipe()

    def writer():
        try:
            print 'writing some lines...'
            for x in xrange(10):
                pw.write('hello\n')
            print 'plus an unfinished one...'
            pw.write('this line never finish...')
        except IOError:
            pass
        print 'writer close'
        pw.close()
        print 'writer bye bye'

    def reader():
        print 'reading 10 lines...'
        for x in range(10):
            line = pr.readline()
            print line.strip()
            assert line == 'hello\n'
        print 'checking last line...'
        line = pr.readline()
        print '<{0}>'.format(line)
        assert line == 'this line never finish...'
        print 'checking eof...'
        line = pr.readline()
        print '<{0}>'.format(line)
        assert line == ''
        line = pr.readline()
        print '<{0}>'.format(line)
        assert line == ''
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_readline_eof_halfline_memcheker():
    pr, pw = pipe()

    def writer():
        try:
            print 'writing some lines...'
            print 64 * 1034 / len('hello') * 3
            print (64 * 1034 / len('hello') * 3) * len('hello')
            for x in xrange(64 * 1034 / len('hello') * 3):
                pw.write('hello\n')
            print 'plus an unfinished one...'
            pw.write('this line never finish...')
        except IOError:
            pass
        print 'writer close'
        pw.close()
        print 'writer bye bye'

    def reader():
        print 'reading 10 lines...'
        for x in range(64 * 1034 / len('hello') * 3):
            line = pr.readline()
            assert line == 'hello\n'
        print 'checking last line...'
        line = pr.readline()
        print '<{0}>'.format(line)
        assert line == 'this line never finish...'
        print 'checking eof...'
        assert pr.readline() == ''
        assert pr.readline() == ''
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_readline_instant_eof():
    pr, pw = pipe()

    print 'writer close'
    pw.close()

    print 'checking eof...'
    assert pr.readline() == ''
    assert pr.readline() == ''

def test_readline_with_size():
    pr, pw = pipe()

    bigline = 'x' * 256 + 'a' * 256 + 'b' * 256 + 'y' * 256 + '\n'
    def writer():
        try:
            print 'writing some lines...'
            for x in xrange(1024):
                pw.write(bigline)
            print 'plus an unfinished one...'
            pw.write('this line never finish...')
        except IOError:
            pass
        print 'writer close'
        pw.close()
        print 'writer bye bye'

    def reader():
        print 'reading 10 lines...'
        for x in range(1024):
            line = pr.readline(512)
            assert line == bigline[0:512]
            line = pr.readline(513)
            assert line == bigline[512:]
        print 'checking last line...'
        line = pr.readline(5)
        print '<{0}>'.format(line)
        assert line == 'this '
        line = pr.readline(19)
        print '<{0}>'.format(line)
        assert line == 'line never finish..'
        line = pr.readline(1)
        print '<{0}>'.format(line)
        assert line == '.'
        print 'checking eof...'
        assert pr.readline() == ''
        assert pr.readline(0) == ''
        assert pr.readline(1) == ''
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_readline_size_zero():
    pr, pw = pipe()

    def writer():
        try:
            print 'writing lines...'
            while True:
                pw.write('hello\n')
        except IOError:
            pass
        print 'writer bye bye'

    def reader():
        print 'reading line of size 0...'
        assert pr.readline(0) == ''
        print 'reading line of size 1...'
        assert pr.readline(1) == 'h'
        print 'reading line normal...'
        assert pr.readline() == 'ello\n'
        print 'reader close'
        pr.close()
        print 'reader bye bye'

    p = Pool()
    p.spawn(reader)
    p.spawn(writer)
    p.join(raise_error=True)

def test_talking_with_sh():

    p = subprocess.Popen('sh', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    print 'shell pid', p.pid

    lines_to_write = Queue()
    def line_writer():
        for line in lines_to_write:
            print 'writing line', line
            p.stdin.write(line.strip() + '\n')
            print 'wrote   line', line
    writer = gevent.spawn(line_writer)

    lines_to_write.put('echo hello')

    print 'reading output...'
    line = p.stdout.readline().strip()
    print '>{0}<'.format(line)
    assert line == 'hello'

    lines_to_write.put('which ls')
    ls_bin = p.stdout.readline().strip()
    print '${0}$'.format(ls_bin)

    lines_to_write.put('ls -l /')
    lines_to_write.put('echo STOP_LS')

    line = '<>'
    while line != 'STOP_LS':
        line = p.stdout.readline().strip()
        print '>{0}<'.format(line)

    lines_to_write.put('exit 42')
    line = '<>'
    while line != '':
        line = p.stdout.readline().strip()
        print '>{0}<'.format(line)
    r = p.wait()
    print 'return_code of sh ->', r
    assert r == 42
    lines_to_write.put(StopIteration)
    writer.join()
    print 'All done cleanly'
