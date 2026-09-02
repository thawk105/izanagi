pytest は実行していない。以下は差分と呼び出し経路の静的検査結果である。

## 所見

**所見:** A1 real — M1 は登録どおり export 行を削除すれば assertion を満たさないが、export が driver 後や到達不能位置にあっても通るため、有効な環境伝播の検査になっていない。  
**根拠:** `orchestrator/tests/test_b10_backoff_shape_sweep.py:1468-1477` は文字列数と独立な「env 未設定なら失敗」を見るだけで、実際の export は `tools/pegasus/b10_backoff_shape_campaign.sh:335`、driver 起動は同 336-348 にある。  
**成果物への影響:** 配置の退行を見逃すと verify/perf は `_prepare_official_output` で停止し、certified 選択結果・レポート・台帳が生成されない。  
**提案:** `unset < OUTPUT_ROOT 最終代入 < export < driver_argv/起動` の順序と、その間・以後に再代入や再 unset がないことを検査する。

**所見:** A2 real — M2 は現在の唯一の `OUTPUT_ROOT=` 行を書き換える変異なら検出するが、後段で repo 内 path に上書きされる実装は検査を通る。  
**根拠:** `orchestrator/tests/test_b10_backoff_shape_sweep.py:29-58` は最初の `OUTPUT_ROOT=` 行だけを抽出実行し、実際に export される最終値を見ず、M2 本体も同 1480-1501 の抽出値だけを中央 resolver へ渡す。  
**成果物への影響:** 実 job は repo 内 root を export して中央 resolver に拒否されるため、選択結果・レポート・台帳が欠落する。  
**提案:** export 直前の実効値を shell から取得する検査へ変え、repo 内への後段上書き変異も登録する。

**所見:** A3 real — M3 も最初の代入だけを見るため、検査対象行を残して export 前に nonce を追加すれば、相ごとの実 root が変わっても検査を通る。  
**根拠:** `orchestrator/tests/test_b10_backoff_shape_sweep.py:1504-1516` は `_job_script_output_root` の抽出値だけを比較し、各 root を official resolver に通してもいないため、s5-author の「各 root は単体で外部性 gate を通る」という一般化も未証明である。  
**成果物への影響:** perf は verify の WAL/lock を見つけられず `orchestrator/campaign/b10_backoff_shape_sweep.py:2920-2922` で停止し、レポートと受理結果が欠落する。  
**提案:** export 直前の実効値を nonce 2 値で取得し、各値を explicit official resolver に通した後で同一性を比較する。

**所見:** A4 real — layout/writer 検査は同名 AST ノードだけを見ており、実行途中で `resolved_output` や `durable_policy` を再束縛しても通る。  
**根拠:** `orchestrator/tests/test_b10_backoff_shape_sweep.py:1519-1558` は引数が `ast.Name("resolved_output")` 等であることしか検査せず、`orchestrator/campaign/b10_backoff_shape_sweep.py:2891-2910` における実行時の値・object identity を観測しない。  
**成果物への影響:** resumable binding を確認した root と verify WAL を書く root が分離し、台帳の参照先や perf が読む certification WAL が変わり得る。  
**提案:** spy で `_prepare_official_output`、`campaign_layout`、`run_campaign` の実引数を捕捉し、同じ root 値と、その root を唯一 approve する同一 policy object が渡ることを挙動検査する。

**所見:** A5 real — `forbidden_roots=()` には到達可能な実害経路があり、正式 CLI/API は `/tmp/<新規名>` を official root として受理できる。  
**根拠:** `orchestrator/campaign/layout.py:412-439` は repo 外・所有権等を検査するが `/tmp` を禁じず、`b10_backoff_shape_sweep.py:2804-2810` は env 由来 root を空の forbidden 集合で policy 化し、`loop.py:202-223` が claim を許可する；`main` からの直接経路も `b10_backoff_shape_sweep.py:3086` に実在し、shell 導出値への束縛はない。  
**成果物への影響:** verify WAL・block 台帳を揮発性 root に置いたまま repo 内レポートを生成でき、後日の resume とレポートの根拠参照が失われ得る。  
**提案:** 実証済み型どおり `forbidden_roots=(Path("/tmp"), Path("/scr"))` を置くか、B10 formal root を shell の決定的導出 path に明示束縛する。

