- **所見 1: report channel は被検査コードから書けるため、非 dispatch 走でも正規申告を偽造できる**

  - 種別: 停止級
  - 根拠: `s2-plan.md:24-28` は manifest path を runner の環境へ渡し、manifest 自体が nonce、digest、K を全て含む (`:11-19`)。無編集の `tools/run_tests.py:1295-1304` は環境を複製し、login 側 collect-only 子にも `:1422-1444` で渡す。消すのは shard 数と plugin spec だけで、manifest 2 key は残る。bounded 子も `:2010-2018`、通常 pytest 子も `:1260-1262,2691-2708` で同じ情報を継承する。collection 時に読み込まれる tip 側 conftest/test は manifest path の親を知り、`s2-plan.md:112-120` の report を `0..K-1` 全て生成できる。mode `0700` は同じ uid の子を隔離しない。また確定設計 (v) の「既存の repo 外 shard artifact 経路」 (`verbatim-T1974-design.md:9-12`) に対し、計画は log 隣接の新規 directory (`s2-plan.md:7-8,108`) へ変更している。
  - 反証条件: 実際の login collect-only 子と bounded/local pytest 子で、manifest path を取得できず、その親へ sentinel を作成できないことを process 境界込みで測れば誤りと分かる。
  - 成果物影響: tip の pathname runner を実行した非 dispatch 走でも K 件を偽造でき、launcher は v5 受入受領証を発行し、land が偽の `runner_executed_sha256` を受理する。D859 と設計 (iv) が無効になる。現 transport のまま進めず、子へ継承されない fd 等の channel へ再設計が必要。

- **所見 2: report 検査を outcome より前へ置くと、既存の no-verdict retry 経路が消える**

  - 種別: must-fix
  - 根拠: 計画は report 不足時に outcome を書かない (`s2-plan.md:149-156`)。待ち手はまず outcome pipe を読む (`tools/dev_wave_wait.py:3810-3819`) ため、EOF は即 `acceptance-command` 失敗となる。child rc を得た後だけ log の dispatch marker を解析する (`:3843-3857`)。一方、全 shard が未起動の queue timeout の marker は `tools/acceptance_shards.py:1149-1177,1320-1328` に実在する。新順序では、その marker を待ち手が評価する地点へ到達しない。
  - 反証条件: report 0 件の全 shard queue timeout を与え、待ち手が `retryable-no-verdict-infra` に分類して同一 process retry することを実測すればよい。
  - 成果物影響: 一時的な queue timeout が再試行可能状態ではなく generic failure となり、受領証は作られず land が止まる。親が見る一次原因も missing report に置換される。

- **所見 3: 未設定・空を `"2"` へ明示化すると、queue/admission 判定を迂回する**

  - 種別: must-fix
  - 根拠: 現 runner は未設定・空を `None` とし (`tools/run_tests.py:253-264`)、eligible のときだけ暗黙 K=2 にする (`:267-297`)。暗黙 K=2 は `explicit_shard_mode=False` なので login admission と queue 可用性を通る (`:2491-2533`)。計画は未設定・空を明示 `"2"` に変える (`s2-plan.md:162-167`) ため `explicit_shard_mode=True` となり、この判定を飛ばして直接 dispatch する (`tools/run_tests.py:2620-2629`)。待ち手は queue を確認できないと env を注入しない (`tools/dev_wave_wait.py:821-845`) ので、この差が実運用で到達する。
  - 反証条件: queue inactive、env 未設定、login headroom 有りと不足の両方で、変更前後の分岐と qsub 回数を比較する。
  - 成果物影響: queue 停止時にも K=2 dispatch を試み、既定 900 秒の queue wait (`tools/pegasus/dispatch_compute.py:65`) まで待って受領証なしとなり得る。受入所要と land 可否が変わる。未設定時は K を manifest で 2 と所有しても、runner env を明示 2 にしない設計が必要。

- **所見 4: 親 brief の「shard 子だけ」と計画の K=1 非 shard binding は一致しない**

  - 種別: must-fix
  - 根拠: 親 P4 は対象を「受入 shard 子だけ」と限定する (`s1-brief.md:49-50`)。しかし計画は K=1 の通常 dispatch を index 0 として受理する (`s2-plan.md:138,171`)。実装上も `shard_count > 1` のときだけ `acceptance_shards.run_parallel` に入り (`tools/run_tests.py:2302-2352`)、K=1 は通常の `_dispatch_result` から単一 tests job に到達できる (`:2620-2637`)。
  - 反証条件: K=1 がどの site、force-dispatch、admission 状態でも compute dispatch へ到達不能であることを分岐実測する。
  - 成果物影響: K=1 受領証を受理するか拒否するかが brief と実装で逆になる。land 自体は schema 上区別できないため、台帳に書く適用範囲が偽になる。

