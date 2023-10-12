## Initial state.
In the initial state, both Sanic and Vue expose HTTPS on both the loopback (127.0.0.1) 
and network (172.x.x.x) interfaces and manage their own HTTPS configuration.
Vue additionally requires WebSocket on TLS.

```mermaid
flowchart LR
    subgraph network
        direction LR
        network_tls_8400_port((  ))-- HTTPS ---network_https_8400(172:8400)
        network_tls_8401_port((  ))-- HTTPS ---network_https_8401(172:8401)
        network_tls_8401_port((  ))-- WSS ---network_wss_8401(172:8401)
    end
    subgraph localhost
        direction LR
        loop_https_8400_port((  ))-- HTTPS ---loop_https_8400(127:8400)
        loop_tls_8401_port((  ))-- HTTPS ---loop_https_8401(127:8401)
        loop_tls_8401_port(( ))-- WSS ---loop_wss_8401(127:8401)
    end
    network_https_8400---sanic[[ Sanic ]]
    loop_https_8400---sanic
    network_https_8401---vue[[ vue ]]
    loop_https_8401---vue
    loop_wss_8401---vue
    network_wss_8401---vue
```

This setup creates an issue when networks(eduroam) interfere with TLS traffic on ports other than 433

## Terminate https
One solution is to direct TLS traffic on 443 port to Nginx and encode further routes in URL.
Further, if internet traffic is proxied by Nginx then Sanic and Vue don't need TLS.

```mermaid
flowchart LR
    subgraph network
        direction LR
        network_tls((  ))-- HTTPS ---network_https_8400(https:/../port/8400)
        network_tls((  ))-- HTTPS ---network_https_8401(https:/../port/8401)
        network_tls(( 443 ))-- WSS ---network_wss_8401(wss:/../port/8401)
    end
    nginx[[nginx]]
    network_https_8400 --- nginx
    network_https_8401 --- nginx
    network_wss_8401 --- nginx

    subgraph localhost
        direction LR
        loop_8400_port(( 8400 ))-- HTTP ---loop_http_8400(http:/..:8400/port/8400)
        loop_8401_port(( 8401 ))-- HTTP ---loop_http_8401(http:/..:8401/port/8401)
        loop_8401_port(( 8401 ))-- WS ---loop_ws_8401(ws:/..:8401/port/8401)
    end
    loop_http_8400---sanic[[ Sanic ]]
    loop_http_8401---vue[[ vue ]]
    loop_ws_8401---vue
    nginx---loop_8400_port
    nginx---loop_8401_port
 
```

## Docker

```mermaid
flowchart LR
    subgraph network
        direction LR
        network_tls((  ))-- HTTPS ---network_https_8400(https:/../port/8400)
        network_tls((  ))-- HTTPS ---network_https_8401(https:/../port/8401)
        network_tls(( 443 ))-- WSS ---network_wss_8401(wss:/../port/8401)
    end

    subgrapsh docker
        direction TD
        nginx[[nginx]]
        network_https_8400 --- nginx
        network_https_8401 --- nginx
        network_wss_8401 --- nginx

        subgraph localhost
            direction LR
            loop_8400_port(( 8400 ))-- HTTP ---loop_http_8400(http:/..:8400/port/8400)
            loop_8401_port(( 8401 ))-- HTTP ---loop_http_8401(http:/..:8401/port/8401)
            loop_8401_port(( 8401 ))-- WS ---loop_ws_8401(ws:/..:8401/port/8401)
        end
    end

    loop_http_8400---sanic[[ Sanic ]]
    loop_http_8401---vue[[ vue ]]
    loop_ws_8401---vue
    nginx---loop_8400_port
    nginx---loop_8401_port
 
```

## Complication #1: Vue doesn't give up the network port.

Unfortunately, Vue doesn't give up the network port. So, after encountering some troubles,
I had to set up a less straightforward scheme where Nginx proxies the ports by adding 1 to the port number. 
So HTTPS:8400 is forwarded to HTTP:18400.

```mermaid
flowchart LR
    subgraph network
        direction LR
        https_172_8400(( )) -- HTTPS --- network_port_8400(172:8400)
        https_172_8401(( )) -- HTTPS --- network_port_8401(172:8401)
        https_172_18401(( )) -- HTTP --- network_port_18401(172:18401)
    end
    nginx[[nginx]]
    network_port_8400 --- nginx
    network_port_8401 --- nginx

    subgraph localhost
        direction LR
        http_127_8400(( )) -- http --- loop_port_18400(127:18400)
        http_127_8401(( ))-- http --- loop_port_18401(127:18401)
    end
    Sanic[[ Sanic ]]
    loop_port_18400---Sanic
    vue[[ vue ]]
    loop_port_18401---vue
    nginx---http_127_8400
    nginx---http_127_8401
    network_port_18401---vue
    linkStyle 0 stroke:red;
    linkStyle 1 stroke:red;
    linkStyle 2 stroke:blue;
    linkStyle 5 stroke:blue;
    linkStyle 6 stroke:blue;
```

Respective redirect config for nginx
```
proxy_pass http://127.0.0.1:1$server_port;
```
Might confuse people as this is an unusual redirect setup.

## Complication #2: Vue needs to proxy WebSockets too.
Vue relies on WebSockets for communication between the client (web browser) and the server in development mode. 
Therefore, WebSockets need to be proxied as well.

```mermaid
flowchart LR
    subgraph network
        direction LR
        https_172_8400(( )) -- HTTPS --- network_port_8400(172:8400)
        https_172_8401(( )) -- HTTPS --- network_port_8401(172:8401)
        wss_172_8401(( )) -- WSS --- network_port_8401(172:18401)
        http_172_8401(( )) -- HTTP --- network_port_18401(172:18401)
        ws_172_18401(( )) -- WS --- network_port_18401(172:18401)
    end
    nginx[[nginx]]
    network_port_8400 --- nginx
    network_port_8401 --- nginx

    subgraph localhost
        direction LR
        http_127_8400(( )) -- http --- loop_port_18400(127:18400)
        http_127_8401(( ))-- http --- loop_port_18401(127:18401)
        ws_127_8401(( ))-- WS --- loop_port_18401(127:18401)
    end
    Sanic[[ Sanic ]]
    loop_port_18400---Sanic
    vue[[ vue ]]
    loop_port_18401---vue
    nginx---http_127_8400
    nginx---http_127_8401
    nginx---ws_127_8401
    network_port_18401---vue
    linkStyle 0 stroke:red;
    linkStyle 1 stroke:red;
    linkStyle 2 stroke:red;
    linkStyle 3 stroke:blue;
    linkStyle 4 stroke:blue;
    linkStyle 7 stroke:blue;
    linkStyle 8 stroke:blue;
    linkStyle 9 stroke:blue;
```

This creates a further complication that when Vue is started in HTTP mode, 
it creates a dynamically unsecured WebSocket backlink. By default, the Vue client in the 
browser will try to communicate with the Vue server on `ws://host:18401`, which is not served. 
This can be explicitly configured in `vue.config.js`:

```javascript
devServer: {
    client: {
        webSocketURL: 'wss://cclaw.legalese.com:8408/ws'
    }
}
```
However, it needs to know the port on the proxy. This can still be done by templating `vue.config`
during the generation of the `vue-0xx` work directory, as the external port is known at the time of 
`vue-0xx` generation. But it further complicates the setup and adds some more "magic".

Basically, what was expected to be a simple proxy setup that simplifies the configuration turned 
out to be a rather complex setup relying on non-standard configurations and runtime template generation.