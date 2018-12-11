// configurations
const config = require('../../../config/config');

module.exports = {
    "general": {
        "heartbeat": 2000,
        "pass_binary_messages": true
    },
    "spouts": [
        {
            "name": "video-input",
            "type": "inproc",
            "working_dir": "./spouts",
            "cmd": "kafka-spout.js",
            "init": {
                "kafka_host": config.kafka.host,
                "topic": "video-topic"
            }
        }
    ],
    "bolts": [
        {
            "name": "material-format",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "material-format.js",
            "inputs": [{
                "source": "video-input"
            }],
            "init": {}
        },
        {
            "name": "video-content-extraction",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "extraction-ttp.js",
            "inputs": [{
                "source": "material-format"
            }],
            "init": {
                "user": config.ttp.user,
                "token": config.ttp.token
            }
        },
        {
            "name": "wikification",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "extraction-wikipedia.js",
            "inputs": [{
                "source": "video-content-extraction"
            }],
            "init": {
                "userKey": config.preproc.wikifier.userKey,
                "wikifierUrl": config.preproc.wikifier.wikifierUrl
            }
        },
        {
            "name": "material-validator",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "material-validator.js",
            "inputs": [{
                "source": "wikification"
            }],
            "init": {}
        },

        /****************************************
         * Storing OER materials into the
         * production and development tables
         */

        {
            "name": "postgresql-storage-production",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "postgresql-storage.js",
            "inputs": [{
                "source": "material-validator",
            }],
            "init": {
                "postgres_table": "oer_materials",
                "pg": config.pg
            }
        },
        {
            "name": "postgresql-storage-development",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "postgresql-storage.js",
            "inputs": [{
                "source": "material-validator",
            }],
            "init": {
                "postgres_table": "oer_materials_dev",
                "pg": config.pg
            }
        },

        /****************************************
         * Storing partial OER materials
         */

        {
            "name": "postgresql-storage-partial",
            "type": "inproc",
            "working_dir": "./bolts",
            "cmd": "postgresql-storage.js",
            "inputs": [{
                "source": "material-format",
                "stream_id": "stream_partial"
            },{
                "source": "video-content-extraction",
                "stream_id": "stream_partial"
            },{
                "source": "wikification",
                "stream_id": "stream_partial"
            },{
                "source": "material-validator",
                "stream_id": "stream_partial"
            }],
            "init": {
                "postgres_table": "oer_materials_partial",
                "pg": config.pg
            }
        }
    ],
    "variables": {}
};