単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md — 親の段 1 brief ((P1)〜(P7)、不変条件、受入・実測環境)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/T-2273-origin.md — 依頼の逐語。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D512-D513.md、D350-D351.md、D2253.md、D2271.md、F264.md — 既裁定・失敗型の逐語。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md — 段 1 前の CPU profile の集計 (発行 child の 99 % が search_repository)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/pin-closure.md — 凍結 pin 閉包と既存 test の一覧 (file:line)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py — `_derive_required_literal` (417)、`_read_search_text` (484)、`_ScanMemo` (497)、`_scan_one` (516)、`search_repository` (592)、`AXIS_TEMPLATES` と key 定数 (60〜110 付近)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_holdout_freeze.py — 380〜1200 行の prefilter / memo / 三段分離の test 群と `_reference_scan_one` (917 付近)。必要な範囲だけ grep / sed で引く。
- 呼出し側の文脈 (変更しない): 同 worktree の orchestrator/campaign/t080_freeze_migration.py (1709 `_draft_reconstruct_holdout`、1889 `_assert_receipt_does_not_pollute_scan`、2000 `validate_draft`、2027 `finalize_receipt`、2256 `_verify_holdout_live_scan`)、orchestrator/tests/test_s8b_oracle_driver.py (1661 以降の発行 child)。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## 目的

自分たちの受入 test 基盤の高速化。受入 shard-0 の律速の一つである T-080 発行 child (約 86 秒) の CPU の 99 % が `s8b_holdout_freeze.search_repository` の走査 (1 回 ≈ 6.6 秒 × 約 13 回) で、その 76 % が `_scan_one` (正規表現 search 1 行 54 %、共通 literal の `in` 19 %) である。`_scan_one` の係数削減の実装プランを起草せよ。

brief の (P1)〜(P7) は親の provisional 裁定であり攻撃対象。より単純で等価な形があれば示してよい。ただし次は不変:
- report の canonical bytes を 1 bit も変えない (D512)。全対象 file の列挙・open・read・decode、例外の型・文言は維持する。
- 呼出しを跨ぐ cache を作らない。memo は 1 回の `search_repository` に閉じ texts identity に束縛 (D512)。production に最適化無効化 knob を足さない (D513)。
- 自作の regex 文法 parser を書かない (D512 却下案)。literal は既存 `_derive_required_literal` の 1 要素 mapping 呼出しで導出する (D350・D512)。
- t080_freeze_migration.py と発行 fixture の走査回数・順序は変えない (P1)。
- ソースに軸 key と具体値を連続 literal で書かない (自己汚染、pin-closure.md の source guard)。
- 仮想リスク向けの gate・検査・台帳・一般化・環境変数を足さない。変更 file は s8b_holdout_freeze.py と test_s8b_holdout_freeze.py を上限とし、他への波及があれば必要性を示して列挙する。

## 書くこと (file:line 粒度)

1. 局所化 search (P2) の変更点と、`compiled.search(text)` の真偽との等価性の論証。W (最大一致長) の取り方 (stdlib `sre_parse` / `re._parser` の `getwidth()`、Python 3.10 で動く形、MAXREPEAT の扱い)、窓 `[max(0, p+len(L)-W), min(len, p+W))` の端の正しさ、重なる出現の扱い、`pos`/`endpos` 付き search が全文 search と同じ真偽になる条件 (helper が非 None を返す文法に anchor・lookaround・`\b` が無いこと)、fallback 条件。str subclass や非 str 式の既存分岐 (`type(expression) is str`、test :508) との整合。
2. 共通 literal `in` の重複 (P3) の削り方と、既存の「共通 literal だけ含む text は軸 search に進まない」挙動 (test :427、fixture の `ycsb_unrelated`) の保存。
3. 既存の発火回数の番人 (P6) — :407 (導出 12 回)、:427 (search 5 回、SearchSpy は `search(self, text)` の 1 引数)、:645、:985〜1097 (三段 0/5/9 と reference 3 回)、:1100〜1196 — の各々について、変更後に何が変わるか、番人の意味 (prefilter を戻す変異・memo を外す変異を殺す) を保つ数え方の改訂案、局所化層だけを無効にした段を同じ fixture で分離する方法 (D513。knob を足さずに reference 実装への差し替えで)。
4. 追加する test (最小): 等価性 (reference 全文 search との per-text 真偽・全 report canonical bytes の一致) を固定する入力 — 単軸 (F264)、literal が text 先頭・末尾・窓境界、重なる出現、値側 `.` が任意 1 文字に一致する形、L が None・W が無限の fallback、8192 byte 以降。
5. 変異候補 4〜6 個を位置と期待 kill node 付きで (窓を 1 文字狭める、`p+len(L)-W` を `p` にする、fallback 条件を外す、共通 literal の memo を text 間で取り違える、等)。各変異が単一理由で赤になるか (他層の mask が無いか、D513 の三段で等価変異にならないか)。
6. 効果の見込み: profile の行別 sample から、変更後に残る走査コストの推定と、その前提 (text の大きさ・出現数の分布は profile から分からない点) を明記。
7. 自己汚染の確認方法 (growth hold を迂回せず `search_repository(root, files=[変更 file])` で)。

## 出力形式

見出し「## 変更点」「## 等価性の論証」「## 既存の番人の改訂」「## test と変異候補」「## 効果の見込み」「## 未決の設計択一」「## 総括」。各項目は file:line を付ける。「## 総括」は 5 行以内。
