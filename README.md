# Docker Workshop Template

A ready-to-use template for creating browser-based coding workshops. Clone it, customize it, and build your own workshop in minutes! Well, maybe not minutes, but it sure is cool looking.

## What Is This?

This template provides a complete workshop environment that runs entirely in Docker with an integrated workbench interface. Attendees get everything they need in one browser window:

- 📚 **Documentation** - Step-by-step instructions
- 💻 **Code Editor** - VS Code in the browser
- 🚀 **Live Preview** - See changes instantly
- 🖥️ **Terminal** - Command-line access
- 🗄️ **Redis Insight** - Database visualization

Perfect for teaching web development, APIs, databases, or any coding topic!

## This Repo: Redis Iris Workshop

This copy of the template runs the [Redis Iris demos](code/iris/README.md) (Semantic Routing, LangCache, Agent Memory, Context Retriever). Before the first `docker compose up`, nothing else is needed; once it is running, fill in the credentials in `code/iris/.env` and run `make setup` in the Terminal panel (see `docs/setup/setup.md`). The agent runs on Gemini through Google Cloud (Vertex AI), using a service account key saved as `secrets/gcp-key.json`; the setup page has the steps. Embeddings run locally, so there is no other model account to create. The demo starts without the key and the chat says it is missing; the backend restarts itself when `.env` changes.

## Try the Demo

See what your attendees will experience:

1. **Clone and start:**
   ```bash
   git clone https://github.com/your-repo/workshop-docker-template.git
   cd workshop-docker-template
   docker compose up
   ```

