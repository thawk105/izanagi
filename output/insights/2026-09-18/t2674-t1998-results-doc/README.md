# [T-2674] [T-1998] balanced stock-inline 対の単独 results 稿 — wave の一次資料 (2026-09-18)

- authority: none / default_effect: no-state-change — 本書は wave の経緯・実測・レビューの索引であり、性能の測定原典ではない。
  **本 wave で測定は 1 回も走らせていない。凍結物 (事前登録・成果物・既存稿) の bytes は 1 byte も変えていない。**
- wave: branch `worktree-dev-wave-t2674-t1998-results-doc`、worktree `.claude/worktrees/dev-wave-t2674-t1998-results-doc`
- 起点 main: `302b94796` (11:01 JST の local main)。11:18 JST に `99fcf2323` を ff-only で取り込み (編集面に差分なし)
- 種別: docs のみ (`docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md` 新規、
  `docs/paper-story/README.md` の results 表 1 行)。実装面差分 0、変異 matrix は `DW-S04` の免除。
  read-only codex 子 3 本 (段 6 レビュー 2 レンズ + 焦点再レビュー 1 本、いずれも `gpt-6-astra` / `medium`)。
- 成果物: 統制稿 (results 系列の凍結物) と README 行。裁定の出所: D1874 / D1993 項 6 / D2044 項 3 / D2120 項 15 / D12 / 絶対規律 7。

## §1 着手前実測 (段 1)

一次資料の現物を親が読み、稿へ写す値を確定した。要点は `verbatim/s1-brief.md` (段 1 brief と実測要点) と
`verbatim/wal-table-parent-derived.txt` (WAL 40 record からの 8 genome 表・統計量の再計算) にある。

| 項目 | 実測 | 出所 |
|---|---|---|
| 成果物 root (repo 外) | 23 file。result.json `354ecd5f…`、reservation.json `45cb2cf1…`、campaign.lock `ba24c65d…`、wal.jsonl `154ab894…` (lock / WAL は result.json の `lock_sha256` / `wal_sha256` と一致) | `sha256sum` |
| WAL | 40 record = 8 genome × 5 stage、`env_tag` は `pegasus` のみ、abort 0 | 親の読取 script (job dir) |
| 登録 2 arm | baseline `84319b1127a6` (src_token `stock`、source `2d691b45…`)、target `93c62227a2d3` (source `678b7203…`)。5 標本・median・cv (標本標準偏差/平均)・ratio 1.1122537536191646・improvement 11.225375361916456 は再計算で全桁一致 | WAL、result.json、decision-final.json |
| 事前登録 blob | `464e3af5…` (測定 commit `a551cdd3` の blob と現行木で同値、Erratum なし) | `git show` + `sha256sum` |
| 測定 commit の blob | job body `dff913cb…`、投入器 `dff1f9d0…`、pipeline.py `2423849c…`、p2_2.py `9b30a7ad…`、env_contract.py `292bbed3…`、loop.py `785dd6fe…` (以上 4 つは lock の loader 束縛 63 blob と一致)、backoff_sweep.py `5d55cbbb…` (loader 束縛外)、patch file `a5e0710c…` | `git show` + `sha256sum` |
| 図 | `docs/paper-story/figures/` に T-1998 の図は 0 件 | ls |
| 活動を止める裁定 | 0 件 (「単独稿」「results 系列」「統制稿」「結果節」を D1993 以降で索引。hit は D1993 理由節と D2120 項 15 で、いずれも支持側) | grep |
| 編集面照合 | README results 表 / results dir を触る未 land branch は `t2775-paper-story-a1-attempt1` (README の stale 注記節、別 hunk) と `t2498-executor-recurse-old` (merge-base が古く main 側追加が差分に見えるだけ) の 2 本。衝突なし | job dir の overlap_check.sh |

2026-09-15 の main 再解析の判定 JSON は dev-wave の job dir を内容 (`1.1122537536191646`) で走査しても
2026-09-14 の `decision-final.json` 1 件しか無い (稿 §4 (b) の根拠)。

## §2 段 4 裁定 (親)

- 段 2・3 は省略 (docs-only、scope は依頼文が固定。`DW-C00` の既定軽量版)。段 6 は凍結物 (append-only で in-place 訂正不能)
  なので read-only 2 レンズ (A: 数値・逐語・識別子の照合 / B: 過剰・削除・限定・裁定整合) を 1 巡 + 焦点再レビュー 1 本。
- (P1) 8 genome 全点の producer 記録を表として載せる (推定量には入れない旨を明記)。依頼文の「8 genome 分の campaign 記録を
  含む一次資料全体」を根拠にした編集判断。段 6 レンズ B が「全点掲載は依頼の要件ではない」と異議 → 表は残し、登録外 2 点の
  比較文と hash 余談を削って注意書き 1 文にした (部分採用)。
