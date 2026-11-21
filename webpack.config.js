const path = require("path");

module.exports = {
    mode: "development",
    entry: "./tools/build-src/index.js",
    output: {
        filename: "webpack-bundle.js",
        path: path.resolve(__dirname, "tools/build-output"),
        clean: false
    }
};
