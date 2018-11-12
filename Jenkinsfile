node {
    def app
    stage('Clone repository') {
        checkout scm
    }
    stage('Tag with Commit Hash') {
		  sh 'git rev-parse HEAD > ./commit.sha && pwd && cat ./commit.sha'
    }

    stage('Build image') {
        app = docker.build("danielsaska/datlas","-f ./Dockerfile .")
    }

    stage('Push image') {
        docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
            app.push("${env.BUILD_NUMBER}")
            app.push("latest")
        }
    }
}
