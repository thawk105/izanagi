静的レビューの結果、must-fix 8 件です。pytest・child process は実走していません。

### RA1

- 主張: protected root の audit 防壁は、複数 path を取る `rename` / `replace` / `link` / `symlink` の宛先を検査せず、保護領域への書込みを許す。
- 根拠: `p3_b4_wiring_probe.py:249-263,273-276,406-410`。`_path_access()` は `args[0]` だけを path として返す。負例は `open(..., "rb"/"ab")` だけ (`test_p3_b4_wiring_probe.py:413-442`)。
- **恒真判定**: 非恒真 — direct `open` なら赤にできるが、許可領域の source を protected root の destination へ `os.rename()` する入力は拒否されない。
- **成果物影響** (DW-G05): protected WAL/checkpoint/digest を移動・上書き・link でき、certified view の受理集合、レポート値、台帳参照が変わりうる。
- 重大度: must-fix
- 推奨 fix: multi-path audit event は source と destination を個別に realpath 解決し、片方でも protected root に重なれば拒否する。各 operation の destination 負例と無変異 canary を追加する。

### RA2

- 主張: 「3 seed のいずれかへ到達する producer は逆閉包へ入る」という evidence は、固定 6 module の候補集合と解決済み call edge だけから導かれており、未走査 module・local alias・動的束縛に対して恒真化している。
- 根拠: module 集合は固定 (`p3_b4_wiring_probe.py:56-75`)。閉包はその集合の関数だけ (`:681-687,745-801`)。visitor が記録した unresolved issue を `_build_inventory()` は検査しない (`:588-615,781-801`)。それでも evidence は module 限定なしに包含を主張する (`:1565-1571`)。
- **恒真判定**: 恒真 — 候補集合外の helper が seed を呼んでも、helper→seed edge 自体が graph に無いため inventory predicate を赤にできない。
- **成果物影響** (DW-G05): 未収載 producer が next synthesis/outcome を生成しても probe が合格し、非標本でない driver が certified 選択候補・レポート・台帳へ入る。
- 重大度: must-fix
- 推奨 fix: 閉じた dependency graph を機械生成し、外部 module edge・local alias・未解決 callable を fail-closed にする。evidence に exact analyzed-module set と hash を記録する。

### RA3

- 主張: import 副作用の拒否は runtime import の後に行われるため、防止機構ではなく事後検知になっている。
- 根拠: `main()` は `_load_runtime()` で import してから静的検査する (`p3_b4_wiring_probe.py:1449-1453`; import 本体 `:804-839`)。静的拒否はその後 (`:647-677`)。テストは synthetic source を解析するだけで実 import しない (`test_p3_b4_wiring_probe.py:167-183`)。
- **恒真判定**: 非恒真 — direct `.start()` は静的に赤になるが、赤になる前に実副作用が完了する。`helper()` 内で thread を start/join する形は静的検査も before/after census も通る。
- **成果物影響** (DW-G05): import 中に synthesis/outcome を生成・閲覧した後で probe が停止しても、HARKing 境界は既に破れ、後続の certified 選択と報告を非標本として扱えない。
- 重大度: must-fix
- 推奨 fix: runtime import より先に source と import-time call closure を検査する。transient thread・間接 `atexit`/signal/finalizer を含む実 import 負例を child process で置く。

### RA4

- 主張: M-12 のテストは seal 機構を直接呼ぶだけで、publish 経路から再検証呼出しを外す変異を殺さない。
- 根拠: production の再検証呼出しは `p3_b4_wiring_probe.py:1296,1316,1318,1488`。負例は swap 後に `guard.verify_seal()` を直接呼ぶだけ (`test_p3_b4_wiring_probe.py:445-482`)。
- **恒真判定**: 恒真 — publish callsite をすべて削除しても `verify_seal()` 本体は残るため、このテストは同じ結果で通る。
- **成果物影響** (DW-G05): 実行した module/code と evidence に記録された inventory が異なる証拠を受理し、driver 適格集合と certified 選択根拠が偽になる。
- 重大度: must-fix
- 推奨 fix: swap を残したまま実 `main(argv)` の publish 境界へ到達させ、証拠 0 件を検査する。M-12 の変異位置を実際の配線呼出しに固定する。

### RA5

- 主張: M-14 は check-loop gate を外しても schema gate が同じ failed check を拒否するため、生存する。
- 根拠: 最初の拒否は `p3_b4_wiring_probe.py:1477-1481`、二つ目は `:1401-1402`。テストは例外種別を区別せず、どちらでも `FAILED_CLOSED` を出す (`test_p3_b4_wiring_probe.py:519-540`)。
- **恒真判定**: 恒真 — `:1479-1480` を削除しても `_validate_evidence_schema()` が拒否し、証拠 0 件の期待は変わらない。
- **成果物影響** (DW-G05): M-14 を KILLED と誤認した変異台帳が採用根拠となり、failed check の publish 防止を独立に証明できないまま候補を受理する。
- 重大度: must-fix
- 推奨 fix: M-14 を一つの exact publish gate に再照準し、前後に同じ入力を拒否する層がない専用入力・node を作る。schema gate 自体は緩めない。

