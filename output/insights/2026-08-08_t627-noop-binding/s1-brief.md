# 段 1 brief — [T-627] activation 遷移述語を (generation, contract hash) 同一入力束縛で実装する

wave: `dev-wave-t627-noop-binding` / branch `worktree-dev-wave-t627-noop-binding` / 基準 `cf90afcc`

## 確定済みユーザー裁定 (逐語裏取り済み)

- `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §45:
  「**[T-627] = 次点 (b) generation + contract hash の同一入力束縛で実装 wave 起票可**
  (T-657 の活性化より前に入れる)」。
- (b) の原文択一 (`docs/archive/worklog-phase3-0807-294-295.md` の [T-627] 項) =
  「generation と contract hash (`GenerationEntry`) を**同一入力で束縛**し `is_valid_successor` と
  合成する」。(a) の数値 mapping 純述語は contract rollback を素通しするため却下済み。
  旧裁定 (c)「実 schema 確定まで置かない」は [T-529] の land で停止条件が解消し、本裁定が supersede する。
- 規則本体は D228 = 「全 env の generation delta ∈ {0,1} かつ少なくとも 1 env が +1」。
  D228 は**実装形を固定していない** (「実 record schema と併せて別途裁定する」)。本 wave がその実装形である。
- env 集合の変化は [T-628] (a) で activation では永久拒否。既存の exact 一致検査が担う (本 wave では触らない)。

## 段 1 実測 (前提の裏取り、`s1-probe.py` + 実編集・即時復元)

現行 `validate_activation_records` に合成 registry と合成 chain を渡した結果:

| ケース | 現状 | 期待 |
|---|---|---|
| serial 1 単独 | ACCEPTED | ACCEPTED |
| no-op (全 env 据置) | **ACCEPTED** | REJECTED |
| 正常前進 (+1, 据置) | ACCEPTED | ACCEPTED |
| **相殺 (+2, −1)** | **ACCEPTED** | REJECTED |
| skip 単独 (+2) | **ACCEPTED** | REJECTED |
| downgrade 単独 (−1) | **ACCEPTED** | REJECTED |
| 3 record 連鎖の途中 no-op | **ACCEPTED** | REJECTED |

- **純増検出力 = 遷移クラス全体。** 性質で検索した結果、遷移を見る層は repo に一つも無い
  (`env_contract_activation.py` / `execution_guard.py` / issuer に `successor`・delta の遷移検査は 0 件)。
  issuer `tools/issue_env_contract_activation.py:206` は `validate_activation_records` を呼ぶので、
  **実効 gate は loader ただ 1 箇所**であり二重層の mask は生じない。
- **既存テストが現状の受理を明示的に pin している。** 実編集 probe (20 行) を入れて対象テストを
  dispatch 実走したところ 3 件が赤 (166 passed):
  `test_chain_intentionally_does_not_enforce_generation_delta_predicates` (no-op/skip/downgrade の
  受理を pin)、`test_downgrade_preserves_pegasus_g2_for_historical_resolution` (downgrade chain を
  fixture にした historical 解決テスト)、`test_issue_main_success_prints_required_head_and_inactive_warning`
  (issuer が no-op な serial 2 を発行する形)。**この 3 件の再著述は scope 内**であり、
  裁定が受理集合を狭めた結果である (テストを甘くする変更ではない)。復元後 bytes は HEAD と一致を確認済み。
- **DW-G04 の位置づけ**: 本番 chain は record 1 件のみ (`env_contract_activations/00000001.json`) なので
  連続 pair が無く、述語は**今日は発火しない**。ただし述語は既に結線済みの
  `validate_activation_records` (module 初期化の `_load_authority_snapshot` から毎回走る) の内部に置くため、
  `is_valid_successor` と同じ「結線済み・未発火」であり「consumer ゼロ」ではない。
  発火 artifact path = `orchestrator/campaign/env_contract_activations/00000002.json` ([T-657] が発行)。
  ユーザー裁定が「T-657 の活性化より前に入れる」と順序を指定しているため、この未発火は裁定済みの前提である。

## scope と成果物影響 (DW-G05)

1. **loader に遷移述語を新設** (`validate_activation_records` の chain ループ)。
   放置すると [T-657] の活性化時に no-op / skip / downgrade / 相殺の record が受理され、
   certified 選択・レポート・試行台帳の activation 参照から契約集合を一意に読み戻せなくなる。
2. **上記 3 テストの再著述 + 負例の固定**。`(+2, −1)` 相殺を必須負例として独立 node で固定する。
   放置すると検出力ゼロの gate が「no-op を拒否する保証」として台帳に残る ([T-624] の再発)。
3. **scope 外**: env 集合変化 ([T-628] 済)、issuer の独立検査追加、pegasus g2 の活性化 ([T-657])、
   durable receipt ([T-658] 見送り済)、contract 実体 rollback の一般対策 (D228 射程外)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 実装位置は `validate_activation_records` の chain ループ内 1 箇所。** issuer は同関数経由なので
  独立実装しない。→ 単一理由性が保てる (DW-M01)。
- **(P2) `is_valid_successor` との合成は registry 経由の推移で満たす。** 登録 sequence の隣接は
  `env_contract._validate_generations_without_bootstrap_fuse` (行 334-339) が module 初期化時に
  `is_valid_successor` で検証済みであり、遷移側は「変化した env の generation が exactly +1 かつ
  hash が registry の当該世代と一致」を要求すれば合成が閉じる。`env_contract_activation.py` から
  `env_contract` を import しない (現状の pure leaf 性と循環 import 回避)。
  **既知の弱点**: この推移は production catalog にのみ成立し、loader が受ける
  `registered_contracts` は呼び出し側が任意に作れる。ここは段 3 の攻撃対象。
- **(P3) 受理条件**: ① 全 env の `(generation, hash)` 対が据置なら拒否 (no-op)。
  ② 変化した env は `generation_new == generation_old + 1` かつ `hash_new == registry[env][generation_new]`。
  ③ 据置 env は許す (D228 の「過剰拒否にならない最小の強化」)。
- **(P4) 3 テストの再著述方針**: `test_chain_intentionally_...` は反転でなく**置換** (名前も含めて
  新しい受理集合を述べる)。`test_downgrade_preserves_...` は前進 chain (g1 → g2) で ever-active な
  g1 を historical 解決する形へ再 fixture する。issuer test は前進 record を発行する形へ。

## 不変条件

- 本番 record 1 件の load は land 前後で不変 (`lookup()` の返り値、`_ACTIVATION_HEAD_*` は変えない)。
- 凍結 bytes は変えない。`env_contract_activation.py` への pin は path membership のみで
  literal sha の byte pin は無い (`FROZEN_MANIFEST` 非収録、pin 閉包は handoff に列挙)。
- 実装子は code と test だけを編集し docs 編集と commit をしない。親は実装面を直接編集しない。

## 分割方針

実装は単一ファイル対 (`env_contract_activation.py` + `test_env_contract_activation.py`) に閉じるため
**段 5 は 1 単位**とする。段 2 プラン 1 本、段 3 敵対 2 レンズ、段 6 敵対レビュー 2 本。
受理集合が変わる wave なので `DW-C00` の軽量版は使わない。

## 環境

受入・実測は Pegasus 計算ノードへの dispatch (`tools/run_tests.py --force-dispatch`)。
段 1 実測は request `895929.nqsv` で成立を確認済み。受入全走の直前に
`tools/wave_land_window.py claim` を行う (並行 wave 2 本稼働中)。
