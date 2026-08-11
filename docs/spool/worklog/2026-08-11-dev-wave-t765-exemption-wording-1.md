---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t765-exemption-wording
seq: 1
title: DW-S04 の変異免除条件を連言明示へ書き換えた — 焦点レビュー 3 巡が 3 つの別々の誤読を潰した (docs のみ、実装面差分ゼロ、branch worktree-dev-wave-t765-exemption-wording)
---

## 本文

- **裁定 (worklog 437、(c)) の実装。** 免除範囲を広げも狭めもせず、現行文面の曖昧さだけを解いた。
  ```
  旧: 免除は実装差分ゼロの「実装しない」裁定の変異 matrix だけ。          (83 bytes)
  新: 免除は「実装しない」裁定済みかつ実装差分ゼロの wave の変異 matrix だけ。 (101 bytes)
  ```
  旧文は連体助詞 `の` が head noun を明示せず連鎖し、(i) 両条件を満たす wave だけ免除 /
  (ii) 実装差分ゼロなら免除、の 2 通りに読めた。新文は 2 属性を `かつ` で連言として同じ wave へ係らせる。
- **曖昧さの実害が一次資料で裏付けられた。** 条項を導入した D237 は見出しが
  「実装差分ゼロの wave で免除するのは変異 matrix だけとする」で、本文は「実装差分ゼロ」を
  **必要条件**として束縛したと書く (十分条件とは書いていない)。しかし導入 wave [T-642] 自身は
  docs を実際に書き換える wave でありながら「実装差分ゼロで変異対象のコードが存在しない」を理由に
  **変異 matrix を免除**していた (`output/insights/2026-08-08_t642-dw-s04-acceptance-scope/README.md:5,97`)。
  **文面の逐語は連言、運用実績は差分ゼロ単独**という乖離が既に生じていた。この乖離の恒久的な扱いは
  {{D:dw-s04-conjunction}} で前向きに確定し、docs-only wave への明示的 carve-out は免除範囲の変更に
  なるため実装せず裁定パッケージへ返した。
- **段 6 の焦点レビューが 3 巡すべて NO-GO。** 3 つの候補文が**それぞれ別の誤読**で破れた。
  | 巡 | 文面 | 破れ方 |
  |---|---|---|
  | 1 | `…と裁定され実装面差分ゼロの wave…` | 連用形の**省略主語**が当該 wave に固定されず、別対象の裁定を拾う `E∧Z` |
  | 2 | `…裁定済みで実装差分ゼロの wave…` | `で` の**原因理由読み**が「裁定ゆえに差分ゼロ」の因果条件を作り `C∧Z∧R` へ縮小 |
  | 3 | `…裁定済み・実装差分ゼロの wave…` | **中黒が選択列挙にも使われる**ため `C∨Z` が成立し、旧文より免除が拡大 |
  3 巡目の指摘は親が独立に裏を取った — 同じ文書群で中黒は連言 (`範囲・言語・起動手順`) にも
  選択 (`指定 reference が不在・読めない`、`process の非 0 終了・timeout`) にも使われている。
  `DW-O16` の 3 巡上限に従い、4 巡目の fix を重ねず親裁定で `かつ` へ確定した。根拠は
  **最悪ケースの非対称性** — `かつ` は選択読みを構造的に持たない (選択は `または`) ため、
  どの読みでも免除集合は `C∧Z` 以下にしかならず、旧文の意図した集合を超えない。
  **確定文は第 4 巡の敵対レビューを受けていない**ことを残余リスクとして記録する (撤回は 1 行)。
- **1 巡目の `実装面` への言い換えは撤回した。** 入口の凍結境界が定義する語だが、`core.md` 単体からは
  定義へ到達できず新しい曖昧さになる。旧文と同じ `実装差分` を維持し、その射程
  (probe・harness・script・機械設定を含むか) は本 wave で変えず裁定パッケージへ返した。
- **本 wave 自身は免除しなかった。** 段 4 で `C=false` (規範文を置換する**通常経路**であり
  `4→7→8→9` の「実装しない」経路ではない)、`Z=true` (実装面差分ゼロ) と裁定した。
  docs-only であることを免除理由にせず、自分の書いた新文で自分を免除する経路を閉じた。
- **変異は実効 gate へ再照準して 1/1 KILLED。** 実 repo の L1 超過で赤になる pytest node は存在しない
  (`test_dev_wave_layer_budget_rejects_plus_one` は `_build_min_repo()` の合成 repo を測る) ため、
  `DW-M01` の F28 経路で `python3 tools/check_docs.py` の L1 層予算へ再照準した。
  104 bytes の意味等価版を注入して **rc=1、finding は `L1 unique footprint 10627 bytes > 予算 10625 bytes`
  の 1 件のみ** (単一理由性)。復元後 `git status` 空・`check_docs` rc=0。
  **曖昧さの解消そのものは機械変異では証明できない** (本文の意味を pin する検査は存在しない) ため、
  KILLED として数えず、真理値表・独立 2 レンズ・焦点 3 巡・consumer 棚卸しを代替証拠とした。
