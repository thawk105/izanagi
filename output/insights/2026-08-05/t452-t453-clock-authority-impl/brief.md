# 段 1 brief — [T-452] + [T-453] clock tolerance authority 実装

base = local main `f009da3` / wave branch `worktree-dev-wave-t452-t453-clock-authority`
設計の正本 = `output/insights/2026-04-08…` ではなく
`output/insights/2026-08-04_t452-clock-tolerance-authority/README.md` (§2〜§7 と §8 の U 表)。

## scope (裁定済み U-1〜U-8 の実装面のみ)

1. `orchestrator/calibrator/effective_clock_policy.py` を新設し `EFFECTIVE_CLOCK_TOLERANCE_PCT: Final[float] = 2.0` を単一権威にする (U-1/U-2)。
2. 手入力面の撤去 (U-3) — `cli.py:131`(option)、`:485-488`(検証)、`:551`(代入) と `tools/pegasus/submit_certify.sh:7,17,22,32-42,177`、`tools/pegasus/certify_calibration.sh:154-164,730`。producer は policy 定数を注入する。
3. observed の型分離 + `pegasus-probe-output/v2` (U-4) — probe は `samples_mhz/method/governor` だけを持つ observed 専用型を返し、v1 は「clock key 4 個 + sentinel 厳密 `100.0`」の legacy parser で射影する。full-profile hash に版付き projection を置く。
4. expected schema 上限を `<100.0` へ (U-5)。完全一致は schema でなく trust boundary が持つ。
5. 各 trust boundary の policy 一致検査 — loader `load_verified_calibration`、issuer の独立比較 (`env_attestation.py:576-592` 相当)、canonical consumer (`execution_guard.py:182-199`)、取得時 self gate、registry 不変条件。receipt は observed/expected を exact key 集合で閉じ、observed への `tolerance_pct` 注入 forged receipt を拒否する。
6. **[T-453]** — `silo_ladder_rung1.py:1962-1966` と `:3401-3417` の median 比較を canonical 述語へ寄せる (同一 landing、U-6)。

## scope 外 (実装しない)

probe 方式 ([T-419] U-1)、較正再取得 ([T-419] U-2)、contract 世代移行 ([T-478])、content-addressed path 強制 ([T-477])。**既知例外集合 `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は空にしない** — 空にするのは U-2 の仕事。

## 段 1 で実測した事実 (承認済み裁定の前提照合)

- 登録較正 `calibration-753f535a8d024727.json` の `tolerance_pct` は既に **`2.0`**、48 標本中 1 個が `3080.935` (median 2101.0 の +46.64 %)。policy 一致の導入だけでは loader を新たに壊さない (設計 §6-3 のとおり)。
- `contract_sha256` は registry の field だけから導出される (`env_contract.py:150-160`)。**本 wave は calibration path/SHA を動かさないので `output/s8b-freeze/floor_protocol.json` の pin は動かない** — `DW-O09` の閉包は発火しない。
- **(新事実 N1)** v1 の観測 artifact は staging 15 件ではなく **19 件** (`output/env/pegasus/smoke/*/observation.json` 4 件を含む)。legacy parser の replay 対象はこの 19 件 + clock 無し 3 件。
- **(新事実 N2)** 既存の観測 artifact **16 件すべて**が median gate は通り canonical 述語では落ちる (min 2101.0 / max ≈3020-3080、帯は `[2058.98, 2143.02]`)。**`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` は `effective_clock_match=True` / `all_pass=True` を記録済み**であり、canonical 化はこの記録と衝突する。設計 §9 が予告した衝突の具体的な爆風半径である。
- median 比較の第 3 の複製が `orchestrator/tests/test_silo_ladder_rung1_evidence.py:945-963` の独立再導出にある。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** N2 の解き方 = 生産経路は canonical へ寄せ、**保存済み silo evidence の記録は歴史として保持**し、current eligibility を外す既知例外 (U-2 で空になる) として明示する。設計 §6 が「旧 silo evidence の binding を新 SHA へ書き換えてはならない」と禁じているため、artifact bytes の貼り替えは選ばない。
- **(P2)** observed 型分離は `probe()` の戻り型を新 dataclass へ変え、`AttestationProfile` は expected 専用として残す。`profile_sha256` は版付き projection で v1 preimage を保存する。
- **(P3)** 実装単位は 3 分割 — (A) policy module + producer/CLI/shell の入力面撤去 + schema 上限、(B) observed 型分離 + v2/legacy parser + hash projection、(C) trust boundary 検査群 + receipt exact key + T-453 silo。所有は素集合にならない箇所 (`schema_v2.py`, `env_attestation.py`) があるため、依存順に A → B → C の直列を既定とし、段 2 で分割可否を再検討する。
- **(P4)** 受入は計算ノードで全走 (runbook §7)。実装子の実走は親の全走を代替しない。

## 成果物影響 (`DW-G05`、実装しない場合)

| scope | 実装しないと成果物がどう変わるか |
|---|---|
| 1 権威一元化 | 受理集合を CLI 操作者が実行ごとに変えられ、台帳に比較不能な tolerance の trial が混在する |
| 2 入力面撤去 | 投入 script に `100` を渡すだけで環境同一性の検査が実質恒真になり、certified 受理が無検査になる |
| 3 observed 型分離 | sentinel `100.0` が expected 側へ漏れれば受理帯が `[0, 2*median]` へ広がり、certified 選択が未証明環境の測定を受理する |
| 4 schema 上限 | `100.0` が schema を通り続け、恒真値が artifact として登録可能なまま残る |
| 5 trust boundary 検査 | 非 policy artifact が取得時 gate と実行時 guard を通り、台帳に偽の pass receipt が残る |
| 6 T-453 | silo ladder の `all_pass` だけが広い median 受理集合を維持し、同じ観測に canonical receipt と異なる verdict を台帳へ記録する |

## 不変条件

- 正しさゲートを緩めない。既存テストの期待値を反転・緩和・skip・削除しない。
- 凍結 bytes (`FROZEN_MANIFEST`)・registry の calibration path/SHA・`contract_sha256` を動かさない。
- issuer の独立比較実装は独立のまま (D155 決定 2)。共有するのは policy 数値だけ。
- 歴史 artifact は parse 可能に保ち、current admission からは外す。恒真化・削除で処理しない。
