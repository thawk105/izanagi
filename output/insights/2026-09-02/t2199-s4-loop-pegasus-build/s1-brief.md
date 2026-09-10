# 段 1 brief — T-2199 段 4 loop のビルド系を Pegasus で通す

## scope

段 4 loop (`orchestrator/campaign/p3_s4_loop.py`) の 1 iteration が Pegasus 計算ノードで
build へ到達し、既存 gate が terminal verdict を返すところまでを通す。編集面は
`tools/pegasus/` 配下の job script / probe と、その登録に要る既存 registry・内容走査テストだけ。
`orchestrator/campaign/**` は読むだけで、1 byte も変えない。

## 確定済みユーザー裁定 (この wave では議論しない)

- `orchestrator/campaign/p3_s4_loop*.py` は稼働中の t2145 wave の所有。触る必要が出たら止めて報告する。
- 絶対規律 1: 計測用ビルドから trace をコンパイル時に完全除去する。ランタイム分岐にしない。
- 実行場所の択一 (Pegasus 移植 / `linux-baremetal`) は技術判断であり、ユーザー裁定を待たない。
  ただし凍結 policy か人間所有の欄を変える必要が出たら止めて返す。
- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外 (DW-G05)。

## 親の provisional 裁定 (割れうる前提 = 段 3 の攻撃対象)

- (P1) **引数の「正式採用に要る 4 前提が未了」は、少なくとも env 登録の層では反証されている。**
  `orchestrator/campaign/env_contract.py` の registry に `pegasus` g1 / g2 が実在し
  (`clocks_per_us=2100`、`attestation_mode="required"`、`single_process=True`、
  `calibration_ref` 束縛)、`docs/pegasus-runbook.md` も 2026-08-01 時点で「登録自体は完了している」
  と書いている。残る実差は、段 4 loop が `ENV_TAG = "linux-baremetal"` (同 file 111 行) を固定し
  Pegasus 契約を引く経路を持たないことである。段 4 で再裁定する。
- (P2) `supply=preprocess-failed` の原因は環境側 (compiler 選択・include・argv) であって
  gate の受理集合ではない。`condition_meaning_gate.py` を変えずに job script 側で解ける。
  **反証されたら実装せず停止して報告する** (gate は編集面の外)。
- (P3) 実行場所は Pegasus を採る。cygnus (`linux-baremetal` = 研究室共有 Dell R760、D59) に
  依存する研究設計をしないのがユーザーの既定方針であり、新規 evidence の既定先は Pegasus。
  ただし「片方でしか出来ない」とは結論しない。根拠は段 2 で両側の費用を実測して書く。
- (P4) 段 4 loop が宣言する env_tag と物理実行環境が一致しないことは、block 理由にしない。
  結果に既知の制約として明記すれば足りる。**ただし Pegasus 上の throughput を
  `linux-baremetal` の測定値へ混ぜない** (D59 不変条件)。

## 不変条件

- gate の受理集合・閾値・pin・compiler を、測定の意味を変える方向へ差し替えない。
- 新しい process 起動点は `orchestrator/tests/test_ccbench_spawn_sites.py` の
  `test_reviewed_process_launch_inventory_is_recursive_and_exact` が exact に走査する。
  既存義務の充足であって gate の新設ではない。
- 実測は計算ノードへ dispatch する。login node で計測しない。単独性は計測ノード上で確認する。
- 凍結成果物の bytes を変えない。変える必要が出たら停止して返す。

## 成果物の形

1. `tools/pegasus/` の job script 1 本 (+ 必要なら probe)。offline 依存の配置、compiler 選択、
   configure、段 4 loop の 1 iteration 起動までを job 内で完結させる。
2. 実測 receipt。停止点が `preprocess-failed` より先へ進んだこと、または terminal verdict。
3. insight 1 本。択一の根拠 (Pegasus / linux-baremetal 双方の実測費用)、停止点の連鎖、主張の境界。

## 並列分割

- 段 2: read-only codex 1 本 — preprocess 失敗の code path 特定、登録簿の pin 閉包、択一の材料。
- 段 3: 敵対 2 本 — レンズ A = 規律 1/2 と gate 受理集合の弱体化、レンズ B = 択一の根拠と主張の境界。
- 段 5: Codex `role=author` 1 本 (D95、実装面)。段 6: review 2 + fix + 変異 + 受入。

**軽量版は採らない。** 実行場所の択一が割れており (DW-C00 の「設計択一が割れる」)、
編集面が正しさ防壁 (condition gate) の隣に接する。段 2・3 と段 6 の review 子を省かない。

## 受入・実測環境

受入全走は計算ノードへ dispatch (`tools/pegasus/dispatch_compute.py --task tests`)。
実測は Pegasus 計算ノード。所在は worklog、機体固有情報は `docs/pegasus-runbook.md`。
