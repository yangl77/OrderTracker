# OrderTracker
Tracking order from gmail

Process: Get your unread email -> Get text -> Query gpt to retrieve order information -> Save in Atlas MongoDB

Configuration:

- Save your Gmail credentials.json under packages/gmail/authorization.

- Save your Atlas MongoDB password in password.json under packages/mongodb/authorization.

- Save your Gpt api_key in api_key.json under packages/gpt/authorization.

- Save your proxy in proxy.json if you need it.
