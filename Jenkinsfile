pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('ANTHROPIC_API_KEY')
        SEARCH_API_KEY = credentials('SEARCH_API_KEY')
        SMTP_SERVER = credentials('SMTP_SERVER')
        SMTP_PORT = credentials('SMTP_PORT')   // Check this line
        SMTP_USER = credentials('SMTP_USER')
        SMTP_PASSWORD = credentials('SMTP_PASSWORD')
    }

    stages {
        stage('Clone Repository') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh 'docker build -t streamlit_app .'
                }
            }
        }

        stage('Run Container') {
            steps {
                script {
                    sh 'docker stop streamlit_container || true'
                    sh 'docker rm streamlit_container || true'
                    
                    sh '''
                    docker run -d -p 8501:8501 --name streamlit_container \
                        -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
                        -e SEARCH_API_KEY=${SEARCH_API_KEY} \
                        -e SMTP_SERVER=${SMTP_SERVER} \
                        -e SMTP_PORT=${SMTP_PORT} \
                        -e SMTP_USER=${SMTP_USER} \
                        -e SMTP_PASSWORD=${SMTP_PASSWORD} \
                        streamlit_app
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Deployment successful!"
        }
        failure {
            echo "Deployment failed!"
        }
    }
}
