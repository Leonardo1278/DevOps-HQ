pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    APP_ENV = 'development'
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    IMAGE_BASE = 'devops-hq-base:1.0'
    IMAGE_APP = 'devops-hq-api:1.0'
    CONTAINER_APP = 'devops-hq-api'
  }

  stages {
    stage('Checkout') {
      steps {
        echo 'Obteniendo el código del repositorio...'
        checkout scm
      }
    }

    stage('Verificar Python') {
      steps {
        sh '''
          set -eu
          if command -v python3.11 >/dev/null 2>&1; then
            PYTHON=python3.11
          elif command -v python3 >/dev/null 2>&1; then
            PYTHON=python3
          else
            echo "ERROR: no hay python3 ni python3.11 en PATH"
            exit 1
          fi
          echo "Usando: $PYTHON"
          $PYTHON --version
        '''
      }
    }

    stage('Verificar Docker') {
      steps {
        sh 'docker --version'
        sh 'docker info >/dev/null'
      }
    }

    stage('Preparar entorno') {
      steps {
        dir('apps/api') {
          sh '''
            set -eu
            if command -v python3.11 >/dev/null 2>&1; then
              PYTHON=python3.11
            else
              PYTHON=python3
            fi
            $PYTHON -m venv .venv
            . .venv/bin/activate
            python --version
            pip install --upgrade pip
            pip install -r requirements-dev.txt
          '''
        }
      }
    }

    stage('Ejecutar Pruebas Python') {
      steps {
        dir('apps/api') {
          sh '''
            set -eu
            . .venv/bin/activate
            pytest tests/test_health.py -q
          '''
        }
      }
    }

    stage('Construir Imagen Base') {
      steps {
        sh 'docker build -t "$IMAGE_BASE" -f Dockerfile.base .'
      }
    }

    stage('Construir Imagen Aplicacion') {
      steps {
        sh 'docker build -t "$IMAGE_APP" -f Dockerfile .'
      }
    }

    stage('Ejecutar Pruebas en Docker') {
      steps {
        sh 'docker run --rm "$IMAGE_APP" pytest tests/test_health.py -q'
      }
    }

    stage('Ejecutar Contenedor') {
      steps {
        sh '''
          set -eu
          docker rm -f "$CONTAINER_APP" >/dev/null 2>&1 || true
          docker run -d --name "$CONTAINER_APP" -p 8000:8000 -e APP_ENV=development "$IMAGE_APP"
          i=0
          while [ "$i" -lt 20 ]; do
            if curl -fsS http://127.0.0.1:8000/health | grep -q '"status":"ok"'; then
              echo "Health OK"
              curl -fsS http://127.0.0.1:8000/health
              echo
              exit 0
            fi
            i=$((i + 1))
            sleep 2
          done
          echo "ERROR: /health no respondió a tiempo"
          docker logs "$CONTAINER_APP" || true
          exit 1
        '''
      }
    }

    stage('Finalizado') {
      steps {
        echo 'Pipeline Fase 2: Python, imagen base, imagen app y contenedor OK.'
      }
    }
  }

  post {
    success {
      echo 'Finished: SUCCESS'
    }
    failure {
      echo 'Finished: FAILURE'
    }
    always {
      dir('apps/api') {
        sh 'rm -rf .venv || true'
      }
    }
  }
}
