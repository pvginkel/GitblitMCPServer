import org.jenkinsci.plugins.pipeline.modeldefinition.Utils

library('JenkinsPipelineUtils') _

podTemplate(inheritFrom: 'jenkins-agent kaniko') {
    node(POD_LABEL) {
        stage('Cloning repo') {
            git branch: 'main',
                credentialsId: '5f6fbd66-b41c-405f-b107-85ba6fd97f10',
                url: 'https://github.com/pvginkel/GitblitMCPServer.git'
        }

        stage("Building GitblitMCPServer") {
            container('kaniko') {
                helmCharts.kaniko([
                    "registry:5000/gitblit-mcp-server:${currentBuild.number}",
                    "registry:5000/gitblit-mcp-server:latest"
                ])
            }
        }

        stage('Deploy Helm charts') {
            build job: 'HelmCharts', wait: false
        }
    }
}
