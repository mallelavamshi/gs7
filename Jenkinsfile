pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('ANTHROPIC_API_KEY')
        SEARCH_API_KEY = credentials('SEARCH_API_KEY')
        SMTP_SERVER = credentials('SMTP_SERVER')
        SMTP_PORT = credentials('SMTP_PORT')
        SMTP_USER = credentials('SMTP_USER')
        SMTP_PASSWORD = credentials('SMTP_PASSWORD')
    }

    stages {
        stage('Clone Repository') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Directories') {
            steps {
                sh '''
                sudo mkdir -p /var/lib/estateai/reports
                sudo chmod -R 777 /var/lib/estateai
                sudo chown -R 1000:1000 /var/lib/estateai
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh '''
                    docker build --build-arg ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
                                 --build-arg SEARCH_API_KEY=${SEARCH_API_KEY} \
                                 --build-arg SMTP_SERVER=${SMTP_SERVER} \
                                 --build-arg SMTP_PORT=${SMTP_PORT} \
                                 --build-arg SMTP_USER=${SMTP_USER} \
                                 --build-arg SMTP_PASSWORD=${SMTP_PASSWORD} \
                                 -t streamlit_app .
                    '''
                }
            }
        }

        stage('Run Container') {
            steps {
                script {
                    sh '''
                    docker stop streamlit_container || true
                    docker rm streamlit_container || true
                    
                    docker run -d -p 8501:8501 --name streamlit_container \
                        -v /var/lib/estateai:/var/lib/estateai \
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