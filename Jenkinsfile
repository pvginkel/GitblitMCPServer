// Builds the gitblit-mcp-server image and pins it into GitSyncDeploy, which Argo CD syncs to prd.
//
// Controller config:
//   - Job: Gitblit/GitblitMCPServer
//   - SCM: pvginkel/GitblitMCPServer, branch main
//   - Script Path: Jenkinsfile

library identifier: 'JenkinsPipelineUtils', changelog: false

pipeline {
    agent {
        kubernetes {
            inheritFrom 'jenkins-agent kaniko'
            yamlMergeStrategy merge()
            yaml podYaml(templates: ['k8s'])
        }
    }

    options {
        disableConcurrentBuilds(abortPrevious: true)
        skipDefaultCheckout()
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build gitblit-mcp-server image') {
            steps {
                container('kaniko') {
                    script {
                        helmCharts.kaniko2(destinations: [
                            "registry:5000/gitblit-mcp-server:${currentBuild.number}",
                            'registry:5000/gitblit-mcp-server:latest',
                        ])
                    }
                }
            }
        }

        stage('Write image pins') {
            steps {
                container('k8s') {
                    script {
                        cicd.writeVersionPins(repo: 'pvginkel/GitSyncDeploy', pins: [
                            'config/prd/values.yaml': ['images.gitblitMCPServer': ":${currentBuild.number}"],
                        ])
                    }
                }
            }
        }
    }
}
