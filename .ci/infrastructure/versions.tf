terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.14.0"
    }

    github = {
      source  = "integrations/github"
      version = "5.34.0"
    }
  }
}
