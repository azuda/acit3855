def call(dockerRepoName, imageName) {

  pipeline {
    agent any

    stages {

      stage("Lint") {
        steps {
          sh "pylint --fail-under=5 *.py"
        }
      }

      stage("Security Scan") {
        steps {
          sh "pip install bandit"
          sh "bandit -r ."
        }
      }

      stage("Package") {
        steps {
          withCredentials([string(credentialsId: "DockerHub", variable: "TOKEN")]) {
            sh "docker login -u azuda -p $TOKEN docker.io"
            sh "docker build -t ${dockerRepoName}:latest --tag azuda/${dockerRepoName}:${imageName} ."
            sh "docker push azuda/${dockerRepoName}:${imageName}"
          }
        }
      }

      stage("Deploy") {
        steps {
          withCredentials([sshUserPrivateKey(credentialsId: "sshKey", keyFileVariable: "SSH_KEY")]) {
            sh "ssh -i $SSH_KEY azureuser@172.210.192.73 'docker pull azuda/${dockerRepoName}:${imageName} && docker-compose up -d'"
          }
        }
      }

    }
  }
}



