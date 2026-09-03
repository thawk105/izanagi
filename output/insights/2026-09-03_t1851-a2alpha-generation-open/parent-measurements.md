# 親の実測 — [T-1851] A2α

すべて親 (Claude) がこの wave で実走した値である。子の非実走は 1 件も緑と数えていない。

## 段 1 の実測

- **E3 は現物で赤だった。** `make_s8b_v2_domain_profile()` が返す v2 profile を
  `_assert_profile()` へ渡すと
  `S8BAttemptRegistryError: [s8b-attempt-registry-profile] domain profile differs from frozen 8b semantics`。
  repo 外 probe で実走 (2026-09-03)。模擬ではない。
- `S8B_V2_RETRYABLE_FAILURE_REASONS = frozenset()` (`s8b_attempt_profile.py:533`)。
- `_assert_profile` の call site は 5 件 (`s8b_attempt_registry.py:519,1343,1376,1410,2082`)。
- `FROZEN_MANIFEST` は 23 件で試行台帳の artifact を 1 件も含まない
  (`test_frozen_artifacts.py:41-115`)。`HELD` 4 件 / `KEEP` 19 件の分割も無関係。
- `docs/decisions.md` の `台帳専用` の hit は D1113 の 2 行だけ。**4 語の literal を凍結した
  裁定は repo に存在しない。**

## 焦点走 (DW-O26)

fix 1 巡目を取り込んだ HEAD `a5d9c8bcd` で実測。

| 対象 | 結果 |
|---|---|
| `orchestrator/tests/test_s8b_attempt_registry.py` (単独走) | 86 passed / rc=0 |
| `orchestrator/tests/test_attempt_registry_core_s8b_profile.py` (単独走) | 89 passed / rc=0 |
| consumer 閉包 (equivalence / trial_registry / s8b_holdout_admission / s8b_floor_attempt_launcher / plain_runner_coverage) | 431 passed / rc=0 |

計 606 node。consumer 閉包は名前の推測でなく参照関係で引いた。

## 検査

| 検査 | 結果 |
|---|---|
| `python3 tools/check_ai_provenance.py` (全史) | rc=0 (7,946 件、新規違反なし) |
| `python3 tools/check_docs.py` | rc=0 (`check_docs: 違反なし`) |
| `python3 tools/check_codex_agents.py` | rc=0 |
| `git diff --check` | rc=0 |

## 計算ノードの投入

- **子は 1 度も pytest を走らせられなかった。** 段 5 の実装子と段 6 の fix 子 5 巡、
  合わせて 6 者すべてが `qstat -Q preflight rc=1` により runner `rc=16`、
  `child_started=false` で終わった。
- **親からの同じ投入は D612 の opt-in 上書きで通る。**
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` と
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`。
  上書き前の親の 1 回目は `queue-wait-timeout` (rc=16、infra 失敗であって赤ではない) だった。
- 結果として、**実装の赤は必ず親の実走まで遅れて出る**構造になっていた。本 wave では
  baseline の赤が 2 回それで出た (いずれも fix 子が新設した test の fixture の作り方)。

## 変異 matrix

`tools/mutation_harness.py`、`--runner-mode dispatch`、`--detached`、
runner argv に `--force-dispatch`。走行対象は
`test_s8b_attempt_registry.py` と `test_attempt_registry_core_s8b_profile.py` の 2 file。

| 走 | HEAD | baseline | 結果 |
|---|---|---|---|
| probe (全件 SURVIVED 期待) | `a5d9c8bcd` | PASSED | 20 変異の観測 node を収集 |
| 較正 1 | `c785bd628` | **FAILED** | 新設 test 1 件が `FileNotFoundError` |
| 較正 2 | `3ca1622b2` | PASSED | 21 変異。M9 / M9b が生存 |
| 較正 3 | `b648d3cd4` | **FAILED** | 新設 test 1 件が protocol schema 不足 |
| 較正 4 | `9df7105f6` | PASSED | 21 変異すべて期待どおり |
| **本走** | `9df7105f6` | PASSED | **rc=0、21/21 一致、KILLED 17 / SURVIVED 4 / MISMATCH 0** |

## 本走の結果

