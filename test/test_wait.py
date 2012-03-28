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

from gevent_subprocess import subprocess
import gevent
from gevent.pool import Pool

def test_detect_kill():
    print 'spawn process...'
    p = subprocess.Popen('sleep 500'.split(' '), close_fds=True)

    def waiter():
        print 'Waiting...'
        assert p.wait() == -15
        print 'Done!'

    w = gevent.spawn(waiter)
    print 'kill it!'
    p.terminate()
    print 'wait after waiter...'
    w.join()
    print 'done!'

def test_lots_of_sleep():

    def coro():
        print 'spawn sleep 2...'
        p = subprocess.Popen('sleep 2'.split(' '), close_fds=True)
        print 'wait after sleep process, pid', p.pid
        r = p.wait()
        print 'done with return code:', r

    p = Pool()
    print 'spawn sleep processes...'
    for x in xrange(200):
        p.spawn(coro)
    print 'wait for completion...'
    p.join()
