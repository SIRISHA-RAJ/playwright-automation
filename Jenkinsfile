pipeline {
    agent any

    stages {

        stage('Clone Code') {
            steps {
               git branch: 'main', url: 'https://github.com/SIRISHA-RAJ/playwright-automation.git'           }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t playwright-tests .'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'docker run -v $PWD/reports:/app/reports playwright-tests pytest -v --html=reports/report.html'
            }
        }

        stage('Archive Report') {
            steps {
                archiveArtifacts artifacts: 'reports/report.html'
            }
        }
    }
}