- (P2) 正しさ検査の条件 (4 thread・200 tuple・rmw・1 秒・max_ope 5) は WAL に無く、lock が束縛する pipeline.py の
  `CorrectnessWorkload` 既定値から導いた → 「束縛された code から導いた値」と書き分け。レンズ B が「既定値の列挙だけでは
  実行条件の導出にならない」と指摘 → 呼出し経路 (loop.py が `correctness` を渡さない、lock の search_config に `verify` key 無し、
  WAL `verify_configs=["legacy"]`) を足し、「実行時 argv の記録ではない」と明記した。

## §3 段 6 レビュー (逐語は `verbatim/`)

| 子 | 所見 | 総括 | 親の裁定 |
|---|---|---|---|
| レンズ A (`s6-review-lensA.output.md`、model_calls 22、wall 471 秒) | must-fix 7 / should-fix 2 / nit 0 | 着地を止める | 9 件すべて real。是正 commit を最初に含む main first-parent 上の commit は `b1a3d45d…` (08:30:25 JST) — 親の `--since` 付き走査が `291892b90…` (11:40:29) を返したのは取り逃し。終了時刻・Elapse の出所は stdout でなく stderr (NQSV の終了要約)。`genome` の階層、lock の `ycsb_*` key、`perf_counter_statuses` の list 型、result.json の 23 key、事前登録 §4 冒頭の引用、`preregistered` block の限定、A-2 / A-6 検査回数の出所 (D1993 理由節) を訂正 |
| レンズ B (`s6-review-lensB.output.md`、model_calls 6) | must-fix 1 / should-fix 4 / nit 1 | 着地を止める | 6 件すべて real (所見 4 は部分採用)。限定 5 の温度ドリフトの断定を撤回、§1.4 の patch 適用断定を弱め、§2.3 に呼出し経路を足し、§4 を 3 区分 (成果物に無い / 束縛の範囲 / 本稿で未照合) に再構成、冒頭と README 行の経緯重複を削減 |

親の手打ちで `tracked_diff_sha256` を 1 桁誤り (`986dc` → `986cb`) — 機械照合 (job dir の `verify_doc.py`: 稿の全 sha256 と数値を
権威 bytes から再計算して突き合わせる) で捕まえて修正した。**稿への sha は手打ちせず現物から貼る。**

fix 後の機械照合: 完全形 sha256 38 件すべて現物と一致、8 genome の標本・median・verify 件数の未掲載 0、
ratio / improvement_percent / cv 全桁一致。`check_docs.py` rc=0、`git diff --check` 緑、三軸語走査 (holdout rr20 / rr80) hit 0。

## §4 焦点再レビュー (fix 後、`DW-O16`)

`verbatim/s6-focus.output.md` (対象 commit `e31030990`、model_calls は receipt のとおり)。
**所見 15 件の対応表: closed 12 / partial 3 / regressed 0。新規所見 0。「着地は止めない」。**
検算は 23 key / 40 record / 63 blob / 限定 20 件 / §4 の 5+2+3 項目 / 23 file (0 byte 9) / 主要 4 file の bytes /
receipt 2 行 / stdout 268 行 / 8 点の median と cv / ratio / 全 sha256 / §2.5 の時刻 / 事前登録 §4 冒頭の逐語まで、
すべて現物と一致。§2.3 の呼出し経路 (loop.py `785dd6fe…`、`_closed_verify_workloads` は `verify` key 不在で None、
`evaluate` に `correctness` 指定なし、`backoff_sweep.py` にも上書きなし) も現物で確認された。

partial 3 件の扱い: B-4 (8 点表の存置) は編集判断として据え置き。B-5 の残存 (§2.1 の「保全されていない」の断定) と
B-6 の残存 (§5.5 の経緯重複) は焦点再レビュー後に直した (commit は §5)。
焦点再レビューが挙げた量化の限界 2 点 — 「投入 1 回・2 本目なし」は指定 receipt・成果物と事前登録 §7 の規則からの記述で
全保存先の不存在監査ではないこと、2026-09-15 の「全桁一致」は insight README の記録であり判定 JSON との独立照合ではないこと —
は稿 §0.1 と §2.1 / §4 (b) の書き方と整合しており、追加の断定は足していない。

## §5 受入・land

受入全走は land 経路で 1 走 (門番 + 連結版の script を job dir に置き、結果は land の受領証)。

## §6 閉じないもの

- 統制稿 §3 の限定 20 件と §4 の 10 項目はそのまま残る。本 wave はそれらを解消していない。
- 2026-09-15 の再解析の判定 JSON が保全されていないこと (§4 (b)) は本 wave でも直していない (再解析を走らせていない)。

## §7 回収時の訂正 (2026-09-18)

§5 の「受入全走は1走」は実記録と一致しないため撤回する。旧最終 `acceptance-final-6.done` は70であり、
受入成功でもland完了でもない。回収木の独立監査・検査は `recovery.md` と今回の受領証へ分ける。

§6 の「判定JSONが保全されていない」は、参照したjob dirでは確認できなかった、という範囲に訂正する。
未発見から未保全・復元不能を導かない。§4 の「2本目なし」と稿の整合という説明も、
指定receiptと当該waveの記録が示す1試行という範囲に限定する。事前登録の投入回数規則は
他の投入の不存在を証明しない。results入口の追補を併読する。原稿・原測定のbytesは保持した。
