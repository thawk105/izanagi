# 段 1 brief — 軸 driver の環境 3 定数を env_contract 解決へ寄せる

対象: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:76-78` の `ENV_TAG` / `CLK` / `NUMA`。
基準 commit `fe2a547`、worktree `.claude/worktrees/dev-wave-axis-env-contract`。

## 経路

`DW-C00` の軽量版に**該当しない** (正しさ防壁 = 計測 provenance の env-tag 境界に触り、
guard 新設で拒否側の受理集合が変わる)。段 2・3 と段 6 敵対レビュー 2 本を省かない。

## scope (in) — 各項に `DW-G05` の成果物影響

- **S1 定数の単一正本化**: `ENV_TAG` から `env_contract.lookup()` を引き、`CLK` / `NUMA` を
  contract 由来にする。
  *実装しない場合*: contract と driver が clocks/numactl の二重正本のままになり、contract 側の
  再校正が軸 campaign の WAL `payload` と bench launch prefix に反映されず、同一 env-tag を
  名乗る試行台帳の値が非整合になる。
- **S2 実行機矛盾の fail-closed guard**: 解決 env_tag と実行機が矛盾する場合、計測へ進まず停止する。
  *実装しない場合*: Pegasus 計算ノード (`bnode*`、`buildcache` の重処理拒否が効かない層) で本 driver を
  回すと、2100 clocks/µs の機械の計測が `env_tag=linux-baremetal` / `clocks_per_us=1800` として
  既存 campaign `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl`
  (実測: 全 record `linux-baremetal`、`commit` 2 件) へ追記される。certified 選択と proof chain が
  別環境の値で汚染され、`campaign_id` に env_tag が無いため分離もされない。

## scope 外 (別 ID / 裁定パッケージへ)

pegasus を本軸の runnable env にすること (D59 の 4 条件と env スコープ付き campaign identity が要る。
`DW-G04` の発火 artifact path / 計測 ID を書けない)。兄弟 driver 11 本の同型定数 (s1/s2/s6/s8a/p2_2/
demo/p3_kickoff/p3_s4_red/backoff_* — 報告済み・凍結済みの計測条件)。`p2_2.ENV_TAG` を machine-pin 名として
import する s8b 系の恒真性。

## 不変条件

- `env_contract.py` を改変しない (`silo_ladder_rung1._runtime_module_paths` の source-hash pin 対象)。
- linux-baremetal の解決結果は現行と等価: `("linux-baremetal", 1800, ["numactl","--interleave=all"])`。
- 既存 campaign の `campaign_id` と `campaign.lock` の正準 pre-image を変えない。
- 受理集合を広げない — 本 wave は拒否を足すだけで、新しい実行可能 env を足さない。
- 正しさゲートを緩める変異を採らない (規律 2)。テストを甘くして緑にしない。

## provisional 裁定 (親の暫定判断であり段 3 の攻撃対象)

- **(P1)** 実行機判定は既存 `site_policy.current_site()` を seam に使う。cygnus を積極同定できない
  非対称 guard (Pegasus を否定できれば偽タグは塞がる) で足りるとする。**恒真 assert にならないこと**を
  含めて攻撃対象。
- **(P2)** `--env-tag` 等の env 選択 CLI は追加しない。`ENV_TAG` は module 定数のまま単一正本とし、
  pegasus 側の期待値 (numactl 空 / 2100) は resolver の単体テストで固定する。
- **(P3)** guard の発火点は `run_campaign` 呼出し前 (`p3_s4_loop_trigger_gating.py:388` 直前)。
  reject 経路 (`record_diff_reject`、:288/:296/:307) は計測しないため guard 対象外でよい。
- **(P4)** `p3_s4_loop.py:218` の `env_tag: str = ENV_TAG` 既定は scope 外 (trigger 側は常に明示渡し)。

## 前提実測 (brief 前に確認済み・攻撃対象)

- `env_contract.lookup("linux-baremetal")` = clocks 1800 / numactl `("numactl","--interleave=all")` で
  現行ハードコードと一致。`lookup("pegasus")` = 2100 / `()` / `attestation_mode="required"` /
  `single_process=True, allow_resume=False`。
- 先例 (`s8b_floor_campaign` / `s8b_oracle_driver`) は CLK/NUMA を contract から取るが、machine-pin は
  `from campaign.p2_2 import ENV_TAG` の literal であり実行機を同定していない。
- ユーザーが阻害要因に挙げた `test_s1_direct_comparison.py:655` と `test_campaign.py:2213-2214` は
  それぞれ `S.NUMACTL` とローカル literal を pin しており、**本 driver の定数を pin していない** (反証)。
- `s1_direct_comparison.py:483` は本 driver を import するが `check_syntax_contract` しか使わない。
  S-1 の報告済み計測条件は本変更の影響を受けない (反証)。
- `docs/phase3.md` 上 8c は未着手・条件付き。「8c supervisor が駆動する軸」は前向きの位置づけ。

## 成果物の形

production 1 ファイル (`orchestrator/campaign/p3_s4_loop_trigger_gating.py`) と
テスト 1 ファイル (`orchestrator/tests/test_p3_s4_loop_trigger_gating.py`)。
positive control = linux-baremetal 解決が上記 3 値に一致し `run_campaign` へその値で渡ること。
negative control = PEGASUS_COMPUTE / PEGASUS_LOGIN site で計測前に fail-closed。
過剰拒否検出の正例 = 非 Pegasus site では現行どおり通過すること。

## 並列分割方針

編集ファイル所有が 2 ファイルで閉じるため実装単位は 1。並列分割せず単一 Codex `role=author` に渡す。

## 受入・実測の環境

実行機は pegasus02 (login)。pytest・build・変異本走はすべて gen_S 計算ノードへ qsub し、
login では静的検査と子の起動だけ行う。measurement は本 wave では行わない (計測値を生まない変更)。
