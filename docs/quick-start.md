# Quick Start
The exact setup will differ slightly depending on your platform. This guide focuses on linux as the Data Atlas service are meant to be run in a server environment.

If you are familiar with Docker or you want to use Docker, the setup process will generally be easier. As all of the dependencies are already installed in the docker containers. The individual services can be run in the host operating system directly as well, however, should you prefer this option. In your deployment environment you will likely want to use docker, however, to aid with your automated deployment and continous delivery.
> On Linux-based system you can simply install docker using your package manager and then start it using `systemctl start docker.service` or otherwise.
> On Windows and Mac, follow [Docker for Windows](https://docs.docker.com/docker-for-windows/) and [Docker for Mac](https://docs.docker.com/docker-for-mac/) guides, respectively.

This guide describes how to use Data Atlas with Docker. If you with to run some (or all) Data Atlas services without docker (for example for local testing), follow guide to do so [here](/quick-start.md)
## Starting MongoDB
To start the database using docker, simply run  
```console
sudo docker run --name datlas-mongo -p 27017:27017 -d mongo
```  
from your command line.

!> The database created is not password protected, for more on how to set up, see [here](/database-advanced.md) and the [Official Documentation](https://hub.docker.com/_/mongo/)

!> This command exposes the database on port 27017 of your host machine which may already be taken if you are running MongoDB on your host machine already. It will also mean anyone on your local network can connect to it if the network allows it. See [here](/database-advanced.md) on how to avoid this.

!> It is suggested to mount the data directory inside the container to a host folder to allow persistance of data across container updates. See [here](/database-advanced.md).

Native setup on your particular operating system is best described by the [Official MongoDB Documentation](https://docs.mongodb.com/manual/administration/install-community/).

## Starting the API server
First you will need to create a configuration file `config.json` which can be stored anywhere as follows:
```json
{
	"port": 8080,
	"mongo"  : "mongodb://172.17.0.1:27017/datlas"
}
```
This assumes the MongoDB is exposed on 27017 on your host machine and 172.17.0.1 is the IP address of your host on the docker network which it should be by default. You can also use `docker.for.mac.localhost` and `docker.for.windows.localhost` hostnames on Mac and Windows, respectively.

Now you can launch the API container and mount the configuration file. From the folder where you stored your `config.json`, run:
```console
sudo docker run --name datlas-api -p 8080:8080 -v $PWD/config.json:/app/config.json -d danielsaska/datlas-api
```
!> Port 8080 may be taken by some other service which would cause the above command to fail. You can replace `-p 8080:8080` with `-p PORT:8080` where *PORT* is a free port on your host operating system.

Navigating to `http://localhost:8080/api/v1/healthz` in your web browser should now return `OK`. If you see `INIT`, the API server did not connect to the database (yet). In such case you may want to recheck whether your database is running and configured correctly.

## Starting the Web Interface
//TODO

# Next {docsify-ignore}
Learn how to inegrate your data with Data Atlas [here](/python-library-start.md).
