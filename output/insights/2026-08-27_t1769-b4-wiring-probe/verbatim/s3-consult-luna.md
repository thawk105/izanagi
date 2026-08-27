### B1

- **主張**: 隔離 fixture の admission が実 campaign 3 件の ID・path・lock/WAL hash を無条件に閲覧するため、現プランは §5.1 (ii) の「閲覧しない」を満たさない。
- **根拠**: `s2-plan.md:46-48` は `require_admitted_campaign()` を必須とする。同 API は `orchestrator/campaign/artifact_admission.py:1141-1157` から `_inspect_campaign()` を呼び、synthetic WAL を検査する前に `:918` で `_load_ledger()` を実行する。台帳は `orchestrator/campaign/legacy_admission_overlay_v1.json:23-49` に実 campaign 3 件の path、ID、lock/WAL SHA-256、historical certification を収録する。protected root は campaign subtree だけであり、この台帳は対象外 (`s2-plan.md:289-290`)。
- **到達可否**: **到達する** — checks 1〜3 の positive path が毎回 admission を通る。
- **成果物影響**: この証拠を採用すると、非標本でない probe の合格 driver が certified 選択候補へ入り、後続レポート・台帳の参照根拠が無効になる。
- **推奨**: **不採用** — public admission gate を緩めず、実 campaign 台帳を一切読まない probe 専用の exact synthetic view 発行境界を別途設計できるまで停止する。

### B2

- **主張**: fixture が outcome 非派生であることを保証する記録がなく、「synthetic」という命名だけでは不十分である。
- **根拠**: プランは marker 付き synthetic rejection を生成するとだけ定め (`s2-plan.md:46,63,380`)、fixture の exact preimage、由来、固定時点、生成規則、domain separation を定めていない。一方、事前登録自身は既知の実結果と fixture 実走を既に閲覧済みと明記する (`ref-prereg-b4.md:374-385`)。
- **到達可否**: **判定不能** — 実装前であり、実 outcome から marker・payload・形状を転記しても計画上は区別できない。
- **成果物影響**: outcome 派生 fixture なら checks 2・3 は既知結果の再生となり、合格 driver 集合とそのレポートは非標本証拠として受理できない。
- **推奨**: **不採用** — probe 専用の予約 ID、型から機械生成する最小 payload、exact bytes/hash、由来説明を先に固定し、campaign ID・性能値・receipt・実 WAL 由来自由文を fixture schema で拒否する。

### B3

- **主張**: protected-root 集合は production が取り得る全配置を覆わず、ambient temporary root を介して実 campaign tree 内へ fixture を作れる。
- **根拠**: protected 対象は repo 既定 root と現在の `IZANAGI_*_OUTPUT_ROOT` だけ (`s2-plan.md:284-290`)。しかし production API は任意の `output_root` を受ける (`orchestrator/campaign/loop.py:232-246`)、exploration resolver は明示値を無検証で優先する (`layout.py:370-379`)。プランの `TemporaryDirectory` は固定 `dir` を定めておらず (`s2-plan.md:286`)、標準動作では `TMPDIR` 等から配置される。明示 `output_root` で作った campaign root を `TMPDIR` にすれば、repo 外・同一 UID・symlink 無しの検査を通る。
- **到達可否**: **到達する** — CLI の ambient environment だけで再現可能で、root 引数は不要。
- **成果物影響**: 実 campaign tree に一時 fixture subtree が追加・削除され、artifact manifest、report consumer、完全性台帳の受理集合を変え得る。
- **推奨**: **不採用** — ambient temp から独立した専用 namespaceを固定し、production の全 output-root producer がその namespace を拒否する共通 gate が必要。

### B4

- **主張**: certified-writer authorization を seed にした reverse closure は outcome producer の権威にならず、probe 自身が集合外の production outcome writer を呼ぶ。
- **根拠**: anchor は「certified sink が書く前」の gate に限定される (`orchestrator/campaign/execution_guard.py:107-119`)。一方 `record_diff_reject()` は anchor を通らず `BUILD_START` と `ABORT` を WAL へ書く (`p3_s4_loop.py:370-392`)。sort も同 writer から `outcome="rejected"` を作る (`p3_s4_loop_sort.py:225-237`)。プランはこの writer を positive path で明示的に呼ぶ (`s2-plan.md:46`) が、負例集合は高位 7 callable だけである (`:102-118`)。
- **到達可否**: **到達する** — production `record_diff_reject` は正例の必須経路。
- **成果物影響**: isolation が1箇所でも破れれば reject が secondary outcome の母数へ混入するのに、interdiction は「blocked attempts 0」のまま合格証拠を出す。
- **推奨**: **不採用** — `wal.log/append`、checkpoint、digest、rejection outcome を含む sink closure を定義し、fixture は production outcome writer と消費可能 schema を共有しない形に分離する。

