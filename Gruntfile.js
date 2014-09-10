module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    less: {
      bootstrap: {
        options: {
          compress: true, // minify the result
          strictMath: true
        },
        files: {
          "./app/static/css/bootstrap.min.css": "./src/less/bootstrap/bootstrap.less"
        }
      }
    },
    watch: {
      files: "./src/less/bootstrap/*",
      tasks: ["less"],
    }
  });

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.registerTask('default', ['less']);
};
