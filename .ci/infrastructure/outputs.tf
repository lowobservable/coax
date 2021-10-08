output "bitstream_cache_bucket" {
  value       = aws_s3_bucket.cache.id
  description = "Use for BITSTREAM_CACHE_BUCKET environment variable"
}