### B5

- **主張**: pre-bound alias は profile で遮断できるが、`sys.modules` 差替え・新 code object・swap-and-restore までは閉じていない。
- **根拠**: 現行 driver は `run_campaign` を直接 import 済み (`p3_s4_loop.py:78`, `p3_s4_loop_sort.py:86`, `p3_s4_loop_trigger_gating.py:72`)、loop も `evaluate` を直接束縛する (`loop.py:35-40`)。同じ `__code__` なら `frame.f_code` 検査は有効である。しかしプランは reload/import 拒否と publish 前の module identity 再検査しか定めない (`s2-plan.md:84-86`)。`sys.modules[name]` の直接代入には audit event がなく、新 code object で呼び、元 module を戻せば事後再検査を通る。
- **到達可否**: **判定不能** — 現行 driver に該当代入はないが、未実装の audit hook が `compile/exec` や swap-and-restore をどう拒否するか記述がない。
- **成果物影響**: 差替え callable が outcome を生成しても inventory code identity と最終 source hash は正常となり、偽の合格 JSONが選択・レポート根拠に残る。
- **推奨**: **不採用** — transitive closure 上の `sys.modules`、`compile/exec`、reload、動的 loader を fail-closed にし、新 code identity の負例を追加する。

### B6

- **主張**: 静的 reachability は条件分岐の実行可能性を証明せず、dead branch でも「到達」と答えられる。
- **根拠**: resolver の仕様は symbol call graph のみで、条件制約を扱わない (`s2-plan.md:37-42`)。プラン自身も runtime 到達を証明しないと認める (`:408`)。実 callsite も base は `do_build && outcome!="dry-pass"` 条件下 (`p3_s4_loop.py:1509-1519`)、trigger も同条件下 (`p3_s4_loop_trigger_gating.py:1031-1041`) にある。
- **到達可否**: **判定不能** — 現行には outcome を生成すれば通る実行可能 branch があるが、probe の静的証拠はその実行可能性を検査しない。
- **成果物影響**: 将来 callsite が `if False` や矛盾条件へ移っても driver が合格し、certified 選択候補・レポート・台帳の driver 参照が誤る。
- **推奨**: **不採用** — 条件付き edge は制約の実行可能性を証明するか、静かに reachable とせず `StaticInventoryError` に倒す。

### B7

- **主張**: 現行 import closure に outcome を起動する atexit/signal/destructor は見つからないが、計画は遅延 handler と import 中に開始済みの thread を inventory していない。
- **根拠**: transitive static scan では `env_contract` の import-time side effect は fork 後に authority を消す handler 登録だけ (`env_contract.py:721-745`)。一方 profile seal は campaign import 後 (`s2-plan.md:91-95`) なので、import 中に既に開始した thread は `threading.setprofile` の対象外になり得る。また JSON publish は atexit より先であり、late handler が拒否されても公開済み証拠は残る。
- **到達可否**: **到達しない** — 現行三 driver の transitive closureには outcome producer を登録する delayed handler を静的に確認しなかった。
- **成果物影響**: 現行成果物への影響はないため **nit**。ただし将来の import side effect を静かに受理する設計余地がある。
- **推奨**: **採用** — 現在地の判定は維持しつつ、transitive top-level の `atexit`、signal、finalizer、thread start を拒否する regression と seal 時の thread census を追加する。

### B8