### RA6

- 主張: M-01、M-03〜M-05、M-08、M-09、M-15 は複数 node を落とし、M-11 は一方の条件だけ外す変異では生存するため、単一理由性を満たさない。
- 根拠: seed 専用検査 `test_p3_b4_wiring_probe.py:190-223`、実 producer 検査 `:241-296`、実 main 負例 `:299-324`、全 driver baseline `:543-607`、workspace の重複条件 `p3_b4_wiring_probe.py:894-908`。
- **恒真判定**: 判定不能 — 個々の検査は発火可能だが、登録した exact mutation と node の一対一対応は成立しない。M-11 は単一 site 変異なら静的に生存する。
- **成果物影響** (DW-G05): 「15 件すべて単一理由で KILLED」という台帳を作れず、その台帳を根拠にした driver 受理集合・certified 選択参照が無効になる。
- 重大度: must-fix
- 推奨 fix: 下表の重複 node を分離し、各 mutation の exact edit site と唯一の期待 node を事前固定する。正例の防御は維持し、mutation 入力側を再設計する。

### RA7

- 主張: M-06 の負例は guard を意図的に付けず、binding gate を外すと実 `record_diff_reject` を repository の protected root へ呼ぶため、変異試験自体が成果物を汚染しうる。
- 根拠: protected root を直接 layout にする (`test_p3_b4_wiring_probe.py:355-366`)。cleanup は issued workspace だけ (`:367-369`)。gate 後は実 production callee を呼ぶ (`p3_b4_wiring_probe.py:1005-1031`)。
- **恒真判定**: 判定不能 — gate 除去後に writer がどこまで作成してから別理由で落ちるかは、未実走かつ射影外の callee 本体に依存する。
- **成果物影響** (DW-G05): `output/campaigns/probe-negative` 等が作られると campaign 列挙・台帳・レポート参照を汚染し、実標本との非接触条件を破る。
- 重大度: must-fix
- 推奨 fix: `tmp_path` 配下を環境指定の protected root にし、before/after manifest を固定する。binding 以外の audit は付けなくても、実 campaign tree は決して target にしない。

### RA8

- 主張: `active_during_json_publish` と `active_during_sha256_publish` は、実 publish より前に採った challenge を「during」と記録している。
- 根拠: observation は evidence 構築前 (`p3_b4_wiring_probe.py:1498-1503`)。実 JSON/sidecar write と link は `:1308-1319`、呼出しは `:1605`。renderer は値をそのまま転記する (`:1257-1273`)。
- **恒真判定**: 非恒真 — boolean 自体は false 入力を構成できるが、実際の write/link 時点を観測していないため、名前が表す時間命題を検証していない。
- **成果物影響** (DW-G05): publish 窓の保証がない evidence と sidecar が採用され、driver 適格性および certified 選択の参照 hash の信頼根拠が弱まる。
- 重大度: must-fix
- 推奨 fix: publish 実装内で JSON/sidecar の各 write/link 前後に hook identity を観測し、その観測から evidence を構成する。少なくとも現在の事前観測を “during” として発行しない。

## 裁定 must-fix 8 項目

|項目|静的判定|根拠|
|---|---|---|
|1 / A2|部分実装|実 `main(argv)` 負例は実在 (`test:299-324`)。hook identity も観測由来 (`probe:305-317,312-316`)。ただし publish window は RA8、M-01 は単一理由でない。|
|2 / A3|部分実装|3 seed は実装 (`probe:71-75`)。ただし閉包の完全性主張は RA2、M-03〜05 は過剰決定。|
|3 / B4|実装あり・試験要修正|exact issued layout gate (`probe:1005-1010`) と protected 負例 (`test:355-369`)。RA7 の変異汚染が残る。|
|4 / B1|実装あり|overlay の実 read 集合照合 (`probe:1489-1493`) と path/hash/classification (`:1533-1540`)。audit の write 完全性は RA1。|
|5 / B8|実装あり|driver 別 guard (`probe:689-742`; `test:127-147`) と trigger site projection (`probe:1223-1246`)。|
|6 / B5/B3/B2/B9/B7/B11|部分実装|各機構は存在するが、B5 は RA4、B7 は RA3、B3 の M-11 は二重拒否。|
|7 / A6|部分実装・全体は判定不能|clean env と `-I -B` は実装 (`test:24-55`)。指定 2 meta-test の受入列への組込みはレビュー対象 2 ファイルから確認不能。|
|8 / source 制約|実装あり|禁止 literal/factory と公開負例 option の検査 (`test:100-124`)、CLI は 2 option のみ (`probe:1432-1436`)。|

## M-01〜M-15

`Tpos[*]` は `test_actual_main_positive_baseline_all_drivers` の 3 parameter node を表します。

