def call(service, dockerRepoName, imageName) {

  pipeline {
    agent any

    parameters {
      booleanParam(defaultValue: false, name: "DEPLOY", description: "Deploy the App")
    }

    stages {

      stage("Lint") {
        steps {
          sh "pylint --fail-under=5 --indent-string='  ' ${service}/*.py"
        }
      }

      stage("Security Scan") {
        steps {
          sh """
          python3 -m venv .venv
          chmod -R 755 .venv
          . .venv/bin/activate
          pip install bandit
          bandit -r ${service}
          """
        }
      }

      stage("Package") {
        steps {
          withCredentials([string(credentialsId: "DockerHub", variable: "TOKEN")]) {
            sh """
            cd ${service}
            docker login -u azuda -p $TOKEN docker.io
            docker build -t ${dockerRepoName}:latest --tag azuda/${dockerRepoName}:${imageName} .
            docker push azuda/${dockerRepoName}:${imageName}
            """
          }
        }
      }

      stage("Deploy") {
        when {
          expression { params.DEPLOY }
        }
        steps {
          sh "docker stop ${dockerRepoName} || true && docker rm ${dockerRepoName} || true"
          sh "docker run -d -p ${portNum}:${portNum} --name ${dockerRepoName} ${dockerRepoName}:latest"
        }
      }

    }
  }
}



