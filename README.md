# Finto-suggestions (Ontology Suggestion Platform)

## Architecture

A Docker setup for development has been created with docker-compose. It consists of three containers: API (Python3.6/Flask), Frontend (Vue.js) and Nginx forward-proxy. Nginx proxies both Flask API (localhost:8080/api) and Vue.js frontend (localhost:8080/) to host machine's port 8080. API Uses a PostgreSQL database for data persistence.

```
                localhost:8080
                     +
                     |
+----------------------------------------+
|                    | :8080             |
|               +----v-----+             |
|               |          |             |
|               |  NGINX   |             |
|               |          |             |
|               +----------+             |
|                   |  |                 |
|             /api  |  |  /*             |
|                   |  |                 |
|         :8050     |  |    :8040        |
|      +----------+ |  | +----------+    |
|      |          | |  | |          |    |
| +---->   API    <-+  +->   WEB    |    |
| |    |          |      |          |    |
| |    +----------+      +----------+    |
| |     Flask API       Vue.js frontend  |
| |                                      |
| |       :5432                          |
| |    +----------+                      |
| |    |          |                      |
| +---->   PSQL   |                      |
|      |          |                      |
|      +----------+                      |
|                                        |
+----------------------------------------+

http://asciiflow.com/
```

```
.
├── api                     # Backend code (Python, Connexion, Flask etc.)
│   ├── api                 # API speicfic code, logic and Swagger API definitions
│   │   ├── logic
│   │   └── specification
│   ├── migrations          # Alembic migrations (with Flask-migrate plugin)
│   │   └── versions
│   └── tests               # Integration and unit tests
├── docker                  # Dockerfiles and configurations
│   ├── api
│   ├── nginx
│   └── web
└── web                     # Vue.js frontend
    ├── node_modules
    ├── public              # Static files
    ├── src                 # Frontend code (Javascript, Vue.js)
    │   ├── assets
    │   ├── components
    │   └── views
    └── tests               # Frontend tests
```

## Installation and Development

### Setting up Development Environment

