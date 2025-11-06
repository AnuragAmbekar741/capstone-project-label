import httpx, os

K8S_CLUSTER_DOMAIN = os.getenv("K8S_CLUSTER_DOMAIN", "svc.cluster.local")

def user_service_url(user_hash: str) -> str:
    # Service name must match your controller’s naming convention
    return f"http://model-{user_hash}.{K8S_CLUSTER_DOMAIN}"

async def forward_json(url: str, payload: dict, headers: dict) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
