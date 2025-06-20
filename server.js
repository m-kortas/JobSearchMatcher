console.log('DEBUG: Script starting');
const express = require('express');
console.log('DEBUG: express required');
const fs = require('fs');
const path = require('path');
console.log('DEBUG: fs and path required');
const app = express();
const port = 3002;
console.log('DEBUG: App created, port set to', port);


app.use(express.text({ limit: '10mb', type: 'text/csv' })); // <-- Add the 'limit' option here
console.log('DEBUG: express.text middleware added with increased limit');


// Middleware to serve your static files (HTML, CSS, client-side JS)
const publicPath = path.join(__dirname, 'public');
console.log('DEBUG: public path resolved to:', publicPath);
if (!fs.existsSync(publicPath)) {
    console.error('DEBUG: Error: public directory NOT found at', publicPath);
    // Keep this commented unless testing directory existence as a hard error
    // process.exit(1);
}
app.use(express.static(publicPath));
console.log('DEBUG: express.static middleware added for', publicPath);


// API endpoint to save job data
app.post('/api/save-jobs', (req, res) => {
    console.log('DEBUG: Received POST request to /api/save-jobs');
    const csvData = req.body;

    if (!csvData || typeof csvData !== 'string') {
        console.error('DEBUG: Bad request: No CSV data received for saving.');
        return res.status(400).send('Bad request: No CSV data received.');
    }

    const filePath = path.join(__dirname, 'public', 'job_matches.csv');
    console.log('DEBUG: Attempting to write CSV data to:', filePath);

    fs.writeFile(filePath, csvData, (err) => {
        if (err) {
            console.error('DEBUG: Error writing CSV file:', err);
            return res.status(500).send('Error saving job data to the server.');
        }
        console.log('DEBUG: job_matches.csv updated successfully.');
        res.status(200).send('Job data saved successfully.');
    });
});
console.log('DEBUG: POST /api/save-jobs route defined');


// Serve your main HTML file
app.get('/', (req, res) => {
    console.log('DEBUG: Received GET request to /');
    const indexPath = path.join(__dirname, 'public', 'index.html');
    console.log('DEBUG: Attempting to send index.html from:', indexPath);
    res.sendFile(indexPath, (err) => {
        if (err) {
            console.error('DEBUG: Error sending index.html:', err);
             if (!res.headersSent) {
                res.status(500).send('Error loading the main page.');
            }
        } else {
            console.log('DEBUG: Successfully sent index.html');
        }
    });
});
console.log('DEBUG: GET / route defined');


const server = app.listen(port, () => {
    console.log(`DEBUG: Server listening at http://localhost:${port}`);
    // Add a checkpoint immediately after the listener starts
    console.log('DEBUG: app.listen callback finished.');
});
console.log('DEBUG: app.listen call completed');

// Add listeners for server events
server.on('close', () => {
    console.log('DEBUG: Server close event fired.');
});

server.on('error', (err) => {
    console.error('DEBUG: Server error event fired:', err);
});

console.log('DEBUG: End of synchronous script execution');

// Add handlers for potential unhandled errors
process.on('unhandledRejection', (reason, promise) => {
  console.error('DEBUG: Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (err) => {
  console.error('DEBUG: Uncaught Exception:', err);
  // Exit the process, but allow logging first
   process.exit(1);
});