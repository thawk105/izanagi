---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2697-b4-binary-placement
seq: 1
title: [T-2697] 調達済み B-4 床値バイナリの配置規則を既存 env スコープ規約の兄弟に定め、ignored 複写で実装した (コード + docs、branch worktree-dev-wave-t2697-b4-binary-placement、変異 matrix = baseline PASSED・8/8 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「B-4 凍結 spec の `artifacts[].binary_relpath` が解決できる場所へ、調達済みの
  候補・参照バイナリを配置する規則を決めて実装する。tracked 化・再 build・複写のどれを採るかが
  未定。本題の配置規則と実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **配置規則は発明せず、既存規約の兄弟に収めた。** `binary_relpath = output/env/<env_tag>/binaries/<binary_sha256>`。
  一次資料は `output/insights/2026-09-16/t2697-b4-binary-placement/README.md`。
- **段 2 plan は新しい namespace `output/b4-binaries/` を提案し、親が段 4 で退けた。**
  `s8b_floor_campaign.py:7669` が既に同じ種類の物を `env_scope_dir(env_tag)/binaries/<sha>` へ
  置いており、`output/env/pegasus/` には `calibration` と `profile` が並ぶ。新 namespace は
  「campaign 横断の実験補助 store」という新分類の新設を要し、依頼が禁じた一般化に当たる。
- **この発見は段 2 の後に出た。** plan 子の prompt には間に合わず、親が段 3 レンズ B へ射影して
  突き合わせさせた。段 1 の閉包に「同種の物の既存置き場を production コードで引く」が無いことが
  原因である ({{F:existing-placement-rule-not-searched-in-stage1}})。
- **段 3 レンズ B が規約統一の理由を限定した。** B-4 対照対 driver は `s8b_floor_campaign` を
  通らない (親の実測で参照 0 件、consumer は `p3_b4_floor_artifact_issuer.py` だけ)。統一の理由は
  実行経路の共有ではなく、同種の物に 2 つの置き場を作らないことである。**path の env 成分は
  消費側が照合しないので、環境整合の gate と説明してはならない。**
- **tracked 化しなかった。** 消費側は binary にだけ HEAD blob 束縛を要求せず、レンズ A の実測では
  repo の tracked executable 58 件に ELF は 0 件だった。**レンズ A の要求どおり凍結の限界を明記した** —
  凍結するのは path・期待 sha256・receipt であって bytes の可用性ではない。判断は {{D:b4-floor-binary-placement}}。
- **生死確認を実装前に置いた。** repo 外の現物 binary へ消費側検査を直接かけ、
  `assert_binary_sha256` と `_assert_no_trace_symbols` が通ることを先に確かめた。
  欠けているのは repo 相対 path に在ることだけだと分かり、依頼の枠組みが実測で裏づいた。
- **段 6 レンズ A が受理集合の拡大を 1 件見つけた。** 配置用コピーへ `binary` key を存在確認なしに
  書き込むと、exact key 集合で拒否されるべき欠損 record が補修されて通る。規律 2 に触れるので
  fix で閉じ、変異 M8 として機械で守った ({{F:transport-copy-repairs-missing-required-key}})。
  恒真テストも 1 件見つかった (新規 `git init` fixture では untracked 判定が必ず緑)。
  レンズ B は must-fix 0 で、API 照合・所有境界・ignore 射程を現物で確認した。
- **変異走行が 1 回目に 6/8 で中止した。** 親が実データ 1 走で置いた 701KB の binary が、
  `.gitignore` の行を消す変異 M7 の下で untracked として現れ、harness の走行前 clean-tree 検査が
  全体を止めた。配置物を退けて再走した ({{F:placed-artifact-breaks-ignore-removal-mutation}})。
- **単一理由性の指摘は半分が実測で反証された。** レンズ A は M1/M3 と M5/M6 が同じ node で落ちると
  したが、probe 走で M1 と M3 は node 集合が異なると分かった。M5/M6 は 7 node 一致だが、
  赤の理由は別である (M5 は `record.binary が絶対 path でない` だけ、M6 は
  `store_path が content address と不一致` が 14 件)。
- **real だが scope 外**として 4 件を残した。配置経路が現行 policy 一致を要求するため古い record を
  配置できないこと (緩めず主張の射程を狭めた)、ignored file は merge で他 checkout へ移らないこと、
  `store_binaries` の docstring と実装の不一致 (並行 wave 所有につき不可触)、ELF テストの `g++`/`nm` 依存。
- 工数: codex 子 7 本 (plan 232 秒 / 8 call、consult 2 = 327 秒 / 18 call と 189 秒 / 7 call、
  author 265 秒 / 10 call、review 2 = 172 秒 / 6 call と 143 秒 / 6 call、fix 90 秒 / 6 call)。
  計算ノード job は変異 probe 2 本 (6/8 で中止 + M7/M8 の 2 件) と本走 1 本、provenance 監査 2 本。
- **受入全走は本 fragment 執筆時点で未実施。** 記録 commit と段 8 の commit を含む tip に対して
  段 9 の直前に投入する。

## 次の一手差分

### 完了

- [T-2697] 配置規則を `output/env/<env_tag>/binaries/<binary_sha256>` (git-ignored) と定め、
  `b4_binary_record.place_record()` と `place` サブコマンドで実装した。現物 701,760 byte を
  置いて消費側 4 検査を通し、冪等・ignored・非 tracked も実測した。
  remaining: none
  base: bc53d54a23bc836e7789337825ebb55c6678a248fb6cc01a5d6d8c58a8b8e7aa
