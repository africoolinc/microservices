/**
 * Cloudflare Worker Deployment Script
 * 
 * Deploys the .crypto DNS resolver worker to Cloudflare
 */

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

const CLOUDFLARE_API_TOKEN = process.env.CLOUDFLARE_API_TOKEN;
const CLOUDFLARE_ACCOUNT_ID = process.env.CLOUDFLARE_ACCOUNT_ID;
const WORKER_NAME = 'crypto-dns-resolver';
const DOMAIN = process.env.DOMAIN || 'mamaduka.crypto';

// Read the worker script
const workerScript = fs.readFileSync(path.join(__dirname, 'worker.js'), 'utf8');

async function deployWorker() {
  if (!CLOUDFLARE_API_TOKEN || !CLOUDFLARE_ACCOUNT_ID) {
    console.error('❌ Missing CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID');
    process.exit(1);
  }

  console.log(`🚀 Deploying ${WORKER_NAME} to Cloudflare...`);
  console.log(`   Account: ${CLOUDFLARE_ACCOUNT_ID}`);
  console.log(`   Worker: ${WORKER_NAME}`);

  try {
    // Upload the worker script
    const response = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${WORKER_NAME}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`,
          'Content-Type': 'application/javascript'
        },
        body: workerScript
      }
    );

    const result = await response.json();

    if (result.success) {
      console.log('✅ Worker uploaded successfully!');
      
      // Set route for .crypto domains
      await setRoutes();
    } else {
      console.error('❌ Deployment failed:', result.errors);
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

async function setRoutes() {
  console.log('📍 Setting up routes...');
  
  // Route: *.mamaduka.crypto/* → Worker
  const route = `*.${DOMAIN}/*`;

  try {
    const response = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/routes`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          pattern: route,
          script_name: WORKER_NAME
        })
      }
    );

    const result = await response.json();

    if (result.success) {
      console.log(`✅ Route configured: ${route}`);
    } else {
      console.log('⚠️  Route setup warning:', result.errors);
    }

  } catch (error) {
    console.error('⚠️  Route setup error:', error.message);
  }
}

async function getStatus() {
  console.log(`📊 Checking worker status...`);

  try {
    const response = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${WORKER_NAME}`,
      {
        headers: {
          'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`
        }
      }
    );

    const result = await response.json();

    if (result.success) {
      console.log('✅ Worker is active!');
      console.log(`   Last modified: ${result.result.modified_on}`);
      console.log(`   Version: ${result.result.version}`);
    } else {
      console.log('⚠️  Worker not found');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// Parse command line args
const command = process.argv[2];

if (command === 'status') {
  getStatus();
} else {
  deployWorker();
}
