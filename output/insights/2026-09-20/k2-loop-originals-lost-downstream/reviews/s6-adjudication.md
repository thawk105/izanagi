# 段 6 裁定 (親、2026-09-20 21:2x〜21:3x JST) — read-only レビュー 1 本 (`s6-review-1.md`、gpt-6-astra、12 call、180 秒) の所見の裁定と fix

レビューは NO-GO (must-fix M1〜M7、nit 2)。「択 A 自体を棄却する技術的根拠は見つからなかった」「NO-GO は証拠の強さを正確に伝えるための文書修正に対するもの」。
所見は全件 real・採用。実装面ゼロなので fix は親が docs を直接直す (DW-C00)。fix 後に焦点再レビュー 1 本 (`s6-focus-1.md`、DW-O16)。

| # | 所見 | 判定 | fix |
|---|---|---|---|
| M1 | roundtrip 行の「値のみ / 内容の一部 / 無し」に走査根拠が無い。走査対象に roundtrip insight が無い | real | 追加実測 `scan_roundtrip.py` (6 root 615 file、21:23 JST、roundtrip 5 file + round 3 lock / digest / WAL の sha 一致と `start_wall` 語の有無)。README §1 の各行に「走査 (a) で 0 件」を付け、走査範囲の段落を (a)/(b) に分けて書き直した。log §8 |
| M2 | B-6 (c) の限定が digest だけ。WAL (bytes 不一致)、round 3 lock (`f1ab4966…`、round 2 写しは別 bytes) も含める | real | README §2 B-6 (c) を書き直し (critic-3 の読取対象 5 種のうち bytes で残るのは受領証と loop_state 再構成だけ、critic-2 の読取対象は scratch に bytes 一致) |
| M3 | B-6 (d) の「完全に再検算できる」は pair 試行だけ。3 巡の未達は各巡の記録・残存資料へ対応づける | real | README §2 B-6 (d) を 3 巡 / pair に分けて書き直し |
| M4 | §4 の「派生物 = 原本」「A と B の provenance は同じ」が過大。sha 一致 (loop_state / AO)・内容同一 (WAL)・不在 (digest / lock)・未作成の次巡完全入力を分ける | real | README §4 を書き直し (証拠の強さの前提を先に置き、A のやらない理由 = 派生物依存が残る、B の利点 = 次系列の依存範囲が減る、C は混在を明示すれば一律に劣るとは言えない) |
| M5 | worklog fragment が次巡の記録文を A 前提で無条件に書く | real | fragment と README §2 [T-2795] 行を「択 A なら…、B / C なら実際に選んだ入力元を書く」に変更 |
| M6 | reconstruction-log の「stdout の逐語」が実態 (sha 省略・注釈) と一致しない | real | log 冒頭を「抜粋・要約」と明記し、生 stdout の逐語を `materials/reconstruction-stdout.txt` (tee の .log を連結) に置いた。初回の sha256sum は tee していないので `sha_capture.py` で 21:24 JST に採り直した |
| M7 | 記録 wave の結論 (roundtrip は sha256 も無い / lock 照合不能) を「矛盾しない」と整理するのは結論まで正当化する。「未記載だったが 3 巡稿で記録が見つかり補正する」と書く | real | README §0 と s4-ruling P1 を「補正する」に書き直し。記録 wave が生きていれば advisory を送る (段 7) |
| nit | 「round 2 `planner-input-2.json`」は roundtrip の materials | real | README §1 を修正 |
| nit | 「whiteboard の実測 (811,956)」→ `current_perf` の実測 | real | README §4 択 C を修正 |

レンズ (b) の判定の取り込み: 択 A = 説明の過大は成立、原本欠落による実行不能は不成立 (harness `k2_next_generation_inputs` / `planner_context_payload` / 値域検査 / `drive_iteration` /
`check_stop` は旧 root の bytes を要求しない)。択 B = 「A と provenance が同じ」は不成立、B を拒む code 上の理由は無い、研究目的次第で合理。択 C = 出所混在は成立、技術的不成立は不成立。
付随項 = scope 外に当たらない (既存 `git worktree lock` の適用)。加えて本 wave は 21:24 JST に pair 原本 6 file を T-2795 job dir へ byte 複製した (lock の代わりではない)。

fix 後の追加 (レビュー後の docs delta、親所有): worklog fragment に新規 T「README stale 注記へ 1 段落」(P3) を足した (story 20260920b wave が「未着地 wave の内容は書かない」規律で
README へ書かないと返答したため)。焦点再レビューの射影に含める。
