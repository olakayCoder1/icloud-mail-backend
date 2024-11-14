provider "aws" {
  region = "us-east-1"  # specify your region
}

# Variable for client-specific information
variable "clients" {
  type = map(object({
    instance_type  = string
    ami            = string
    security_group = string
    key_name       = string
    client_name    = string
  }))
  default = {
    "client_a" = {
      instance_type  = "t2.micro"
      ami            = "ami-0c55b159cbfafe1f0"  # Example AMI for client A
      security_group = "sg-12345678"
      key_name       = "client_a_key"
      client_name    = "Client A"
    },
    "client_b" = {
      instance_type  = "t2.micro"
      ami            = "ami-0c55b159cbfafe1f0"  # Example AMI for client B
      security_group = "sg-87654321"
      key_name       = "client_b_key"
      client_name    = "Client B"
    }
  }
}

# Clone Server Configuration for Each Client
resource "aws_instance" "client_servers" {
  for_each = var.clients

  ami           = each.value.ami
  instance_type = each.value.instance_type
  key_name      = each.value.key_name
  security_groups = [each.value.security_group]

  tags = {
    Name = each.value.client_name
  }
}

# Output the public IPs for each client
output "client_servers_ips" {
  value = { for client, server in aws_instance.client_servers : client => server.public_ip }
}