2. **Wait for services to start** (you'll see "ready in X ms" from Vite in the logs)

3. **Open the workbench:**
   ```
   http://localhost
   ```

You'll see a unified interface with:

- **Left sidebar:** Workshop documentation
- **Right panels:** Code editor and a live app preview

**Try it out:**
- Edit `code/web/index.html` in the Code panel
- Watch changes appear instantly in the App panel

There are other panels including a terminal and Redis Insight. They are hidden by default but can be shown by clicking the menu button in the top left corner.

Getting a little crowded? Open any panel in a new browser tab if you prefer (URLs shown in the workbench)

## Building Your Own Workshop

### Step 1: Clone and Customize

```bash
# Clone this template
git clone https://github.com/your-repo/workshop-docker-template.git my-workshop
cd my-workshop

# Remove the original git history if you want to start fresh
rm -rf .git
git init
```

### Step 2: Update the Workbench Title

Edit `workbench/config.js`:

```javascript
const config = {
  title: "My Awesome Workshop",  // ← Change this
  // ... rest of config
};
```

### Step 3: Write Your Workshop Content

**Documentation** (`docs/` folder):
- Edit `docs/home.md` - Your workshop welcome page
- Edit `docs/setup/*.md` - Setup instructions
- Edit `docs/tasks/*.md` - Workshop exercises
- Edit `docs/reference/*.md` - Reference materials

Docsify automatically renders your markdown as interactive HTML.

**Starter Code** (`code/web/` folder):
- Edit `code/web/index.html` - Starting HTML
- Edit `code/web/style.css` - Starting CSS
- Edit `code/web/main.js` - Starting JavaScript
- Update `code/web/package.json` - Add dependencies your workshop needs

### Step 4: Test Your Workshop

```bash
docker compose up
```

Open http://localhost and go through your workshop as a student would.

### Step 5: Add More Services (Optional)

Need another service? You'll need to update three files:

**1. Add the service to `docker-compose.yml`:**

```yaml
services:
  # ... existing services ...

  myservice:
    image: myservice:latest
    container_name: workshop-myservice
```

Note: Services don't need exposed ports — they're accessed through the workbench proxy.

**2. Add a proxy route to `workbench/nginx.conf`:**

```nginx
location /myservice/ {
    proxy_pass http://myservice:8080/;
    include /etc/nginx/proxy/proxy-params.conf;
}
```

If your service uses WebSockets, also add:
```nginx
    include /etc/nginx/proxy/proxy-params-websocket.conf;
```

NOTE: Tools like vite, which we are using, use Websockets for hot module replacement. So, even though your code is not using WebSockets, the server might.

If your service has long-lived connections that might exceed nginx's default 60-second timeout (e.g., long-running API), also add:
```nginx
    include /etc/nginx/proxy/proxy-params-long-running.conf;
```

⚠️ **Trailing slash warning:** The trailing slash in `proxy_pass` matters!
- With slash (`http://host:port/`): strips the location prefix from the request
- Without slash (`http://host:port`): preserves the full path

Most services work with the trailing slash. Some (like Vite, Redis Insight) need the path preserved — check the service's documentation.

**3. Add a panel to `workbench/config.js`:**

```javascript
panels: [
  // ... existing panels ...
  {
    id: 'myservice',
    name: 'My Service',
    path: '/myservice/',
    icon: 'fa-cube',
    visible: true
  }
]
```

### Step 6: Deploy

See [SETUP.md](SETUP.md) for detailed instructions on deploying this to PS Portal.

## Reference

### Project Structure

```
.
├── docker-compose.yml     # Docker configuration - add services here
├── workbench/             # Unified workbench interface
│   ├── index.html         # Main workbench page
│   ├── config.js          # ← CUSTOMIZE: Panel configuration
│   ├── nginx.conf         # ← CUSTOMIZE: Proxy routes for services
│   ├── proxy/             # Shared proxy config includes
│   │   ├── proxy-params.conf              # Common proxy headers
│   │   ├── proxy-params-websocket.conf    # WebSocket support headers
│   │   └── proxy-params-long-running.conf # Timeout settings for long connections
│   └── assets/            # Workbench styles and scripts
├── code/                  # ← CUSTOMIZE: Your workshop starter code
│   └── iris/              # Redis Iris demo (FastAPI backend + React/Vite frontend)
│       ├── .env           # Credentials (copied from .env.example on first start)
│       ├── Makefile       # make setup / reset / domains
│       ├── backend/       # Served at /api/ by the `backend` container
│       └── frontend/      # Served at /app/ by the `web` container (Vite, base /app/)
├── docs/                  # ← CUSTOMIZE: Your workshop documentation
│   ├── index.html         # Docsify entry point
│   ├── home.md            # Welcome page
│   ├── setup/             # Setup instructions
│   ├── tasks/             # Workshop exercises
│   └── reference/         # Reference materials
└── README.md              # This file
```

### How It Works

The environment runs six Docker containers, all accessed through a single nginx reverse proxy on port 80:

1. **workbench** (port 80)
   - Nginx reverse proxy serving the unified workbench interface
   - Routes all services via paths (e.g., `/vscode/`, `/app/`, `/terminal/`)
   - Same-origin access eliminates iframe security issues

2. **vscode** (accessed via `/vscode/`)
   - VS Code running in your browser (code-server)
   - Mounts the `code/` folder for editing
   - No authentication required (configured with `--auth none`)

3. **web** (accessed via `/app/` and `/terminal/`)
   - Vite development server with hot module replacement
   - Web-based terminal (ttyd) for command-line access
   - Automatically installs npm dependencies on startup

4. **docs** (accessed via `/docs/`)
   - Nginx serving Docsify documentation
   - Renders markdown files as interactive HTML
   - Updates in real-time when markdown changes

5. **redis**
   - Local Redis database, available to the web container at `redis:6379`
   - Not used by the Iris demo, which reads and writes the Redis database configured in `code/iris/.env`

6. **redisinsight** (accessed via `/redisinsight/`)
   - Redis Insight GUI for database visualization
   - Starts with no database. Add the Redis database from `code/iris/.env` (the Iris demo does not use the local `redis` container) by following Task 2 in the workshop docs

**Path-Based Routing:**

All services are accessed through the workbench nginx proxy using paths instead of ports. This approach:

- Makes all iframes same-origin, avoiding X-Frame-Options issues
- Exposes only a single port (80), simplifying deployment
- Works seamlessly with platforms like PS Portal

**File Synchronization:**

- VS Code edits files in `code/web/`
- Vite watches `code/web/` for changes
- When you save in VS Code → Vite detects the change → Browser hot-reloads

**Security Note:** VS Code only has access to the `code/` folder, not the root project directory. This prevents accidental modification of `docker-compose.yml` or other infrastructure files.

### Using the Workbench

**Panel Controls:**
- **Drag dividers** between panels to resize
- Click the **refresh button** (↻) to reload a panel
- Click the **eye button** to hide a panel
- Click the **maximize button** (⛶) on any panel for full-screen

**Showing Hidden Panels:**
- Click the **☰ menu button** (top-left) to show/hide panels

**Opening in New Tabs:**
- Click the **open in new tab button** (↗) in the panel header to open the panel in a new tab 

Useful for multi-monitor setups or when the workbench gets too crowded.


### Stopping the Environment

```bash
docker compose down              # Stop services
docker compose down -v           # Stop and remove all data
```

---

## Common Customizations

### Editing config.js

The `workbench/config.js` file controls which panels appear in the workbench:

```javascript
const config = {
  title: "My Workshop",  // Displayed in the header

  sidebar: {
    id: 'instructions',
    name: 'Instructions',
    path: '/docs/',      // Path through nginx proxy
    icon: 'fa-book'
  },

  panels: [
    {
      id: 'vscode',
      name: 'Code',
      path: '/vscode/',  // Path through nginx proxy
      icon: 'fa-code',
      visible: true      // Show by default
    },
    // ... more panels
  ]
};
```

**Panel fields:**
- `id` - Unique identifier
- `name` - Display name in header and menu
- `path` - URL path (must match a route in nginx.conf)
- `icon` - Font Awesome icon class
- `visible` - Whether shown by default (can be toggled via menu)

### Editing nginx.conf

The `workbench/nginx.conf` file defines proxy routes for each service:

```nginx
location /myservice/ {
    proxy_pass http://myservice:8080/;
    include /etc/nginx/proxy/proxy-params.conf;
}
```

Each panel's `path` in config.js must have a matching `location` block in nginx.conf.

⚠️ **Trailing slash warning:** See the comments in nginx.conf — the trailing slash in `proxy_pass` changes behavior significantly.

### Adding More Documentation

Docsify supports:
- Multiple markdown files (automatically linked)
- Sidebar navigation (`docs/_sidebar.md`)
- Navbar (`docs/_navbar.md`)
- Cover page (`docs/_coverpage.md`)
- Custom themes and plugins
- Search functionality

Just add `.md` files to `docs/` and they'll be rendered automatically.

---

### Attendee Experience

**What attendees see:**
- One URL to open (the workbench)
- All tools in one browser window
- Instant feedback when they make changes
- No installation or setup required

**What attendees can do:**
- Follow instructions in the sidebar
- Edit code in the browser
- See results immediately
- Use the terminal if needed
- Open panels in new tabs for multi-monitor setups

