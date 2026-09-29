## 所見

- **S06-C-1｜must-fix｜GC 低下率の範囲が誤り。** [一次資料:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:139) は最良設定が GC 10,000 µs で「13〜42% 落ちる」とするが、同資料の [W4 表:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:131) と `summary.json` の条件別 median からは、W4 は 96,365 → 88,778 tps、**7.87%**の低下。W1〜W3 は順に 31.00%、20.11%、42.09%。**放置時の成果物への影響:** 一次資料と論文に渡す「大きな GC 間隔でどれだけ弱くなるか」の範囲が誇張される。**推奨:** 全 workload を指すなら「約 8〜42%」に直し、W1〜W3 だけを指すなら対象を明記する。[結論:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:202) も合わせて直す。

- **S06-C-2｜should｜RSS 増加を `REUSE_VERSION=0` 全般の性質として読める。** [一次資料:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:106) の「3.1〜4.8 GB」は一部の組合せに当たる。`summary.json` の J1 条件別 median では、例えば W2・GC 10・`BACK_OFF=1, OPT=1, REUSE=0, W=1` は **1,184,376 kB**。**放置時の成果物への影響:** RSS の増加が単独の REUSE 軸に帰せられ、設定選択の説明が強すぎる。**推奨:** 3.1〜4.8 GB となった genome 群を明記し、他の `REUSE=0` 点もあると示す。

- **S06-C-3｜should｜作図の summary 束縛は入力パスとセルの存在まで。** [plot_vhash_cicada_tuning.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:97) は summary にキーがあれば生行を再集計し、[同:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:297) は入力パスだけを照合する。同じパスの内容が解析後に変われば、summary の median と異なる図を受理できる。**放置時の成果物への影響:** 図と最良設定・表の値が食い違い得る。**推奨:** 描くセルの median・反復数を summary と照合するか、解析時の入力 SHA256 を summary に保存して作図時に検証する。現存の図では provenance の J1 96 セル・J2 48 セルが summary とすべて一致した。

## 裁定・事前登録との照合

| 段 6 所見 | 対応 | 現行の根拠 |
|---|---|---|
| F1 合成 LLC counter | **closed** | 実測 loads・misses を保持する [driver.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:419)、[analysis.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:29)。今回の perf 不可の結果には影響しない。 |
| F2 J2 が 5 job、欠測で作図停止 | **closed** | W5 を W2 job に同居させ最大 4 job [driver.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:145)。測定済み workload のみ描く [plot:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:138)、[plot:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:194)。 |
| F3 R4 の W4 候補 | **not-fixed-by-ruling** | W4 は依然 `selected[W4]` を要する [driver.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:148)。段 6 裁定で R4 不要・未実装とした。 |
| F4 絶対 TPS median | **closed** | 条件別 median と RSS を出す [analysis.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:70)、J1/J2 を summary に含める [driver.py:625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:625)。 |
| F5 図 (b) の「探索値」 | **closed** | J1 と J2 の注記を分けた [plot:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:22)。 |
| F6 作図の完走・計画一致 | **partial** | `exit_code=0`・perf なしを選ぶ [plot:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:76)。解析は計画行を照合する [driver.py:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:589) が、作図時の summary 内容束縛は S06-C-3 の範囲。 |
| F7 CV 負例の赤理由 | **closed** | 1 rep に期待を揃え、集合のみ判定不能を検査 [test_vhash_cicada_tuning.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/orchestrator/tests/test_vhash_cicada_tuning.py:187)。 |
| B1 欠測作図 | **closed** | 欠測 workload・セルを provenance に記録 [plot:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:264)。0・補間値は入れない。 |
| B2 R4 の W4 候補 | **not-fixed-by-ruling** | F3 と同じ。 |
| B3 build 単価過小 | **closed（運用裁定）** | 段 6 裁定で並列時 45 秒を保守側に置き R1〜R3 を適用。コード上の見積り式は [analysis.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:151)。 |
| B4 J2 が 5 job | **closed** | [driver.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:145)。実走も W1〜W4 の 4 job。 |
| B5 compile command の対象 | **closed** | `ycsb_cicada.exe` の object に限定し、3 TU 各 1 件を要求 [driver.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:59)。 |
| B6 TPS median 不在 | **closed** | F4 と同じ。図も median [plot:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:70)。 |
| B7 任意 genome の RSS 副軸 | **closed** | J2 は throughput の系列のみ [plot:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:210)。RSS は summary に残る。 |
| B8 private helper 依存 | **not-fixed-by-ruling** | 依存を一関数に局所化 [driver.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:184)。段 6 裁定が受容。 |
| B9 広い設定 API | **not-fixed-by-ruling** | 任意 `k`・格子・反復を引き続き受理 [driver.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:116)。段 6 裁定は使用 argv の記録で運用する。 |