| ID | 期待 | 結果 | 単一理由性 |
|---|---|---|---|
| M1 | KILLED (10 node) | KILLED | schema dispatch を v1 固定へ戻す。v2 を受理する層は他に無い |
| M2 | KILLED (3 node) | KILLED | `terminal_row_validator` identity 比較。`dataclasses.replace` 無効化を止める層は他に無い |
| M3 | KILLED (2 node) | KILLED | `retryable_terminal_opens_next_attempt` exact 比較 |
| M4a | **SURVIVED** | SURVIVED | adapter terminal の v2 拒否だけ。core validator が同じ入力を拒否する |
| M4b | KILLED (2 node) | KILLED | M4a + core validator 呼出しの両層同時 |
| M5 | KILLED (4 node) | KILLED | `_assert_state_path()` の protocol 分岐。他 10 呼出しはこの入口を通らない |
| M6 | KILLED (1 node) | KILLED | 世代 publish の既存世代拒否 |
| M6b | KILLED (3 node) | KILLED | M6 + `_publish_create_only` の事前拒否 + link race 拒否 |
| M7a | **SURVIVED** | SURVIVED | publish の parent symlink 検査だけ。他 3 層が再検査する |
| M7b | KILLED (2 node) | KILLED | M7a + 世代 symlink 判定 + `_read_regular_bytes` の parent 検査 |
| M8 | KILLED (5 node) | KILLED | claim v3 address から `measurement_ordinal` を落とす |
| M9 | KILLED (1 node) | KILLED | claim v3 の `protocol_sha256` 比較 |
| M9b | KILLED (1 node) | KILLED | M9 + claim address identity 検査の両層同時 |
| M10a | KILLED (1 node) | KILLED | `_atomic_update_locked` の lock 生存 guard |
| M10b | KILLED (2 node) | KILLED | M10a + admission 側 2 箇所の再検査 |
| M11 | KILLED (1 node) | KILLED | v2 start-only resume の fail-closed |
| M12 | KILLED (1 node) | KILLED | marker 経路の prelock hook を lock 内へ移す |
| M13 | **SURVIVED** | SURVIVED | reserve の marker 必須早期 gate だけ。下流の明示例外が残る |
| M13b | KILLED (1 node) | KILLED | M13 + 下流の明示例外の両層同時 |
| M14 | KILLED (1 node) | KILLED | **診断感度 pin。kill に数えない (下記)** |
| EQ | **SURVIVED** | SURVIVED | 等価変異。harness の SURVIVED 検出が生きていることの正例対照 |

**kill として数えるのは 16 件である。** M14 は `DW-M03` により kill に数えない (下記 erratum)。

## erratum — 変異登録の訂正 (DW-M02、初回結果は消さない)

### 段 4 の登録から変わった点

- **M6 を SURVIVED から KILLED へ。** 段 6 のレビュー D は「早期拒否を消しても
  `_publish_create_only` が再度拒否するので診断差でだけ赤になる」と静的に判定し、親もそう裁定した。
  **実走では単層でも実効的に殺されていた。** fix 1 巡目が入れた直接検査が効いている。
- **M10a を SURVIVED から KILLED へ。** レビュー C 所見 16 は「`_atomic_update_locked` の
  下層 guard は直接検査されていない」と判定し、親もそう裁定した。**fix 1 巡目の直接検査が
  これを閉じており、実走では単層で殺される。**
- **M9 を KILLED から SURVIVED へ、そして再び KILLED へ。** 初回 probe では単層も両層 (M9b) も
  生存した。レビュー D は「v2 lifecycle node の protocol tamper が kill する」と静的に判定して
  いたが、実走ではその node は赤にならなかった。fix 4・5 巡目で検査を新設した後は両方 KILLED。
- **M11 を再照準した。** 段 4 の M11 (「v2 resume の marker 分岐を legacy reader へ戻す」) は
  文字列置換として一意に表現できなかった。fix 1 巡目が入れた v2 start-only resume の
  fail-closed guard へ再照準した。
- **M14 を新設し、その後 kill から外した。** 下記。

### M14 — 冗長 gate であり kill に数えない

`resume_attempt()` の v2 回復序数 gate
(`[s8b-attempt-registry-consume] v2 resume recovery ordinal is not capability-backed`) は、
本走で赤になるが**赤の実体は拒否署名の差である**。gate を消しても resume は
start-only gate で拒否され続け、**受理集合は変わらない。**

`reserve_attempt_slot()` の同じ gate が先に拒否するため、**分類行を持つ `attempt_ordinal != 0`
の状態を公開経路で作れない。** fix 3 巡目が実装を変えずにこれを報告して停止した。

`DW-M03` の「診断文字列だけの赤を kill にしない」「過剰決定なら冗長 gate と明記して単独変異の
証拠から外す」に従い、**M14 は診断感度の pin として別枠に記録し、kill 16 件の内訳に含めない。**

### 初回 probe の結果 (消さずに残す)

初回 probe (HEAD `a5d9c8bcd`、20 変異) では M9・M12・M14 が生存した。
M12 と M14 は「防壁を消しても赤にならない」形で、**段 3 と段 6 の敵対レビュー 4 本すべてが
見落としていた。** M9 はレビュー D が明示的に「kill する」と判定していた箇所である。

## 受入全走

段 7 の記録 commit を含む最終 tip に対して 1 回だけ実施した。

- 投入: `tools/dev_wave_wait.py acceptance --wave dev-wave-t1851-unit-a`
  `--lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease -- python3 tools/run_tests.py`
- attempt 1: `classification=child-green`、`reason=child-verdict`、`retry=false`、
  raw child rc=0 / normalized child rc=0。
- `verdict=child-green`、`tested_main=36406d376be6003eaffbf32c1633717c1d9d346f`、
  `tested_tip=fe9c234803100783780aabaef52df216e243b417`、`lease_holder=a089fc930b73`。
- 走行 rc=0。lease は走行後に `tools/wave_land_window.py release` で解放した
  (`state=released`、`holder_self=true`)。
- **この受入は本節の記載を足す amend より前の tip に対するものである。** amend 後の tip では
  取り直していない。D1341 により本 wave は land せず、6 段が揃った時点で受入を取り直す。
