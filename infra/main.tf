terraform {
  required_providers {
    ncloud = {
      source = "NaverCloudPlatform/ncloud"
    }
  }
  required_version = ">= 0.13"
}

provider "ncloud" {
  access_key  = var.access_key
  secret_key  = var.secret_key
  region      = "KR"
  site        = "PUBLIC"
  support_vpc = true
}

locals {
  env               = "k8s"
  server_image_code = "SW.VSVR.OS.LNX64.UBNTU.SVR2004.B050"
}

data "ncloud_vpc" "vpc" {
  id = module.network.vpc_id
}

resource "ncloud_subnet" "subnet" {
  vpc_no         = module.network.vpc_id
  subnet         = cidrsubnet(data.ncloud_vpc.vpc.ipv4_cidr_block, 8, 5)
  zone           = "KR-1"
  network_acl_no = data.ncloud_vpc.vpc.default_network_acl_no
  subnet_type    = "PUBLIC"
  name           = "k8s-subnet-01"
  usage_type     = "GEN"
}

resource "ncloud_subnet" "subnet_lb" {
  vpc_no         = data.ncloud_vpc.vpc.id
  subnet         = cidrsubnet(data.ncloud_vpc.vpc.ipv4_cidr_block, 8, 6)
  zone           = "KR-1"
  network_acl_no = data.ncloud_vpc.vpc.default_network_acl_no
  subnet_type    = "PRIVATE"
  name           = "k8s-subnet-lb"
  usage_type     = "LOADB"
}


data "ncloud_nks_versions" "version" {
  filter {
    name   = "value"
    values = ["1.25.8"]
    regex  = true
  }
}

resource "ncloud_login_key" "loginkey" {
  key_name = "k8s-login-key"
}


resource "ncloud_nks_cluster" "cluster" {
  cluster_type         = "SVR.VNKS.STAND.C002.M008.NET.SSD.B050.G002"
  k8s_version          = data.ncloud_nks_versions.version.versions.0.value
  login_key_name       = ncloud_login_key.loginkey.key_name
  name                 = "ncp-k8s-cluster"
  lb_private_subnet_no = ncloud_subnet.subnet_lb.id
  kube_network_plugin  = "cilium"
  subnet_no_list       = [ncloud_subnet.subnet.id]
  public_network       = true
  vpc_no               = data.ncloud_vpc.vpc.id
  zone                 = "KR-1"
  log {
    audit = true
  }
}


data "ncloud_server_image" "image" {
  filter {
    name   = "product_name"
    values = ["ubuntu-20.04"]
  }
}

data "ncloud_server_product" "product" {
  server_image_product_code = data.ncloud_server_image.image.product_code

  filter {
    name   = "product_type"
    values = ["STAND"]
  }

  filter {
    name   = "cpu_count"
    values = [2]
  }

  filter {
    name   = "memory_size"
    values = ["8GB"]
  }

  filter {
    name   = "product_code"
    values = ["SSD"]
    regex  = true
  }
}

resource "ncloud_nks_node_pool" "node_pool" {
  cluster_uuid   = ncloud_nks_cluster.cluster.uuid
  node_pool_name = "k8s-node-pool"
  node_count     = 1
  product_code   = data.ncloud_server_product.product.product_code

  autoscale {
    enabled = true
    min     = 1
    max     = 2
  }

  lifecycle {
    ignore_changes = [node_count, subnet_no_list]
  }
}
