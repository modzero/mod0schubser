from twisted.internet import reactor
from twisted.internet import ssl
from lib import forwarder
import re

# This file shows:
# - How to forward ports with your own SSL config
#  - E.g. to redirect SSL stuff through proxyfuzz (TCP-only fuzzer)
#  - Can be used in combination with burp
# - How to do simple modifications on TCP traffic (only outbound/only inbound/both)
#  - E.g. search replace
# A lot of examples are for HTTP, but it's exactly the point that it works with other TCP protocols just fine

# Remarks:
# 1. If you chain localhost ports to localhost, the order matters.
#    Of course you can not connect to ports that are not already opened.
# 2. You can listen on the lo interface with wireshark if you chain
#    localhost to localhost

#
# Simple examples first
# For most methods the arguments are something like (incoming_port, outgoing_server, outgoing_port)

# #TCP to TCP
# #Example 1, test with: nc localhost 11000
# forwarder.tcpToTcp(11000, "www.example.org", 80)
# 
# #Example 2: nc localhost 11010
# forwarder.tcpToTcp(11005, "www.example.org", 80)
# forwarder.tcpToTcp(11010, "localhost", 11005)
# 
# #Example 3: openssl s_client -connect localhost:11020
# forwarder.tcpToTcp(11015, "www.example.org", 443)
# forwarder.tcpToTcp(11020, "localhost", 11015)
# 
# 
# #SSL to TCP (SSL on listening port but no SSL outgoing)
# #Example 1: openssl s_client -connect 127.0.0.1:12000 with specified server cert
# keypath = "certs/serverkey.pem"
# certpath = "certs/servercert.pem"
# serverContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
# forwarder.sslToTcp(12000, "www.example.org", 80, serverContextFactory)
# 
# 
# #TCP to SSL (no SSL on listening port but on outgoing)
# #Example 1: nc localhost 13000, no client certificate
# forwarder.tcpToSSL(13000, "www.example.org", 443)
# 
# #Example 2: openssl s_client -connect 127.0.0.1:13005 with specified client cert
# keypath = "certs/serverkey.pem"
# certpath = "certs/servercert.pem"
# clientContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
# forwarder.tcpToSSL(13005, "www.example.org", 80, clientContextFactory)
# 
# 
# #SSL to SSL (with intercepting SSL) - the most common case
# #Example 1: openssl s_client -connect 127.0.0.1:14000, no client cert
keypath = "certs/serverkey.pem"
certpath = "certs/servercert.pem"
serverContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
forwarder.sslToSSL(14000, "www.example.org", 443, serverContextFactory)


# #Example 2: openssl s_client -connect 127.0.0.1:14005, same client cert as server cert
# keypath = "certs/serverkey.pem"
# certpath = "certs/servercert.pem"
# clientContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
# serverContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
# forwarder.sslToSSL(14005, "www.example.org", 443, serverContextFactory, clientContextFactory)


#
# On-the-fly modification examples
#

# TODO: forwarder only supports on-the-fly modifications that
# are applied to *all* TCP incoming. TODO: specific per port.
# Workaround for now: start several python instances
#
# Attention: if you want several callbacks, you have to chain them on your own!
# Meaning client_printer calls one function, then the other, etc.

# #Example 1: Print all responses sent to the client and to the server
def client_printer(data):
    print "Server -> Client:"
    print data  # or even better for binary data: print repr(data)
    return data


forwarder.setClientReceiveCallback(client_printer)


def server_printer(data):
    print "Client -> Server:"
    data = data.replace("Host: localhost:14000", "Host: www.example.org")
    print data  # or even better for binary data: print repr(data)
    return data


forwarder.setServerReceiveCallback(server_printer)

# 
# #Example 2: Print only responses sent to the client coming through a SSL channel
# forwarder.setSSLClientReceiveCallback(printer)
# 
# #Example 3: Print only responses sent to the client coming through a TCP channel
# forwarder.setTCPClientReceiveCallback(printer)
# 
# #Example 4: Change "200 OK" to "666 HAHA" for responses
# def haha(data):
#     data = data.replace("200 OK", "666 HAHA")
#     #or as regex:
#     data = re.sub(r'200\sOK', '666 HAHA', data, flags=re.IGNORECASE)
#     return data
# forwarder.setClientReceiveCallback(haha)
# 
# #Example 5: Change HTTP version for request
# def version_change(data):
#     data = data.replace("HTTP/1.0\n", "HTTP/1.1\nHost: www.example.org\n")
# forwarder.setServerReceiveCallback(version_change)
# 
# #Example 6: Random Fuzz with A's for incoming (to client) TCP traffic
# def randomFuzz(data):
#     import random
#     loc = random.randint(0,len(data))
#     data = data[:loc]+"A"*10000+data[loc:]
#     return data
# forwarder.setClientReceiveCallback(randomFuzz)
#
# #Example 7: A strange SSL client once sent 1 byte per connection, meaning we wanted to buffer here
# #We were able to intercept as long as we flushed when a \n or } was seen:
# class ClientIntercept:
#     def __init__(self):
#         self.buffered_data = ""
#     def client_printer(self, data):
#         self.buffered_data += data
#         if '\n' in self.buffered_data or '}' in self.buffered_data:
#             tmp = self.buffered_data
#             self.buffered_data = ""
#             print "Server:", repr(tmp)
#             return tmp
#         else:
#             return ""
# c = ClientIntercept()
# forwarder.setClientReceiveCallback(c.client_printer)
#
# class ServerIntercept:
#     def __init__(self):
#         self.buffered_data = ""
#     def server_printer(self, data):
#         self.buffered_data += data
#         if '\n' in self.buffered_data or '}' in self.buffered_data:
#             tmp = self.buffered_data
#             self.buffered_data = ""
#             print "Client:", repr(tmp)
#             return tmp
#         else:
#             return ""
# s = ServerIntercept()
# forwarder.setServerReceiveCallback(s.server_printer)


