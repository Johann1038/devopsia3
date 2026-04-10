// ════════════════════════════════════════════════════════════════════════════
// Luxury Car Resale Showroom — Jenkins CI/CD Pipeline
// Stages: Checkout → Build → Test → Push → Deploy
//
// Jenkins credentials required:
//   DOCKERHUB_CREDS  → Username/Password credential (Docker Hub)
//   KUBECONFIG_FILE  → Secret file credential (kubeconfig)
// ════════════════════════════════════════════════════════════════════════════

pipeline {
    agent any

    environment {
        // ── Docker Hub ─────────────────────────────────────────────────────
        DOCKERHUB_USER  = "johannkarunya28"
        IMAGE_NAME      = "${DOCKERHUB_USER}/prestige-motors"
        IMAGE_TAG       = "${env.BUILD_NUMBER}"
        IMAGE_LATEST    = "${IMAGE_NAME}:latest"
        IMAGE_VERSIONED = "${IMAGE_NAME}:${IMAGE_TAG}"

        // ── Kubernetes ─────────────────────────────────────────────────────
        K8S_NAMESPACE  = "luxury-cars"
        K8S_DEPLOYMENT = "prestige-motors"

        // ── PayPal Microservice (Render) ───────────────────────────────────
        PAYPAL_SERVICE_URL = "https://payment-w1qr.onrender.com"
        PAYMENT_API_KEY    = credentials('PAYMENT_API_KEY')   // Jenkins secret text credential
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {

        // ── Stage 1: Checkout ─────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "========== STAGE 1: Checkout Source Code =========="
                checkout scm
                sh '''
                    echo "Branch  : ${GIT_BRANCH}"
                    echo "Commit  : ${GIT_COMMIT}"
                    echo "Build # : ${BUILD_NUMBER}"
                    ls -la
                '''
            }
        }

        // ── Stage 2: Build Docker Image ───────────────────────────────────
        stage('Build') {
            steps {
                echo "========== STAGE 2: Build Docker Image =========="
                sh '''
                    echo "Building image: ${IMAGE_VERSIONED}"
                    docker build \
                        --target runtime \
                        --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                        --build-arg VCS_REF=${GIT_COMMIT} \
                        -t ${IMAGE_VERSIONED} \
                        -t ${IMAGE_LATEST} \
                        .
                    echo "Image size:"
                    docker images ${IMAGE_NAME} --format "{{.Repository}}:{{.Tag}} {{.Size}}"
                '''
            }
        }

        // ── Stage 3: Test (pytest inside the built image) ─────────────────
        stage('Test') {
            steps {
                echo "========== STAGE 3: Run Pytest Unit Tests =========="
                sh '''
                    docker run --rm \
                        --name prestige-test-${BUILD_NUMBER} \
                        --entrypoint "" \
                        -e FLASK_ENV=testing \
                        ${IMAGE_VERSIONED} \
                        /opt/venv/bin/pytest backend/tests/ -v --tb=short --junitxml=/tmp/test-results.xml

                    # Extract test results from container layer
                    CONTAINER_ID=$(docker create ${IMAGE_VERSIONED})
                    docker cp ${CONTAINER_ID}:/tmp/test-results.xml ./test-results.xml || true
                    docker rm ${CONTAINER_ID} || true
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        // ── Stage 4: Push to Docker Hub ───────────────────────────────────
        stage('Push') {
            steps {
                echo "========== STAGE 4: Push Image to Docker Hub =========="
                withCredentials([usernamePassword(
                    credentialsId: 'DOCKERHUB_CREDS',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh '''
                        echo "${DH_PASS}" | docker login -u "${DH_USER}" --password-stdin
                        docker push ${IMAGE_VERSIONED}
                        docker push ${IMAGE_LATEST}
                        echo "Pushed ${IMAGE_VERSIONED} and ${IMAGE_LATEST}"
                        docker logout
                    '''
                }
            }
        }

        // ── Stage 5: Deploy to Kubernetes ─────────────────────────────────
        stage('Deploy') {
            steps {
                echo "========== STAGE 5: Deploy to Kubernetes =========="
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh '''
                        export KUBECONFIG=${KUBECONFIG}

                        # Apply all manifests (idempotent)
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/deployment.yaml
                        kubectl apply -f k8s/service.yaml
                        kubectl apply -f k8s/hpa.yaml

                        # Roll out the new image version
                        kubectl set image deployment/${K8S_DEPLOYMENT} \
                            prestige-motors=${IMAGE_VERSIONED} \
                            -n ${K8S_NAMESPACE}

                        # Inject PayPal URL
                        kubectl set env deployment/${K8S_DEPLOYMENT} \
                            PAYPAL_SERVICE_URL=${PAYPAL_SERVICE_URL} \
                            -n ${K8S_NAMESPACE}

                        # Wait for the rolling update to finish (max 3 min)
                        kubectl rollout status deployment/${K8S_DEPLOYMENT} \
                            -n ${K8S_NAMESPACE} \
                            --timeout=180s

                        echo "--- Deployment complete ---"
                        kubectl get pods -n ${K8S_NAMESPACE} -o wide
                        kubectl get svc  -n ${K8S_NAMESPACE}
                        kubectl get hpa  -n ${K8S_NAMESPACE}
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCEEDED — Image: ${IMAGE_VERSIONED}"
        }
        failure {
            echo "Pipeline FAILED — Stage: ${currentBuild.result}"
        }
        always {
            sh 'docker image prune -f || true'
            cleanWs()
        }
    }
}
