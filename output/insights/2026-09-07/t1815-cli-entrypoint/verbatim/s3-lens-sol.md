## プランへの所見

所見 1: `DECIDER_VERSION` 据え置きは、現行の凍結規範と両立するとまだ証明されていない  
深刻度: blocker  
根拠 (file:line): `docs/phase3-8c-preregistration.md:321-325` は受理集合だけでなく「拒否理由」の意味変更にも bump を要求する一方、修正は CLI の 12 件 `evaluator-exception` を混合 reason へ変える (`brief.md:20-29`; `s8c_preregistration.py:1850-1856`)。library 経路が不変という `s2-plan.md:63-68` の説明だけでは、同じ core module の CLI 経路を規範対象外にできない  
推奨: まずユーザー裁定で「壊れていた CLI transport の復旧は decider 意味変更ではない」と明示できるなら v9 を維持する。意味変更と裁定するなら g15 は改変せず、v10・g16・CLI entrypoint の意味を明記する凍結規範改訂を同じ commit に入れる。版だけの g16 は `s8c_preregistration.py:1495-1500` の `spurious-revision` に拒否されるため、そこを緩めて整合させてはならない

所見 2: 別 checkout を `--repo-root` に渡しても、三 module の blob 検査そのものは弱くならない  
深刻度: nit  
根拠 (file:line): core は実行 file の `__file__` と target commit を比較し (`s8c_preregistration.py:1866-1873,1895-1904`)、evaluator と projection も各 live file を target blob と比較する (`:1769-1800,1804-1838`)。評価器の repository 読取は渡された root/resolved commit を使う (`s8c_preregistration_evidence.py:3371-3397`)  
推奨: target の三 blob が実行 checkout と同一なら別 checkout の commit を評価するのは設計どおり、どれかが異なれば fail-closed、と明記する。現行 v9 では `SATISFIABLE_CONDITION_IDS={"C10"}` と全 12 条件連言により最終 `effective=true` 集合は広がらない (`s8c_preregistration_evidence.py:3335,3444-3453`; `s8c_preregistration.py:1927-1956`) が、predicate 単位では全 ERROR から正しい混合 status へ広がる

所見 3: canonical alias の無条件上書きは通常の fresh CLI では妥当だが、既存 instance がある長寿命 process では危険である  
深刻度: must-fix  
根拠 (file:line): 計画は無条件代入を選ぶ (`s2-plan.md:26-40`)。通常の `-m` は `__main__` namespace で走り (`/usr/lib/python3.10/runpy.py:171-197`)、現行 `orchestrator/campaign/__init__.py:1-20` は core を先行 import しないため衝突しない。一方、`sitecustomize` や canonical import 後の `runpy.run_module` では package attribute が旧 instance を保持し、`sys.modules` だけ新 instance に替わり得る。評価器は package-relative import を使う (`s8c_preregistration_evidence.py:18`)  
推奨: scoped contract を「fresh standalone process」に限定する裁定を残す。embedding も支援するなら scope 外で、既存の別 instance を検出して明示的に fail-closed にする設計を検討する。`setdefault` は二重実体化を温存し通常評価を直さず、無条件代入は host の module state を不整合にするので、どちらも embedding の完全解ではない

所見 4: core bytes だけの事前 assert では、oracle と CLI の同時故障による恒真化を防げない  
深刻度: must-fix  
根拠 (file:line): 新設案が pin するのは core だけ (`s2-plan.md:101-108`)。evaluator が dirty なら双方 `evaluator-blob-mismatch`、projection が dirty なら双方 `projection-blob-mismatch` となり、未修正の二重実体化へ到達せず比較が一致する (`s8c_preregistration.py:1792-1800,1829-1838,1905-1918`)  
推奨: core・evaluator・projection の三 live bytes を resolved commit blob と事前比較し、expected が `core/evaluator/projection-*-mismatch` または一様 `evaluator-exception` でないことも要求する。さらに real HEAD case は既存の literal snapshot (`test_s8c_preregistration_predicates.py:282-331`) と同じ status/reason 集合を直接 pin すれば共通 oracle 故障を除ける

