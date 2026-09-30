"""Constants for the Silo lock order policy axis."""
from . import pin

MARKER_ID = 'silo-lock-order-policy'
SOURCE_REL = 'cc/silo/transaction.cc'
TEMPLATE_PATCH = 'silo-lock-order-variant.patch'
API_HEADER = 'orchestrator/campaign/silo_lock_order_api.hh'
HAND_POLICY_DIR = 'orchestrator/campaign/silo_lock_order_hand'
FLAG = 'SILO_ORDER_VARIANT'
PIN = pin.CURRENT_PIN
REASON_NAMES = (
    'unset', 'lock_conflict', 'update_absent', 'read_tid',
    'read_locked', 'node_validation', 'insert_node', 'scan_node',
)
HAND_POLICIES = {'version_desc': 'version_desc.cpp'}
EXCLUSIVE_PATCHES = ('silo-sort-variant.patch', 'silo-function-policy-variant.patch')
