data "aws_caller_identity" "current" {}

data "github_repository" "coax" {
  full_name = "lowobservable/coax"
}

locals {
  # Until there is a aws_iam_openid_connect_provider data source...
  github_openid_connect_provider_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
}

resource "aws_ecr_repository" "icecube2" {
  name                 = "icecube2"
  image_tag_mutability = "MUTABLE"

  tags = {
    project = "coax"
  }
}

resource "aws_s3_bucket" "cache" {
  bucket_prefix = "coax"

  tags = {
    project     = "coax"
    description = "Cached bitstreams for https://github.com/lowobservable/coax"
  }
}

resource "aws_s3_bucket_acl" "cache" {
  bucket = aws_s3_bucket.cache.id
  acl    = "private"
}

resource "aws_s3_bucket_policy" "cache" {
  bucket = aws_s3_bucket.cache.id
  policy = data.aws_iam_policy_document.cache_access.json
}

data "aws_iam_policy_document" "cache_access" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.cache.arn]

    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.github_actions.arn]
    }
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.cache.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.github_actions.arn]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "github-actions-coax"
  description        = "GitHub Actions role for https://github.com/lowobservable/coax"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = {
    project = "coax"
  }
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.github_openid_connect_provider_arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:lowobservable/coax:*"]
    }
  }
}

resource "aws_iam_role_policy" "github_actions_access" {
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_access.json
}

data "aws_iam_policy_document" "github_actions_access" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability"
    ]
    resources = [
      aws_ecr_repository.icecube2.arn
    ]
  }
}

resource "github_actions_secret" "aws_iam_role" {
  repository      = data.github_repository.coax.name
  secret_name     = "AWS_IAM_ROLE"
  plaintext_value = aws_iam_role.github_actions.arn
}

resource "github_actions_variable" "bitstream_cache_bucket" {
  repository    = data.github_repository.coax.name
  variable_name = "BITSTREAM_CACHE_BUCKET"
  value         = aws_s3_bucket.cache.id
}
