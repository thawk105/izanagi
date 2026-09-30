# 段 1 brief — md_5: check_docs.py を判定不変で高速化 (wave: dev-wave-check-docs-speed)

基準: main = 4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed` (branch worktree-dev-wave-check-docs-speed)。
依頼原文: /work/1/SFC/tanab/tmp/speedup-2026-09-29/md_5.txt と common.txt。

- 研究前進 (土台): check_docs は wave ごとに複数回 (段 7 検査・受入 gate・land の fold 検証) 走り、並走 15 wave 前後で共有される。2026-09-29 ユーザー依頼「日常の営みを高速化」の対象。完了判定 = 変更前後の出力 (rc・所見集合、原則 stdout 全体) が main 現物・故障注入版・test_check_docs 全 fixture で一致し、計算ノードの同時刻対照で wall が縮むこと。
- 実測 (計算ノード bnode、request 37675.nqsv、Elapse 78 s、cProfile 下 72.1 s、`/work/SFC/tanab/tmp/check-docs-speed-2026-09-30/base-4f412c67.prof`):
  `_check_backlog_guard` 65.5 s (91%)。内訳: `_line_number` 193 万回 16.2 s (`str.count` を先頭から数え直す、tools/check_docs.py:1381)、
  `_top_level_ids` 6,394 回 15.7 s (同じ entry 本文・section の再解析、:1931、呼出し元 :2971/:2989/:3019/:3121/:3133)、
  `_visible_markdown_lines` 10,382 回 17.1 s (うち所有外 `_mask_html_comments` 517 万回 7.2 s、:1480/:1513)、
  `_iter_carry_references` 95.9 万 carry 28.0 s (:2005、`_top_level_item_raw_slice` 6.8 s :1953、`_is_carry_candidate` 3.6 s :1983)、
  `_archive_is_before` 135 万組 4.8 s (archive 1,645 本の全ペア、:2560/:2536/:3190)。stat は計算ノードで 2.9 万回 1.4 s (login の 25 s は login 側の事情、本 wave の主対象外)。
- 確定済みユーザー裁定: common.txt 第 2・4 節 (検査項目の削除・閾値緩和・対象除外をしない、既存テストの期待値を変えない)、D335/成長比例テスト新設禁止 (memory test-time-regression-rule)、D95 (実装面は Codex author)。
- 不変条件 (P0、攻撃対象外): 任意の入力木について rc・findings・warnings の列 (順序含む) を変えない。`_safe_read_text` の毎回の symlink/lstat 判定と identity 無効化 (T-1222、F381) を変えない。
  `_iter_carry_references` の逐次性 (test_backlog_guard_carry_references_are_streamed が `_top_level_items` を monkeypatch して観測) を保つ。所有外 (tools/dev_waves/launch_authority.py 等) を編集しない。
- (P1) 親の provisional: 最適化は次の 5 種に限る — O1 `_line_number` を改行位置索引 + bisect に (純関数の小 LRU)、O2 同一本文の `_top_level_ids` 再計算を呼出し側で 1 回に (check_transition の sink と entry_has_id の共有、archive 境界の先頭 entry の ids を保持)、
  O3 `_top_level_item_raw_slice` の 1 文字ループを find/正規表現の等価実装へ、O4 `_archive_entry_point` の純関数 memo (例外は非 cache)、O5 `_visible_markdown_lines` 内で `not in_comment and "<!--" not in line` のとき `_mask_html_comments` を呼ばず行をそのまま使う (値は同一)。`_is_carry_candidate` の正規表現の事前 compile は付随で可。
- (P2) main() 全域の無制限 cache (全 entry 本文の解析結果の保持) は採らない — 見込み ~200〜400 MB の常駐増で login の 1 コマンド予算を食う。採るなら peak RSS の実測を条件にする。
- (P3) 期待効果: 72 s → 30 s 前後 (O1 ~15 s、O2 ~10 s、O3 ~5 s、O4 ~3.5 s、O5 ~5 s)。残る成長比例項 (carry 95.9 万件の走査・1 回解析) は次の一手として書く。
- 成果物: tools/check_docs.py (Codex author)、test_check_docs.py への「新実装と旧実装 (test 内に逐語複製した参照実装) の等価性」単体テスト (tmp_path/合成文字列のみ、実 corpus 不到達)、repo 外 probe (差分比較・計測 driver、Codex author、job dir へ退避)、
  一次資料 output/insights/2026-09-30/check-docs-speed/README.md、spool fragment (worklog・必要なら decisions)。
- 判定不変の検証 (段 6): E1 main 現物と故障注入 5〜6 種 (宙吊り carry、entry 番号重複、archive 順序曖昧、CRLF/CR 混在の archive、section 内 fence・HTML comment、carry 文法崩れ) を新旧で走らせ stdout 全文と rc を比較。
  E2 test_check_docs.py 全 node を新旧 check_docs で走らせ、各 subprocess 呼出しの (nodeid, 順番, rc, root 正規化 stdout) を記録して一致比較 + 両走の pass/fail 一致。
  E3 計算ノード 1 job 内で旧/新を交互 (ABAB) 5 回ずつ走らせ wall 分布を並記 (同一 node・同時刻対照)。計算量合計 < 1 node 時間の見込み。
- 分割: author 1 本 (check_docs.py + test、単一 file 所有で一枚岩)、probe author 1 本 (worktree 内 `wave-probe/` に書かせ親が job dir へ退避、所有素集合)。
- 受入: `tools/dev_wave_wait.py acceptance` (計算ノード) を段 6 で 1 回、記録 commit 後に最終。変異 matrix は段 4 で事前登録 (O1 の bisect 境界、O3 の CR 処理、O2 の sink 取り違え、O4、O5 の in_comment 条件)。
