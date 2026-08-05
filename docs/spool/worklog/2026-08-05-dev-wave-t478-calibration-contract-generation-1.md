---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t478-calibration-contract-generation
seq: 1
title: 較正の contract 世代移行を設計した — 既存の世代交代機構が防壁の実体、択一 5 件を裁定へ返す (docs のみ、branch worktree-dev-wave-t478-calibration-contract-generation)
---

## 本文

- [T-452] U-7 = (a) の裁定で起票された [T-478] の設計 wave。**実装しない**と段 4 で裁定したため
  段 5・6 を飛ばした (`DW-S04`)。**実装差分がないため変異 matrix と受入全走は射程外**である。
  docs 訂正 1 件があるため `check_docs.py` と関連テストのみ走らせた。
- 成果物 = `output/insights/2026-08-05_t478-calibration-contract-generation/`
  (README = 裁定パッケージの正本、§9 が択一の正本)。逐語 6 本を同梱。
- **段 3 の敵対 2 レンズは両方 NO-GO、所見 19 件 = real 18 / 部分反証 1 / refuted 0。**
  採用 16 / scope 外で裁定へ返却 2 / 本 wave で docs 訂正 1。
- **親が実測で子の食い違いを解決した 1 件**: production の `env_contract.lookup` 呼び出し数は
  **21** (campaign 18 + T-126 2 + T-419 probe 1)。段 2 の「18」は campaign 配下限定、
  レンズ B の「全体 18」は誤り、**親 brief の「20」も誤り (erratum)**。
- **親の新事実**: この repo には世代交代機構の実装済み前例がある
  (`s8b_ratified_freeze.py` の pointer 連鎖・承認 record 分離・失効 tombstone・F5 transition table)。
  transition table が「変わってよい JSON Pointer を完全列挙し、列挙外は前世代と厳密一致」を
  強制する型であり、これが敵対レンズの must-fix 2 件 (successor が attestation を無効化できる /
  blind seal を再発行できる) をそのまま塞ぐ。**推奨機構は新発明でなく既存型の適用**である。
  同機構が `/env_tag` 変更を「環境が変わる = 別実験」として拒否している事実は、
  新 env_tag を切る案への反対材料でもある。
- **問題設定が実測で変わった**: `output/s8b-freeze/` に ratified freeze も完走 campaign 成果物も
  存在しない。守るべき「既存 certified 参照」は過去の測定値ではなく、
  **事前登録 (blind seal) の性質**である。移行設計の第一の禁止は
  「較正更新を口実に実験設計や予測を選び直せる経路を作らないこと」になった。
- docs 訂正 1 件 (レンズ A-7、親が実測確認): `docs/freeze-permanent-design.md` の
  `FROZEN_MANIFEST` 記述が「8 件・件数が合えば差替えが通る」のままだったが、実装は
  **23 件 + 独立 exact key-set 検査**である。移行監査が閉包件数を誤るため erratum を入れた。
- **影響テスト = 375 passed / 0 failed (rc=0)** (計算ノード request 889961、21.32s)。対象は
  repo scan invariant (F34)・check_docs meta・frozen artifacts・env contract。
  **[T-452] の変異 harness (m6b) が走行中だったため受入全走は投入していない** — 本 wave は
  実装差分ゼロで射程外であり、docs 変更に影響する最小集合だけを別 worktree から投げた。
- 手順違反・セッション異常なし。並行 wave 4 本 (t452-t453 / t474 / t476 / token-economy) は非接触。
- 段 8 自己改善: 候補 2 件を検討し**いずれも不採用**。(1)「敵対 2 レンズが同じ数値で食い違ったとき
  親が実測で解決する」は `DW-S03` の「親自身の実測値もレンズへ入れる」と `DW-O18` の帰属検査で
  既に覆われる重複。(2) `DW-O01` の起動形 (`bash -c '<cmd>; …'` inline) は **worktree 隔離の
  背景 job では harness guard に「複合すぎて worktree 内と検証できない」と拒否される**ため
  launcher script を Write して `nohup setsid bash <script>` で起動する必要がある —
  実測した食い違いだが、`docs/dev-wave/operations.md` の予算残が **35 bytes** (8365/8400) しかなく
  意味等価な追記が入らない。予算引き上げは独立審査事項であり、guard の拒否 message 自体が
  分割を指示するため実害なく 1 手で復帰できる。**予算を理由に安全義務は削らず、変更を止めた。**

## 次の一手差分

### 更新

- [T-478] **P2・設計完了 → ユーザー裁定待ち (択一 5 件)**: 較正の contract 世代移行の設計を確定した。
  推奨は **案 A′** = 「immutable 世代列 + contract hash 逆引き + `HistoricalContract`/`CurrentContract`
  の型分離」に、既存 F5 transition table 型の successor 制約 (可変 pointer は `/calibration_ref/*`
  のみ) と activation receipt・campaign identity への contract hash 束縛を組み込んだ合成案。
  裁定へ返す択一 = (1) 世代機構 A′/B/C/D、(2) 「解決不能」の定義を三状態の強い定義にするか、
  (3) campaign identity への `environment_contract_sha256` 必須化 (D13 改訂)、
  (4) **[T-452] U-8 の「連続 2 commit」制約との衝突** — staging resolver を挟むと 2 commit に
  収まらない可能性があり、承認済み裁定の前提を覆す未見の新事実のため親は読み替えず返す、
  (5) 8c/P3 prereg 下流の更新時期。実装は [T-419] U-2 wave の所有で、本 wave はコード・テスト・
  凍結成果物・pin を一切変更していない。
  一次資料 = `output/insights/2026-08-05_t478-calibration-contract-generation/README.md` (§9 が択一の正本)
  base: 64b5feb1cc9a4a68fc872a3d08afc48b6a2fb25e810c4b8874f08237b0e2ff44
