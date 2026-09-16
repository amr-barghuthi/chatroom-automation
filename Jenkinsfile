pipeline {
    agent {
        docker {
            image 'mcr.microsoft.com/playwright:v1.42.1-jammy'
            args '-u root'
        }
    }

    options {
        timeout(time: 5, unit: 'MINUTES') // Ensures execution stays strictly under 5 mins
        ansiColor('xterm')
    }

    environment {
        CI = 'true'
        BASE_URL = 'https://dev.connect-plus.app/en-US/login'
        API_URL = 'https://dev-api.connect-plus.app'
        TEST_USER_EMAIL = credentials('CHATROOM_DEPLOY_USER')
        TEST_USER_PASSWORD = credentials('CHATROOM_DEPLOY_PASSWORD')
        INTEGRATION_API_TOKEN = credentials('CHATROOM_INTEGRATION_TOKEN')
    }

    stages {
        stage('Checkout & Setup') {
            steps {
                echo '=== Setting up environment for Production Deployment Smoke Test ==='
                sh 'node -v'
                sh 'npm -v'
                sh 'npm ci || npm install'
            }
        }

        stage('Run Deployment Smoke Tests (2-5 Min)') {
            steps {
                echo '=== Running Playwright APIRequestContext Deployment Automation ==='
                sh 'npx playwright test --config=playwright.config.ts'
            }
        }
    }

    post {
        always {
            echo '=== Archiving Test Results ==='
            // Publish JUnit report for Jenkins test trends UI
            junit allowEmptyResults: true, testResults: 'test-results/results.xml'
            
            // Archive HTML report artifacts
            archiveArtifacts artifacts: 'playwright-report/**', allowEmptyArchive: true
        }
        success {
            echo '✅ Deployment Automation Passed! Production deployment verified successfully.'
        }
        failure {
            echo '❌ Deployment Automation Failed! Alerting team (Raghad, Amro, Firas).'
        }
    }
}
