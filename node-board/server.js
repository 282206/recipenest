// RecipeNest Quick Browse - a lightweight Node.js server (no npm packages needed)
//  - serves the AngularJS page from /public
//  - forwards /api/* requests to the Django server, so the browser
//    never has to make a cross-origin (CORS) request
// Run:  node server.js     then open http://localhost:3000

const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 3000;
const DJANGO = { host: "127.0.0.1", port: 8000 };
const PUBLIC_DIR = path.join(__dirname, "public");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

function proxyToDjango(req, res) {
  const options = {
    hostname: DJANGO.host,
    port: DJANGO.port,
    path: req.url,
    method: req.method,
    headers: { ...req.headers, host: `${DJANGO.host}:${DJANGO.port}` },
  };
  const upstream = http.request(options, (djangoRes) => {
    res.writeHead(djangoRes.statusCode, djangoRes.headers);
    djangoRes.pipe(res);
  });
  upstream.on("error", () => {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Django server is not running on port 8000" }));
  });
  req.pipe(upstream);
}

function serveStatic(req, res) {
  const urlPath = req.url.split("?")[0];
  const file = urlPath === "/" ? "index.html" : urlPath.slice(1);
  const fullPath = path.join(PUBLIC_DIR, path.normalize(file));

  if (!fullPath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403);
    return res.end("Forbidden");
  }
  fs.readFile(fullPath, (err, data) => {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      return res.end("Not found");
    }
    res.writeHead(200, { "Content-Type": MIME[path.extname(fullPath)] || "application/octet-stream" });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  console.log(`${new Date().toLocaleTimeString()}  ${req.method} ${req.url}`);
  if (req.url.startsWith("/api/")) return proxyToDjango(req, res);
  serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`RecipeNest Quick Browse running at http://localhost:${PORT}`);
});
