"""Closed, bounded admission of the Silo lock order model result."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Mapping

from tools.cc_model_checker.schema import Counterexample, validate_counterexample

SCHEMA = 'cc-model-result/1'
AXIS = 'silo-lock-order-policy'
REASONS = frozenset({
    'model-unregistered', 'model-result-missing', 'model-result-invalid',
    'model-digest-mismatch', 'model-scenario-missing', 'model-incomplete',
    'model-coverage-mismatch', 'model-witness-missing', 'model-counterexample',
})
_DIGEST = re.compile(r'sha256:[0-9a-fA-F]{64}\Z')
_ID = re.compile(r'[A-Za-z0-9_.:-]{1,64}\Z')
_TOP = {'schema', 'axis', 'specification_digest', 'scenarios'}
_SCENARIO = {'scenario_id', 'complete', 'stop_reason',
             'explored_configurations', 'witness_reached', 'counterexamples'}


@dataclass(frozen=True)
class ModelRegistry:
    specification_digest: str | None
    scenarios: Mapping[str, Mapping[str, object]] | None
    vocabulary: Mapping[str, frozenset[str]] | None = None


@dataclass(frozen=True)
class ModelDecision:
    passed: bool
    reject_code: str | None
    specification_digest: str | None
    scenario_ids: tuple[str, ...] = ()
    counterexamples: tuple[Counterexample, ...] = ()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('non-finite JSON number')


def _registered(registry):
    if type(registry) is not ModelRegistry:
        return False
    digest, scenarios = registry.specification_digest, registry.scenarios
    if type(digest) is not str or not _DIGEST.fullmatch(digest):
        return False
    if not isinstance(scenarios, Mapping) or not scenarios or len(scenarios) > 4096:
        return False
    for key, requirement in scenarios.items():
        if type(key) is not str or not _ID.fullmatch(key):
            return False
        if type(requirement) is not dict or set(requirement) != {
                'expected_configurations', 'witness_required'}:
            return False
        expected = requirement['expected_configurations']
        if expected is not None and (type(expected) is not int or expected < 0):
            return False
        if type(requirement['witness_required']) is not bool:
            return False
    return True


def check_model_result(result_bytes: bytes | None, registry: ModelRegistry) -> ModelDecision:
    """Return one closed reason; a passed result is only structural evidence."""
    if not _registered(registry):
        return ModelDecision(False, 'model-unregistered', None)
    digest = registry.specification_digest
    if result_bytes is None:
        return ModelDecision(False, 'model-result-missing', digest)
    try:
        if type(result_bytes) is not bytes:
            raise ValueError('result must be bytes')
        data = json.loads(result_bytes.decode('utf-8'), object_pairs_hook=_unique_pairs,
                          parse_constant=_invalid_constant)
        if type(data) is not dict or set(data) != _TOP or data['schema'] != SCHEMA:
            raise ValueError('invalid result fields')
        if (type(data['axis']) is not str or type(data['specification_digest']) is not str
                or not _DIGEST.fullmatch(data['specification_digest'])):
            raise ValueError('invalid identity')
        raw_scenarios = data['scenarios']
        if type(raw_scenarios) is not list or len(raw_scenarios) > 4096:
            raise ValueError('invalid scenario array')
        scenarios = {}
        counterexamples = []
        for raw in raw_scenarios:
            if type(raw) is not dict or set(raw) != _SCENARIO:
                raise ValueError('invalid scenario fields')
            sid = raw['scenario_id']
            if type(sid) is not str or not _ID.fullmatch(sid) or sid in scenarios:
                raise ValueError('invalid or duplicate scenario id')
            if (type(raw['complete']) is not bool
                    or type(raw['stop_reason']) is not str
                    or raw['stop_reason'] not in ('exhausted', 'max_states', 'max_seconds')
                    or type(raw['explored_configurations']) is not int
                    or raw['explored_configurations'] < 0
                    or raw['witness_reached'] is not None
                    and type(raw['witness_reached']) is not bool
                    or type(raw['counterexamples']) is not list):
                raise ValueError('invalid scenario value')
            if len(counterexamples) + len(raw['counterexamples']) > 64:
                raise ValueError('too many counterexamples')
            for item in raw['counterexamples']:
                validated = validate_counterexample(item, vocabulary=registry.vocabulary)
                if (validated.specification_digest != data['specification_digest']
                        or validated.scenario_id != sid):
                    raise ValueError('counterexample identity mismatch')
                counterexamples.append(validated)
            scenarios[sid] = raw
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
        return ModelDecision(False, 'model-result-invalid', digest)
    ids = tuple(sorted(scenarios))
    evidence = tuple(counterexamples)
    def reject(code):
        return ModelDecision(False, code, digest, ids, evidence)
    if data['axis'] != AXIS or data['specification_digest'] != digest:
        return reject('model-digest-mismatch')
    if any(sid not in scenarios for sid in registry.scenarios):
        return reject('model-scenario-missing')
    for sid, requirement in registry.scenarios.items():
        found = scenarios[sid]
        if not found['complete'] or found['stop_reason'] != 'exhausted':
            return reject('model-incomplete')
        expected = requirement['expected_configurations']
        if expected is not None and found['explored_configurations'] != expected:
            return reject('model-coverage-mismatch')
        if requirement['witness_required'] and found['witness_reached'] is not True:
            return reject('model-witness-missing')
    if evidence:
        return reject('model-counterexample')
    return ModelDecision(True, None, digest, ids)
