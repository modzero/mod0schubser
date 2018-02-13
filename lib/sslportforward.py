# Out of the twisted-box:
# TCP in - TCP out
# SSL in - TCP out
# Needs the classes in this file:
# TCP in - SSL out
# SSL in - SSL out (with SSL termination of course)

### START ###
# simple adjustments from
# https://github.com/twisted/twisted/blob/trunk/src/twisted/protocols/portforward.py
from twisted.internet import protocol
from twisted.python import log


class SSLProxy(protocol.Protocol):
    noisy = True
    peer = None

    def setPeer(self, peer):
        self.peer = peer

    def connectionLost(self, reason):
        if self.peer is not None:
            self.peer.transport.loseConnection()
            self.peer = None
        elif self.noisy:
            log.msg("Unable to connect to peer: %s" % (reason,))

    def dataReceived(self, data):
        self.peer.transport.write(data)


class SSLProxyClient(SSLProxy):
    def connectionMade(self):
        self.peer.setPeer(self)
        # We're connected, everybody can read to their hearts content.
        self.peer.transport.resumeProducing()


class SSLProxyClientFactory(protocol.ClientFactory):
    protocol = SSLProxyClient

    def setServer(self, server):
        self.server = server

    def buildProtocol(self, *args, **kw):
        prot = protocol.ClientFactory.buildProtocol(self, *args, **kw)
        prot.setPeer(self.server)
        return prot

    def clientConnectionFailed(self, connector, reason):
        self.server.transport.loseConnection()


class SSLProxyServer(SSLProxy):
    clientProtocolFactory = SSLProxyClientFactory

    def connectionMade(self):
        # Don't read anything from the connecting client until we have
        # somewhere to send it to.
        self.transport.pauseProducing()

        client = self.clientProtocolFactory()
        client.setServer(self)

        from twisted.internet import reactor
        reactor.connectSSL(self.factory.host, self.factory.port, client, self.factory.sslClientContextFactory)


class SSLProxyFactory(protocol.Factory):
    """Factory for port forwarder."""
    protocol = SSLProxyServer

    def __init__(self, host, port, sslClientContextFactory):
        self.host = host
        self.port = port
        self.sslClientContextFactory = sslClientContextFactory
