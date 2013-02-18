import gevent_subprocess as subprocess

Now you can use subprocess as usual, its fully gevent compliant and asynchronous :)

note:

This is useful only with gevent <1.0 (as I am writing this, on pypi you will
find gevent 0.13b something like that). The future release of gevent >=1.0, currently
in release candidate will include a subprocess adapation.