|ID|静的判定|落ちる node / 生存理由|
|---|---|---|
|M-01|KILLED・過剰決定|実 main 負例に加え、profile call ledger が 0 になるため `Tpos[base/sort/trigger]` も落ちる。|
|M-02|KILLED・単一理由|`test_evidence_hook_booleans_are_observation_derived`。|
|M-03|KILLED・過剰決定|anchor 専用、inventory、実 `pipeline.evaluate`、実 main 負例、seed 数を見る `Tpos[*]`。|
|M-04|KILLED・過剰決定|save seed 専用、実 save producer、`Tpos[*]`。|
|M-05|KILLED・過剰決定|project seed 専用、実 project producer、`Tpos[*]`。|
|M-06|判定不能・危険|`test_record_diff_reject_requires_issued_layout_root` は落ちる見込みだが、実 writer の別エラーまたは protected tree 変異になりうる。|
|M-07|KILLED・単一理由|`test_nonliteral_getattr_on_proof_path_fails_closed` は error message まで固定。|
|M-08|KILLED・過剰決定|共有 `L.make_critic_digest` を 3 driver 全てが検査するため `Tpos[*]` 全て。|
|M-09|KILLED・過剰決定|同じ off/green byte 検査を 3 driver で反復するため `Tpos[*]` 全て。|
|M-10|判定不能|どの driver の `default_cfg` を変異するか未指定。trigger では raw/projected の二つの理由が同時に赤になる。|
|M-11|SURVIVED（単一 site 変異）|temp parent 条件 `probe:894-897` と issued path 条件 `:905-908` が同じ入力を拒否する。|
|M-12|SURVIVED|publish 経路の `verify_seal()` 呼出しを外しても direct-method swap test は通る。|
|M-13|KILLED・単一理由|`test_fixture_is_type_generated_reserved_and_rejects_outcome_fields`。|
|M-14|SURVIVED|check-loop gate を外しても evidence schema gate が同じ failed check を拒否する。|
|M-15|KILLED・過剰決定|static guard test と `Tpos[sort]` の両方が落ちる。|

## 負例の実体性と自走性

|負例|callee / 根拠|判定|
|---|---|---|
|9 producer entry|symbol 列 `test:241-253` → `_runtime_function()` `probe:769-778` → 実 callable 呼出し `test:266-278`|production 実体。既知定義は `pipeline.evaluate:705`、base `run_one_iteration:1066`、`save_loop_state:802`、`project_whiteboard:593`、sort `drive_iteration:423`。残りの定義 line は test が `co_firstlineno > 0` としか固定しない。|
|実 main→pipeline|`test:299-324`; `P.main` `probe:1439`、`pipeline.evaluate:705`|main と producer は実体。差替える `_CHECKS` callback だけが裁定どおりの private test seam。|
|record binding|`test:355-369`; wrapper `probe:1005`、実 callee 呼出し `:1029`|wrapper は production 実体。ただし負例では actual `record_diff_reject:370` の直前で拒否する。|
|audit WAL|`test:413-442`; `_ProcessGuard._audit` `probe:384`|実 guard + synthetic temp WAL。protected path は代用物だが mechanism は実体。|
|module/code swap|`test:445-482`; `verify_seal` `probe:471`|実 production module/function と実 guard。ただし publish 配線は代用されているため RA4。|
|fixture/root/symlink/ambient|`test:345-410`; `probe:891-1031`|実 probe gate、入力だけ synthetic。|
|nonliteral/import-side-effect|`test:149-183`; `probe:618-677,689`|source と module は代用物。静的 analyzer 単体負例で、runtime import 防止の実証ではない。|
|hook boolean|`test:327-342`; `probe:1257`|`FakeGuard` と observations の両方が代用物。renderer の literal 化だけを検査する。|
|failed publish|`test:519-540`; `P.main` `probe:1439`|main/publish 経路は実体、failed check だけ代用物。RA5 の二重 gate がある。|

collection を skip へ変える記述はなく、top-level import 失敗は collection error になります (`test:15-21`)。child success が必要な箇所は `check=True` または return code を検査し、失敗を握り潰していません (`:37-55,299-324,543-557`)。したがって test file 自身について、静的に確認できる偽緑経路は見つかりません。

## 総括

- 所見は must-fix 8 件、nit/backlog はゼロです。
- 最大の実装欠陥は protected destination の audit 漏れと、固定候補集合から導く過大な逆閉包保証です。
- import 副作用検査は実 import 後であり、非標本性の予防になっていません。
- 実 `main(argv)`→実 `pipeline.evaluate` の負例自体は存在します。
- M-11、M-12、M-14 は登録どおりの局所変異では生存します。
- M-01、M-03〜05、M-08、M-09、M-15 は過剰決定です。
- test file の collection/child failure による偽緑は静的には認めません。
- pytest は 1 nodeid も実走しておらず、緑とは判定していません。