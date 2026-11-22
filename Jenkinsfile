pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        COMPOSE_PROJECT_NAME = 'pulsewatch'
        // "Secret file" credential (ID: pulsewatch-env) holding the contents of .env.
        // Jenkins exposes it as a temp file path, so secrets never enter the repo or the logs.
        ENV_FILE = credentials('pulsewatch-env')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint & Test') {
            steps {
                sh '''
                    docker build -f backend/Dockerfile -t pulsewatch-test .
                    docker run --rm --entrypoint sh pulsewatch-test \
                        -c "flake8 --max-line-length=120 . && pytest -q"
                '''
            }
        }

        stage('Build') {
            steps {
                sh 'docker compose --env-file "$ENV_FILE" build'
            }
        }

        stage('Deploy') {
            steps {
                // No "-v": the pgdata volume (users + metrics) survives redeploys.
                sh '''
                    docker compose --env-file "$ENV_FILE" down || true
                    docker compose --env-file "$ENV_FILE" up -d
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    sleep 10
                    for i in 1 2 3 4 5 6; do
                        curl -f http://localhost/api/health && exit 0
                        echo "Not ready yet (attempt $i), retrying in 5s..."
                        sleep 5
                    done
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'PulseWatch deployed and healthy: http://<EC2-PUBLIC-IP>'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above (docker compose logs on the server may help).'
        }
        always {
            sh 'docker image prune -f || true'
        }
    }
}
