# 段 6 裁定 1 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: review-a.md (レンズ A、NO-GO)、review-b.md (レンズ B = 過剰・削除、NO-GO)、親の SMOKE dry-run (runs/probe/result-SMOKE.json: `ValueError: patch applied with offset/fuzz: patches/instr-cicada-trace-m.patch`、stock stack の最初の build)。対象 = 統合 commit bc81d2b6b と job dir の起動器・変異 patch。fix 前の snapshot は `snapshot-pre-fix1/`。

| ID | 裁定 | 処置 (fix 担当) |
|---|---|---|
| S1 (親) M patch が stock stack で offset 付きで当たる | real (must-fix) | U1: M patch の hunk header を `pin C → instr` 後の source の実行番号に合わせ、stock stack で offset 0・fuzz 0 にする。E-max stack (`instr → variant → gc → target → M`) は variant が行を動かすので同じ bytes で offset 0 にはできない。**裁定の改訂: E-max stack では文脈完全一致 (fuzz 0) の offset を許し、hunk ごとの offset を result に記録する。** U2: M の offset 拒否を stock stack だけに限り、E-max stack では `git apply --verbose` の offset 行を result に記録する (fuzz は全 stack で拒否のまま) |
| A1 API 壊しが `API_EXTRA_REGISTER` も出す | real (must-fix) | U1: 終了時の「余分な登録」照合は、どの外部 read 呼び出しにも対応しない read set 要素 (過剰) だけを数え、登録の不足は数えない (不足は呼び出し単位の `API_EXTERNAL` が担う)。壊し API の期待は `API_EXTERNAL` だけのまま |
| A2・B1 壊し B の FIRED 行に `rts_raised` が無い | real (must-fix) | U1: `CICADA_BREAK_FIRED slug=m-early-reclaim` に `rts_raised=<n>` と `gcflag_set=<n>` を足す。U2: FIRED の `rts_raised` と EVENT の `rts_raised=1` の件数の一致も確かめる |
| A3・B3 母集団の等式が独立でない | real (must-fix) | U1: `tx_end_reads_nonempty` を `traceEnd` の中でなく tx の終端 site (書く tx の `writePhase`、read-only の `commit`、`abort`) で `traceEnd` を呼ぶ前に独立に数える。`api_checked` は `read()` 入口でなく呼び出し単位の照合を完了した地点で数える。`reconnoiter_end` の呼び出しを数える集計 key `tx_reconnoiter` を足す。U2: 等式を `tx_commit_write + tx_commit_ronly` = stdout commit 数 = C 行数、`0 <= tx_begin − (tx_commit_write + tx_commit_ronly + tx_abort) <= thread 数`、`b_end_checked_commit + b_end_checked_ronly + b_end_checked_abort = tx_end_reads_nonempty`、`api_checked = read_calls`、`tx_reconnoiter = 0` にする |
| B2 事象側で所有解除が世代加算より先 | real (must-fix) | U1: 事象の順序を裁定どおり `trace_gen_.fetch_add(acq_rel)` → `atomic_thread_fence(release)` → `trace_owner_ = nullptr`・`trace_last_event_` の store → 版の状態変更、に直す。patch 内の順序コメントも合わせる |
| A4 U 壊しは設置対公開を発火させない | real (should) | 実装しない。**裁定の改訂: 壊し U の期待は `U_MISSING_W` (公開対 W) だけ。設置対公開の照合 (`U_INSTALLED_UNPUBLISHED`・`U_PUBLISHED_UNINSTALLED`) の発火は今回確かめず、一次資料に未確認と書く** |
| B4 CUSTOM が stock として合格しうる | real (should) | U2: CUSTOM の run は分類を `custom-diagnostic` に固定し `pass` を返さない |
| B5 対照と同一性 build の重複 | real (should) | U2: `--control-result <result-*.json>` (複数可) を足し、genome・stack・cell・thread・patch 列の sha256・run argv が一致する合格済み stock run を対照として参照できるようにする (見つからなければ同 job の対照を探す、それも無ければ不合格)。IDENT は SMOKE で済んだ ycsb の 2 組を `--skip-ident <genome>:<target>` で外せるようにする |

## 事後検査 (fix 後、親)

- stock stack の `git apply --verbose` に offset 行 0、E-max stack は fuzz 0 (offset は記録)。既存壊し 3 本・新壊し 3 本・変異 3 組の適用 (U1 が実測、親が SMOKE の dry-run で再実測)。
- 変異 patch 3 本は M の変更後も M の上に当たること (U1 が作り直す)。
- 焦点再レビュー 1 本 (DW-S06-C、所見ごとの closed / partial / regressed 表)。
