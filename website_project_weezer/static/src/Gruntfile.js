module.exports = function(grunt) {

    require('time-grunt')(grunt);

    require('load-grunt-tasks')(grunt, ['grunt-*']);

    grunt.initConfig({

        pkg: grunt.file.readJSON('package.json'),

        sass: {
            build: {
                options: {
                    compass: true,
                    style: 'expanded', // Odoo will compress later
                    debugInfo: false,
                    lineNumbers: false,
                    require: ['./sass/url64.rb']
                },
                expand: true,
                cwd: './sass/',
                src: ['*.scss'],
                dest: './css/',
                ext: '.css'
            }
        },

        watch: {
            scripts: {
                files: ['**/*.scss'],
                tasks: ['sass'],
                options: {
                    spawn: false,
                }
            }
        }

    });

    grunt.registerTask('default', ['sass','watch']);

};