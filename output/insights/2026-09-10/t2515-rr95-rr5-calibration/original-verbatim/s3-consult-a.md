静的検査のみ実施し、テストは実走していない。

[1] publication 全体の rratio 受理集合は 5 値に閉じていない / `cli.py` は workload を空白正規化して任意 map として受け入れ、`--certify` 検査にも rratio allowlist がない。acquisition receipt に workload 束縛もなく、quality 判定後はそのまま publish する (`cli.py:104-114,785-802,911-990,1002-1028`; `schema_v2.py:562-568,705-710`) / 正しい receipt と binary を用意して CLI を直接 `ycsb_rratio=51` または `05` で起動すると、測定品質さえ通れば accepted JSON を登録できる。公式の二つの shell 経路だけを受理集合の対象とするなら防げるが、その限定は brief の「accepted の集合」と一致しない / 自己判定: real。end-to-end の exact 集合を要件とするなら CLI 側の束縛または検査は本題に必要であり、新規 gate scope 外という理由では除外できない。

[2] 公式 submitter→job body 経路では非 canonical な字面が通る懸念は成立しない / 両 gate は引用された文字列の exact 比較で、数値変換や regex がない (`submit_certify.sh:27-43`; `certify_calibration.sh:150-161`) / `05`、`+5`、前後空白、全角数字、改行付き値、`--RRATIO` は拒否される。単一引用した文字列 `$((5))` も拒否される。呼出元 shell が `$((5))` を先に `5` へ展開した場合、callee が受け取る argv は canonical な `5` であり、元の shell 字面を識別することはできない / 自己判定: refuted。ただし [1] の直接 CLI 経路は別問題。

[3] allowlist literal 抽出テストは恒真になり得て、提案された負例も exact 性を閉じていない / plan は comparator literal の exact 集合を主要保証とし、実行負例は `0,100,51,"","95 "` に限る (`s2-plan-out.md:29-32,58-63,69-78`) / gate 前に `RRATIO=${RRATIO#+}` または先頭 0 の除去を加えれば、抽出集合は 5 値のままなので静的テストは緑で、列挙負例も緑だが `+5` や `05` が通る。job body の gate 断片だけを実行するテストも、その前段の正規化や bypass を観測しない。少なくとも `05,+5," 5","5 ",全角５` を submitter の runtime 負例に含める必要があり、これは exact 受理集合という本題の検出に必要 / 自己判定: real。

[4] job body gate の移動は必要ではなく、失敗 provenance を失う / 現行は staging と trap、`write_failure` を準備した後に rratio を検査するため、不正値を `submit_binding` の `failure.json` として記録する (`certify_calibration.sh:27-104,150-160`)。plan はこれを PBS 検査直後へ移し、stderr だけにすると明記する (`s2-plan-out.md:27-28,61`) / qsub export が壊れて `51` になった場合、現行は job ID に束縛された構造化失敗を残すが、移動後は監査可能な failure artifact が残らない。また invalid job を直接実行して `/scr` 不在を要求するのは brief にない新しい順序意味論である / 自己判定: real。親の「移動しない」が正しい。

[5] rr95/rr5 が quality reason や schema gate を実質回避する経路はない / quality は ratio を参照せず、saturation null は `required-metrics-missing` と `selection-invalid`、選択不能・cache warning・CV 超過も拒否する (`report.py:87-129`)。accepted schema も saturation null、空 sweep/noise、未固定 binary、HT、qsub/PBS ID、walltime 等を拒否する (`schema_v2.py:522-545`)。CLI は理由が一つでもあれば rejected とし、accepted のみ publish する (`cli.py:997-1028`) / rr95 が飽和しなくても D15 の下限選択が正しく立てば accepted、下限も選べなければ rejected になる。ratio による reason 無効化分岐はない / 自己判定: refuted。

[6] 「正当な selection」という説明は、D15 の数値関係を独立検証する保証としては強すぎる / D15 は `maxrss >= K×L3` の最小点を要求する (`decisions.md:220-236`)。しかし report は `saturated or lower_bound_selected` と `cache_floor_warning` だけを見ており、schema は `l3_multiple` と `working_set_ratio` を optional な有限数として型検査するだけである (`report.py:115-119`; `schema_v2.py:648-675`) / `lower_bound_selected=true`、`working_set_ratio=null` または `1`、`l3_multiple=4`、`cache_floor_warning=false` という内部矛盾でも他条件が揃えば accepted になり得る / 自己判定: real。ただし既存 producer を信頼する現行設計の弱点で、この allowlist 拡張による緩和ではない。新しい検査は rr95/rr5 の取得自体には不要なので backlog。

[7] `ratio in ("20","80")` を不変とする判断は accepted の意味について正しい / capability は 20/80 でだけ発行され、他値では `None` のまま calibrator へ渡るが、quality、schema、publish のどの述語も capability を参照しない (`cli.py:911-990,997-1028`) / rr5/rr95 は rr50 と同じ capability 無しの側へ入り、capability 不在だけで quality reason が消えたり accepted になったりはしない。提示された rr50 accepted の事実とも整合する / 自己判定: refuted。