所見 5: exact commit を引数には渡しているが、CLI がその commit を実際に採用したことを検査していない  
深刻度: must-fix  
根拠 (file:line): `expected.commit` は resolved OID であり (`s8c_preregistration.py:1957-1959`)、それを `--commit` へ渡すので通常の HEAD 移動競合はない (`s2-plan.md:120-145`)。しかし比較対象は predicates/effective/rc だけで、payload の commit を見ていない (`s2-plan.md:154-176`)。CLI が `--commit` を無視して HEAD を評価し、結果集合が同じなら緑になる  
推奨: prereg は `payload["commit"]`、gate は `payload["source"]["commit"]` が `expected.commit` と exact 一致することを assert する。必要なら oracle 取得から subprocess 完了まで real-repo fixture lock を保持して worktree bytes の TOCTOU も避ける

所見 6: proposed E2E test 単独では、厳格な型検査を緩める代替実装を排除できない  
深刻度: must-fix  
根拠 (file:line): 二重実体化時の拒否は `PredicateResult` と `EvidenceRef` の exact instance 検査に依存する (`s8c_preregistration.py:1739-1755`)。alias を追加せず両検査を duck typing／coercion へ緩めれば、計画の oracle 比較は通り得る。現行 tests には `predicate-result-type` / `predicate-evidence-type` を直接 pin する node がない  
推奨: alias が package bootstrap の外、class 定義・`main()` 実行より前に canonical key を `sys.modules[__name__]` へ結ぶことを構造 pin し、少なくとも一つの実プロセス結果検査と対にする。構造 pin 単独は alias を `finally` で遅れて設定しても通せるため不可。既存 `isinstance` 行は変更対象外として明示する

所見 7: 4 parameter case は 4 回ではなく最大 8 回の full 評価を発生させる  
深刻度: must-fix  
根拠 (file:line): 各 case が最初に `activation_report_at` を実行し (`s2-plan.md:97-108`)、さらに subprocess でも評価する (`:147-153`)。追補の 39〜119 秒を当てると新設分だけで約 312〜952 秒であり、既存 test も real repo を二度評価する (`test_s8c_gate_report.py:464-466`)  
推奨: gate direct は `--definitely-invalid` または小さな合成 repo、prereg の module case も合成 repoで安く検査し、real repo full 評価は literal snapshot を使う 1 process に絞る。oracle を case ごとに再計算しない

所見 8: 小さな合成 repo で同じ module-identity 欠陥を安く踏めない、という前提は誤りである  
深刻度: must-fix  
根拠 (file:line): 合成 commit に live core/evaluator/projection の exact bytes をコピーすれば三 blob gate を通過できる (`s8c_preregistration.py:1868-1924`)。evidence contract を意図的に置かなければ evaluator は即座に 12 件 `evidence-contract-missing` を返す (`s8c_preregistration_evidence.py:3374-3393,3472-3483`)。未修正 CLI だけが foreign class のため `evaluator-exception` へ崩れる  
推奨: この合成 repo を prereg path/module と gate path の軽量実プロセス fixture に使う。ただし最終 `effective` は両方 false なので受理集合の pin ではなく、構造 pin と real repo 1 case の双方を残す

所見 9: `stderr == ""` は今回の正しさ欠陥を検出するには過剰である  
深刻度: nit  
根拠 (file:line): assert は全 case に掛かる (`s2-plan.md:173`) が、prereg の二重実体化は例外を握り潰すため stderr が元から空 (`s8c_preregistration.py:1850-1856`)。gate direct の ImportError は stdout JSON parse と rc/payload 検査だけで十分に検出できる  
推奨: stderr 無音を公開 CLI 契約として別途 pin するのでなければ削除し、少なくとも `Traceback` 不在へ狭める。環境由来 warning 1 行で本件と無関係な偽赤を作らない

## 親 brief の前提判定 (P1〜P5)

所見 10: P1 — real。ただし測定された fresh-process・三 blob 一致経路に限る  
深刻度: nit  
根拠 (file:line): bootstrap は canonical 登録をせず (`s8c_preregistration.py:36-38`)、評価器は canonical core を import し (`s8c_preregistration_evidence.py:18`)、その型を返す (`:1473-1483`)。`__main__` 側の exact 型検査が拒否し (`s8c_preregistration.py:1739-1755`)、広い catch が全 ERROR 化する (`:1850-1856`)  
推奨: P1 は採用してよい。evaluator/projection mismatch、preloaded module、別 checkout 全般へ「原因はこれだけ」と一般化せず、strict 型検査は不変とする

