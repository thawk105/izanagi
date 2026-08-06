---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t574-world
seq: 2
title: [T-574] 残余を閉じた — 配線すべき consumer は 0 件で、残っていたのは裁定済み 3 項だった。[T-529] の blocker は外れていない (コード + docs、受入 6846 passed / 20 skipped、変異 4/4 KILLED、branch worktree-dev-wave-t574-world)
---

## 本文

- **依頼の「残る production consumer への world 拡大分」は、実測すると 0 件だった。** 記録
  `contract_sha256` を current registry と比較する production site を全走査し、
  live admission (D202 据置) / 現行互換と裁定済み / 記録 contract を持たない reader /
  非 certified probe へ分類した結果、historical resolver を新たに配線すべき read-only 再検証
  consumer は残っていなかった。段 3 の 2 レンズが独立に反例を探して出せなかった。
  inventory は `output/insights/2026-08-06_t574-world-expansion/README.md`。
- **代わりに残っていたのは裁定済み 3 項だった。** [T-588] の fail-closed 化、[T-587] の回帰試験、
  [T-586] の終端。裁定は {{D:receipt-expectation-scope}}、{{D:current-only-resume-spec}}、
  {{D:silo-verify-result-current-compat}} として記録した。
- **[T-529] を unblock しなかった。** 段 1 brief は unblock すると書いたが、段 3 が 2 点で覆し、
  親が裏取りして採用した。(1) R1 (記録 hash を世代選択の権威にしてよいか) がユーザー裁定待ちのまま
  である。(2) `reverify_published_freeze` の唯一の production loader が active pointer 不在で
  `no-active` になるため、historical 経路の production 正例を今日書けない。よって D196 (3) は
  「配線すべき consumer を洗い出して配線し切った」までが済み、「発火する正例を持つ」は済んでいない。
- **段 2 が提案した回帰試験は恒真だった。** `attestation_mode="none"` の calibration loader は
  grandfathered bytes だけを受理するため、守るべき current 契約検査を消しても後段が同じ例外型で
  落ちる。親が `env_attestation.py:1119-1121` で裏取りし、段 4 で calibration loader の呼出し回数 0
  という因果 pin へ差し替えた。変異 M3 はこの pin でだけ KILLED になる。
  型は {{F:tautological-exception-type-pin}}。
- **段 1 brief は 3 点誤っていた。** (1) 「`MappingProxyType` で 2 世代の試験注入が構造的に塞がれて
  いる」は誤りで、module 属性の局所 patch は既存慣行だった。(2) 記録 hash 比較 site の列挙が不完全
  だった。(3) 「未知 hash で世代跨ぎを模す」案は世代跨ぎ固有の退行を検出しない。
  いずれも段 3 が指摘し段 4 で訂正した。**親の一般化が段 3 で覆るのはこれで 2 wave 連続**である。
- **レビュー R2 の must-fix 1 件を親が blocker から降ろした。** 「report source bytes を変えると
  `generator_versions.report` の pin が動き live の manifest 受理が反転する」という指摘は事実だが、
  これは byte pin の意味論そのもので、bug fix を含むどんな編集でも起きる。blocker にすると当該
  ファイルを永久に編集できない。発行済み manifest 0 件のため既存受理は不変。択一 R12 として返す。
- **変異 run 1 は erratum として残した。** 過剰拒否検出の正例変異が非 Mapping 経路も巻き込み、
  事前登録外 2 node を落として MISMATCH になった。field 不在経路だけへ再照準した run 2 が採用値で、
  4/4 一致 (全 KILLED)。焦点再レビューが「結果への期待値合わせではない」と独立に判定した。
- **provenance 監査は 5 違反だが、5 件すべて別セッション (`worktree-rulings-20260806-a`) の既存
  merge commit**で、本 wave の commit は clean である。
- **裁定手順と実行手順が 1 点食い違った。** 段 4 は実装子を 2 単位 (所有素集合) へ分けると裁定したが、
  実際には**単一単位**で投入した。所有パス限定 patch の統合が過去に別 worktree を汚染した先例があり、
  A と B が合計 3 ファイル・小規模だったため、並列化の利得より統合事故の面を嫌った。
  受理集合・所有境界には影響していない。
- **ユーザー裁定待ちの択一が 4 件ある** (R9〜R12、insights の README が正本)。骨格を決めるのは
  R11 (`reverify_published_freeze` の production 到達性をいつ確保するか) で、これは [T-529] の
  blocker (2) と同一である。
- **段 8 の改善候補は 3 件で、reference は 1 行も変えなかった。** (1) 負例試験の oracle を因果で
  pin する作法は `DW-M01` へ統合するのが自然だが、`docs/dev-wave/**` は 25,187 / 25,200 bytes で
  **残り 13 bytes** しかない。[T-577] の裁定 (予算上限は上げない、入らない分の再発防止は failures
  台帳が担う) に従い {{F:tautological-exception-type-pin}} の恒久対応で閉じた。
  (2) worktree 隔離背景 job の codex 起動を launcher script 経由にする作法は、同じ予算理由で
  **見送り 4 例目**。(3) carry 鎖を遡って base digest を出す helper が repo に無く、
  worklog ローテーション後は archive 走査が要るため wave ごとに書き捨てている。実装面の新規 tool に
  なるため段 8 では実装せず、記録に留める (プロトタイプ基準 D205)。

