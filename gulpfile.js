const { src, dest } = require("gulp");

function copyTestSource() {
    return src("tools/build-src/index.js")
        .pipe(dest("tools/build-output/gulp"));
}

exports.default = copyTestSource;
exports.copyTestSource = copyTestSource;