所見 11: P2 — real  
深刻度: nit  
根拠 (file:line): 親は path と `-m` の双方で 12 件 ERROR を実測している (`brief.md:20-22`)。CPython 3.10 の `-m` は target code を `sys.modules["__main__"]` の namespace で実行する (`/usr/lib/python3.10/runpy.py:171-197`)。gate report の `-m` は core を canonical import するため別挙動である (`s8c_gate_report.py:16,111-117`)  
推奨: alias を package-empty bootstrap の外に置き、path と `-m` を別々の process test で守る。ただし両方を real repo full 評価にする必要はない

所見 12: P3 — refuted  
深刻度: blocker  
根拠 (file:line): core は現行・歴史的 enforcement closure の双方に入るが (`campaign_lock.py:49-66,117-134`)、`s8c_gate_report.py` は入らない。さらに core CLI の拒否理由変更に対する version 据え置きは、凍結規範 `docs/phase3-8c-preregistration.md:321-325` と未裁定である  
推奨: 「core のみ source-bound、gate report は非 bound」へ親記録を訂正する。gate report を closure に追加しない。version 問題は所見 1 の裁定を先に解く

所見 13: P4 — real  
深刻度: nit  
根拠 (file:line): `_default_registry_results` は normalize を含む全例外を 12 件 `evaluator-exception` に変換する (`s8c_preregistration.py:1842-1856`)。今回の原因を隠した実害はあるが、brief は明示的に不変・scope 外としている (`brief.md:43-44,62`)  
推奨: 本 wave では触らない。scope 外所見として、将来は fail-closed status を維持しつつ構造化した内部 reason を残す独立 task にする

所見 14: P5 — refuted。ただし 39〜119 秒という混雑 regime の実測値自体は real  
深刻度: must-fix  
根拠 (file:line): 追補自身が空き regime への一般化を禁止する (`brief-addendum.md:6-13`)。さらに「小さな合成 repo では同じ欠陥を踏めない」説明 (`:17-23`) には、live 三 module bytes を合成 commit へコピーし、missing evidence contract の typed result を使う反例がある (`s8c_preregistration_evidence.py:3374-3393`)  
推奨: P5 は「real repo full case は高価」に限定して採用し、合成 repoを安い identity negative control にする。候補 2 の機構 pin だけでは、遅すぎる alias や型緩和で通せるため但し書きだけでは不足。構造 pin＋合成 process＋real process 1 case の三点にする

## 変異の提案と帰属

所見 15: M1 — direct-path だけ canonical alias を無効化する変異を登録できる  
深刻度: must-fix  
根拠 (file:line): 予定 alias guard (`s2-plan.md:26-28`) を一時的に `__spec__ is not None` でも条件付ければ direct path だけ二重実体化する。三 blob 一致後、内側 evaluator は正しい tuple を返し、唯一の崩壊点は outer normalize (`s8c_preregistration.py:1739-1755,1920-1924`)  
推奨: 期待赤 node を新設 `test_prereg_real_path_matches_pinned_head_report` 一つに限定し、期待差を mixed literal → 12 `evaluator-exception` と事前登録する。blob mismatch や commit mismatch が先に赤なら MISMATCH とし、KILLED に数えない

所見 16: M2 — alias を package-empty bootstrap 内へ戻す `-m` 専用変異を登録できる  
深刻度: must-fix  
根拠 (file:line): `-m` では `__package__` が既設定なので、alias を `s8c_preregistration.py:36-38` の block 内に置く変異だけで module surface が壊れ、direct path は保たれる。exact 三 module bytes＋missing contract の合成 repoなら evaluator 自体は 12 valid results を返す (`s8c_preregistration_evidence.py:3374-3393,3472-3483`)  
推奨: 期待赤 node は `test_prereg_module_tiny_repo_preserves_registry_reason` とし、期待を `evidence-contract-missing`、変異値を `evaluator-exception` に固定する。他の node の偶発赤を帰属に加えない

