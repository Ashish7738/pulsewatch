pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
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
                sh '''
                    set -a; . "$ENV_FILE"; set +a
                    docker compose -f docker-compose.web.yml --env-file "$ENV_FILE" build
                    DOCKER_HOST=ssh://ubuntu@$APP_HOST \
                        docker compose -f docker-compose.app.yml --env-file "$ENV_FILE" build
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -a; . "$ENV_FILE"; set +a

                    DOCKER_HOST=ssh://ubuntu@$DB_HOST \
                        docker compose -f docker-compose.db.yml --env-file "$ENV_FILE" up -d --wait

                    DOCKER_HOST=ssh://ubuntu@$APP_HOST \
                        docker compose -f docker-compose.app.yml --env-file "$ENV_FILE" down || true
                    DOCKER_HOST=ssh://ubuntu@$APP_HOST \
                        docker compose -f docker-compose.app.yml --env-file "$ENV_FILE" up -d --wait

                    docker compose -f docker-compose.web.yml --env-file "$ENV_FILE" down || true
                    docker compose -f docker-compose.web.yml --env-file "$ENV_FILE" up -d
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    set -a; . "$ENV_FILE"; set +a
                    sleep 10
                    for i in 1 2 3 4 5 6; do
                        curl -f http://$APP_HOST:5000/api/health \
                          && curl -f http://localhost/api/health && exit 0
                        echo "Not ready yet (attempt $i), retrying in 5s..."
                        sleep 5
                    done
                    exit 1
                '''
            }
        }
    }

    post {
        success { echo 'PulseWatch deployed on 3 servers' }
        failure { echo 'Pipeline failed. Check the stage logs above.' }
        always  { sh 'docker image prune -f || true' }
    }
}