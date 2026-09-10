## 総括

静的検査の結論は、単位 A は現プランのままでは NO-GO、単位 B は設計方向は妥当だが guard とメタ gate に must-fix がある、です。pytest は実走しておらず、緑は主張しません。

最大の問題は、Python が識別子を NFKC 正規化するため、ASCII の生文字列検索が AST 発見集合の上位集合にならないことです。さらに parse 前 prefilter は、従来落ちていた marker 不在の構文エラーも隠します。`s2-plan.md:22-23`、`orchestrator/tests/test_p3_exploration_namespace.py:54-90,131-147`。

成果物影響: 新 driver が `_CAMPAIGN_DRIVERS`、契約検査、全 parameterized node から同時に消えたまま受理され、探索結果・材料レポート・試行台帳が不完全な driver 集合を参照しうる。

## A-1 字句 prefilter の健全性

- **real — ASCII marker は Python 意味論上の必要条件ではない。** `layout.ｅxploration_campaign_layout(...); run_campaign(...)` は、生 source に ASCII の `exploration_campaign_layout` を含まない一方、`ast.parse` 後の `Attribute.attr` は NFKC 正規化されて `"exploration_campaign_layout"` になる。現行 `_call_name` はこれを検出するが、計画した raw substring filter は parse 前に捨てる。`s2-plan.md:21-24,66-70`、`orchestrator/tests/test_p3_exploration_namespace.py:54-90`。成果物影響: Unicode 正規化表記の新 driver が族・契約簿・実行時配線検査から消える。must-fix。

- **refuted — alias import は prefilter 固有の取りこぼしではない。** `... import exploration_campaign_layout as ecl; ecl()` では import 文に marker があるので prefilter は通るが、現行 `_call_name` は `ecl` を返すため AST 発見されない。`orchestrator/tests/test_p3_exploration_namespace.py:54-59,82-90`、`s2-plan.md:77`。成果物影響: なし。現行 AST 述語自体の既知の盲点は残る。

- **refuted — 文字列結合 `getattr` も挙動差ではない。** 外側 call の `func` は `ast.Call`、内側は `getattr` なので、現行述語は探索 root call と認識しない。prefilter も連続 marker がないため落とすが、発見集合は同じである。`orchestrator/tests/test_p3_exploration_namespace.py:54-59,69-90`、`s2-plan.md:76-78`。成果物影響: なし。

- **refuted — comment・docstring・文字列だけの marker は安全側の false positive。** prefilter は通るが、それらは `_call_names` の `ast.Call` にならず、AST 判定で除外される。`orchestrator/tests/test_p3_exploration_namespace.py:62-90`、`s2-plan.md:47,80`。成果物影響: なし。余分に parse するだけで受理集合は広がらない。

- **real — 3 marker の結論はそれぞれ異なる。** `run_campaign` は `CampaignLayout` branch の `p3_autonomous_workload_trial` に不要であり、`CampaignLayout` は `run_campaign` branch の `p3_kickoff` に不要である。`exploration_campaign_layout` だけが AST 述語上は全 creator に必要だが、raw ASCII source 上は前述の NFKC 反例がある。`orchestrator/campaign/p3_autonomous_workload_trial.py:3804-3809`、`orchestrator/campaign/p3_kickoff.py:152-165`、`orchestrator/tests/test_p3_exploration_namespace.py:82-90`。成果物影響: `run_campaign` または `CampaignLayout` を marker にすると現行 7 件の受理集合自体が欠ける。

- **real — marker 不在の構文エラーが隠れる。** 現行は全 `.py` を `ast.parse` するので collection error になるが、計画経路は `continue` が先である。別の campaign 全体 syntax gate は確認できなかった。`orchestrator/tests/test_p3_exploration_namespace.py:131-147`、`s2-plan.md:82-91`。成果物影響: 壊れた新 campaign source が受入を赤にせず、材料レポートが正常 collection と誤認しうる。must-fix。

## A-2 新 driver 登録漏れの検出可能性

- **real — 現プランは新 driver 登録漏れを独立には検出しない。** 完全一致 assertion の右辺は prefilter 済み `_CAMPAIGN_DRIVERS` であり、追加予定の names pin も既知 7 件だけ、bounded fixture に NFKC 正例はない。新しい正規化識別子 driver を契約簿にも pin にも追加しなければ、三者すべて旧 7 件のまま一致する。`orchestrator/tests/test_p3_exploration_namespace.py:147,502-505`、`s2-plan.md:31-55,59-62`。成果物影響: 新 driver の certified 契約・campaign ID・routing 観測が丸ごと生成されないのに検査が通りうる。must-fix。

