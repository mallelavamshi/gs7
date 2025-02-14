pipeline {
    agent any

    environment {
        IMAGE_NAME = "streamlit_app"
        CONTAINER_NAME = "streamlit_container"
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
                    sh 'docker build -t ${IMAGE_NAME} .'
                }
            }
        }

        stage('Run Container') {
            steps {
                script {
                    // Stop and remove any existing container
                    sh 'docker stop ${CONTAINER_NAME} || true'
                    sh 'docker rm ${CONTAINER_NAME} || true'
                    
                    // Run the container
                    sh 'docker run -d -p 8501:8501 --name ${CONTAINER_NAME} ${IMAGE_NAME}'
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
