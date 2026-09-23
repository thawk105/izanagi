## レンズ A の所見

静的検査のみです。build・発火・hook 受理は実測していません。以下、`s2/s3/s5/t152` は対応する `orchestrator/campaign/*coverage.py` 等、`plan` は親 job の `codex/s2-plan.md` を指します。

**A1 — must-fix：checks の真偽だけでは４分類を決められない。保存する観測が不足する。**

既存 driver が残す情報は次のとおりです。

| driver | 保存される観測 | 欠ける観測と根拠 |
|---|---|---|
| s2 | `runs.<条件>.verifier` に verdict、certified、total_cycles、exit_code、txns | integrity 全体、X/P/I 件数を捨てる。`s2_verify_calibration.py:218`、`:334` |
| s3 | `runs.<条件>` に上記主要判定、`lock_coverage_violations`、raw X の `x_reasons` | P/I、version dup、orphan 等を捨てる。`s3_lock_coverage.py:177`、`:228` |
| s5 | `runs.<条件>` に主要判定、P 件数・詳細、raw P reasons、oracle 照合 | X/I とその他 integrity を捨てる。`s5_permutation_coverage.py:207`、`:261` |
| t152 | `runs.<条件>.verifier.integrity` 全体、主要判定、`trace` に raw X/P/I 件数と I reasons | この用途に必要な主要情報は揃う。`t152_write_intent_coverage.py:522`、`:549`、`:598`、`:816` |

例えば s2 が I になっても、現 JSON だけでは原因を特定できません。s3 が X>0・I でも「X **だけ**」とは言えません。s5 の「他 reason=0」は P 内の他 reason であり、他の integrity 違反がゼロという意味ではありません。trace は清掃されます（`s2:333`、`s3:234`、`s5:269`）。

`plan:117` の限界注記だけでは、想定外の結果を分類する材料が増えません。**既存 verifier subprocess の stdout JSON・stderr・rc を、判定を変えずに起動器から保存する**か、情報不足時は「その他：原因特定不能」とする方針を明記してください。全 raw trace の保存までは必須ではありません。

**A2 — should：差し替えの到達性に、計画を破る参照漏れは確認できなかった。ただし差し替える名前を厳密に限定する。**

| 差し替え | 静的確認 |
|---|---|
| `s2.PIN` | `_broken_build_and_verify` が実行時に参照し、`applied(patch, PIN, sub)` に渡す。照合省略にはならない（`s2:308`）。 |
| 各 driver の `buildcache` 参照 | condition gate と直接 configure は `buildcache.DEFAULT_CXX/CC` を実行時に参照する（`s2:106`、`:314`、`s3:93`、`:211`、`s5:90`、`:244`）。 |
| `buildcache.build` の明示 kwargs | 必須。定義時既定値が残るため、module 定数だけ変更しても stock build は直らない（`buildcache.py:3413`）。 |
| `source_digest.resolve_evidence(cxx=...)` | 必須。driver の呼出しは compiler を省略している（`s3:257`、`s5:292`）。既定値は `g++-13`（`source_digest.py:2418`）。 |
| `repo_output_root` | 各 driver のローカル束縛を変更すれば届く。`layout` 側だけの変更では届かず、従来の出力先へ書く（`s3:46`、`:318`、`s5:43`、`:359`、`t152:37`、`:932`）。 |
| `ENV_TAG` | s3/s5 の結果 metadata と出力先に届く。判定述語には使われない（`s3:248`、`:293`、`:318`、`s5:282`、`:325`、`:359`）。 |

元の `buildcache.build` が内部で参照する別 module の `source_digest` は、driver 側の proxy には置換されません。しかし再照合では **明示 cxx を渡す**ため、ここは取り残しではありません（`buildcache.py:3647`）。

patch 適用は引き続き `git apply`、排他内 pin/clean 照合、終了時復元を通ります（`patchharness.py:204`、`:256`）。差し替え対象に `applied`、gate、verifier、checks を加える必要はありません。