- **所見 5: 束縛されるのは compute の直近 runner 一層だけである**

  - 種別: must-fix
  - 根拠: 束縛分岐は compute dispatcher が直近の `run_tests.py` を stdin 実行する箇所だけ (`s2-plan.md:80-100`; 現行 seam は `tools/pegasus/dispatch_compute.py:1010-1022`)。scope 外は、login の tip dispatcher import (`tools/run_tests.py:1317-1323`)、tip dispatcher を pathname 起動する job script (`tools/pegasus/dispatch_compute.py:623-687`)、login collect-only pytest (`tools/run_tests.py:1402-1457`)、bounded scope の pathname runner (`:1895-1906,2000-2018`)、compute pytest controller (`:1495-1533`)、xdist workers、およびテストが起こす grandchildren。K=2/3 は K 個の直近 runner、K=1 は単一 runnerだけが束縛される。
  - 反証条件: 各 process で `/proc/<pid>/cmdline`、実行 source digest、親子関係を採り、上記全層が main blob 由来であることを示す。
  - 成果物影響: v5 受領証が証明するのは runner digest 一値だけで、dispatcher、pytest、xdist、grandchild の bytes は証明しない。台帳で「受入全層を main に束縛」と一般化すると保証が過大になる。

- **所見 6: 提案テストは launcher と dispatcher の実在する継ぎ目を一度も通らない**

  - 種別: must-fix
  - 根拠: launcher 正例は注入 `blob_runner` 自身に report を書かせる (`s2-plan.md:179-182`)。現 seam は `_launch` が `blob_reader` と `blob_runner` を直接差し替えられる (`tools/acceptance_launcher.py:425-441`)。dispatcher 側も fake scheduler と記録用 `subprocess.run` を使う (`s2-plan.md:191-200`)。既存 helper は hostname、chdir、child 起動を全て mock する (`orchestrator/tests/test_pegasus_dispatch_compute.py:4002-4067`)。実 Git revision、実 `_run_blob`、実 `run_tests`、実 dispatch request、compute bootstrap を一本に繋ぐ検査がない。
  - 反証条件: main と tip で runner bytes が異なる実 Git repoを作り、main launcherから実 subprocess chainを通し、compute 相当子が main sourceだけを実行したことを外部観測する E2E が赤緑になること。
  - 成果物影響: 前 wave と同型に、revision 指定や環境伝播を殺しても unit が緑になり得る。変異 matrix の KILL と P の activation 証拠を受領証・land の根拠にできない。

- **所見 7: index authority と検査順の提案には「診断だけ」の kill が混ざる**

  - 種別: must-fix
  - 根拠: internal argv と `intent_shard_index` は同じ `InternalSpec` から作られる (`tools/acceptance_shards.py:992-1018`)。計画の index=1 正例 (`s2-plan.md:200`) は両方が 1 なので、argv から index を読む変異を殺せない。intent=1、argv index=0 の不一致入力が必要。また main 再取得と report 検査の順序テスト (`s2-plan.md:188`) で両方が失敗する場合、両者を入れ替えても受理集合は拒否のままで、変わるのは診断の先着だけである。report を outcome 後へ動かす変異とは分ける必要がある。未設定の検査はあるが、空文字と不正値の launcher test も列挙されていない (`:182` 対 `:164-167`)。
  - 反証条件: 各提案変異について acceptance の受理・拒否、outcome 公開、receipt 公開のいずれが反転したかを個別に記録する。
  - 成果物影響: 診断差だけを KILL に数えると変異 matrix と台帳の検出力が水増しされる。受領証の受理集合を守る検査数が実数より多く記録される。

- **所見 8: 既存の実 Git waiter E2E が計画から漏れており、そのままでは全体テストが赤になる**

  - 種別: must-fix
  - 根拠: `orchestrator/tests/test_dev_wave_wait.py:8884-8903` は実 launcher をコピーし、非 dispatch の synthetic runner を実行する。同テストは rc=0 と v5 receipt を要求する (`:8960-9008`)。同型の正例が `:9161-9187`, `:9190-9302`, `:9384-9492` にもある。新 launcher は report 0 件を無条件拒否するため、これらは意図どおり赤になるが、`s2-plan.md:177-203` の変更対象に含まれていない。
  - 反証条件: 現計画の差分だけを適用した全 suite で、これらの nodeid が既存期待のまま緑になること。
  - 成果物影響: 関連テスト完了条件を満たせず、land へ進めない。期待を単純に失敗へ変えると waiter の real Git positive coverage が消えるため、代替 E2E が必要。

