# 再利用先の棚卸し (D500 決定 (6) が次 wave の段 1 要件と定めたもの)

親が実読した結果。2026-08-18 13:35 JST。すべて worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/worktree-dev-wave-t338-submission-gate` 上の実測。

## D234 決定 (7) の gate 署名と 7 条件に対する既存部品の対応

| 条件 | 内容 | 既存部品 | 判定 |
|---|---|---|---|
| (i) | `core_ref.path` が canonical core path と byte 一致 | `preregistration/approval_payload.py` の `target_core` (D282 payload) | 結線のみ |
| (ii) | commit tree に blob 実在 + SHA-256 一致 + 承認済み core digest と一致 | `campaign/trial_registry.py:895` `_blob_at_commit`、`preregistration/blobref.py` `read_pinned_blob` | 結線のみ |
| (iii) | `core_ref.commit` が D234 fold commit の子孫 | `campaign/trial_registry.py` の `_assert_ancestor` | 結線のみ |
| (iv) | 追補が記す core の三つ組が `core_ref` と一致 | `preregistration/addendum_envelope.py` | 結線のみ |
| (v) | 追補が閉集合を exact-key で満たす (欠落も余剰も失敗) | 同 `require_exact_fields` / `require_approved_addendum_a_fields`、`T139_EXACT_FIELDS` | **実装済み** |
| (vi) | `core_ref.commit` / `addendum_a.commit` が `measurement_head` の祖先 | `campaign/trial_registry.py:878` `assert_prereg_ancestor` (D234 が「同型」と名指しした当の関数) | **実装済み** |
| (vii) | core の `pilot_admission` が要求する追補が (iv)(v) で解決済み | `preregistration/erratum.py` `compose_core` + 上記 | 結線のみ |

`measurement_head` は「caller の引数ではなく `repository_root` の実 checkout から resolver が導出する」
(D234 逐語) — 導出は `trial_registry` の既存 git helper で足りる。

## 受領証 writer と parse 層

| 要求 | 既存部品 | 判定 |
|---|---|---|
| §6.10 writer 認可 (opaque capability を必須 keyword-only) | `qualification/artifacts.py:125` `QualificationWriteCapability` (private token・不変・`__slots__`) | **構造的先例。`PreregBinding` を同型で書く** |
| §6.10 単一 fd / snapshot・`O_NOFOLLOW`・symlink 拒否 | `qualification/artifacts.py:82` `read_regular_file_with_identity` | **実装済み** |
| §7 duplicate JSON key 拒否 (parse 前段)・canonical bytes・末尾 LF | 同 `:541` `load_json_strict` | **実装済み** |
| §7 dialect draft-07 | 同 `:632` `validate_json_schema` (`Draft7Validator`) | **実装済み** |
| 原子公開 | `qualification/atomic_publish.py:24` `publish_bytes` (dir fsync 付き) | **実装済み** |
| canonical JSON bytes | `qualification/contract.py` `canonical_json_bytes` | **実装済み** |

## attempt registry の土台

- **採る: `qualification/attempt_ledger.py` (473 行)。** create-only・series-global の hash 連鎖台帳。
  `previous_event_sha256` / `event_sha256` / nonce / job_id / `qsub_invocation_sha256` /
  `submission_evidence_sha256` を持ち、event 型は
  `initial_intent` / `initial_submitted` / `attempt_outcome` / `attempt_outcome_pending` /
  `retry_intent` / `retry_submitted`。D500 決定 (6) が名指しした再利用先であり、
  受領証 `attempts[]` の `qsub_result` / `performance_started_marker` と型が合う。
- **採らない: `campaign/s8b_holdout_admission.py` の `O_EXCL` marker** (`:348`, `:683`)。
  同 file 自身が「`O_EXCL` は file が存在する間だけ効く。この耐性は本 wave の保証範囲外」と
  明記している (`:10`, `:2273`)。producer が選べない intent authority の土台にはならない。
- **採らない (単独では): `qualification/series.py` (378 行)。** T-126 の単一 controller FSM で
  SPRT 判定に束縛されており、RF study の 3 arm cluster 設計と identity が合わない。
  `contract.py` の `canonical_json_bytes` / `balanced_order` は個別に借りる。

## 見積りへの含意 (親の再計算)

- gate 段 1+2 (承認 manifest 解決 + 祖先検査): 当初 400〜800 行 → **250〜450 行** (結線が主)
- `PreregBinding` + 受領証 writer: 当初 250〜450 行 → **150〜300 行** (capability と publish が既存)
- 固定 semantic validator: **1,100〜2,400 行** (変わらず。ここが主費用)
- `submit_pilot` / `verify_receipt` 入口: 150〜300 行

**切り直し後の production 再見積り = 1,650〜3,450 行。**
下限でも D220 の 645〜816 行を 2.0 倍超える。**この事実は最終報告でユーザーへ明示する。**

## D234 決定 (6) の裏付け

「凍結の実装は commit/blob 参照束縛だけとする。**現在の作業木の bytes を固定する検査は置かない**
— main の前進を妨げる検査を作らない。」

承認済み契約自身が重い凍結機構を既に却下しており、(P1)/(P2) の切り直しと同じ向きである。
