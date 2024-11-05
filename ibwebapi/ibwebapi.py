import json

import requests
import urllib3
import websocket
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import json
from typing import Callable, Dict, Optional

from loguru import logger


class IBWebSocketHandler:
    def on_open(self, client: "IBClient") -> None:
        """Handle WebSocket opening event."""
        logger.debug("WebSocket opened.")

    def on_message(self, client: "IBClient", message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            data: dict = json.loads(message)
            logger.debug(f"Received message: \n{json.dumps(data, indent=4, default=str, sort_keys=True)}")

            topic: str = data.get("topic", "")

            # Map topics to their respective handler methods
            topic_handlers: Dict[str, Callable[[IBClient, dict], None]] = {
                "sld": self.handle_account_ledger,
                "smd": self.handle_market_data,
                "smh": self.handle_historical_data,
                "sts": self.handle_auth_status,
                "blt": self.handle_bulletin,
                "system": self.handle_system_message,
                "ntf": self.handle_notification,
                "sbd": self.handle_price_ladder_response,
                "shs+exercise": self.handle_exercise_response,
                "inp+exercise": self.handle_confirmation,
                "sor": self.handle_live_order_update,
                "spl": self.handle_profit_and_loss_update,
                "str": self.handle_trade_data_update,
                "act": self.handle_account_updates,
            }

            # Find and call the appropriate handler based on the topic
            handler: Optional[Callable[[IBClient, dict], None]] = next(
                (func for key, func in topic_handlers.items() if topic.startswith(key)),
                None
            )

            if handler:
                handler(client, data)  # Pass client to the handler
            else:
                logger.warning(f"Unhandled topic: {topic}")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message.")

    def on_error(self, client: "IBClient", error: Exception) -> None:
        """Handle WebSocket error events."""
        logger.exception("WebSocket error occurred:")

    def on_close(self, client: "IBClient", close_status_code: int, close_msg: str) -> None:
        """Handle WebSocket closing event."""
        logger.debug("WebSocket closed.")

    def handle_account_ledger(self, client: "IBClient", data: dict) -> None:
        """Handle account ledger updates."""
        pass

    def handle_auth_status(self, client: "IBClient", data: dict) -> None:
        """Handle authentication status updates."""
        pass

    def handle_bulletin(self, client: "IBClient", data: dict) -> None:
        """Handle bulletin messages."""
        pass

    def handle_system_message(self, client: "IBClient", data: dict) -> None:
        """Handle system messages."""
        pass

    def handle_notification(self, client: "IBClient", data: dict) -> None:
        """Handle notifications."""
        pass

    def handle_market_data(self, client: "IBClient", data: dict) -> None:
        """Handle market data updates."""
        pass

    def handle_historical_data(self, client: "IBClient", data: dict) -> None:
        """Handle historical data updates."""
        pass

    def handle_price_ladder_response(self, client: "IBClient", data: dict) -> None:
        """Handle price ladder responses."""
        pass

    def handle_exercise_response(self, client: "IBClient", data: dict) -> None:
        """Handle exercise responses."""
        pass

    def handle_confirmation(self, client: "IBClient", data: dict) -> None:
        """Handle confirmation messages."""
        pass

    def handle_live_order_update(self, client: "IBClient", data: dict) -> None:
        """Handle live order updates."""
        pass

    def handle_profit_and_loss_update(self, client: "IBClient", data: dict) -> None:
        """Handle profit and loss updates."""
        pass

    def handle_trade_data_update(self, client: "IBClient", data: dict) -> None:
        """Handle trade data updates."""
        pass

    def handle_account_updates(self, client: "IBClient", data: dict) -> None:
        """Handle account updates."""
        pass



class IBClient:
    def __init__(self, host: str = "localhost", port: int = 5002, ssl: bool = False) -> None:
        self.url = f"http{'s' if ssl else ''}://{host}:{port}/v1/api/"
        self.ssl = ssl
        self._account_id = None
        self.session_token = None
        self._ws = None

        try:
            status = self.get_auth_status()
            if status['authenticated'] and status['connected']:
                self._account_id = self.get_accounts()[0]["accountId"]
                logger.debug(f"Set account to {self.account_id}")
                self.session_token = self.tickle()["session"]
                logger.debug(f"WebSocket session token set: {self.session_token}")
            else:
                logger.warning("IB Gateway is not authenticated or connected.")
        except requests.exceptions.ConnectionError:
            logger.warning("IB Gateway is not running.")

    @property
    def account_id(self) -> str:
        if self._account_id is None:
            raise ValueError("The account_id has not been set.")
        return self._account_id

    @property
    def ws(self):
        """WebSocket property that raises an error if not initialized."""
        if self._ws is None:
            raise ValueError("WebSocket connection is not active.")
        return self._ws

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.url}{endpoint}"
        response = requests.request(method, url, verify=self.ssl, **kwargs)
        response.raise_for_status()
        return response.json()

    def ws_subscribe_account_summary(self, keys: list[str] = None, fields: list[str] = None):
        """Subscribes to account summary data for a specified account."""
        msg = {
            "keys": keys or [],
            "fields": fields or []
        }
        subscription_message = f"ssd+{self.account_id}+{json.dumps(msg)}"
        self.ws.send(subscription_message)
        logger.debug(f"Subscribed to account summary for account ID: {self.account_id}")

    def ws_unsubscribe_account_summary(self):
        """Unsubscribes from account summary data for a specified account."""
        unsubscribe_message = f"usd+{self.account_id}+{{}}"
        self.ws.send(unsubscribe_message)
        logger.debug(f"Unsubscribed from account summary for account ID: {self.account_id}")

    def ws_subscribe_account_ledger(self, keys: list[str] = None, fields: list[str] = None):
        """Subscribes to account ledger data for a specified account."""
        msg = {
            "keys": keys or [],
            "fields": fields or []
        }
        subscription_message = f"sld+{self.account_id}+{json.dumps(msg)}"
        self.ws.send(subscription_message)
        logger.debug(f"Subscribed to account ledger for account ID: {self.account_id}")

    def ws_unsubscribe_account_ledger(self):
        """Unsubscribes from account ledger data for a specified account."""
        unsubscribe_message = f"uld+{self.account_id}+{{}}"
        self.ws.send(unsubscribe_message)
        logger.debug(f"Unsubscribed from account ledger for account ID: {self.account_id}")

    def ws_subscribe_market_data(self, conid: str, fields: list[str] = None):
        """Subscribes to market data for a specific contract (conid)."""
        msg = {
            "fields": fields or []
        }
        subscription_message = f"smd+{conid}+{json.dumps(msg)}"
        self.ws.send(subscription_message)
        logger.debug(f"Subscribed to market data for conid: {conid}")

    def ws_unsubscribe_market_data(self, conid: str):
        """Unsubscribes from market data for a specific contract (conid)."""
        unsubscribe_message = f"umd+{conid}+{{}}"
        self.ws.send(unsubscribe_message)
        logger.debug(f"Unsubscribed from market data for conid: {conid}")

    def ws_subscribe_historical_data(self, conid: str, exchange: str = "SMART", period: str = "30d",
                                      bar: str = "1d", outside_rth: bool = False,
                                      source: str = "trades", format: str = "%o"):
        """Subscribes to historical market data for a specific contract (conid)."""
        params = {
            "exchange": exchange,
            "period": period,
            "bar": bar,
            "outsideRth": outside_rth,
            "source": source,
            "format": format
        }
        subscription_message = f"smh+{conid}+{json.dumps(params)}"
        self.ws.send(subscription_message)
        logger.debug(f"Subscribed to historical market data for conid: {conid}, period: {period}, bar: {bar}")

    def ws_unsubscribe_historical_data(self, server_id: str):
        """Unsubscribes from historical market data for the given server_id."""
        unsubscribe_message = f"umh+{server_id}"
        self.ws.send(unsubscribe_message)
        logger.debug(f"Unsubscribed from historical market data with server_id: {server_id}")

    def ws_subscribe_price_ladder(self, conid: str, exchange: str = None):
        """Subscribes to BookTrader price ladder data for a specific account and contract (conid)."""
        topic = f"sbd+{self.account_id}+{conid}"
        if exchange:
            topic += f"+{exchange}"

        self.ws.send(topic)
        logger.debug(f"Subscribed to price ladder data for acct_id: {self.account_id}, conid: {conid}, exchange: {exchange}")

    def ws_unsubscribe_price_ladder(self):
        """Unsubscribes from BookTrader price ladder data for the given account ID."""
        unsubscribe_message = f"ubd+{self.account_id}"
        self.ws.send(unsubscribe_message)
        logger.debug(f"Unsubscribed from price ladder data for acct_id: {self.account_id}")

    def ws_initiate_option_exercise(self, option_conid: str):
        """Initiates the option exercise process by sending a handshake request."""
        message = f'shs+exercise+{{"CEX":"{option_conid}"}}'
        self.ws.send(message)
        logger.debug(f"Initiated option exercise for conid: {option_conid}")

    def ws_submit_exercise(self, exercise_id: str, quantity: int, make_final: bool = True):
        """Submits the exercise request."""
        message = f'inp+exercise+{{"action":"user_input","data":{{"id":"{exercise_id}","user_action":"submit","exercise":{{"make_final":{str(make_final).lower()},"value":{quantity}}}}}}}'
        self.ws.send(message)
        logger.debug(f"Submitted exercise request for {quantity} options with ID: {exercise_id}")

    def ws_continue_exercise(self, prompt_id: str):
        """Continues the exercise process after receiving a warning or confirmation prompt."""
        message = f'inp+exercise+{{"action":"user_input","data":{{"id":"{prompt_id}","user_action":"continue"}}}}'
        self.ws.send(message)
        logger.debug(f"Continued exercise process for prompt ID: {prompt_id}")

    def ws_ping_session(self):
        """Pings the WebSocket session to keep it alive."""
        ping_message = "tic"
        self.ws.send(ping_message)
        logger.debug("Pinged the WebSocket session to keep it alive.")

    def ws_subscribe_live_orders(self):
        """Subscribes to live order updates."""
        subscribe_message = "sor+{}"
        self.ws.send(subscribe_message)
        logger.debug("Subscribed to live order updates.")

    def ws_unsubscribe_live_orders(self):
        """Cancels the subscription for live order updates."""
        unsubscribe_message = "uor+{}"
        self.ws.send(unsubscribe_message)
        logger.debug("Unsubscribed from live order updates.")

    def ws_subscribe_profit_loss(self):
        """Subscribes to live profit and loss information."""
        subscribe_message = "spl+{}"
        self.ws.send(subscribe_message)
        logger.debug("Subscribed to live profit and loss information.")

    def ws_unsubscribe_profit_loss(self):
        """Cancels the subscription for profit and loss updates."""
        unsubscribe_message = "upl+{}"
        self.ws.send(unsubscribe_message)
        logger.debug("Unsubscribed from profit and loss updates.")

    def ws_request_trades_data(self, realtime_updates_only: bool = False, days: int = 1):
        """Subscribes to trades data, returning all executions data while streamed."""
        request_message = f"trd+{{\"realtimeUpdatesOnly\":{realtime_updates_only},\"days\":{days}}}"
        self.ws.send(request_message)
        logger.debug("Subscribed to trades data with realtimeUpdatesOnly=%s and days=%d", realtime_updates_only, days)

    def ws_cancel_trades_data(self):
        """Cancels the trades data subscription."""
        cancel_message = "utr"
        self.ws.send(cancel_message)
        logger.debug("Cancelled trades data subscription.")

    def start_websocket(self, handler: IBWebSocketHandler):
        """
        Start the WebSocket client, using an external object for callback functions.

        Args:
        - handler: An object that provides on_open, on_message, on_error, and on_close functions.
        """
        ws_url = self.url.replace("http", "ws").rstrip("/") + "/ws"

        # Create the WebSocket app with inlined callback functions
        self._ws = websocket.WebSocketApp(
            url=ws_url,
            on_open=lambda ws: handler.on_open(self),
            on_message=lambda ws, message: handler.on_message(self, message),
            on_error=lambda ws, error: handler.on_error(self, error),
            on_close=lambda ws, close_status_code, close_msg: handler.on_close(self, close_status_code, close_msg),
            cookie=f"api={self.session_token}"
        )
        self._ws.run_forever()

    def stop_websocket(self):
        """Closes the WebSocket connection if it is active."""
        if self._ws is not None:
            self._ws.close()
            logger.debug("WebSocket connection closed.")
            self._ws = None  # Reset the ws property to None
        else:
            logger.warning("No active WebSocket connection to close.")

    def tickle(self) -> dict:
        """
        Ping the server to keep the session alive.

        This endpoint should be called approximately every 60 seconds
        to maintain the connection to the brokerage session. If the gateway
        has not received any requests for several minutes, the open session
        will automatically timeout.

        Returns:
            dict: Information about the server's response.

            Example return value:
            {
                "session": "bb665d0f55b6289d70bc7380089fc96f",
                "ssoExpires": 460311,
                "collission": false,
                "userId": 123456789,
                "hmds": {
                    "error": "no bridge"
                },
                "iserver": {
                    "authStatus": {
                        "authenticated": true,
                        "competing": false,
                        "connected": true,
                        "message": "",
                        "MAC": "98:F2:B3:23:BF:A0",
                        "serverInfo": {
                            "serverName": "JifN19053",
                            "serverVersion": "Build 10.25.0p, Dec 5, 2023 5:48:12 PM"
                        }
                    }
                }
            }

        Raises:
            HTTPError: If the API request fails with a status code of 401 (Unauthorized) or other errors.
        """
        return self._request("POST", "tickle")

    def switch_account(self, acct_id: str | None = None) -> dict:
        """
        Switch the active account for how you request data.
        This method is only available for financial advisors and multi-account structures.

        Args:
        - acct_id (str | None): Identifier for the unique account to retrieve information from. If None, the first
            account from `get_accounts()` will be selected. (optional)
            Example: "U1234567"

        Returns:
        - dict: A response indicating whether the account has been successfully switched.

        Example return value:
        {
            "set": true,
            "acctId": "U2234567"
        }
        """
        request_body = {"acctId": acct_id or self.get_accounts()[0]["accountId"]}
        result = self._request("POST", "iserver/account", json=request_body)
        self._account_id = acct_id or self.get_accounts()[0]["accountId"]
        self.session_token = self.tickle()["session"]
        logger.debug(f"WebSocket session token set: {self.session_token}")
        logger.debug(f"Switched account to {self._account_id}")
        return result

    def get_signatures_and_owners(self) -> dict:
        """
        Retrieve a list of all applicant names on the account, along with the account and entity representation.

        Args:
            accountId (str): The account identifier to fetch information for.

        Returns:
            dict: An object containing account details, including users and their roles, and signature information.
                  Example:
                  {
                    "accountId": "U1234567",
                    "users": [
                        {
                            "roleId": "OWNER",
                            "hasRightCodeInd": True,
                            "entity": {
                                "entityType": "INDIVIDUAL",
                                "entityName": "John Smith",
                                "firstName": "John",
                                "lastName": "Smith"
                            }
                        }
                    ],
                    "applicant": {
                        "signatures": ["John Smith"]
                    }
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.

        Raises:
            ValueError: If the accountId is empty or None.

        """
        endpoint = f"acesws/{self.account_id}/signatures-and-owners"
        return self._request("GET", endpoint)

    def get_delivery_options(self) -> dict:
        """
        Retrieve options for sending FYIs (For Your Information) to email and other devices.

        Returns:
            dict: A dictionary containing available delivery options for FYIs.
                  Example:
                  {
                    "E": [
                        {
                            "NM": "iPhone",
                            "I": "apn://mtws@SDFSDFDSFS123123DSFSDF",
                            "UI": "apn://mtws@SDFSDFDSFS123123DSFSDF",
                            "A": 1
                        }
                    ],
                    "M": 1
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "fyi/deliveryoptions"
        return self._request("GET", endpoint)

    def enable_disable_device_option(self, device_option: dict) -> dict:
        """
        Choose whether a particular device is enabled or disabled.

        Args:
            device_option (dict): A dictionary specifying the device option to enable or disable.
                                  Example structure:
                                  {
                                      "deviceId": "iPhone",
                                      "enabled": true
                                  }

        Returns:
            dict: A dictionary confirming the update of the device option.
                  Example:
                  {
                    "status": "success",
                    "deviceId": "iPhone",
                    "enabled": true
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If device_option is empty or not provided.
        """
        if not device_option:
            raise ValueError("device_option is required and cannot be empty.")

        endpoint = "fyi/deliveryoptions/device"
        return self._request("POST", endpoint, json=device_option)

    def enable_disable_email_option(self, enabled: bool) -> dict:
        """
        Enable or disable your account’s primary email to receive notifications.

        Args:
            enabled (bool): Specify whether to enable (True) or disable (False) email notifications.

        Returns:
            dict: A dictionary confirming the update of the email notification option.
                  Example:
                  {
                      "V": 1,
                      "T": 10
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If the enabled parameter is not provided.
        """
        if enabled is None:
            raise ValueError("The 'enabled' parameter is required.")

        endpoint = "fyi/deliveryoptions/email"
        params = {"enabled": enabled}
        return self._request("PUT", endpoint, params=params)

    def delete_device(self, device_id: str) -> None:
        """
        Delete a specific device from the saved list of notification devices.

        Args:
            device_id (str): The identifier of the device to delete from IB’s saved list.
                              This ID can be retrieved from the /fyi/deliveryoptions endpoint.

        Returns:
            None: This method returns no content; a successful deletion will result in an empty response with a 200 status code.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If the device_id parameter is not provided or is empty.
        """
        if not device_id:
            raise ValueError("The 'device_id' parameter is required and cannot be empty.")

        endpoint = f"fyi/deliveryoptions/{device_id}"
        self._request("DELETE", endpoint)

    def get_disclaimer(self, typecode: str) -> dict:
        """
        Get disclaimer for a certain kind of FYI.

        Args:
            typecode (str): The typecode for which the disclaimer is requested.

        Returns:
            dict: A dictionary containing the disclaimer details. Example return value:
                  {
                      "DT": "This communication is provided for information purposes only and is not a recommendation or a solicitation to buy, sell or hold any investment product. Selling securities short involves significant risk and you may lose more than you invest.",
                      "FC": "BA"
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If the typecode parameter is not provided or is empty.
        """
        if not typecode:
            raise ValueError("The 'typecode' parameter is required and cannot be empty.")

        endpoint = f"fyi/disclaimer/{typecode}"
        return self._request("GET", endpoint)

    def mark_disclaimer_read(self, typecode: str) -> dict:
        """
        Mark a specific disclaimer message as read.

        Args:
            typecode (str): The typecode of the disclaimer to mark as read.

        Returns:
            dict: A dictionary confirming the disclaimer has been marked as read. Example return value:
                  {
                      "V": 1,
                      "T": 10
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If the typecode parameter is not provided or is empty.
        """
        if not typecode:
            raise ValueError("The 'typecode' parameter is required and cannot be empty.")

        endpoint = f"fyi/disclaimer/{typecode}"
        return self._request("PUT", endpoint)

    def get_notifications(self, max: int, include: str = None, exclude: str = None, id: str = None) -> list:
        """
        Get a list of available notifications.

        Args:
            max (int): Specify the maximum number of notifications to receive (maximum of 10).
            include (str, optional): Specify any additional filters for notifications to include.
            exclude (str, optional): Specify any filters for notifications to exclude.
            id (str, optional): Notification ID to define the next batch border.

        Returns:
            list: A list of notifications. Example return value:
                   [
                       {
                           "R": 0,
                           "D": "1710847062.0",
                           "MS": "FYI: Changes in Analyst Ratings",
                           "MD": "<html>Some investors use analysts ratings...</html>",
                           "ID": "2024031947509444",
                           "HT": 0,
                           "FC": "PF"
                       },
                       ...
                   ]

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If the max parameter is not provided or exceeds the limit.
        """
        if max <= 0 or max > 10:
            raise ValueError("The 'max' parameter must be a positive integer and cannot exceed 10.")

        params = {
            "max": max,
            "include": include,
            "exclude": exclude,
            "id": id
        }

        endpoint = "fyi/notifications"
        return self._request("GET", endpoint, params=params)

    def mark_notification_read(self, notification_id: str) -> dict:
        """
        Mark a particular notification message as read or unread.

        Args:
            notification_id (str): The ID of the notification to mark.
                                    Value received from /fyi/notifications.

        Returns:
            dict: Acknowledgment of the action. Example return value:
                  {
                      "V": 1,
                      "T": 5,
                      "P": {
                          "R": 1,
                          "ID": "2024031947509444"
                      }
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
            ValueError: If the notification_id is not provided.
        """
        if not notification_id:
            raise ValueError("The 'notification_id' parameter must be provided.")

        endpoint = f"fyi/notifications/{notification_id}"
        return self._request("PUT", endpoint)

    def get_notification_settings(self) -> list:
        """
        Get the current choices of subscriptions for notifications.

        Returns:
            list: The notification settings. Example return value:
                  [
                      {
                          "FC": "PF",
                          "H": 0,
                          "A": 1,
                          "FD": "Notify me of recent activity affecting my portfolio holdings.",
                          "FN": "Portfolio FYIs"
                      },
                      {
                          "FC": "PT",
                          "H": 0,
                          "A": 1,
                          "FD": "Notify me of potential account configuration changes needed and useful features based on my position transfers.",
                          "FN": "Position Transfer"
                      }
                  ]

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "fyi/settings"
        return self._request("GET", endpoint)

    def modify_fyi_notifications(self, typecode: str, enabled: bool) -> dict:
        """
        Enable or disable a group of notifications by the specific typecode.

        Args:
            typecode (str): The code representing the group of notifications to modify.
            enabled (bool): Indicates whether the notification should be enabled or disabled.

        Returns:
            dict: The response indicating the result of the modification. Example return value:
                  {
                      "V": 1,
                      "T": 10
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = f"fyi/settings/{typecode}"
        request_body = {"enabled": enabled}
        return self._request("POST", endpoint, json=request_body)

    def get_unread_notifications(self) -> dict:
        """
        Returns the total number of unread notifications.

        Returns:
            dict: A dictionary containing the number of unread bulletins. Example return value:
                  {
                      "BN": 4
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "fyi/unreadnumber"
        return self._request("GET", endpoint)

    def retrieve_processed_application(self, external_id: str = None) -> dict:
        """
        Retrieve the application request and IBKR response data based on IBKR accountId or externalId.
        Only available for accounts that originate via API.

        Args:
            external_id (str, optional): The external ID associated with the account. Defaults to None.

        Returns:
            dict: A dictionary containing the application request and IBKR response data. Example return value:
                  {
                      "fileDetails": {
                          "fileId": "12345",
                          "status": "processed"
                      }
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/accounts"
        params = {}
        if external_id:
            params["external_id"] = external_id
        else:
            params["account_id"] = self.account_id

        return self._request("GET", endpoint, params=params)

    def create_account(self, application_payload: dict) -> dict:
        """
        Submit account application to create a brokerage account for the end user.

        Args:
            application_payload (dict): The application details to create the account.

        Returns:
            dict: A dictionary indicating the result of the application submission. Example return value:
                  {
                      "status": "success",
                      "message": "Account application submitted successfully."
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/accounts"
        headers = {"Content-Type": "application/jwt"}
        return self._request("POST", endpoint, headers=headers, json=application_payload)

    def update_account(self, account_management_payload: dict) -> dict:
        """
        Update information for an existing accountId.

        Args:
            account_management_payload (dict): The updated account details.

        Returns:
            dict: A dictionary indicating the result of the update operation. Example return value:
                  {
                      "status": "success",
                      "message": "Account updated successfully."
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/accounts"
        headers = {"Content-Type": "application/jwt"}
        return self._request("PATCH", endpoint, headers=headers, json=account_management_payload)

    def close_account(self, client_id: str, instruction: dict) -> dict:
        """
        Submit a request to close an account that is opened.

        Args:
            client_id (str): The client ID for the instruction.
            instruction (dict): The details for closing the account, including:
                - instructionType (str): Must be "ACCOUNT_CLOSE".
                - instruction (dict): Contains the following fields:
                    - clientInstructionId (str): Unique ID for the instruction.
                    - accountId (str): The account ID to be closed.
                    - closeReason (str): Reason for closing the account.
                    - withdrawalInfo (dict, optional): Information for withdrawal (if applicable).

        Returns:
            dict: A dictionary containing the result of the account closure request. Example return value:
                  {
                      "instructionResult": {
                          "clientInstructionId": 1013031,
                          "instructionType": "ACCOUNT_CLOSE",
                          "instructionStatus": "PENDING",
                          "instructionId": 43091814
                      },
                      "instructionSetId": 1703,
                      "status": 202
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/accounts/close"
        headers = {"Content-Type": "application/json"}
        payload = {
            "instructionType": "ACCOUNT_CLOSE",
            "instruction": instruction
        }
        return self._request("POST", endpoint, headers=headers, json=payload)

    def get_login_messages(self, login_message_request: dict) -> dict:
        """
        Query all accounts associated with the Client ID that have incomplete login messages.

        Args:
            login_message_request (dict): Request parameters to filter login messages. Must contain:
                - clientId (str): The Client ID for which to query login messages.

        Returns:
            dict: A dictionary containing the login messages associated with the specified Client ID. Example return value:
                  {
                      "messages": [
                          {
                              "accountId": "U46377",
                              "loginMessage": "Your account is inactive. Please contact support.",
                              "timestamp": "2024-10-22T12:34:56Z"
                          }
                      ]
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/accounts/login-messages"
        params = {"loginMessageRequest": login_message_request}
        return self._request("GET", endpoint, params=params)

    def get_account_status(self, account_status_request: dict) -> dict:
        """
        Query status of all accounts associated with the Client ID.

        Args:
            account_status_request (dict): Request parameters to filter account status. Must contain:
                - clientId (str): The Client ID for which to query account status.

        Returns:
            dict: A dictionary containing the status of all accounts associated with the specified Client ID. Example return value:
                  {
                      "accounts": [
                          {
                              "accountId": "U46377",
                              "status": "ACTIVE",
                              "lastUpdated": "2024-10-22T12:34:56Z"
                          }
                      ]
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/accounts/status"
        params = {"accountStatusRequest": account_status_request}
        return self._request("GET", endpoint, params=params)

    def get_account_details(self) -> dict:
        """
        View information associated with a specific account, including contact data,
        financial information, and trading configuration.

        Returns:
            dict: A dictionary containing detailed information about the account. Example return value:
                  {
                      "accountId": "U46377",
                      "contactData": {
                          "email": "user@example.com",
                          "phone": "123-456-7890"
                      },
                      "financialInformation": {
                          "balance": 10000.00,
                          "currency": "USD"
                      },
                      "tradingConfiguration": {
                          "leverage": 2,
                          "marginCall": true
                      }
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = f"gw/api/v1/accounts/{self.account_id}/details"
        return self._request("GET", endpoint)

    def get_kyc_url(self) -> dict:
        """
        Generate a URL address to complete real-time KYC verification using Au10Tix.

        Returns:
            dict: A dictionary containing the KYC URL. Example return value:
                  {
                      "kycUrl": "https://kyc.au10tix.com/verify?id=abc123"
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = f"gw/api/v1/accounts/{self.account_id}/kyc"
        return self._request("GET", endpoint)

    def get_login_messages(self, message_type: str = None) -> dict:
        """
        Query login messages assigned by accountId.

        Args:
            message_type (str, optional): The type of message to filter by. Defaults to None.

        Returns:
            dict: A dictionary containing the login messages. Example return value:
                  {
                      "messages": [
                          {
                              "id": "msg1",
                              "content": "Your login was successful.",
                              "timestamp": "2024-10-22T10:00:00Z"
                          },
                          {
                              "id": "msg2",
                              "content": "Please verify your email.",
                              "timestamp": "2024-10-22T10:05:00Z"
                          }
                      ]
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = f"gw/api/v1/accounts/{self.account_id}/login-messages"
        params = {"type": message_type} if message_type else {}
        return self._request("GET", endpoint, params=params)

    def get_account_status(self) -> dict:
        """
        Query status of account by accountId.

        Returns:
            dict: A dictionary containing the account status. Example return value:
                  {
                      "status": "active",
                      "lastUpdated": "2024-10-22T10:00:00Z",
                      "details": {
                          "balance": 10000.00,
                          "currency": "USD",
                          "accountType": "individual"
                      }
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = f"gw/api/v1/accounts/{self.account_id}/status"
        return self._request("GET", endpoint)

    def get_registration_tasks(self, task_type: str = None) -> dict:
        """
        Query registration tasks assigned to account and pending tasks required for account approval.

        Args:
            task_type (str, optional): The type of tasks to filter by. Can be 'pending' or 'registration'. Defaults to None.

        Returns:
            dict: A dictionary containing the registration tasks or pending tasks. Example return value:
                  {
                      "tasks": [
                          {
                              "id": "task1",
                              "type": "pending",
                              "description": "Complete identity verification",
                              "status": "in_progress"
                          },
                          {
                              "id": "task2",
                              "type": "registration",
                              "description": "Provide proof of address",
                              "status": "pending"
                          }
                      ]
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = f"gw/api/v1/accounts/{self.account_id}/tasks"
        params = {"type": task_type} if task_type else {}
        return self._request("GET", endpoint, params=params)

    def manage_bank_instructions(self, instruction_type: str, instruction: dict) -> dict:
        """
        Create or delete bank instructions by accountId. Only ACH and EDDA are supported for 'Create'.

        Args:
            instruction_type (str): The type of bank instruction. Must be one of:
                - 'ACH_INSTRUCTION'
                - 'TRADITIONAL_BANK_INSTRUCTION_VERIFICATION'
                - 'DELETE_BANK_INSTRUCTION'
                - 'PREDEFINED_DESTINATION_INSTRUCTION'
                - 'EDDA_INSTRUCTION'
            instruction (dict): The bank instruction details based on the instruction type. Example:
                {
                    "clientInstructionId": "1012983",
                    "bankInstructionCode": "ACHUS",
                    "achType": "DEBIT_CREDIT",
                    "bankInstructionName": "TestInstr",
                    "currency": "USD",
                    "accountId": "U223454",
                    "clientAccountInfo": {
                        "bankRoutingNumber": "202012983",
                        "bankAccountNumber": "101267576983",
                        "bankName": "JPM Chase",
                        "bankAccountTypeCode": 999
                    }
                }

        Returns:
            dict: A dictionary containing the result of the instruction. Example return value:
                  {
                      "instructionResult": {
                          "clientInstructionId": 80009,
                          "instructionType": "ACH_INSTRUCTION",
                          "instructionStatus": "PENDING",
                          "instructionId": 43092478
                      },
                      "instructionSetId": 2487,
                      "status": 202
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails with an error status code.
        """
        endpoint = "gw/api/v1/bank-instructions"
        body = {
            "instructionType": instruction_type,
            "instruction": instruction
        }
        return self._request("POST", endpoint, json=body)

    def query_bank_instructions(self, client_id: str, request_body: dict) -> dict:
        """
        View active bank instructions for a given accountId.

        Parameters:
            client_id (str): The client ID associated with the bank instructions.
            request_body (dict): The request body containing the instruction type and instruction details.
                Should include:
                - instructionType (str): Type of instruction (e.g., "QUERY_BANK_INSTRUCTION").
                - instruction (dict): Instruction details according to the specified type.

        Returns:
            dict: The response containing the results of the query.
                Example response:
                {
                    "instructionResult": {
                        "accountId": "U46377",
                        "bankInstructionMethod": "WIRE",
                        "instructionDetails": [
                            {"bankInstructionName": "testCitadele", "type": "FOREIGN_BANK", "currency": "USD"},
                            ...
                        ],
                        "instructionStatus": "PROCESSED",
                        "instructionId": 43094187
                    },
                    "instructionSetId": 3771,
                    "status": 201
                }

        Raises:
            HTTPError: If the request to the API fails.
        """
        endpoint = "gw/api/v1/bank-instructions/query"
        headers = {"Content-Type": "application/json"}
        data = {
            "clientId": client_id,
            **request_body
        }
        return self._request("POST", endpoint, headers=headers, json=data)

    def get_client_instruction_status(self, client_id: str, client_instruction_id: str) -> dict:
        """
        Retrieve the status of a request by clientInstructionId.

        Parameters:
            client_id (str): The client ID associated with the instruction.
            client_instruction_id (str): The ID of the instruction to query.

        Returns:
            dict: The response containing the status of the instruction.
                Example response:
                {
                    "httpStatusCode": 200,
                    "instructionResult": {
                        "clientInstructionId": 7008156,
                        "instructionType": "INTERNAL_CASH_TRANSFER",
                        "status": "PENDING",
                        "instructionId": 43092595
                    },
                    "instructionSetId": 2650
                }

        Raises:
            HTTPError: If the request to the API fails or the instruction is not found.
        """
        endpoint = f"gw/api/v1/client-instructions/{client_instruction_id}"
        params = {"clientId": client_id}
        return self._request("GET", endpoint, params=params)

    def get_enumerations(self, enumeration_type: str, currency: str = None, ib_entity: str = None,
                         md_status_non_pro: str = None, form_number: str = None) -> dict:
        """
        Get enumerations for Trading permission, Employment detail, Affiliation detail,
        Financial Range information, ACATS and so on.

        Parameters:
            enumeration_type (str): The type of enumeration to retrieve (e.g., "tradingPermission").
            currency (str, optional): The currency type to filter the enumerations.
            ib_entity (str, optional): The IB entity for the request.
            md_status_non_pro (str, optional): Market data status for non-professionals.
            form_number (str, optional): Specific form number to filter results.

        Returns:
            dict: The response containing the enumerations.
                Example response:
                {
                    "enumerations": [
                        {
                            "type": "tradingPermission",
                            "value": "PERMISSION_GRANTED"
                        },
                        {
                            "type": "tradingPermission",
                            "value": "PERMISSION_DENIED"
                        }
                    ]
                }

        Raises:
            HTTPError: If the request to the API fails or if the request is invalid.
        """
        endpoint = f"gw/api/v1/enumerations/{enumeration_type}"
        params = {
            "currency": currency,
            "ibEntity": ib_entity,
            "mdStatusNonPro": md_status_non_pro,
            "form-number": form_number
        }
        return self._request("GET", endpoint, params={k: v for k, v in params.items() if v is not None})

    def transfer_positions_externally(self, client_id: str, instruction: dict) -> dict:
        """
        Transfer Positions Externally (ACATS, ATON, FOP, DWAC, Complex Asset Transfer).

        Initiate request to deposit or withdrawal between IBKR account and bank account.
        More information on transfer methods can be found here -
        https://www.interactivebrokers.com/campus/trading-lessons/cash-and-position-transfers/

        Args:
            client_id (str): The client ID for the transfer.
            instruction (dict): The transfer instruction details. Must include the `instructionType` and
                                `instruction` as required fields.

        Example `instruction` structure:
        {
            "instructionType": "DWAC",
            "instruction": {
                "clientInstructionId": 7013036,
                "direction": "IN",
                "accountId": "U1001095",
                "contraBrokerAccountId": "12345678A",
                "contraBrokerTaxId": "123456789",
                "quantity": 1000,
                "accountTitle": "Special Company Holding LLC",
                "referenceId": "refId",
                "tradingInstrument": {
                    "conId": 12123,
                    "currency": "USD"
                }
            }
        }

        Returns:
            dict: The response from the API indicating the result of the transfer instruction.

            Example return value:
            {
                "instructionResult": {
                    "clientInstructionId": 7013036,
                    "instructionType": "DWAC",
                    "instructionStatus": "PENDING",
                    "instructionId": 43091814
                },
                "instructionSetId": 1703,
                "status": 202
            }

        Raises:
            requests.exceptions.HTTPError: For any HTTP errors encountered.
        """
        endpoint = "external-asset-transfers"
        headers = {"clientId": client_id}
        return self._request("POST", endpoint, json={"instruction": instruction}, headers=headers)

    def transfer_cash_externally(self, client_id: str, instruction_type: str, instruction: dict) -> dict:
        """
        Initiate a request to transfer cash externally between IBKR account and bank account.

        Args:
            client_id (str): The client ID associated with the request.
            instruction_type (str): The type of instruction, either "DEPOSIT" or "WITHDRAWAL".
            instruction (dict): A dictionary containing the transfer instruction details.

        Returns:
            dict: A dictionary containing the result of the cash transfer request.

        Example:
            {
                "instructionResult": {
                    "clientInstructionId": 7008143,
                    "instructionType": "DEPOSIT",
                    "instructionStatus": "PENDING",
                    "instructionId": 43092468
                },
                "instructionSetId": 2480,
                "status": 202
            }

        Raises:
            ValueError: If the instruction type is invalid or the request fails.
            HTTPError: For unsuccessful HTTP responses.
        """
        endpoint = "gw/api/v1/external-cash-transfers"
        body = {
            "instructionType": instruction_type,
            "instruction": instruction
        }

        response = self._request("POST", endpoint, json=body, params={"clientId": client_id})
        return response

    def query_cash_balances(self, client_id: str, instruction: dict) -> dict:
        """
        View available cash for withdrawal with and without margin loan by accountId.

        Parameters:
        - client_id (str): The client ID associated with the account.
        - instruction (dict): The instruction object containing details for the query.
            Must include:
            - instructionType (str): Must be 'QUERY_WITHDAWABLE_FUNDS'.
            - instruction (dict): Contains account and currency details.

        Example instruction:
        {
            "instructionType": "QUERY_WITHDAWABLE_FUNDS",
            "instruction": {
                "clientInstructionId": "7009005",
                "accountId": "U87440",
                "currency": "USD"
            }
        }

        Returns:
        - dict: The response containing query results.

        Example return value:
        {
            "status": 201,
            "instructionSetId": 17791,
            "instructionResult": {
                "accountId": "U46377",
                "currency": "EUR",
                "withdrawableAmount": 0,
                "withdrawableAmountNoBorrow": 0,
                "allowedTransferAmountToMaster": 0,
                "withdrawableAmountWithoutOriginationHoldNoBorrow": 0,
                "ibReferenceId": 0,
                "clientInstructionId": 7013230,
                "instructionType": "QUERY_WITHDRAWABLE_FUNDS",
                "instructionStatus": "PROCESSED",
                "instructionId": 43133309
            }
        }
        """
        endpoint = f"gw/api/v1/external-cash-transfers/query"
        body = {
            "instructionType": "QUERY_WITHDAWABLE_FUNDS",
            "instruction": instruction
        }
        return self._request("POST", endpoint, json=body, params={"clientId": client_id})

    def set_fees_for_account(self, client_id: str, instruction: dict) -> dict:
        """
        Apply predefined fee template to existing account.

        Parameters:
        - client_id (str): The client ID associated with the account.
        - instruction (dict): The instruction object containing details for applying the fee template.
            Must include:
            - instructionType (str): Must be 'APPLY_FEE_TEMPLATE'.
            - instruction (dict): Contains the client instruction ID, account ID, and template name.

        Example instruction:
        {
            "instructionType": "APPLY_FEE_TEMPLATE",
            "instruction": {
                "clientInstructionId": "1012983",
                "accountId": "U46377",
                "templateName": "Test template"
            }
        }

        Returns:
        - dict: The response containing the status of the instruction.

        Example return value:
        {
            "status": 202,
            "instructionSetId": 1703,
            "instructionResult": {
                "clientInstructionId": 1013031,
                "instructionType": "APPLY_FEE_TEMPLATE",
                "instructionStatus": "PENDING",
                "instructionId": 43091814
            }
        }
        """
        endpoint = "gw/api/v1/fee-templates"
        body = {
            "instructionType": "APPLY_FEE_TEMPLATE",
            "instruction": instruction
        }
        return self._request("POST", endpoint, json=body, params={"clientId": client_id})

    def query_fee_template(self, client_id: str, instruction: dict) -> dict:
        """
        View fee template applied to an existing account.

        Parameters:
        - client_id (str): The client ID associated with the account.
        - instruction (dict): The instruction object containing details for querying the fee template.
            Must include:
            - instructionType (str): Must be 'QUERY_FEE_TEMPLATE'.
            - instruction (dict): Contains the client instruction ID and account ID.

        Example instruction:
        {
            "instructionType": "QUERY_FEE_TEMPLATE",
            "instruction": {
                "clientInstructionId": "1012983",
                "accountId": "U46377"
            }
        }

        Returns:
        - dict: The response containing the result of the fee template query.

        Example return value:
        {
            "status": 201,
            "instructionSetId": 3770,
            "instructionResult": {
                "templateDetails": {
                    "accountId": "U46377",
                    "templateName": ""
                },
                "ibReferenceId": 0,
                "clientInstructionId": 12001818,
                "instructionType": "GET_FEE_TEMPLATE",
                "instructionStatus": "PROCESSED",
                "instructionId": 43094186,
                "error": {
                    "errorCode": "FEE_TEMPLATE_NOT_FOUND",
                    "errorMessage": "Fee template not found for client account U46377"
                }
            }
        }
        """
        endpoint = "gw/api/v1/fee-templates/query"
        body = {
            "instructionType": "QUERY_FEE_TEMPLATE",
            "instruction": instruction
        }
        return self._request("POST", endpoint, json=body, params={"clientId": client_id})

    def get_forms(self, form_no: list[int] = None, get_docs: str = None,
                  from_date: str = None, to_date: str = None,
                  language: str = None) -> dict:
        """
        Retrieve forms based on specified parameters.

        Parameters:
        - form_no (list[int], optional): A list of form numbers to retrieve.
        - get_docs (str, optional): Specify whether to get documents.
        - from_date (str, optional): Start date for filtering forms (format: YYYY-MM-DD).
        - to_date (str, optional): End date for filtering forms (format: YYYY-MM-DD).
        - language (str, optional): Language preference for the forms.

        Returns:
        - dict: The response containing the forms data.

        Example return value:
        {
            "status": 200,
            "forms": [
                {
                    "formId": 1,
                    "formName": "Account Opening Form",
                    "available": true,
                    "dateCreated": "2023-01-01"
                },
                {
                    "formId": 2,
                    "formName": "Withdrawal Form",
                    "available": false,
                    "dateCreated": "2023-01-15"
                }
            ]
        }
        """
        endpoint = "gw/api/v1/forms"
        params = {
            "formNo": form_no,
            "getDocs": get_docs,
            "fromDate": from_date,
            "toDate": to_date,
            "language": language
        }
        return self._request("GET", endpoint, params={k: v for k, v in params.items() if v is not None})

    def get_instruction_set_status(self, instruction_set_id: str) -> dict:
        """
        Retrieve the status of all requests associated with a given instruction set ID.

        Parameters:
        - instruction_set_id (str): The unique identifier for the instruction set.

        Returns:
        - dict: The response containing the status of multiple instructions.

        Example return value:
        {
            "status": "success",
            "instructionSetId": "123456",
            "instructions": [
                {
                    "instructionId": "1",
                    "status": "PROCESSED",
                    "result": "Success"
                },
                {
                    "instructionId": "2",
                    "status": "PENDING",
                    "result": None
                }
            ]
        }

        Raises:
        - ValueError: If the instruction_set_id is not provided.
        """
        if not instruction_set_id:
            raise ValueError("instruction_set_id is required")

        endpoint = f"gw/api/v1/instruction-sets/{instruction_set_id}"
        return self._request("GET", endpoint)

    def cancel_instruction(self, instruction: dict) -> dict:
        """
        Cancel a request by instruction ID.

        Parameters:
        - instruction (dict): The instruction to cancel, must include 'instruction' and 'instructionType'.
            Example:
            {
                "instructionType": "CANCEL_INSTRUCTION",
                "instruction": {
                    "clientInstructionId": "12001810",
                    "instructionId": 43085477,
                    "reason": "Testing"
                }
            }

        Returns:
        - dict: The response containing the result of the cancel operation.

        Example return value:
        {
            "instructionResult": {
                "clientInstructionId": 12001810,
                "instructionType": "CANCEL_INSTRUCTION",
                "instructionStatus": "PROCESSED",
                "instructionId": 43094179
            },
            "instructionSetId": 3763,
            "status": 201
        }

        Raises:
        - ValueError: If the instruction parameter is not provided or is missing required fields.
        """
        if not instruction or 'instruction' not in instruction or 'instructionType' not in instruction:
            raise ValueError("Instruction must include 'instruction' and 'instructionType'.")

        endpoint = "gw/api/v1/instructions/cancel"
        return self._request("POST", endpoint, json=instruction)

    def query_recent_instructions(self, instruction: dict) -> dict:
        """
        Query the list of recent transactions based on account ID.

        Parameters:
        - instruction (dict): The instruction to query recent transactions. Must include 'instruction' and 'instructionType'.
            Example:
            {
                "instructionType": "QUERY_RECENT_INSTRUCTIONS",
                "instruction": {
                    "clientInstructionId": "7009001",
                    "accountId": "U139838",
                    "transactionHistory": {
                        "daysToGoBack": 3,
                        "transactionType": "ACH_INSTRUCTION"
                    }
                }
            }

        Returns:
        - dict: The response containing the status of the instruction query.

        Example return value:
        {
            "instructionResult": {
                "ibReferenceId": 0,
                "clientInstructionId": 7009001,
                "instructionType": "QUERY_RECENT_INSTRUCTIONS",
                "status": "PENDING",
                "instructionId": 43094002,
                "code": "PENDING",
                "description": "Query is being processed. Please poll for status 1 minutes later using FB status endpoint. No new queries will be allowed before this one is processed."
            },
            "instructionSetId": 3702,
            "httpStatusCode": 202
        }

        Raises:
        - ValueError: If the instruction parameter is not provided or is missing required fields.
        """
        if not instruction or 'instruction' not in instruction or 'instructionType' not in instruction:
            raise ValueError("Instruction must include 'instruction' and 'instructionType'.")

        endpoint = "gw/api/v1/instructions/query"
        return self._request("POST", endpoint, json=instruction)

    def get_instruction_status(self, instruction_id: str) -> dict:
        """
        Retrieve the status of a request by instructionId.

        Parameters:
        - instruction_id (str): The ID of the instruction to retrieve the status for.

        Returns:
        - dict: The response containing the status of the instruction.

        Example return value:
        {
            "httpStatusCode": 200,
            "instructionResult": {
                "clientInstructionId": 7008156,
                "instructionType": "INTERNAL_CASH_TRANSFER",
                "status": "PENDING",
                "instructionId": 43092595
            },
            "instructionSetId": 2650
        }

        Raises:
        - ValueError: If the instruction_id parameter is not provided.
        """
        if not instruction_id:
            raise ValueError("Instruction ID must be provided.")

        endpoint = f"gw/api/v1/instructions/{instruction_id}"
        return self._request("GET", endpoint)

    def transfer_positions_internally(self, instruction: dict) -> dict:
        """
        Transfer positions internally between two accounts with Interactive Brokers.

        Parameters:
        - instruction (dict): The instruction for the internal position transfer.
          Should contain 'instructionType' and 'instruction' details.

        Example instruction:
        {
            "instructionType": "INTERNAL_POSITION_TRANSFER",
            "instruction": {
                "clientInstructionId": 7013044,
                "sourceAccountId": "U399192",
                "targetAccountId": "U87440",
                "position": 106,
                "transferQuantity": 6,
                "tradingInstrument": {
                    "tradingInstrumentDescription": {
                        "securityIdType": "ISIN",
                        "securityId": "459200101",
                        "assetType": "STK"
                    },
                    "currency": "USD"
                }
            }
        }

        Returns:
        - dict: The response containing the result of the instruction transfer.

        Example return value:
        {
            "instructionResult": {
                "clientInstructionId": 7008152,
                "instructionType": "INTERNAL_POSITION_TRANSFER",
                "status": "PENDING",
                "instructionId": 43092590
            },
            "instructionSetId": 2614,
            "httpStatusCode": 202
        }

        Raises:
        - ValueError: If the instruction parameter is not provided.
        """
        if not instruction:
            raise ValueError("Instruction must be provided.")

        endpoint = "gw/api/v1/internal-asset-transfers"
        return self._request("POST", endpoint, json={"instruction": instruction})

    def transfer_cash_internally(self, instruction: dict) -> dict:
        """
        Transfer cash internally between two accounts with Interactive Brokers.

        Parameters:
        - instruction (dict): The instruction for the internal cash transfer.
          Should contain 'instructionType' and 'instruction' details.

        Example instruction:
        {
            "instructionType": "INTERNAL_CASH_TRANSFER",
            "instruction": {
                "clientInstructionId": "1012983",
                "sourceAccountId": "U46377",
                "targetAccountId": "U15667",
                "amount": 123.45,
                "currency": "GBP",
                "dateTimeToOccur": "2018-03-20T09:12:13Z"  # Optional
            }
        }

        Returns:
        - dict: The response containing the result of the cash transfer.

        Example return values:
        Success (201):
        {
            "instructionResult": {
                "clientInstructionId": 1013032,
                "instructionType": "INTERNAL_CASH_TRANSFER",
                "instructionStatus": "PROCESSED",
                "instructionId": 43091814,
                "ibReferenceId": 132123
            },
            "instructionSetId": 1703,
            "status": 201
        }

        Success (202):
        {
            "instructionResult": {
                "clientInstructionId": 1013031,
                "instructionType": "INTERNAL_CASH_TRANSFER",
                "instructionStatus": "PENDING",
                "instructionId": 43091814
            },
            "instructionSetId": 1703,
            "status": 202
        }

        Raises:
        - ValueError: If the instruction parameter is not provided.
        """
        if not instruction:
            raise ValueError("Instruction must be provided.")

        endpoint = "gw/api/v1/internal-cash-transfers"
        return self._request("POST", endpoint, json={"instruction": instruction})

    def get_participating_banks(self, bank_type: str) -> dict:
        """
        Get list of banks which support banking connection with Interactive Brokers.

        Parameters:
        - bank_type (str): The type for which the list of participating banks is fetched.
          Example: "eDDA"

        Returns:
        - dict: The response containing the list of participating banks.

        Example return value:
        {
            "type": "eDDA",
            "participatingBanks": [
                {
                    "institutionName": "WELAB BANK LIMITED",
                    "clearingCode": "390",
                    "BIC": "WEDIHKHHXXX"
                },
                {
                    "institutionName": "INDUSTRIAL AND COMMERCIAL BANK OF CHINA (ASIA) LIMITED",
                    "clearingCode": "072",
                    "BIC": "UBHKHKHHXXX"
                },
                {
                    "institutionName": "FUSION BANK LIMITED",
                    "clearingCode": "391",
                    "BIC": "IFFUHKHHXXX"
                },
                {
                    "institutionName": "CITIBANK (HONG KONG) LIMITED",
                    "clearingCode": "250",
                    "BIC": "CITIHKAXXXX"
                }
            ]
        }

        Raises:
        - ValueError: If the bank_type parameter is not provided.
        """
        if not bank_type:
            raise ValueError("Bank type must be provided.")

        endpoint = "gw/api/v1/participating-banks"
        params = {"type": bank_type}
        return self._request("GET", endpoint, params=params)

    def get_requests_details_by_timeframe(self, request_details: dict) -> dict:
        """
        Fetch Requests' Details By Timeframe.

        Parameters:
        - request_details (dict): A dictionary containing request parameters for fetching request details.
          The structure should conform to the RequestDetailsRequest schema.

        Returns:
        - dict: The response containing the details of the requests.

        Example return value:
        {
            "requests": [
                {
                    "requestId": "12345",
                    "status": "COMPLETED",
                    "createdDate": "2023-01-01T10:00:00Z",
                    "updatedDate": "2023-01-02T11:00:00Z",
                    "details": "Request details here"
                },
                ...
            ]
        }

        Raises:
        - ValueError: If request_details parameter is not provided or is invalid.
        """
        if not request_details:
            raise ValueError("Request details must be provided.")

        endpoint = "gw/api/v1/requests"
        return self._request("GET", endpoint, params=request_details)

    def get_request_status(self, request_id: str, response_type: str) -> dict:
        """
        Get status of a request.

        Parameters:
        - request_id (str): The ID of the request whose status is being fetched.
        - response_type (str): The type of response required. Must be either 'response' or 'update'.

        Returns:
        - dict: The response containing the status of the request.

        Example return value:
        {
            "requestId": "12345",
            "status": "COMPLETED",
            "message": "The request has been processed successfully."
        }

        Raises:
        - ValueError: If request_id or response_type is not provided or invalid.
        """
        if not request_id:
            raise ValueError("Request ID must be provided.")
        if response_type not in ["response", "update"]:
            raise ValueError("Response type must be 'response' or 'update'.")

        endpoint = f"gw/api/v1/requests/{request_id}/status"
        return self._request("GET", endpoint, params={"type": response_type})

    def create_sso_session(self, authorization: str, session_data: dict) -> dict:
        """
        Create a new SSO session on behalf of an end-user.

        Parameters:
        - authorization (str): The authorization header containing the signed JWT.
        - session_data (dict): The request body containing data for creating the SSO session.

        Returns:
        - dict: A JSON object containing a reference to the newly created SSO session.

        Example return value:
        {
            "sessionId": "abc123",
            "createdAt": "2024-10-22T12:00:00Z",
            "expiresAt": "2024-10-23T12:00:00Z"
        }

        Raises:
        - ValueError: If session_data is not provided.
        """
        if not session_data:
            raise ValueError("Session data must be provided.")

        endpoint = "gw/api/v1/sso-sessions"
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json"
        }
        return self._request("POST", endpoint, json=session_data, headers=headers)

    def generate_statement(self, authorization: str, statement_request: dict) -> dict:
        """
        Generates statements in supported formats based on request parameters.

        Parameters:
        - authorization (str): The authorization header containing the signed JWT.
        - statement_request (dict): The report request object specifying statement parameters.

        Returns:
        - dict: A JSON object containing the relevant statement.

        Example return value:
        {
            "statementId": "123456",
            "format": "pdf",
            "content": "<binary data>",
            "contentType": "application/pdf"
        }

        Raises:
        - ValueError: If statement_request is not provided.
        """
        if not statement_request:
            raise ValueError("Statement request data must be provided.")

        endpoint = "gw/api/v1/statements"
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json"
        }
        return self._request("POST", endpoint, json=statement_request, headers=headers)

    def verify_username(self, username: str) -> dict:
        """
        Verify whether the specified username is valid and available.

        Parameters:
        - username (str): The username to verify.

        Returns:
        - dict: A JSON object indicating whether the username is available.

        Example return value:
        {
            "available": true,
            "message": "Username is available."
        }

        Raises:
        - ValueError: If the username is not provided.
        """
        if not username:
            raise ValueError("Username must be provided.")

        endpoint = f"gw/api/v1/validations/usernames/{username}"
        return self._request("GET", endpoint)

    def get_historical_data_beta(self, conid: str, period: str, bar: str, bar_type: str = "Last",
                                 start_time: str = None, direction: int = 1, outside_rth: bool = False) -> dict:
        """
        Request historical data for an instrument in the form of OHLC bars.

        Parameters:
        - conid (str): IB contract ID of the requested instrument (required).
        - period (str): A time duration away from startTime (required).
        - bar (str): The width of the bars (required).
        - bar_type (str, optional): The requested historical data type (default is "Last").
        - start_time (str, optional): A fixed UTC date-time reference point (format: YYYYMMDD-hh:mm:ss).
        - direction (int, optional): The requested period's direction (-1 for future, 1 for past; default is 1).
        - outside_rth (bool, optional): Whether to include data outside of regular trading hours (default is False).

        Returns:
        - dict: A JSON object containing the historical data.

        Example return value:
        {
            "startTime": "20231211-04:00:00",
            "startTimeVal": 1702285200000,
            "endTime": "20231211-17:51:20",
            "endTimeVal": 1702335080000,
            "data": [
                {
                    "t": 1702285200000,
                    "o": 195.01,
                    "c": 194.8,
                    "h": 195.01,
                    "l": 194.8,
                    "v": 1723.0
                }
            ],
            "points": 1,
            "mktDataDelay": 0
        }
        """
        params = {
            "conid": conid,
            "barType": bar_type,
            "startTime": start_time,
            "period": period,
            "direction": direction,
            "bar": bar,
            "outsideRth": outside_rth
        }

        # Remove keys with None values to avoid sending them as query parameters
        params = {k: v for k, v in params.items() if v is not None}

        return self._request("GET", "hmds/history", params=params)

    def get_scanner_params(self) -> dict:
        """
        Query the parameter list for the HMDS market scanner.

        Returns:
        - dict: An object containing details about the HMDS scanner parameters.

        Example return value:
        {
            "instrument_list": [
                {
                    "display_name": "display_name",
                    "type": "type",
                    "filters": []
                }
            ],
            "scan_type_list": [
                {
                    "display_name": "display_name",
                    "code": "code",
                    "instruments": []
                }
            ],
            "location_tree": [
                {
                    "display_name": "display_name",
                    "type": "type",
                    "locations": [
                        {
                            "display_name": "display_name",
                            "locationCode": "locationCode",
                            "locations": []
                        }
                    ]
                }
            ]
        }
        """
        return self._request("GET", "hmds/scanner/params")

    def run_scanner(self, request_body: dict) -> dict:
        """
        Request a market scanner from the HMDS service. Can return a maximum of 250 contracts.

        Args:
        - request_body (dict): A dictionary containing the parameters for the scanner request.
            Expected keys include:
            - instrument (str): Type of instrument to scan (e.g., "BOND").
            - locations (str): Locations to scan (e.g., "BOND.US").
            - scanCode (str): The code for the type of scan (e.g., "HIGH_BOND_ASK_YIELD_ALL").
            - secType (str): The security type (e.g., "BOND").
            - delayedLocations (str): Locations for delayed data (e.g., "SMART").
            - maxItems (int): The maximum number of items to return (up to 250).
            - filters (list): A list of filters to apply to the scan.

        Returns:
        - dict: An object containing details about the market scanner results.

        Example return value:
        {
            "total": 17616,
            "size": 250,
            "offset": 0,
            "scanTime": "20240403-20:31:48",
            "id": "scanner20",
            "position": "v1:AAAAAQABG3gAAAAAAAAA+g==",
            "Contracts": {
                "Contract": [
                    {
                        "inScanTime": "20240403-20:31:48",
                        "contractID": 403154854
                    },
                    {
                        "inScanTime": "20240403-20:31:48",
                        "contractID": 460655952
                    }
                ]
            }
        }
        """
        return self._request("POST", "hmds/scanner/run", json=request_body)

    def get_alert_details(self, alert_id: str, alert_type: str) -> dict:
        """
        Request details of a specific alert by providing the assigned alertId.

        Args:
        - alert_id (str): The identifier for the alert (order ID).
            Example: "833967258"
        - alert_type (str): The query type, must be "Q".

        Returns:
        - dict: An object containing all unique details of the specified alert.

        Example return value:
        {
            "account": "U1234567",
            "order_id": 833967258,
            "alert_name": "IBM",
            "tif": "GTC",
            "expire_time": null,
            "alert_active": 1,
            "alert_repeatable": 0,
            "alert_email": "john.smith@example.com",
            "alert_send_message": 1,
            "alert_message": "alert message",
            "alert_show_popup": 1,
            "alert_play_audio": null,
            "order_status": "Submitted",
            "alert_triggered": false,
            "fg_color": "#FFFFFF",
            "bg_color": "#0000CC",
            "order_not_editable": false,
            "itws_orders_only": 0,
            "alert_mta_currency": null,
            "alert_mta_defaults": null,
            "tool_id": null,
            "time_zone": null,
            "alert_default_type": null,
            "condition_size": 1,
            "condition_outside_rth": 1,
            "conditions": [
                {
                    "condition_type": 1,
                    "conidex": "8314@NYSE",
                    "contract_description_1": "IBM",
                    "condition_operator": ">=",
                    "condition_trigger_method": "0",
                    "condition_value": "500.00",
                    "condition_logic_bind": "n",
                    "condition_time_zone": null
                }
            ]
        }
        """
        endpoint = f"iserver/account/alert/{alert_id}"
        params = {"type": alert_type}
        return self._request("GET", endpoint, params=params)

    def get_allocatable_sub_accounts(self) -> dict:
        """
        Retrieves a list of all sub-accounts, returning their net liquidity and available equity
        for advisors to make allocation decisions.

        Returns:
        - dict: A list of allocatable sub-accounts with their net liquidity and available equity.

        Example return value:
        {
            "accounts": [
                {
                    "data": [
                        {"value": "230013224.04", "key": "NetLiquidation"},
                        {"value": "229617260.41", "key": "AvailableEquity"}
                    ],
                    "name": "U1234567"
                },
                {
                    "data": [
                        {"value": "229453917.57", "key": "NetLiquidation"},
                        {"value": "229153196.12", "key": "AvailableEquity"}
                    ],
                    "name": "U1234568"
                }
            ]
        }
        """
        endpoint = "iserver/account/allocation/accounts"
        return self._request("GET", endpoint)

    def list_allocation_groups(self) -> dict:
        """
        Retrieves a list of all allocation groups associated with the advisor's account.

        Returns:
        - dict: A list of allocation groups with details such as name and size.

        Example return value:
        {
            "data": [
                {
                    "allocation_method": "E",
                    "size": 16,
                    "name": "group_1"
                },
                {
                    "allocation_method": "N",
                    "size": 3,
                    "name": "group_2"
                }
            ]
        }
        """
        endpoint = "iserver/account/allocation/group"
        return self._request("GET", endpoint)

    def modify_allocation_group(self, name: str, accounts: list, default_method: str, prev_name: str = None) -> dict:
        """
        Modify an existing allocation group.

        Parameters:
        - name (str): New name for the allocation group. If prev_name is specified, this becomes the new name.
        - accounts (list): An array of accounts to be included in the allocation group.
        - default_method (str): The method used for allocation.
        - prev_name (str, optional): Previous name of the allocation group for renaming.

        Returns:
        - dict: Confirmation of modification success.

        Example return value:
        {
            "success": true
        }
        """
        endpoint = "iserver/account/allocation/group"
        payload = {
            "name": name,
            "accounts": accounts,
            "default_method": default_method,
            "prev_name": prev_name
        }
        return self._request("PUT", endpoint, json=payload)

    def add_allocation_group(self, name: str, accounts: list, default_method: str) -> dict:
        """
        Add a new allocation group.

        Parameters:
        - name (str): Name used to refer to the new allocation group.
        - accounts (list): An array of accounts to be included in the allocation group.
        - default_method (str): The method used for allocation.

        Returns:
        - dict: Confirmation of addition success.

        Example return value:
        {
            "success": true
        }
        """
        endpoint = "iserver/account/allocation/group"
        payload = {
            "name": name,
            "accounts": accounts,
            "default_method": default_method
        }
        return self._request("POST", endpoint, json=payload)

    def remove_allocation_group(self, name: str) -> dict:
        """
        Remove an existing allocation group.

        Parameters:
        - name (str): Name of the existing allocation group to be removed.

        Returns:
        - dict: Confirmation of removal success.

        Example return value:
        {
            "success": true
        }
        """
        endpoint = "iserver/account/allocation/group/delete"
        payload = {"name": name}
        return self._request("POST", endpoint, json=payload)

    def retrieve_allocation_group(self, name: str) -> dict:
        """
        Retrieve the configuration of a single allocation group.

        Parameters:
        - name (str): Name of the existing allocation group to retrieve.

        Returns:
        - dict: Details of the allocation group, including its accounts and allocation method.

        Example return value:
        {
            "name": "group1",
            "accounts": [
                {"name": "U1234567"},
                {"name": "U1234568"}
            ],
            "default_method": "E"
        }
        """
        endpoint = "iserver/account/allocation/group/single"
        payload = {"name": name}
        return self._request("POST", endpoint, json=payload)

    def retrieve_allocation_presets(self) -> dict:
        """
        Retrieve the preset behavior for allocation groups for specific events.

        Returns:
        - dict: The preset details for allocation groups.

        Example return value:
        {
            "group_auto_close_positions": false,
            "default_method_for_all": "AvailableEquity",
            "profiles_auto_close_positions": false,
            "strict_credit_check": false,
            "group_proportional_allocation": false
        }
        """
        endpoint = "iserver/account/allocation/presets"
        return self._request("GET", endpoint)

    def set_allocation_presets(self, presets: dict) -> dict:
        """
        Set the preset behavior for new allocation groups for specific events.

        Parameters:
        - presets (dict): The preset configuration to be set for allocation groups.

        Returns:
        - dict: Confirmation of the preset submission.

        Example return value:
        {
            "success": true
        }
        """
        endpoint = "iserver/account/allocation/presets"
        return self._request("POST", endpoint, json=presets)

    def get_mta_alert(self) -> dict:
        """
        Retrieve information about your MTA alert.

        Each login user only has one mobile trading assistant (MTA) alert with its own unique tool ID that cannot be changed.
        MTA alerts can only be modified, not created or deleted. Modifications generate a new order ID.

        Returns:
        - dict: The alert details for the unique MTA alert on the account.

        Example return value:
        {
            "account": "U1234567",
            "order_id": 167426254,
            "alert_name": "MTA (AutoAlert)",
            "tif": "GTC",
            "expire_time": null,
            "alert_active": 1,
            "alert_repeatable": 1,
            "alert_email": "jonh.smith@example.com",
            "alert_send_message": 1,
            "alert_message": null,
            "alert_show_popup": 0,
            "alert_play_audio": null,
            "order_status": "Submitted",
            "alert_triggered": false,
            "fg_color": "#FFFFFF",
            "bg_color": "#0000CC",
            "order_not_editable": false,
            "itws_orders_only": 0,
            "alert_mta_currency": "USD",
            "alert_mta_defaults": "9:STATE=1,MIN=-260000,MAX=260000,STEP=500,DEF_MIN=-26000,DEF_MAX=26000|8:STATE=0,MIN=-15,MAX=15,STEP=0.5,DEF_MIN=-2,DEF_MAX=2|7:STATE=1,MIN=-5,MAX=5,STEP=0.5,DEF_MIN=-2,DEF_MAX=2|4:STATE=1,MIN=1,MAX=50,STEP=1,DEF_VAL=10|5:STATE=0",
            "tool_id": 55834574848,
            "time_zone": "all timezones can be here",
            "alert_default_type": null,
            "condition_size": 1,
            "condition_outside_rth": 0,
            "conditions": [
                {
                    "condition_type": 5,
                    "conidex": "*@*",
                    "contract_description_1": "Unknown",
                    "condition_operator": null,
                    "condition_trigger_method": null,
                    "condition_value": "*",
                    "condition_logic_bind": "n",
                    "condition_time_zone": null
                }
            ]
        }
        """
        endpoint = "iserver/account/mta"
        return self._request("GET", endpoint)

    def get_order_status(self, order_id: str) -> dict:
        """
        Retrieve the status of a single order.

        Args:
            order_id (str): The IB-assigned order ID of the desired order ticket.

        Returns:
            dict: The status details of the specified order.

            Example return value:
            {
                "sub_type": null,
                "request_id": "209",
                "server_id": "0",
                "order_id": 1799796559,
                "conidex": "265598",
                "conid": 265598,
                "symbol": "AAPL",
                "side": "S",
                "contract_description_1": "AAPL",
                "listing_exchange": "NASDAQ.NMS",
                "option_acct": "c",
                "company_name": "APPLE INC",
                "size": "0.0",
                "total_size": "5.0",
                "currency": "USD",
                "account": "U1234567",
                "order_type": "MARKET",
                "cum_fill": "5.0",
                "order_status": "Filled",
                "order_ccp_status": "2",
                "order_status_description": "Order Filled",
                "tif": "DAY",
                "fg_color": "#FFFFFF",
                "bg_color": "#000000",
                "order_not_editable": true,
                "editable_fields": "",
                "cannot_cancel_order": true,
                "deactivate_order": false,
                "sec_type": "STK",
                "available_chart_periods": "#R|1",
                "order_description": "Sold 5 Market, Day",
                "order_description_with_contract": "Sold 5 AAPL Market, Day",
                "alert_active": 1,
                "child_order_type": "0",
                "order_clearing_account": "U1234567",
                "size_and_fills": "5",
                "exit_strategy_display_price": "193.12",
                "exit_strategy_chart_description": "Sold 5 @ 192.26",
                "average_price": "192.26",
                "exit_strategy_tool_availability": "1",
                "allowed_duplicate_opposite": true,
                "order_time": "231211180049"
            }
        """
        endpoint = f"iserver/account/order/status/{order_id}"
        return self._request("GET", endpoint)

    def get_orders(self, filters: str = None, force: bool = None) -> dict:
        """
        Retrieves open orders and filled or cancelled orders submitted during the current brokerage session.

        Args:
            filters (str, optional): Filter results using a comma-separated list of Order Status values.
                                     Accepts values like "Inactive", "Filled", etc. Can also sort results by time.
            force (bool, optional): Instructs IB to clear cache of orders and obtain an updated view from the brokerage backend.
                                    If set, the response will be an empty array.

        Returns:
            dict: A dictionary containing orders for a specific account.

            Example return value:
            {
                "orders": [
                    {
                        "acct": "U1234567",
                        "exchange": "IDEALPRO",
                        "conidex": "15016138@IDEALPRO",
                        "conid": 15016138,
                        "account": "DU4355398",
                        "orderId": 1370093238,
                        "cashCcy": "CAD",
                        "sizeAndFills": "2.4K CAD",
                        "orderDesc": "Bought 2806.46 Limit 0.90000, Day",
                        "description1": "AUD.CAD",
                        "ticker": "AUD",
                        "secType": "CASH",
                        "listingExchange": "FXCONV",
                        "remainingQuantity": 0.0,
                        "filledQuantity": 2499.99,
                        "totalSize": 2806.46,
                        "totalCashSize": 2500.0,
                        "companyName": "Australian dollar",
                        "status": "Filled",
                        "order_ccp_status": "Filled",
                        "origOrderType": "LIMIT",
                        "supportsTaxOpt": "0",
                        "lastExecutionTime": "240425160326",
                        "orderType": "Limit",
                        "bgColor": "#FFFFFF",
                        "fgColor": "#000000",
                        "isEventTrading": "0",
                        "price": "0.90000",
                        "timeInForce": "CLOSE",
                        "lastExecutionTime_r": 1714061006000,
                        "side": "BUY",
                        "avgPrice": "0.8908"
                    }
                ],
                "snapshot": true
            }
        """
        endpoint = "iserver/account/orders"
        params = {k: v for k, v in {"filters": filters, "force": force, "accountId": self.account_id}.items()
                  if v is not None}
        return self._request("GET", endpoint, params=params)

    def get_partitioned_pnl(self) -> dict:
        """
        Retrieves the updated Profit and Loss (PnL) details for accounts in a partitioned format.

        Returns:
            dict: A dictionary containing the updated PnL details.

            Example return value:
            {
                "upnl": {
                    "U1234567.Core": {
                        "rowType": 1,
                        "dpl": -12510.0,
                        "nl": 1290000.0,
                        "upl": 256000.0,
                        "el": 824600.0,
                        "mv": 1700000.0
                    }
                }
            }
        """
        endpoint = "iserver/account/pnl/partitioned"
        return self._request("GET", endpoint)

    def search_dynamic_account(self, search_pattern: str) -> dict:
        """
        Searches for dynamic accounts that match the specified pattern.

        Args:
            search_pattern (str): The pattern used to search for accounts.
                Including part of an account ID will return the full value.

        Returns:
            dict: A dictionary containing matched accounts based on the search pattern.

            Example return value:
            {
                "matchedAccounts": [
                    {
                        "accountId": "U1234567",
                        "alias": "U1234567",
                        "allocationId": "U1234567"
                    }
                ],
                "pattern": "U1"
            }
        """
        endpoint = f"iserver/account/search/{search_pattern}"
        return self._request("GET", endpoint)

    def get_trades(self, days: str = None) -> dict:
        """
        Retrieve a list of trades for the specified account.

        Args:
            days (str, optional): The number of prior days to include in the response, up to a maximum of 7.
                If omitted, only the current day's executions will be returned.

        Returns:
            dict: A dictionary containing a list of trades.

            Example return value:
            [
                {
                    "execution_id": "0000e0d5.6576fd38.01.01",
                    "symbol": "AAPL",
                    "supports_tax_opt": "1",
                    "side": "S",
                    "order_description": "Sold 5 @ 192.26 on ISLAND",
                    "trade_time": "20231211-18:00:49",
                    "trade_time_r": 1702317649000,
                    "size": 5.0,
                    "price": "192.26",
                    "order_ref": "Order123",
                    "submitter": "user1234",
                    "exchange": "ISLAND",
                    "commission": "1.01",
                    "net_amount": 961.3,
                    "account": "U1234567",
                    "accountCode": "U1234567",
                    "account_allocation_name": "U1234567",
                    "company_name": "APPLE INC",
                    "contract_description_1": "AAPL",
                    "sec_type": "STK",
                    "listing_exchange": "NASDAQ.NMS",
                    "conid": 265598,
                    "conidEx": "265598",
                    "clearing_id": "IB",
                    "clearing_name": "IB",
                    "liquidation_trade": "0",
                    "is_event_trading": "0"
                }
            ]
        """
        params = {}
        if days is not None:
            params["days"] = days
        if self.account_id is not None:
            params["accountId"] = self.account_id

        return self._request("GET", "iserver/account/trades", params=params)

    def create_or_modify_alert(self, alert_data: dict) -> dict:
        """
        Create a new alert or modify an existing alert.

        Args:
            alert_data (dict): A dictionary containing the alert details. The structure should follow the schema:
                {
                    "alertName": str,
                    "alertMessage": str,
                    "alertRepeatable": int,
                    "email": str,
                    "expireTime": str,
                    "iTWSOrdersOnly": int,
                    "outsideRth": int,
                    "sendMessage": int,
                    "showPopup": int,
                    "tif": str,
                    "conditions": [
                        {
                            "conidex": str,
                            "logicBind": str,
                            "operator": str,
                            "timeZone": str,
                            "triggerMethod": str,
                            "type": int,
                            "value": str
                        }
                    ]
                }

        Returns:
            dict: A dictionary containing the response from the alert creation/modification request.

            Example return value for successfully created alert:
            {
                "request_id": null,
                "order_id": 1408549184,
                "success": true,
                "text": "Submitted",
                "order_status": null,
                "warning_message": null
            }

            Example return value for successfully modified alert:
            {
                "request_id": null,
                "order_id": 1408549184,
                "success": true,
                "text": "Submitted",
                "order_status": null,
                "warning_message": null
            }

            Example return value for bad request:
            {
                "error": "Bad Request: body can't be empty",
                "statusCode": 400
            }
        """
        endpoint = f"iserver/account/{self.account_id}/alert"
        return self._request("POST", endpoint, json=alert_data)

    def activate_deactivate_alert(self, alert_activation_data: dict) -> dict:
        """
        Activate or deactivate an existing alert.

        Args:
            alert_activation_data (dict): A dictionary containing the alert activation details. The structure should follow the schema:
                {
                    "alertId": int,
                    "alertActive": int  # 1 to activate, 0 to deactivate
                }

        Returns:
            dict: A dictionary containing the response from the alert activation/deactivation request.

            Example return value for successfully activated or deactivated alert:
            {
                "request_id": null,
                "order_id": 833967258,
                "success": true,
                "text": "Request was submitted",
                "failure_list": null
            }

            Example return value for a failed request:
            {
                "error": "failed to activate/deactivate alert"
            }
        """
        endpoint = f"iserver/account/{self.account_id}/alert/activate"
        return self._request("POST", endpoint, json=alert_activation_data)

    def delete_alert(self, alert_id: str) -> dict:
        """
        Permanently delete an existing alert.

        Args:
            alert_id (str): The ID of the alert to be deleted, which should be the order_id returned from the original alert creation.

        Returns:
            dict: A dictionary containing the response from the alert deletion request.

            Example return value for successfully deleted alert:
            {
                "request_id": null,
                "order_id": 833967258,
                "success": true,
                "text": "Request was submitted",
                "failure_list": null
            }

            Example return value for a failed deletion:
            {
                "error": "failed to delete alert: Alert 83396732432423258 doesn't exist"
            }
        """
        endpoint = f"iserver/account/{self.account_id}/alert/{alert_id}"
        return self._request("DELETE", endpoint)

    def get_alerts(self) -> list:
        """
        Retrieve a list of all alerts attached to the provided account.

        Returns:
            list: A list of dictionaries containing alert information for the specified account.

            Example return value when alerts are found:
            [
                {
                    "order_id": 9876543210,
                    "account": "U1234567",
                    "alert_name": "AAPL",
                    "alert_active": 1,
                    "order_time": "20240308-17:08:38",
                    "alert_triggered": false,
                    "alert_repeatable": 0
                }
            ]

            Example return value when no alerts are found:
            []
        """
        endpoint = f"iserver/account/{self.account_id}/alerts"
        return self._request("GET", endpoint)

    def modify_order(self, order_id: str, order_data: dict) -> dict:
        """
        Modify an existing, unfilled order.

        Args:
            order_id (str): The IB-assigned order ID of the desired order ticket.
            order_data (dict): The data for modifying the order.

        Returns:
            dict: The status of the order submission.

            Example return value on successful modification:
            {
                "order_id": "1370093239",
                "order_status": "PreSubmitted",
                "encrypt_message": "1"
            }

            Example return value on error:
            {
                "error": "OrderID 123456 doesn't exist"
            }
        """
        endpoint = f"iserver/account/{self.account_id}/order/{order_id}"
        return self._request("POST", endpoint, json=order_data)

    def cancel_order(self, order_id: str) -> dict:
        """
        Cancel an existing, unfilled order.

        Args:
            order_id (str): The IB-assigned order ID of the desired order ticket.

        Returns:
            dict: The status of the cancellation submission.

            Example return value on successful cancellation:
            {
                "msg": "Request was submitted",
                "order_id": "1370093239",
                "order_status": "PreSubmitted",
                "encrypt_message": "1"
            }

            Example return value on error:
            {
                "error": "OrderID 123456 doesn't exist"
            }
        """
        endpoint = f"iserver/account/{self.account_id}/order/{order_id}"
        return self._request("DELETE", endpoint)

    def submit_order(self, order_data: dict, auto_confirm: bool = True) -> dict:
        """
        Submit a new order(s) ticket, bracket, or OCA group, and optionally auto-confirm messages.

        Args:
            order_data (dict): The data for the order submission.
            auto_confirm (bool): If True, automatically confirm any messages that require confirmation.

        Returns:
            dict: The response from the order submission.

            Example return value on successful submission:
            {
                "order_id": "1370093239",
                "order_status": "PreSubmitted",
                "encrypt_message": "1"
            }

            Example return value on error:
            {
                "error": "Order not confirmed"
            }
        """
        endpoint = f"iserver/account/{self.account_id}/orders"
        response = self._request("POST", endpoint, json=order_data)

        # Auto-confirm messages if required
        msg = response[0]
        if auto_confirm:
            while "order_id" not in msg:
                logger.debug(f"Answering yes to: {msg['message']}")
                msg = self.confirm_order_reply(msg["id"])

        return msg

    def preview_order(self, order_data: dict) -> dict:
        """
        Preview the projected effects of an order ticket or bracket of orders, including cost and changes to margin and account equity.

        Args:
            order_data (dict): The data for the order submission.

        Returns:
            dict: The projected effects of the order.

            Example return value:
            {
                "amount": {
                    "amount": "1,977.60 USD (10 Shares)",
                    "commission": "1 USD",
                    "total": "1,978.60 USD"
                },
                "equity": {
                    "current": "123,456",
                    "change": "-1",
                    "after": "123,455"
                },
                "initial": {
                    "current": "1000",
                    "change": "652",
                    "after": "1652"
                },
                "maintenance": {
                    "current": "900",
                    "change": "590",
                    "after": "1490"
                },
                "position": {
                    "current": "20",
                    "change": "10",
                    "after": "30"
                },
                "warn": "21/You are trying to submit an order without having market data for this instrument. \nIB strongly recommends against this kind of blind trading which may result in \nerroreous or unexpected trades.",
                "error": null
            }
        """
        endpoint = f"iserver/account/{self.account_id}/orders/whatif"
        return self._request("POST", endpoint, json=order_data)

    def get_account_summary(self) -> dict:
        """
        Provides a general overview of the account details such as balance values.

        Returns:
            dict: A summary of the account details.

            Example return value:
            {
                "accountType": "",
                "status": "",
                "balance": 825903.0,
                "SMA": 368538.0,
                "buyingPower": 3307124.0,
                "availableFunds": 825903.0,
                "excessLiquidity": 826781.0,
                "netLiquidationValue": 1290490.0,
                "equityWithLoanValue": 1281714.0,
                "regTLoan": 0.0,
                "securitiesGVP": 1793178.0,
                "totalCashValue": -401846.0,
                "accruedInterest": 0.0,
                "regTMargin": 0.0,
                "initialMargin": 464586.0,
                "maintenanceMargin": 463709.0,
                "cashBalances": [
                    {"currency": "EUR", "balance": 194.0, "settledCash": 194.0},
                    {"currency": "HKD", "balance": 0.0, "settledCash": 0.0},
                    {"currency": "JPY", "balance": 14781.0, "settledCash": 14781.0},
                    {"currency": "USD", "balance": -402158.0, "settledCash": -402158.0},
                    {"currency": "Total (in USD)", "balance": -401846.0, "settledCash": -401846.0}
                ]
            }
        """
        endpoint = f"iserver/account/{self.account_id}/summary"
        return self._request("GET", endpoint)

    def get_available_funds_summary(self) -> dict:
        """
        Provides a summary specific for available funds giving more depth than the standard /summary endpoint.

        Returns:
            dict: A summary of available funds.

            Example return value:
            {
                "total": {
                    "current_available": "825,208 USD",
                    "current_excess": "826,089 USD",
                    "Prdctd Pst-xpry Excss": "0 USD",
                    "SMA": "368,538 USD",
                    "Lk Ahd Avlbl Fnds": "821,067 USD",
                    "Lk Ahd Excss Lqdty": "822,324 USD",
                    "overnight_available": "821,067 USD",
                    "overnight_excess": "822,324 USD",
                    "buying_power": "3,304,346 USD",
                    "leverage": "n/a",
                    "Lk Ahd Nxt Chng": "@ 16:00:00",
                    "day_trades_left": "Unlimited"
                },
                "Crypto at Paxos": {
                    "current_available": "0 USD",
                    "current_excess": "0 USD",
                    "Prdctd Pst-xpry Excss": "0 USD",
                    "Lk Ahd Avlbl Fnds": "0 USD",
                    "Lk Ahd Excss Lqdty": "0 USD",
                    "overnight_available": "0 USD",
                    "overnight_excess": "0 USD"
                },
                "commodities": {
                    "current_available": "22,483 USD",
                    "current_excess": "23,361 USD",
                    "Prdctd Pst-xpry Excss": "0 USD",
                    "Lk Ahd Avlbl Fnds": "18,342 USD",
                    "Lk Ahd Excss Lqdty": "19,597 USD",
                    "overnight_available": "18,342 USD",
                    "overnight_excess": "19,597 USD"
                },
                "securities": {
                    "current_available": "802,725 USD",
                    "current_excess": "802,727 USD",
                    "Prdctd Pst-xpry Excss": "0 USD",
                    "SMA": "368,538 USD",
                    "Lk Ahd Avlbl Fnds": "802,725 USD",
                    "Lk Ahd Excss Lqdty": "802,727 USD",
                    "overnight_available": "802,725 USD",
                    "overnight_excess": "802,727 USD",
                    "leverage": "1.43"
                }
            }
        """
        endpoint = f"iserver/account/{self.account_id}/summary/available_funds"
        return self._request("GET", endpoint)

    def get_account_balances_summary(self) -> dict:
        """
        Provides a summary of account balances, including net liquidation and cash.

        Returns:
            dict: A summary of account balances.

            Example return value:
            {
                "total": {
                    "net_liquidation": "1,288,301 USD",
                    "Nt Lqdtn Uncrtnty": "0 USD",
                    "equity_with_loan": "1,279,520 USD",
                    "Prvs Dy Eqty Wth Ln Vl": "1,275,902 USD",
                    "Rg T Eqty Wth Ln Vl": "1,256,229 USD",
                    "sec_gross_pos_val": "1,791,096 USD",
                    "cash": "-401,693 USD",
                    "MTD Interest": "-549 USD",
                    "Pndng Dbt Crd Chrgs": "0 USD"
                },
                "Crypto at Paxos": {
                    "net_liquidation": "0 USD",
                    "equity_with_loan": "0 USD",
                    "cash": "0 USD",
                    "MTD Interest": "0 USD",
                    "Pndng Dbt Crd Chrgs": "0 USD"
                },
                "commodities": {
                    "net_liquidation": "32,072 USD",
                    "equity_with_loan": "23,291 USD",
                    "cash": "32,072 USD",
                    "MTD Interest": "0 USD",
                    "Pndng Dbt Crd Chrgs": "0 USD"
                },
                "securities": {
                    "net_liquidation": "1,256,229 USD",
                    "equity_with_loan": "1,256,229 USD",
                    "Prvs Dy Eqty Wth Ln Vl": "1,275,902 USD",
                    "Rg T Eqty Wth Ln Vl": "1,256,229 USD",
                    "sec_gross_pos_val": "1,791,096 USD",
                    "cash": "-433,765 USD",
                    "MTD Interest": "-549 USD",
                    "Pndng Dbt Crd Chrgs": "0 USD"
                }
            }
        """
        endpoint = f"iserver/account/{self.account_id}/summary/balances"
        return self._request("GET", endpoint)

    def get_account_margin_summary(self) -> dict:
        """
        Provides a summary of account margin balances.

        Returns:
            dict: A summary of account margin balances.

            Example return value:
            {
                "total": {
                    "RegT Margin": "896,255 USD",
                    "current_initial": "468,562 USD",
                    "Prdctd Pst-xpry Mrgn @ Opn": "0 USD",
                    "current_maint": "467,308 USD",
                    "projected_liquidity_inital_margin": "468,562 USD",
                    "Prjctd Lk Ahd Mntnnc Mrgn": "467,308 USD",
                    "projected_overnight_initial_margin": "468,562 USD",
                    "Prjctd Ovrnght Mntnnc Mrgn": "467,308 USD"
                },
                "Crypto at Paxos": {
                    "current_initial": "0 USD",
                    "Prdctd Pst-xpry Mrgn @ Opn": "0 USD",
                    "current_maint": "0 USD",
                    "projected_liquidity_inital_margin": "0 USD",
                    "Prjctd Lk Ahd Mntnnc Mrgn": "0 USD",
                    "projected_overnight_initial_margin": "0 USD",
                    "Prjctd Ovrnght Mntnnc Mrgn": "0 USD"
                },
                "commodities": {
                    "current_initial": "13,794 USD",
                    "Prdctd Pst-xpry Mrgn @ Opn": "0 USD",
                    "current_maint": "12,540 USD",
                    "projected_liquidity_inital_margin": "13,794 USD",
                    "Prjctd Lk Ahd Mntnnc Mrgn": "12,540 USD",
                    "projected_overnight_initial_margin": "13,794 USD",
                    "Prjctd Ovrnght Mntnnc Mrgn": "12,540 USD"
                },
                "securities": {
                    "RegT Margin": "896,255 USD",
                    "current_initial": "454,768 USD",
                    "Prdctd Pst-xpry Mrgn @ Opn": "0 USD",
                    "current_maint": "454,768 USD",
                    "projected_liquidity_inital_margin": "454,768 USD",
                    "Prjctd Lk Ahd Mntnnc Mrgn": "454,768 USD",
                    "projected_overnight_initial_margin": "454,768 USD",
                    "Prjctd Ovrnght Mntnnc Mrgn": "454,768 USD"
                }
            }
        """
        endpoint = f"iserver/account/{self.account_id}/summary/margins"
        return self._request("GET", endpoint)

    def get_account_market_value_summary(self) -> dict:
        """
        Provides a summary of the account's market value.

        Returns:
            dict: A summary of the account's market value.

            Example return value:
            {
                "EUR": {
                    "total_cash": "194",
                    "settled_cash": "194",
                    "MTD Interest": "0",
                    "stock": "0",
                    "options": "0",
                    "futures": "0",
                    "future_options": "0",
                    "funds": "0",
                    "dividends_receivable": "0",
                    "mutual_funds": "0",
                    "money_market": "0",
                    "bonds": "0",
                    "Govt Bonds": "0",
                    "t_bills": "0",
                    "warrants": "0",
                    "issuer_option": "0",
                    "commodity": "0",
                    "Notional CFD": "0",
                    "cfd": "0",
                    "Cryptocurrency": "0",
                    "net_liquidation": "194",
                    "unrealized_pnl": "0",
                    "realized_pnl": "0",
                    "Exchange Rate": "1.092525"
                },
                "HKD": {
                    "total_cash": "0",
                    "settled_cash": "0",
                    "MTD Interest": "0",
                    "stock": "19,441",
                    "options": "0",
                    "futures": "0",
                    "future_options": "0",
                    "funds": "0",
                    "dividends_receivable": "0",
                    "mutual_funds": "0",
                    "money_market": "0",
                    "bonds": "0",
                    "Govt Bonds": "0",
                    "t_bills": "0",
                    "warrants": "0",
                    "issuer_option": "0",
                    "commodity": "0",
                    "Notional CFD": "0",
                    "cfd": "0",
                    "Cryptocurrency": "0",
                    "net_liquidation": "19,441",
                    "unrealized_pnl": "4,857",
                    "realized_pnl": "0",
                    "Exchange Rate": "0.1278515"
                },
                ...
                "Total (in USD)": {
                    "total_cash": "-401,646",
                    "settled_cash": "-401,646",
                    "MTD Interest": "-549",
                    "stock": "1,694,154",
                    "options": "0",
                    "futures": "-212",
                    "future_options": "0",
                    "funds": "0",
                    "dividends_receivable": "0",
                    "mutual_funds": "0",
                    "money_market": "0",
                    "bonds": "0",
                    "Govt Bonds": "0",
                    "t_bills": "0",
                    "warrants": "0",
                    "issuer_option": "0",
                    "commodity": "0",
                    "Notional CFD": "0",
                    "cfd": "0",
                    "Cryptocurrency": "0",
                    "net_liquidation": "1,291,959",
                    "unrealized_pnl": "253,896",
                    "realized_pnl": "0",
                    "Exchange Rate": "1.00"
                }
            }
        """
        endpoint = f"iserver/account/{self.account_id}/summary/market_value"
        return self._request("GET", endpoint)

    def get_user_accounts(self) -> dict:
        """
        Retrieve brokerage accounts for the current user.

        This method returns a list of accounts that the user has trading access to, along with their respective aliases
        and the currently selected account. This endpoint must be called before modifying an order or querying open orders.

        Returns:
            dict: An object containing valid accounts and their properties regarding trading access.

            Example return value:
            {
                "accounts": ["All", "U1234567", "U2234567", "U3234567"],
                "acctProps": {
                    "All": {
                        "hasChildAccounts": false,
                        "supportsCashQty": false,
                        "supportsFractions": false
                    },
                    "U1234567": {
                        "hasChildAccounts": false,
                        "supportsCashQty": true,
                        "supportsFractions": true
                    },
                    ...
                },
                "aliases": {
                    "All": "All",
                    "U1234567": "U1234567",
                    ...
                },
                "allowFeatures": {
                    "showGFIS": true,
                    ...
                },
                "chartPeriods": {
                    "STK": ["*"],
                    ...
                },
                "groups": ["All"],
                "profiles": [],
                "selectedAccount": "U1234567",
                "serverInfo": {
                    "serverName": "server",
                    "serverVersion": "Build 99.99.9, May 22, 2020 4:19:22 PM"
                },
                "sessionId": "65ee8a41.0000001e",
                "isFT": false,
                "isPaper": true
            }
        """
        return self._request("GET", "iserver/accounts")

    def initialize_brokerage_session(self, session_init_request: dict) -> dict:
        """
        Initialize the brokerage session.

        After retrieving the access token and subsequent Live Session Token, customers can initialize their brokerage
        session with the ssodh/init endpoint.

        Args:
            session_init_request (dict): The request body containing the session initialization parameters.

        Returns:
            dict: An object detailing the brokerage session status.

            Example return value:
            {
                "authenticated": true,
                "competing": false,
                "connected": true,
                "message": "",
                "MAC": "98:F2:B3:23:BF:A0",
                "serverInfo": {
                    "serverName": "JifN19053",
                    "serverVersion": "Build 10.25.0p, Dec 5, 2023 5:48:12 PM"
                }
            }
        """
        return self._request("POST", "iserver/auth/ssodh/init", json=session_init_request)

    def get_auth_status(self) -> dict:
        """
        Retrieve the current authentication status of the brokerage session.

        This endpoint checks the authentication status to the Brokerage system. Market data and trading are not
        possible if the session is not authenticated.

        Returns:
            dict: Detailed status of the brokerage session.

            Example return value:
            {
                "authenticated": true,
                "competing": false,
                "connected": true,
                "message": "",
                "MAC": "12:B:B3:23:BF:A0",
                "serverInfo": {
                    "serverName": "JifN19053",
                    "serverVersion": "Build 10.25.0p, Dec 5, 2023 5:48:12 PM"
                },
                "fail": ""
            }
        """
        return self._request("POST", "iserver/auth/status")

    def search_contract_rules(
            self, conid: int, is_buy: bool = True, modify_order: bool = False, order_id: int = None) -> dict:
        """
        Search for trading related rules for a specific contract and side.

        Args:
            conid (int): Contract identifier for the interested contract.
            is_buy (bool, optional): Set to true for Buy Orders, false for Sell Orders. Defaults to true.
            modify_order (bool, optional): Used to find trading rules related to an existing order. Defaults to false.
            order_id (int, optional): Specify the order identifier used for tracking a given order.

        Returns:
            dict: An array of objects detailing contract information.

            Example return value:
            {
                "algoEligible": true,
                "overnightEligible": true,
                "costReport": false,
                "canTradeAcctIds": ["U1234567", "U1234568", "U1234569"],
                "error": null,
                "orderTypes": ["limit", "midprice", "market", "stop", "stop_limit", "mit", "lit", "trailing_stop", "trailing_stop_limit", "relative", "marketonclose", "limitonclose"],
                "ibAlgoTypes": ["limit", "stop_limit", "lit", "trailing_stop_limit", "relative", "marketonclose", "limitonclose"],
                "fraqTypes": ["limit", "market", "stop", "stop_limit", "mit", "lit", "trailing_stop", "trailing_stop_limit"],
                "forceOrderPreview": false,
                "defaultSize": 100,
                "cashSize": 0.0,
                "sizeIncrement": 100,
                "cashCcy": "USD",
                "priceMagnifier": null,
                "increment": 0.01,
                "incrementDigits": 2,
                "preview": true,
                "limitPrice": 198.22,
                "stopPrice": 198.22,
                "hasSecondary": true
            }
        """
        payload = {
            "conid": conid,
            "isBuy": is_buy,
            "modifyOrder": modify_order
        }
        if order_id is not None:
            payload["orderId"] = order_id

        return self._request("POST", "iserver/contract/rules", json=payload)

    def search_algo_params(self, conid: str, algos: str = None, add_description: int = 0, add_params: int = 0) -> dict:
        """
        Search for supported IB Algos for a specific contract.

        Args:
            conid (str): Contract identifier for the requested contract of interest.
            algos (str, optional): List of algo ids delimited by ";" to filter by (max of 8). Case sensitive.
            add_description (int, optional): Whether to add algo descriptions to response. Set to 1 for yes, 0 for no. Defaults to 0.
            add_params (int, optional): Whether to show algo parameters. Set to 1 for yes, 0 for no. Defaults to 0.

        Returns:
            dict: A list of available algos and a description of their behavior.

            Example return value:
            {
                "algos": [
                    {"name": "Adaptive", "id": "Adaptive"},
                    {"name": "Arrival Price", "id": "ArrivalPx"},
                    {"name": "Close Price", "id": "ClosePx"},
                    {"name": "DarkIce", "id": "DarkIce"},
                    {"name": "Percentage of Volume", "id": "PctVol"},
                    {"name": "TWAP", "id": "Twap"},
                    {"name": "VWAP", "id": "Vwap"}
                ]
            }
        """
        params = {
            "algos": algos,
            "addDescription": add_description,
            "addParams": add_params
        }
        return self._request("GET", f"iserver/contract/{conid}/algos", params=params)

    def get_contract_info(self, conid: str) -> dict:
        """
        Retrieve full contract details for the given contract identifier.

        Args:
            conid (str): Contract identifier for the requested contract of interest.

        Returns:
            dict: Contract information, including details like symbol, instrument type, trading class, and valid exchanges.

            Example return value for stock contract:
            {
                "cfi_code": "",
                "symbol": "IBM",
                "cusip": null,
                "expiry_full": null,
                "con_id": 8314,
                "maturity_date": null,
                "industry": "Computers",
                "instrument_type": "STK",
                "trading_class": "IBM",
                "valid_exchanges": "SMART,AMEX,NYSE,CBOE,...",
                "allow_sell_long": false,
                "is_zero_commission_security": false,
                "local_symbol": "IBM",
                "currency": "USD",
                "company_name": "INTL BUSINESS MACHINES CORP",
                "smart_available": true,
                "exchange": "SMART",
                "category": "Computer Services"
            }
        """
        return self._request("GET", f"iserver/contract/{conid}/info")

    def get_contract_info_and_rules(self, conid: str) -> dict:
        """
        Retrieve full contract details and associated rules for the given contract identifier.

        Args:
            conid (str): Contract identifier for the requested contract of interest.

        Returns:
            dict: Contract information and rules, including details like symbol, instrument type, trading class,
                  valid exchanges, and trading rules.

            Example return value for stock contract:
            {
                "cfi_code": "",
                "symbol": "IBM",
                "cusip": null,
                "expiry_full": null,
                "con_id": 8314,
                "maturity_date": null,
                "industry": "Computers",
                "instrument_type": "STK",
                "trading_class": "IBM",
                "valid_exchanges": "SMART,AMEX,NYSE,CBOE,...",
                "allow_sell_long": false,
                "is_zero_commission_security": false,
                "local_symbol": "IBM",
                "currency": "USD",
                "company_name": "INTL BUSINESS MACHINES CORP",
                "smart_available": true,
                "exchange": "SMART",
                "category": "Computer Services",
                "rules": {
                    "algoEligible": true,
                    "overnightEligible": true,
                    "orderTypes": ["limit", "market", "stop", ...],
                    "defaultSize": 100,
                    "sizeIncrement": 100,
                    ...
                }
            }
        """
        return self._request("GET", f"iserver/contract/{conid}/info-and-rules")

    def get_currency_pairs(self, currency: str) -> dict:
        """
        Obtain available currency pairs corresponding to the given target currency.

        Args:
            currency (str): Specify the target currency to receive official pairs of.

        Returns:
            dict: A dictionary containing valid forex pairs for the specified currency.
                  The currency can apply as both the target or base currency.

            Example return value:
            {
                "USD": [
                    {"symbol": "USD.SGD", "conid": 37928772, "ccyPair": "SGD"},
                    {"symbol": "USD.RON", "conid": 38231133, "ccyPair": "RON"},
                    {"symbol": "USD.CZK", "conid": 34838409, "ccyPair": "CZK"}
                ]
            }
        """
        return self._request("GET", "iserver/currency/pairs", params={"currency": currency})

    def set_dynamic_account(self, acct_id: str) -> dict:
        """
        Set the active dynamic account for future requests.

        Args:
            acct_id (str): The account ID that should be set.

        Returns:
            dict: A response indicating whether the account was successfully set.

            Example return value:
            {
                "set": true,
                "acctId": "U2234567"
            }
        """
        payload = {"acctId": acct_id}
        return self._request("POST", "iserver/dynaccount", json=payload)

    def get_exchange_rate(self, source: str, target: str) -> dict:
        """
        Obtain the exchange rates of the specified currency pair.

        Args:
            source (str): The base currency to request data for.
            target (str): The quote currency to request data for.

        Returns:
            dict: A response containing the exchange rate for the currency pair.

            Example return value:
            {
                "rate": 0.91324199
            }
        """
        params = {"source": source, "target": target}
        return self._request("GET", "iserver/exchangerate", params=params)

    def get_historical_data(self, conid: str, period: str, bar: str, exchange: str = None, start_time: str = None,
                            outside_rth: bool = False) -> dict:
        """
        Request historical data for an instrument in the form of OHLC bars.

        Args:
            conid (str): IB contract ID of the requested instrument.
            period (str): A time duration for the data request (e.g., "6d").
            bar (str): The width of the bars (e.g., "5mins").
            exchange (str, optional): The exchange from which data is requested (e.g., "NYSE").
            start_time (str, optional): A fixed UTC date-time reference point in the format YYYYMMDD-hh:mm:ss.
            outside_rth (bool, optional): Whether to include data outside of regular trading hours.

        Returns:
            dict: A response containing historical market data.

            Example return value:
            {
                "serverid": "20477",
                "symbol": "AAPL",
                "text": "APPLE INC",
                "data": [
                    {
                        "t": 1692345600000,
                        "o": 173.4,
                        "c": 174.7,
                        "h": 175.1,
                        "l": 171.7,
                        "v": 472117.45
                    }
                ]
            }
        """
        params = {
            "conid": conid,
            "period": period,
            "bar": bar,
            "exchange": exchange,
            "startTime": start_time,
            "outsideRth": outside_rth
        }
        return self._request("GET", "iserver/marketdata/history", params=params)

    def get_market_data_snapshot(self, conids: str, fields: str = "31,55,84,86,85,88,6004,6008,6509") -> dict:
        """
        Get a live market data snapshot for the given contract identifier(s).

        A pre-flight request must be made prior to ever receiving data. For some fields, it may
        take more than a few moments to receive information.

        The endpoint `get_user_accounts()` must be called prior to `get_market_data_snapshot()`.

        For derivative contracts the endpoint `search_secdef()` must be called first.

        Args:
            conids (str): Contract identifier(s) for the contract of interest. Can be a comma-separated list.
            fields (str, optional): Specific fields to request in the snapshot. Valid field type codes include:

            - 31 - Last Price. The last price at which the contract traded. May contain one of the following prefixes: C - Previous day's closing price. H - Trading has halted.
            - 55 - Symbol.
            - 58 - Text.
            - 70 - High. Current day high price
            - 71 - Low. Current day low price
            - 73 - Market Value. The current market value of your position in the security. Market Value is calculated with real time market data (even when not subscribed to market data).
            - 74 - Avg Price. The average price of the position.
            - 75 - Unrealized PnL. Unrealized profit or loss. Unrealized PnL is calculated with real time market data (even when not subscribed to market data).
            - 76 - Formatted position.
            - 77 - Formatted Unrealized PnL.
            - 78 - Daily PnL. Your profit or loss of the day since prior close. Daily PnL is calculated with real time market data (even when not subscribed to market data).
            - 79 - Realized PnL. Realized profit or loss. Realized PnL is calculated with real time market data (even when not subscribed to market data).
            - 80 - Unrealized PnL %. Unrealized profit or loss expressed in percentage.
            - 82 - Change. The difference between the last price and the close on the previous trading day
            - 83 - Change %. The difference between the last price and the close on the previous trading day in percentage.
            - 84 - Bid Price. The highest-priced bid on the contract.
            - 85 - Ask Size. The number of contracts or shares offered at the ask price. For US stocks
            - 86 - Ask Price. The lowest-priced offer on the contract.
            - 87 - Volume. Volume for the day
            - 88 - Bid Size. The number of contracts or shares bid for at the bid price. For US stocks
            - 6004 - Exchange.
            - 6008 - Conid. Contract identifier from IBKR's database.
            - 6070 - SecType. The asset class of the instrument.
            - 6072 - Months.
            - 6073 - Regular Expiry.
            - 6119 - Marker for market data delivery method (similar to request id).
            - 6457 - Underlying Conid. Use /trsrv/secdef to get more information about the security.
            - 6508 - Service Params..
            - 6509 - Market Data Availability. The field may contain three chars. First char defines: R = RealTime, D = Delayed, Z = Frozen, Y = Frozen Delayed, N = Not Subscribed, i - incomplete, v - VDR Exempt (Vendor Display Rule 603c). Second char defines: P = Snapshot, p = Consolidated. Third char defines: B = Book. RealTime Data is relayed back in real time without delay, market data subscription(s) are required. Delayed - Data is relayed back 15-20 min delayed. Frozen - Last recorded data at market close. relayed back in real time. Frozen Delayed - Last recorded data at market close, relayed back delayed. Not Subscribed - User does not have the required market data subscription(s) to relay back either real time or delayed data. Snapshot - Snapshot request is available for contract. Consolidated - Market data is aggregated across multiple exchanges or venues. Book - Top of the book data is available for contract.
            - 7051 - Company name.
            - 7057 - Ask Exch. Displays the exchange(s) offering the SMART price. A=AMEX, C=CBOE, I=ISE, X=PHLX, N=PSE, B=BOX, Q=NASDAQOM, Z=BATS, W=CBOE2, T=NASDAQBX, M=MIAX, H=GEMINI, E=EDGX, J=MERCURY
            - 7058 - Last Exch. Displays the exchange(s) offering the SMART price. A=AMEX, C=CBOE, I=ISE, X=PHLX, N=PSE, B=BOX, Q=NASDAQOM, Z=BATS, W=CBOE2, T=NASDAQBX, M=MIAX, H=GEMINI, E=EDGX, J=MERCURY
            - 7059 - Last Size. The number of unites traded at the last price
            - 7068 - Bid Exch. Displays the exchange(s) offering the SMART price. A=AMEX, C=CBOE, I=ISE, X=PHLX, N=PSE, B=BOX, Q=NASDAQOM, Z=BATS, W=CBOE2, T=NASDAQBX, M=MIAX, H=GEMINI, E=EDGX, J=MERCURY
            - 7084 - Implied Vol./Hist. Vol %. The ratio of the implied volatility over the historical volatility, expressed as a percentage.
            - 7085 - Put/Call Interest. Put option open interest/call option open interest for the trading day.
            - 7086 - Put/Call Volume. Put option volume/call option volume for the trading day.
            - 7087 - Hist. Vol. %. 30-day real-time historical volatility.
            - 7088 - Hist. Vol. Close %. Shows the historical volatility based on previous close price.
            - 7089 - Opt. Volume. Option Volume
            - 7094 - Conid + Exchange.
            - 7184 - canBeTraded. If contract is a trade-able instrument. Returns 1(true) or 0(false).
            - 7219 - Contract Description.
            - 7220 - Contract Description.
            - 7221 - Listing Exchange.
            - 7280 - Industry. Displays the type of industry under which the underlying company can be categorized.
            - 7281 - Category. Displays a more detailed level of description within the industry under which the underlying company can be categorized.
            - 7282 - Average Volume. The average daily trading volume over 90 days.
            - 7283 - Option Implied Vol. %. A prediction of how volatile an underlying will be in the future.At the market volatility estimated for a maturity thirty calendar days forward of the current trading day, and based on option prices from two consecutive expiration months. To query the Implied Vol. % of a specific strike refer to field 7633.
            - 7284 - Historical volatility %. Deprecated
            - 7285 - Put/Call Ratio.
            - 7286 - Dividend Amount. Displays the amount of the next dividend.
            - 7287 - Dividend Yield %. This value is the toal of the expected dividend payments over the next twelve months per share divided by the Current Price and is expressed as a percentage. For derivatives
            - 7288 - Ex-date of the dividend.
            - 7289 - Market Cap.
            - 7290 - P/E.
            - 7291 - EPS.
            - 7292 - Cost Basis. Your current position in this security multiplied by the average price and multiplier.
            - 7293 - 52 Week High. The highest price for the past 52 weeks.
            - 7294 - 52 Week Low. The lowest price for the past 52 weeks.
            - 7295 - Open. Today's opening price.
            - 7296 - Close. Today's closing price.
            - 7308 - Delta. The ratio of the change in the price of the option to the corresponding change in the price of the underlying.
            - 7309 - Gamma. The rate of change for the delta with respect to the underlying asset's price.
            - 7310 - Theta. A measure of the rate of decline the value of an option due to the passage of time.
            - 7311 - Vega. The amount that the price of an option changes compared to a 1% change in the volatility.
            - 7607 - Opt. Volume Change %. Today's option volume as a percentage of the average option volume.
            - 7633 - Implied Vol. %. The implied volatility for the specific strike of the option in percentage. To query the Option Implied Vol. % from the underlying refer to field 7283.
            - 7635 - Mark. The mark price is
            - 7636 - Shortable Shares. Number of shares available for shorting.
            - 7637 - Fee Rate. Interest rate charged on borrowed shares.
            - 7638 - Option Open Interest.
            - 7639 - % of Mark Value. Displays the market value of the contract as a percentage of the total market value of the account. Mark Value is calculated with real time market data (even when not subscribed to market data).
            - 7644 - Shortable. Describes the level of difficulty with which the security can be sold short.
            - 7655 - Morningstar Rating. Displays Morningstar Rating provided value. Requires Morningstar subscription.
            - 7671 - Dividends. This value is the total of the expected dividend payments over the next twelve months per share.
            - 7672 - Dividends TTM. This value is the total of the expected dividend payments over the last twelve months per share.
            - 7674 - EMA(200). Exponential moving average (N=200).
            - 7675 - EMA(100). Exponential moving average (N=100).
            - 7676 - EMA(50). Exponential moving average (N=50).
            - 7677 - EMA(20). Exponential moving average (N=20).
            - 7678 - Price/EMA(200). Price to Exponential moving average (N=200) ratio -1
            - 7679 - Price/EMA(100). Price to Exponential moving average (N=100) ratio -1
            - 7724 - Price/EMA(50). Price to Exponential moving average (N=50) ratio -1
            - 7681 - Price/EMA(20). Price to Exponential moving average (N=20) ratio -1
            - 7682 - Change Since Open. The difference between the last price and the open price.
            - 7683 - Upcoming Event. Shows the next major company event. Requires Wall Street Horizon subscription.
            - 7684 - Upcoming Event Date. The date of the next major company event. Requires Wall Street Horizon subscription.
            - 7685 - Upcoming Analyst Meeting. The date and time of the next scheduled analyst meeting. Requires Wall Street Horizon subscription.
            - 7686 - Upcoming Earnings. The date and time of the next scheduled earnings/earnings call event. Requires Wall Street Horizon subscription.
            - 7687 - Upcoming Misc Event. The date and time of the next shareholder meeting
            - 7688 - Recent Analyst Meeting. The date and time of the most recent analyst meeting. Requires Wall Street Horizon subscription.
            - 7689 - Recent Earnings. The date and time of the most recent earnings/earning call event. Requires Wall Street Horizon subscription.
            - 7690 - Recent Misc Event. The date and time of the most recent shareholder meeting
            - 7694 - Probability of Max Return. Customer implied probability of maximum potential gain.
            - 7695 - Break Even. Break even points
            - 7696 - SPX Delta. Beta Weighted Delta is calculated using the formula; Delta x dollar adjusted beta
            - 7697 - Futures Open Interest. Total number of outstanding futures contracts
            - 7698 - Last Yield. Implied yield of the bond if it is purchased at the current last price. Last yield is calculated using the Last price on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher.
            - 7699 - Bid Yield. Implied yield of the bond if it is purchased at the current bid price. Bid yield is calculated using the Ask on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher.
            - 7700 - Probability of Max Return. Customer implied probability of maximum potential gain.
            - 7702 - Probability of Max Loss. Customer implied probability of maximum potential loss.
            - 7703 - Profit Probability. Customer implied probability of any gain.
            - 7704 - Organization Type.
            - 7705 - Debt Class.
            - 7706 - Ratings. Ratings issued for bond contract.
            - 7707 - Bond State Code.
            - 7708 - Bond Type.
            - 7714 - Last Trading Date.
            - 7715 - Issue Date.
            - 7718 - Beta. Beta is against standard index.
            - 7720 - Ask Yield. Implied yield of the bond if it is purchased at the current offer. Ask yield is calculated using the Bid on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher.
            - 7741 - Prior Close. Yesterday's closing price
            - 7762 - Volume Long. High precision volume for the day. For formatted volume refer to field 87.
            - 7768 - hasTradingPermissions. if user has trading permissions for specified contract. Returns 1(true) or 0(false).
            - 7920 - Daily PnL Raw. Your profit or loss of the day since prior close. Daily PnL is calculated with real-time market data (even when not subscribed to market data).
            - 7921 - Cost Basis Raw. Your current position in this security multiplied by the average price and and multiplier.

        Returns:
            dict: A response containing the market data snapshot.

            Example return value:
            [
                {
                    "55": "JPY",
                    "88": "41",
                    "conidEx": "395718531",
                    "_updated": 1729662392190,
                    "server_id": "q2",
                    "6509": "DPB",
                    "conid": 395718531,
                    "6119": "q2",
                    "84": "0.0066210",
                    "85": "12",
                    "31": "0.0066210",
                    "6508": "&serviceID1=784&serviceID2=798&serviceID3=778&serviceID4=713&serviceID5=714&serviceID6=715",
                    "86": "0.0066215"
                }
            ]
        """
        params = {
            "conids": conids,
            "fields": fields
        }
        result = self._request("GET", "iserver/marketdata/snapshot", params=params)
        return [self.field_mapping(x) for x in result]

    def unsubscribe_market_data(self, conid: int) -> dict:
        """
        Instruct IServer to close its backend stream for the specified instrument.

        Args:
            conid (int): The IB contract ID of the instrument whose market data feed is to be unsubscribed.

        Returns:
            dict: A response acknowledging the successful request.

            Example return value:
            {
                "success": true
            }
        """
        body = {
            "conid": conid
        }
        return self._request("POST", "iserver/marketdata/unsubscribe", json=body)

    def unsubscribe_all_market_data(self) -> dict:
        """
        Instruct IServer to close all of its open backend data streams for all instruments.

        Returns:
            dict: A response indicating the successful request to unsubscribe all streams.

            Example return value:
            {
                "unsubscribed": true
            }
        """
        return self._request("GET", "iserver/marketdata/unsubscribeall")

    def respond_to_server_prompt(self, order_id: int, req_id: str, text: str) -> str:
        """
        Respond to a server prompt received via ntf websocket message.

        Args:
            order_id (int): IB-assigned order identifier obtained from the ntf websocket message.
            req_id (str): IB-assigned request identifier obtained from the ntf websocket message.
            text (str): The selected value from the "options" array delivered in the server prompt ntf websocket message.

        Returns:
            str: Confirmation of successful reply to the server prompt.

            Example return value:
            "Reply submitted successfully."
        """
        payload = {
            "orderId": order_id,
            "reqId": req_id,
            "text": text
        }
        response = self._request("POST", "iserver/notification", json=payload)
        return response

    def suppress_order_replies(self, message_ids: list) -> dict:
        """
        Suppress the specified order reply messages for the duration of the brokerage session.

        Args:
            message_ids (list): Array of order reply messageId identifier strings to be suppressed.

        Returns:
            dict: Confirms the successful suppression of specified messageIds.

            Example return value:
            {"status": "submitted"}
        """
        payload = {
            "messageIds": message_ids
        }
        response = self._request("POST", "iserver/questions/suppress", json=payload)
        return response

    def reset_order_reply_suppression(self) -> dict:
        """
        Removes suppression of all order reply messages that were previously suppressed
        in the current brokerage session.

        Returns:
            dict: Confirms the successful removal of suppression.

            Example return value:
            {"status": "submitted"}
        """
        response = self._request("POST", "iserver/questions/suppress/reset")
        return response

    def reauthenticate(self) -> dict:
        """
        Re-authenticate the Brokerage Session.

        This method triggers a reauthentication to the Brokerage system,
        applicable when using the CP Gateway and as long as there is a valid brokerage session.

        Returns:
            dict: Confirmation that the reauthentication action was performed successfully.

            Example return value:
            {"message": "triggered"}
        """
        response = self._request("GET", "iserver/reauthenticate")
        return response

    def confirm_order_reply(self, reply_id: str, confirmed: bool) -> dict:
        """
        Confirm an order reply message and proceed with the submission of the order ticket.

        Args:
            reply_id (str): The UUID of the reply message to be confirmed,
                            obtained from an order submission response.
            confirmed (bool): If true, answers the question affirmatively and
                              proceeds with order submission.

        Returns:
            dict: Status of the reply.

            Example return values:
            - Successful confirmation:
              {"order_id": "1370093239", "order_status": "PreSubmitted", "encrypt_message": "1"}
            - Order reply message:
              {"id": "99097238-9824-4830-84ef-46979aa22593", "isSuppressed": false,
               "message": ["You are submitting an order without market data..."],
               "messageIds": ["o354"]}
            - Order submission error:
              {"error": "Order not confirmed"}
            - Reply ID not found:
              {"error": "reply id not found: '99097238-9824-4830-84ef-46979aa22593'"}
        """
        endpoint = f"iserver/reply/{reply_id}"
        body = {"confirmed": confirmed}
        response = self._request("POST", endpoint, json=body)
        return response

    def get_scanner_params(self) -> dict:
        """
        Returns the parameters available for the Iserver scanner request.

        Returns:
            dict: A dictionary containing all available scanner parameters.

            Example return values:
            {
                "scan_type_list": [
                    {
                        "display_name": "Top % Gainers",
                        "code": "TOP_PERC_GAIN",
                        "instruments": [
                            "STK", "ETF.EQ.US", "ETF.FI.US", "FUT.US",
                            "IND.US", "STOCK.NA", "FUT.NA", "SSF.NA",
                            "STOCK.EU", "FUT.EU", "IND.EU", "SSF.EU",
                            "STOCK.ME", "STOCK.HK", "FUT.HK", "IND.HK",
                            "SSF.HK"
                        ]
                    }
                ],
                "instrument_list": [
                    {
                        "display_name": "US Stocks",
                        "type": "STK",
                        "filters": [
                            "afterHoursChange", "afterHoursChangePerc",
                            "avgOptVolume", "avgPriceTarget", "avgRating"
                        ]
                    }
                ],
                "filter_list": [
                    {
                        "group": "afterHoursChangeAbove",
                        "display_name": "After-Hours Change Above",
                        "code": "afterHoursChangeAbove",
                        "type": "non-range"
                    },
                    {
                        "group": "stkTypes",
                        "display_name": "Stock type",
                        "code": "stkTypes",
                        "combo_values": [{"default": True, "vendor": None}]
                    }
                ],
                "location_tree": [
                    {
                        "display_name": "US Stocks",
                        "type": "STK",
                        "locations": [
                            {"display_name": "Listed/NASDAQ", "type": "STK.US.MAJOR", "locations": []},
                            {"display_name": "OTCMarkets", "type": "STK.US.MINOR", "locations": []}
                        ]
                    },
                    {
                        "display_name": "US Futures",
                        "type": "FUT.US",
                        "locations": [
                            {"display_name": "CME", "type": "FUT.CME"},
                            {"display_name": "CBOT", "type": "FUT.CBOT"},
                            {"display_name": "NYMEX", "type": "FUT.NYMEX"}
                        ]
                    }
                ]
            }
        """
        endpoint = "iserver/scanner/params"
        return self._request("GET", endpoint)

    def run_scanner(self, instrument: str, location: str, scan_type: str, filters: list) -> dict:
        """
        Searches for contracts according to the filters specified.

        Parameters:
            instrument (str): The type of instrument (e.g., "STK").
            location (str): The market location (e.g., "STK.US.MAJOR").
            scan_type (str): The type of scan to perform (e.g., "TOP_TRADE_COUNT").
            filters (list): A list of filters to apply to the scan.

        Returns:
            dict: A dictionary containing the results of the scanner run.

            Example return values:
            {
                "contracts": [
                    {
                        "server_id": "0",
                        "column_name": "Trades",
                        "symbol": "TSLA",
                        "conidex": "76792991",
                        "con_id": 76792991,
                        "available_chart_periods": "#R|1",
                        "company_name": "TESLA INC",
                        "scan_data": "221.521K",
                        "contract_description_1": "TSLA",
                        "listing_exchange": "NASDAQ.NMS",
                        "sec_type": "STK"
                    },
                    {
                        "server_id": "1",
                        "symbol": "SPY",
                        "conidex": "756733",
                        "con_id": 756733,
                        "available_chart_periods": "#R|1",
                        "company_name": "SPDR S&P 500 ETF TRUST",
                        "scan_data": "123.661K",
                        "contract_description_1": "SPY",
                        "listing_exchange": "ARCA",
                        "sec_type": "STK"
                    }
                ],
                "scan_data_column_name": "Trades"
            }
        """
        endpoint = "iserver/scanner/run"
        request_body = {
            "instrument": instrument,
            "location": location,
            "type": scan_type,
            "filter": filters
        }
        return self._request("POST", endpoint, json=request_body)

    def get_bond_filters(self, symbol: str, issueId: str) -> dict:
        """
        Search for bond filter information based on the specified parameters.

        This method requests a list of filters relating to a given bond issuer ID.
        The issuerId is retrieved from the /iserver/secdef/search endpoint.

        Args:
            symbol (str): This should always be set to "BOND".
                Example: "BOND"
            issueId (str): Specifies the issuerId value used to designate the bond issuer type.
                Example: "e1400715"

        Returns:
            dict: A dictionary containing the bond filter information,
            which includes various attributes like maturity date, issue date,
            coupon rate, and currency. Example return value:

            {
                "bondFilters": [
                    {
                        "displayText": "Maturity Date",
                        "columnId": 27,
                        "options": [
                            {"text": "Jan 2025", "value": "202501"},
                            {"text": "Dec 2028", "value": "202812"}
                        ]
                    },
                    {
                        "displayText": "Issue Date",
                        "columnId": 28,
                        "options": [
                            {"text": "Sep 18 2014", "value": "20140918"},
                            {"text": "Apr 09 2015", "value": "20150409"}
                        ]
                    },
                    {
                        "displayText": "Coupon",
                        "columnId": 25,
                        "options": [
                            {"value": "1.301"},
                            {"value": "1.34"}
                        ]
                    },
                    {
                        "displayText": "Currency",
                        "columnId": 5,
                        "options": [
                            {"value": "EUR"},
                            {"value": "USD"}
                        ]
                    }
                ]
            }

        Raises:
            HTTPError: If the request fails or if the server response indicates an error.
        """
        params = {
            "symbol": symbol,
            "issueId": issueId
        }
        return self._request("GET", "iserver/secdef/bond-filters", params=params)

    def get_secdef_info(self, conid: str = None, sectype: str = None, month: str = None,
                        exchange: str = None, strike: float = None, right: str = None,
                        issuer_id: str = None, filters: str = None) -> dict:
        """
        Retrieve security definition information for a contract.

        Parameters:
            conid (str, optional): Contract identifier of the underlying.
            sectype (str, optional): Security type of the requested contract.
            month (str, optional): Expiration month for the given derivative.
            exchange (str, optional): Designate the exchange for the contract.
            strike (float, optional): Strike price for the requested contract details.
            right (str, optional): Set the right for the given contract.
                                   Options: 'C' for Call options, 'P' for Put options.
            issuer_id (str, optional): Set the issuerId for the bond issuer type.
            filters (str, optional): Comma-separated list of additional filters (for BOND).

        Returns:
            dict: A dictionary containing the security definition information.

            Example return values:
            {
                "conid": 8314,
                "ticker": "IBM",
                "secType": "STK",
                "listingExchange": "NYSE",
                "exchange": "SMART",
                "companyName": "INTL BUSINESS MACHINES CORP",
                "currency": "USD",
                "validExchanges": "SMART,AMEX,NYSE,CBOE,PHLX,ISE,CHX,ARCA,NASDAQ,DRCTEDGE,BEX,BATS,EDGEA,BYX,NYSEDARK,NASDDARK,IEX,EDGX,FOXRIVER,PEARL,NYSENAT,IEXMID,JANELP,IMCLP,LTSE,MEMX,JUMPLP,OLDMCLP,RBCCMALP,IBEOS,GSLP,BLUEOCEAN,OVERNIGHT,JANEMID,G1XLP,PSX",
                "priceRendering": null,
                "maturityDate": null,
                "right": "?",
                "strike": 0.0
            }
        """
        endpoint = "iserver/secdef/info"
        params = {
            "conid": conid,
            "sectype": sectype,
            "month": month,
            "exchange": exchange,
            "strike": strike,
            "right": right,
            "issuerId": issuer_id,
            "filters": filters
        }
        return self._request("GET", endpoint, params={k: v for k, v in params.items() if v is not None})

    def search_secdef(self, symbol: str = None, sec_type: str = "STK", name: bool = None,
                      more: bool = None, fund: bool = None, fund_family_conid_ex: str = None,
                      pattern: bool = None, referrer: str = None) -> list:
        """
        Returns a list of contracts based on the search symbol provided as a query param.

        Parameters:
        - symbol (str): The ticker symbol, bond issuer type, or company name of the equity you are looking to trade. Example: "AAPL".
        - sec_type (str): Available underlying security types. Default is "STK". Options are: "STK", "IND", "BOND".
        - name (bool): Denotes if the symbol value is the ticker symbol or part of the company's name.
        - more (bool): Additional search parameter.
        - fund (bool): Indicates if this is a fund search.
        - fund_family_conid_ex (str): Additional identifier for the fund family.
        - pattern (bool): Indicates if a pattern search is to be performed.
        - referrer (str): Referrer information for the search.

        Returns:
        - list: An array of objects detailing contract information.

        Example return value:
        [
            {
                "conid": "8314",
                "companyHeader": "INTL BUSINESS MACHINES CORP - NYSE",
                "companyName": "INTL BUSINESS MACHINES CORP",
                "symbol": "IBM",
                "description": "NYSE",
                "sections": [
                    {"secType": "STK"},
                    {"secType": "OPT", "months": "MAR24;APR24;MAY24;..."},
                    {"secType": "BOND"}
                ]
            },
            ...
        ]
        """
        params = {
            "symbol": symbol,
            "secType": sec_type,
            "name": name,
            "more": more,
            "fund": fund,
            "fundFamilyConidEx": fund_family_conid_ex,
            "pattern": pattern,
            "referrer": referrer
        }
        return self._request("GET", "iserver/secdef/search", params=params)

    def get_strikes(self, conid: str, sectype: str, month: str, exchange: str = "SMART") -> dict:
        """
        Get strikes for a specified contract.

        Args:
            conid (str): Contract identifier of the underlying.
                         May also pass the final derivative conid directly.
                         Example: "265598".
            sectype (str): Security type of the requested contract of interest.
                           Example: "OPT".
            month (str): Expiration month for the given derivative.
                         Example: "JAN24".
            exchange (str, optional): Exchange from which derivatives should be retrieved from.
                                      Defaults to "SMART".
                                      Example: "NASDAQ".

        Returns:
            dict: A dictionary containing the security definition for the specified contract.

            Example return value:
            {
                "call": [70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0],
                "put": [70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0]
            }

        Raises:
            ValueError: If 'conid', 'sectype', or 'month' are not provided or invalid.
        """
        params = {
            "conid": conid,
            "sectype": sectype,
            "month": month,
            "exchange": exchange
        }
        return self._request("GET", "iserver/secdef/strikes", params=params)

    def get_watchlist(self, id: str) -> dict:
        """
        Retrieve details of a single watchlist stored in the username's settings.

        Args:
            id (str): Watchlist ID of the requested watchlist.
                       Example: "1234".

        Returns:
            dict: A dictionary containing the details of the specified watchlist.

            Example return value:
            {
                "id": "1234",
                "hash": "1234987651621",
                "name": "Test Watchlist",
                "readOnly": false,
                "instruments": [
                    {
                        "ST": "STK",
                        "C": "8314",
                        "conid": 8314,
                        "name": "INTL BUSINESS MACHINES CORP",
                        "fullName": "IBM",
                        "assetClass": "STK",
                        "ticker": "IBM",
                        "chineseName": ""
                    }
                ]
            }
        """
        params = {"id": id}
        return self._request("GET", "iserver/watchlist", params=params)

    def create_watchlist(self, watchlist: dict) -> dict:
        """
        Create a named watchlist by submitting a set of conids.

        Args:
            watchlist (dict): A dictionary containing the watchlist contents.
                              Must include 'id', 'name', and 'rows'.

        Returns:
            dict: A dictionary confirming the successful creation of the watchlist.

            Example return value:
            {
                "id": "1234",
                "hash": "1234987651621",
                "name": "Test Watchlist",
                "readOnly": false,
                "instruments": []
            }
        """
        return self._request("POST", "iserver/watchlist", json=watchlist)

    def delete_watchlist(self, id: str) -> dict:
        """
        Delete a specified watchlist from the username's settings.

        Args:
            id (str): Watchlist ID of the watchlist to be deleted.
                       Example: "1234".

        Returns:
            dict: A dictionary confirming the successful deletion of the watchlist.

            Example return value:
            {
                "data": {"deleted": "1234"},
                "action": "context",
                "MID": "2"
            }
        """
        params = {"id": id}
        return self._request("DELETE", "iserver/watchlist", params=params)

    def get_watchlists(self, sc: str = None) -> dict:
        """
        Retrieve all saved watchlists stored on IB backend for the username in use
        in the current Web API session.

        Args:
            sc (str, optional): Filter to return only user-created watchlists.
                                Must be "USER_WATCHLIST" to apply this filter.

        Returns:
            dict: A dictionary containing the retrieved watchlists.

            Example return value:
            {
                "data": {
                    "scanners_only": false,
                    "show_scanners": false,
                    "bulk_delete": false,
                    "user_lists": [
                        {
                            "is_open": false,
                            "read_only": false,
                            "name": "Test Watchlist",
                            "modified": 1702581306241,
                            "id": "1234",
                            "type": "watchlist"
                        }
                    ]
                },
                "action": "content",
                "MID": "2"
            }
        """
        params = {}
        if sc is not None:
            params["SC"] = sc
        return self._request("GET", "iserver/watchlists", params=params)

    def logout(self) -> dict:
        """
        Logout of the current session.

        Logs the user out of the gateway session. Any further activity requires
        re-authentication.

        Returns:
            dict: A dictionary confirming the logout action.

            Example return value:
            {
                "status": true
            }
        """
        return self._request("POST", "logout")

    def get_regulatory_snapshot(self, conid: str) -> dict:
        """
        Request a regulatory snapshot for an instrument.

        WARNING: Each regulatory snapshot made will incur a fee of $0.01 USD to the account.
        This applies to both live and paper accounts.

        If you are already paying for, or are subscribed to, a specific US Network subscription,
        your account will not be charged.

        For stocks, there are individual exchange-specific market data subscriptions necessary
        to receive streaming quotes. For instance, for NYSE stocks this subscription is known
        as “Network A”, for ARCA/AMEX stocks it is called “Network B” and for NASDAQ stocks it is
        “Network C”. Each subscription is added a la carte and has a separate market data fee.

        Alternatively, there is also a “US Securities Snapshot Bundle” subscription which does
        not provide streaming data but which allows for real time calculated snapshots of US market
        NBBO prices. Making a request with this endpoint, the returned value is a calculation of
        the current market state based on data from all available exchanges.

        Args:
            conid (str): An IB contract ID for the requested instrument.

        Returns:
            dict: Market data regulatory snapshot for the specified instrument.

            Example return value:
            {
                "conid": 265598,
                "conidEx": "265598",
                "sizeMinTick": 1.0,
                "BboExchange": "9c",
                "HasDelayed": false,
                "84": "174.58",
                "86": "174.59",
                "88": 1,
                "85": 3,
                "BestBidExch": 512,
                "BestAskExch": 512,
                "31": "174.59",
                "7059": 2,
                "LastExch": 8,
                "7057": "Q",
                "7068": "Q",
                "7058": "D"
            }
        """
        params = {"conid": conid}
        return self._request("GET", "md/regsnapshot", params=params)

    def request_access_token(self, authorization: str = None) -> dict:
        """
        Request an access token for the IB username that has granted authorization to the consumer.

        Args:
            authorization (str, optional): OAuth 1.0a authorization request header for request to /access_token endpoint.

        Returns:
            dict: Success response containing the OAuth access token information.

            Example return value:
            {
                "is_true": true,
                "oauth_token": "a1b2c3d4e5f6a7b8c9d0",
                "oauth_token_secret": "coPZc+YOyFy7IdMg6is+etf9HASi3Um3SIhZvILcaifG6zhzZygYafYZx4XTFsrefRV/qrsy4sMAMwyPVp07VgkfQJPJkxYA7Sjhwz/Q76vuVN2YZNsRirNyL63Q3t+EHkjKA5HJEFY2PiIgqO4EWZ4etZUl3iZjCStiahhD+BNv7zgrlxS0bB4lL4vKw9AGcUiUnIQrqzTGJPj0/P2Zc3fMqCbXVWRcoYRcwUkk9ZYtMaIwPPVgvJ0c76rle5O5m4R4ZoFgrjfXpNiXC1F8MRS0fc7T6pgyyMvV+vI2C9XZbl7cNIEuCvtz3XYLNlUi+svyeZJh4RzjB824qH/fJQ=="
            }
        """
        headers = {"Authorization": authorization} if authorization else {}
        return self._request("POST", "oauth/access_token", headers=headers)

    def generate_live_session_token(self, authorization: str = None) -> dict:
        """
        Generate a Live Session Token shared secret and gain access to Web API.

        Args:
            authorization (str, optional): OAuth 1.0a authorization request header for request to /live_session_token endpoint.

        Returns:
            dict: Success response containing the Diffie-Hellman challenge and signature.

            Example return value:
            {
                "diffie_hellman_challenge": "74d222b7c3c0916eb3c7e60ecec937cd4f531aab5ea5698ebd754feeb39a9d7fe04c2887b5e11d8a8e4176c2eee7ddd42016e57c7a98cfbb9a3282c5247f7d4a9b8f544a34fac4d6334065b55d6a2e73e390175cfb94e80281443e555030c576d1db409bf96870dab20581bc01cdf28489778f20c714e7ad39af60c476cf2207a119df3af82bbefcdad7749fa5b4ae6e93169ec14f66ff3220cf3156487ca33932284b0a09af14f05a75269ab243362ff4eabb2e2a57db0d7911ca549f24affa1f92f04908fd9a2349cefb0f9326aca65fc144847ab837fcbd1635b1aa84b4509198e349fad87c2caf6744cb94be2c5c1c7ef9f08c44e85ded45ebeefa248dc8",
                "live_session_token_signature": "712549e22ba937ab10bc8d571bd3a9c20c43d7cb",
                "live_session_token_expiration": 1714669716258
            }
        """
        headers = {"Authorization": authorization} if authorization else {}
        return self._request("POST", "oauth/live_session_token", headers=headers)

    def request_temporary_token(self, authorization: str = None) -> dict:
        """
        Request a temporary token as a third party to begin the OAuth 1.0a authorization workflow.

        Args:
            authorization (str, optional): OAuth 1.0a authorization request header for request to /request_token endpoint.

        Returns:
            dict: Success response containing the temporary OAuth access token.

            Example return value:
            {
                "oauth_token": "e0d75b4c5c1d2c0f2af7"
            }
        """
        headers = {"Authorization": authorization} if authorization else {}
        return self._request("POST", "oauth/request_token", headers=headers)

    def request_oauth2_token(self, grant_type: str, client_id: str, client_secret: str, scope: str = None) -> dict:
        """
        Request an OAuth 2.0 access token.

        This endpoint returns OAuth 2.0 access tokens based on the request parameters.

        Args:
            grant_type (str): The grant type of the token request.
            client_id (str): The client identifier issued to the client.
            client_secret (str): The client secret.
            scope (str, optional): The scope of the access request.

        Returns:
            dict: Token response containing the access token and related information.

            Example return value:
            {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI...",
                "token_type": "Bearer",
                "scope": "echo.read echo.write",
                "expires_in": 86399
            }
        """
        payload = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return self._request("POST", "oauth2/api/v1/token", headers=headers, data=payload)

    def account_performance_all_periods(self, param0: str = None, acct_ids: list[str] = None) -> dict:
        """
        Retrieve account performance (MTM) for the given accounts over all time periods.

        Args:
            param0 (str, optional): If defined, only this account will be considered.
                                    Accounts passed in the request body will be ignored.
            acct_ids (list[str], required): An array of strings containing each account identifier
                                             to retrieve performance details for.

        Returns:
            dict: A dictionary containing account performance details.
                Example return value:
                {
                    "currencyType": "base",
                    "rc": 0,
                    "view": ["DU123456"],
                    "nd": 368,
                    "DU123456": {
                        "lastSuccessfulUpdate": "2024-04-26 16:46:42",
                        "start": "20230426",
                        "YTD": {
                            "nav": [1282878.735, ...],
                            "cps": [0, -0.0047, ...],
                            "freq": "D",
                            "dates": ["20240101", ...]
                        },
                        "1D": {
                            "nav": [1390987.0689],
                            "cps": [0.0072],
                            "freq": "D",
                            "dates": ["20240426"],
                            "startNAV": {"date": "20240425", "val": 1381022.2557}
                        }
                    }
                }
        """
        endpoint = "pa/allperiods"
        body = {"acctIds": acct_ids} if acct_ids else {}
        params = {"param0": param0} if param0 else {}
        return self._request("POST", endpoint, json=body, params=params)

    def get_account_performance(self, acct_ids: list, period: str = "12M") -> dict:
        """
        Retrieves the performance (MTM) for the specified accounts.

        Args:
            acct_ids (list): An array of strings containing each account identifier to retrieve performance details for.
            period (str): Specify the period for which the account should be analyzed. Available options:
                          - '1D' - The last 24 hours.
                          - '7D' - The last 7 full days.
                          - 'MTD' - Performance since the 1st of the month.
                          - '1M' - A full calendar month from the last full trade day.
                          - '3M' - 3 full calendar months from the last full trade day.
                          - '6M' - 6 full calendar months from the last full trade day.
                          - '12M' - 12 full calendar months from the last full trade day.
                          - 'YTD' - Performance since January 1st.
                          Default is '12M'.

        Returns:
            dict: A dictionary containing account performance data. The structure of the response is as follows:
                {
                    "currencyType": "base",
                    "rc": 0,
                    "nav": {
                        "data": [
                            {
                                "idType": "acctid",
                                "navs": [202767332.1223, 215718598.8239],
                                "start": "20230102",
                                "end": "20231213",
                                "id": "U1234567",
                                "startNAV": {
                                    "date": "20221230",
                                    "val": 202767761.3449
                                },
                                "baseCurrency": "USD"
                            }
                        ],
                        "freq": "D",
                        "dates": ["20230102", "20231213"]
                    },
                    "nd": 346,
                    "cps": {
                        "data": [
                            {
                                "idType": "acctid",
                                "start": "20230102",
                                "end": "20231213",
                                "returns": [0, 0.0639],
                                "id": "U1234567",
                                "baseCurrency": "USD"
                            }
                        ],
                        "freq": "D",
                        "dates": ["20230102", "20231213"]
                    },
                    "tpps": {
                        "data": [
                            {
                                "idType": "acctid",
                                "start": "20230102",
                                "end": "20231213",
                                "returns": [0.0037, 0.0031, 0.0033, 0.0034, 0.02, 0.0127, 0.0036, 0.0036, 0.0034, 0.0012, 0.0026, 0.0017],
                                "id": "U1234567",
                                "baseCurrency": "USD"
                            }
                        ],
                        "freq": "M",
                        "dates": ["202301", "202302", "202303", "202304", "202305", "202306", "202307", "202308", "202309", "202310", "202311", "202312"]
                    },
                    "id": "getPerformanceData",
                    "included": ["U1234567"],
                    "pm": "TWR"
                }
        """
        payload = {
            "acctIds": acct_ids,
            "period": period
        }
        return self._request("POST", "pa/performance", json=payload)

    def get_transaction_history(self, acct_ids: list, conid: str, currency: str = "USD", days: int = 90) -> dict:
        """
        Retrieves the transaction history for specified accounts and contract IDs.

        Args:
            acct_ids (list): Include each account ID as a string to receive data for.
            conid (str): Include contract ID to receive data for. Only supports one contract ID at a time.
            currency (str): Define the currency to display price amounts with. Default is 'USD'.
            days (int): Specify the number of days to receive transaction data for. Default is 90.

        Returns:
            dict: A dictionary containing transaction history data. The structure of the response is as follows:
                {
                    "rc": 0,
                    "nd": 4,
                    "rpnl": {
                        "data": [
                            {
                                "date": "20231211",
                                "cur": "USD",
                                "fxRate": 1,
                                "side": "L",
                                "acctid": "U1234567",
                                "amt": "12.2516",
                                "conid": "265598"
                            }
                        ],
                        "amt": "12.2516"
                    },
                    "currency": "USD",
                    "from": 1702270800000,
                    "id": "getTransactions",
                    "to": 1702530000000,
                    "includesRealTime": true,
                    "transactions": [
                        {
                            "date": "Mon Dec 11 00:00:00 EST 2023",
                            "cur": "USD",
                            "fxRate": 1,
                            "pr": 192.26,
                            "qty": -5,
                            "acctid": "U1234567",
                            "amt": 961.3,
                            "conid": 265598,
                            "type": "Sell",
                            "desc": "Apple Inc"
                        }
                    ]
                }
        """
        payload = {
            "acctIds": acct_ids,
            "conids": [conid],
            "currency": currency,
            "days": days
        }
        return self._request("POST", "pa/transactions", json=payload)

    def get_accounts(self) -> list:
        """
        Retrieves the user's account information.

        Returns:
            list: An array of account objects, each containing information about an account.
            The structure of the response is as follows:
            [
                {
                    "id": "DU123456",
                    "PrepaidCrypto-Z": false,
                    "PrepaidCrypto-P": false,
                    "brokerageAccess": true,
                    "accountId": "DU123456",
                    "accountVan": "DU123456",
                    "accountTitle": "John Smith, LLC",
                    "displayName": "John Smith, LLC",
                    "accountAlias": null,
                    "accountStatus": 1590724800000,
                    "currency": "USD",
                    "type": "DEMO",
                    "tradingType": "STKNOPT",
                    "businessType": "IB_SALES",
                    "ibEntity": "IBLLC-US",
                    "faclient": false,
                    "clearingStatus": "O",
                    "covestor": false,
                    "noClientTrading": false,
                    "trackVirtualFXPortfolio": true,
                    "acctCustType": "LLC",
                    "parent": {
                        "mmc": [],
                        "accountId": "",
                        "isMParent": false,
                        "isMChild": false,
                        "isMultiplex": false
                    },
                    "desc": "DU123456"
                }
            ]
        """
        return self._request("GET", "portfolio/accounts")

    def get_positions(self, conid: str) -> dict:
        """
        Get positions in accounts for a given instrument.

        Args:
            conid (str): Conid of the instrument for which positions are requested.

        Returns:
            dict: An object containing positions in the requested conid broken out by account.

            Example return value:
            {
                "DU123456": [
                    {
                        "acctId": "DU123456",
                        "conid": 8314,
                        "contractDesc": "IBM",
                        "position": 1412.0,
                        "mktPrice": 166.7599945,
                        "mktValue": 235465.11,
                        "currency": "USD",
                        "avgCost": 144.46141,
                        "avgPrice": 144.46141,
                        "realizedPnl": 0.0,
                        "unrealizedPnl": 31485.6,
                        "assetClass": "STK",
                        "multiplier": 0.0
                    }
                ]
            }

        Raises:
            HTTPError: If the request to the API fails.
        """
        return self._request("GET", f"portfolio/positions/{conid}")

    def get_subaccounts(self) -> list:
        """
        Retrieve attributes of the subaccounts in the account structure.

        Returns:
            list: An array of objects representing subaccounts in the structure.

        Example:
            [
                {
                    "id": "DU1234511",
                    "PrepaidCrypto-Z": false,
                    "PrepaidCrypto-P": false,
                    "brokerageAccess": false,
                    "accountId": "DU1234511",
                    "accountVan": "DU1234511",
                    "accountTitle": "John Smith, LLC",
                    "displayName": "John Smith, LLC",
                    "accountAlias": null,
                    "accountStatus": 1590724800000,
                    "currency": "USD",
                    "type": "DEMO",
                    "tradingType": "STKNOPT",
                    "businessType": "IB_SALES",
                    "ibEntity": "IBLLC-US",
                    "faclient": false,
                    "clearingStatus": "O",
                    "covestor": false,
                    "noClientTrading": false,
                    "trackVirtualFXPortfolio": true,
                    "acctCustType": "LLC",
                    "parent": {
                        "mmc": [],
                        "accountId": "",
                        "isMParent": false,
                        "isMChild": false,
                        "isMultiplex": false
                    },
                    "desc": "DU1234511"
                }
            ]
        """
        return self._request("GET", "portfolio/subaccounts")

    def get_account_allocation(self, model: str = None) -> dict:
        """
        Get an account's allocations by asset class, sector group, and sector.

        Parameters:
            model (str, optional): Optional model parameter.

        Returns:
            dict: Response containing account allocations.

        Example:
            {
                "assetClass": {
                    "long": {
                        "CRYPTO": 255.17,
                        "OPT": 44352.82,
                        "STK": 1564447.6240790943,
                        "BOND": 380106.54,
                        "CASH": 72425.68706744915
                    },
                    "short": {
                        "OPT": -80.53,
                        "STK": -103716.11109948158,
                        "CASH": -508096.16629793524
                    }
                },
                "sector": {
                    "long": {
                        "Others": 704313.8907064605,
                        "Industrial": 380106.54,
                        "Technology": 309264.47000000003,
                        "Consumer, Cyclical": 18213.43337263364,
                        "Communications": 164576.99,
                        "Financial": 412637.11,
                        "Consumer, Non-cyclical": 49.72
                    },
                    "short": {
                        "Technology": -87162.0,
                        "Consumer, Cyclical": -11763.0,
                        "Communications": -189.53,
                        "Financial": -4682.111099481583
                    }
                },
                "group": {
                    "long": {
                        "Computers": 279285.37,
                        "Others": 704313.8907064605,
                        "Biotechnology": 49.72,
                        "Aerospace/Defense": 380106.54,
                        "Semiconductors": 371.9,
                        "Auto Manufacturers": 18213.43337263364,
                        "Banks": 366666.31,
                        "Diversified Finan Serv": 45970.8,
                        "Software": 29607.2,
                        "Internet": 164576.99
                    },
                    "short": {
                        "Semiconductors": -87162.0,
                        "Auto Manufacturers": -11763.0,
                        "Insurance": -4682.111099481583,
                        "Internet": -189.53
                    }
                }
            }
        """
        endpoint = f"portfolio/{self.account_id}/allocation"
        params = {"model": model} if model else {}
        return self._request("GET", endpoint, params=params)

    def get_account_ledger(self) -> dict:
        """
        Get ledger data for the given account.

        Returns:
            dict: Response containing account ledger data.

        Example:
            {
                "CAD": {
                    "commoditymarketvalue": 0.0,
                    "futuremarketvalue": 0.0,
                    "settledcash": 3899.42,
                    "exchangerate": 0.73095405,
                    "sessionid": 1,
                    "cashbalance": 3899.42,
                    "corporatebondsmarketvalue": 0.0,
                    "warrantsmarketvalue": 0.0,
                    "netliquidationvalue": 3899.42,
                    "interest": 0,
                    "unrealizedpnl": 0.0,
                    "stockmarketvalue": 0.0,
                    "moneyfunds": 0.0,
                    "currency": "CAD",
                    "realizedpnl": 0.0,
                    "funds": 0.0,
                    "acctcode": "DU123456",
                    "issueroptionsmarketvalue": 0.0,
                    "key": "LedgerList",
                    "timestamp": 1712784785,
                    "severity": 0,
                    "stockoptionmarketvalue": 0.0,
                    "futuresonlypnl": 0.0,
                    "tbondsmarketvalue": 0.0,
                    "futureoptionmarketvalue": 0.0,
                    "cashbalancefxsegment": 0.0,
                    "secondkey": "CAD",
                    "tbillsmarketvalue": 0.0,
                    "dividends": 0.0,
                    "cryptocurrencyvalue": 0.0
                },
                "USD": {
                    ...
                },
                "BASE": {
                    ...
                }
            }
        """
        endpoint = f"portfolio/{self.account_id}/ledger"
        return self._request("GET", endpoint)

    def get_account_meta(self) -> dict:
        """
        Get a single account's attributes and capabilities.

        Returns:
            dict: Response containing the account's attributes.

        Example:
            {
                "id": "DU123456",
                "PrepaidCrypto-Z": false,
                "PrepaidCrypto-P": false,
                "brokerageAccess": false,
                "accountId": "DU123456",
                "accountVan": "DU123456",
                "accountTitle": "John Smith, LLC",
                "displayName": "John Smith, LLC",
                "accountAlias": "Retirement",
                "accountStatus": 1590724800000,
                "currency": "USD",
                "type": "DEMO",
                "tradingType": "STKNOPT",
                "businessType": "IB_SALES",
                "ibEntity": "IBLLC-US",
                "faclient": false,
                "clearingStatus": "O",
                "covestor": false,
                "noClientTrading": false,
                "trackVirtualFXPortfolio": true,
                "acctCustType": "LLC",
                "parent": {
                    "mmc": [],
                    "accountId": "",
                    "isMParent": false,
                    "isMChild": false,
                    "isMultiplex": false
                },
                "desc": "DU123456"
            }
        """
        endpoint = f"portfolio/{self.account_id}/meta"
        return self._request("GET", endpoint)

    def invalidate_positions(self) -> dict:
        """
        Instructs IB to discard cached portfolio positions for a given account.

        This method instructs IB to discard cached portfolio positions for the specified account,
        ensuring that the next request for positions returns freshly obtained data.

        Returns:
            dict: Response indicating the status of the invalidation.

        Example:
            {
                "message": "success"
            }
        """
        endpoint = f"portfolio/{self.account_id}/positions/invalidate"
        return self._request("POST", endpoint)

    def get_positions(self, page_id: str = "0", model: str = None,
                      sort: str = "name", direction: str = "a", wait_for_sec_def: bool = None) -> list:
        """
        Get all positions in an account.

        Retrieves all positions for the specified account. The response can be paginated and
        sorted according to the specified parameters.

        Parameters:
            page_id (str, optional): Paginates positions response. Default is "0".
            model (str, optional): Name of model.
            sort (str, optional): Field to sort the positions by. Default is "name".
            direction (str, optional): Sorting direction, "a" for ascending or "d" for descending. Default is "a".
            wait_for_sec_def (bool, optional): Whether to wait for all security definitions to be received.

        Returns:
            list: Array of objects reflecting all positions in the given account.

        Example:
            [
                {
                    "acctId": "DU123456",
                    "conid": 479624278,
                    "contractDesc": "BTC CRYPTO",
                    "position": 0.00365831,
                    "mktPrice": 69814.3984375,
                    "mktValue": 255.4,
                    "currency": "USD",
                    "avgCost": 27608.34921045,
                    "avgPrice": 27608.34921045,
                    "realizedPnl": 0.0,
                    "unrealizedPnl": 154.4,
                    "assetClass": "CRYPTO",
                    "ticker": "BTC"
                },
                ...
            ]
        """
        endpoint = f"portfolio/{self.account_id}/positions/{page_id}"
        params = {
            "model": model,
            "sort": sort,
            "direction": direction,
            "waitForSecDef": wait_for_sec_def
        }
        return self._request("GET", endpoint, params={k: v for k, v in params.items() if v is not None})

    def get_portfolio_summary(self) -> dict:
        """
        Retrieve the portfolio account summary for a specific account.

        Returns:
            dict: A dictionary containing the account summary. Example return value:
            {
                "accountcode": {
                    "amount": 0.0,
                    "currency": None,
                    "isNull": False,
                    "severity": 0,
                    "timestamp": 1712156105000,
                    "value": "DU123456"
                },
                "accountready": {
                    "amount": 0.0,
                    "currency": None,
                    "isNull": False,
                    "severity": 0,
                    "timestamp": 1712156105000,
                    "value": "true"
                },
                ...
            }
        """
        return self._request("GET", f"portfolio/{self.account_id}/summary")

    def get_position(self, conid: str) -> dict:
        """
        Get position for a given instrument in a single account.

        Args:
            conid (str): Conid of the instrument whose position in the account is requested.

        Returns:
            dict: Position details for the specified instrument in the account.

            Example return value:
            {
                "acctId": "DU123456",
                "conid": 580947749,
                "contractDesc": "META JUN2024 330 P [META 240621P00330000 100]",
                "position": -1.0,
                "mktPrice": 0.77968365,
                "mktValue": -77.97,
                "currency": "USD",
                "avgCost": 4229.1637,
                "avgPrice": 42.291637,
                "realizedPnl": 0.0,
                "unrealizedPnl": 4151.2,
                "exchs": None,
                "expiry": "20240621",
                "putOrCall": "P",
                "multiplier": 100.0,
                "strike": "330",
                "assetClass": "OPT",
                ...
            }

        Raises:
            ValueError: If conid is invalid.
            HTTPError: If the API request fails.
        """
        if not conid:
            raise ValueError("conid is required.")
        return self._request("GET", f"portfolio/{self.account_id}/position/{conid}")

    def validate_sso(self) -> dict:
        """
        Validate the current session for the SSO user.

        Returns:
            dict: Information detailing the SSO validation result.

            Example return value:
            {
                "USER_ID": 123456789,
                "USER_NAME": "user1234",
                "RESULT": true,
                "AUTH_TIME": 1702580846836,
                "SF_ENABLED": false,
                "IS_FREE_TRIAL": false,
                "CREDENTIAL": "user1234",
                "IP": "12.345.678.901",
                "EXPIRES": 415890,
                "QUALIFIED_FOR_MOBILE_AUTH": null,
                "LANDING_APP": "UNIVERSAL",
                "IS_MASTER": false,
                "lastAccessed": 1702581069652,
                "LOGIN_TYPE": 2,
                "PAPER_USER_NAME": "user1234",
                "features": {
                    "env": "PROD",
                    "wlms": true,
                    "realtime": true,
                    "bond": true,
                    "optionChains": true,
                    "calendar": true,
                    "newMf": true
                },
                "region": "NJ"
            }

        Raises:
            HTTPError: If the API request fails with a status code of 401 (Unauthorized) or other errors.
        """
        return self._request("GET", "sso/validate")

    def get_all_conids(self, exchange: str, asset_class: str = "STK") -> list:
        """
        Retrieve all contracts available on a specified exchange.

        This method sends a request to retrieve all tradable contracts on the given
        exchange, including those not using the exchange as their primary listing.

        Args:
            exchange (str): The exchange from which derivatives should be retrieved.
                Example: "AMEX"
            asset_class (str): The asset class to filter contracts.
                Default is "STK".

        Returns:
            list: A list of dictionaries containing contract information.

            Example return value:
            [
                {
                    "ticker": "BMO",
                    "conid": 5094,
                    "exchange": "NYSE"
                },
                {
                    "ticker": "BNS",
                    "conid": 15156975,
                    "exchange": "NYSE"
                }
            ]

        Raises:
            HTTPError: If the API request fails with a status code of 401 (Unauthorized),
            500 (Internal Server Error), or 503 (Service Unavailable).
        """
        params = {"exchange": exchange, "assetClass": asset_class}
        return self._request("GET", "trsrv/all-conids", params=params)

    def get_futures_by_symbol(self, symbols: str, exchange: str = None) -> dict:
        """
        Retrieve non-expired future contracts for the specified symbol(s).

        This method sends a request to get a list of non-expired future contracts
        associated with the provided symbols. It accepts a comma-delimited string of symbols.

        Args:
            symbols (str): A comma-delimited string of symbol(s) for which futures are to be retrieved.
                Example: "ES,MES"
            exchange (str, optional): The exchange for which to filter the futures.
                If not provided, futures from all exchanges will be included.

        Returns:
            dict: A dictionary containing the future contracts' security definitions.

            Example return value:
            {
                "ES": [
                    {
                        "symbol": "ES",
                        "conid": 495512557,
                        "underlyingConid": 11004968,
                        "expirationDate": 20241220,
                        "ltd": 20241219,
                        "shortFuturesCutOff": 20241219,
                        "longFuturesCutOff": 20241219
                    },
                    {
                        "symbol": "ES",
                        "conid": 495512563,
                        "underlyingConid": 11004968,
                        "expirationDate": 20251219,
                        "ltd": 20251218,
                        "shortFuturesCutOff": 20251218,
                        "longFuturesCutOff": 20251218
                    }
                ]
            }

        Raises:
            HTTPError: If the API request fails with a status code of 401 (Unauthorized),
            500 (Internal Server Error), or 503 (Service Unavailable).
        """
        params = {"symbols": symbols}
        if exchange:
            params["exchange"] = exchange
        return self._request("GET", "trsrv/futures", params=params)

    def get_security_definition(self, conids: str, criteria: str = None, bondp: str = None) -> dict:
        """
        Search the security definition by Contract ID.

        This method retrieves a list of security definitions for the given contract IDs (conids).
        The input is a comma-separated series of contract IDs.

        Args:
            conids (str): A comma-separated series of contract IDs to retrieve.
                Example: "265598,8314"
            criteria (str, optional): Optional criteria to filter the results.
            bondp (str, optional): Optional parameter for bond pricing.

        Returns:
            dict: A dictionary containing the security definitions.

            Example return value:
            {
                "secdef": [
                    {
                        "incrementRules": [{"lowerEdge": 0.0, "increment": 0.01}],
                        "displayRule": {
                            "magnification": 0,
                            "displayRuleStep": [{"decimalDigits": 2, "lowerEdge": 0.0, "wholeDigits": 4}]
                        },
                        "conid": 8314,
                        "currency": "USD",
                        "time": 770,
                        "chineseName": "&#x56FD;&#x9645;&#x5546;&#x4E1A;&#x673A;&#x5668;",
                        "allExchanges": "AMEX,NYSE,CBOE,...",
                        "listingExchange": "NYSE",
                        "countryCode": "US",
                        "name": "INTL BUSINESS MACHINES CORP",
                        "assetClass": "STK",
                        "expiry": None,
                        "lastTradingDay": None,
                        "group": "Computers",
                        "sector": "Technology",
                        "ticker": "IBM",
                        "fullName": "IBM",
                        "isUS": True,
                        "hasOptions": True
                    }
                ]
            }

        Raises:
            HTTPError: If the API request fails with a status code of 204 (No Content),
            400 (Bad Request), 401 (Unauthorized), 500 (Internal Server Error),
            or 503 (Service Unavailable).
        """
        params = {"conids": conids}
        if criteria:
            params["criteria"] = criteria
        if bondp:
            params["bondp"] = bondp
        return self._request("GET", "trsrv/secdef", params=params)

    def get_trading_schedule(
            self, assetClass: str, symbol: str, exchange: str = None, exchangeFilter: str = None) -> dict:
        """
        Retrieve the trading schedule by symbol.

        This method returns the trading schedule up to a month for the requested contract.

        Args:
            assetClass (str): Specify the security type of the given contract.
                Valid asset classes are:
                - STK - Stock
                - OPT - Option
                - FUT - Future
                - CFD - Contract for Difference
                - WAR - Warrant
                - SWP - Forex
                - FND - Mutual Fund
                - BND - Bond
                - ICS - Inter-Commodity Spread
            symbol (str): Specify the symbol for your contract. Example: "AAPL"
            exchange (str, optional): Specify the primary exchange of your contract. Example: "NASDAQ"
            exchangeFilter (str, optional): Specify all exchanges you want to retrieve data from. Example: "AMEX,NASDAQ,NYSE"

        Returns:
            dict: A dictionary containing the trading schedule.

            Example return value:
            {
                "schedules": [
                    {
                        "id": "p101781",
                        "tradeVenueId": "v13038",
                        "exchange": "NYSE",
                        "description": "New York Stock Exchange",
                        "timezone": "America/New_York",
                        "schedules": [
                            {
                                "clearingCycleEndTime": "0000",
                                "tradingScheduleDate": "20000101",
                                "sessions": [],
                                "tradingtimes": [
                                    {"openingTime": "0035", "closingTime": "2330", "cancelDayOrders": "Y"}
                                ]
                            },
                            ...
                        ]
                    }
                ]
            }

        Raises:
            HTTPError: If the API request fails with a status code of 400 (Bad Request),
            401 (Unauthorized), 500 (Internal Server Error), or 503 (Service Unavailable).
        """
        params = {
            "assetClass": assetClass,
            "symbol": symbol
        }
        if exchange:
            params["exchange"] = exchange
        if exchangeFilter:
            params["exchangeFilter"] = exchangeFilter
        return self._request("GET", "trsrv/secdef/schedule", params=params)

    def get_stocks_by_symbol(self, symbols: str, exchange: str = None, is_us: bool = None) -> dict:
        """
        Retrieve stock security definitions by symbol with optional filters.

        This method returns an object containing all stock contracts for the given symbol(s).
        Optional filters can be applied to narrow the results by exchange or by whether the
        contract is US-based. Only items with non-empty contracts are returned.

        Args:
            symbols (str): Comma-separated list of stock symbols. Example: "AAPL,IBKR"
            exchange (str, optional): Filter contracts by exchange (e.g., "NYSE", "LSE").
            is_us (bool, optional): Filter contracts based on whether they are US-based.

        Returns:
            dict: A dictionary containing the filtered stock contracts' security definitions,
                only including items whose contracts list is not empty.

            Example return value:
            {
                "IBM": [
                    {
                        "name": "INTL BUSINESS MACHINES CORP",
                        "chineseName": "&#x56FD;&#x9645;&#x5546;&#x4E1A;&#x673A;&#x5668;",
                        "assetClass": "STK",
                        "contracts": [
                            {"conid": 8314, "exchange": "NYSE", "isUS": true},
                            {"conid": 1411277, "exchange": "IBIS", "isUS": false},
                            {"conid": 38709473, "exchange": "MEXI", "isUS": false},
                            {"conid": 41645598, "exchange": "LSE", "isUS": false}
                        ]
                    },
                    {
                        "name": "INTL BUSINESS MACHINES C-CDR",
                        "chineseName": "&#x56FD;&#x9645;&#x5546;&#x4E1A;&#x673A;&#x5668;",
                        "assetClass": "STK",
                        "contracts": [
                            {"conid": 530091934, "exchange": "AEQLIT", "isUS": false}
                        ]
                    }
                ]
            }

        Raises:
            HTTPError: If the API request fails with a status code of 400, 401, 500, or 503.
        """
        params = {"symbols": symbols}
        response = self._request("GET", "trsrv/stocks", params=params)

        # Apply optional filters on exchange and isUS
        filtered_response = {}
        for symbol, details in response.items():
            filtered_stocks = []
            for stock in details:
                stock['contracts'] = [
                    contract for contract in stock['contracts']
                    if (exchange is None or contract['exchange'] == exchange) and
                    (is_us is None or contract['isUS'] == is_us)
                ]
                if stock['contracts']:
                    filtered_stocks.append(stock)

            filtered_response[symbol] = filtered_stocks

        return filtered_response

    def open_websocket(self, api: str, oauth_token: str) -> None:
        """
        Open a websocket connection.

        This method opens a websocket connection by switching protocols.

        Args:
            api (str): A 32-character Web API session cookie value.
                Example: "c8fh17fnjr01hfnrh39rhfh8shd1hd93"
            oauth_token (str): An 8-character OAuth access token.
                Example: "a1b2c3d4"

        Returns:
            None: This method does not return a value but will raise an exception
            if the websocket cannot be opened.

        Raises:
            HTTPError: If the API request fails or if the server response
            indicates an error while trying to switch protocols.
        """
        headers = {
            "Connection": "Upgrade",
            "Upgrade": "websocket"
        }
        cookies = {"api": api}
        params = {"oauth_token": oauth_token}

        # Make a request to open the websocket
        response = requests.get(f"{self.url}ws", headers=headers, cookies=cookies, params=params, verify=self.ssl)

        # Raise an error if the response status code is not 101 (Switching Protocols)
        response.raise_for_status()

    def translate_availability_code(self, code):
        """Translates the availability code into human-readable format."""
        availability_codes = [
            ("R", "RealTime",
             "Data is relayed back in real time without delay; market data subscriptions are required."),
            ("D", "Delayed", "Data is relayed back 15-20 minutes delayed."),
            ("Z", "Frozen", "Last recorded data at market close, relayed back in real time."),
            ("Y", "Frozen Delayed", "Last recorded data at market close, relayed back delayed."),
            ("N", "Not Subscribed",
             "User does not have the required market data subscription(s) to relay back either real-time or delayed data."),
            ("v", "VDR Exempt", "Vendor Display Rule 603c"),
            ("P", "Snapshot", "Snapshot request is available for the contract."),
            ("p", "Consolidated", "Market data is aggregated across multiple exchanges or venues."),
            ("B", "Book", "Top of the book data is available for the contract."),
            ("d", "Performance Details Enabled",
             "Additional performance details are available for this contract (internal use intended)."),]

        # Convert the availability codes list to a dictionary for quick lookup
        availability_dict = {x[0]: (x[1], x[2]) for x in availability_codes}

        # Handle codes of fewer than 3 characters
        translations = []
        for char in code or []:
            if char in availability_dict:
                translations.append(availability_dict[char][0])
            else:
                translations.append(f"Unknown ({char})")

        return translations

    def unavailable_data_rules(self):
        rules = [
            "1. Unavailable Historical Data Copy Location: Bars whose size is 30 seconds or less older than six months.",
            "2. Expired futures data older than two years counting from the future’s expiration date.",
            "3. Expired options, FOPs, warrants, and structured products.",
            "4. End of Day (EOD) data for options, FOPs, warrants, and structured products.",
            "5. Data for expired future spreads.", "6. Data for securities which are no longer trading.",
            "7. Native historical data for combos: Historical data is not stored in the IB database separately for combos; combo historical data in TWS or the API is the sum of data from the legs.",
            "8. Historical data for securities which move to a new exchange will often not be available prior to the time of the move.",
            "9. Studies and indicators such as Weighted Moving Averages or Bollinger Bands are not available from the API."]
        return rules

    def get_field_info(self, field_id):
        # Mapping of field IDs to their properties (return type, name, description)
        fields_data = {
            "31": ("str", "Last Price", "The last price at which the contract traded. May contain one of the following prefixes: C – Previous day’s closing price. H – Trading has halted."),
            "55": ("str", "Symbol", ""),
            "58": ("str", "Text", ""),
            "70": ("str", "High", "Current day high price"),
            "71": ("str", "Low", "Current day low price"),
            "73": ("str", "Market Value", "The current market value of your position in the security. Market Value is calculated with real-time market data (even when not subscribed to market data)."),
            "74": ("str", "Avg Price", "The average price of the position."),
            "75": ("str", "Unrealized PnL", "Unrealized profit or loss. Unrealized PnL is calculated with real-time market data (even when not subscribed to market data)."),
            "76": ("str", "Formatted position", ""),
            "77": ("str", "Formatted Unrealized PnL", ""),
            "78": ("str", "Daily PnL", "Your profit or loss of the day since prior close. Daily PnL is calculated with real-time market data (even when not subscribed to market data)."),
            "79": ("str", "Realized PnL", "Realized profit or loss. Realized PnL is calculated with real-time market data (even when not subscribed to market data)."),
            "80": ("str", "Unrealized PnL %", "Unrealized profit or loss expressed in percentage."),
            "82": ("str", "Change", "The difference between the last price and the close on the previous trading day"),
            "83": ("str", "Change %", "The difference between the last price and the close on the previous trading day in percentage."),
            "84": ("str", "Bid Price", "The highest-priced bid on the contract."),
            "85": ("str", "Ask Size", "The number of contracts or shares offered at the ask price. For US stocks, the number displayed is divided by 100."),
            "86": ("str", "Ask Price", "The lowest-priced offer on the contract."),
            "87": ("str", "Volume", "Volume for the day, formatted with ‘K’ for thousands or ‘M’ for millions. For higher precision volume refer to field 7762."),
            "88": ("str", "Bid Size", "The number of contracts or shares bid for at the bid price. For US stocks, the number displayed is divided by 100."),
            "6004": ("str", "Exchange", ""),
            "6008": ("int", "Conid", "Contract identifier from IBKR’s database."),
            "6070": ("str", "SecType", "The asset class of the instrument."),
            "6072": ("str", "Months", ""),
            "6073": ("str", "Regular Expiry", ""),
            "6119": ("str", "Marker for market data delivery method", "similar to request id"),
            "6457": ("int", "Underlying Conid", "Use /trsrv/secdef to get more information about the security"),
            "6508": ("str", "Service Params", ""),
            "6509": ("str", "Market Data Availability", "The field may contain three chars..."),
            "7051": ("str", "Company name", ""),
            "7057": ("str", "Ask Exch", "Displays the exchange(s) offering the SMART price."),
            "7058": ("str", "Last Exch", "Displays the exchange(s) offering the SMART price."),
            "7059": ("str", "Last Size", "The number of units traded at the last price."),
            "7068": ("str", "Bid Exch", "Displays the exchange(s) offering the SMART price."),
            "7084": ("str", "Implied Vol./Hist. Vol %", "The ratio of the implied volatility over the historical volatility, expressed as a percentage."),
            "7085": ("str", "Put/Call Interest", "Put option open interest/call option open interest for the trading day."),
            "7086": ("str", "Put/Call Volume", "Put option volume/call option volume for the trading day."),
            "7087": ("str", "Hist. Vol. %", "30-day real-time historical volatility."),
            "7088": ("str", "Hist. Vol. Close %", "Shows the historical volatility based on previous close price."),
            "7089": ("str", "Opt. Volume", "Option Volume"),
            "7094": ("str", "Conid + Exchange", ""),
            "7184": ("str", "canBeTraded", "If contract is a trade-able instrument. Returns 1(true) or 0(false)."),
            "7219": ("str", "Contract Description", ""),
            "7220": ("str", "Contract Description", ""),
            "7221": ("str", "Listing Exchange", ""),
            "7280": ("str", "Industry", "Displays the type of industry under which the underlying company can be categorized."),
            "7281": ("str", "Category", "Displays a more detailed level of description within the industry."),
            "7282": ("str", "Average Volume", "The average daily trading volume over 90 days."),
            "7283": ("str", "Option Implied Vol. %", "A prediction of how volatile an underlying will be in the future."),
            "7284": ("str", "Historical volatility %", "Deprecated, see field 7087"),
            "7285": ("str", "Put/Call Ratio", ""),
            "7286": ("str", "Dividend Amount", "Displays the amount of the next dividend."),
            "7287": ("str", "Dividend Yield %", "Total of expected dividend payments over the next twelve months per share."),
            "7288": ("str", "Ex-date of the dividend", ""),
            "7289": ("str", "Market Cap", ""),
            "7290": ("str", "P/E", ""),
            "7291": ("str", "EPS", ""),
            "7292": ("str", "Cost Basis", "Your current position in this security multiplied by the average price and multiplier."),
            "7293": ("str", "52 Week High", "The highest price for the past 52 weeks."),
            "7294": ("str", "52 Week Low", "The lowest price for the past 52 weeks."),
            "7295": ("str", "Open", "Today’s opening price."),
            "7296": ("str", "Close", "Today’s closing price."),
            "7308": ("str", "Delta", "The ratio of the change in the price of the option to the corresponding change in the price of the underlying."),
            "7309": ("str", "Gamma", "The rate of change for the delta with respect to the underlying asset’s price."),
            "7310": ("str", "Theta", "A measure of the rate of decline the value of an option due to the passage of time."),
            "7311": ("str", "Vega", "The amount that the price of an option changes compared to a 1% change in the volatility."),
            "7607": ("str", "Opt. Volume Change %", "Today’s option volume as a percentage of the average option volume."),
            "7633": ("str", "Implied Vol. %", "The implied volatility for the specific strike of the option in percentage."),
            "7635": ("str", "Mark", "The mark price is..."),
            "7636": ("str", "Shortable Shares", "Number of shares available for shorting."),
            "7637": ("str", "Fee Rate", "Interest rate charged on borrowed shares."),
            "7638": ("str", "Option Open Interest", ""),
            "7639": ("str", "% of Mark Value", "Displays the market value of the contract as a percentage of the total market value of the account."),
            "7644": ("str", "Shortable", "Describes the level of difficulty with which the security can be sold short."),
            "7655": ("str", "Morningstar Rating", "Displays Morningstar Rating provided value."),
            "7671": ("str", "Dividends", "Total of the expected dividend payments over the next twelve months per share."),
            "7672": ("str", "Dividends TTM", "Total of the expected dividend payments over the last twelve months per share."),
            "7674": ("str", "EMA(200)", "Exponential moving average (N=200)."),
            "7675": ("str", "EMA(100)", "Exponential moving average (N=100)."),
            "7676": ("str", "EMA(50)", "Exponential moving average (N=50)."),
            "7677": ("str", "EMA(20)", "Exponential moving average (N=20)."),
            "7678": ("str", "Price/EMA(200)", "Price to Exponential moving average (N=200) ratio -1, displayed in percents."),
            "7679": ("str", "Price/EMA(100)", "Price to Exponential moving average (N=100) ratio -1, displayed in percents."),
            "7680": ("str", "Price/EMA(50)", "Price to Exponential moving average (N=50) ratio -1, displayed in percents."),
            "7681": ("str", "Price/EMA(20)", "Price to Exponential moving average (N=20) ratio -1, displayed in percents."),
            "7682": ("str", "Change Since Open", "The difference between the last price and the open price."),
            "7683": ("str", "Upcoming Event", "Shows the next major company event. Requires Wall Street Horizon subscription."),
            "7684": ("str", "Upcoming Event Date", "The date of the next major company event. Requires Wall Street Horizon subscription."),
            "7685": ("str", "Upcoming Analyst Meeting", "The date and time of the next scheduled analyst meeting. Requires Wall Street Horizon subscription."),
            "7686": ("str", "Upcoming Earnings", "The date and time of the next scheduled earnings/earnings call event. Requires Wall Street Horizon subscription."),
            "7687": ("str", "Upcoming Misc Event", "The date and time of the next shareholder meeting, presentation or other event. Requires Wall Street Horizon subscription."),
            "7688": ("str", "Recent Analyst Meeting", "The date and time of the most recent analyst meeting. Requires Wall Street Horizon subscription."),
            "7689": ("str", "Recent Earnings", "The date and time of the most recent earnings/earning call event. Requires Wall Street Horizon subscription."),
            "7690": ("str", "Recent Misc Event", "The date and time of the most recent shareholder meeting, presentation or other event. Requires Wall Street Horizon subscription."),
            "7694": ("str", "Probability of Max Return", "Customer implied probability of maximum potential gain."),
            "7695": ("str", "Break Even", "Break even points"),
            "7696": ("str", "SPX Delta", "Beta Weighted Delta is calculated using the formula; Delta x dollar adjusted beta, where adjusted beta is adjusted by the ratio of the close price."),
            "7697": ("str", "Futures Open Interest", "Total number of outstanding futures contracts."),
            "7698": ("str", "Last Yield", "Implied yield of the bond if it is purchased at the current last price. Last yield is calculated using the Last price on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher."),
            "7699": ("str", "Bid Yield", "Implied yield of the bond if it is purchased at the current bid price. Bid yield is calculated using the Ask on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher."),
            "7700": ("str", "Probability of Max Return", "Customer implied probability of maximum potential gain."),
            "7702": ("str", "Probability of Max Loss", "Customer implied probability of maximum potential loss."),
            "7703": ("str", "Profit Probability", "Customer implied probability of any gain."),
            "7704": ("str", "Organization Type", ""),
            "7705": ("str", "Debt Class", ""),
            "7706": ("str", "Ratings", "Ratings issued for bond contract."),
            "7707": ("str", "Bond State Code", ""),
            "7708": ("str", "Bond Type", ""),
            "7714": ("str", "Last Trading Date", ""),
            "7715": ("str", "Issue Date", ""),
            "7718": ("str", "Beta", "Beta is against standard index."),
            "7720": ("str", "Ask Yield", "Implied yield of the bond if it is purchased at the current offer. Ask yield is calculated using the Bid on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher."),
            "7741": ("str", "Prior Close", "Yesterday’s closing price."),
            "7762": ("str", "Volume Long", "High precision volume for the day. For formatted volume refer to field 87."),
            "7768": ("str", "hasTradingPermissions", "If user has trading permissions for specified contract. Returns 1(true) or 0(false)."),
            "7920": ("str", "Daily PnL Raw", "Your profit or loss of the day since prior close. Daily PnL is calculated with real-time market data (even when not subscribed to market data)."),
            "7921": ("str", "Cost Basis Raw", "Your current position in this security multiplied by the average price and multiplier."),
        }

        # Fetching field info based on field_id
        return fields_data.get(field_id, "Field ID not found.")

    def field_mapping(self, data):
        # Define the mapping from numeric fields to names
        mapping = {
            "31": "last_price",
            "55": "symbol",
            "58": "text",
            "70": "high",
            "71": "low",
            "73": "market_value",
            "74": "avg_price",
            "75": "unrealized_pnl",
            "76": "formatted_position",
            "77": "formatted_unrealized_pnl",
            "78": "daily_pnl",
            "79": "realized_pnl",
            "80": "unrealized_pnl_percent",
            "82": "change",
            "83": "change_percent",
            "84": "bid_price",
            "85": "ask_size",
            "86": "ask_price",
            "87": "volume",
            "88": "bid_size",
            "6004": "exchange",
            "6008": "conid",
            "6070": "sectype",
            "6072": "months",
            "6073": "regular_expiry",
            "6119": "market_data_delivery_method",
            "6457": "underlying_conid",
            "6508": "service_params",
            "6509": "market_data_availability",
            "7051": "company_name",
            "7057": "ask_exchange",
            "7058": "last_exchange",
            "7059": "last_size",
            "7068": "bid_exchange",
            "7084": "implied_vol_hist_vol_percent",
            "7085": "put_call_interest",
            "7086": "put_call_volume",
            "7087": "hist_vol_percent",
            "7088": "hist_vol_close_percent",
            "7089": "opt_volume",
            "7094": "conid_exchange",
            "7184": "can_be_traded",
            "7219": "contract_description_1",
            "7220": "contract_description_2",
            "7221": "listing_exchange",
            "7280": "industry",
            "7281": "category",
            "7282": "average_volume",
            "7283": "option_implied_vol_percent",
            "7284": "historical_volatility_percent",
            "7285": "put_call_ratio",
            "7286": "dividend_amount",
            "7287": "dividend_yield_percent",
            "7288": "ex_date_of_dividend",
            "7289": "market_cap",
            "7290": "pe_ratio",
            "7291": "eps",
            "7292": "cost_basis",
            "7293": "52_week_high",
            "7294": "52_week_low",
            "7295": "open",
            "7296": "close",
            "7308": "delta",
            "7309": "gamma",
            "7310": "theta",
            "7311": "vega",
            "7607": "opt_volume_change_percent",
            "7633": "implied_vol_percent",
            "7635": "mark",
            "7636": "shortable_shares",
            "7637": "fee_rate",
            "7638": "option_open_interest",
            "7639": "percent_of_mark_value",
            "7644": "shortable",
            "7655": "morningstar_rating",
            "7671": "dividends",
            "7672": "dividends_ttm",
            "7674": "ema_200",
            "7675": "ema_100",
            "7676": "ema_50",
            "7677": "ema_20",
            "7678": "price_to_ema_200",
            "7679": "price_to_ema_100",
            "7681": "price_to_ema_50",
            "7682": "price_to_ema_20",
            "7683": "change_since_open",
            "7684": "upcoming_event",
            "7685": "upcoming_event_date",
            "7686": "upcoming_analyst_meeting",
            "7687": "upcoming_earnings",
            "7688": "recent_analyst_meeting",
            "7689": "recent_earnings",
            "7690": "recent_misc_event",
            "7694": "probability_of_max_return",
            "7695": "break_even",
            "7696": "spx_delta",
            "7697": "futures_open_interest",
            "7698": "last_yield",
            "7699": "bid_yield",
            "7700": "probability_of_max_return",
            "7702": "probability_of_max_loss",
            "7703": "profit_probability",
            "7704": "organization_type",
            "7705": "debt_class",
            "7706": "ratings",
            "7707": "bond_state_code",
            "7708": "bond_type",
            "7714": "last_trading_date",
            "7715": "issue_date",
            "7718": "beta",
            "7720": "ask_yield",
            "7741": "prior_close",
            "7762": "volume_long",
            "7768": "has_trading_permissions",
            "7920": "daily_pnl_raw",
            "7921": "cost_basis_raw"
        }

        # Create a new dictionary with the mapped names
        mapped_data = {}
        for key, value in data.items():
            if key in mapping:
                mapped_data[mapping[key]] = value
            else:
                mapped_data[key] = value

        return mapped_data

