---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2236-ledger-refresh
seq: 1
title: [T-2236] 受入所要時間台帳を実測 JUnit から再生成した — 既存生成器へ refresh mode (凍結 8 suite 据え置き・それ以外を全再生成) を足し、24379 entry / 被覆 99.16% へ (コード + テスト + 台帳 + docs、branch worktree-dev-wave-t2236-ledger-refresh、変異 matrix = baseline PASSED・9/9 KILLED・等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「受入の `acceptance_duration_ledger.json` を実測 JUnit から再生成し、新設・改名 node へ追随させる。入力は
  2026-09-17 の受入 shard 成果物で値を合成しない。既存の生成器を使い新設はしない。動機は shard-0 = 344〜349 秒、shard-1 =
  234〜245 秒、shard-2 = 201〜212 秒の約 140 秒の偏り (均等化の目安 267 秒、300 秒達成の保証ではない)。再生成後に受入
  1 走で shard 別 wall を実測して before / after を記録する。Codex author (D95)。scheduler の新設・test 隔離基盤は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2236-ledger-refresh/README.md`。設計判断は
  {{D:acceptance-ledger-refresh-mode}}。実装 commit `363e79b10` (Codex author)。
- **段 1 の実測で原因を分解した。** 入力走 `d3ebafc0…` (06:31、main 相当、0 fail / 0 error) を現行台帳で解析すると、台帳予測の
  shard 負荷は 5701 / 5700 / 5700 秒で均等なのに実測の直列和は 8852 / 4433 / 4519 秒。差 3151 秒 (shard-0) の内訳は既知 node
  の値の陳腐化 2932 秒 + 未登録 219 秒で、主因は凍結 8 suite の外 (`test_s8b_oracle_driver.py` +2126 秒、
  `test_s8b_floor_campaign.py` +1289 秒)。既存 2 mode (全再生成 = T-1574 pin を壊す、`--add-only` = 既存値を保持) では
  主因を直せないと確定し、既存生成器へ refresh mode を足す方針を (P1) として段 3 に攻撃させた。
- **段 3 レンズ A / B は方針を反証しなかったが 3 点を訂正した。** (a) 被覆分子は 24379 でなく 24361 (stale 18 は分母外)、
  (b) 親 brief の「陳腐化が原因なので均す」は過剰断定 (D357: node 秒は仕事量の代理にならない) → 記録は観測値のみに、
  (c) land 競合時の契約が未定 → 段 4 で「main 現物を base に同じ JUnit で再走、落ちた node は名前と件数を記録」と定めた。
  レンズ B の「親の集計 script が consumer の `nodeid@group` fallback を再現していない」は再集計で影響 0 (fallback hit 0) を実測。
- **段 6 レビュー 2 本は must-fix 0 / GO。** nit 4 件 (parametrize id の ASCII 短名化・stdout count 名の mode 間差・
  `@real-repo` entry を死蔵と断定しない・親検算の「値の出所」行の強化) のうち親検算の強化だけ行い (before snapshot の
  426 値との照合へ)、他は記録に留めた。parametrize id (`[orchestrator/tests/test_critic.py::]`) は変異 harness が
  完全一致で中継できたので fix 不要と判断した。
- 実走: 焦点走 5 file (ledger test・schedule_order・a1_headline・run_tests_shards・t1998) **400 passed / 65 秒** (計算ノード)。
  親の検算 18 項目すべて OK (凍結 426 行 byte 一致・T-1574 の 8 hash と 12 値と removed 不在・`nodeid_count` 24379・
  非凍結 = JUnit map 23953・重複 0・failed 0・被覆 24361 / 24568・非凍結 stale 0・canonical 再描画一致)。
- **変異 matrix (固定 commit `363e79b10` の使い捨て worktree、runner は `run_tests.py --force-dispatch` で ledger test 1 file)。**
  probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走。本走は baseline PASSED、負例 9 件 (M1〜M9) すべて KILLED で
  期待 node と観測 node が完全一致 (M1 = 11 node、M2 = 8、M3 = 3、M4 = 9、M5 = 11、M6 = 1、M7 = 1、M8 = 9、M9 = 1)、
  等価変異 M0 (docstring) は SURVIVED、MISMATCH 0、anchor は全件 1 箇所。wrapper の共有木事後検査は 2 走とも並行 session の
  churn で rc=125 だが、固定 commit の隔離 worktree で取れた測定は有効 (10/10 recorded)。
- **受入 after (1 走の観測値、D357 により改善主張はしない):** session `895f300a…` (tip `31c92c151`、24530 passed / 67 skipped、
  child-green)。shard 別 wall = **337.9 / 249.2 / 204.1 秒** (before 4 走は 344〜351 / 236〜245 / 201〜211 秒)。差は 10% 未満で
  「変化なし」の域。**台帳の再生成だけでは偏りは縮まらなかった** — refresh 後台帳で割付器 (LPT) が置いた予測負荷は
  7502 / 5328 / 5328 秒 (均等なら 6053 秒) で、shard-0 は 25 file / 3908 node が 4 つの衝突 xdist group
  (`campaign-repository-scan` / `real-repo` / `s8c-predicate-snapshot` / `s8c-preregistration-candidate`) で 1 連結成分に連結されて
  おり、その成分 (予測 7502 秒、実測 8569 秒) だけで均等負荷を超える。陳腐化した台帳はこの床を「均等」に見せていただけで、
  正確な重みで初めて数値として露出した。床を下げる手 (成分単位を file から node へ、大 file の real-repo node の分離) は
  scope 外なので数値付きで次の一手に起票した。
- 残存 (scope 外、記録のみ): 凍結 8 suite は stale 18・未登録 207 のまま (D1152 の帰結、T-1903 が未実施の限界。shard 間の
  残差は最大 563 秒 = 均等負荷 6046 秒の 9.3% 見込み)。`--coverage-against` は collection 出力の `IZANAGI_GROWTH_HOLD_V1`
  marker 行 (`::` を含む) を nodeid と誤読して rc=2 になる (本 wave は marker 行を除いた一覧を渡した)。1 走入力は割付の
  頑健性を保証しない (同一 node の time が走間で 2 倍動く)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra` / `medium`)。親の実測は集計 script 4 本、
  焦点走 1 本、変異 2 走 (probe 11 request + 本走 11 request)、受入 1 走。