- **主張**: 「既存 §8 テスト 10 件から checks 2・3・4 を sort/trigger に一般化できる」という親の主張は成立しない。
- **根拠**: checks 2・3 の既存テストは共通実体 `L.make_critic_digest` を直接呼ぶだけ (`test_p3_s4_loop.py:2029-2201`)。sort の no-build 経路は admission と digest 書込みを無条件に行う (`p3_s4_loop_sort.py:502-513,690-704`)。逆に trigger は no-build 時に admitted consumer と digest を明示的に飛ばす (`p3_s4_loop_trigger_gating.py:1031-1049`)。さらに identity test は raw `default_cfg` のみ (`test_p3_s4_loop.py:2204-2224`) だが、trigger の sanctioned 経路は site projection 後の cfg から ID を作る (`p3_s4_loop_trigger_gating.py:423-437,806-822`)。
- **到達可否**: **到達する** — sort の build-free path は digest生成・閲覧へ到達し、trigger の build-free path は切替点へ到達しない。
- **成果物影響**: sort を安全な no-build 経路と誤認すれば実 campaign を閲覧し、trigger の site projection が reflux を落とす変異は見逃され、適格 driver 集合が変わる。
- **推奨**: **不採用** — 親の一般化を撤回し、trigger は actual site projection 後の identity、sort/trigger は各 consumer callsite の条件を個別に検査する。

### B9

- **主張**: evidence JSON は実配置そのものを読まなくても、production-derived campaign ID を生で公開し、実 root の locator になり得る。
- **根拠**: schema は `on_campaign_id` / `off_campaign_id` を保持する (`s2-plan.md:259-267`)。base の現行値は exact golden がある (`test_p3_s4_loop.py:2483-2487`)。ID から root への写像は決定的である (`layout.py:589-597`)。
- **到達可否**: **判定不能** — ID と一致する live campaign の存在確認自体が禁止対象で、プランには非衝突証明がない。WAL hash や campaign path を直接出す schema ではない。
- **成果物影響**: evidence consumer が ID を実 campaign root へ解決すると、dogfood と実 outcome の参照が結合され、レポート・台帳の非標本境界が曖昧になる。
- **推奨**: **不採用** — raw ID を削り、既存の domain-separated preimage hash と `different=true` のみにする。

### B10

- **主張**: 新 file を追加するだけでも既存 repository-wide gate の受理集合は変わるため、「既存受理集合は変更しない」は字義どおりには偽である。
- **根拠**: import gate は tracked/untracked operational file を列挙し、全 campaign Python に規則を適用する (`test_campaign_import_invariant.py:1001-1044`)。exploration driver gate も campaign glob を走査する (`test_p3_exploration_namespace.py:123-139`)。一方 campaign identity の計算元である既存 driver は編集しない (`s2-plan.md:300-311`)。
- **到達可否**: **到達する** — 新 module は既存 gate の入力集合へ必ず入る。ただしプランどおりの shape なら現在の verdict は変わらない。
- **成果物影響**: development gate の受理集合は狭まるが、certified 選択・B-4 report・campaign identity・既存台帳値には影響しないため研究成果物については **nit**。
- **推奨**: **採用** — regression 群は維持し、文言を「既存 driver の runtime 受理集合と identity は不変、repository gate の対象集合は拡張」に修正する。

### B11

- **主張**: 直接の新規 public placement/negative-control API は計画上は開いていない。
- **根拠**: CLI は root 系引数を持たず (`s2-plan.md:9-11`)、negative control は test child 内だけ (`:100-120`)、workspace factory は exact capability を要求する (`:284-298`)。
- **到達可否**: **到達しない** — CLI 引数から任意 campaign path や duck-typed layout を注入する経路はない。ambient temporary-root 経路は別所見 B3。
- **成果物影響**: 直接 API による campaign 参照拡大はないため **nit**。
- **推奨**: **採用** — private `_make_probe_view()` を zero-argument・exact return type のまま保ち、test のための token/path constructor を追加しない。

## 総括

- 現プランは **不採用**。B1 の overlay 台帳閲覧だけで §5.1 (ii) 違反が確定する。
- fixture 非派生性も未証明であり、production rejection writer は interdiction 集合外で実際に発火する。
- protected-root 集合は公開 `output_root` と ambient temporary root を閉じていない。
- pre-bound alias と通常 subprocess は概ね閉じるが、reload・`sys.modules` swap は未閉鎖である。
- 静的 reachability は branch feasibility を証明せず、fail-closed になっていない。
- 親の 10-test 一般化は sort/trigger の実 no-build 経路には成立しない。
- 既存 runtime identity は不変だが、repository-wide gate の受理対象集合は増える。
- pytest は実行しておらず、以上は指定どおり静的検査による。