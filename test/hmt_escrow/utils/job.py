from typing import Optional

from basemodels import Manifest

from hmt_escrow.job import Job
from test.hmt_escrow.utils import manifest as sample_manifest


def create_job(
    manifest: Optional[Manifest] = None,
    gas_payer: Optional[str] = None,
    gas_payer_priv: Optional[str] = None,
) -> Job:
    """Creates sample Job instance"""
    manifest = manifest or sample_manifest
    credentials = {
        "gas_payer": gas_payer or "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        "gas_payer_priv": gas_payer_priv
        or "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
    }
    return Job(credentials=credentials, escrow_manifest=manifest)
