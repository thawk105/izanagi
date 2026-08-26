---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1851-floor-retry-ordinal-axis
seq: 1
title: [T-1851] 床値の測り直し軸は、配線を塞ぐ 2 つの未見事実が出たため実装せず裁定へ返す (docs のみ、branch worktree-dev-wave-t1851-floor-retry-ordinal-axis、実装面の差分 0 のため変異 matrix 免除)
---

## 本文

D1032 (測り直しは耐久台帳の中の別の試行番号軸として置き、性能量に到達する前に理由を固定する) の
実装 wave。段 2 で plan を起草し、段 3 で異なる 2 レンズの敵対相談を並列で回した結果、
**D1032 の裁定時には見えていなかった事実が 2 件出た。どちらも機構を production で発火させる工程を
塞いでおり、正しさ防壁の意味を変える設計択一を含む。** 段 4 で「実装しない」と裁定し、
裁定パッケージとしてユーザーへ返す。実装面の差分は 0。

**未見事実 1 — 台帳の名前空間が現用の 2 つの protocol 世代を収容できない。** 台帳の path は freeze
SHA だけで決まる (`s8b_attempt_profile.py` の `registry_path`) 一方、genesis の binding は protocol
SHA を含み、台帳の全行は 1 つの binding を共有しなければならない。現用の床値 protocol は
`output/s8b-freeze/floor_protocol.json` (ccbench_pin `d706650c`) と
`output/s8b-freeze/floor-protocols/e576e9cd...--511c9538....json` (同 `511c9538`) の 2 つで、
**どちらも freeze `315b1eb8` を共有し、campaign は両方を索引して選択できる**。
D444 がこの namespace を「組ごとに 1 件・追加のみ」と定めているため世代は構造的に増え続ける。
未配線の現状では衝突しないが、配線した瞬間に後の世代の campaign が binding 不一致で拒否される。
測り直しが止まるのではなく campaign 全体が止まる。回避策 2 つはいずれも防壁の意味を変える
(詳細と択一は {{D:floor-registry-namespace-fork}})。

**未見事実 2 — certified 検証は台帳を一切読んでいない。** `verify_floor_artifact` 自身が attempt
registry と schedule の突合を保証外と明記し、live wrapper は holdout admission 台帳だけを検査し、
ratified verifier も result / journal / live admission だけを渡す。legacy trigger の認可は台帳行が
無くても通る。よって新軸を書く経路を作っても**台帳を削除して certified 検証が通る**状態は変わらず、
本 wave が掲げた成果物影響 (certified 選択の根拠から測り直しが欠落する) は解消しない。
台帳を proof chain へ束縛するには受理面を変える必要があり、既存 certified 成果物を遡って
対象にするかも含めて裁定が要る ({{D:floor-registry-proof-chain-binding}})。

**段 3 の結果:** レンズ 2 本 (裁定の読みと防壁の実効性 / consumer 閉包と記録の同一性)。
所見は real 13 件・refuted 0 件。うち 11 件を次 wave の plan v2 への拘束として採用し、
2 件 (上記) を scope 外として裁定へ返した。**両レンズが独立に同じ分割を推した** —
前半は legacy 統計的測り直しの縦切り 1 本 (schema、sealed な理由 authority、terminal 理由の
再導出、二台帳の crash 整合、配線、final inspector まで同時)、後半は外部 scheduler 証拠側
(現状 authority 集合が空で収集器も理由を発行できず到達不能)。**書き手と検査を別々に land する
分割は不可**で、書き手先行なら proof chain が台帳の欠落を許し、検査先行なら既存 campaign が止まる。

最重要の 3 件: (1) terminal 理由の一致検査の例外が閉集合 membership だけで広すぎる —
throughput 由来の 2 理由に限定し canonical session bytes から再導出して証明する形だけを許す。
(2) 理由が呼び手から偽造できる — `FloorRetryAuthorization` は公開 dataclass で `isinstance` しか
検査せず authority 境界になっていない。(3) journal と台帳の二台帳間に crash 整合が無く、
片側だけ書けた孤児状態で次 ordinal が永久に開かなくなる。

**親裁定 2 件を記録した。** (P1) の読み ({{D:floor-remeasurement-reason-scope}}) と、
部分実装をしない判断 ({{D:no-partial-land-for-dead-gate}})。前者は段 3 で
レンズごとに判定が割れた項目で、ユーザーが覆せるよう裁定パッケージにも併記する。

**引数の前提 1 件が実測と食い違った。** 依頼は編集面の起点を
`orchestrator/campaign/floor_job_checkpoint.py` としていたが、同 file は全 worktree で変更 0 件、
かつ `AUTHORITY = "diagnostic-only"` の診断用 checkpoint で再試行の判断を持たない
(`retry` の出現 0 件)。実際の編集面は attempt registry の profile / core と床値 campaign の
統計判定側だった。

**工数:** codex 子 3 本 (plan 1 / consult 2、いずれも rc=0、`check_codex_output.py` rc=0)。
段 5・6 は「実装しない」裁定により飛ばした (4→7→8→9)。

## 次の一手差分

### 更新

- [T-1851] **P1・裁定済み (D1032) だが、裁定時に見えていなかった事実 2 件で実装が塞がれた**:
  測り直しを耐久台帳の中の別 ordinal 軸として置く方向は維持する。ただし
  {{D:floor-registry-namespace-fork}} と {{D:floor-registry-proof-chain-binding}} の 2 件が
  返るまで実装へ進めない。返り次第、段 3 の両レンズが推した縦切り 1 本 (legacy 統計的測り直し)
  として再開する。段 4 裁定の全文は本エントリ本文と、次 wave へ渡す
  `output/insights/2026-08-27_t1851-floor-retry-ordinal-axis/` を参照。
  base: a2dc67aef84cfc55a950e68b7bf1aae11e6a20a260de5a010ce7fbc2ee51d578

### 新規

- {{T:floor-registry-namespace-fork}} **P1・ユーザー裁定待ち**: 床値の attempt registry を
  freeze 単位のまま据え置くか、protocol 世代ごとに分けるか。世代ごとに分けると
  `_s8b_budget_key` が freeze 単位に集約している測り直し予算が世代ごとにリセットされ、
  「protocol を版上げして同じ cell を測り直す」経路が開く。据え置くと新しい ccbench pin で
  床値 campaign を走らせられなくなる。詳細は {{D:floor-registry-namespace-fork}}。
- {{T:floor-registry-proof-chain-binding}} **P1・ユーザー裁定待ち**: attempt registry を
  certified 成果物の proof chain へ束縛するか、束縛するなら既存 certified 成果物を遡って
  対象にするか。詳細は {{D:floor-registry-proof-chain-binding}}。
- {{T:floor-retry-authorization-not-sealed}} **P2・新規**: `FloorRetryAuthorization` が公開
  dataclass で、runner が `isinstance` しか検査しないため authority 境界になっていない。
  T-1851 の実装に含めるが、実装が塞がれている間も既存の穴として残る。
- {{T:floor-registry-parse-failure-legacy-fallback}} **P2・新規**: attempt registry の parse が
  失敗したとき legacy 候補 1 件を受理する fallback があり、候補件数が判定不能なまま
  D880 の XOR を通す。本 wave が作った穴ではなく既存の穴。
