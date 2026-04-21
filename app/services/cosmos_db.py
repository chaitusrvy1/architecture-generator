import logging
from azure.cosmos import CosmosClient, exceptions
from app.core.config import settings

from app.core.lifespan import state

logger = logging.getLogger(__name__)

# Realistic Patent-related Mock Data
MOCK_DB = {
    "pat-991": {
        "title": "Decentralized Identity Verification System",
        "description": "A system for verifying user identity using zero-knowledge proofs on a blockchain-based ledger.",
        "technical_claims": [
            "Self-sovereign identity management",
            "ZK-proof generation at edge devices",
            "Distributed ledger for attestation storage"
        ],
        "components": ["Edge Wallet App", "ZK-Proof Generator", "Identity Bridge Service", "Ethereum Layer 2", "IPFS Storage"]
    },
    "pat-992": {
        "title": "Self-Optimizing Neural Network Gateway",
        "description": "An intelligent gateway that dynamically reconfigures model weights based on real-time network latency and power constraints.",
        "technical_claims": [
            "Dynamic weight quantization",
            "Latency-aware routing engine",
            "Real-time feedback loop from edge nodes"
        ],
        "components": ["Inference Gateway", "Latency Monitor", "Weight Optimization Engine", "Model Registry", "Edge Deployment Controller"]
    },
    "pat-993": {
        "title": "Automated Privacy-Preserving Data Synthesis",
        "description": "A system that generates synthetic datasets from sensitive PII data while maintaining differential privacy guarantees.",
        "technical_claims": [
            "GAN-based data synthesis",
            "Differential privacy noise injection",
            "Statistical utility scoring"
        ],
        "components": ["Data Ingestion Pipe", "Privacy Guardrail Engine", "GAN Synthesizer", "Utility Evaluator", "Compliance Audit Log"]
    }
}

async def get_invention_details(invention_id: str) -> dict:
    """
    Fetches invention details from Cosmos DB with a focus on patent-related information.
    """
    # 1. Check if we should use mock data
    if not settings.cosmos_db_endpoint or "mock" in settings.cosmos_db_endpoint:
        logger.info(f"Using mock patent data for ID: {invention_id}")
        return MOCK_DB.get(invention_id, {
            "title": "Standard Innovation",
            "description": "A technical solution for an industry problem.",
            "components": ["Generic Frontend", "Processing Layer", "Database"]
        })

    # 2. Use the shared container if available
    container = state.cosmos_container
    
    # 3. Fallback to local client if lifespan didn't initialize it (e.g. in tests)
    if not container:
        try:
            logger.info("Initializing ad-hoc Cosmos client (lifespan state not found)")
            client = CosmosClient(settings.cosmos_db_endpoint, settings.cosmos_db_key)
            database = client.get_database_client(settings.cosmos_db_database_name)
            container = database.get_container_client(settings.cosmos_db_container_name)
        except Exception as e:
            logger.error(f"Failed to initialize ad-hoc Cosmos client: {str(e)}")

    if container:
        try:
            return container.read_item(item=invention_id, partition_key=invention_id)
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Invention {invention_id} not found in Cosmos DB. Falling back to mock.")
        except Exception as e:
            logger.error(f"Cosmos DB lookup failed: {str(e)}. Falling back to mock.")
            
    return MOCK_DB.get(invention_id, {"title": "Fallback System", "components": ["App", "API", "DB"]})
