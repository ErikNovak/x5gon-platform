/**
 * Runs the X5GON platform server
 */

// external modules
const gatsbyExpress = require("gatsby-plugin-express");
const express = require("express");
const bodyParser = require("body-parser");
const cookieParser = require("cookie-parser");
const session = require("express-session");
const passport = require("passport");
const flash = require("connect-flash");
const path = require("path");
// configurations
const config = require("./config/config");

// internal modules
const PostgreSQL = require("./library/postgresQL");
const pgSession = require("connect-pg-simple")(session);
const Logger = require("./library/logger");
const Monitor = require("./library/process-monitor");

// create a logger for platform requests
const logger = Logger.createGroupInstance("requests", "platform", config.isProduction);
// create process monitoring instance
const monitor = new Monitor();

const pg = new PostgreSQL(config.pg);

// create express app
let app = express();
let http = require("http").Server(app);

// add the public folder
app.use(express.static(path.join(__dirname, "/public/")));
// configure application
app.use(bodyParser.json()); // to support JSON-encoded bodies
app.use(bodyParser.urlencoded({ // to support URL-encoded bodies
    extended: true
}));
// redirect specific requests to other services
require("./routes/proxies")(app, config);
// configure cookie parser
app.use(cookieParser(config.platform.sessionSecret));

// add session configurations
if (config.isProduction) {
    app.set("trust proxy", 1);
}
app.use(session({
    store: new pgSession({
        pool: pg._pool
    }),
    secret: config.platform.sessionSecret,
    saveUninitialized: false,
    resave: false,
    cookie: {
        maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
        ...(config.isProduction && { domain: ".x5gon.org" })
    }
}));
// use flash messages
app.use(flash());
// initialize authentication
app.use(passport.initialize());
app.use(passport.session({ secret: config.platform.sessionSecret }));
// passport configuration
require("./settings/passport")(passport, pg);
// socket.io configuration
require("./settings/sockets")(http, monitor);

app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "X-Requested-With");
    next();
});

// add handlebars configurations
require("./settings/handlebars")(app);

// sets the API routes - adding the postgresql connection, logger, config file,
// passport object (for authentication), and monitoring object
require("./routes/route.handler")(app, pg, logger, config, passport, monitor);

const frontEndPath = path.join(__dirname, "/frontend");
app.use(express.static(path.join(frontEndPath, "public")));
app.use(gatsbyExpress(path.join(frontEndPath, "/gatsby-express.json"), {
    publicDir: path.join(frontEndPath, "/public"),
    // redirects all /path/ to /path
    // should be used with gatsby-plugin-remove-trailing-slashes
    redirectSlashes: true
}));

// parameters used on the express app
const PORT = config.platform.port;
// start the server without https
const server = http.listen(PORT, () => logger.info(`platform listening on port ${PORT}`));

// export the server for testing
module.exports = server;
