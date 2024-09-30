pipeline {
    agent any
    environment {
        DOCKER_REGISTRY = 'trieuvu'
        IMAGE_NAME = 'recommend'
        IMAGE_TAG = 'new'
    }
    stages {
        stage('Clone') {
            steps {
                git branch: 'protect/deploy', url: 'https://github.com/vutrieuIT/recommend_system.git'
            }
        }
        stage('Check Branch') {
            steps {
                script {
                    if (env.GIT_BRANCH != 'origin/protect/deploy') {
                        echo "Not on protect/deploy branch, exiting pipeline. Branch is ${env.GIT_BRANCH}"
                        error("Not on protect/deploy branch, exiting pipeline.")
                    }
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                withDockerRegistry(credentialsId: 'docker-hub', url: 'https://index.docker.io/v1/') {
                    sh 'docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG .'
                    sh 'docker push $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG'
                }
            }
        }
    }
    post {
        success {
            mail bcc: '', body: 'build recommend done', cc: '', from: '', replyTo: '', subject: 'jenkins build', to: 'vutrieu2002@gmail.com'
        }
        failure {
            mail bcc: '', body: 'build recommend fail', cc: '', from: '', replyTo: '', subject: 'jenkins build', to: 'vutrieu2002@gmail.com'
        }
    }
}
