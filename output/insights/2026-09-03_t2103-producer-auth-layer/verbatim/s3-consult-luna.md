## 総括

要修正である。plan は二重 pin を正しく認識しているが、frozen 候補は現行 5-file closure ではなく一時的な 6-file counterfactual を測り、復元保証、候補有効中の非後退検査、事前登録上の拒否理由、変更閉包の集計に未解決点があるため、このまま author 段へ渡すべきではない。

静的検査のみで、pytest や変異実走は行っていない。

## 凍結 closure が事実上動く箇所

- `s2-plan.md:34-37`: `_SOURCE_CLOSURE_PATHS` と `_CLOSURE_PATHS` の双方を 5 path から 6 path へ広げ、さらに closure 内の `evaluate_b4_artifacts` の入力と拒否挙動も変えるため、frozen の `6/12 KILLED` は現行 frozen consumer の性質ではなく改変済み counterfactual の値になる。
- `orchestrator/campaign/p3_b4_analysis_path.py:67-73`、`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98-104,752-754`: plan は二重 pin と AST 照合を認識し双方を同時に変えるので、片側だけ変更して照合を壊す設計にはなっていない。
- `s2-plan.md:87-95`: 実 receipt と AST 照合を通す方針自体は妥当だが、report と decision fragment では候補名を「現行 frozen consumer」ではなく「一時的 6-member expanded-closure prototype」と記さないと、比較結果の参照対象が誤る。
- `s2-plan.md:150`: 5-file literal を守る既存 test を一時変異中だけ走らせない方針は凍結ゲートの意図的な除外なので、これらを post-restore の緑で相殺せず、frozen 候補の既知 EXPECTED-RED と変更費用として比較表へ載せる必要がある。

## 一時変異の復元

- `s1-brief.md:44-46`、`s2-plan.md:71,79`: `finally` と `git checkout --` は child の `SIGKILL`、親 process の異常終了、node 障害では実行されないため、途中終了時には二つの closure tuple、`evaluate_b4_artifacts`、issuer または raw producer の prototype bytes が worktree に残る。
- `s2-plan.md:73,79`: 復元元の immutable preimage、復元処理の所有 process、原子的な置換方法が定義されていないため、復元失敗時に「どの bytes が正本か」を harness 自身が確定できない。
- `s2-plan.md:78-79`: case 結果の保存が復元確認より先に書かれているため、復元失敗後にも KILLED または SURVIVED の行だけが残り、後続の `comparison.json` や decision が汚染されうる。
- 修正案は主 worktree を変異させず disposable worktree または完全な source overlay で各 case を実行し、各 case の結果は元 worktree の hash と対象限定 diff が復旧済みと確認された後だけ昇格させ、外部 backup は復元根拠にしないことである。
- 復元に失敗した case は結果を `ABORTED_RESTORE_FAILED` とし、matrix、比較値、decision fragmentを生成せず、残存差分の全 path と observed SHA-256 を報告する必要がある。

## 正しさゲートの弱体化

- `s2-plan.md:29,76-77`: raw assembly の再導出と byte 一致を通し、material-report と既存 raw gate を緩めない方針なので、受理集合を広げる変更は plan 上確認できない。
- `s2-plan.md:67,150`: 既存 29 producer node を prototype 復元後にだけ走らせても候補有効中の過剰拒否を検出できないため、期待値を一切変えず各候補が有効な状態でも同じ 29 node を通すことを受入条件にする必要がある。
- `s2-plan.md:18-22`、`orchestrator/campaign/p3_b4_prerun_issuer.py:40-41,1081-1099`: issuer 候補は commitment の key set を増やす一方で v1 schema の扱いを定めておらず、同じ v1 を名乗る既存 publication が loader から拒否されるため、POS-1 だけでは既存受理集合の維持を証明できない。
- `s2-plan.md:150`: closure literal test を避けて比較 node だけ走らせると「実験中だけ correctness gate を外した」状態になるため、期待される既存 test の赤を隠さず候補の変更閉包とともに比較結果へ記録すべきである。
- `s1-brief.md:32`、`verbatim-t2049-mutation-table.md:25-28`: brief の「M01〜M18 は 18/18 KILLED」は M13 が正例である一次資料と矛盾し、producer 非後退値とその参照を誤らせるため削除し、一次測定記録がある場合だけ「17 負例の結果と M13 正例の結果」を別々に記すべきである。

## 事前登録との束縛

