"""
Cloud service facts database - pre-populated key information about common cloud services.
This provides baseline information that changes infrequently to reduce tool calls.
"""

from typing import Dict, Any, List
from dr_agent.utils.tool_cache import get_tool_cache


def initialize_cloud_facts():
    """Initialize the cache with common cloud service facts"""
    cache = get_tool_cache()

    # AWS Service Facts
    aws_facts = {
        "regions": {
            "us-east-1": "N. Virginia (US East)",
            "us-east-2": "Ohio (US East)",
            "us-west-1": "N. California (US West)",
            "us-west-2": "Oregon (US West)",
            "eu-west-1": "Ireland (Europe)",
            "eu-west-2": "London (Europe)",
            "eu-central-1": "Frankfurt (Europe)",
            "ap-southeast-1": "Singapore (Asia Pacific)",
            "ap-southeast-2": "Sydney (Asia Pacific)",
            "ap-northeast-1": "Tokyo (Asia Pacific)"
        },
        "instance_families": {
            "t3": "General purpose, burstable CPU",
            "t4g": "General purpose, burstable, ARM-based",
            "m5": "General purpose, Intel Xeon",
            "m6g": "General purpose, ARM-based",
            "c5": "Compute optimized",
            "c6g": "Compute optimized, ARM-based",
            "r5": "Memory optimized",
            "r6g": "Memory optimized, ARM-based"
        },
        "database_engines": {
            "postgresql": "Supported versions: 12, 13, 14, 15, 16",
            "mysql": "Supported versions: 5.7, 8.0",
            "mariadb": "Supported versions: 10.6, 10.11",
            "sqlserver": "Supported versions: 2017, 2019, 2022"
        },
        "rds_storage": {
            "gp2": "General Purpose SSD (baseline 3 IOPS/GB, max 3,000 IOPS)",
            "gp3": "General Purpose SSD v3 (baseline 3,000 IOPS, max 16,000 IOPS)",
            "io1": "Provisioned IOPS SSD (1-256,000 IOPS)",
            "magnetic": "Legacy magnetic storage (deprecated)"
        },
        "pricing_models": {
            "on_demand": "Pay per hour/second, no commitment",
            "reserved": "1 or 3 year term, 30-40% discount",
            "savings_plan": "Flexible commitment, 40-66% discount",
            "spot": "Up to 90% discount, can be reclaimed"
        }
    }

    # GCP Service Facts
    gcp_facts = {
        "regions": {
            "us-east1": "South Carolina (US East)",
            "us-east4": "Northern Virginia (US East)",
            "us-west1": "Oregon (US West)",
            "us-west2": "Los Angeles (US West)",
            "us-central1": "Iowa (US Central)",
            "europe-west1": "Belgium (Europe)",
            "europe-west4": "Netherlands (Europe)",
            "asia-southeast1": "Singapore (Asia)",
            "asia-northeast1": "Taiwan (Asia)",
            "asia-northeast3": "Seoul (Asia)"
        },
        "machine_types": {
            "e2": "General purpose, AMD/Intel",
            "e2-medium": "General purpose, 2 vCPUs, 4GB RAM (baseline)",
            "n2": "General purpose, Intel Xeon",
            "n2-standard": "General purpose, balanced CPU/memory",
            "n2-highmem": "High memory optimized",
            "n2-highcpu": "High CPU optimized",
            "c2": "Compute optimized, Intel Xeon",
            "t2a": "General purpose, AMD Milan"
        },
        "cloud_sql_engines": {
            "postgresql": "Supported versions: 12, 13, 14, 15",
            "mysql": "Supported versions: 5.7, 8.0",
            "sqlserver": "Supported versions: 2017, 2019, 2022 Web/Standard/Enterprise"
        }
    }

    # Azure Service Facts
    azure_facts = {
        "regions": {
            "eastus": "East US",
            "westus": "West US",
            "westus2": "West US 2",
            "centralus": "Central US",
            "westeurope": "West Europe",
            "northeurope": "North Europe",
            "southeastasia": "Southeast Asia",
            "eastasia": "East Asia"
        },
        "vm_series": {
            "B-series": "Burstable, low cost",
            "Dv5/Dasv5": "General purpose, Intel",
            "Ev5/Easv5": "Memory optimized",
            "Fv5/Fasv5": "Compute optimized",
            "Lsv3/Lsv2": "Storage optimized"
        },
        "database_tiers": {
            "basic": "Single core, up to 2GB storage",
            "standard": "High availability, up to 1TB storage",
            "premium": "High performance, up to 4TB storage"
        }
    }

    # Redis/Memcached Facts
    redis_facts = {
        "common_configs": {
            "cache.t3.micro": "1 vCPU, 0.5GB RAM (AWS)",
            "cache.t3.small": "1 vCPU, 1.3GB RAM (AWS)",
            "cache.t3.medium": "1 vCPU, 2.8GB RAM (AWS)",
            "cache.m5.large": "2 vCPU, 12GB RAM (AWS)"
        },
        "multi_az": {
            "description": "Automatic failover across AZs",
            "cost_increase": "2x single-AZ pricing",
            "recommended_for": "Production workloads"
        },
        "cluster_mode": {
            "max_shards": "500",
            "replicas_per_shard": "5",
            "use_case": "Scaling reads and writes"
        }
    }

    # Kubernetes Facts
    kubernetes_facts = {
        "node_pools": {
            "aws": "EC2 instances with Kubernetes optimization",
            "gcp": "Google Kubernetes Engine optimized VMs",
            "azure": "AKS-optimized VM sizes"
        },
        "pricing_components": [
            "Master/control plane (often free)",
            "Worker nodes (VM costs)",
            "Load balancer costs",
            "Storage costs",
            "Network egress costs"
        ],
        "managed_services": {
            "aws": "EKS - $0.10/hour per cluster",
            "gcp": "GKE - Free control plane",
            "azure": "AKS - Free control plane"
        }
    }

    # Store all facts in cache
    cache.store_key_facts("aws_facts", aws_facts)
    cache.store_key_facts("gcp_facts", gcp_facts)
    cache.store_key_facts("azure_facts", azure_facts)
    cache.store_key_facts("redis_facts", redis_facts)
    cache.store_key_facts("kubernetes_facts", kubernetes_facts)

    # Common pricing patterns (general rules of thumb)
    pricing_patterns = {
        "memory_multiplier": {
            "description": "Memory-optimized instances cost ~2.5x compute-optimized",
            "examples": ["r5.large vs m5.large", "r6g.large vs m6g.large"]
        },
        "burstable_discount": {
            "description": "T-series instances offer ~70% cost savings for intermittent workloads"
        },
        "reserved_discount": {
            "1_year": "~30% discount vs on-demand",
            "3_year": "~45% discount vs on-demand"
        },
        "regional_pricing": {
            "us-east-1": "Usually baseline (cheapest)",
            "us-west-2": "Often 5-10% more expensive",
            "eu-west-1": "Often 10-15% more expensive",
            "ap-northeast-1": "Often 20-25% more expensive"
        },
        "egress_costs": {
            "first_100gb_month": "Free within AWS",
            "inter_region": "~$0.02/GB",
            "internet": "~$0.09/GB"
        }
    }

    cache.store_key_facts("pricing_patterns", pricing_patterns)


