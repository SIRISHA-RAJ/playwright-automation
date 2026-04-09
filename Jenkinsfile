pipeline {
    agent any

    stages {
        // Stage 1: Jenkins automatically clones, so we don't need a manual 'git' stage
        // unless you are cloning a SECOND different repository.

        stage('Build Docker Image') {
            steps {
                bat 'docker build --cache-from playwright-tests -t playwright-tests .'
            }
        }

        stage('Run Tests') {
            steps {
                // Create the reports folder if it doesn't exist
                bat 'if not exist reports mkdir reports'
                
                // Run the container. Note: We don't add "pytest..." at the end 
                // because the Dockerfile CMD handles it.
                bat "docker run --rm -v %WORKSPACE%/reports:/app/reports playwright-tests"
            }
        }

        stage('Archive Report') {
            steps {
                archiveArtifacts artifacts: 'reports/report.html', allowEmptyArchive: true
            }
        }
    }
}
