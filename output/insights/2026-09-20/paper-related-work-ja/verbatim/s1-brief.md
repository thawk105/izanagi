# 段 1 brief と依頼の逐語 (wave `dev-wave-paper-related-work-ja`、2026-09-20)

## 依頼 (ユーザー、`/dev-wave` 引数の逐語)

> 本体論文 (日本語) の関連研究節を起草する (docs-only、軽量版 DW-C00、台帳 ID 未起票の新規執筆依頼)。着手直前の local main から fresh
> worktree。正典 `docs/related-work/README.md` と `docs/related-work/claim-survey/` (SysInsight 裁定 2026-09-03、軸 1 の実行記録 2026-08-27 /
> 2026-09-19) の範囲だけで書き、新規の文献取得はしない (D1760 / D1931 で停止。停止を「調査不要」へ広げない)。差別化の核 (説明可能性、軸 3)
> と落とせない限定 3 つは story 2026-09-20 版 §1 の記述に揃え、軸 1 = RW1・軸 3 = RW0 の成熟度を本文の限定として明記する。成果物は
> `output/insights/<日付>/paper-related-work-ja/related-work.md` + README。`docs/paper-story/README.md` の表 1 行と `docs/phase3.md`
> への追記は、稼働中 dev-wave-paper-story-20260920b (README 93 行編集中) / dev-wave-paper-intro-ja (phase3 +6 行)
> と重なるので起動時に重複検査し、両行保持 merge の型で扱う。英訳・要旨・結論・新規実験は scope 外。規律 2 を緩めない。仮想リスク向けの
> gate・検査・台帳の追加は scope 外。

## 段 1 brief (親、handoff の同名節の逐語)

## 段 1 brief (親、20:57 JST)

- **研究前進:** 論文本文の第 2 節 (関連研究) の統制稿を 1 本用意する。序論稿 (稼働中) が「個々の先行との比較は関連研究の節に委ねる」と書く先。
  完了判定 = 正典の限定・成熟度 (軸 1 `RW1` / 軸 3 `RW0`) を 1 つも落とさない散文が、独立 read-only レビューで must-fix 0 になること。実験・図表は増えない。
- **scope:** `output/insights/2026-09-20/paper-related-work-ja/related-work.md` (本文) + 同 `README.md` (wave 記録)、`docs/phase3.md` 現行チェックポイントへ [x] 1 項、
  worklog fragment 1 本。正典 (`docs/related-work/`、`docs/paper-story/`、decisions) は 1 byte も変えない。英訳・要旨・結論・新規実験・新規文献取得・Web は scope 外。
- **確定済み裁定:** D1598 (核 3 点で書く、忠実性・proof chain・provenance は補助)、D1760 / D1931 (軸 1 / 軸 3 の停止 — 「調査不要」へ広げない、`RW1` / `RW0` の
  表現規律をそのまま守る)、DCDS 裁定の落とせない限定 3 つ (LLM が / action 空間自体を拡張 / トランザクションの CC を対象)、CIR+CVN の限定
  (空間の拡張であって固定した原始操作語彙の中の生成ではない)、SysInsight 裁定 §2.7 の 3 限定 + 核にできない狭い能力 3 語、7.7.3 (RW1 = 既存の限定付き文の
  逐語引用だけ、RW0 = 世界の不在を一切使わない)、7.7.2 (内部の不在は母集合 + 走査語を同じ場所に)、D2148 項 11 (一次資料再抽出 docs-only は review 1 本)。
- **不変条件:** (1) 世界の不在の新しい文を作らない・系譜の序数・世界初・「最も近い」を書かない (7.7.3)。(2) 内部の不在は母集合と走査語を併記し内部の不在と読める形にする。
  (3) 新規文献取得ゼロ (Web 不使用、正典に無い書誌・数値を書かない)。(4) 一次資料の判定 (強さ / 極性) を言い換えず、README と claim-survey が矛盾すれば README が勝つ。
  (5) 規律 2 を緩める記述をしない (verifier をループ内に持つことを差別化の (iii) として書く)。(6) 凍結物・正典の bytes 不変。
- **成果物の形:** 平易な日本語の論文本文 (節構成: 位置づけの 1 文 / CC 側の系譜 / AI 探索・進化的合成 / 対象特化の自動合成と検証付き合成 / knob チューニングと SysInsight /
  learned DB components / 自己改善・運用 (簡潔) / 調査の状態と限定) + 末尾「出所 (執筆者向け)」。本文に T 番号は書かず D 番号と一次資料 path は出所へ寄せる
  (先例 = paper-methods-ja / paper-results-ja / paper-intro-ja 稿)。README は wave 記録 (先例 = `output/insights/2026-09-20/paper-results-ja/README.md`)。
- **(P1) paper-story README の「表 1 行」:** 同 README の表は版の履歴 / claim-evidence 系列 / results 系列の 3 つで、いずれも凍結物系列の一覧。草稿を載せる表は無く、
  先例 3 wave (results-ja 09-10 / 09-20、methods-ja 09-20、intro-ja) も README に行を足していない (intro 稿 README「README … は 1 byte も変えていない」)。
  → 親の provisional 裁定 = README 行は足さず `docs/phase3.md` の [x] 1 項だけで登録する。新しい表の新設は hot file への構造変更で、20b wave の編集 (README 93 行) と
  衝突するうえ依頼の「表 1 行」の意味を超える。段 6 レビューの攻撃対象。最終報告で明示する。
- **(P2) phase3 [x] の位置:** 現行チェックポイントの先頭 (results-ja 09-20 の先例)。intro wave は [T-2340] 項直後 → anchor が違い auto-merge で通る見込み。
  衝突したら両行保持 (main 側 → 自分の行) で解く。
- **分割方針:** 軽量版。段 2・3 省略、段 5 は親起草 (実装面ゼロ)、段 6 = read-only codex review 1 本 (2 レンズ: A 一次資料忠実性 = 判定・限定・成熟度・母集合/走査語の逐語照合、
  B 論文散文としての過大主張・禁止句・story §1 整合・平易さ) + 焦点再レビュー ≤ 2 (DW-O16)。変異 matrix は実装差分ゼロで免除 (DW-S04)、受入全走は免除しない。
- **受入・実測環境:** 受入 = `tools/dev_wave_wait.py acceptance --lease-optional` (docs-only、Pegasus 計算ノード、門番は他 wave の leader 数と load)。実測は無し (読み取りだけ)。
- **条件 dispatch の評価 (段 1 前):** DW-O08 / O09 / O10 (freeze・oracle・proof chain・凍結 bytes) = 非成立 (新規 insight dir と phase3 [x] 項のみ)。DW-O13 (gate 新設) = 非成立。
  DW-O11 (削除) = 非成立。DW-O20 = 済。

