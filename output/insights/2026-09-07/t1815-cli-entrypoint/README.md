# [T-1815] 8c 事前登録 CLI の二重実体化と相対 import を直す — 実施記録

- wave branch: `worktree-dev-wave-t1815-cli-entrypoint`
- 着手時 local main: `cf4273f5671ecda87c6f1b76148df239ce043ead`
- 実装 commit: `98e6821d8` / fix commit: `3b9f305c0` / 台帳 commit: `d53c91a2b`
- 関連台帳: F631 (欠陥の発見記録)、archive worklog 981 で [T-1815] として登録
- 逐語: `verbatim/` (段 1 brief と追補、段 2 プラン、段 3 の 2 レンズ、段 4 裁定、
  段 5 実装子、段 6 レビュー 2 本と fix 2 本)

---

## 1. 直した欠陥

`orchestrator/campaign/s8c_preregistration.py` を実プロセスとして起動すると、
core module が canonical 名 `orchestrator.campaign.s8c_preregistration` で**もう一度**実体化する。
評価器 (`s8c_preregistration_evidence.py:18` の `from . import s8c_preregistration as core`) は
canonical 側の core を掴むため、返す `PredicateResult` が `__main__` 側の同名クラスと別クラスになる。
`_normalize_predicate_results` の `isinstance` が偽になって `PreregistrationError("predicate-result-type")`
が上がり、`_default_registry_results` の広い `except Exception` がそれを握り潰して
**12 条件すべてを `ERROR / evaluator-exception` へ倒していた。**

`orchestrator/campaign/s8c_gate_report.py` はファイルパス直接起動で、module body 初期化中の
相対 import が `ImportError` になり、`_main()` の JSON 例外処理にも到達しなかった。

## 2. 親が実測した before / after

すべて親の実測。実行機は login node (`/work/1/SFC/tanab/izanagi` および wave worktree)。

| 起動形 | 修正前 | 修正後 |
|---|---|---|
| `python3 <path>/s8c_preregistration.py check --json` | 12 件 `ERROR / evaluator-exception` | library と一致する混合 status |
| `python3 -m orchestrator.campaign.s8c_preregistration check --json` | 12 件 `ERROR / evaluator-exception` | 同上 |
| `python3 <path>/s8c_gate_report.py` | `ImportError` traceback | 構造化 JSON |
| `python3 -m orchestrator.campaign.s8c_gate_report` | 正常 (対照) | 変わらず正常 |

**`-m` 形式も壊れていた点は F631 の記述より広い。** F631 は「package として import して `main()` を
呼ぶと本当の内訳が出る」と書いており、これは正しいが、`-m` は `runpy` が対象コードを
`sys.modules["__main__"]` の namespace で実行するため同じ二重実体化を起こす。
F631 が独立入口として名指しした `python3 -m orchestrator.campaign.s8c_gate_report` が正しく動くのは、
gate report が `__main__` で core を**通常の canonical import** するからである。

修正後の real repo HEAD (commit `98e6821d8`、29.7 秒、rc=1):

```
effective=false  freeze=valid  decider=decider-version-match
C01 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C02 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C03 UNSATISFIED        manifest-registry-proof-undefined
C04 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C05 EVIDENCE_UNDEFINED schedule-schema-absent
C06 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C07 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C08 EVIDENCE_UNDEFINED prereg-binding-proof-undefined
C09 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C10 SATISFIED          cross-binding-readiness-satisfied
C11 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C12 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
§5: 9 欄中 8 欄が未充足
```

**受理集合は変わっていない。** 修正前後とも `effective=false`、rc=1 である。変わったのは
「何が塞いでいるか」が読めるようになったことだけである。

## 3. 段 3 と段 6 が親の前提を覆した点

- **親の追補 (P5) は親自身の実測で反証された。** 親は「real repo の全評価は混雑 regime で
  39〜119 秒かかる」を測ったうえで、「小さな合成 repo を作って安く同じ欠陥を踏ませることはできない」
  と書いて子へ渡した。**これは測っていない否定であり、誤りだった。** レンズ sol の所見 8 が
  「live の 3 module bytes を合成 commit へ copy すれば三 blob gate を通過できる」と指摘し、
  親が実測して確認した。合成 repo なら **1 走 0.2〜0.3 秒**である。
- **その結果、段 2 の 4 ケース全評価案 (最悪 8 回の全評価 = 313〜950 秒) を捨てた。**
  最終形の新規テストは 4 ケースで **1.31 秒** (親実測、自走 harness)。
- **レンズ sol の blocker 所見 1 (`DECIDER_VERSION` を bump せよ) は親が一次資料で反証した。**
  根拠は 3 点で、とくに `_assert_history_transition` (`s8c_preregistration.py:1498-1500`) が
  `protected_sha256` の変わらない世代更新を `spurious-revision` で機械拒否するため、
  凍結範囲を変えない本 wave では **v10 + g16 が発行不能**である。
- **`s8c_gate_report.py` は campaign lock の enforcement source closure に入っていない。**
  親の段 1 brief (P3) は「両 file が enforcement source」と書いたが、段 2 と段 3 の双方が反証した。
  core だけが closure 内である。
- **`test_campaign_import_invariant.py` の `campaign-direct-bootstrap` 規則に、
  `s8c_gate_report.py` は修正前から違反していた。** 例外台帳 `KNOWN_EXCEPTIONS` (10 件) に
  `BOOTSTRAP_RULE` の項目は 1 件も無い。赤になっていなかったのは、この test file 全体が
  growth hold 下にあり既定の走行に入らないためである。本 wave の修正はこの潜在違反も同時に閉じる。

