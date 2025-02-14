pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('ANTHROPIC_API_KEY')
        SEARCH_API_KEY = credentials('SEARCH_API_KEY')
        SMTP_SERVER = credentials('smtp_server')
        SMTP_PORT = credentials('smtp_port')
        SMTP_USER = credentials('smtp_user')
        SMTP_PASSWORD = credentials('smtp_password')
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
