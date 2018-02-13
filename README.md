##About

Schubser is a simple TLS Man-In-The-Middle, programmed for people who can code Python 2. The goal is to be very basic and only allow to intercept traffic and specify callbacks. What you do with the traffic (print, safe to file, search/replace, etc.) is up to you and you only need to program python functions for that. You don't need to remember any command line options and because of the very basic functionality, there is not much that can go wrong.

This project was developed by Tobias Ospelt (@floyd_ch) of modzero (@mod0).

##When to use Schubser

Use Schubser when Burp can not be used (eg. non-HTTP traffic). It should be used when you want something much simpler than mitmproxy, socat and all the other MITM proxies out there. Schubser is so simple that it is feasible to put all the code into one python file which can then serve as a minified Proof of Concept.

Schubser uses Python Twisted to listen on a port (or many ports) for a client (or multiple clients). It supports TCP and TLS. It then forwards the traffic to a server (TCP or TLS) you specify.

##Howto use Schubser

1. We need to create certificates for TLS first. Modify the first line of the script certs/create-ca-and-server-cert.sh to specify the server hostname Schubser should use in it's TLS server.
2. Execute "cd certs; ./create-ca-and-server-cert.sh" (it will create a CA certificate you can install in your client so the connection is trusted)
3. Install the Python dependencies if you haven't already ("pip install -r requirements.txt")
4. Execute "python schubser.py". By default Schubser is now listening on port 14000.
5. Open up your Browser and connect to [https://localhost:14000](https://localhost:14000) . You should see the www.example.org website. In the terminal window where you ran Schubser you will see traffic in both directions (client to server and server to client).
6. Modify schubser.py to your needs. There are already many examples of what you can do in the comments.

proxyfuzz.py was included because it can be helpful if you want to do very simple fuzzing of TCP traffic. proxyfuzz is "Copyright (C) 2011 Rodrigo Marcos" and under GNU General Public License version 3.