def get_cached_facts(provider: str, service: str = None) -> Dict[str, Any]:
    """Get cached facts for a specific cloud provider and service"""
    cache = get_tool_cache()

    if service:
        category = f"{provider}_facts"
        facts = cache.get_key_facts(category)
        if facts and service in facts:
            return facts[service]
    else:
        return cache.get_key_facts(f"{provider}_facts")

    return {}


def get_relevant_technology_facts(question: str) -> List[Dict[str, Any]]:
    """Extract relevant facts based on the question content"""
    cache = get_tool_cache()
    relevant_facts = []

    question_lower = question.lower()

    # Check for AWS mentions
    if any(term in question_lower for term in ['aws', 'amazon']):
        aws_facts = cache.get_key_facts("aws_facts")
        if aws_facts:
            relevant_facts.append({"provider": "AWS", "facts": aws_facts})

    # Check for GCP mentions
    if any(term in question_lower for term in ['gcp', 'google cloud']):
        gcp_facts = cache.get_key_facts("gcp_facts")
        if gcp_facts:
            relevant_facts.append({"provider": "GCP", "facts": gcp_facts})

    # Check for Azure mentions
    if any(term in question_lower for term in ['azure', 'microsoft']):
        azure_facts = cache.get_key_facts("azure_facts")
        if azure_facts:
            relevant_facts.append({"provider": "Azure", "facts": azure_facts})

    # Check for specific services
    if any(term in question_lower for term in ['redis', 'cache']):
        redis_facts = cache.get_key_facts("redis_facts")
        if redis_facts:
            relevant_facts.append({"service": "Redis", "facts": redis_facts})

    if any(term in question_lower for term in ['kubernetes', 'k8s', 'eks', 'gke', 'aks']):
        k8s_facts = cache.get_key_facts("kubernetes_facts")
        if k8s_facts:
            relevant_facts.append({"service": "Kubernetes", "facts": k8s_facts})

    # Check for pricing questions
    if any(term in question_lower for term in ['cost', 'price', 'pricing', 'expensive', 'cheap']):
        pricing_facts = cache.get_key_facts("pricing_patterns")
        if pricing_facts:
            relevant_facts.append({"category": "Pricing Patterns", "facts": pricing_facts})

    return relevant_facts


# Initialize facts on import
try:
    initialize_cloud_facts()
    print("[CACHE] Initialized cloud service facts database")
except Exception as e:
    print(f"[CACHE] Warning: Failed to initialize cloud facts: {e}")