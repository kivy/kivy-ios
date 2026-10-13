"""Toolchain recipe download output, without network access or Xcode."""
import io
import logging

import pytest

from kivy_ios import toolchain


URL = "https://example.com/source.zip"


class DownloadStream(io.StringIO):
    def __init__(self, interactive):
        super().__init__()
        self.interactive = interactive
        self.flushes = 0

    def isatty(self):
        return self.interactive

    def flush(self):
        self.flushes += 1
        super().flush()


@pytest.fixture
def download(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=toolchain.logger.name)
    monkeypatch.setattr(toolchain.urllib.request, "urlcleanup", lambda: None)
    return toolchain.Recipe().download_file


@pytest.mark.parametrize("size", [8192 * 1000, 0, -1])
def test_redirected_download_only_logs_start_and_success(download, monkeypatch, tmp_path, caplog, size):
    stream = DownloadStream(False)
    monkeypatch.setattr(toolchain, "stdout", stream)
    filename = tmp_path / "source.zip"
    filename.write_bytes(b"old archive")

    def retrieve(url, destination, reporthook):
        assert url == URL
        assert destination == str(filename)
        assert not filename.exists()
        # Simulate a large transfer if a progress callback is installed.
        for index in range(1001):
            if reporthook:
                reporthook(index, 8192, size)
        filename.write_bytes(b"new archive")

    monkeypatch.setattr(toolchain.urllib.request, "urlretrieve", retrieve)
    assert download(URL, "source.zip", cwd=str(tmp_path)) == str(filename)
    assert filename.read_bytes() == b"new archive"
    assert stream.getvalue() == ""
    assert stream.flushes == 0
    assert caplog.messages == ["Downloading " + URL, "Downloaded " + str(filename)]
    assert toolchain.url_opener.addheaders is toolchain.url_orig_headers


@pytest.mark.parametrize("size,progress", [
    (16384, ["0.00%", "50.00%", "100.00%"]),
    (0, ["0 bytes", "8192 bytes", "16384 bytes"]),
    (-1, ["0 bytes", "8192 bytes", "16384 bytes"]),
])
def test_terminal_keeps_every_progress_update_and_finishes_line(download, monkeypatch, tmp_path, caplog, size, progress):
    stream = DownloadStream(True)
    monkeypatch.setattr(toolchain, "stdout", stream)

    def retrieve(url, destination, reporthook):
        for index in range(3):
            reporthook(index, 8192, size)

    monkeypatch.setattr(toolchain.urllib.request, "urlretrieve", retrieve)
    filename = str(tmp_path / "source.zip")
    assert download(URL, filename) == filename
    assert stream.getvalue() == "".join("- Download {}\r".format(value) for value in progress) + "\n"
    assert stream.flushes == 4
    assert caplog.messages[-1] == "Downloaded " + filename


@pytest.mark.parametrize("interactive", [False, True])
@pytest.mark.parametrize("failures", [1, 5])
def test_retries_preserve_reporting_and_only_log_real_success(download, monkeypatch, tmp_path, caplog, interactive, failures):
    stream = DownloadStream(interactive)
    monkeypatch.setattr(toolchain, "stdout", stream)
    attempts = []
    sleeps = []
    error = OSError("incomplete transfer")

    def retrieve(url, destination, reporthook):
        attempts.append(destination)
        assert toolchain.url_opener.addheaders == [("User-agent", "Wget/1.0")]
        if reporthook:
            # Even a 100% estimate does not mean the transfer succeeded.
            reporthook(1, 8192, 8192)
        if len(attempts) <= failures:
            raise error

    def sleep(delay):
        sleeps.append(delay)
        assert toolchain.url_opener.addheaders is toolchain.url_orig_headers
        if interactive:
            assert stream.getvalue().endswith("\n")

    monkeypatch.setattr(toolchain.urllib.request, "urlretrieve", retrieve)
    monkeypatch.setattr(toolchain.time, "sleep", sleep)
    filename = str(tmp_path / "source.zip")
    if failures == 5:
        with pytest.raises(OSError) as raised:
            download(URL, filename)
        assert raised.value is error
        assert caplog.messages[-1] == "Max download attempts reached: 5"
        assert not any(message.startswith("Downloaded ") for message in caplog.messages)
    else:
        assert download(URL, filename) == filename
        assert caplog.messages[-1] == "Downloaded " + filename

    expected_attempts = min(failures + 1, 5)
    assert len(attempts) == expected_attempts
    assert sleeps == [1] * min(failures, 4)
    assert caplog.messages.count("Downloading " + URL) == 1
    assert caplog.messages.count("Download failed. Retrying in 1 second...") == len(sleeps)
    assert stream.getvalue() == ("- Download 100.00%\r\n" * expected_attempts if interactive else "")
    assert toolchain.url_opener.addheaders is toolchain.url_orig_headers


def test_unexpected_failure_also_finishes_terminal_line(download, monkeypatch, tmp_path, caplog):
    stream = DownloadStream(True)
    monkeypatch.setattr(toolchain, "stdout", stream)

    def retrieve(url, destination, reporthook):
        reporthook(0, 8192, -1)
        raise ValueError("unexpected failure")

    monkeypatch.setattr(toolchain.urllib.request, "urlretrieve", retrieve)
    with pytest.raises(ValueError, match="unexpected failure"):
        download(URL, str(tmp_path / "source.zip"))
    assert stream.getvalue() == "- Download 0 bytes\r\n"
    assert caplog.messages == ["Downloading " + URL]
    assert toolchain.url_opener.addheaders is toolchain.url_orig_headers
