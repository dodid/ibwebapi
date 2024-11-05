# IBWebAPI

## Overview

`ibwebapi` is a wrapper around the Interactive Brokers Web API that provides a RESTful interface for interacting with the IB Client Portal Gateway. It's a direct translation of the [IBKR Web API document](https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1) to Python. Not all endpoints are tested. The package serves as a starting point for further customization. It is intended for personal use and may not be suitable for production. Issues and pull requests are welcome, but no official support is provided.

## Features

- `IBClient` API for interacting with the IB Client Portal Gateway
- Launch IB Client Portal Gateway
- Automate login to IB Client Portal Gateway
- Log HTTP and Websocket requests and responses between the client and the IB Client Portal Gateway

## Installation

The package can be installed from source using `pip`:

```bash
$ git clone https://github.com/dodid/ibwebapi.git
$ cd ibwebapi
$ pip install .
```

## Environment Variables

The following environment variables may be set. Use `.env_template` for reference.

- `JAVA_PATH`: Path to the Java executable (default: `/usr/bin/java`)
- `IBGATEWAY_DIR`: Directory for IB Client Portal Gateway (default: `~/.ibgateway`)
- `IB_USERNAME`: IB account username
- `IB_PASSWORD`: IB account password
- `IB_PORT`: Port for IB Gateway (default: `5001`)
- `IB_LOG_PORT`: Port for IB Gateway with logging (default: `5002`)
- `AUTO_LOGIN`: Automatically login to IB Gateway (default: `False`)


## Launch IB Client Portal Gateway

To launch the IB Client Portal Gateway, run the following command. It will load `.env` file from current directory if it exists.

```bash
$ launch-ibgateway
```

## Usage

Here is an example of how to use the IBClient and IBWebSocketHandler:

```python
from ibwebapi import IBClient, IBWebSocketHandler

class WsHandler(IBWebSocketHandler):

    def handle_system_message(self, client: IBClient, message_info: dict) -> None:
        if "success" in message_info:
            client.ws_subscribe_market_data(265598, ["31", "84", "86"]) # AAPL

    def handle_market_data(self, client: IBClient, data: dict) -> None:
        print(data)

# Connect to IB Client Portal Gateway with logging, or use 5001 for no logging
ib = IBClient("localhost", 5002)

print(ib.get_account_summary())

ib.start_websocket(WsHandler())
```

## License

This project is licensed under the MIT License.
