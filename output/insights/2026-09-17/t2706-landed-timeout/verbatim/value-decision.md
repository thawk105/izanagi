# 値の確定 — COMMAND_TIMEOUT_SECONDS (親、段 4 の事前登録規則を 30 件完了後に適用)

## 入力 (固定)
- JSONL `timing-lifted-2.jsonl` (job dir 原本名 `timing-lifted-2.json.jsonl`) sha256 `d53424b91904673df4b46ee41802ad17654bf408b17bf2d8e7cdc2950f2a4a1f` (30 run、git command 2,935 本、打切り 0 本)
- 母集合: `docs/unreachable-object-ledger.md` の到達不能 commit 30 件 (T-2640 で記帳・救出済み)。proof unit 数 1〜42 (中央値 13)
- 観測 regime: pegasus02 login node、git 2.34.1、main `b4631a92e` (11,246 commit、packed 176,575 object、19 pack、579 MB)、2026-09-17 06:5x〜07:2x JST、load average 24 → 92 (他 wave の codex 子 4 本と test 走行 11 本が同居)。適用先 (rescue gate / cleanup の判定) も同じ login node なので regime は一致する
- 上限を 300 秒に持ち上げた「無中断」走。壁時計 10.2〜250.6 秒 (中央値 52.6)、合計 2,194 秒

## 操作別の完了時間 (秒、nearest-rank p95)
| 操作 | n | 中央値 | p95 | 最大 | 層 |
|---|---:|---:|---:|---:|---|
| `log --full-history --max-count=1 --find-object=<oid> <main>` | 8 | 16.35 | 26.87 | **26.87** | 決定的 (負証拠 `not-landed` に必須) |
| `log --full-history --format=%H --max-count=1025 <main> -- <path>` | 349 | 3.84 | 9.11 | 21.29 | 決定的 (exact state 探索) |
| `cherry -v <main> <oid>` | 30 | 4.17 | 12.91 | 13.66 | 観測 (patch-id、timeout は捕捉して続行) |
| `rev-list --topo-order` (history scan / closure) | 36 | 0.51 | 1.16 | 1.19 | 決定的 |
| `ls-tree` | 1,089 | 0.05 | 0.25 | 1.16 | 決定的 |
| `diff` / `cat-file --batch` / `show` / `cat-file --batch-check` / `diff-tree` / `rev-parse` / `cat-file` / `for-each-ref` | 30 / 10 / 19 / 341 / 49 / 270 / 674 / 30 | ≤ 0.84 | ≤ 1.11 | ≤ 1.12 | 混在 |

## 規則の適用
- 全 command の最大 = 26.87 秒 (`log --find-object`)。× 1.5 = 40.3 → 格子 {10, 15, 20, 30, 45, 60} の最小の上 = **45**。45 ≤ `DEFAULT_TIMEOUT_SECONDS` (60)。
- 倍率 1.5 は親の判断値。同じ操作 (`--find-object`) が load 24 で 13.2 秒、load 92 で 26.9 秒と 2 倍の幅を持つことが観測されたので、最大に 1.5 倍を掛けた 45 は「観測最大の 1.67 倍」の余裕になる。30 (暫定) は 1.12 倍で、規則の出力でもない。
- 反復点検 (B2、`repeat-heavy.json`、load 27〜40、30 件走の直後): `log -- <path>` 69 本 (cd066a04 の 23 path × 3) = min 1.95 / 中央値 7.87 / **最大 35.94** 秒 (同じ path が 9.6 → 35.9 秒と 3.7 倍の幅、共有 /work の I/O 競合)、`--find-object` 3 本 = 11.34 / 17.50 / 20.76、`cherry` 3 本 = 2.43 / 2.85 / 6.87。反復の最大 35.94 ≤ 45 なので手順どおり 45 で確定 (余裕 1.25 倍)。暫定 30 では反復の 2 本 (35.9 / 30.5 秒) が超過していた (25.4 / 24.3 秒の 2 本も 30 に近い)。60 は全体予算と同値で `min(c, remaining)` により per-command 上限が無意味になる (B3) ので採らない。
- cap ごとの上限超過 command (30 件・2,935 本): cap 5 → 136 本 (`log -- <path>` 117、`cherry` 11、`--find-object` 8)、cap 10 → 25、cap 15 → 11、cap 20 → 3、**cap 30 以上 → 0**。
- 無中断推計 (完走 : 確定 / 30): 予算 60 → cap 5 で 3:0、cap 10 で 10:1、cap 20 で 15:3、**cap ≥ 30 で 16:4**。予算 120 → cap ≥ 30 で 27:6。予算 300 → cap ≥ 30 で 30:6。予算 8 (rescue 内部) → どの cap でも 0:0。
- 予算 60 で cap を上げても完走しない 14 件は、いずれも全体予算 60 秒の枯渇 (`min(cap, remaining)` の remaining 側が先に尽きる)。推計で最初に予算切れになった操作は `log -- <path>` 12 件、`--find-object` 1 件、終端 ref 確認の `rev-parse` 1 件 — cap ではなく全体予算 × 必要操作の合計の律速。
- verdict 内訳 (持ち上げ走): landed 2 / not-landed 4 / indeterminate 24 (うち refs-moved 1、one-or-more-states-unproven 23)。observations / ref_snapshot phase は 30 件とも matched (300 秒予算)。採用値 45・既定予算 60 での実走は `live-new-45s.jsonl` (段 7 で件数を記録)。

## 確定値
**`COMMAND_TIMEOUT_SECONDS = 45.0`** (反復点検でも覆らず確定)。

## コメント文面 (逐語、2 行、既存コメントと同じ英語)
```
# T-2706 / D2104 item 24: 30 unreachable commits measured on the login node (main 11,246 commits, load 24-92):
# max per git command 26.9s (find-object; path log 21.3s, repeat check 35.9s); max x1.5 -> 45, <= DEFAULT_TIMEOUT_SECONDS.
```

## 変異事前登録の訂正 (段 6、レビュー A RA1 / B RB2 / 焦点再レビュー)
- **M6 (`_regular_decision` の `any_path.incomplete` → not-landed) は登録から除外する。** 理由: `_find_object_any_path` の timeout は `Git.run` の `AssessmentError` として `_proof_unit` (非 spool) で捕捉されず最上位へ伝播するため、`any_path.incomplete` が真になる経路が現行コードに無い (any-path 探索は matched / not-matched を返すか例外を伝播する)。M5 を併用しても当該分岐へは戻らない。両層変異 (例外を incomplete な `SearchResult` へ変換する層 + 分岐の反転) は一箇所置換の条件を外れ帰属も曖昧になるため、本 wave では登録しない。
- 登録は M0 (等価)・M1〜M5・M7 の 7 件。専属 killer とは書かず、主担当 node と全検出 node を台帳の観測で記す。
- F1 (焦点再レビュー、nit): `__cause__.timeout == approx(0.05)` は wrapper の `remaining() > 1.0` と `Git.run` 内の再取得の間で 0.95 秒超の停止が起きたときだけ偽赤になる。発生には隣接 2 文の間の秒級停止が要るため fix せず記録に留める。
