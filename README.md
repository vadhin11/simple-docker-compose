## Compose sample application
### Python/FastAPI with Nginx proxy and MySQL database

Project structure:
```
.
├── compose.yaml
├── backend
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app
│       ├── db.ap
│       └── main.py
├── frontend
│   ├── Dockerfile
│   └── static
│       ├── index.html
│       ├── script.js
│       └── styles.css
└── db
│   └── password.txt
└── proxy
    └── nginx.conf

```

[_compose.yaml_](compose.yaml)
```
services:
  db:
    # We use a mariadb image which supports both amd64 & arm64 architecture
    image: mariadb:10-focal
    # If you really want to use MySQL, uncomment the following line
    #image: mysql:8
    command: '--default-authentication-plugin=mysql_native_password'
    restart: always
    healthcheck:
      test: ['CMD-SHELL', 'mysqladmin ping -h 127.0.0.1 --password="$$(cat /run/secrets/db-password)" --silent']
      interval: 3s
      retries: 5
      start_period: 30s
    secrets:
      - db-password
    volumes:
      - db-data:/var/lib/mysql
    networks:
      - backnet
    environment:
      - MYSQL_DATABASE=example
      - MYSQL_ROOT_PASSWORD_FILE=/run/secrets/db-password
    expose:
      - 3306
      - 33060

  backend:
    build:
      context: backend
      target: builder
    restart: always
    secrets:
      - db-password
    ports:
      - 8000:8000
    networks:
      - backnet
      - frontnet
    depends_on:
      db:
        condition: service_healthy
  frontend:
    build:
      context: frontend
    restart: always
    ports:
      - 8080:80
    networks:
      - frontnet
    depends_on:
      - proxy   # optional: ensures backend is up first
  proxy:
    build: proxy
    restart: always
    ports:
      - 80:80
    depends_on: 
      - backend
    networks:
      - frontnet

volumes:
  db-data:

secrets:
  db-password:
    file: db/password.txt

networks:
  backnet:
  frontnet:

```
The compose file defines an application with three services `proxy`, `frontend`, `backend` and `db`.
When deploying the application, docker compose maps port 80 of the proxy service container to port 80 of the host as specified in the file.
Make sure port 80 on the host is not already being in use.

> ℹ️ **_INFO_**  
> For compatibility purpose between `AMD64` and `ARM64` architecture, we use a MariaDB as database instead of MySQL.  
> You still can use the MySQL image by uncommenting the following line in the Compose file   
> `#image: mysql:8`

## Deploy with docker compose

```
$ docker compose up --build
[+] Running 12/12
 ✔ db Pulled   
...
...
[+] Running 9/9
 ✔ nginx-fast-mysql-v2-backend               Built
 ✔ nginx-fast-mysql-v2-proxy                 Built
 ✔ nginx-fast-mysql-v2-frontend              Built
 ✔ Network nginx-fast-mysql-v2_backnet       Created
 ✔ Network nginx-fast-mysql-v2_frontnet      Created 
 ✔ Container nginx-fast-mysql-v2-db-1        Created
 ✔ Container nginx-fast-mysql-v2-backend-1   Created
 ✔ Container nginx-fast-mysql-v2-proxy-1     Created
 ✔ Container nginx-fast-mysql-v2-frontend-1  Created
Attaching to backend-1, db-1, frontend-1, proxy-1
db-1  | 2025-10-27 17:14:30+00:00 [Note] [Entrypoint]: Entrypoint script for MariaDB Server 1:10.7.3+maria~focal started.
db-1  | 2025-10-27 17:14:30+00:00 [Note] [Entrypoint]: Switching to dedicated user 'mysql'
db-1  | 2025-10-27 17:14:31+00:00 [Note] [Entrypoint]: Entrypoint script for MariaDB Server 1:10.7.3+maria~focal started.
db-1  | 2025-10-27 17:14:31+00:00 [Note] [Entrypoint]: MariaDB upgrade not required
....
```

## Expected result

Listing containers should show three containers running and the port mapping as below:
```
$ docker ps
NAME                               IMAGE                            COMMAND                  SERVICE    CREATED             STATUS                       PORTS
simple-docker-compose-backend-1    simple-docker-compose-backend    "uvicorn app.main:ap…"   backend    About an hour ago   Up About an hour             8000/tcp
simple-docker-compose-db-1         mariadb:10-focal                 "docker-entrypoint.s…"   db         About an hour ago   Up About an hour (healthy)   3306/tcp, 33060/tcp
simple-docker-compose-frontend-1   simple-docker-compose-frontend   "/docker-entrypoint.…"   frontend   About an hour ago   Up About an hour             0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
simple-docker-compose-proxy-1      simple-docker-compose-proxy      "nginx -g 'daemon of…"   proxy      About an hour ago   Up About an hour             0.0.0.0:80->80/tcp, [::]:80->80/tcp
```

After the application starts, navigate to `http://localhost:80` or `http://localhost` or `http://<IP>`  in your web browser or run:
```
$ curl localhost
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Auth Demo (HTML + FastAPI + MariaDB)</title>
  <link rel="stylesheet" href="styles.css"/>
</head>
<body>
  <div class="container">
    <h1>Register Login Fetch user Demo</h1>

    <section class="card">
      <h2>Register</h2>
      <form id="registerForm">
        <label>Username <input name="username" minlength="3" maxlength="100" required></label>
        <label>Password <input name="password" type="password" minlength="6" maxlength="128" required></label>
        <button type="submit">Create account</button>
      </form>
      <pre id="registerResult" class="result"></pre>
    </section>

    <section class="card">
      <h2>Login</h2>
      <form id="loginForm">
        <label>Username <input name="username" required></label>
        <label>Password <input name="password" type="password" required></label>
        <button type="submit">Login</button>
      </form>
      <div class="row">
        <button id="logoutBtn" class="secondary">Logout</button>
        <span id="sessionInfo"></span>
      </div>
      <pre id="loginResult" class="result"></pre>
    </section>

    <section class="card">
      <h2>Users</h2>
      <div class="row">
        <button id="refreshUsersBtn">Refresh</button>
      </div>
      <table id="usersTable">
        <thead><tr><th>ID</th><th>Username</th><th>Created At</th></tr></thead>
        <tbody></tbody>
      </table>
    </section>
  </div>
  <script src="script.js"></script>
</body>
</html>
```

Stop and remove the containers
```
$ docker compose down
```
