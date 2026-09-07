pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    APP_ENV = 'development'
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
  }

  stages {
    stage('Checkout') {
      steps {
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
          '''
        }
      }
    }

    stage('Instalar dependencias') {
      steps {
        dir('apps/api') {
          sh '''
            set -eu
            . .venv/bin/activate
            pip install -r requirements-dev.txt
          '''
        }
      }
    }

    stage('Ejecutar pruebas') {
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

    stage('Validar FastAPI') {
      steps {
        dir('apps/api') {
          sh '''
            set -eu
            . .venv/bin/activate
            python -c "from app.main import app; print('app:', app.title)"
          '''
        }
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
