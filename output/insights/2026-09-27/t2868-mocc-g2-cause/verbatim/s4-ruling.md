# [T-2868] 段 4 裁定 (親) — 2026-09-27

入力: brief `s1-brief.md`、plan `codex/s2-plan.md`、親実測 `codex/s3-parent-facts.md`、相談 A `codex/s3a-out.md`・B `codex/s3b-out.md`。裁定 inbox (full37・full38) に本件の新裁定なし。

## 所見の裁定 (全件 real・採用・scope 内)

| 所見 | 裁定 |
|---|---|
| A1 独立抽出は parser 実装から独立だが C/R/W の意味・hook の正確性・版の (epoch,tid) 順を verifier と共有 | real。insight に共有前提を明記。MOCC の版生成 (write lock 下で直前 tid より大きい tid を publish) が順序仮定を静的に支えることは書くが、実走の全履歴と hook の忠実性の証明とは書かない |
| A2 / B6 段 A は「記録された trace 内の G2 の再現と整合」までで、hook の誤記録と本体欠陥を分離しない | real。切り分け表の verifier 列は「記録内で整合 (verifier の判定は trace と一致)」、hook 列は「未検証」と分けて書く |
| A3 patch 照合前に意味変更を排除しない・排除範囲は「照合した差分による validation・lock・hook の直接変更」まで | real。(P1) を改める: 6 件それぞれの保全 patch を照合し、通れば「直接変更なし」。timing が並行実行の結果を変える経路は残る |
| A4 / B3 6/119 は値の異なる候補の合算。親の「計 90 で約 99%」は既観測 30 を未観測扱いした誤り | real。親の計算を撤回。追加 N の検出確率は「stock 率を仮に 6/119 とした場合」の設計計算に限り、追加 30 反復で約 79%、58 反復で約 95%。stock 陽性 1 件は「literal が必要」をその条件で退ける。陰性は 3 分岐を決めない |
| A5 各 R の版が実在の W (または初期版) に結び付くこと・版の重複・欠落を示す | real。probe の出力項目に入れる |
| A6 stock 0/35 → 性能構成では 0/30、insight §4 の abort 率列は legacy の値 | real。insight に追記で訂正 (元の記述は書き換えない、規律 7) |
| B1 T-2779 runner の改造は不要、既存 `run-block-controls --protocol mocc` で stock slot を回せる | real。段 B は既存 harness + job body (`IZANAGI_S4_T2849_MODE=block-controls`、`IZANAGI_S4_T2849_BLOCK_STOCK_SESSIONS=N`、`IZANAGI_TRACE_ARCHIVE_ROOT`) で新規コード 0 |
| B2 BACK_OFF=0 は既存 harness で指定不可 (`p3_s4_loop.py` の genome 固定)、leader も変わる | real。(P2) を撤回し BACK_OFF=0 arm を削除 |
| B4 1 slot = 性能 4 + legacy 1、job 約 792 s、anomaly で打ち切り、段 A の費用も合計に含める | real |
| B5 「rep 5」と分母は解決済み、段 A の探索を削る | real。同定は WAL の non-serializable `verify_done` の commits = inventory `--expected-commits` で行う |

## plan v2

- 段 A (1 job、`dispatch_compute.py --task generic`、wave 木から投入): Codex author の probe `t2868_recheck.py` (repo 外に退避して実行)。6 件それぞれ: (1) 同定、(2) inventory の sha256 で trace を検算して展開、(3) 同じ verifier 版 (現行 main の `orchestrator/verifier` は保全時の sha256 と一致を親が実測、probe も inventory と照合) を保全 argv と同じ引数で再実行し witness を digest と照合、(4) verifier を import しない独立抽出 (2 取引の C/R/W/E frame、witness の key の全 W、R 版の producer または初期版、直後の W、版の重複・欠落、X/I/P 行の件数)、(5) 保全 patch と template の照合 (変更 file 集合と hole 外の一致)。`--ccbench-root` は計算ノード scratch に pin C の checkout + 保全 patch。selftest (合成 trace の write skew 正例・直列の負例・余分な hunk を持つ patch の負例) を本走の前に同じ job で回す。
- 段 B: 既存 harness の stock slot (新 cohort `t2868-mocc-stock-v1`、同じ cell・pin C・trace 保全)。単価は t2849 §2 の read-heavy block 対照 (job 792 s)。N は段 A の後に決め、段 A を含む合計が 2 node 時間以上ならユーザー確認。
- 変異 matrix: repo の実装面の差分 0 なので免除 (DW-S04)。probe は repo 外の一回限りの解析で、selftest の正例・負例で機構を確かめる。受入全走は段 7 前に行う。
- 論文: 切り分け表が埋まるまで主張に使わない。段 A だけでは「記録内で整合する gate reject」までしか言えない。