#
# More advanced examples
#

# #Example 1: Use proxyfuzz in a SSL to SSL channel, to fuzz what's inside SSL
# #Means: --SSL-->Forwarder--TCP-->Proxyfuzz--TCP-->Forwarder--SSL-->www.example.org
# listenport = 15000
# remotehost = "www.example.org"
# remoteport = 443
# forwarder.tcpToSSL(15010, remotehost, remoteport)
# #Problem here: we have to start one handler here, then proxyfuzz, then another handler here
# #because we can not connect to close ports. Although for some reason it works without here... 
# def startSecondHandler():
#     print "Please start proxyfuzz. If you want to fuzz the client side:"
#     print "python proxyfuzz.py -l 15005 -r localhost -p 15010 -c"
#     print "If you want to fuzz the server side (both sides: omit last argument):"
#     print "python proxyfuzz.py -l 15005 -r localhost -p 15010 -s "
#     raw_input("Press enter when proxyfuzz is running...")
#     keypath = "certs/serverkey.pem"
#     certpath = "certs/servercert.pem"
#     serverContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
#     forwarder.sslToTcp(listenport, "localhost", 15005, serverContextFactory)
#     #FIXME:
#     #Some strange bug in proxyfuzz. Only works after connecting once to 15005 first...
#     import socket
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.connect(("localhost", 15005))
#     sock.close()
#     #END FIXME
#     print "Use to check if it's working correctly:"
#     print "openssl s_client -connect localhost:%i" % listenport
#     print "Or:"
#     print "https://localhost:%i/" % listenport
# from thread import start_new_thread
# start_new_thread(startSecondHandler, ())


# #Example 2: Use proxyfuzz in a SSL to SSL channel, to fuzz test a webserver/webapplication
# #by testing with the local browser on this system
# #Needs root if you don't change listenport 443 to something else, but then you
# #run into troubles with absolute URLs, because the website might include links to
# #https://hostname/whatever which implies 443. So most likely you *need* to start on 443.
# listenport = 443
# #ATTENTION! Use the IP here. You're going to overwrite the name in /etc/hosts
# remotehost = "93.184.216.34" #www.example.org
# remoteport = 443
# #We use SSL incoming so that absolute https:// URLs work fine if we overwrite the hostname
# #in /etc/hosts, e.g. www.example.org 127.0.0.1 and use 443 as the incoming port as well
# #Means: --SSL-->Forwarder--TCP-->Proxyfuzz--TCP-->Forwarder--SSL-->www.example.org
# forwarder.tcpToSSL(15010, remotehost, remoteport)
# #Problem here: we have to start one handler here, then proxyfuzz, then another handler here
# #because we can not connect to close ports
# def startSecondHandler():
#     print "Please start proxyfuzz. If you want to fuzz the client side:"
#     print "python proxyfuzz.py -l 15005 -r localhost -p 15010 -c"
#     print "If you want to fuzz the server side (both sides: omit last argument):"
#     print "python proxyfuzz.py -l 15005 -r localhost -p 15010 -s "
#     raw_input("Press enter when proxyfuzz is running...")
#     keypath = "certs/serverkey.pem"
#     certpath = "certs/servercert.pem"
#     serverContextFactory = ssl.DefaultOpenSSLContextFactory(keypath, certpath)
#     forwarder.sslToTcp(listenport, "localhost", 15005, serverContextFactory)
#     #FIXME:
#     #Some strange bug in proxyfuzz. Only works after connecting once to 15005 first...
#     import socket
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.connect(("localhost", 15005))
#     sock.close()
#     #END FIXME
#     print "IMPORTANT: add to /etc/hosts --> %s 127.0.0.1" % remotehost
#     print "Use to check if it's working correctly:"
#     print "openssl s_client -connect %s:%i" % (remotehost, listenport)
#     print "https://%s:%i/" % (remotehost, listenport)
# from thread import start_new_thread
# start_new_thread(startSecondHandler, ())


# VERY IMPORTANT, you need this at the end:
reactor.run()