1.  Copy the .env.default file and rename it to .env (from project root)
2.  Modify the environment variables in .env as desired
3.  Download and install [Docker CE](https://docs.docker.com/install/) to your computer. Docker-compose should be included with the installation.
4.  Download and install [Python 3.6+](https://www.python.org/downloads/) and after that install pipenv with command `pip install pipenv`. Pipenv is used to install/remove packages and run scripts api-side.
5. Download and install latest LTS Node.Js (https://nodejs.org/en/download/)
6.  Start the freshly installed Docker
7.  Run `docker-compose up` in project's **root** folder. This command builds the required containers (api, web and nginx) and starts them. Hitting `CTRL+C` should exit the output feed from docker. However the containers should still be running. You can check the container status with a command `docker ps`.
8.  Initialize the database. In api directory (while the containers are running), run `pipenv run upgrade-db`
9.  In web/.env.local set VUE_APP_GITHUB_CLIENT_ID if you wanna use github login/registeration, developer team will provide this for you.

When the application is running, you should find the application running on localhost:8080. The web frontend (Vue.js app) can be found on root url (localhost:8080/) and API on localhost:8080/api. Swagger ui can be found on localhost:8080/api/ui/#/.

You can start developing! Both api and web services should reload automatically.

Please see [a terminal recording](documentation/img/docker-compose-up.svg) of a successful setup.

### Halting Containers, Teardown

All the running (composed) containers can be halted with command `docker-compose down`.
You can remove previously built containers (and volumes) by executing `docker-compose rm -sv`.

### Local Production Installation

An example docker-compose file has been created for a simple and minimal production setup.

1. In production environment, copy the .env.default file and rename it to .env (from project root). Modify accordingly.
2. Manually (!) run `npm docker:build` in web directory to build the production-ready distribution (web/dist).
3. Run docker-compose with an extra production file, that overwrites a few serve commands: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`

Backend is served using [gunicorn](http://gunicorn.org/) and frontend using [http-server](https://www.npmjs.com/package/http-server). Ideally, you would want to serve the static files directly with Nginx.

### Staging Installation

Our Staging installation are automated and for now they are automatic installed when any commit goes to master branch

### Production Installation

Production installation will be automated something sameway as staging enviroment, will be updated this when that time comes.

### Development Workflow

Both API and Frontend can be developed simultaneously. All the changes to the code should update automatically without any restarts.

### Frontend

Frontend is initialized with vue-cli (3.0.3, https://github.com/vuejs/vue-cli).

Add new dependencies `npm install package-name` or `npm install package-name --save-dev`. In this case, you need to rebuild the containers by running `docker-compose build web`. You need to have node installed on your computer to do this. You could also just simply modify package.json.

Frontend can be run locally (without docker). You should have node installed. Run `npm install` in /web directory to install required dependencies. After that you can start the development server by running `npm run serve`.


### Backend (API)

Backend (API) is a simple Python webapp. Dependency management is handled by Pipenv.

Add new dependencies by running `pipenv install package-name` or `npm install package-name --dev` on your own computer (to update the Pipfile and Pipfile.lock). Afterwards, rebuild the api container `docker-compose build api` so that the changes are also installed within containers. You need to have Python3 and pipenv installed to do this locally.

#### Backend Commands

| **command**  | **description**                                                                                             | **example**                                           |
|--------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| start        | Starts the Docker containers (docker-compose up)                                                            | pipenv run start                                      |
| psql         | Opens a psql console within the db container                                                                | pipenv run psql                                       |
| shell        | Opens an interactive Python shell within the api container. Flask context is automatically available.       | pipenv run shell                                      |
| prune        | Prunes all blacklisted (/logout) access tokens. This should be run occasionally to keep the database clean. | pipenv run prune                                      |
| test         | Runs Python API tests.                                                                                      | pipenv run test                                       |
| create-admin | Creates a new admin user.                                                                                   | pipenv run create-admin admin admin@admin.fi password |
| start-db     | Starts the database container.                                                                              | pipenv run start-db                                   |
| migrate-db   | Creates a new Alembic migration file.                                                                       | pipenv run migrate-db                                 |
| upgrade-db   | Upgrades the database (to the next migration version).                                                      | pipenv run upgrade-db                                 |
| downgrade-db | Downgrades the database (to the previous migration version).                                                | pipenv run downgrade-db                               |

See [examples](documentation/examples.md) for additional tips and examples for development.

#### Database (migrations, accessing container etc.)

The database container runs a vendor Postgres Docker image on top of an Alpine container. Upon fresh installation, the database is initialized (currently) based on three environment variables set in .env file:

- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

SQLAlchemy is used as an ORM for creating the database tables and further Flask-migrate (based on Alembic) is used for migrations.

Whenever you make changes to the database layout, a new migration needs to be done (check [Flask-migrate docs](https://flask-migrate.readthedocs.io/en/latest/)). Run `pipenv run migrate-db` in project's **api** directory to create a new migration. Before upgrading the database, it is a good practise to verify the migration file in migrations/versions directory.

After creating a new migration file, upgrade the database by running `pipenv run upgrade-db`.

In case you'd rather downgrade to a previous migration, run `pipenv run downgrade-db` and remove the latest migration file from migrations/versions.

Recording of an example migration / upgrade [here](documentation/img/migrate-and-upgrade.svg).

**You can access a psql prompt** with a command `pipenv run psql` (See Pipfile -- unfortunately it doesn't use environmental variables for login credentials at this point).

See the animation on using psql [here](documentation/img/pipenv-psql.svg).

### Continous deployment and git strategy

Strategy how to use version control is that **master** -branch handles the latest staging and production version while development features and task are made in
**develop**-branch.

Feature task flow is that you made first your feature branch **feature/<some_task>** and when you are ready, made pull request that are targeted to **develop**-branch. After that when develop are tested in localy, features by pull request commits are transfered to master, which are automaticly builded to images that will be used in testin enviroment. When staging are tested out, that version is pushed to tag to handle correct version that is installed to production.

Our continous deployment flow works semiautomatic. It listens commits in **master**-branch, when ne commit is pushed it pulls new version and builds api and web images, pushes them to quay and after that you have to add them by hand in portainer -service to use newest images in staging or production. Some flow graph under:

git: master/push -> drone.io -> pull git -> build -> push to quay
portainer: pull newest image with tag:staging -> shutdown containers -> start newest container by newest image (but this has to made by user)

#### Bugs and quirks

Occasionally pytest doesn't get installed on the system when building the docker containers.

> OCI runtime exec failed: exec failed: container_linux.go:348: starting container process caused "exec: \"pytest\": executable file not found in $PATH": unknown

In that case, you need to install it manually in order to run tests: `docker-compose exec api pip install pytest`.
