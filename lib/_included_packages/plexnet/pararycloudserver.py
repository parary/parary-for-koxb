from __future__ import absolute_import
from . import util
from . import plexserver
from . import plexconnection

from . import http
from . import callback

class PararyCloudServer(object):
 
    def __init__(self):
        util.DEBUG_LOG( "Parary Cloud Server Created !!" )

    def discover(self):
        
        util.DEBUG_LOG( "\t\tParary Cloud Server First START !!" )

        request = http.HttpRequest("https://parary.kro.kr/plex.php?tokens=all&type=json")
        context = request.createRequestContext("parary_connections", callback.Callable(self.onPararyConnectionsResponse))
        context.serverAddress = "https://parary.kro.kr"
        context.address = "parary.kro.kr"
        context.proto = "https"
        context.port = 443
        util.APP.startRequest(request, context)

    def onPararyConnectionsResponse(self, request, response, context):
                
        if not response.isSuccess():
            return
        
        import json
        data = json.loads( response.getBodyString() )
        
        # del data["parary"]
        # del data["media"]
        # del data["Lizstudio_Synology"]
        
        
        for key in data.keys():
            self.createServer( key, data[key] )
        
    def createServer(self, name, token):
        util.DEBUG_LOG( f"\t\tParary Cloud Server INFO : {token}" )

        request = http.HttpRequest( f"https://plex.tv/pms/resources?X-Plex-Token={token}")
        # request.session.verify = False
        context = request.createRequestContext("parary_connections", callback.Callable(self.createServerResponse))
        context.serverAddress = "https://plex.tv"
        context.address = "plex.tv"
        context.proto = "https"
        context.port = 443
        context.serverKey = name
        context.accessToken = token
        util.APP.startRequest(request, context)
        
    def createServerResponse(self, request, response, context):
        
        data = response.getBodyXml()
        pararyServers = []
        
        for device in data.findall("Device"):
            
            at = device.attrib.get('accessToken')
            
            if at:
                util.DEBUG_LOG( f"\t\tParary Device Info : {device.attrib.get('name')} - {at} " )
                machineID = device.attrib.get('clientIdentifier')
                name = device.attrib.get('name')
                
                server = plexserver.createPlexServer()
                server.accessToken = at
                server.uuid = machineID
                server.name = name
                server.sameNetwork = False
                                
                for conn in device.findall("Connection"):                                                
                    if conn.attrib.get('local') == '0':             
                        connection = plexconnection.PlexConnection(
                            source=plexconnection.PlexConnection.SOURCE_MANUAL_AND_MYPLEX
                            , address=conn.attrib.get('uri')
                            , isLocal=conn.attrib.get('local') == '1'
                            , token=at
                            , isFallback=conn.attrib.get('protocol') == 'https'
                            )
                        
                        util.DEBUG_LOG( f"\t\tParary Add Connection {name}: {connection}" )
                        
                        connection.refreshed = False
                        if connection.isSecure:
                            server.connections.insert( 0, connection )
                        else:
                            server.connections.append(connection)
                
                if(server.connections):
                    util.DEBUG_LOG("\t\t Parary Server Update : {0}   --- {1}".format(server.getToken(), server) )
                    from . import plexapp
                    plexapp.SERVERMANAGER.updateFromDiscovery(server)
                    # for conn in server.connections:
                    #     conn.refreshed = True
                    # pararyServers.append(server)

        # if pararyServers:
        #     util.DEBUG_LOG("\t\tFinished Parary Cloud Server discovery, found {0} server(s)".format(len(pararyServers)))
        #     from . import plexapp
        #     plexapp.SERVERMANAGER.updateFromConnectionType(pararyServers, plexconnection.PlexConnection.SOURCE_MYPLEX)
        #     plexapp.SERVERMANAGER.updateFromDiscovery(pararyServers)
        #     pararyServers.clear()

CLOUD_SERVER = PararyCloudServer()
