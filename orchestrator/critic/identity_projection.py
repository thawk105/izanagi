# -*- coding: utf-8 -*-
"""critic recipient へ出す候補識別子の射影契約。

CLI の直接実行時にも ``critic.digest`` と campaign 側 factory が同じ nominal
type を共有できるよう、描画実装から独立した中立 module に置く。
"""
from __future__ import annotations

from typing import Optional


class IdentityProjection:
    """campaign-local projector と明示 raw 診断の共通契約。"""

    def project_variant(self, value: Optional[str]) -> Optional[str]:
        raise NotImplementedError

    def project_src_token(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        raise NotImplementedError

    def project_build_attempt_id(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        raise NotImplementedError

    def project_build_admission_receipt_sha256(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        raise NotImplementedError


class _RawIdentityProjection(IdentityProjection):
    """raw 診断を選ぶ明示 sentinel の実装。"""

    def project_variant(self, value: Optional[str]) -> Optional[str]:
        return value

    def project_src_token(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        return value

    def project_build_attempt_id(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        return value

    def project_build_admission_receipt_sha256(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        return value


IdentityProjection.RAW = _RawIdentityProjection()