- **受入全走**: 本エントリの記録 commit を含む tip で実走する (結果はこのエントリ末尾へ追記する)。
  免除の可否は証拠で判定した — 実 repo を読むテストは実在する
  (`orchestrator/tests/test_check_docs.py::test_dev_wave_waiter_consumer_pins_accept_current_docs_contract`
  が `check_docs.REPO / "docs/dev-wave/core.md"` を読む) ため、docs のみでも免除しない。
- **docs 予算は上げていない。** L1 = 10,606 → **10,624 / 10,625** (余白 1)。worklog 435 の
  [T-786] 棚卸し後の値と整合する。L1.5 は 9,564 / 9,566 で不変。予算値の定数は 1 bytes も触っていない。
- **段 3 レンズ A が `evidence_status=invalid` で未採用になり、原因を repo 内の 2 行まで特定した。**
  `codex_exit_code=0` / `validator_rc=0` / rollout 健全 / 成果物 10,488 bytes 完全
  (`check_codex_output.py` rc=0) でありながら `launcher_rc=1` (784 秒・入力 237 万 token)。
  launcher の stdout 解析を実 events へ当てて原因行を割り出したところ、**JSONL の Unicode NFC 要求**に
  抵触していた。出典は tracked file 全体でわずか **2 行** —
  `orchestrator/tests/test_check_docs.py:4442` と `:4465` の分解済み「プ」(U+30D5 + U+309A)。
  子が `grep` でこの行を読むと event 行が非 NFC になり、内容と無関係に run 全体が捨てられる。
  症状は F217 と同じだが原因は別で、F217 の再発検知手順では検出できない
  ({{F:non-nfc-line-invalidates-codex-run}}、{{T:normalize-non-nfc-test-literals}})。
  親が独立監査して成果物を採用し、レビュー結果として数えた。

## 次の一手差分

### 完了

- [T-765] `DW-S04` の免除条項を `免除は「実装しない」裁定済みかつ実装差分ゼロの wave の変異 matrix だけ。`
  へ置換し、免除範囲を変えずに曖昧さを解いた。焦点レビュー 3 巡と変異 1/1 KILLED で裏取りした。
  remaining: none
  base: 21f2c58ff75caa4dad224a105119768e76cc9022a895de4772f2d38d6daee234

### 新規

- {{T:dw-s04-scope-of-impl-diff}} **P3・ユーザー裁定待ち**: `DW-S04` の `実装差分` の射程を
  入口の「実装面」(コード・テスト・実行可能 probe / harness / script・機械設定) へ明示的に束縛するか。
  現状は旧文と同じ `実装差分` のままで、probe・script だけを変えた wave が `Z=true` と誤分類されうる。
  択 = (a) 文面を `実装面差分ゼロ` にする (要 3 bytes、L1 余白 1 → 定義到達性の手当ても要る) /
  (b) core.md から入口の定義へ逆参照を張る (予算追加が要る) / (c) 現状維持で段 4 記録の運用に委ねる。
  親の推奨は **(a)**: 誤分類の向きが免除拡大 (規律 2 の面) であり、`実装面` は入口が既に定義済みの語で
  新概念を作らない。定義到達性は `DW-S04` 内に `(入口の定義)` と 1 語添える案を同時に測る。
- {{T:dw-s04-docs-only-carveout}} **P3・ユーザー裁定待ち**: docs-only wave に変異 matrix 免除の
  明示的 carve-out を作るか。D237 の見出しと [T-642] の自己免除は Z 単独読みで動いており、
  {{D:dw-s04-conjunction}} で連言と確定した結果、**docs 契約を書き換える wave は今後必ず
  実効 gate への再照準を伴う変異を要求される** (本 wave が第一号)。
  択 = (a) carve-out を作る (免除拡大なので (a) 系の裁定) / (b) 作らない (現状) /
  (c) 「機械 gate が存在しない場合の代替証拠」を明文化する。親の推奨は **(c)**:
  本 wave の実測どおり docs-only でも実効 gate への再照準は可能で、免除を広げずに手順の空白だけが埋まる。
- {{T:normalize-non-nfc-test-literals}} **P2・新規**: `orchestrator/tests/test_check_docs.py:4442,4465` の
  分解済み「プ」を NFC へ正規化する (実装面のため Codex author が要る)。この 2 行を読んだ Codex 子は
  成果物が完全でも必ず不採用になる ({{F:non-nfc-line-invalidates-codex-run}})。
  併せて「tracked file に非 NFC 行があれば赤」の機械検査を `tools/check_docs.py` へ入れるかを裁定する
  — 入れれば混入時点で止まり、子を走らせてから捨てる無駄が構造的に消える。
  実測: 全 tracked file の非 NFC 行はこの 2 行だけで、判定は `git ls-files` + `unicodedata` で 2 秒。