段 4 の測定格子、J1 選抜と J2 確認の分離、GC=10 control 比、標本 CV、perf 付き較正値の隔離、W5 の固定 1 ms 条件は**実装どおり**。J0 の待機 build 失敗だけを続行し、configure・通常 build 失敗は停止する [driver.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:475)。masstree は build ごとに複写し、configure/build ログと SHA256 を残す [driver.py:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:220)。J0c の待機失敗、J1 の 8 build 失敗はいずれも生 build ログで確認した。

段 4 の「8M でも N 未決定なら当該 workload を除く」は J0 全体を停止する実装との**ずれ** [driver.py:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:555) だが、段 6 裁定が今回の全 workload で N 確定済みとして実装しないとした。R4 も同裁定に従う**未実装**。段 4 の図 (b) の RSS 副表示は段 6 裁定で削除した。R-add1〜4 は現行実装に反映されている。

変異 M1〜M9 は最終 spec の置換位置と各テストの対象条件を静的に照合した。M1 は 32 点化を 24 点・16 buildable 点の期待が検出し、M2/M3 は各 define の負例、M4 は RSS 境界、M5 は候補集合境界、M6 は標本 CV、M7 は holdout helper の直接拒否、M8 は実 Figure の強制重なり、M9 は待機比 0.5/0.95 で、それぞれ**一つの変更理由で期待 node が赤になる構成**。`mutation-selfrun-final.log` では全 M1〜M9 の期待 node の赤と復元を観測している。ただし同ログの M1 期待 node 表示は旧指定であり、`mutation-spec-final2.json` 自体の本走結果とは区別する。

## 正しいと確認した点

- J0c の較正表は生行の 3 反復平均と丸めの範囲で一致。N=1M、perf 不可による RSS 下限選択、within-run CV、5 session の job 間 CV も `summary.json` と一致する。
- J1 表の **16 genome × 6 列、計 96 値**は summary の条件別 median と一致。J2 の最良 genome・GC、score、単一候補の集合、絶対 tps は summary と一致する。図 provenance の J1 96 セル・J2 48 セルも summary と一致し、表示時だけ Mtps に換算する [plot:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:162)。凡例、`genome_index`、`series` の対応もコードと provenance で追える。
- 生 manifest は J0c・J1 の完了 job・J2 の 4 job の完了を示す。J1 の失敗 8 build は同じ `Storage`→`int` compile error、J0b/J0c の待機 build は `thid`・`clock_delay` 未宣言であり、一次資料の二つの CCBench 不具合と W5 欠測はログに裏付けられる。
- abort 率の記載、control に対する約 2.15・4.54・3.41・1.38 倍、GC 曲線の表値は生行・summary の範囲で整合する。性能値を「正しさ未検証の診断値」とし、公式 floor・compare・採否に使わない旨も明記されている。
- md_6 の README と driver はこの worktree に存在しないため、[一次資料:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:200) の「md_6 は CMake 既定 build」という関係は独立検算できなかった。これは射影必読 file の欠落ではないため、レビューは継続した。

## 総括

実測の選抜・確認・欠測・作図の主要経路は裁定に沿い、現存する最良設定と図の値は整合する。公開する一次資料では **GC 低下率の範囲を先に訂正**し、RSS の記述を該当 genome に限定する必要がある。今回は指定どおり静的点検のみで、テスト・計測・変異の本走は行っていない。