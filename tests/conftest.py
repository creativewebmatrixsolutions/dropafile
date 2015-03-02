import multiprocessing
import os
import pytest
import signal


class AbortCondition(object):

    def __init__(self, text='Running'):
        self.text = text

    def check_err(self, out, err):
        return self.text in err


def outerr_append(out, err, src):
    # append contents read by capsys.readouterr/capfd.readouterr to
    # out, err
    new_out, new_err = src.readouterr()
    if new_out:
        out += new_out
    if new_err:
        err += new_err
    return out, err


class SubprocessRunner(object):

    abort_when = AbortCondition().check_err

    def __init__(self, capfd):
        self.capfd = capfd

    def run(self, target, *args, **kw):
        # start target with parameters `args` and keywords `kw`.
        # Capture output with capfd and abort started process when
        # `abort_when` evaluates to ``True``.
        # `abort_when` must be a function accepting stdout and stderr
        # output.  If it returns ``True`` the target is terminated and
        # output returned.
        p1 = multiprocessing.Process(target=target, args=args, kwargs=kw)
        p1.start()
        timeout = 0.1
        out, err = ('', '')
        while timeout <= 103.0:  # abort after about 10 rounds
            p1.join(timeout)
            timeout *= 2
            out, err = outerr_append(out, err, self.capfd)
            if self.abort_when(out, err):
                break
        if p1.is_alive():
            # do not use p1.terminate() here, as only with SIGINT we get
            # coverage data from subprocess (terminate() sends SIGTERM).
            os.kill(p1.pid, signal.SIGINT)
            p1.join()
        out, err = outerr_append(out, err, self.capfd)
        return out, err


@pytest.fixture(scope="function")
def proc_runner(request, capfd):
    runner = SubprocessRunner(capfd)
    return runner