[8] 新規 registered JSON が既存 campaign の record 選択を静かに変える懸念はない / env contract は directory を探索せず、各 generation が calibration の path と完全 SHA-256 を固定する (`env_contract.py:219-245,248-312`)。hash 解決も一意性と ever-active を要求する (`env_contract.py:881-913`) / rr5/rr95 JSON を directory に追加しても g1/g2 や既存 lock は従来 hash を参照し続けるため、自動的な取り違えは起きない。逆に、新 record を campaign で使うには後続の明示的な contract/lock 更新が必要 / 自己判定: refuted。accepted artifact 取得だけが完了条件なら scope 外でよい。

[9] 既存の「95 を拒否」テストを変更すること自体は検出力低下ではない / 旧テストは 95、旧 usage、旧 error を pin しており、目的と論理的に両立しない (`s2-plan-out.md:13-19,46-50`)。plan は 5/95 の正例と未登録値の parameterized 負例を分ける (`s2-plan-out.md:29-32,58-63`) / 95 の正例がなく負例だけ削れば退行だが、正例、伝播、未登録値の拒否、拒否時の attempts 不在を併置すれば境界検出は維持できる。usage/error pin の更新も同じ公開契約変更に伴う必須更新であり、無関係な pin の道連れではない / 自己判定: refuted。ただし負例集合は [3] の補強が必要。

[10] brief と plan の実アンカーには A4 以外にもずれがある / A1 は gate を 42-45 行とするが実体は 40-43 行で、44 行から protocol gate である (`brief.md:27`; `submit_certify.sh:40-49`)。plan の effective-clock 判定 `cli.py:1002` も実体は 1003-1004 行である (`s2-plan-out.md:65`; `cli.py:1002-1005`)。A4 の実体は確認済みどおり `tools/pegasus/README.md:125-140` である (`brief.md:30`) / 古い anchor に従うと protocol 条件を rratio gate と誤認したり、quality reason 呼出しを effective-clock 判定と誤認する / 自己判定: real。A2 の 154-158 行は実体と一致する。

[11] brief の registered 成果物契約は誤り / brief は JSON と md を各一件 registered 配下に置くとする (`brief.md:45-48`)。実装は md を attempt staging に書き、registered へ publish するのは JSON だけである (`cli.py:1012-1019,1025-1028`) / 完了検査が registered 内の md を待つと、正常な job を未完了扱いする / 自己判定: real。plan の訂正が正しい。

[12] P2 が D1488 を直接の根拠にするのは一例からの一般化 / D1488 の対象は study ごとの workload/cell shape と `--policy` path の exact map で、calibration rratio は扱っていない (`decisions.md:46462-46492`; `brief.md:18-19`) / D1488 を rratio authority と扱うと、別の exact map 判断まで同決定が自動適用される。しかし `{5,20,50,80,95}` 自体は依頼から直接導けるため、実装結論は変わらない / 自己判定: real。これは親が一例から一般化している箇所であり、根拠表現の問題。

[13] P3 は balanced の一例を rr95/rr5 の records 値へ一般化していない / brief は 1,000,000 を期待値にせず calibrator の結果を採ると明記し、D15 も飽和優先、無ければ L3 下限という workload 非依存の決定手順を定める (`brief.md:20-22`; `decisions.md:220-244`) / rr95/rr5 が balanced と異なる点で飽和または下限に達しても、その実測値を採用するので事前仮定は破れない / 自己判定: refuted。

[14] F660 と admission registry 更新が必要という懸念は、射影内の証拠では否定できる / 変更対象は既存二つの shell の引数集合で、新しい実行 path は作らない。README は `submit_certify.sh` を既存 `login-direct/local-ok` と記録し (`README.md:29-35`)、D1488 も新しい `.sh` を複製する場合に registry 追加が要ると述べる (`decisions.md:46487-46492`) / 同じ script path の比較 literal を増やしても新規実行体にはならないため、registry entry を追加する理由はない / 自己判定: refuted。ただし `admission_registry.json` 本体は今回の必読射影に含まれず、実 bytes の直接確認まではできていない。

[15] P1、A3、admission registry の「実物での検証」は、この dispatch の射影だけでは完結しない / P1 の一次資料、A3 のテストファイル、`admission_registry.json` は必読事項に含まれず、plan 自身も P1 を再確認不能としている (`brief.md:13-17,29,42-43`; `s2-plan-out.md:5,15-19`) / 引用された test line や registry 登録を誤っていても、この consult は plan の記述を再引用するだけになり、独立検証にはならない / 自己判定: real。これはコード欠陥ではなく evidence gap であり、親が実物を確認する必要がある。

## 総括

最重は、二つの shell は閉じても `cli.py --certify` の publisher 自体は任意 rratio を accepted として登録できる点。  
次に、literal 抽出テストは `05` や `+5` の事前正規化で恒真化するため、runtime の非 canonical 負例が必要。  
job gate の前方移動は不要で、invalid submit binding の構造化 failure provenance を失うため採らない。