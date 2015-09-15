west: Any proxy with WebSocket tunnel
=====================================

## What is it ?

*west* is a reverse proxy written by Python.
*west* accepts a request from a client,
and transports the request to the other specified *west*.
The specified *west* received the request acts as a proxy as well,
and returns the response from the server to the source *west*.
The source *west* returns the response to the client.
*west* currently only support HTTP proxy.

The point is that *west* utilizes WebSocket tunnel to transport the requests
between *west*s.
That is it allows a HTTP client to access to a HTTP server behind NAT.

## Requirements

- Python 2.7
- [wesocket-server][https://pypi.python.org/pypi/websocket-server/0.4]
- [websocket-client][https://pypi.python.org/pypi/websocket-client]
- [chunkable_http_server.py][https://github.com/tanupoo/chunkable_http_server.py]

both websocket-server and websocket-client can be installed by pip.
chunkable_http_server.py must be placed into the same directory you deployed the source codes of *west*..

## Usage

you have to write a configuration file before you launch it.
you can find examples in the sample directory.
the file name corresponds to the use case number below this document.

typically *west* can be stared like below.

    ~~~~
    % west.py -c config.json
    ~~~~

the usage is here.

    ~~~~
    usage: west.py [-h] [-c CONFIG] [-O OUTFILE] [-v] [-d] [--input INFILE]
                   [--output OUTFILE] [--verbose] [--debug _DEBUG_LEVEL]
                   [--version]
    
    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG             specify the configuration file.
      -O OUTFILE            specify a output file, default is stdout.
      -v                    enable verbose mode.
      -d                    increase debug mode.
      --input INFILE        specify an input file, default is stdin.
      --output OUTFILE      specify an output file, default is stdout.
      --verbose             enable verbose mode.
      --debug _DEBUG_LEVEL  specify a debug level.
      --version             show program's version number and exit
    ~~~~

## To get the state

You can get the server state at any time.
for example, if the control port is 127.0.0.1:9701, just type below command.

    ~~~~
    % wget -q -O - -t 1 http://127.0.0.1:9701
    --- west object ---
    {
        "addr":"",
        "cp":":9701",
        "nm":"ws://case3.G.fiap.org",
        "port":9701
    }
    --- wsts object ---
    {
        "addr":"127.0.0.1",
        "port":9801,
        "sp":"ws://127.0.0.1:9801"
    }
    --- wstc object ---
    {
        "ws://case3.L2.fiap.org":{
            "ee":"no",
            "nm":"ws://case3.G.fiap.org"
        }
    }
    --- proxy object ---
    {
        "http://127.0.0.1:9961":{
            "/by":{
                "ou":"http://127.0.0.1:9971/b"
            },
            "addr":"127.0.0.1",
            "en":"ws://case3.L2.fiap.org",
            "port":9961
        }
    }
    ~~~~

## TODO

- error code.
- access control for the connection from the other *west*.
- access control from an HTTP client.
- SSL in WebSocket.
- IEEE1888 support between IEEE1888 component and *west*.
- chunk support of http_proxy_client.py
- gzip support of http_proxy_client.py

## architecture

see doc/any-proxy-websocket.pptx

## trouble shooting

- if you seee "Address already in use" when you launch this application.

    ~~~~
    ERROR: [Errno 48] Address already in use
    ~~~~

    ~~~~
    % sysctl -a | grep v6only
    net.inet6.ip6.v6only: 0
    % sudo sysctl -w net.inet6.ip6.v6only=1
    net.inet6.ip6.v6only: 0 -> 1
    ~~~~

## configuration syntax

    one west server will be connected from multiple west clients.
    one west client will have multiple proxy processes.
    one proxy process will bind to one west server having an end point of address through one west client.
    or one proxy process will bind to one west client having an end point of name through one west server..

    ~~~~
    west object:

        configuration about the west.  (required)

        "west" : {
            "nm" : "...",
            "cp" : "...",
        }

        nm: string of the WebSocket origin.  (required)
            The name of the west server is required.
            it will be used for the default origin name.
            If you want to specify a origin for a WebSocket client,
            you can specify in the west client object.
        cp: the west control port. (option)
            e.g. '203.178.141.195:9801' or ':9801'

    west server object:

        configuration about the WebSocket tunnel server.

        "wsts" : {
            "sp" : "...",
            "ca" : [ ]
        }

        sp: URL string of the WebSocket server.  (conditional required)
            If you make this program be a WebSocket tunnel server,
            you have to specify this attribute.
        ca: access list of the WebSocket clients connecting to this server.
            (option)
            TBD

    west client object:

        configuration about the WebSocket tunnel client.

        "wstc" : {
            <a WebSocket tunnel server's configuration> [, ...]
        }
        
        <a WebSocket tunnel server's configuration> :=
            "<URL of a WebSocket tunnel server>" : {
                "nm" : "...",
                "ee" : "<yes or no>"
            }

        nm: the origin name that the client sends to the server.  (option)
            it overrides the name defined in the west object.
        ee: enables or disables early establishment. (option)
            if this object is not defined, the program establish a WebSocket
            tunnel with the server before a client initiates a session.

    proxy object:

        configuration about the proxy.

        client's configuration and server's one are different.
        the client needs to use the ea attribute.
        the server needs to use the en attribute.
        either en or ea not both must be defined.
        it is allowed that the multiple proxy configurations use same end point.

        "proxy" : {
            <a proxy configuration> [, ...]
        }

        < a proxy configuration> :=
            <a proxy configuration for a ws tunnel server> or
            <a proxy configuration for a ws tunnel client>

        <a configuration for a ws tunnel server> :=
            "<proxy URL address>" : {
                "en" : "...",
                "<proxy incoming URL path>" : {
                    "ou" : "...",
                    "ca" : [ ] } ... }

        <a configuration for a ws tunnel client> :=
            "<proxy URL address>" : {
                "ea" : "...",
                "<proxy incoming URL path>" : {
                    "ou" : "...",
                    "ca" : [ ] } ... }

        <Proxy URL address>: host name and port number to be listened.
        en: WebSocket name of the end point.  (conditional required)
            a WebSocket end's name is required for a WebSocket tunnel server
            to forward messages to the client.
        ea: WebSocket address of the end point.  (conditional required)
            a WebSocket end's address is required for a WebSocket tunnel
            client, if it is defined and ee is not defined for this address
            in the west client object, a WebSocket client establishes the tunnel
            before a client initiates a session.
        <proxy incoming URL path>: a path part of the incoming URL.  (required)
            it must be leaded by '/'.
        ou: outgoing proxy URL. (required)
        ca: access list for clients connecting to the incoming URL.  (option)
    ~~~~

## use cases

client in the picture means an HTTP client.
server is an HTTP server.
G is a global proxy.
L is a Local proxy.

### case 1

the client at the bottom accesses to the server at the top.

    ~~~~
                           server
                              |      http://127.0.0.1:9921/x
                              |                 ^
                  ............|..........       |
                  .     proxy_client            |
                  .           |
                  G           |
                  .           |
    ws://127.0.0.1:9801  west_server
                  ............|..........
                              |
                  ............|..........
                  .      west_client
                  .           |                 ^
                  L           |                 |
                  .           |      http://127.0.0.1:9921/x
                  .     proxy_server
                  ............|..........
                              |      http://127.0.0.1:9911/px
                              |                 ^
                              |                 |
                           client
    ~~~~

if you don't want to establish the websocket tunnel before
client initiates a session, define "ee" : "no" in the west client object.
default is "yes".

    ~~~~
        "wstc" : {
            "ws://127.0.0.1:9801" : { "ee" : "no" }
        }
    ~~~~

if you want to use a specific name of the websocket client,
you can define it in the west client object like below.
default is referred to "nm" in the west server object.

    ~~~~
        "wstc" : {
            "ws://127.0.0.1:9801" : { "nm" : "ws://special.name.fiap.org" }
        }
    ~~~~

### case 2

the client at the top accesses to the server at the bottom.

    ~~~~
                           client
                              |                 |
                              |                 v
                              |      http://127.0.0.1:9931/pa
                  ............|............
                  .     proxy_server       
                  .           |      http://127.0.0.1:9941/a
                  G           |                 |
                  .           |                 v
    ws://127.0.0.1:9801  west_server
                  ............|............
                              |
                  ............|............
                  .      west_client
                  .           |
                  L           |
                  .           |
                  .     proxy_client
                  ............|............     |
                              |                 |
                              |                 v
                              |      http://127.0.0.1:9941/a
                           server
    ~~~~

### case 3

the client at the bottom in L accesses to the server at the bottom in L2
through the west server at the top.

    ~~~~
                          
      .....                      ___________________
      .                         |                   |
      .                         |                   v
      .           |             |       http://127.0.0.1:9961/by  |
      .     proxy_client                                    proxy_server
      .           |                     http://127.0.0.1:9971/b   |
      G           |                                 |             |
      .           |                                 v             |
      .                            west_server               west_server
      .                        ws://127.0.0.1:9801                |
      ............................................................|.....
                  |                                               |
                  |                                               |
      ............|..........             ........................|.....
      .   ws://127.0.0.1:9802             .             ws://127.0.0.1:9803
      .      west_client                  .                  west_client
      .           |                       .                       |
      L           |                       L2                      |
      .           |             ^         .                       |
      .           |             |         .                       |
      .           |  http://127.0.0.1:9961/by                     |
      .     proxy_server                  .                 proxy_client
      ............|..........             ..........|..........   |
                  |  http://127.0.0.1:9951/bx       |             |
                  |             ^                   v             |
                  |             |       http://127.0.0.1:9971/b   |
               client                                           server
    ~~~~


