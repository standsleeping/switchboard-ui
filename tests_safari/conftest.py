"""Fixtures for the real-Safari regression tests.

These exist because Safari is the one engine the Playwright suite cannot
contain: Playwright drives a bundled WebKit build, and the behaviours these
cases guard — back/forward-cache restoration above all — belong to Safari
proper. Apple's safaridriver is the only sanctioned way in, so the driver here
is Selenium rather than Playwright, pointed at the system Safari.

The fixture server and pages are the Playwright suite's own: the cases must
exercise the same shipped assembly, and a second copy of it could drift.

One driver serves the whole run because a Safari session costs seconds to
start. Isolation between cases still holds without any cleanup: every ``Site``
binds a fresh port, and web storage is scoped per origin, so a new server is a
clean slate.
"""

import contextlib
import sys
import time
from collections.abc import Iterator

import pytest
from selenium.webdriver import Safari
from tests_browser.conftest import site, slow_site  # noqa: F401  (fixtures)


@pytest.fixture(scope="session")
def safari() -> Iterator[Safari]:
    """A driven system Safari, or a skip that says why one is not available."""
    if sys.platform != "darwin":
        pytest.skip("real Safari exists only on macOS")
    try:
        driver = Safari()
    except Exception as error:
        pytest.skip(f"no safaridriver session ({error}); run: safaridriver --enable")
    # An explicit window size: on a CI runner the automation window's default
    # geometry is not a real screen's, and interactions against a degenerate
    # window fail in ways that read as the page's fault.
    driver.set_window_size(1280, 900)
    yield driver
    driver.quit()


def activate(driver: Safari, element: object) -> None:
    """Click an element, falling back to a script-dispatched activation.

    On hosted macOS runners safaridriver accepts a click and performs nothing:
    the session is healthy, the element is found, and no navigation or scroll
    follows. A script-dispatched click still runs the element's native
    activation behaviour — the navigation, the fragment jump — and skips only
    the synthesized input pipeline those runners drop. A machine whose input
    pipeline works never reaches the fallback, so locally the click stays
    real. The stale-element guard covers the click that was merely slow: if
    the document is already gone, the native click landed.
    """
    probe = "return location.href + '|' + window.scrollY"
    before = driver.execute_script(probe)
    element.click()  # type: ignore[attr-defined]
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if driver.execute_script(probe) != before:
            return
        time.sleep(0.05)
    with contextlib.suppress(Exception):
        driver.execute_script("arguments[0].click()", element)


def wait_until(driver: Safari, script: str, timeout: float = 5.0) -> None:
    """Poll a page-side expression until it is true, or fail with it named.

    The Selenium analogue of Playwright's ``wait_for_function``: restoration
    and placement land in frame callbacks, so a fixed-time read races them.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if driver.execute_script(f"return {script}"):
            return
        time.sleep(0.05)
    raise AssertionError(f"condition never became true: {script}")
