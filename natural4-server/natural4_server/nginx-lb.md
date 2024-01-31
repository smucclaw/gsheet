
# Add second serving L4 host

Currently L4 is served from the single host. While this is simple and easy to maintain, it is not robust.
If the host goes down, the whole service goes down. As service quite frequently gets stuck and requires reload
it would be better to have a second host serving the same service. So at least one host is always up.

Current deployment is as follows:

```mermaid
flowchart TB
    subgraph VPC
        subgraph prod
            nginx-->docker
            subgraph docker
                direction LR
                nginx2-->sanic
                sanic-->id1[(files)]
            end
        end
    end
```

One issue is files are stored inside the docker container. So when host is reloading other host won't be able to serve
these files. To solve this issue, we need to store files outside of the docker container and host.
This can be done by storing them in EFS or S3 bucket. 

```mermaid
flowchart LR
    subgraph VPC
        direction LR
        subgraph host1
            nginx
        end

        subgraph host2
            subgraph docker1
                nginx2-->sanic1
            end
        end
        
        subgraph host3
            subgraph docker2
                nginx3-->sanic2
            end
        end
        
        nginx-->nginx3
        nginx-->nginx2
    end
    efs[(EFS)]
    sanic1-->efs
    sanic2-->efs
```