---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t627-noop-binding
seq: 2
title: [T-627] 世代遷移述語を (generation, contract hash) の同一入力束縛で実装した — no-op・skip・downgrade・相殺を拒否する (コード + docs、受入 7438 passed / 20 skipped、変異 9/9 KILLED・SURVIVED 0、branch worktree-dev-wave-t627-noop-binding)
---

## 本文

- **裁定どおり次点 (b) で実装し、番号 delta 述語 ((a) 案) は採らなかった。** 実装形の設計判断は
  {{D:activation-transition-bound-pair}}。本番 chain は record 1 件のままで、
  `lookup()` の返り値と activation head 定数は land 前後で不変である。
- **段 1 の実測が本 wave の形を決めた。** 合成 registry と合成 chain を loader へ直接渡すと、
  no-op / skip / downgrade / `(+2, −1)` / `(+1, −1)` / 連鎖途中 no-op の**すべてが受理**されていた。
  遷移を見る層は repo に 1 つも無く、発行 tool も同じ loader を呼ぶため実効 gate は 1 箇所だった。
  20 行の実編集 probe を入れて対象テストを実走したところ、**現状の緩い受理集合を明示的に pin する
  既存テストが 1 件**あることも判明した (`..._intentionally_does_not_enforce_generation_delta_predicates`)。
  裁定が受理集合を狭めた結果としてこれを置換し、他に 3 件の fixture を再著述した。
- **親 brief の `DW-G04` 主張は誤りで、段 3 が訂正した。** 親は「新述語は既存の後継検査と同じ
  『結線済み・未発火』だ」と書いたが、既存の後継検査は import 時の世代列検証から実際に呼ばれている。
  新述語は本番 chain が 1 record であるため呼ばれる入力が存在せず、**`DW-G04` は満たしていない**。
  後発のユーザー裁定が順序を明示したため本件に限り狭く override された、と記録する。
  **consumer の存在を発火証拠とは呼ばない。**
- **親の provisional 裁定 (P2) は段 2 が反証した。** 「registry 経由の推移で後継検査との合成を満たす」
  案は、loader が受け取る catalog を呼び出し側が任意に構成できるため、loader の契約上は合成が
  現れない。必須注入 + production adapter へ切り替えた。
- **model 多様性が実際に検出力を生んだ。** 段 6 の敵対レビュー 2 本と焦点再レビュー (計 3 本、
  いずれも同一 model) を通過した実装に対し、追加した別 model のレビューが**先行 3 本が
  見逃した real な穴を 4 件**構成した — 最初の隣接 pair だけ検査する実装、発行 tool の adapter 結線を
  常時真の callback に差し替える実装、adapter が import 時 snapshot を握る実装、後段 env の
  非 bool / 例外を無視する実装。いずれも実装済み全 node を通過していた。
- **`changed[:N]` 型の量化縮退は有限 fixture では族全体を殺せない。** 3 env の fixture では
  `changed[:3]` が、4 env にしても `changed[:4]` が生存する (後者は追加レビューが独立に構成した)。
  親は 4 env で止め、**「N ≥ 5 は既知の残穴」を該当 node の docstring へ明記**して閉じた。
  5 env 以上は追加していない。保証を謳わないことをもって終端とする。
- **変異は 3 走。未登録の SURVIVED はゼロ。** run 1 は spec の category 語彙が harness の集合に無く
  preflight で abort し、変異は 1 件も適用されていない。run 2 は 9 変異すべて rc=1 (赤) だったが
  7 件が MISMATCH で、正規化して突き合わせると**期待 node はすべて記録 node の部分集合、欠落ゼロ**
  だった (差分は fix 第 3 巡が spec 作成後に足した node)。erratum として残し、期待 node を実測へ
  合わせた run 3 で 9/9 KILLED・完全一致を得た。
- **事前登録の誤りを 2 件、焦点再レビューが実行前に見つけた。** `exactly +1` を非減少へ緩める変異の
  期待 kill に相殺ケースを挙げていたが、相殺の片側は残存 gate に拒否されるため赤にならない
  (run 3 の記録 6 node に相殺 node は含まれず、指摘は実測で裏付けられた)。量化を縮退させる変異では、
  赤くなる 10 node のうち受理集合が変わる semantic kill は 3 件で、残る 7 件は call 列・診断だけが
  変わる観測 pin である。kill 件数に合算していない。
- **catalog 順序を使う誤実装は単一 site の変異として構成できなかった。** private gate に catalog 引数が
  無く、署名変更を伴う multi-site 改造になる。`DW-M04` の「置換対象が一箇所でなければ停止」に従い
  実行せず、設計上の観測として記録する (この構造自体が当該誤実装を排している)。
- **wave 中に dev-wave 契約が 2 度変わり、いずれも段をやり直さずに扱った。** (i) 段 3 敵対相談の
  2 model 混成 — 本 wave の段 3 は land 前に単一 model 2 本で実行済みだったため、段 4〜6 を
  無効化しないよう**段 3 は再実行せず段 6 へ別 model のレビューを 1 本追加**した (これが上記の
  4 件を見つけた)。(ii) 段 6 review 子の reasoning 機械 pin — 本 wave の段 6 は land 前に
  1 段上の effort で実行済みであり過小ではない。再実行なし。経緯は該当 merge commit にも書いた。
- **親の実測 script を insights へ `.py` で置けなかった。** insights 直下の `.py` は AI provenance の
  実装面判定対象であり Codex author を要求する。本 wave のそれは `DW-S01` と `DW-M04` / `DW-M08` が
  親へ課す測定器であって production の実装面ではないため、Codex author を偽らず、
  逐語を code block として markdown へ凍結した。実行可能な原本は wave の job directory に残した。
- **fix は 3 巡** (`DW-O16` の上限)。production の挙動を変えたのは統合 commit だけで、
  第 2・第 3 巡はテストとコメントのみ。並行 wave の land を 3 回取り込んだ。
- 一次資料 = `output/insights/2026-08-08_t627-noop-binding/` (段 1 brief と probe、段 2 プラン、
  段 3 の 2 レンズ、段 4 裁定と変異事前登録、段 5 実装報告、段 6 の 3 レビュー + 追加レビュー、
  fix 3 巡、変異 spec 2 版と台帳 2 走、親の実測 script の逐語)。

## 次の一手差分

### 完了

- [T-627] 世代遷移述語を (generation, contract hash) の同一入力束縛で実装し、
  no-op・skip・downgrade・相殺を拒否する受理集合の縮小を land した。実装形は
  {{D:activation-transition-bound-pair}}。
  remaining: none
  base: be2bc032064641b4b975214438e451fab31c1da25305190723eca3cad2d30cbc

### 新規

- {{T:activation-certified-writer-source-binding}} **P2・新規・ユーザー裁定待ち**:
  汎用 certified producer の source binding。silo と qualification は activation の 2 module を
  code identity に含めるが、汎用 certified 経路はその binding を呼ばない。第 2 世代の活性化後は、
  dirty / 未レビューの loader bytes で certified 選択・レポート・WAL を生成しても activation 参照
  だけでは検出できない。活性化の前提として設計択一が要る。
- {{T:activation-transition-property-based-tests}} **P3・新規**:
  遷移述語の量化縮退 (`changed[:N]`) は有限 fixture では族全体を殺せない。現状は 4 env までの
  固定 fixture と docstring への残穴明記で閉じている。生成的 / property-based テストを
  入れるかどうかは別途決める。
