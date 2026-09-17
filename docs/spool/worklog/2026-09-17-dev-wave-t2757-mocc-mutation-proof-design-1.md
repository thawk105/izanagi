---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2757-mocc-mutation-proof-design
seq: 1
title: [T-2757] mocc を変異探索面へ入れる前の auditor-live 相当の機械実証を設計した — 温度述語を proof の接続先候補にし、hot/cold の実行証拠と stock mocc の静的反例候補を固定、後続は 2 wave (docs のみ、branch worktree-dev-wave-t2757-mocc-mutation-proof-design、実装面 0 byte)
---

## 本文

- ユーザー依頼は「mocc を変異探索面へ入れるために D579 が要求する、独立の auditor-live 相当の機械実証を設計する。着手直前の
  local main から fresh worktree を作る。固定するもの = hole 位置 (cc/mocc/transaction.cc の EVOLVE-BLOCK 候補)、auditor 入力、
  X/P/I・hot/cold lock の被覆、陽性/陰性 control と期待拒否。後続実装者がそのまま使える形。Silo 版の auditor-live 実証を再導出の
  出発点にする。設計完了で変異探索を解禁しない。チェックリストの再掲に留まるなら『実証 wave の plan 段へ統合』と結論に書く。
  規律 2 を緩めない。本題の設計だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (設計確定、実測未了、探索・pin 前進・軸採用は未解禁)。** 一次資料は
  `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md`。設計判断は {{D:mocc-mutation-proof-design}}。
  コード・patch・テスト・driver は書いていない。`docs/phase3.md` は編集していない (準備 T の進捗は本台帳末尾が正本)。
- **再掲に留まらない (純増あり)。** 既存被覆 = T-2294 (D1686) の X/P 計装・負例 3 本・compute 14 check。純増 = hole 位置の候補比較と採用
  (温度述語 4 site → file-scope helper の 1 hole、proof の接続先候補であり正式軸ではない)、hot 経路の実行証拠の欠落 (T-2294 の 6 走は
  温度述語 false の記録のみ) と負例による機械化 (hot 専用負例 = update の早期 w_lock 直後に unlock、publish 前に `rwlock_.w_lock()` で
  直接再取得、blind UPDATE 1 操作の workload `ycsb_rratio=0, ycsb_rmw=false, ycsb_max_ope=1`)、36 走の matrix (受入必須 / 観測のみ)、
  同一性 4 比較と計装 patch の `#line` 再生成、auditor.md の mocc 節 (既存型番号の mocc 説明) と n=1 の 3 候補、gate の鍵 (template /
  軸 module の登録 + consumer 束縛の対照。EBS 所属は mocc で常時 true なので使わない)、I 行の除外根拠、pin との境界。
- **親 brief の誤り 5 件を段 3 が訂正した。** (1) 「hot/cold は正しさの入力ではない (torn read は validation で必ず捕まる)」は不成立 —
  cold 読みは counter 検査 (322) → body 読み (347) → 版の再読 (350) の順で、validation は版 (1010〜1013) の後に counter (1024) を読む。
  writer の publish (1195) + unlock (1207) がその間に入ると両検査を通る (レンズ A)。(2) 「同じ鍵では恒真」は前件が常時 true であって含意全体の
  恒真ではない。(3) 「pin 非依存」→「現行 pin を前進させず実施できるが e9e477ca と patch sha に束縛される」。(4) 「1 thread は全 cold」→
  「温度述語 false と見なせる (code からの推論、abort 数は JSON に無い)」。(5) n=1 の A 候補 `thid_` / `result_` 読取は file-scope helper では
  未宣言識別子の指摘になる → `FLAGS_clocks_per_us` 読取へ。
- **stock mocc (RWLOCK 版) の静的反例候補 2 件を insight §3.2 に構造化した (還元判断: ユーザー確認待ち)。** (a) 上記の版/counter 別読みの
  観測間隙 — D2114 が未確定とする G2 anomaly 5/42 の根因候補 (仮説、T-1943 の 1 cell no-G2 は否定していない)。(b) hot 読みは cold 読みと違い
  `absent` を検査しない (341〜344 対 356〜364) — DELETE を含む workload で削除済み record を読みうる (YCSB では到達しない)。
  このため安全論拠は「既存防壁 (validation・CLL/RLL・X/P・write_set_ 登録) を骨格で固定し、その保存と発火範囲を実測する」に限定した。
- 親が現物で検算した plan / consult の主張: Options.cmake の universal 相乗りが `ccbench_add_protocol` → `ccbench_universal_definitions`
  (cmake/ProtocolHelpers.cmake:19〜29) で mocc TU に届く、U workload は `include/ycsb.hh:65〜73, 128〜133` で `Ope::WRITE` → `tx.update()`
  直接呼出、`patches/ledger.json` の entry は 1 (ability probe 専用)、`p3_s4_loop.py` の PIN は `511c9538` literal、EBS の 3 要素目が mocc。
