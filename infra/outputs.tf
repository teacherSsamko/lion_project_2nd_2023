output "k8s_ip" {
  value = ncloud_public_ip.k8s.public_ip
}

output "cluster_uuid" {
  value = ncloud_nks_cluster.cluster.uuid
}
