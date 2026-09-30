## 所見ごとの判定

判定対象は指定の HEAD `2aff9ff54`、起動器 v7、提示された result です。`closed` は当該裁定の処置を満たす判定であり、下記の新所見まで解消した意味ではありません。

| 所見 | 判定 | 根拠 | 残る問題 |
|---|---|---|---|
| D1 壊し B の compile | **closed** | [B patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-early-reclaim.patch:21) の待機は `rdtscp()` と `FLAGS_clocks_per_us` を使用。`smoke-5/result-SMOKE.json` の B 2 run は `hostname=bnode036`、build 記録あり、`rc=0`。記録された patch SHA-256 は現物と一致。 | なし |
| D2 build dir の再利用 | **closed** | [起動器:1045](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:1045) で試行ごとに `build-{build_attempt}`、[同:1072](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:1072) で失敗した依存 build を記録。smoke-5 の `builds=8`、`exceptions=[]`。 | 失敗後の継続経路そのものの実測は提示 result にない。 |
| D3 違反 kind の接頭辞 | **closed** | [M patch:101–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:101) は集計 label から `v_` を除いて出力。smoke-5 の `m_violations[].kind` は `B_RETIRED`、`U_MISSING_W`、`API_EXTERNAL` として解析済み。 | なし |
| D4 default の B 到達 | **closed** | [B patch:16–35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-early-reclaim.patch:16) は 1/64 選択、待機中に下限を再取得。smoke-5 default B は `reached=1227`、`changed=rts_raised=1013`、`B_RETIRED=3273`、`expected-detection`。 | なし |
| D5 B 計数の順序 | **closed** | [起動器:317–325](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:317) は B に `reached≥changed`、`reached≥committed`、`changed=rts_raised` を適用。smoke-5 default の `changed=1013 < committed=1227` を正しく受理。 | なし |
| D6 B の帰属鍵 | **closed** | [起動器:368–390](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:368) は重複を拒否し、`rts_raised=1` の `(thid, tx_seq)` だけを帰属鍵にする。smoke-5 の `attribution.matched` は default **3273/3273**、best **3715/3715**。 | tx 単位の帰属と個々の違反の因果関係は同義ではない。N2 参照。 |
| D7 記録済み result の再分類 | **partial** | [起動器:791–865](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:791) に `--reclassify` があり、元 path と別の出力を要求し、raw と verifier JSON の digest を検査する。 | 提示された result には再分類の実行結果がなく、動作の実測までは判定できない。 |
| D8 `#line` のずれ | **closed** | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:179) の `#line` は focus2 対象版から修正済み。`ident-4/result-IDENT.json` では stock 8 組と E-max 2 組の全 TU で `instructions_sha256` が左右一致。M patch の記録 SHA-256 も現物と一致。 | 命令列ハッシュの正規化による取りこぼしは N3 参照。 |
| D9 前処理出力の空行 | **closed** | [起動器:550–560](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:550)、[同:775–787](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:775) は行番号指令と空行を除いて比較し、空行数を別記録。ident-4 の全 10 組で `nonblank_diff_lines=0`、`equal=true`。 | N3 参照。 |
| D10 MUT の SMOKE 前提 | **closed** | [起動器:531–547](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:531) は正例 3 本と同 cell 対照だけを見る。`smoke-5.failed=true` のまま `mut-2` が 3 run を実行した。 | なし |
| D11 MV-U の単一理由 kill | **partial** | `mut-2/result-MUT.json` は `MV-U.classification=survived`、`v_U_MISSING_W=0`、`u_w_rows=0`、`checks.u_reached=false`。裁定 8 が要求する比較部分だけの再照準は、この提示対象に含まれない。 | MV-U を再照準し、MUT を取り直す必要がある。 |
| N1 失敗ログの byte 上限 | **closed** | [起動器:168–182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:168) は stdout・stderr 各末尾 200 行と 64 KiB を上限にする。 | 上限適用の失敗ログ実測は提示 result にない。 |

### N2 tx 単位の B 帰属は同一 tx の別原因を区別できない

**重大度: must（一次資料の因果表現）。** [帰属関数](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:368) は違反の `ver`、`key`、`event` を使いません。例えば、壊しで選ばれ下限を上げた tx が、別の競合によって別版の `B_RETIRED` も起こせば、その違反も帰属済みになります。smoke-5 では全 **6,988 件**が tx 鍵に一致する一方、EVENT に記録された版 pointer との一致は **1,925 件**です。これは tx 単位の機序と整合しますが、各違反の原因を個別には証明しません。同 cell の stock 対照が B 違反 0 でも、壊し run 内でだけ起こる別原因への防壁にはなりません。**成果物への影響:** 「全件が下限を上げた tx に帰属」は記載可能ですが、「全件が壊しによって発生した」は主張できません。**推奨対処:** 一次資料は前者の文言に限定し、因果を強めるなら版ごとの追加証拠を取ってください。

### N3 TRACE=0 の命令列比較は分岐先の差を消す

**重大度: must（同一性判定器）。** [起動器:746–753](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:746) は `objdump` の記号名を削り、`call`・ジャンプの十六進 operand を一律 `ADDR` に置き換えます。例えば `call foo` と `call bar` の機械語上の分岐先だけが違っても、正規化後の命令行は一致し得ます。`nm`・`strings` の一覧が同じでも、この呼び先の違いは排除できません。今回の ident-4 で差があったという証拠はありませんが、`equal=true` は命令列の完全一致を検査する式にはなっていません。**成果物への影響:** 「TRACE=0 は 10 組すべて一致」は、現行判定器の意味に限った結果です。**推奨対処:** 分岐先を識別できる正規化または relocation を含む比較で 10 組を再判定してください。

### N4 B の tx 母集団等式は独立した検査になっていない

**重大度: should。** [M patch:576–600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:576) の各終了経路は、同じ `read_set_.empty()` 判定の直後に `tx_end_reads_nonempty` を加算して `traceEnd` を呼びます。[traceEnd:110–115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:110) も同じ条件で B 終了件数を加算します。そのため [起動器の `b_population`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:353) は、現行の呼び出し配置では実質的に恒真です。**成果物への影響:** この等式を独立した母集団網羅の証拠としては数えられません。**推奨対処:** tx 終了の入口側で独立計数するか、一次資料ではこの等式の証拠力を限定してください。

量化の照合結果は次のとおりです。`summary-final.tsv` の **18 件**の stock・E-max `pass` 行は違反数 0 で、直接読める smoke-5 の **5 件**も `m_summary.violations_total=0` です。ident-4 は **10/10 組**で `equal=true`、各 TU の `preprocess_diffs.*.nonblank_diff_lines=0` です。B は **3273/3273、3715/3715** 件が `rts_raised=1` の tx に帰属しています。smoke-5 の result 全体の `failed=true` は当時の同一性 2 組が `equal=false` だったためで、同一性は ident-4 で再判定されています。

## 総括

**NO-GO。** D11 の MV-U 再照準と再実測が未完了です。
TRACE=0 の 10 組一致は現行の正規化判定では成立しますが、N3 の分岐先の取りこぼしを解消してから強い同一性主張に使うべきです。
B 違反の全件について記載できるのは「下限を上げた tx への帰属」までです。