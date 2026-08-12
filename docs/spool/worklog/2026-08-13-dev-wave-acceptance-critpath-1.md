---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-acceptance-critpath
seq: 1
title: 受入全走の律速仮説 3 つを実験で潰し、計測系が ±9% 揺れることを実測した — 排他の置き換えは不採用 (docs のみ、branch worktree-dev-wave-acceptance-critpath)
---

## 本文

ユーザー依頼「受入全走のボトルネックを賢く解決してください。リワードハック禁止」の wave。
同じ依頼文で `dev-wave-t950-acceptance-floor` が並行稼働していたため、**t950 が scope 外として
裁定へ返した項目 2 (critical path の計測)** を lane に取った。編集面は素集合。

**結論から言うと、実装すべき改善は見つからなかった。潰したのは仮説の方である。**
3 つの候補を順に立てて、いずれも自分の実測で否定した。設計判断は
{{D:real-repo-group-stays-serialized}} と {{D:acceptance-wall-needs-repeated-runs}}。

**仮説 1「`@real-repo` 直列鎖が律速」— 否定。** tip 2310ea67 の全走で wall 112.66 秒、
鎖 100.97 秒 (44 node、うち 68.29 秒が 1 node) だったので、鎖が wall の 89% を説明した。
しかし因果実験が 3 本とも wall を動かさなかった。F (node 秒の 31% を占める
`test_s8b_oracle_driver.py` を丸ごと除外) = 113.07 秒、G (鎖の頭を持つ file を除外) = 112.97 秒、
**H (`--dist load` で直列 group を全廃 = 置き換えの最良ケース) = 116.63 秒**。
G では鎖の長さが 106.70 秒のまま変わらず、68 秒は「group 内で最初に走った node が払う
共有 `verify_receipt`」で特定 node の性質ではないと分かった。

**仮説 2「排他を保ったまま並列化できる (reader/writer ロック)」— 正しさ側で否定。**
段 2 プランは 44 node を file:line で当たり「全て reader、writer 0」と判定し、
親も荷重の大きい 4 系統を自分で確認した (`applied` が `nullcontext`、layout は
`tempfile.mkdtemp()`)。**しかし段 3 レンズ A が反例を出した。** `git status` を
`GIT_OPTIONAL_LOCKS=0` なしで実行する経路が複数あり、read-only に見える node も
git の optional index lock を書く。同 repo 内の別経路はこの抑止が必要だと明記し、1 箇所は
実際に抑止している。さらに正本リストの閉包漏れは 1 件ではなく、**実 git object を書く node**
と共有 submodule の common-dir を変更する canary が list 外にあった。
レンズ B も独立に「実装するな」と結論した (下界に反する見積り、fixture 重複、hang の診断契約なし)。
**両レンズが独立に同じ結論へ達したので、段 5 の実装子は起動していない。**

**仮説 3「worker 数が throughput の頂点を過ぎている」— 変動に埋もれて否定。**
最初の測定では 24 本 105.51 秒 < 48 本 112.66 秒に見えたが、これは 12 本走と 24 本走を
**同時に投入した**ための相互干渉だった (同走の赤 3 件も、自分の dispatch receipt が
`output/pegasus-dispatch/` へ落ちた既知の汚染で、worker 数とは無関係)。
逐次・条件交互で取り直すと 48/32/24 本は 112.17・112.08・117.80 / 109.93・99.53・99.30 秒で、
**同一条件の 2 走が 19% 開いた。**

**本 wave の最大の成果はこの変動幅そのものである。** 受入 wall の観測域は同一 tip で
99.3〜117.8 秒 (±9%)。**1 走同士の比較で 10% 未満の改善を主張することはできない。**
これは本 wave の当初解析だけでなく、1 走の値で律速を同定してきた一連の判断に掛かる。
併せて、node 秒合計が worker 12/24/32/48 本で 1,542/2,261/2,828/3,344 秒と単調に増えることも
実測した — **48 worker の duration は競合で約 2 倍に膨らんでおり、仕事量の代理にならない。**

