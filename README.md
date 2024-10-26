# OrderTracker
Tracking order from gmail

Process: Get your unread email -> Get text -> Query gpt to retrieve order information -> Save in Atlas MongoDB

Configuration:

- Put your gmail credentials.json under packages/gmail/authorization.

- Put your Atlas MongoDB password in password.json under packages/mongodb/authorization.

- Put your Gpt api_key in api_key.json under packages/gpt/authorization.

- Put your proxy in proxy.json if you need it.ß
