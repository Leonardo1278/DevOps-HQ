# Servidor NUEVO para Fase 3 (IaC).
# No gestiona i-0413353cd5ac45395 ni el SG devops-hq-jenkins.
#
# Antes de plan/apply, reemplaza:
#   key_name  — par de claves creado en EC2 (paso 7 del PDF)
#   subnet_id — VPC → Subnets → copia el ID de una subred pública us-east-1
#
# Cloud Shell (en la carpeta terraform):
#   terraform init
#   terraform plan -out=tfplan
#   terraform apply "tfplan"

locals {
  key_name      = "devops-hq-fase3"
  subnet_id     = "subnet-REEMPLAZA"
  instance_type = "t3.small"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_subnet" "selected" {
  id = local.subnet_id
}

resource "aws_security_group" "fase3" {
  name        = "devops-hq-fase3"
  description = "Fase 3 Terraform. Independiente del SG de Fase 1-2."
  vpc_id      = data.aws_subnet.selected.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP (rubrica)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS (rubrica)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jenkins"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App FastAPI /health"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "devops-hq-fase3"
    Project     = "DevOps-HQ"
    Environment = "academic"
    CreatedBy   = "Terraform"
  }
}

resource "aws_instance" "fase3" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = local.instance_type
  subnet_id                   = local.subnet_id
  key_name                    = local.key_name
  vpc_security_group_ids      = [aws_security_group.fase3.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -eux
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y docker.io git curl
    systemctl enable --now docker
    usermod -aG docker ubuntu
    git clone --depth 1 https://github.com/Leonardo1278/DevOps-HQ.git /opt/devops-hq
    cd /opt/devops-hq
    docker build -t devops-hq-base:1.0 -f Dockerfile.base .
    docker build -t devops-hq-api:1.0 -f Dockerfile .
    docker rm -f devops-hq-api || true
    docker run -d --name devops-hq-api --restart unless-stopped -p 8000:8000 devops-hq-api:1.0
  EOF

  tags = {
    Name        = "devops-hq-fase3"
    Project     = "DevOps-HQ"
    Environment = "academic"
    CreatedBy   = "Terraform"
  }
}

output "public_ip" {
  value = aws_instance.fase3.public_ip
}

output "ssh" {
  value = "ssh -i devops-hq-fase3.pem ubuntu@${aws_instance.fase3.public_ip}"
}

output "health" {
  value = "http://${aws_instance.fase3.public_ip}:8000/health"
}

output "aviso" {
  value = "Esta instancia NO es la de Fase 1-2. No ejecutar destroy sobre recursos viejos: este state solo crea devops-hq-fase3."
}