- `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47-51,394-407`: §5.1.1 の exact raw bytes と semantic bytes は無条件に pin されており、plan が実 consumer route を使う限り文書 bytes の無断変更は拒否される。
- `s2-plan.md:37`、`docs/phase3-b4-reflux-ablation-preregistration.md:461-478`: producer digest 不一致を `binding_domain_error` に写す案は、同 reason を `contract_binding` の hash、id、期待値の欠落または型違反に限定した凍結文面と異なる拒否意味を追加し、比較結果を `protocol_violation` に変えてしまう。
- `orchestrator/campaign/p3_b4_analysis_path.py:18-21`: 現行の integration-layer 拡張は ledger byte/hash と再生成失敗に限定して説明されているため、producer provenance まで同じ reason へ追加するなら §5.1.1 の改訂と hash 更新が必要であり、本 wave 外の裁定パッケージ候補になる。
- 本 wave では producer 認証不一致を experiment harness の独立した `producer_auth_rejection` として evaluator 呼出し前に記録し、既存の `B4AnalysisResult` と凍結 reason enum を変更しない設計が必要である。

## scope 逸脱

- `s2-plan.md:118`、`s2-plan.md:101-112`: 固定 trust anchor と 3 層の guard を持つ file を `orchestrator/campaign/` に恒久追加しながら experiment harness として production file 数から除外しており、本採用実装の先取りと変更閉包の過少計上になる。
- `s2-plan.md:108-114`: 新規 campaign module を現配置のまま残すなら各候補の production file 数へ少なくとも 1 file を加え、その module 内の固定 digest literal も定義どおり pin site に数えなければ、最小変更候補の選択値が不正確になる。
- `s2-plan.md:28`: `observed_producer_sha256` を公開 `B4RawAnalysisAssembly` へ追加する任意案は比較に不要な wire/API 面の恒久拡張なので、plan から削除すべきである。
- `s2-plan.md:114`: frozen だけは未実装の material-report 配線を本採用時の closure に数え、issuer/raw は experiment module や schema 互換対応を数えないため、三候補の file 数が同じ基準で比較されていない。
- `s2-plan.md:121-125`: mutation prereg、comparison、逐語、report、decision fragment は本比較実験の直接成果物なので、新台帳や族一般化には当たらず scope 内である。

## 親 brief の不変条件の充足判定

| 親 brief §4 の項目 | 判定 | 根拠 |
|---|---|---|
| 5-file pin の恒久 bytes 変更を含めない | 未充足 | `s2-plan.md:127` は復元成功を前提にしているが、`s2-plan.md:79` の `finally` では異常終了後の残存差分を防げない。 |
| producer の既存受理集合を変えず、既存 29 node を維持 | 未充足 | `s2-plan.md:150` は復元後の通常 suite しか要求せず、候補有効中の過剰拒否と issuer v1 互換性を検査しない。 |
| 自己申告 hash を認証根拠にしない | 充足 | `s2-plan.md:3,28,30,35,95` は事前固定した外部 SHA-256 との照合を要求し、artifact の自己申告値を受理根拠にしていない。 |
| 実体を名指しした負例を使い stub で通さない | 充足 | `s2-plan.md:44-48,74-77,119` は P/T/C の実 anchor、実 issuer、実 rederivation、実 closure consumer、rogue producer を使う。 |

## 書くべき非保証

- `s2-plan.md:5-10,44-67`: KILLED/SURVIVED は C0、C1、R、D の各投入位置と P/T/C の三判断値、および POS-1 にだけ適用され、他の判断値、任意のコード変異、coordinated rewrite、path race に一般化できないと明記する。
- `s2-plan.md:21-23,27,36-37`: `(path, SHA-256)` の一致は各層が検査した時点の repository bytes しか示さず、その bytes が対象 artifact を実際に生成したという因果的 provenance、import 済みコード、別 process の実行主体を証明しないと明記する。
- `s2-plan.md:34-40`: frozen の測定値は一時的に拡張した 6-member closure と追加 evaluator gate の値であり、現行 5-file consumer の拒否能力や本採用可否を示さないと明記する。
- `s2-plan.md:29,58-60,76`: R-P/R-T/R-C の raw KILL は既存の source rederivation gate によるもので、追加した producer SHA-256 guard の増分能力ではないと比較表で分離する。
- `s2-plan.md:61-65`: D-P/D-T/D-C が全候補で SURVIVED するため、どの候補も post-assembly 改変を含む end-to-end authenticity を保証しないと明記する。
- `s2-plan.md:23`: issuer が issuance 後の producer 交代を観測できないという既存記述は適切なので、そのまま report の非保証へ移す。

## nit

- `s2-plan.md:77`: `product の material-report` は `production の material-report` の誤記で、成果物の値や受理集合には影響しない。