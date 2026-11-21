module.exports = function (grunt) {
    grunt.initConfig({
        copy: {
            testSource: {
                src: "tools/build-src/index.js",
                dest: "tools/build-output/grunt/index.js"
            }
        }
    });

    grunt.registerTask("default", ["copy:testSource"]);

    grunt.registerTask("copy:testSource", function () {
        const fs = require("fs");
        const path = require("path");

        const source = path.resolve("tools/build-src/index.js");
        const destination = path.resolve("tools/build-output/grunt/index.js");

        fs.mkdirSync(path.dirname(destination), { recursive: true });
        fs.copyFileSync(source, destination);

        grunt.log.ok("SCDF test source copied successfully.");
    });
};
