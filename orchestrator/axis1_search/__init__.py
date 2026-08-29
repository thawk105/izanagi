"""Public, dependency-light API for Axis 1 search registration and parsing."""

from .catalog import (
    CATALOG_SCHEMA_VERSION,
    REGISTERED_CUTOFF,
    REGISTRATION_EPOCH,
    Catalog,
    Index,
    LogicalKind,
    LogicalQuery,
    RequestSpec,
    Shard,
    build_catalog_document,
    build_request,
    derive_expected_logical_ids,
    derive_fixed_shards,
    load_catalog,
    render_catalog_json,
)
from .parsers import (
    Occurrence,
    ParsedPage,
    parse_arxiv_page,
    parse_dblp_page,
    parse_openalex_page,
)

__all__ = [
    "CATALOG_SCHEMA_VERSION",
    "REGISTERED_CUTOFF",
    "REGISTRATION_EPOCH",
    "Catalog",
    "Index",
    "LogicalKind",
    "LogicalQuery",
    "Occurrence",
    "ParsedPage",
    "RequestSpec",
    "Shard",
    "build_catalog_document",
    "build_request",
    "derive_expected_logical_ids",
    "derive_fixed_shards",
    "load_catalog",
    "parse_arxiv_page",
    "parse_dblp_page",
    "parse_openalex_page",
    "render_catalog_json",
]
