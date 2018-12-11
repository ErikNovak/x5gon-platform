/********************************************************************
 * PostgresQL storage process
 * This component receives the verified OER material object and stores
 * it into postgresQL database.
 */

class PostgresqlStorage {

    constructor() {
        this._name = null;
        this._onEmit = null;
        this._context = null;
    }

    init(name, config, context, callback) {
        this._name = name;
        this._context = context;
        this._onEmit = config.onEmit;
        this._prefix = `[PostgresqlStorage ${this._name}]`;

        // create the postgres connection
        this._pg = require('../../../../lib/postgresQL')(config.pg);

        // the postgres table in which we wish to insert
        this._postgresTable = config.postgres_table;

        callback();
    }

    heartbeat() {
        // do something if needed
    }

    shutdown(callback) {
        // prepare for gracefull shutdown, e.g. save state

        // close connection to postgres database
        this._pg.close();

        // shutdown component
        callback();
    }

    receive(material, stream_id, callback) {
        // takes the material and insert it into the OER material table
        this._pg.insert(material, this._postgresTable, (error, result) => {
            if (error) {
                console.warn({ error: error.message, materialUrl: material.materialUrl });
            } else {
                console.log('material inserted into oer_material database', { materialUrl: material.materialUrl });
            }
            // this is the end of the material processing pipeline
            return callback();
        });
    }
}

exports.create = function (context) {
    return new PostgresqlStorage(context);
};