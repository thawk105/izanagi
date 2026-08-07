---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t598-forward-collection
seq: 1
title: [T-598] wave 単位の前向き収集を結線した — ただし収集は 1 件も走っていない。実行場所が §7.0 未分類のため tool が自ら停止する (コード + docs、受入 7207 passed / 20 skipped、変異 9/9 KILLED + erratum 2 件、branch worktree-dev-wave-t598-forward-collection)
---

## 本文

- **本 wave の最重要の発見は、親自身が規約を 2 件破っていたことである。** 実行場所分類の測定は
  「AI セッション・子エージェント・自動化は自分で行わない」とユーザー裁定で明記されている手番だが、
  親は資源量の判定基準だけを読み、手番の帰属を読み落として**正規手順で実測してしまった**。
  さらに段 1 の実測で未分類 tool をログインノードで 6 回走らせた。前 wave (288) も同じことを
  しており、異なるセッションでの独立 2 例である。詳細は {{F:ai-ran-classification-measurement}} と
  {{F:unclassified-tool-on-login-node}}。**測った 140.0 MiB は分類根拠に使わない。**
- **したがって「前向き収集を開始する」という裁定 U-1 は、機構としては満たしたが実データは 0 件である。**
  tool はログインノードで自ら停止し `blocked` を記録する。分類が済んだ瞬間に同じ契約のまま
  baseline が貯まり始める形にした。この「発効したが走らない」状態を隠さず記録する。
- **段 2 のプランは欠測条件を `files_scanned == 0` に置いており、これは誤りだった。**
  同 field は file を開いた数であって filter 一致件数ではない。段 3 の 2 レンズが独立に
  「200 file 読んで対象 0 件」が完全走査の 0 として保存されうると指摘し、親も同じ結論に達した。
  採った規則は {{D:wave-usage-missing-rule}} — 集計 model call 0 は常に欠測。
  wave は Claude が駆動するので真の 0 が存在しないという性質を使い、
  collector の schema を 1 byte も変えずに D220 決定 3 を満たした。
- **段 3・段 6 の 4 レンズはすべて NO-GO を返した。** must-fix は延べ 20 件。親は
  「保存される観測値が偽になる」「規約違反が land する」「非 gate を破って wave が止まる」の
  3 基準だけで裁定し、9 件を採用、4 件を見送り、1 件を却下した。却下したのは
  「文書地図に『正本は tool の `--help`』と書くのは規範 detail の逃がし」という所見で、
  **同じ文書の既存行がまったく同じ書き方で実行場所の正本を指している**ため、
  文書自身の確立した書式であると判断した。
- **親が独自に real 所見を 1 件発見し、fix がその修正で新しい退行を作った。** repo 外検査が
  worktree root 基準だったため本体 checkout の path を受理していた (実測で確認)。
  第 1 巡の fix は `.git` の有無だけで判定し、**過去の job が残した中身が空の `.git` directory を
  repository と誤判定して、正当な保存先を恒久的に拒否する**退行を作った。
  親が再度 probe して検出し、第 2 巡で HEAD の有無まで見る形に直した。
  **規範や検査の fix が新しい不整合を生む型の再発である。**
- **変異の erratum が 2 件。** (1) 初回は期待 node 3 件がパラメータ付きの実 ID と一致せず
  harness が fail-closed した。collect-only で実 ID を取り直した。(2) 2 回目は M3 が MISMATCH で、
  読むと登録した 2 node のうち 1 node だけが赤だった。もう一方は collector を直接叩くテストで
  helper 側の受け渡しに依存しない。**実装が正しく親の登録が過剰だった。**
  初回台帳を erratum として残し、登録を実測へ合わせて再走した。
- **local main が wave 中に 3 度先行した (19 / 3 / 9 commit)。** そのつど取り込み (すべて競合なし)、
  最初の取り込み後 HEAD で変異 anchor 9 件の一意性を再検証してから変異を本走し直した。
  3 度目の incoming は [T-625] の条件 dispatch 追加を含んでいたが、追記先が入口 command 側で
  `docs/dev-wave/**` は 25,196 / 25,200 のまま予算衝突しなかった。
  **受入全走は 3 回走らせ、採る値は最後の `93c35183` での 7207 passed / 20 skipped である**
  (先行 2 回は 7204 passed / 20 skipped。差の 3 件は [T-625] が足したテスト)。
  本 fragment の受入値差し替えだけが同 commit より後の差分である。
- **段 8 の参照文書への統合はゼロ。** 候補 3 件のうち 2 件は既存規則が覆っていた —
  期待 node の形式不一致は `DW-M08` の正規化義務が、変異 runner の cgroup attest race は
  F155/F156 の既定 recipe が既に担う。残る 1 件
  ({{F:fix-narrowed-acceptance-without-positive-control}}) は `DW-M01` の正例登録義務が
  段 4 の文脈でしか発火しないという実測の穴だが、**`docs/dev-wave/**` の余白が 4 bytes しかなく
  `DW-S06-B` へ入らない。** F146 の先例に従い failures 台帳を恒久対応の所在とした。
  予算上限は上げていない。
- エージェント工数: codex 7 本 (プラン起草 1 + 敵対相談 2 + 実装 1 + 敵対レビュー 2 + fix 2 +
  焦点再レビュー 1 の計 9 — うち fix は 2 巡)。実装子・fix 子はいずれも共有計算資源へ届かず
  rc=16 で未実走を正しく申告し、緑判定はすべて親の実走に置き換えた。
- 一次資料 = `output/insights/2026-08-07_t598-forward-collection/README.md`

## 次の一手差分

### 更新

- [T-598] **P2・実装 land 済み → 実データ 0 件 (ユーザー手番待ち)**: consumer を
  `tools/collect_wave_usage.py` として結線し、契約行 62 bytes を `DW-S09` へ入れた
  (`docs/dev-wave/**` は 25,196 / 25,200、上限不変)。欠測規則は
  {{D:wave-usage-missing-rule}}、selector と実行場所は {{D:wave-usage-selector-and-siting}}。
  **収集はまだ 1 件も走っていない** — 実行場所が §7.0 未分類のため tool が `blocked` を記録する。
  残件は {{T:usage-collector-siting-classification}} の分類手番のみで、
  それが済めば同じ契約のまま baseline が貯まり始める。
  base: 434b7867cb8d5871ddc809c189ff3f80b4989ee2445b83ba4ec583c18580c589

### 新規

- {{T:usage-collector-siting-classification}} **P2・新規・ユーザー手番**:
  `tools/claude_session_ledger.py` と `tools/collect_wave_usage.py` の実行場所を §7.0 の手順で
  分類する。手順は専用 scope を作って `memory.current` を sampling する形で、記録項目は
  commit / argv / 入力の総 bytes と件数 / `memory.max` / 観測ピーク / 繰り返し数 / 測定日。
  **AI は測らない。** 参考値 (分類根拠にはできない) は
  `output/insights/2026-08-07_t598-forward-collection/README.md` にある。
  これが済むまで前向き収集は `blocked` を記録し続ける。
- {{T:ai-classification-turn-violation-handling}} **P2・新規・ユーザー裁定待ち**:
  AI が §7.0 の測定手番を実行してしまった件 ({{F:ai-ran-classification-measurement}}) と、
  未分類 tool をログインノードで走らせた独立 2 例 ({{F:unclassified-tool-on-login-node}}) の扱い。
  hook の admission registry は `tools/pegasus/` 配下しか見ないため、他 path の tool は
  規律だけが防壁である。この穴を制度化して塞ぐか、規律のままとするか。