所見 17: M3 — gate-report direct bootstrap 全削除を登録できる  
深刻度: must-fix  
根拠 (file:line): relative import より前の bootstrap が唯一の direct-path 到達条件である (`s8c_gate_report.py:10-16`; `s2-plan.md:42-59`)。valid な小型 repo invocation なら core は structured NOT_EFFECTIVE report を正常に返し、bootstrap 変異だけが import-time traceback に変える  
推奨: 期待赤 node を `test_gate_path_tiny_repo_returns_structured_report` 一つにする。unknown-option のように parser 自身も拒否する入力は単一理由性が弱いため mutation attribution には使わない

所見 18: `setdefault`、型緩和、mismatch fixture は現状の mutation matrix へ登録すべきでない  
深刻度: must-fix  
根拠 (file:line): fresh process では `setdefault` と代入が同値で survivor になる。正しい alias 後の型緩和は同じ型しか流れず観測差がない。module blob mismatch 入力は identity layer より前に拒否される (`s8c_preregistration.py:1796-1800,1835-1838,1903-1918`)  
推奨: 「同じ入力を他層が先に拒否する」「単独変異で観測差がない」ものは登録しない。型緩和を別途 mutation 対象にするなら、foreign `PredicateResult` と foreign `EvidenceRef` を各々一層だけが拒否する専用 unit negative control が必要だが、本 wave の変更行ではない

## scope 外の real 所見 (裁定パッケージ候補)

所見 19: preloaded canonical core/evaluator を伴う embedded execution は real だが、今回の standalone CLI scope 外である  
深刻度: nit  
根拠 (file:line): 無条件代入案 (`s2-plan.md:26-40`) は `sys.modules` key だけを替え、既ロード package attribute や evaluator の global `core` は替えない (`s8c_preregistration_evidence.py:18`)。strict normalization が現状は fail-closed に倒す (`s8c_preregistration.py:1739-1755`)  
推奨: 裁定パッケージには「fresh process 限定」か「embedding も支援」の択一を載せる。後者なら canonical key・package attribute・既ロード evaluator の整合設計を独立 wave にし、本件へ互換層を足さない

所見 20: `s8c_gate_report.py` が campaign lock の source closure 外であることは real  
深刻度: nit  
根拠 (file:line): exact 62-path closure は core/evaluator/projection を含むが gate report を含まない (`campaign_lock.py:47-112`)。歴史的 closure も同様 (`:114-142`)  
推奨: 親 brief の事実訂正だけ本 wave に反映し、closure 追加は別裁定へ回す。今回追加すると source 集合・digest・歴史整合の別問題になる

所見 21: evaluator 例外の原因消失は real だが、本 wave で診断 schema を追加するのは scope 逸脱である  
深刻度: nit  
根拠 (file:line): 全例外を自由文なしの `evaluator-exception` に変える (`s8c_preregistration.py:1850-1856`) 一方、brief は P4 として明示的に除外する (`brief.md:43-44`)  
推奨: 今回は alias 修正と回帰検査だけに留め、例外 provenance、追加 reason、台帳、一般化 gate は裁定パッケージ候補として分離する

所見 22: プランの consumer 列挙は調査としては妥当だが、そこから production 改修へ広げてはならない  
深刻度: nit  
根拠 (file:line): 計画は多数の downstream consumer と焦点 test を列挙する (`s2-plan.md:194-231`) が、brief の production scope は二つの bootstrap だけである (`brief.md:3-10,68-73`)  
推奨: consumer は回帰確認対象に限定する。新しい binding、campaign-lock path、汎用 entrypoint helper、互換層を本 wave へ追加しない

## 総括

所見 23: 計画は as-written では NO-GO。bootstrap 方針自体は scoped fresh process に対して正しい  
深刻度: blocker  
根拠 (file:line): 必須修正は version 裁定、三 module の共通故障排除、出力 commit pin、型緩和で代替できない identity pin、実評価数削減である (`docs/phase3-8c-preregistration.md:321-325`; `s8c_preregistration.py:1739-1755,1769-1924`; `s2-plan.md:97-176`)  
推奨: v9 維持可否を先に裁定し、その後「構造 pin＋三 blob が同一な小型 repo の path/module/gate process tests＋literal を持つ real repo full 1 process」へ改稿する。静的検査のみで、pytest・CLI 回帰・変異は実走しておらず、file 書換え・commit も行っていない