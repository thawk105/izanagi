---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t419-u2-contract-generation
seq: 1
title: 契約世代の受け皿を data 層として置き、2 世代目を fuse で拒否した — U-2 本体は entry condition 未成立で着手しない (コード + docs、受入 6445 passed、branch worktree-dev-wave-t419-u2-contract-generation)
---

## 本文

- **U-2 (較正の再取得) は着手できないと実測で確定した。** 設計正本 §6.1 が定める entry condition の
  1 件目「方式 α の probe 実装が済んでいること」が未成立である。本番 attestation の probe は
  `/proc/cpuinfo` を 1 回読むだけで、方式名も旧いまま。方式 α 自体 (K=5・走行 CPU の rotation・
  論理 CPU ごとの累積最小) は T-419 の因果実験用 probe tool には実装済みだが、同 tool は
  non-certifying / counterfactual-only を自己宣言しており較正の取得経路ではない。
  よって本 wave は「[T-478] の実装は U-2 wave の所有」という裁定に従い、**契約世代機構だけ**を進めた。
- **敵対レンズ 2 本が段 3 で揃って NO-GO を出し、親は所見を全面採用して scope を縮小した。**
  段 2 案にあった `CurrentContract` / `HistoricalContract` の型分離、消費者 21 箇所の移行、
  旧 lookup API の削除はすべて撤回した。理由は {{D:contract-generation-bootstrap-fuse}}。
  とくに「public な dataclass の型検査は生成権限を証明しない (履歴契約を包み直せば通る)」は
  2 レンズが独立に指摘した。
- **親 brief の実測を 2 点訂正した。** (1) 「方式 α は未実装」は広すぎた。正しくは
  「本番 attestation への結線が未実装」。(2) 旧 API 温存の理由を当初「事前登録 evidence の
  述語が機械的に止める」と書いたが、当該述語は機械検査対象外で dormant だった。
  正しい理由は「凍結 evidence contract の参照互換」。どちらも段 6 のレンズが指摘し、親が裏取りした。
- **変異の単一理由性で 2 度つまずき、3 巡の fix で閉じた** ({{F:fuse-masks-mutation-attribution}}、
  {{F:delegation-seam-left-unpinned-by-its-own-fix}})。事前登録 8 件のうち 2 件が
  「後段の安全弁が同じ入力を拒否する」ため帰属不成立で、是正のための抽出 refactor が
  今度は委譲辺を未固定にした。最終的に spy による委譲専用 witness を置いて閉じた。
- **変異台帳は 4 本残す。** 独立 golden を 3 テストが共有する変異 (M7) は初回 MISMATCH となり、
  期待 node を 3 件へ再登録して KILLED になった。親はこれを**冗長 gate と裁定し、
  単独変異の単一理由性の証拠から外す**。初回 MISMATCH は erratum として保持する。
- 受入全走は 3 回実施し、最終 (`d2d65767`) が **6445 passed / 20 skipped / 0 failed**。
  変異は全走 baseline PASSED のうえ M1〜M6・M9・M10 が期待 node どおり KILLED。
- 逐語・prompt・台帳は `output/insights/2026-08-05_t419-u2-contract-generation/` に凍結した。

## 次の一手差分

### 更新

- [T-419] **P1・U-2 は entry condition 未成立で着手不能 → 次は方式 α の本番結線**:
  R-0 / R-1 は裁定済み ((208) 参照)。**[T-478] の世代機構は第 1 層を land 済み**
  ({{D:contract-generation-bootstrap-fuse}})。残る着手条件は
  (i) 方式 α (走行 CPU rotation + 論理 CPU ごと最小) を**本番 attestation の probe へ結線**する、
  (ii) 正規 CLI の accepted publish receipt を得る、(iii) 独立な self-comparison が通る、
  (iv) 既知の自己不整合較正の例外集合が空になる。(i) が次の wave の所有。
  方式 α のロジック自体は因果実験 probe に実装済みだが、同 probe は non-certifying 宣言のため
  取得経路には使えない。受理集合・凍結 bytes・pin は方式実装 wave まで不変。
  一次資料 = `output/insights/2026-08-04_t419-probe-causality/ruling-package.md` / D143 / F108 / F110 / F111
  base: 1a61f49a1ecaffff0b72c50a06448732d80a85d3c25ad2bf449cd22775a2654d
- [T-478] **P2・案 A′ の第 1 層を land 済み → 残る 5 構成要素は活性化権限 wave の所有**:
  land したのは immutable 世代列 + contract hash 逆引き + successor 制約 + 候補 mapping の
  純関数 validator + bootstrap fuse ({{D:contract-generation-bootstrap-fuse}})。
  **未実装として明示的に残すもの** = (a) activation record からの権威導出と全入口の
  activation receipt (この 2 つは対で入れる)、(b) campaign identity への
  `environment_contract_sha256` 必須化 (D13 改訂)、(c) versioned predicate dispatch、
  (d) 起動 wrapper の結線、(e) bundle role / 非空 cardinality / literal trust root の独立検査。
  型による権限分離は**実装しない**と裁定した (public dataclass は包み直しで偽造できる)。
  裁定 (4) の supersede を書く新 D も (b) と同じ wave が持つ。
  一次資料 = `output/insights/2026-08-05_t478-calibration-contract-generation/README.md` §9 /
  `output/insights/2026-08-05_t419-u2-contract-generation/`
  base: 82043ead04c8ee7e1c0072f36bee771c2f2e8fa394e50b38db81efb5f5f356b6
- [T-506] **P2・裁定済み → self-pass は「較正を登録する wave」に同梱 (U-2 の下流へ繰り下げ)**:
  loader への canonical 述語 self-pass は新較正の登録と同時に課す方針は不変。ただし U-2 本体が
  entry condition 未成立で着手不能と判明したため、同梱先は「方式 α 結線 → 再取得 → 登録」の
  chain の最終段になる。それまでは「再較正まで certified campaign を開かない」の運用宣言を維持する
  base: 789e68def5e06ef26475a4a885fb3780891ca111b6abc4e8d8c16b1e8b7ec2d1

### 新規

- {{T:probe-method-alpha-production-wiring}} **P1・新規**: 方式 α を本番 attestation の probe へ結線する。
  走行 CPU を移しながら K 回読み、論理 CPU ごとに最小値を採る。ロジックは T-419 の因果実験 probe に
  実装済みなので、移植先は取得経路と方式名・schema。**これは U-2 の entry condition 1 件目**であり、
  完了するまで較正の再取得は開始できない。方式名が変わるため凍結 bytes と pin の更新を伴う点は既知
- {{T:contract-generation-activation-authority}} **P1・新規**: 契約世代の**活性化権限**を実装する。
  activation record からの権威導出と、全入口 (floor / oracle / P3 / 適格性 / selector / silo 昇格) が
  最初の書込み前に同じ migration epoch と bundle hash を検査する activation receipt を**対で**入れる。
  これが入るまで {{D:contract-generation-bootstrap-fuse}} の fuse は外せない
  (外すと、正規 publish を通っていない較正を source へ足すだけで current にできてしまう)。
  campaign identity への contract hash 束縛と versioned predicate dispatch も同 wave の候補
- {{T:campaign-env-contract-none-bypass}} **P2・新規**: 計測を認可する経路が環境契約を
  省略したまま certified へ到達できる迂回を塞ぐ。契約を渡さない既定値が site 検査より前に返るため、
  契約 hash に束縛されない run が certified 受理集合に残る。単独で塞ぐと承認外の受理縮小になるので、
  campaign identity への hash 束縛と同じ wave で行う。段 6 の 2 レンズが独立に指摘