- **refuted — 通常の ASCII AST creator については既存 exact assertion が働く。** ASCII `exploration_campaign_layout` を call する parse 可能な新 driver は prefilter を通り、未登録なら `_DRIVER_CONTRACTS` との集合差で赤になる。`orchestrator/tests/test_p3_exploration_namespace.py:82-90,502-505`。成果物影響: なし。ただし上記 Unicode・構文エラー反例を救わない。

- **real — bounded fixture の比較は恒真ではないが、実 repo の将来追加を量化していない。** production 関数の両経路を直接呼ぶ点は良い一方、比較対象が固定 fixture なので、fixture にない Python 字句意味論の反例は通る。`s2-plan.md:43-55`。成果物影響: fixture が表現する構文についてだけ同値を証明し、実 driver 候補集合の完全性は証明しない。must-fix。

## A-3 guard が検査を弱めていないか

- **real — `Path.exists()` は「不在だけ」を表さない。** Python 3.10 では `ENOENT` に加えて `ENOTDIR` と `ELOOP` も False にする。したがって既存の非-directory component や symlink loop を「欠落」として skip し、verifier の structural failure を隠せる。権限エラーはこの実装では再送出される。`s2-plan.md:105-107`、`/usr/lib/python3.10/pathlib.py:30-40,1285-1298`。成果物影響: invalid な外部証拠木が「測定不能」に再分類され、physical receipt の rejected/skipped 区別が変わる。must-fix。

- **refuted — 正常な完全 input set では、計画上の既存 assertion 減少は 0 件。** t189 は既存 node 本体前、t1434 は外部を実読する各 node 前にだけ guard を置き、期待値本文は変えない。`s2-plan.md:105-107,122-141`、`orchestrator/tests/test_t189_oracle_wiring_slice.py:84-94`、`orchestrator/tests/test_t1434_t1222_science_slice.py:77-126,209-249,293-365`。成果物影響: 正常な 4/21-file set では受理値・参照・assertion 数は不変。

- **real — structural error が `exists()` に隠れた場合は検査が実際に蒸発する。** t189 は `test_optional_jobs_root_audits_pinned_prompt_and_receipt_bytes` の 2 assertion、t1434 は 11 pytest node ID、静的に計 25 個の `assert`/`pytest.raises` 検査が skip されうる。対象は physical real、SS-M4、SS-M6、reader table 4 parameter、reader duplicate、reader equivalent duplicate 3 parameter。`orchestrator/tests/test_t189_oracle_wiring_slice.py:84-94`、`orchestrator/tests/test_t1434_t1222_science_slice.py:77-126,209-249,293-365`。成果物影響: science-slice の coverage、reader agreement、byte pin の再計算が行われない。must-fix。

- **refuted — 先例より粒度・理由文字列が劣るとは言えない。** 先例は session label/id を列挙し、present、missing、SHA mismatch 非隠蔽の対照を持つ。計画は exact relative path、missing-one、complete-set 対照を置き、t1434 reader は必要な 1 file だけで guard するため粒度はむしろ細かい。`orchestrator/tests/test_codex_reasoning_ab.py:787-806,822-827,875-907`、`s2-plan.md:129-141`。成果物影響: skip 理由から「外部入力欠落」と「assertion 緩和」を区別でき、正常時の参照集合も維持される。

- **real — B-10 2 module の guard 設計が未完成。** scope へ名前を加えただけで、22-file requirements、guard 挿入 node、missing/full/invalid 対照が具体化されていない。また両 file の自走 `_run()` は `Exception` しか捕捉せず、`pytest.skip.Exception` は `BaseException` 系なので外部 root 不在時の直接実行は traceback/nonzero になる。`s2-plan.md:181-193,202-219`、`orchestrator/tests/test_b10_extended_figure_provenance.py:282-340,840-857`、`orchestrator/tests/test_plot_b10_extended_backoff.py:146-179,281-298`、`orchestrator/tests/skiputil.py:2-7,24-32`。成果物影響: B-10 root 剪定時に論文図 provenance/plot node が依然 hard red となり、全 wave の land を止めうる。must-fix。

## A-4 メタ gate の恒真性

