
import os
import signal
import subprocess
import sys
import threading
import time

import click
import requests
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .ibwebapi import IBClient
from .logging_proxy import start_proxy_server

load_dotenv(dotenv_path=os.path.join(os.path.curdir, '.env'))

global JAVA_PATH, IBGATEWAY_DIR, IB_USERNAME, IB_PASSWORD, IB_PORT, IB_LOG_PORT
JAVA_PATH = os.getenv("JAVA_PATH", "/usr/bin/java")
IBGATEWAY_DIR = os.path.expanduser(os.getenv("IBGATEWAY_DIR", os.path.expanduser('~/.ibgateway')))
IB_USERNAME = os.getenv("IB_USERNAME")
IB_PASSWORD = os.getenv("IB_PASSWORD")
IB_PORT = int(os.getenv("IB_PORT", 5000))
IB_LOG_PORT = int(os.getenv("IB_LOG_PORT", 5001))


def configure_logging(log_level: str):
    """Configure logging with the specified level."""
    logger.remove()
    logger.add(
        sink=sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level)


def launch_ibgateway():
    """Launch the IB Gateway and return the instance."""
    logger.info("Starting IB Client Portal Gateway...")

    cmd = [
        JAVA_PATH, '-server',
        '-Dvertx.disableDnsResolver=true',
        '-Djava.net.preferIPv4Stack=true',
        '-Dvertx.logger-delegate-factory-class-name=io.vertx.core.logging.SLF4JLogDelegateFactory',
        '-cp', 'root:dist/ibgroup.web.core.iblink.router.clientportal.gw.jar:build/lib/runtime/*',
        'ibgroup.web.core.clientportal.gw.GatewayStart', '--nossl', '--port', str(IB_PORT)
    ]

    try:
        proc = subprocess.Popen(cmd, cwd=IBGATEWAY_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.error(f"Failed to launch IB Client Portal Gateway: {e}")
        logger.error(f"Please check if the IB Client Portal Gateway is correctly installed in {IBGATEWAY_DIR}")
        sys.exit(1)

    logger.info(f"IB Gateway launched with PID {proc.pid} on port {IB_PORT}")

    # Log the output from the subprocess
    def log_subprocess_output():
        while True:
            output = proc.stdout.readline()
            if output == b"" and proc.poll() is not None:
                break
            if output:
                logger.info(f"[IB] {output.decode().strip()}")  # Added [Subprocess] flag

        # Log any error output
        while True:
            error_output = proc.stderr.readline()
            if error_output == b"" and proc.poll() is not None:
                break
            if error_output:
                logger.error(f"[IB] {error_output.decode().strip()}")  # Added [Subprocess] flag

    # Start a thread to log subprocess output
    output_thread = threading.Thread(target=log_subprocess_output, daemon=True)
    output_thread.start()

    time.sleep(1)  # Allow time for the process to start
    return proc.pid  # Return the process ID


def terminate_ibgateway(pid: int):
    """Terminate the IB Gateway process."""
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Terminated IB Gateway with PID {pid}")
        except OSError as e:
            logger.error(f"Error terminating IB Gateway: {e}")


def auto_login_ibgateway():
    """Automatically log in to the IB Gateway using Selenium."""
    root_url = f'http://localhost:{IB_PORT}'
    redirect_url = f'http://localhost:{IB_PORT}/sso/Dispatcher'

    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        logger.debug(f'{IB_USERNAME} loading {root_url}')
        driver.get(root_url)
        logger.debug(f'{IB_USERNAME} page loaded {driver.current_url}')

        # Fill in username and password
        driver.find_element(By.NAME, 'username').send_keys(IB_USERNAME)
        logger.debug(f'{IB_USERNAME} filled in username')
        driver.find_element(By.NAME, 'password').send_keys(IB_PASSWORD)
        logger.debug(f'{IB_USERNAME} filled in password')
        driver.find_element(By.CSS_SELECTOR, ".form-group:nth-child(1) > .btn").click()
        logger.debug(f'{IB_USERNAME} submitted login form')
        time.sleep(3)

        # Check for manual 2FA
        manual_2fa = False
        try:
            manual_2fa = driver.find_element(By.CSS_SELECTOR,
                                             '.text-center > .xyz-showchallenge > small').is_displayed()
        except Exception:
            logger.debug(f'{IB_USERNAME} no manual 2FA required.')

        logger.debug(f'{IB_USERNAME} manual 2FA = {manual_2fa}')

        if manual_2fa:
            driver.find_element(By.CSS_SELECTOR, ".text-center > .xyz-showchallenge > small").click()
            logger.debug(f'{IB_USERNAME} switched to logging in by challenge code')
            challenge_code = driver.find_element(By.CSS_SELECTOR, '.xyz-goldchallenge').text
            logger.debug(f'{IB_USERNAME} found challenge code: {challenge_code}')
            logger.info(f'Log in to "{IB_USERNAME}", challenge:\n{challenge_code}')

            challenge_response = input("Enter the challenge response: ").strip()

            if challenge_response:
                logger.debug(f'{IB_USERNAME} got challenge response: {challenge_response}')
                driver.find_element(By.NAME, "gold-response").send_keys(challenge_response)
                logger.debug(f'{IB_USERNAME} filled in challenge response')
                driver.find_element(By.CSS_SELECTOR, ".xyzform-gold .btn").click()
                logger.debug(f'{IB_USERNAME} submitted challenge response')
                WebDriverWait(driver, timeout=60).until(lambda d: d.current_url.startswith(redirect_url))
                logger.info(f'{IB_USERNAME} login succeeded')
        else:
            logger.info(f'{IB_USERNAME} login initiated')
            WebDriverWait(driver, timeout=60).until(lambda d: d.current_url.startswith(redirect_url))
            logger.info(f'{IB_USERNAME} login succeeded')

        # Initialize IbApi after successful login
        ib_api = IBClient(port=IB_PORT)

        # Check status after login
        for i in range(20):
            status = ib_api.get_auth_status()
            if status['authenticated'] and status['connected']:
                logger.info('Authentication succeeded')
                return status
            else:
                logger.debug(f'{IB_USERNAME} waiting for auth status to be ready ({i}s)')
                time.sleep(1)
        else:
            logger.info('Login timeout')
            raise RuntimeError(f'Gateway auth timeout for {IB_USERNAME}')
    finally:
        if driver:
            driver.close()
            driver.quit()


def status_checker():
    """Periodically check the IB Gateway status every 1 second and log the result."""
    ib_api = None
    while True:
        try:
            if not ib_api:
                ib_api = IBClient(port=IB_PORT)
            status = ib_api.get_auth_status()
            if status['authenticated'] and status['connected']:
                logger.debug(f"Gateway status: OK")
            else:
                logger.error(f"Gateway status: Incomplete, authenticated={status['authenticated']}, connected={status['connected']}")
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Gateway status: Unauthorized")
            else:
                logger.error(f"Failed to check gateway status: {e}")
        time.sleep(1)


@click.command()
@click.option('--log-level', default='INFO', help='Set the logging level (default: INFO)')
def main(log_level):
    configure_logging(log_level)

    pid = None
    try:
        proxy_thread = threading.Thread(
            target=start_proxy_server,
            kwargs={"local_port": IB_LOG_PORT, "remote_port": IB_PORT},
            daemon=True)
        proxy_thread.start()

        pid = launch_ibgateway()  # Launch IB Gateway on startup
        if os.getenv("AUTO_LOGIN", "false").lower() == "true":
            auto_login_ibgateway()  # Auto-login after launch
        else:
            root_url = f'http://localhost:{IB_PORT}'
            logger.warning(f"IB Client Portal Gateway launched. Please log in at {root_url}.")
            input(f'After you see "Client login succeeds", press Enter to continue...')

        # Start a separate thread for checking status
        status_thread = threading.Thread(target=status_checker, daemon=True)
        status_thread.start()

        # Main loop to keep the program running
        while True:
            input()

    except KeyboardInterrupt:
        logger.info("Terminating IB Gateway due to Ctrl+C...")
    finally:
        terminate_ibgateway(pid)  # Ensure IB Gateway is terminated on exit


if __name__ == "__main__":
    main()
