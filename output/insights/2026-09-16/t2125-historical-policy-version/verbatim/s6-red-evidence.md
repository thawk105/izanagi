# [T-2125] 段 6 時点の実測 (親が測った)

## 取り込みと commit

- 実装子の差分を所有 path 限定 patch で wave worktree へ適用し、統合 commit
  `2a785eeb5` を作った (7 file、486 insertions / 14 deletions)。
- `python3 tools/check_ai_provenance.py` (全史) rc=0、10466 件、新規違反なし。

## 基準 (変更前、base d97c423bd)

| 走 | 結果 |
|---|---|
| `test_artifact_admission.py` | **146 passed** (rc=0) |
| `test_build_admission.py` + `test_layer3_report.py` + `test_layer3_admission_diagnosis.py` + `test_t671_source_binding.py` | **634 passed** (rc=0) |

## 変更後 1 回目 (commit 前) — 19 failed / 794 passed

**未 commit 由来の偽赤だった。** 本文に
`contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/campaign/wal.py`。
`artifact_admission.py` / `build_admission.py` / `wal.py` は enforcement source closure の
member なので、未 commit だと HEAD blob と disk が食い違う。**実装の回帰ではない。**

## 変更後 2 回目 (commit 2a785eeb5) — 14 failed / 799 passed

**既存テストはすべて緑に戻った。** 1 回目に落ちていた `test_layer3_report.py` の
certifying 系 5 件 (`test_render_accepted_persists_certifying_report`、
`test_accepted_report_rejects_no_commit_campaign`、
`test_accepted_report_requires_e1_and_records_epoch`、
`test_certified_report_omits_current_verifier_conformance`、
`test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`) は緑。

**残る 14 件はすべて実装子が新しく足したテストである** (子は rc=16 で 1 件も走らせていない)。

| nodeid | 備考 |
|---|---|
| `test_artifact_admission.py::test_historical_policy_version_reads_recorded_v2[pin]` | **`[generator]` と `[review]` は緑。落ちるのは `[pin]` だけ** |
| `test_artifact_admission.py::test_historical_policy_drift_preserves_structure_checks[…]` | 6 parametrize すべて |
| `test_artifact_admission.py::test_historical_policy_drift_preserves_trigger_checks[…]` | 3 parametrize すべて |
| `test_artifact_admission.py::test_historical_policy_drift_rechecks_bytes[campaign.lock]` / `[runs/wal.jsonl]` | 2 件 |
| `test_artifact_admission.py::test_historical_policy_version_preserves_pre_t733_epoch` | 1 件 |
| `test_layer3_report.py::test_historical_policy_version_report_schema` | 1 件 |

## 14 件の共通原因 (1 つ) — 親が単独走行で切り分けた

単独走行 `test_historical_policy_version_reads_recorded_v2` は **1 failed / 2 passed**。
落ちるのは `[pin]` だけで、`[generator]` と `[review]` は緑である。

すべて同じ例外で落ちている。

```
orchestrator/campaign/build_admission.py:701: BuildAdmissionError
E  orchestrator.campaign.build_admission.BuildAdmissionError:
   source evidence は stock/review/generator/coder のどれも支持しない
```

発火点は `derive_build_admission` の分類 (`build_admission.py:672-701`)。STOCK 枝の条件は

```
    if source.src_token == STOCK and source.tracked_clean is True \
            and source.ccbench_commit == CURRENT_PIN:
```

## 親が特定した根本原因

新しい fixture `recorded_policy_campaign` (`test_artifact_admission.py:49-80`) は
`change == "pin"` のとき **2 箇所しか差し替えていない**。

```
issuing.setattr(B, "CURRENT_PIN", "d706650")          # build_admission の global
issuing.setitem(globals(), "CURRENT_PIN", "d706650")  # test_artifact_admission の global
```

しかし素材づくりの経路は **3 つ目の名前空間**からも `CURRENT_PIN` を読む。

```
orchestrator/tests/commit_receipt_support.py:83:        ccbench_commit=CURRENT_PIN,
```

`commit_receipt_support` は自分の module global として `CURRENT_PIN` を持っており、
fixture の `globals()` 差し替えはここに届かない。**その結果、同じ campaign の中で
d706650 の evidence と 511c953 の evidence が混ざり、分類が成立しない。**

`[generator]` / `[review]` の変種は pin を触らないので、この不整合が起きず緑になる。

## 親の判断

- **実装の回帰ではない。新しいテストの素材づくりが不完全である。**
- ただし**放置してはいけない**。pin 前進は本 wave が実測した唯一の版上げ事象であり、
  その正例が作れないままでは、**解こうとしている故障モードを立証できていない**ことになる。
- fix は Codex 子が行う。親は実装面を編集しない。
- fix の際、`commit_receipt_support` の**本文を書き換えて現行 pin を壊さない**こと。
  差し替えは fixture 側で、素材を作る間だけに限る。
