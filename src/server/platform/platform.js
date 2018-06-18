/**
 * Runs the X5GON platform server
 */

// external modules
const https = require('https');
const express = require('express');
const helmet = require('helmet');
const exphbs = require('express-handlebars');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const fs = require('fs');


// internal modules
const pg = require('../../lib/postgresQL')(require('../../config/pgconfig'));
const Logger = require('../../lib/logging-handler')();

// create a logger instance for logging API requests
const logger = Logger.createGroupInstance('api-requests', 'api');

// parameters given to the process
const argv = require('minimist')(process.argv.slice(2));
// log process parameters
logger.info('accepted process parameters', { argv });

// create express app
let app = express();

// configure application
app.use(bodyParser.json());     // to support JSON-encoded bodies
app.use(bodyParser.urlencoded({ // to support URL-encoded bodies
    extended: true
}));

app.use(session({
    secret: argv['session-secret'],
    resave: true,
    saveUninitialized: true,
    cookie: { domain: '.x5gon.org' }
}));

// add the public folder
app.use(express.static(__dirname + '/public/'));
// secure Express server through setting HTTP headers
app.use(helmet());
// set rendering engine
app.engine('hbs', exphbs({
    extname: 'hbs',
    defaultLayout: 'main'
}));
app.set('view engine', 'hbs');

// TODO: handle redirections - using proxy

// cookie parser
app.use(cookieParser(argv['session-secret']));

// sets the API routes
require('./routes/route.handler')(app, pg, logger);

// parameters used on the express app
const PORT = argv.PORT || 8080;

// security options
const security = require('./config/security');

if (security['ssl-certificate']) {
    // set https options and run the server
    const sslOptions = {
        cert: fs.readFileSync(security['ssl-certificate'].cert, 'utf8'),
        key: fs.readFileSync(security['ssl-certificate'].key, 'utf8')
    };
    https.createServer(sslOptions, app).listen(PORT);
    logger.info(`platform listening on port ${PORT}`);
} else {
    // start the server without https
    app.listen(PORT, () => logger.info(`platform listening on port ${PORT}`));
}