## 4. 段 6 の敵対レビューが出した must-fix

| 出所 | 所見 | 対応 |
|---|---|---|
| レビュー A | `--commit` 採用検査が恒真 (tiny repo が 1 commit しか持たず HEAD と一致) | 第 2 commit を足し `HEAD != 評価対象 commit` にした |
| レビュー B | Git と Python の環境が閉じておらず、継承 `PYTHONPATH` が変異 M4 を mask する | allowlist env を 1 箇所に作り全 git と 4 subprocess へ適用した |
| レビュー B | consumer 6 suite が未走 | 親が焦点走で実走した |
| レビュー B | 新規 4 node が所要台帳に未登録 | 実測 JUnit から `--add-only` で登録した |

**レビュー B の環境所見は衛生ではなく検出力の問題だった。** 継承 `PYTHONPATH` があると
`sys.path.insert` を消しても `orchestrator` が解決でき、事前登録した M4 が生存してしまう。
fix 子が実際に一時変異で確かめ、閉じた env の下で `[gate-path]` だけが赤になることを実証した。

## 5. 変異 matrix — diagnostic sensitivity pin

`DW-M08` に従い、本 wave の変異は KILLED ではなく **diagnostic sensitivity pin** として記録する。
4 件とも受理集合を変えず (`effective` はどの経路でも false のまま)、変えるのは診断出力だけだからである。

台帳は `mutation-ledger.json`、spec は `mutation-spec.json` (sha256
`baf7792348fbe17439f0cab0e0cec44c16f236f5b8ab1b22ceea6a3334b73ad4`)。
runner は `python3 tools/run_tests.py --force-dispatch -p no:randomly -q -rf
orchestrator/tests/test_s8c_cli_entrypoints.py`、`--runner-mode dispatch`。

| id | 変異 | 期待赤 node | 観測 | 判定 |
|---|---|---|---|---|
| baseline | なし | — | 赤 0 件 | PASSED |
| M1 | prereg の alias block を丸ごと削除 | `[prereg-path]` `[prereg-module]` | 同一 | KILLED |
| M2 | alias block を `__package__` guard の内側へ移動 | `[prereg-module]` | 同一 | KILLED |
| M3 | gate の `__package__` 代入行を削除 | `[gate-path]` | 同一 | KILLED |
| M4 | gate の `sys.path.insert` 行を削除 | `[gate-path]` | 同一 | KILLED |

期待 node と観測 node は 4/4 で完全一致した。

**M3 と M4 には既定走では発火しない第 2 の検出層がある。** 逐語 `DIRECT_BOOTSTRAP` を壊すため、
growth hold を解放すれば `test_campaign_import_invariant.py` の
`test_real_campaign_package_has_canonical_direct_bootstrap` も赤になる。既定走では hold により
skip されるので観測赤は `[gate-path]` だけだが、**全 suite に対する単一層性ではない。**

登録しなかった候補と理由 (レンズ sol・luna が独立に一致した):

- `setdefault` 化 — fresh process では代入と同値で観測差がない。
- `_normalize_predicate_results` の型緩和 — 本 wave の変更行ではなく、alias 修正後は同じ型しか
  流れないため単独変異では観測差がない。
- 新規 test file 自身の変異 — production 欠陥ではない。

## 6. 実走した検査

| 対象 | 結果 |
|---|---|
| 新規 test file 単独 (自走 harness、`PYTHONPATH` 有/無) | 4 passed / 0.8〜0.9 秒 |
| 焦点走 1 (新規 + s8c 3 + t671 + artifact_admission + plain_runner + collection + schedule_order + ccbench_spawn) | rc=0、1257 passed / 5 skipped / 93.7 秒 (job 981410) |
| 焦点走 2 (p3_autonomous_workload_trial + reflux_origin_binding + trial_registry + campaign_import_invariant) | rc=0、536 passed / 6 skipped / 169.4 秒 (job 981416) |
| 変異 matrix | baseline PASSED、4/4 KILLED |
| 全史 AI provenance 監査 | rc=0 |

`test_campaign_import_invariant.py` は growth hold により実走されない。**hold を解放していない。**

## 7. 本 wave では触らなかった real 所見 (裁定パッケージ候補)

- **機構を強制する構造 pin がない。** 新設テストは「answer」を pin するので、alias を足さずに
  `_normalize_predicate_results` の型検査を緩める実装でも通ってしまう。ユーザーが
  「仮想リスク向けの gate・検査の追加は scope 外」と明示したため実装しなかった。
  規律 2 は「`_normalize_predicate_results` を不変とする」不変条件、段 6 敵対レビュー、
  変異 matrix で守った。
- `_default_registry_results` の `except Exception` が例外理由を握り潰す点 (F631 が
  「なぜ通らなかったかが消える」と書いた部分)。
- `s8c_gate_report.py` を campaign lock の enforcement source closure へ入れるかどうか。
  入れると 62 path 集合と digest が変わるので別裁定とした。
- `test_campaign_import_invariant.py` の growth hold 解放。
- 所要台帳に本 wave と無関係な未登録 node が 202 件ある (最初の台帳投入で判明。他 wave 由来)。
- 長寿命 process へ埋め込んだときの canonical alias 上書き。本 wave の契約は
  **fresh standalone process 限定**とする。