**現時点で最もよく合うモデル**は「wall ≈ 最長 node + 27〜41 秒」で、最長 node は全 7 走で
同一の 1 本 (`test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment`、
61.6〜90.0 秒)。**このテストは単独走では 6.81 秒**であり、全走で 10 倍以上になるのは module
fixture `benchmark_snapshots` (単独走 49.80 秒) を 3 worker がそれぞれ払うためである。
ただし共有化しても payer 1 本が残るので wall は動かない。動かすには payer 自身を安くする必要があり、
それは実 repo を hardlink なしで複製している点に帰着する。

**親自身の誤りを 4 件撤回した。** (i) 「writer 7 node = 21.20 秒」の分類は根拠が
conftest のコメントだけで、実装と乖離していた。(ii) 「RW ロックなら 89.5 秒、hoist なら 68.3 秒」の
見積りは H が両方とも到達不能と示した。(iii) 「wall は収集 6.8 秒 + 鎖 101 秒でほぼ説明され残差 5 秒」は
偶然の一致で、鎖は wall の説明にはなるが原因ではない。(iv) node 秒を仕事量の代理に使った議論は
worker 数依存のため全て信頼できない。

副次的に t950 の (P3)「oracle driver の 15 node は flock 待ちか」を決着させた = **待ちである。**
同 file 単独・worker 1 本では 94 node が 76.25 秒で重い node は 1 本 (55.04 秒) だけだが、
48 worker 全走では 16 node が各約 64 秒 = 1,027 秒になる。差の約 950 秒は
`real_repo_receipt_memo` の排他 flock 待ちで、CPU 仕事ではない。ただし F が示すとおり wall には効かない。

工数は Codex 3 本 (plan 1・consult 2、いずれも `gpt-5.6-sol` / `gpt-5.6-luna`・reasoning=max)、
計算ノードの全走 11 本。実装子・fix 子・変異は裁定により起動していない。

## 次の一手差分

### 新規

- {{T:benchmark-snapshots-payer-cost}} **P1・新規**: 受入 wall の最長 node
  (`test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment`、
  全走 61.6〜90.0 秒 / 単独走 6.81 秒) の実体は module fixture `benchmark_snapshots` の
  snapshot 構築 (単独走 49.80 秒) である。実 repo を hardlink なしで複製しているため
  **commit 数に比例**する。hardlink / object 共有で payer 自体を安くすれば
  「wall ≈ 最長 node + 約 30 秒」モデル上は wall が動く唯一の場所。
  検証は {{D:acceptance-wall-needs-repeated-runs}} に従い 3 走以上の中央値で行う。
- {{T:real-repo-closure-gaps}} **P1・新規**: `REAL_REPO_SERIAL_NODES` の閉包漏れ。
  `test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control` は
  fixture 経由で実 submodule source を読むのに正本外 (親が裏取り済み)。
  段 3 レンズ A はさらに、実 git object を書く node と共有 submodule common-dir を変更する
  canary が正本外にあると指摘した。**速度と無関係に排他の穴であり、fail-closed 側の実バグ。**
- {{T:git-optional-locks-missing}} **P2・新規**: `git status` を `GIT_OPTIONAL_LOCKS=0` なしで
  実行する経路が 2 箇所あり、read-only 検査が optional index lock を書く。
  同 repo 内の別経路は抑止が必要と明記し、1 箇所は実際に抑止している。並列化の可否と独立に揃える。
- {{T:receipt-memo-flock-wait}} **P3・新規**: `real_repo_receipt_memo` の排他 flock 待ちが
  48 worker 全走で約 950 node 秒。wall には効かない (因果実験 F で確認) が、
  worker slot を占有し測定値を歪める。payer を早く走らせる順序付けで消える可能性がある。
- {{T:benchmark-snapshots-cross-worker}} **P3・新規**: `benchmark_snapshots` の worker 跨ぎ
  重複構築 (3 worker × 約 50 秒)。wall は動かないが node 秒を約 165 秒減らす。
  先例は `real_repo_receipt_memo` の session cache + flock。
  {{T:benchmark-snapshots-payer-cost}} を先に済ませると効果が小さくなるので順序に注意。
