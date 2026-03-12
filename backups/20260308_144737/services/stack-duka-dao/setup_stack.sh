#!/bin/bash

# duka_dao_setup.sh - Updated Setup script for Duka DAO Docker Tech Stack
# Fixes npm ci error by switching to 'npm install --omit=dev' in Dockerfile (no lockfile needed).
# All other functionality unchanged. Run as: bash duka_dao_setup.sh

set -euo pipefail  # Exit on error, unset variables, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

# Function to create directories idempotently
create_dirs() {
    mkdir -p views public/css public/js DAO_members
    log "Created project directories."
}

# Function to write file content using heredoc
write_file() {
    local file="$1"
    shift
    cat <<EOF > "$file"
$*
EOF
    log "Wrote file: $file"
}

# Function to check/install prerequisites
check_prereqs() {
    if ! command -v docker &> /dev/null; then
        error "Docker is required. Install from https://docs.docker.com/engine/install/"
    fi
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is required. Install from https://docs.docker.com/compose/install/"
    fi
    if ! command -v systemctl &> /dev/null; then
        error "systemd is required (Linux only). This script assumes a systemd-based system."
    fi
    # Ensure Docker service starts on boot
    sudo systemctl enable docker --now || log "Docker already enabled."
}

# Main setup for Node.js app files (renamed to Duka DAO)
setup_app_files() {
    create_dirs

    # Write package.json (init if needed, but we'll create it)
    cat > package.json <<EOF
{
  "name": "duka-dao",
  "version": "1.0.0",
  "description": "Duka DAO - Marketplace DAO for emerging markets",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "body-parser": "^1.20.0",
    "ejs": "^3.1.0"
  }
}
EOF
    log "Created package.json"

    # Write server.js (renamed/rethemed)
    write_file server.js \
'// server.js - Node.js Express application for Duka DAO website

const express = require('"'"'express'"'"');
const bodyParser = require('"'"'body-parser'"'"');
const fs = require('"'"'fs'"'"');
const path = require('"'"'path'"'"');
const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('"'"'public'"'"')); // Serve static files (CSS, JS)
app.set('"'"'view engine'"'"', '"'"'ejs'"'"'); // Use EJS for templating
app.set('"'"'views'"'"', path.join(__dirname, '"'"'views'"'"'));

// Ensure DAO_members folder and members.json exist
const membersDir = path.join(__dirname, '"'"'DAO_members'"'"');
const membersFile = path.join(membersDir, '"'"'members.json'"'"');
if (!fs.existsSync(membersDir)) {
  fs.mkdirSync(membersDir);
}
if (!fs.existsSync(membersFile)) {
  fs.writeFileSync(membersFile, JSON.stringify([]));
}

// Home page with product market list
app.get('"'"'/'"'"', (req, res) => {
  res.render('"'"'index'"'"');
});

// Signup page
app.get('"'"'/signup'"'"', (req, res) => {
  res.render('"'"'signup'"'"');
});

// Handle signup form submission
app.post('"'"'/signup'"'"', (req, res) => {
  const { name, email, phone } = req.body;

  // Read existing members
  let members = JSON.parse(fs.readFileSync(membersFile, '"'"'utf8'"'"'));

  // Add new member
  members.push({ name, email, phone, signupDate: new Date().toISOString() });

  // Write back to file
  fs.writeFileSync(membersFile, JSON.stringify(members, null, 2));

  // Redirect to thank you page or home with success message
  res.redirect('"'"'/?success=true'"'"');
});

// Start server
app.listen(port, () => {
  console.log(`Duka DAO Server running at http://localhost:${port}`);
});'

    # Write views/index.ejs (renamed/rethemed to Duka DAO - marketplace focus)
    write_file views/index.ejs \
