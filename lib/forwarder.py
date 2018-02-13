from twisted.internet import reactor
from twisted.internet import ssl
from twisted.protocols import portforward
from lib import sslportforward


# Seems like serverContextFactory=ssl.ContextFactory()
# doesn't work as an option parameter. Using
# ssl.DefaultOpenSSLContextFactory instead

def tcpToTcp(localport, remotehost, remoteport):
    print "TCP on localhost:%i forwarding to %s:%i" % (localport, remotehost, remoteport)
    return reactor.listenTCP(localport, portforward.ProxyFactory(remotehost, remoteport))


def sslToTcp(localport, remotehost, remoteport, serverContextFactory):
    print "SSL on localhost:%i forwarding to %s:%i" % (localport, remotehost, remoteport)
    return reactor.listenSSL(localport, portforward.ProxyFactory(remotehost, remoteport), serverContextFactory)


def tcpToSSL(localport, remotehost, remoteport, clientContextFactory=ssl.ClientContextFactory()):
    print "TCP on localhost:%i forwarding to SSL %s:%i" % (localport, remotehost, remoteport)
    return reactor.listenTCP(localport, sslportforward.SSLProxyFactory(remotehost, remoteport, clientContextFactory))


def sslToSSL(localport, remotehost, remoteport, serverContextFactory, clientContextFactory=ssl.ClientContextFactory()):
    print "SSL on localhost:%i forwarding to SSL %s:%i" % (localport, remotehost, remoteport)
    return reactor.listenSSL(localport, sslportforward.SSLProxyFactory(remotehost, remoteport, clientContextFactory),
                             serverContextFactory)


def setTcpServerReceiveCallback(callback):
    def server_dataReceived(self, data):
        data = callback(data)
        portforward.Proxy.dataReceived(self, data)

    portforward.ProxyServer.dataReceived = server_dataReceived


def setSSLServerReceiveCallback(callback):
    def server_ssl_dataReceived(self, data):
        data = callback(data)
        sslportforward.SSLProxy.dataReceived(self, data)

    sslportforward.SSLProxyServer.dataReceived = server_ssl_dataReceived


def setTcpClientReceiveCallback(callback):
    def client_dataReceived(self, data):
        data = callback(data)
        portforward.Proxy.dataReceived(self, data)

    portforward.ProxyClient.dataReceived = client_dataReceived


def setSSLClientReceiveCallback(callback):
    def client_ssl_dataReceived(self, data):
        data = callback(data)
        sslportforward.SSLProxy.dataReceived(self, data)

    sslportforward.SSLProxyClient.dataReceived = client_ssl_dataReceived


def setClientReceiveCallback(callback):
    setSSLClientReceiveCallback(callback)
    setTcpClientReceiveCallback(callback)


def setServerReceiveCallback(callback):
    setSSLServerReceiveCallback(callback)
    setTcpServerReceiveCallback(callback)