**A3 — should：compiler/cache_root 変更だけを理由に admission が拒否する、という懸念は反証できる。**

`SourceEvidence` の生成内容には compiler path や cache_root の独立した束縛項目がありません。ただし compiler は source の解析・digest 計算に使われます（`source_digest.py:2439`、`:2450`）。

build は admission と evidence を照合し、genome・commit・source root を確認します（`buildcache.py:3438`、`:648`）。再計算にも同じ明示 cxx が渡され、evidence 全体を比較します（`:3647`）。cache_root は出力先、cc/cxx は cache key に反映されます（`:3450`）。

したがって、**同じ source・同じ cxx で evidence を生成して元 build に渡す案は整合的**です。旧 compiler の evidence を流用したり、checkout の source root を混ぜたりする案にはしないでください。

**A4 — must-fix：環境 toolchain 方式は静的には通るが、CMake の版確認を「未確認点」のまま投入しない。**

対象経路で環境を失う箇所は確認できませんでした。

- gate の requested/control configure は同じ共通関数を通り、subprocess に置換環境を渡さない（`condition_meaning_gate.py:1698`、`:1813`、`:1999`）。
- 前処理は生成済み compile argv の include 等を保持して実行する。toolchain を前処理器が直接読むわけではない（同 `:2166`、`:2217`、`:2386`）。
- legacy buildcache は env 未指定で継承する（`buildcache.py:3540`、`:3791`）。
- t152 の configure は `env=None` で継承する（`t152:149`、`:470`）。
- MOCC helper の空 toolchain 指定は事実だが、依存 install／準備 build には依存先を argv で供給するため矛盾しない（`s3_mocc_lock_coverage.py:204`、`:266`）。