## 次の一手差分

### 完了

- [T-574] 記録 contract hash からの世代解決について、配線すべき read-only 再検証 consumer が
  残っていないことを全 site 走査で確定し、残余だった裁定済み 3 項を消化した。
  閉包 inventory と残 blocker は `output/insights/2026-08-06_t574-world-expansion/README.md`。
  前 wave から持ち越した R4 (真の世代別述語 dispatch) は起票せず insights の記録に留める
  (D203 で保証範囲を縮めた結果、現 successor 規則では観測差を作れないため)。
  remaining: none
  base: 3f7a89bfb720e002f992361d2f534891fbfc17c3f846b121571fec8cac6846da
- [T-586] silo `verify-result` の binding 層を current 互換検査と明示し、記録 hash からの歴史
  再検証の対象外として終端した。{{D:silo-verify-result-current-compat}}。decisions の新設のみで
  既存 decision 本文は書き換えていない。裁定文が想定した「資料側の 1 行修正」は、対象の肯定表現が
  D196 本文に存在しなかったため行っていない (段 3 レンズ B が指摘、親が裏取り)。
  remaining: none
  base: 9d7a704fae7172bceafffc35df06ec7d87fdcaa96b80e61cecac84ff0f239acd
- [T-587] 契約世代を跨いだ resume の喪失を正式仕様として受容し、回帰試験で固定した。
  例外型の一致では恒真になるため、current 契約検査が calibration 読込みより前に拒否したという
  因果を calibration loader 呼出し回数 0 で pin し、通る正例を添えた。
  {{D:current-only-resume-spec}}。production code は 1 行も変えていない。
  remaining: none
  base: 94e4adb4174213ca8a04be1f5689daed200ac4f6c10b972f37a07030fec37548
- [T-588] 宣言済み `run_contract` の identity 欠落・空・非文字列を legacy 扱いにせず fail-closed に
  した。{{D:receipt-expectation-scope}}。裁定文の「manifest-global error」は実態と違うため
  その語を使わず、診断が行へ載る適用層 (campaign-start が一意で row のある campaign の観測経路)
  を明記した。発行済み manifest 0 件のため既存受理は 1 件も変わらない。
  remaining: none
  base: 89c26a784b1c91be868db2b45b4a31e863031936ee4bb4b52cd35e85c4f960ec

### 更新

- [T-529] **P1・裁定済み (6 択一とも推奨どおり)。[T-574] は完了したが blocker は外れていない**:
  D196 (3) のうち「配線すべき consumer を洗い出して配線し切る」は済んだ。残るのは
  (1) R1 = 記録 hash を世代選択の権威にしてよいかがユーザー裁定待ち、
  (2) `reverify_published_freeze` の唯一の production loader が active pointer 不在で `no-active`
  になるため historical 経路の production 正例を書けない (`DW-G04` 不充足) の 2 点。
  裁定内容は変わらない (trust root = レビュー済み git commit / 入口 receipt は process-local /
  fuse 解除前に historical resolver を consumer へ配線 / `linux-baremetal` g1 は grandfather /
  certified writer 閉包は別タスク / silo 昇格入口は未実装と名乗る)。
  設計凍結 = `output/insights/2026-08-06_t529-activation-authority/`、
  残 blocker の根拠 = `output/insights/2026-08-06_t574-world-expansion/README.md`
  base: 390d4d429903224ee7998ca23831a1c29a326d55550fb3af51255623b3c907a8

### 新規

- {{T:receipt-diagnostic-reach}} **P3・ユーザー裁定待ち**: receipt expectation の診断を manifest
  全域へ効かせるか。現状は campaign-start が一意で row のある campaign の観測経路にだけ載り、
  早期 return と 0-row campaign では消える。(a) 現状受容 (本 wave の採用) / (b) top-level structured
  issue を新設する。(b) は observations の issue/reason または report CLI の受理集合を変える。
  根拠 = `output/insights/2026-08-06_t574-world-expansion/README.md` の択一 R9
- {{T:v2-manifest-producer}} **P2・ユーザー裁定待ち**: v2 oracle manifest の production producer を
  いつ作るか。`build_manifest` / `write_manifest` の production caller が 0 件で、v2 manifest を
  発行する経路が実装されていない。receipt 束縛の検査群はこの producer が現れるまで一切発火しない
  (同 README の択一 R10)
- {{T:reverify-reachability}} **P1・ユーザー裁定待ち**: `reverify_published_freeze` の production
  到達性をいつ確保するか。active pointer 未発効のため唯一の loader が `no-active` で落ち、
  historical 再検証の正例を書けない。[T-529] の blocker と同一である (同 README の択一 R11)
- {{T:generator-hash-rollover}} **P3・ユーザー裁定待ち**: 生成器 source bytes の変更が
  `generator_versions` の pin を動かす件をどう扱うか。(a) 設計どおりとして受容 (本 wave の採用) /
  (b) rollover 手順を明文化する。発行済み manifest 0 件のため既存受理は不変 (同 README の択一 R12)