- **refuted — source candidate 集合は registry から導出されていない。** `test_*.py` を独立列挙して AST constant を抽出し、registry の二分類 union と exact 比較する構造なので、registry row 削除は source 側との差になる。`s2-plan.md:145-172,239-248`。成果物影響: 対象 regexp に入る未登録 literal は受理されない。

- **real — external/inert の意味分類自体は機械検証されない。** 実外部 binding を `inert-literal` と登録すれば union exact は通り、guard/requirements test の parameter からも消える。`s2-plan.md:147-172,191-193`。成果物影響: 誤分類された外部 root は登録済み扱いのまま pruning 後に acceptance を hard red にできる。must-fix。

- **real — scanner は「全 repo 外束縛」ではない。** `/home/`、`/work/`、`~/` で始まる単一 constant だけなので、`Path("/work") / "1/..."`、`"/mnt/..."`、複数片の join、環境値だけから導出する binding は候補にならない。プラン自身も `/mnt` 非保証を認めている。`s2-plan.md:166-179,278-280`。成果物影響: registry の受理集合外に新外部依存を作れてしまい、「全数防護済み」という材料レポートは成立しない。must-fix。

- **refuted — guard 正例は実体を通る設計である。** registry の module/guard 名を resolve して実 guard に nonexistent root を渡し、`pytest.skip.Exception` を要求する。さらに missing-one/full-set の module-local 対照を要求しており、stub だけの偽緑ではない。`s2-plan.md:191-193,241-246`。成果物影響: B-10 の未設計分を除けば、guard の return 化や root-only 化は検出可能。

- **refuted — 指定された既存 literal の inert 判定は現物と一致する。** `~/t956-repo/...` は expanduser 入力、`/home/tester/...` は注入 receipt 値、`/home/u/x` は `resolve=False` の synthetic mountinfo 入力で、host filesystem を読まない。`/home/role` は sandbox 内 mount destination/HOME であり、scanner 自体も production file を対象にしない。`orchestrator/tests/test_hooks.py:1091-1100`、`orchestrator/tests/test_t316_sandbox_probe.py:958-976`、`orchestrator/tests/test_real_repo_serialization.py:5393-5405`、`orchestrator/codex_roles/launcher.py:581-600`、`s2-plan.md:168,174-179`。成果物影響: これらを external-resource として不要に skip させる必要はない。

- **real — 全 test source scan は新しい file/byte 数比例 gate である。** D335 はその新設を禁じており、現射影の裁定には例外がない。プランも明示裁定が必要と認めている。`rulings-verbatim.md:21-38`、`s2-plan.md:9,166-170,278`。成果物影響: liveness 対策自身が repository 成長とともに受入時間を増やす。明示例外なしでは実装不可。must-fix。

## A-5 親 brief 自身の誤り

- **refuted — 「2.7 秒は元から取り残る量だった」という読み替えは資料から導けない。** 元の T-2242 は明示的に「約 2.7 秒が上限」と、ast.walk 削減見積りとして記録している。新測定から言えるのは、その旧見積りが誤りで、新測定では `0.629 s` saved、`2.686 s` residual だったことまでである。数値が偶然ほぼ同じでも同一の量ではない。`rulings-verbatim.md:121-124`、`measurements.md:13-21`、`brief.md:42-46`。成果物影響: insight は「旧 2.7-s saving estimate を反証、別測定の residual は 2.686 s」と記録する必要がある。must-fix。

- **real — 145 回の数え方は正しい。** 3 shard を並列起動し、各 internal shard が同じ `IZANAGI_TEST_NPROC=48` から `-n 48` を構成し、さらに login collect-only が 1 回あるため `48×3+1=145` collection となる。ただし並列なので wall savings に145倍してはならない。`tools/acceptance_shards.py:1243-1248,1306-1319`、`tools/run_tests.py:1495-1505,550-572`、`s2-plan.md:262-264`。成果物影響: collection invocation 数は145のまま、wall 改善値には転用しない。

