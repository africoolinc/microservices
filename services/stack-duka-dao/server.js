// server.js - Node.js Express application for Duka DAO website

const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public')); // Serve static files (CSS, JS)
app.set('view engine', 'ejs'); // Use EJS for templating
app.set('views', path.join(__dirname, 'views'));

// Ensure DAO_members folder and members.json exist
const membersDir = path.join(__dirname, 'DAO_members');
const membersFile = path.join(membersDir, 'members.json');
if (!fs.existsSync(membersDir)) {
  fs.mkdirSync(membersDir);
}
if (!fs.existsSync(membersFile)) {
  fs.writeFileSync(membersFile, JSON.stringify([]));
}

// Home page with product market list
app.get('/', (req, res) => {
  res.render('index');
});

// Signup page
app.get('/signup', (req, res) => {
  res.render('signup');
});

// Handle signup form submission
app.post('/signup', (req, res) => {
  const { name, email, phone } = req.body;

  // Read existing members
  let members = JSON.parse(fs.readFileSync(membersFile, 'utf8'));

  // Add new member
  members.push({ name, email, phone, signupDate: new Date().toISOString() });

  // Write back to file
  fs.writeFileSync(membersFile, JSON.stringify(members, null, 2));

  // Redirect to thank you page or home with success message
  res.redirect('/?success=true');
});

// Start server
app.listen(port, () => {
  console.log(`Duka DAO Server running at http://localhost:${port}`);
});
