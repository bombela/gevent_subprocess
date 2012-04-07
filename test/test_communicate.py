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

import gevent_subprocess as subprocess

def test_communicate():

    print 'spawn /bin/sh...'
    p = subprocess.Popen(['/bin/sh'], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print 'communicate...'
    stdout, stderr = p.communicate('''
echo COUCOU
ls /DONOTEXIST/FORREAL
ls -d /tmp
echo DONE
exit
''')
    print 'stdout --\n', stdout
    print 'stderr --\n', stderr
    assert stdout == 'COUCOU\n/tmp\nDONE\n'
    assert stderr == 'ls: cannot access /DONOTEXIST/FORREAL: No such file or directory\n'
    import gevent

def test_communicate_nostderr():

    print 'spawn /bin/sh...'
    p = subprocess.Popen(['/bin/sh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    print 'communicate...'
    stdout, stderr = p.communicate('''
echo COUCOU
ls /DONOTEXIST/FORREAL
ls -d /tmp
echo DONE
exit
''')
    print 'stdout --\n', stdout
    print 'stderr --\n', stderr
    assert stdout == 'COUCOU\n/tmp\nDONE\n'
    assert stderr is None

def test_communicate_onlystdin():

    print 'spawn /bin/sh...'
    p = subprocess.Popen(['/bin/cat'], stdin=subprocess.PIPE)

    print 'communicate...'
    stdout, stderr = p.communicate('''
HELLO
PARTY
PEOPLE!!!!
LETS ROOOOCK!!!!
''')
    print 'stdout --\n', stdout
    print 'stderr --\n', stderr
    assert stdout is None
    assert stderr is None

def test_communicate_nostdin():

    print 'spawn /bin/ls -d /tmp'
    p = subprocess.Popen('/bin/ls -d /tmp'.split(' '), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    print 'communicate...'
    stdout, stderr = p.communicate()
    print 'stdout --\n', stdout
    print 'stderr --\n', stderr
    assert stdout == '/tmp\n'
    assert stderr == ''