- 段 2 plan (codex read-only) は温度述語の条件付き採用と F-b の限定、absent 非対称、P2 の鍵修正、n=1 の分離、36 走を起草。段 3 レンズ A
  (正しさ境界・恒真性) は must-fix 4 / should 3 / nit 1、レンズ B (実効性・整合) は must-fix 4 / should 4 で 2 wave 分割を推奨。段 4 で
  全所見 real・採用 (refuted 0)。逐語は insight の `verbatim/`。
- 段 2 に `--reasoning xhigh` を渡した (DW-S02 の現行値は medium、memory の古い値を引いた親の argv 誤り。launcher は受理、実害なし)。
  段 3 は medium。
- 受入全走は本 commit を含む tip に対して land 前に 1 回走らせ、結果は land の受領証 (job dir) に置く。
- 工数: codex 子 4 本 (plan 1、consult 2、review 1、全段 `gpt-6-astra`)。親の実測は現物検算のみ (build・compute なし)。

## 次の一手差分

### 完了

- [T-2757] mocc の auditor-live 相当の機械実証の設計を insight に固定した (hole 位置、auditor 入力、X/P/I・hot/cold の被覆、
  陽性/陰性 control と期待拒否、gate の鍵、2 wave 分割)。設計完了で変異探索を解禁しない。
  remaining: none
  base: 60e5312facffdd658a1968bd509b5ae994d06f84b3aa3b845c7ea5f8248ef076

### 新規

- {{T:mocc-proof-wave1-path-common}} **P1・新規** (D579、{{D:mocc-mutation-proof-design}} 項 3〜5・8): mocc の auditor-live 相当の
  機械実証 wave 1 (経路共通、template 不要)。`patches/broken-mocc-hot-update-unlock.patch` (update の早期 w_lock 直後に unlock、
  publish 前に `rwlock_.w_lock()` で直接再取得、abort 側は `unlockCLL()` 前に再取得、裸 directive は owner file に 1 回)、新 driver
  `orchestrator/campaign/s3_mocc_mutation_proof.py` (旧 driver・旧 JSON・14 check は不変)、36 走 (hot 0 / cold 21 / 既定 10 × 1 / 4 thread ×
  {stock-W、lockskip-W、perm-erase-W、early-unlock-W、hot-update-unlock-U、stock-U}) を計算ノードで実走、受入必須の走だけを check に対応
  (insight §7 の表)、新 JSON `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` に run ごとの実 argv・終了状態・certified を記録、
  登録簿 (materializer / condition gate / 裸 define / spawn_sites) の閉包。完了判定 = 新 producer の compute 実測で all_pass、hot 専用負例の
  完走 (timeout なし)、stock-U 対照 6 走 certified。Codex author (D95) + 変異事前登録。正式 template は含めない。設計正本 = insight §6〜§7・§12
- {{T:mocc-proof-wave2-template-binding}} **P1・新規** (D579、{{D:mocc-mutation-proof-design}} 項 1・3・6〜8。前提 = wave 1 完了と、
  温度述語の軸オンボーディング段階 A (人間承認) / B (敵対レビュー)): mocc の auditor-live 相当の機械実証 wave 2 (template 接続)。
  `patches/mocc-temperature-predicate-variant.patch` (file-scope helper の 1 hole、4 callsite、OFF 原文保存、Options.cmake universal 相乗り)、
  `orchestrator/campaign/axis_mocc_temperature.py`、計装 patch の template 版 (`#line` を template 適用後の論理行へ再生成、旧 patch は不変)、
  同一性 4 比較 (無 template↔OFF、OFF↔ON、計装なし↔あり、旧 pin↔候補は別 T)、DiffQuarantine 対照 (frame / outside-region (CLL/RLL・validation・
  X/P・write_set_ 登録 477) / hole-escape / malformed)、`.claude/agents/auditor.md` の mocc 節 (既存型番号の mocc 説明)、gate test (鍵 = template /
  軸 module の登録、consumer 束縛の対照 3 種)、fresh auditor n=1 の 3 候補 (lockskip diff = reject、`FLAGS_clocks_per_us` 読取 = reject、
  `!(temp < threshold)` = pass)。完了判定 = template に束縛された機械証拠と別記の n=1 素材。**緑でも探索・pin 前進を認可しない**。設計正本 =
  insight §5・§8〜§10・§12
- {{T:mocc-stock-observation-gap-probe}} **P1・新規** (D2114 理由節「mocc は確実な第 2 成功例ではない」、insight §3.2): stock mocc (RWLOCK 版、
  e9e477ca) の静的反例候補 2 件を実走で検証する — (a) cold 読みの counter 検査 → body 読み → 版の再読と、validation の版比較 → counter 読取の
  別読みによる torn read の commit (G2 anomaly 5/42 の根因候補)、(b) hot 読みの `absent` 非検査 (DELETE を含む workload のみ)。(a) は多 thread・
  hot key・小 value で確率が上がるという仮説を立て、payload lineage discriminator (T-1943 の道具) で読み値の出所を照合する。CCBench 本体の改変は
  D16 / D18 / D20 に従い insight に構造化、上流 PR は人間判断。wave 1 と独立に投げられる。成功しても失敗しても mocc の certified 昇格の判定は変えない