環境 `CMAKE_TOOLCHAIN_FILE` の初期化は **CMake 3.21 以降・新規 build tree** が条件です。[CMake 公式仕様](https://cmake.org/cmake/help/latest/envvar/CMAKE_TOOLCHAIN_FILE.html)

従って、依存 build より前に実行先の CMake を確認し、条件未達なら停止する手順へ移してください。これは新しい正しさ gate ではなく、採用した供給方式の実行前提です（`plan:32`、`:172`）。

**A5 — should：masstree の事前生成は必要。ただし「CCBench 全体の stock build が必要」とは別。**

gate は configure 後に前処理しますが、configure だけでは masstree の `config.h` は生成されません。`masstree_wrapper.hh` はこれを include します（`external/ccbench/include/masstree_wrapper.hh:20`）。

生成物は build tree ではなく **masstree source directory 内**に置かれます（`ThirdParty.cmake:57`、`:66`、`:74`）。各 configure が同じ `FETCHCONTENT_SOURCE_DIR_MASSTREE` を指し、source directory を生存させれば、準備用 checkout の破棄後も使えます。include path も同じ場所です（`:85`）。

`_prepare_build_dependencies` の採用は成立します（`silo_policy_coverage.py:719`）。ただし必要物を作る既存 target は `masstree_build` であり、全 `ycsb_silo.exe` build は必要最小限ではありません（`ThirdParty.cmake:78`）。

**A6 — should：generic の投入形は成立するが、環境・実行場所の記録に補足が要る。**

generic は request の環境値を拒否し、さらに clean environment を作ります。親の `CMAKE_PREFIX_PATH`、toolchain、TMPDIR を事前 export しても、そのまま子へ届く前提にはできません（`dispatch_compute.py:155`、`:354`、`:1661`、`:1832`）。起動器内設定、絶対パス、repo root の import path 追加は妥当です（同 `:1841`、`:1880`）。

ただし次を明記すべきです。

- Python の版確認は repo module import **前**。選んだ絶対 interpreter 自体が計算ノードに必要（`docs/pegasus-runbook.md:737`）。
- compiler helper は `g++-12` を直接選ぶのでなく、PATH 上の `gcc/g++` を探して policy と照合する（`s3_mocc_lock_coverage.py:147`）。「g++-12 がある」だけでは通過保証にならない。
- s2 は `numactl` と `/usr/bin/time` も必要（`s2:67`、`:154`、`:201`）。
- hook の受理は dispatcher の string-list 受理と別。現時点で拒否されるとも、通るとも断言しない（`dispatch_compute.py:1573`、`hooks/guard_bash.py:1226`）。
- **t152 JSON は `host_role="login-node"` を固定出力する。** 元 JSON は保存し、起動器側の hostname／dispatch 記録と併記して、この欄が実行場所の証拠でないと注記する（`t152:799`）。

## レンズ B の所見

**B1 — should：s3/s5 の main 維持は合理的。関数だけ呼べば必ず小さくなるわけではない。**

変異だけなら `_build_broken` と `_variant_run` で足ります。しかし stock control と既存 checks の組立てを起動器で再実装することになり、削除したコード量より転記が増えます（`s3:254`、`:293`、`s5:289`、`:325`）。

stock を捨てると、正しい source でも X/P が出る問題と変異の検出を切り分けにくくなります。**main 維持なら compiler・evidence・出力先の差し替えは必要経費**です。`ENV_TAG` は判定には不要ですが、環境を誤記しないため残すべきです。

**B2 — should：削減候補は、依存準備の反復と準備用の全 stock build。**

４ job ごとに gflags/glog install と準備 stock build を繰り返す案は保守的ですが、最小ではありません（`plan:155`）。既存 `masstree_build` target だけで準備する案、または一つの直列 job 内で依存 source/install を生存させて使い回す案には余地があります。

ただし共有 cache の新設や永続化の仕組みは不要です。最初の実走では既存 helper のまま測り、準備費が支配的な場合に限定して削減する方が、起動器の実装量との釣合いがよいです（`silo_policy_coverage.py:725`、`s3_mocc_lock_coverage.py:224`）。

**B3 — should：t152 の abort/BOMB は対象４変異の分類には必須でないが、既存 checks を維持するなら残す。**

`_evaluate_checks` は stock_single、stock_abort、bomb_smoke と４変異を要求します（`t152:640`）。BOMB target を含む stock build と追加 run は main の契約です（`:856`、`:889`）。

従って「今回の問いに必要だから全部残す」という説明は過大です。一方、削って従来の `all_pass` を維持することもできません。**新しい checks を作らず既存 main を使うため残す**、が適切な説明です。

**B4 — should：sort の未実走は条件付きで妥当。ただし「define を渡すだけ」の案は成立確認にならない。**

`SORT_VARIANT` は gate に登録済みで、s5 の gate 関数が裸マクロ専用という説明は不正確です。route は registry から選ばれます（`condition_meaning_gate.py:180`、`:1784`）。

問題は実 build 側です。

- gate：`-DCCBENCH_SORT_VARIANT=1`
- s5 `_build_broken`：`-DCMAKE_CXX_FLAGS=-DSORT_VARIANT=1`
- patch の Options：既定 `CCBENCH_SORT_VARIANT=0` から `SORT_VARIANT=0` も供給

根拠は `s5:239`、`patches/broken-silo-sort-nonswo.patch:64`、`:73`。二重定義の順序に依存する build を、gate が確認した cache 経路と同一視できません。さらに s5 の既定 `max_ope=5` は記録済み hang 条件に届きません（`s5:68`、insight `README.md:188`）。

既存関数の引数変更だけで契約が揃うなら「既存 driver の利用」です。しかし今回は configure 経路と workload の追加対応が要ります。未実走理由は **「現起動器の既存経路では供給契約が一致せず、対応を今回の範囲外とした」**と書くべきで、「実行できない」とは書かないでください。

**B5 — must-fix：110 分を２ node 時間未満の根拠にしない。**

110 分は４ job の要求 walltime の和で、実測見積りではありません。依存準備、開発検査、受入、失敗した job と再走が含まれていません（`plan:157`、`:168`、`brief.md:8`、`:18`）。

最初の限定 job の Elapse と残り build/run 数から、**既消費＋残り＋受入**を再見積りしてください。２ node 時間以上なら、次の投入前に親が裁定どおりユーザー確認を行う必要があります。静的資料だけから「直ちに確認必須」とも「確認不要」とも断定できません。

## brief 自身への所見

**C1 — must-fix：４分類の意味を揃える。**

brief は４番目を「その他」としていますが、元 insight §4.6 の４番目は「誤検出」です（`brief.md:6`、insight `README.md:225`）。また V09〜V12 の S は「盲点として期待に整合」であり、V01 の S＝「有限走で異常未観測」と同じ意味ではありません。

表では最低限、次を区別してください。

- 「期待どおり」の内訳：期待層で検出／盲点として S／到達しない対照で S
- 「別の層」：実際に観測した counters を根拠に記載
- 「未発生」：有限走で期待する異常を観測しなかった
- 「その他」：未実走、build/gate 失敗、timeout、原因情報不足、対照異常

これは表の説明で済み、新しい判定 gate は不要です。

**C2 — must-fix：P3 の `all_pass=false` は盲点の観測証拠にならない。**

stock・abort・BOMB の check は I emitter を要求しません（`t152:659`、`:670`、`:676`）。変異 check の false も、別 integrity 違反や想定外 verdict を含み得ます。

各変異の `trace.write_intent_total`、verdict、cycles、integrity を読んで初めて期待と突き合わせられます（`brief.md:12`、`t152:522`、`:549`）。S だったとしても、欠けた I 証拠だけから意図改竄の動的発生まで証明したとは書けません。

**C3 — should：P6 の tracked JSON 上書き・復元案は削除する。**

各 driver の出力先束縛を job 内へ変更すれば不要です。s2 の変異関数はそもそも dict を返すだけです（`brief.md:15`、`s2:339`、`s3:318`、`s5:359`、`t152:932`）。plan の修正方向を採用できます。

## 推奨する plan v2 の差分

1. **must-fix：観測保存を補う。** 既存 verifier の完全な JSON・stderr・rc を受動保存する。既存 checks と元の返却値は変更しない。保存しない場合は、原因不明を「その他」とする限界を表に明記する（`plan:115`、`:117`）。
2. **must-fix：分類を checks から分離する。** run ごとに条件、verdict、cycles、利用可能な X/P/I・integrity、既存 checks、分類理由を並べる。複数層の併発を落とさない（insight `README.md:152`、`:225`）。
3. **must-fix：実行前提を準備前に確認する。** Python、CMake、compiler policy、依存 cache、s2 の補助実行体を確認し、環境設定は起動器内で行う（`plan:42`、`:172`、`dispatch_compute.py:1661`）。
4. **should：６種の差し替えと main 利用は基本維持する。** 参照漏れを理由とした追加 monkeypatch は不要。t152 の固定 host_role には外側から事実を補足する（`plan:54`、`t152:799`）。
5. **should：sort の省略理由を供給経路の不一致に書き換える。** gate 未登録・単なる列挙不在を実走不能の根拠にしない（`plan:143`、`:147`）。
6. **must-fix：110 分を暫定要求値と明記し、pilot 後に総 node 時間を再見積りする。** 依存準備の削減はその実測を見て判断する（`plan:168`、`brief.md:8`）。

## 総括

**起動器による差し替え案は、静的には成立します。** pin 照合、git apply、admission、condition gate、verifier、既存 checks を緩める必要はありません。

修正の中心は、**判定材料の保存不足、４分類の曖昧さ、sort の省略理由、計算予算の根拠**です。これらを直した plan v2 で限定的な初回実走へ進み、実測をもとに残りの投入量を判断するのが妥当です。