'<!-- views/index.ejs - Home page with product market list for Duka DAO -->

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Duka DAO - Marketplace DAO for Emerging Markets</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="/css/styles.css"> <!-- Custom CSS for engagement -->
</head>
<body>
  <header class="bg-primary text-white text-center py-5">
    <h1>Welcome to Duka DAO</h1>
    <p>Decentralized marketplace governance for unbanked traders and vendors</p>
    <a href="/signup" class="btn btn-light btn-lg">Sign Up Now</a> <!-- CTA for engagement -->
  </header>

  <section class="container my-5">
    <h2>Product Market List: Verticals and Use Cases</h2>
    <p>Explore our marketplace verticals and revenue-generating use cases for emerging markets.</p>

    <!-- Verticals Table - Optimized for readability and engagement -->
    <table class="table table-striped table-hover">
      <thead>
        <tr>
          <th>Vertical</th>
          <th>Projected Market Size (2025)</th>
          <th>Revenue Potential</th>
          <th>Key Risks</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>E-commerce/Marketplace</td>
          <td>$1T+ (global digital trade)</td>
          <td>High (transaction fees on vendors)</td>
          <td>Logistics in remote areas</td>
        </tr>
        <tr>
          <td>DeFi/Trade Finance</td>
          <td>$100B TVL</td>
          <td>Medium-High (lending for inventory)</td>
          <td>Crypto volatility</td>
        </tr>
        <tr>
          <td>Governance/Community</td>
          <td>$10B DAO assets</td>
          <td>Medium (vendor subscriptions)</td>
          <td>Low vendor engagement</td>
        </tr>
        <tr>
          <td>AI/Data Services</td>
          <td>$5B AI-blockchain</td>
          <td>High (market analytics)</td>
          <td>Data privacy concerns</td>
        </tr>
        <tr>
          <td>Gaming/NFTs</td>
          <td>$50B Web3 gaming</td>
          <td>Medium (digital collectibles)</td>
          <td>Competition from centralized platforms</td>
        </tr>
      </tbody>
    </table>

    <!-- Use Cases List - With accordions for interactive engagement -->
    <h3>Key Use Cases</h3>
    <div class="accordion" id="useCasesAccordion">
      <div class="card">
        <div class="card-header" id="headingEcom">
          <h5 class="mb-0">
            <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapseEcom" aria-expanded="true" aria-controls="collapseEcom">
              E-commerce and Marketplace
            </button>
          </h5>
        </div>
        <div id="collapseEcom" class="collapse show" aria-labelledby="headingEcom" data-parent="#useCasesAccordion">
          <div class="card-body">
            - Listing Fees for Products<br>
            - Cross-Border Trade<br>
            - Affiliate Vendor Referrals
          </div>
        </div>
      </div>
      <!-- Add similar accordions for other verticals -->
      <div class="card">
        <div class="card-header" id="headingDeFi">
          <h5 class="mb-0">
            <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseDeFi" aria-expanded="false" aria-controls="collapseDeFi">
              DeFi and Trade Finance
            </button>
          </h5>
        </div>
        <div id="collapseDeFi" class="collapse" aria-labelledby="headingDeFi" data-parent="#useCasesAccordion">
          <div class="card-body">
            - Yield Farming for Vendors<br>
            - DAO-Backed Inventory Loans<br>
            - Passive Income via Smart Contracts
          </div>
        </div>
      </div>
      <!-- Repeat for Governance, AI, Gaming -->
    </div>

    <div class="text-center mt-4">
      <a href="/signup" class="btn btn-primary btn-lg">Join Duka DAO Today!</a> <!-- Repeated CTA -->
    </div>
  </section>

  <footer class="bg-dark text-white text-center py-3">
    <p>&copy; 2025 Duka DAO</p>
  </footer>

  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="/js/engagement.js"></script> <!-- Custom JS for engagement -->
</body>
</html>'

    # Write views/signup.ejs (renamed/rethemed)
    write_file views/signup.ejs \
'<!-- views/signup.ejs - Signup page for Duka DAO -->

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign Up - Duka DAO</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="/css/styles.css">
</head>
<body>
  <header class="bg-primary text-white text-center py-5">
    <h1>Sign Up to Join Duka DAO</h1>
    <p>Enroll now and start participating in marketplace governance</p>
  </header>

  <section class="container my-5">
    <form action="/signup" method="POST" class="border p-4 rounded">
      <div class="form-group">
        <label for="name">Name</label>
        <input type="text" class="form-control" id="name" name="name" required>
      </div>
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" class="form-control" id="email" name="email" required>
      </div>
      <div class="form-group">
        <label for="phone">Phone Number</label>
        <input type="tel" class="form-control" id="phone" name="phone" required placeholder="+254...">
      </div>
      <button type="submit" class="btn btn-primary btn-block">Sign Up</button>
    </form>

    <div class="text-center mt-3">
      <p>Already a member? <a href="/">Go back to home</a></p>
    </div>
  </section>

  <footer class="bg-dark text-white text-center py-3">
    <p>&copy; 2025 Duka DAO</p>
  </footer>

  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'

    # Write public/css/styles.css (unchanged, but logged)
    write_file public/css/styles.css \
'/* public/css/styles.css - Custom styles for engagement optimization */

/* Mobile-first responsive design */
body {
  font-family: Arial, sans-serif;
}