**所見:** A6 real — claim root の親 symlink が同じ approved root 内を指す場合、policy は意図した `env/<tag>/claims` 以外への claim 書込みを承認する。  
**根拠:** `b10_backoff_shape_sweep.py:2805-2806` は raw `mkdir` で親 symlink を辿り、`layout.py:132-139` と `durable_root.py:207-220` は canonicalized candidate が広い approved root 配下なら許可し、`loop.py:209` は capability を捨てて同 223 の直接 writer に進む；一方 `layout.py:103-129` の `ensure_directory_with_capability` なら各 component の symlink を拒否するが未使用である。  
**成果物への影響:** claim 台帳が別 namespace に置かれ、競合実行を誤って拒否または見逃し、結果台帳の排他性と参照を損ない得る。  
**提案:** resolved root の capability から `ensure_directory_with_capability` で claim root を作り、leaf capability を捨てず claim writer まで渡す；このため brief の編集許可を `loop.py`/claim writer まで広げる。

**所見:** A7 real — logical root 配線は揃ったが、campaign leaf と `campaign-locks` の symlink は未検査なので、WAL・block record・lock を resolved root 外へ迂回できる。  
**根拠:** `layout.py:415-418` の suffix 検査は `campaigns` と `env` までで、`campaign_layout` は同 248-251 で未検査の campaign-id leaf を連結し、`CampaignLayout.ensure` は同 226-230、`campaign_lock_dir` は同 50-58 で raw mkdir、最終 lock open も `lock.py:72-76` で親 symlinkを追う。  
**成果物への影響:** redirected WAL/block 台帳が `_certification_attempts` やレポート入力として読まれ、台帳値・受理集合・根拠参照が意図した official root と分離し得る。  
**提案:** shared layout で campaign leaf と lock directory を capability ベースで作成・再検査する；堅牢な修正には brief が禁止する `layout.py` の変更が必要である。

## 同意できる点

**所見:** 同意 — 現在の唯一の行を対象にした登録済み M1/M2/M3 は、静的にはそれぞれ追加 assertion を満たさない。  
**根拠:** M1 は `test_b10_backoff_shape_sweep.py:1470-1473`、M2 は同 1493-1500、M3 は同 1508-1516 が直接検出する。  
**成果物への影響:** ただし未実走であり、上記は実測結果ではない。  
**提案:** なし。ただし A1〜A3 の実効値検査が必要である。

**所見:** 同意 — perf の論理的な出力配線は網羅され、report だけが要求どおり repo 内に残る。  
**根拠:** certification WAL は `b10_backoff_shape_sweep.py:2422-2426,2922`、block read/write は同 2924-2928,3025-3028,3035-3045 で resolved layout、report は `_repo_root()` を得る同 2837 と repo 内 root を作る同 3047-3058、実 writer は同 2572-2581,2633-2637,2708-2710 を使う。  
**成果物への影響:** 通常 path では verify の WAL、perf の block 台帳、他 workload の読取りは同じ外部 root、JSON/Markdown report は従来の repo 内 path となる。  
**提案:** logical routing 自体の修正は不要で、A6/A7 の物理 path 防壁を加える。

**所見:** 同意 — 事前登録の判定面と correctness gate のコードは差分で変更されていない。  
**根拠:** 差分は import、`_prepare_official_output`、root/policy 引数だけで、`PreregistrationBinding`/`PreregistrationSpec` は `b10_backoff_shape_sweep.py:180-267`、統計・物理残差関数は同 806,1271,1611-1723、correctness gate は同 1541-1608,2422-2475,2922,2967-2973,2999,3062-3068 のままである。  
**成果物への影響:** grid、α、等価域、欠測・曝露、物理残差、binding field、binary certification と `correctness_certified` の判定値は本差分では変わらない。  
**提案:** なし。

## 総括

real と判定した所見は A1、A2、A3、A4、A5、A6、A7。特に成果物の完全性に直結するのは、直接 official 入力で `/tmp` を許す A5、claim capability の canonical-path すり替えを許す A6、campaign/WAL/lock の子 symlink を許す A7 である。