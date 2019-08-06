# Quick Start
The exact setup will differ slightly depending on your platform. This guide focuses on linux as the Data Atlas service are meant to be run in a server environment.

If you are familiar with Docker or you want to use Docker, the setup process will generally be easier. As all of the dependencies are already installed in the docker containers. The individual services can be run in the host operating system directly as well, however, should you prefer this option. In your deployment environment you will likely want to use docker, however, to aid with your automated deployment and continous delivery.

This guide describes how to use Data Atlas without Docker. Using Docker is highly recommended and guide to do so can be found [here](/quick-start.md)


## Starting MongoDB
Native setup on your particular operating system is best described by the [Official MongoDB Documentation](https://docs.mongodb.com/manual/administration/install-community/).


## Starting the API server
The API server uses Node.JS and you will need `npm` on your system. On most linux distributions, you can install it using your package manager, otherwise follow the [Official Installation Guide](https://www.npmjs.com/get-npm).

Once you have Node.JS with npm installed, install `pm2`:
```console
sudo npm install pm2 -g
```

Clone the *datlas-api* repository and install necessary packages:
```console
git clone https://github.com/DanielSaska/datlas-api.git
cd datlas-api
npm install
```

You will need to create a configuration file `config.json` which can be stored anywhere as follows:
```json
{
	"port": 8080,
	"mongo"  : "mongodb://127.0.0.1:27017/datlas"
}
```
!> Port 8080 may be taken by some other service. You can replace `-p 8080:8080` with `-p PORT:8080` where *PORT* is a free port on your operating system.

Now you can start the server using `pm2`:
```console
pm2 start app.js
```

Navigating to `http://localhost:8080/api/v1/healthz` in your web browser should now return `OK`. If you see `INIT`, the API server did not connect to the database (yet). In such case you may want to recheck whether your database is running and configured correctly.

## Starting the Web Interface
You should already have Node.JS installed and npm available on your system from the previous step. Install `angular-cli`:
```console
npm install -g @angular/cli
```

Clone the *datlas-www* repository and install necessary pacakages:
```console
git clone https://github.com/DanielSaska/datlas-www
cd datlas-www
npm install
```

Create configuration file `src/assets/config.json`:
```json
{
	"apiUrl": "http://localhost:8080/api",
	"dataUrl": ""
}
```
and launch the Angular server:
```console
ng serve
```
The server will give you url to access, usually `http://localhost:4200/`. If you access it from your web browser, you should see the Data Atlas Web Interface.

# Next {docsify-ignore}
Learn how to inegrate your data with Data Atlas [here](/python-library-start.md).