/* Fast loading: Simple styles, no heavy images */
.table-hover tbody tr:hover {
  background-color: #f8f9fa; /* Interactive hover for engagement */
}

/* CTAs with contrast */
.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
}

/* Accordion for interactive content */
.accordion .card-header button {
  text-decoration: none;
}'

    # Write public/js/engagement.js (updated for Duka DAO)
    write_file public/js/engagement.js \
'// public/js/engagement.js - Client-side JS for engagement

// Lazy loading for images (if any)
document.addEventListener('"'"'DOMContentLoaded'"'"', () => {
  // Example: Add social share buttons dynamically
  const shareBtn = document.createElement('"'"'button'"'"');
  shareBtn.className = '"'"'btn btn-secondary mt-3'"'"';
  shareBtn.textContent = '"'"'Share on X'"'"';
  shareBtn.onclick = () => {
    window.open('"'"'https://x.com/intent/tweet?text=Join Duka DAO - Marketplace for Emerging Markets!&url='"'"' + window.location.href);
  };
  document.querySelector('"'"'.text-center.mt-4'"'"').appendChild(shareBtn);

  // Success message if redirected
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('"'"'success'"'"') === '"'"'true'"'"') {
    alert('"'"'Signup successful! Welcome to Duka DAO.'"'"');
  }
});'

    # Write DAO_members/members.json (initial empty)
    write_file DAO_members/members.json '[]'
}

# Setup Docker files (updated Dockerfile to fix npm ci issue)
setup_docker() {
    # Write Dockerfile (fixed: use npm install --omit=dev instead of npm ci)
    cat > Dockerfile <<EOF
# Dockerfile for Duka DAO Node.js app
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use install --omit=dev to avoid needing lockfile; generates one if missing)
RUN npm install --omit=dev && npm cache clean --force

# Copy app source
COPY . .

# Expose port
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:3000', (res) => { if (res.statusCode !== 200) throw new Error(); })"

# Start app
CMD ["npm", "start"]
EOF
    log "Created updated Dockerfile (fixed npm install)."

    # Write docker-compose.yml with restart policy
    cat > docker-compose.yml <<EOF
# docker-compose.yml for Duka DAO Tech Stack
version: '3.8'

services:
  duka-dao-app:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./DAO_members:/app/DAO_members  # Persist members data
    restart: unless-stopped  # Auto-restart on boot/failure
    environment:
      - NODE_ENV=production

volumes:
  duka_data:
EOF
    log "Created docker-compose.yml"
}

# Setup systemd service for auto-start
setup_systemd() {
    local service_name="duka-dao-stack"
    local compose_dir=$(pwd)

    # Create service file (updated ExecStart/Stop to use 'docker compose' if v2, but fallback to docker-compose)
    local compose_cmd="docker compose"
    if ! command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    fi

    sudo tee /etc/systemd/system/${service_name}.service > /dev/null <<EOF
[Unit]
Description=Duka DAO Docker Compose Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${compose_dir}
ExecStart=${compose_cmd} up -d
ExecStop=${compose_cmd} down
TimeoutStartSec=0
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    # Reload and enable
    sudo systemctl daemon-reload
    sudo systemctl enable ${service_name}.service
    log "Created and enabled systemd service: ${service_name}.service"
    log "To start now: sudo systemctl start ${service_name}.service"
}

# Build and test (optional, but idempotent)
build_and_test() {
    log "Building Docker image..."
    docker-compose build --no-cache

    log "Starting stack (detached)..."
    docker-compose up -d

    log "Waiting for app to be healthy..."
    sleep 10

    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log "Success! Duka DAO is running at http://localhost:3000"
    else
        error "App failed to start. Check logs: docker-compose logs"
    fi
}

# Main execution
main() {
    log "Starting Duka DAO Tech Stack setup (updated to fix npm build error)..."

    check_prereqs
    setup_app_files
    setup_docker
    setup_systemd

    log "Setup complete!"
    log "The stack will auto-start on boot via systemd."
    log "To manage:"
    log "  - Start: sudo systemctl start duka-dao-stack"
    log "  - Stop: sudo systemctl stop duka-dao-stack"
    log "  - Logs: journalctl -u duka-dao-stack or docker-compose logs"
    log "  - Access: http://localhost:3000"
    log "  - Rebuild: docker-compose build --no-cache && docker-compose up -d"

    # Optional: Build and test if user confirms (comment out if not desired)
    read -p "Build and start now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_and_test
    fi
}

main "$@"