- **real — 現行 growth hold は module import 費用を消せない。** `_CAMPAIGN_DRIVERS` は module import 時に走り、hold は collection 完了後の `pytest_collection_modifyitems` で付く。`orchestrator/tests/test_p3_exploration_namespace.py:131-147`、`orchestrator/tests/conftest.py:1985-2032`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/main.py:864-879`。成果物影響: hold・shard・deselect の有無にかかわらずこの collector 費用は各 collection に残る。

- **real — ただし一般に collection 前 hook は存在する。** `pytest_ignore_collect` は file/directory を specific collection hook より前に除外できるが、この repository には実装がなく、node-level hold の可視性・完全性をそのまま代替もしない。`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/hookspec.py:302-329`、`orchestrator/tests/conftest.py:1985-2032`。成果物影響: 現行値は変わらないが、「pytest には構造上不可能」という一般化だけは避ける。

- **refuted — brief の「repo 外束縛は3件」は誤り。** addendum の 5 module・3 root が現物と一致する。B-10 provenance は22 inputを hash/readし、plot test は measurement loader へ root を渡す。`brief-addendum.md:25-42`、`orchestrator/tests/test_b10_extended_figure_provenance.py:21-24,215-225,282-309`、`orchestrator/tests/test_plot_b10_extended_backoff.py:15-18,146-179`。成果物影響: registry/guard の受理集合は5 moduleでなければならず、B-10図 provenance 参照も含める。

- **real — 修正後の単位 A/B は編集面も producer/consumer 契約も分離できる。** `test_codex_reasoning_ab.py` が参照するのは checked-in wiring slice と production toolであり、単位 B が変更する `test_t189_oracle_wiring_slice.py` 自体ではない。単位 A は P3 test だけである。`orchestrator/tests/test_codex_reasoning_ab.py:109-126,6223-6232`、`s2-plan.md:200-210`。成果物影響: B-10 を B に含めても A/B の成果物参照や edit ownership は交差しない。

## must-fix 一覧

- **real — MF-1:** parse 前 raw marker filter は採らない。最低限 NFKC 正規化正例を追加する必要があるが、それだけでは構文エラー退行を直せないため、検出力維持を優先するなら「全 file parse後、AST walk 前 prefilter」の0.629秒削減へ戻す。`s2-plan.md:21-24,43-55,82-91`。成果物影響: driver 受理集合と collection error 集合を現行同値に戻す。

- **real — MF-2:** prefilter と独立した新 driver 候補集合を持たせるか、MF-1 の parse-all 経路へ戻し、登録漏れが `_CAMPAIGN_DRIVERS` と同時に消えないようにする。`orchestrator/tests/test_p3_exploration_namespace.py:502-505`、`s2-plan.md:31-62`。成果物影響: 新 driver が全契約・campaign ID・routing 試行へ必ず編入される。

- **real — MF-3:** guard は `Path.exists()` ではなく、欠落だけを限定捕捉し、symlink、loop、非-directory component、型不正、権限エラーを verifier の red へ渡す。structural negative 対照も追加する。`/usr/lib/python3.10/pathlib.py:30-40,1285-1298`、`s2-plan.md:105-107`。成果物影響: physical receipt の invalid と unavailable を混同しない。

- **real — MF-4:** B-10 2 moduleについて22-file requirements、guard 対象 node、missing/full/invalid testsを具体化し、自走時は `skiputil.skip` と `except Skip` で SKIP を可視化する。`orchestrator/tests/test_b10_extended_figure_provenance.py:282-340,840-857`、`orchestrator/tests/test_plot_b10_extended_backoff.py:146-179,281-298`。成果物影響: measurement root 剪定時も図 provenance/plot の未測定を hard red と区別する。

- **real — MF-5:** メタ gate は明示的な D335 例外裁定なしに新設しない。また保証名を「対象 prefix の単一 path literal registry」に狭めるか、constructed path と別 prefix を検出する契約を追加する。`rulings-verbatim.md:21-38`、`s2-plan.md:166-170,278-280`。成果物影響: registry coverage 値の意味を実際の検出集合と一致させ、liveness regression を避ける。

- **real — MF-6:** 最終 insight では旧 2.7秒を residual に読み替えず、旧 saving estimate の反証と、新測定 `0.629 s saved / 2.686 s residual` を別 provenance で記録する。`rulings-verbatim.md:121-124`、`measurements.md:13-21`。成果物影響: 材料レポートの改善量・残差・参照測定を正しい量へ直す。

## nit 一覧

- **real — nit:** 「保留機構は構造的に見られない」は「現行 node-level hold では」と限定する。`pytest_ignore_collect` という pre-import hook 自体は存在する。`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/hookspec.py:302-329`。成果物影響: 値・受理集合は変わらず、説明の射程だけが正確になる。

- **refuted — nit不要:** 145回という invocation count と、修正後の A/B 素集合性には訂正不要。`tools/acceptance_shards.py:1306-1319`、`s2-plan.md:200-210,262-264`。成果物影響: なし。