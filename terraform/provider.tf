# Fase 3 — AWS (cuenta de la práctica). Región fija us-east-1.
# NO apunta a la EC2 de Fase 1–2 (devops-hq-jenkins / 3.91.227.140).

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