## 次の一手差分

### 完了

- [T-2236] `--refresh` mode を既存生成器へ足し、`d3ebafc0…` の 3 shard JUnit から台帳を再生成した (24379 entry、被覆
  24361 / 24568 = 99.16%、凍結 8 suite は据え置き、T-1574 pin 不変)。after の shard 別 wall は insight に観測値として記録。
  remaining: none
  base: 80e20e0d9a9c9d0eb38b773df52b9b0907aebefec8b113194be53cbd2e60b368

### 新規

- {{T:acceptance-shard-component-floor}} **P2・新規**: 受入 shard-0 の床は台帳でなく連結成分の粒度にある。after 走
  (`895f300a…`) で shard-0 = 25 file / 3908 node が 4 つの衝突 xdist group (`campaign-repository-scan` / `real-repo` /
  `s8c-predicate-snapshot` / `s8c-preregistration-candidate`、`conftest.py` の `REAL_REPO_RESOURCE_NODES` が `real-repo` を動的付与)
  で 1 成分になり、台帳予測 7502 秒 / 実測 8569 秒 (均等なら 6053 秒)。上位は `test_s8b_oracle_driver.py` 2804 秒 (147 node)、
  `test_s8b_floor_campaign.py` 2368 秒 (528 node)。`allocate` が file を成分単位にするため、real-repo node を 1 つでも含む file が
  file ごと成分に入る。候補: (a) 成分単位を file から node へ (real-repo node だけを成分に置き、同 file の他 node を別 shard へ
  出せるか、順序依存の検査が要る)、(b) 大 file の real-repo node を別 file へ分離。どちらも受理集合を変えず D358 (real-repo の
  直列化は維持) を守る設計が要る。一次資料は `output/insights/2026-09-17/t2236-ledger-refresh/README.md`。Codex author。
- {{T:ledger-coverage-marker-lines}} **P3・新規**: `tools/update_acceptance_duration_ledger.py --coverage-against` が
  `pytest --collect-only -q` の出力に混じる `IZANAGI_GROWTH_HOLD_V1 {…"node_id":"…::…"}` marker 行 (50 行、`::` を含む) を
  nodeid と誤読して rc=2 になる。本 wave は marker 行を除いた一覧を渡して回避した。生成器側で `orchestrator/tests/` で
  始まらない行を読み飛ばすか、marker 行を別 stream へ出すかは要裁定。Codex author。
