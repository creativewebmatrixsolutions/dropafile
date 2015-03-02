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
    """Runs a passed in Python function (with args, kws).

    Desigend for use with server processes that must be aborted. After
    `run()` was called, we execute the passed in command, wait until
    we meet the abort condition evaluated by `abort_when(out, err)`
    and return the output.

    `abort_when` looks by default for string `Running` in stderr.
    """

    #: The condition to meet to abort a started server process
    abort_when = AbortCondition().check_err

    def __init__(self, capfd):
        self.capfd = capfd

    def run(self, target, *args, **kw):
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
