# 段 1 brief — dev-wave [T-419] (iii) 別 process の完全独立検証

branch `worktree-dev-wave-t419-iii`、起点 main `29ae9975`。

## scope

publish 済み較正 artifact を、**それを作った process の外から、bytes だけを入力に**判定する
独立 verifier を実装し、判定を再現可能な artifact として残す。対象 = [T-419] 着手条件 (iii)。

**scope 外 (名乗らない):** 較正の登録・活性化、`env_contract` の `calibration_ref` 切替、
`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の空化 ((iv))、[T-529] 活性化権限、
final receipt の収集そのもの、取得経路の source acquisition proof、
benchmark 中/後の clock 窓 (D191 が明示的に射程外とした)。

## 確定済み裁定 (前提)

- D181 = 方式 α の取得手続きを identity に載せる。受理述語と `tolerance_pct` は変えない。
- D191 = 取得の自己整合検査は benchmark 前後の二重、publish 済み bytes は同一 process 内で再読。
  **決定 1「判定は canonical 述語を経由し、帯計算を再実装しない」は本 wave にも掛かる。**
  D191 の射程節が「別 process による完全独立の検証と、その判定を最終 receipt へ束縛すること」を
  未実装として返している = 本 wave の対象。
- (i)(ii) は成立済み。(iv) は本 wave の対象外。

## 前提実測 (2026-08-07、login node、repo 外の使い捨て probe)

| 対象 | 実測 |
|---|---|
| `registered/calibration-94a4b79fa31bba3c.json` | 別 process から canonical 述語 **pass**、content-address **一致**、schema v2 **ok**、48 samples、method = α (`k5/interval-ns50000000`)、`tolerance_pct=2.0` = 現行 policy |
| `registered/calibration-753f535a8d024727.json` | 同じ経路で canonical 述語 **fail** (既知の自己不整合)、content-address 一致、schema v2 ok、method = `proc-cpuinfo` |
| 両者とも v1 probe marker を含まない | `test_probe_output_v1_corpus_...` の exact 集合 (48 件) に触れない |
| job 892707 `calibrate_rc` | **0** (= `campaign.execution_guard` → `env_contract` の import 連鎖は計算ノードの `python3` で実際に通っている)。`docs/phase3.md` T-272 の「3.10+ module は certify 経路から呼べない」は少なくとも execution_guard 連鎖については現状に合わない |
| 既存被覆 (性質で検索) | `registered/` を列挙する test は 1 件も無い。`test_env_contract` は `REGISTRY` の 2 entry (= 旧 753f) しか見ない。**新較正 94a4 には現在ゼロの常設被覆**しかない |
| pin 閉包 (DW-O09) | `.py` からの pin は 753f のみ (`test_env_contract.py` ×3、`env_contract.py` ×1)。94a4 の pin は無い。`FROZEN_MANIFEST` (23 件) に calibration path は無い。`attempts/*/calibration.md` は exact 集合 pin あり (`.md` のみ)、`.json` は v1 marker を含むものだけが pin 対象 |

**純増検出力:** (a) 未登録だが publish 済みの artifact に対する判定 (現在ゼロ被覆)、
(b) content-address (filename ↔ bytes digest) の束縛 (既存 gate に無い)、
(c) 別 interpreter = 取得 process 内での policy 定数・述語の再束縛に免疫、
(d) 判定を**後からいつでも再計算できる** (in-process の判定は certify job を再走しない限り再現不能)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** verifier は `orchestrator/calibrator/verify_published.py` に置き、
  薄い entry `orchestrator/verify_published_calibration.py` を添える (`calibrate.py` と同型)。
- **(P2)** 判定 = 5 条件の**連言**。(1) bytes の sha256、(2) content-address 一致
  (`basename == "calibration-" + sha256[:16] + ".json"`)、(3) schema v2 validation、
  (4) canonical clock 述語 (`effective_clock_comparison_passes`、帯計算は再実装しない)、
  (5) policy identity (`tolerance_pct == effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT`)。
- **(P3)** 判定 artifact = `output/env/pegasus/calibration/verifications/<sha256[:16]>/…`、
  schema `izanagi/independent-published-calibration-verification/v1`。
  **job staging へ後から書き足さない** — 終了した job の成果物集合を事後に増やすのは provenance の捏造。
- **(P4)** 取得経路への結線は `certify_calibration.sh` が calibrate 成功後に**別 process として**起動する。
  calibrator 自身に自分の verifier を起動させる形は採らない (被検証者が検証者を選ぶことになる)。
  in-job の判定は attempt staging に書き、final receipt の manifest に載る。
- **(P5)** `collect_receipt.py` への明示 field 追加は本 wave では行わず裁定へ返す
  (final receipt の収集自体が別 blocker で、本 wave では実測できない)。
- **(P6)** 既存の in-process `published-self-comparison` は削除しない (D191 決定 2 と同型)。

## 不変条件

- 登録済み較正・`env_contract`・凍結 bytes・pin を **1 件も動かさない**。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を空にしない (それは (iv))。
- 帯計算を再実装しない (D191 決定 1)。診断値を受理判断に使わない (D191 決定 6)。
- verifier は 753f を **reject**、94a4 を **accept** する。両方を固定 vector にする。
- 受理集合の変化は「取得 job が publish 後の独立検証で赤なら job 全体が失敗する」縮小のみ。
  既登録較正・contract・pin は不変。**publish 済み artifact は削除しない** (D191 決定 4)。

## 成果物影響 (DW-G05)

実装しないと (iii) が閉じず、(iv) → 登録 → 活性化 ([T-529]) へ進めない。その間 certified 選択結果は
**旧較正 `calibration-753f535a8d024727.json` (自己不整合の既知例外) に束縛されたまま**で、
campaign 再開チェーンが止まる。実装すると、publish 済み較正の帯適合が第三者に再計算可能な
artifact になり、(iv) の前提が 1 つ埋まる。受理集合は上記の縮小のみ。

## 成果物の形

verifier module + entry + 判定 artifact schema + 実 artifact 2 件への実走判定 + 単体テスト +
certify script の結線 + 変異 matrix + 記録 (worklog / decisions / insights fragment)。

## 分割方針

段 5 は実装子 1 本 (verifier module + tests) と実装子 1 本 (certify script 結線) に所有を分ける。
段 6 は敵対レビュー 2 本 (レンズ = 恒真性/自己成就 pin、独立性の名乗り過剰)。

## 環境

受入・テストは計算ノードへ dispatch (`tools/run_tests.py`)。verifier の実走判定は JSON 1 本の
読取りなので login node で足りる (§7.0 の量基準)。実測値は測った checkout を併記する。