- **所見 9: `check_docs` は壊れない代わりに、runbook の意味論 drift を検出しない**

  - 種別: must-fix
  - 根拠: parser は literal `TASKS` と `_TaskSpec(... child_script=<literal>)` だけを見る (`tools/check_docs.py:3681-3728,3937-3978`)。計画どおり別 dataclassを足し、`TASKS["tests"].child_script` を保持すれば consumer test (`orchestrator/tests/test_check_docs.py:2959-2969`) は緑のまま。一方 runbook は現在「dispatch 内側の子も pathname を読み直し束縛外」と明記する (`docs/pegasus-runbook.md:929-947`) ため P 後は半分が偽になる。表だけは同じ (`:634-641`) なので checker は検出しない。`TASKS` を非 literal化、`_TaskSpec` call を改名、`child_script` を非 literal化すれば parser が拒否し、値を変えれば runbook 表との比較が拒否する (`tools/check_docs.py:4025-4039`)。他の内容走査 consumer `tools/mutation_harness.py:1683-1713` は optional `runner_binding` field を許容する。
  - 反証条件: 現計画相当の sourceを parserへ渡して finding が出る、または runbook `:946` が変更後も事実であることを実測する。
  - 成果物影響: `check_docs` 緑でも運用文書と台帳に古い残余が残る。runbook を変更対象へ追加しないと、land 後の保証説明が実装と一致しない。

- **所見 10: payload 上限が数値化されておらず、既存 request schema に上限はない**

  - 種別: must-fix
  - 根拠: 現 `tools/run_tests.py` は 96,988 bytes、canonical base64 は 129,320 bytes。K=3 では source 部分だけで request 3 本合計 387,960 bytesとなり、各 login dispatcher の manifest 再読と各 compute job の request 再読も加わる。request reader は全 bytes を一括読込してから JSON parse するだけで size gate がない (`tools/pegasus/dispatch_compute.py:704-716`)。request は共有 filesystem の file として書かれ (`:2857-2868`)、qsub argv/env 上限には載らない。計画は「size 上限」とだけ書き、数値・境界 test・将来の runner 増大時の扱いを定めていない (`s2-plan.md:36,44`)。
  - 反証条件: cap の exact 値、現 main payload の余裕、cap-1/cap/cap+1 の検査、および K=1/2/3 の request bytesと wall timeを実測する。
  - 成果物影響: cap が小さければ正規 main が qsub 前に拒否され受領証なし、大きさ無制限なら dispatcher が巨大 manifest/request を保持する。現サイズだけなら増分は 1 MB 未満で、受入全走時間を実質増やす証拠はまだない。

- **所見 11: 「6/24 だから申告必須」はデータから直接は導けない**

  - 種別: must-fix
  - 根拠: 主張は commit 単位の file touch 数である (`output/insights/2026-08-27_runner-tip-equality-dispatch/README.md:178-191`)。6 件には dispatcher 導入、sharding 導入に加え、runner の env 意味変更に合わせた dispatcher allowlist の 1、2 行変更も含まれる。危険な runner source 選択変更の発生率ではない。さらに親自身が「runner と dispatcher の両方を変える wave は捕まらない」と認める (`s1-brief.md:51-53`) ため、この母集団は申告の必要性より残余の大きさを示す。
  - 反証条件: 24 commit を意味分類し、runner の実行 sourceを誤らせ得る変更、dispatcher 同時変更、提案申告が実際に kill する変更の三集合を提示する。
  - 成果物影響: 受領証の値は直ちに変わらないが、worklog/decisions に「25% が機構で閉じるため必須」と記録すると台帳の根拠が偽になる。「同時 touch は稀でない」までに限定すべき。

- **所見 12: `acceptance_shards.py` の他 wave 衝突は現計画にはない**

  - 種別: nit
  - 根拠: 親は同 file 不編集を不変条件に置き (`s1-brief.md:29-30`)、計画も不変更を明記する (`s2-plan.md:220`)。
  - 反証条件: 実装差分に `tools/acceptance_shards.py` が現れれば直ちに停止級へ上がる。
  - 成果物影響: 現状は受領証・land・台帳への影響なし。ただし所見 1 の修正を同 file 編集で済ませる案は別 wave 所有と衝突する。

## 総括

最重は所見 1で、manifest path の環境伝播が tested child に report の完全な偽造能力を渡す。  
このままでは非 dispatch fail-closed が恒真ではなく、偽の v5 receipt が land まで到達し得る。  
親が最初に測るべきものは、K=3 login collect-only 子から manifest key が見え、その親 directoryへ sentinel を作成できるかである。  
その probe が成立したら現 plan を停止し、run_tests の subprocess descendantsへ継承されない channel に再設計すべきである。