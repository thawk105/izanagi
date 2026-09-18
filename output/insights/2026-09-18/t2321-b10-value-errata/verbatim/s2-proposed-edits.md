# 追記文言案 (段 2 プラン相当、親起草) — [T-2321]

すべて純挿入 (既存行は 1 byte も変えない)。行番号は worktree HEAD 4e3d1df97 のもの。挿入位置は「直後」= その行の次に空行を挟んで blockquote を置く。

## A. 「24 反復」の訂正 (3 箇所、2 file)

### A1. `output/insights/2026-09-03/t1905-b10-road-and-balanced/README.md` — 但し書き blockquote (L46-50) の直後に挿入

対象主張: L29 表「実規模 (約 17M commit) の 1 反復あたり所要 24 反復ぶん」、L42「全 24 反復が `certified=true` / `verdict=serializable`、anomaly 0」。

> **訂正 (T-2321、2026-09-18、規律 7 の追記訂正)。** 上の表の「24 反復ぶん」と「全 24 反復が `certified=true`」を、範囲を分けて次のとおり訂正する。campaign `ed8a676b` の WAL (`runs/wal.jsonl`、33 行) に残る read-heavy の `verify_done` は **22 反復 = 初期確認 (legacy) 4 + 本規模 (performance) 18** で、22 反復すべてが `verdict=serializable` / `certified=true`、anomaly 0 (`abort` 0 件)。表の本規模反復は **18** (5+5+5+3) で、この 22 の部分集合である。「24」はどちらの範囲にも対応する記録が無い。上の但し書きが引く一次資料 (`verify_done=22`、本規模 18) と同じ値であり、既存行は書き換えない。帯・us/commit・換算は本規模 18 反復を入力としたままで、無効にしない。

### A2. `docs/b10-multinode-formal-run-design.md` — §4 の但し書き blockquote (L145-151) の直後に挿入

対象主張: L136-137「read-heavy の実規模 (1 反復あたり約 17M commit) の所要が 24 反復ぶん残っていた」。

> **訂正 (T-2321、2026-09-18、規律 7 の追記訂正)。** 上の「24 反復ぶん」は、campaign `ed8a676b` の WAL に残る `verify_done` **22 反復 (初期確認 4 + 本規模 18)**、実規模 (本規模) だけを数えるなら **18 反復** に訂正する。「24」に対応する記録は無い。1 反復 1346.9-1465.6 秒・79.6-86.0 マイクロ秒と、そこから出した約 14.0-16.2 時間・1.48-1.71 倍・閾値 66-72 マイクロ秒/commit は本規模 18 反復を入力としたままで変わらない。既存行は書き換えない。

## B. 「5 時間 5 分」の区間 (6 箇所、5 file)

### B0. 一次資料から確定した事実 (insight README に全文、各箇所には B1/B2 の短文)

- request `965996.nqsv`: Started 2026-09-02 01:07:49 JST、Ended 06:56:55、Elapse 20950S、Remaining Elapse 22250S、終了理由 `Terminated` (`scheduler.stderr`)。
- campaign `ed8a676b` WAL (JST): 先頭 `build_start` 01:08:17。3 変種目 `commit` 05:40:56 (開始から 16,387 秒 = 4 時間 33 分 07 秒)。4 変種目 `292d58f1dad8`: `build_start` 05:40:58、legacy `verify_done` 05:42:10、performance `verify_done` 06:06:15 (開始から 17,906 秒) / 06:28:42 (19,253 秒) / 06:52:31 (20,682 秒 = 5 時間 44 分 42 秒、最後の記録)。
- 「5 時間 5 分」(約 18,300 秒) は WAL のどの記録境界とも一致しない。同時代記録 (archive worklog 1187) の「CPU 時間 17,909 秒 / 経過 18,196 秒」(→ 06:11:05) と同時期の走行中 qstat 観測での request 経過時間と整合する。その時点は 4 変種目の本規模 2 反復目の途中で、認証確定は 3 変種。qstat の逐語は残っておらず (投入証拠の `qstat-f.stdout` は投入直後 Elapse 3S の 1 回、撤去セッションの job dir にも無し)、観測時刻は分単位では確定しない。
- campaign dir に journal は無い (`runs/` は `wal.jsonl` のみ)。

