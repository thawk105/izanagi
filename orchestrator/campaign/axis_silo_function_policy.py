"""Constants for the Silo function-policy skeleton (D2214)."""
from . import pin

MARKER_ID = "silo-function-policy"
SOURCE_REL = "cc/silo/transaction.cc"
TEMPLATE_PATCH = "silo-function-policy-variant.patch"
API_HEADER = "orchestrator/campaign/silo_function_policy_api.hh"
HAND_POLICY_DIR = "orchestrator/campaign/silo_function_policy_hand"
FLAG = "SILO_POLICY_VARIANT"
PIN = pin.CURRENT_PIN
ABORT_WAIT_MAX_US = 1000
LOCK_WAIT_MAX_US = 50
LOCK_ATTEMPT_LIMIT = 32
REASON_NAMES = (
    "unset", "lock_conflict", "update_absent", "read_tid",
    "read_locked", "node_validation", "insert_node", "scan_node",
)
REASON_SITES = {
    "insert_node_version_mismatch": "insert_node",
    "write_set_lock_conflict": "lock_conflict",
    "update_target_absent": "update_absent",
    "read_set_tid_changed": "read_tid",
    "read_set_locked_by_other": "read_locked",
    "validation_node_version_mismatch": "node_validation",
    "scan_node_version_mismatch": "scan_node",
}
HAND_POLICIES = {
    "abort0": "abort0.cpp",
    "maxwait": "maxwait.cpp",
    "static5": "static5.cpp",
    "static10": "static10.cpp",
    "retry": "retry.cpp",
    "huge": "huge.cpp",
}
