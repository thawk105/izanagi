# 段 2 plan への親 addendum (2026-09-18 15:55 JST) — 段 3 の攻撃対象に含める

plan の裁定パッケージ候補 1〜5 に対する親の provisional 応答。段 4 で確定する。

## (A1) P5 の逆転経路を塞ぐ: 有界走査 + 条件付き再走査
- 旧版は path ごとに `--max-count=limit+1` で止まる。union 走査を無制限にすると、少数 path で上限に早く達する入力 (例: `docs/worklog.md` 1 unit) で旧版より遅くなる逆転経路がある (plan の指摘は real)。
- 対策: union 走査に `--max-count=K`、K = (limit+1) × |P| を付ける。走査が返した distinct commit 数を n とし、
  - n < K → 履歴を歩き切った → 全 path の派生列は完全 (旧版と同一)。
  - n == K かつ全 path が limit+1 件以上 → 全 path 飽和 → 完全 (各 path の派生列は同じ走査順の prefix なので旧版と同一)。
  - n == K かつ未飽和 path あり → その path の列が不完全な可能性 → **無制限で 1 回だけ歩き直す** (2 本目の `Git.run`)。
- |P| = 1 なら K = limit+1 で旧 command と同形 (出力形式だけ違う)。旧版の「時間内に集め切れる入力集合」を縮めない: 再走査が要る入力は旧版でも path ごとに独立走査していた入力であり、新版の合計 ≤ 旧版合計 + 有界走査 1 本。
- `--max-count` は commit 数を数える (merge の親別 entry は 1 commit)。実装は distinct H の数で n を数える。要検証 (段 5 の test で fixture を持つ)。

## (A2) framing: `%x1e` をやめ `--format=%x00%H` にする
- 実測 (git 2.34.1、`-z`): entry = `\0` + `<H>` + `\0` + `\n` + (`<name>` + `\0`)*。name は非空で NUL を含まないので、**NUL 区切りで割ったとき空 field の直後が header** — 任意の合法 file 名 (RS・LF・CR・先頭 LF を含む) と衝突しない。header 直後の field は必ず `\n` で始まり (git の区切り)、**ちょうど 1 個の LF を剥がして** name1 とする (name が LF で始まっていても保存される)。
- 文法 (strict): stream := (`\0` H `\0` `\n` name (`\0` name)* `\0`)* 。逸脱 (H が 40/64 hex でない、header 直後の field が `\n` で始まらない、name が空、UTF-8 不正、末尾 `\0` 欠落) は `AssessmentError("history-candidate-parse-error", outcome="error")`。空 stream は候補 0 で正常。
- `-c log.showRoot=true` は `GIT_CONFIG` 定数の後、`log` の前に置く (`git.run(["-c","log.showRoot=true","log",...])`)。

## (A3) argv 上限: `--stdin` は使わない。超過時は旧 per-path command へ fallback
- 推定 argv bytes (Σ(len(path utf-8)+1) + 固定分) が上限 (定数、例 256 KiB) を超えるときだけ、供給 object は union を作らず path ごとに旧 command (`log --full-history --format=%H --max-count=limit+1 <main> -- <path>`) を遅延実行する (D2054 の `batch_safe` fallback と同型: 一括できない入力は従来経路)。LF/CR を含む path も従来経路のまま通る (argv は任意 bytes を運べる)。
- `--stdin` は `strbuf_getline` の CR/LF 処理で path を変えうるので採らない。

## (A4) timing: plan 案を採る
- `SearchResult.elapsed_seconds` は関数入口からの経過のまま (初回要求 unit に走査時間が乗る)。`timing.history_candidate_walk_seconds` と `timing.history_candidate_walks` (本数: 0 / 1 / 2、fallback 時は path 数) を別記。brief (P6) の「照合のみ」は撤回。

## (A5) timeout 下の同一性の主張範囲 (事前登録)
- 主張する: 正常完走時の候補列・verdict・unit・evidence・summary の同一 (timing 系 field を除く)。timeout 時は verdict が `indeterminate` であること (旧版と同じ class)。
- 主張しない: timeout 時の `reason` の一致 (旧版は unit ごとの走査のどれが切れたかで `assessment-timeout` / `one-or-more-states-unproven` が分かれる。新版は初回要求 unit で切れる)。parse 対象拡大 (上限の先まで解析) による `history-candidate-parse-error` の早期化。
- 受入条件: 固定 OID 559bcbc29c… で (i) 候補列 33/33 一致 (probe)、(ii) 旧/新 payload の timing 系以外 byte 一致、(iii) git 子 process 数 244 → 減少、(iv) 同時刻交互 A/B で wall 短縮。checker-timeout 解消は条件にしない。

## (A6) memo と失敗の記憶
- 供給 object は成功 memo と失敗 (AssessmentError) を記憶し、2 回目以降の要求で再走査しない。失敗は同じ例外を再送出する (旧版: 非 spool unit では 1 回目で assess が止まる、spool unit は unit ごとに捕捉 → 新版でも同じ経路)。
