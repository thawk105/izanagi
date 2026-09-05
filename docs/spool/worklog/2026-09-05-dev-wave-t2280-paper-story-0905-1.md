---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t2280-paper-story-0905
seq: 1
title: [T-2280] 論文ストーリー 2026-09-05 版を全面再導出で書いた — 軸 3 の核を D1598 の 3 点へ書き直し、A-2 の既完走 4-cell が採用構成を build していなかった事実を D1645 に従って取り込み、前版を 5 箇所訂正した (docs のみ、branch worktree-dev-wave-t2280-paper-story-0905、実装面 0・変異 matrix 免除)
---

## 本文

- 依頼は「`docs/paper-story/2026-09-05.md` を新版として書く。核は D1598 の 3 点、忠実性・proof chain・試行
  provenance は補助へ。差分改訂は禁止なので 09-02 版以降の決着を全項目で取り込む。裁定待ちは裁定待ちと書き、
  数値・日付・判定は一次資料からだけ引く。docs のみ、実装差分ゼロ」。
- **依頼の前提 1 件を起動時に覆した。** 「稼働中」とされた paper-story-backoff-scaffold wave は同日 07:20 に
  land 済み (commit dc02a6248) で、編集面の重複は無く、docs/README.md の地図更新も不要だった。
- **09-02 版の訂正は 5 件。** (1) adaptive backoff の「到達不能」「離散状態の被覆」を機構一般として書いた
  4 箇所 (README の stale 注記 1 が指していた箇所、D1505 / D1506)。(2) A-2 attempt `t2022-20260828c` の
  adopted cell は patch 無しの木で build され `BACK_OFF=1` 対 `BACK_OFF=0` を測っていた (T-2228 の
  一次資料、F707 再発)。(3) その correctness も同じ driver の source routing から導出上は同じ木で、
  「write-heavy と balanced は性能 workload そのもので certification を取った」は成り立たない
  (correctness 側の独立記録は無い、D1257)。(4) §2 (g) の見出し「主張は 1 行も増えていない」が同版 §6 と
  矛盾したまま残っていた。(5) §0 の「訂正は別に 6 か所」が同版冒頭の 7 と食い違っていた。(4)(5) は
  段 6 レビュー A の所見。
- **執筆中に local main が進み、ff で 3 回取り込んで版へ反映した。** /rulings 第 9 回 (1277、D1644〜D1649) で
  [T-2338] が D1645 (A-2 の結論は正しい identity で取り直すまで論文素材から外す、追記訂正と results 新日付
  file は AI 作業) と [T-2337] が D1644 に裁定され、草稿の「裁定待ち」を「裁定に従う」へ書き換えた。
  1278 で [T-1675] 予算承認の発行と [T-2146] 鍵対の配置がユーザー自身の実行で済み、D1638 が想定した
  「AI が鍵を生成した場合の限界」は発生しなかったので、草稿の「受領証の AI からの独立を主張しない」を撤回し
  「鍵はユーザー生成・script は AI 起草・hooks の防護追加は未実施」の 3 点併記へ直した。
- **段 6 は read-only codex レビュー 2 lens (stale 引き写し・出所 / 主張の強さ・非対称性・裁定の先取り)。**
  所見 15 件 (A 6 / B 9、両 lens 共通 2)、real 12 / partial 1 / refuted 1 / 裁定着地で準拠へ 1。
  最重要 3 件: A-5 と A-6 の停止原因の同一視 (A-5 は関門の preprocess 段で `config.h` 不在、A-6 は計算ノードの
  network 不在)、A-2 correctness の build identity を直接観測のように書いていた (導出へ書き分け)、D1598 の
  3 点を certified な単一鎖に強めていた。refuted は「参照を basename に統一せよ」(前版と同形・check_docs
  準拠・basename では一意にならない)。修正後の焦点再レビュー 1 本は closed 10 / partial 4 / regressed 0 /
  refuted-by-parent 1 (レンズは不同意) と新規 2 件 (§7 の鍵儀式 stale、§10 の件数不整合) で NO-GO を返し、
  親が 6 件を直接直して閉じた (3 巡目は起動せず)。所見と裁定の全文は新版 §10、逐語は job dir の codex 成果物。
- 未着地の稼働 wave (T-2301 / T-2293 / T-2090 / B-10 read-heavy 正式走 977647) の成果は取り込まず、
  「この版の時点で正典に無い」と書いた。
- エージェント工数: codex 子 3 本 (review 2 + focus 1、`gpt-5.6-sol` / xhigh、read-only。review は model call
  44 + 26、focus は receipt 参照)。実装子 0、新規計測 0、変異 matrix 免除 (実装面 0)。三軸語 CLI 走査 rc=0 (commit 前後とも
  conjunction_hits 空、positive_control 146)、check_docs 緑、git diff --check 空。
- 段 8 の改善候補: なし。

## 次の一手差分

### 完了

- [T-2280] 2026-09-05 版 (`docs/paper-story/2026-09-05.md`) で軸 3 の核を D1598 の 3 点へ書き直し、README を更新した。
  A-2 の追記訂正と results 新日付 file は [T-2338] (D1645) が持つ。
  remaining: none
  base: 6bc0b0bbe484c6d30ab610444c0bcd43947d7401a8c0663b2f56dde52bce6647