### B1. `docs/b10-multinode-formal-run-design.md` §1 — 但し書き blockquote (L20-28) の直後に挿入 (全文版)

> **区間の確定 (T-2321、2026-09-18、規律 7 の追記訂正)。** 「5 時間 5 分」は一次資料の時刻で次のとおり位置づく。request `965996` は 2026-09-02 01:07:49 JST 開始・06:56:55 終了 (`scheduler.stderr`、Elapse 20950S、終了理由 `Terminated`)。campaign `ed8a676b` の WAL では、3 変種目の認証確定 (`commit`) が 05:40:56 (開始から 16,387 秒 = 4 時間 33 分 07 秒)、4 変種目 `292d58f1dad8` は 05:40:58 に build を始め、初期確認 1 反復 (05:42:10) と本規模 3 反復 (06:06:15 / 06:28:42 / 06:52:31) を終えた。最後の完了記録 06:52:31 は開始から 20,682 秒 (5 時間 44 分 42 秒)。「5 時間 5 分」(約 18,300 秒) は WAL のどの記録境界とも一致せず (本規模 1 反復目 17,906 秒、2 反復目 19,253 秒)、撤去判断時の走行中観測 (同時代記録 worklog 1187 の「CPU 時間 17,909 秒 / 経過 18,196 秒」と同時期、06:11〜06:13 頃) での request 経過時間である。その時点は 4 変種目の本規模 2 反復目の途中で、認証確定は 3 変種。観測の qstat 逐語は残っておらず、観測時刻は分単位では確定しない。上の但し書きは書き換えず、値を無効にせず、欠測 attempt の時間を除いた再計算は行っていない。時刻列は `output/insights/2026-09-18/t2321-b10-value-errata/README.md`。

### B2. 残り 5 箇所 — 各但し書きの直後に挿入 (短文版、全文複製しない)

- `docs/b10-multinode-formal-run-design.md` §4 但し書き (L157-161) の直後
- `output/insights/2026-08-31_t1905-b10-formal-run/README.md` 但し書き (L161-166) の直後
- `output/insights/2026-09-02/t2229-t2230-verify-cost-erratum/README.md` 但し書き (L93-98) の直後
- `output/insights/2026-09-02/t1905-b10-multinode-design/README.md` 但し書き (L36 を含む blockquote) の直後
- `output/insights/2026-09-02_paper-story-a6-certification/README.md` EOF 節 (L229 を含む項) — file の宣言に従い EOF 節へ項を足す

> **区間の確定 (T-2321、2026-09-18)。** 「5 時間 5 分」は request `965996` (開始 2026-09-02 01:07:49 JST、終了 06:56:55、Elapse 20950S) の撤去判断時の走行中観測 (worklog 1187 の経過 18,196 秒と同時期、06:11〜06:13 頃) での request 経過時間で、WAL の記録境界とは一致しない。WAL で確定できるのは、3 変種の認証確定まで 16,387 秒 (4 時間 33 分 07 秒)、最後の完了記録 (4 変種目の本規模 3 反復目) まで 20,682 秒 (5 時間 44 分 42 秒)。時刻列と根拠は `docs/b10-multinode-formal-run-design.md` §1 の同名訂正と `output/insights/2026-09-18/t2321-b10-value-errata/README.md`。上の但し書きは書き換えず、値を無効にしない。

## C. 台帳
- worklog fragment 1 件 (完了)。decisions fragment 1 件: 「T-2321 の追記訂正を採用。D1605 理由節の『24 反復ぶん』も同じ誤値で本 D が訂正する (D1605 本文は変えない)」。failures は無し (新しい失敗型ではない)。

## D. 検査
- `python3 tools/check_docs.py` rc=0、`git diff --numstat` 削除 0、`git diff --check` 緑。pin 0 件のため焦点走無し、受入全走は land 経路の 1 走。
