# 段 2 実装プラン

静的に起草した。ファイル編集、`check_docs`、pytest は実走していない。以下では、親案をそのまま採る形も示すが、推奨は `rare` ではなく「発火条件を持つ risk 面」で分ける案である。

## 1. 新 reference 族

### 親の P1/P2 をそのまま採る場合

機械的には次で実現できる。

- root: `docs/dev-wave-rare/`
- `docs/dev-wave-rare/guards.md`: `DW-O04`, `DW-O06`, `DW-O08`, `DW-O09`, `DW-O10`, `DW-O11`, `DW-O14`
- `docs/dev-wave-rare/hang.md`: `DW-M06`
- 個別 cap: 2,600 / 500 bytes
- 族 ceiling: 2,900 bytes
- 入口見積り: 9,254 bytes

ただし `docs/dev-wave/operations.md:46-58` 自身が `DW-O09` は docs-only wave でも成立すると明記し、brief も `s1-brief.md:97-98` で頻発を認めている。`rare` という分類には機械的に観測できる根拠がないため採用を勧めない。

### 推奨対案 P1′/P2′

root は次とする。

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t328-docs-externalize/docs/dev-wave-risks/`

分割軸は実行頻度ではなく、次をすべて満たす「発火条件または局所 risk に閉じた手順」とする。

1. named condition、または `hang_risk` のような明示 predicate がある。
2. wave 開始・段 1・段 2・段 3 の通常工程を定義しない。
3. 外出し後も段／条件 dispatch から exact `(path, section ID)` で到達できる。
4. 本文を byte-for-byte 移し、適用条件・期限を弱めない。

この軸は `.claude/commands/dev-wave.md:60-75,84-105` から静的に判定できる。`DW-O03` は段 2・3 preflight の両方で常時読まれるため残し、`DW-M06` は段 6 の読了義務を維持したまま外へ置く。

### ファイルと移設対応

H2 の先頭から次の H2 直前までを UTF-8 byte で数えた。移設時はこのスライスを編集せず移す。

| 移設後 | 新 H2 行 | 移設元 | 現行 bytes |
|---|---:|---|---:|
| `docs/dev-wave-risks/guards.md:5` `DW-O04` | 5 | `docs/dev-wave/operations.md:26-30` | 200 |
| `docs/dev-wave-risks/guards.md:10` `DW-O06` | 10 | `docs/dev-wave/operations.md:36-40` | 210 |
| `docs/dev-wave-risks/guards.md:15` `DW-O08` | 15 | `docs/dev-wave/operations.md:41-45` | 183 |
| `docs/dev-wave-risks/guards.md:20` `DW-O09` | 20 | `docs/dev-wave/operations.md:46-58` | 935 |
| `docs/dev-wave-risks/guards.md:33` `DW-O10` | 33 | `docs/dev-wave/operations.md:59-63` | 261 |
| `docs/dev-wave-risks/guards.md:38` `DW-O11` | 38 | `docs/dev-wave/operations.md:64-68` | 223 |
| `docs/dev-wave-risks/guards.md:43` `DW-O14` | 43 | `docs/dev-wave/operations.md:78-82` | 200 |
| `docs/dev-wave-risks/hang.md:5` `DW-M06` | 5 | `docs/dev-wave/mutation.md:38-42` | 258 |
| **移設合計** |  |  | **2,470** |

P2 の 7 節だけでは 2,270 bytes であり、brief の約 1,830 bytes は過小見積り、かつ目安 2,300 bytes に30 bytes足りない。`DW-O04` は condition 04 と段 8 の局所 risk で、追加移設先として意味的にも整合する。

新ファイルの前置きは次に固定する。

- `guards.md`: 152 bytes

  `# dev-wave リスク別 guard` と、発火条件の正本を command、共通工程の正本を core とする1文。

- `hang.md`: 133 bytes

  `# dev-wave hang リスク` と、`hang_risk` 時だけの隔離で共通契約は mutation とする1文。

したがって初期実 bytes は次になる。

| member | 移設本文 | 前置き | 見積り | cap | 余裕 |
|---|---:|---:|---:|---:|---:|
| `guards.md` | 2,212 | 152 | 2,364 | 2,600 | 236 |
| `hang.md` | 258 | 133 | 391 | 500 | 109 |
| **族合計** | 2,470 | 285 | **2,755** | **2,900 ceiling** | **145** |

定数は以下を推奨する。

```text
DEV_WAVE_RISK_FAMILY_CEILING_BYTES = 2_900
DEV_WAVE_RISK_CAP_SUM_MAX_PERCENT = 110
```

個別 cap 総和は 3,100、族 ceiling の 110% は 3,190 なので余裕は90 bytesである。

### 総量逃がしを防ぐ対案

新族を別 ceiling だけにすると、既存 25,200 と新族 2,900を同時に満たす最大値は28,100 bytesになる。D110 の「分割で総量 gate を骨抜きにしない」という趣旨に対し弱い。

そこで追加で次を推奨する。

```text
DEV_WAVE_ALL_REFERENCE_CEILING_BYTES = 27_200
DEV_WAVE_ALL_REFERENCE_CAP_SUM_MAX_PERCENT = 110
```

後述の A1〜A11 統合後は次の計算になる。

- primary 4本: 24,191 bytes
- risk 族: 2,755 bytes
- 全 reference: 26,946 ≤ 27,200、余裕254
- 全個別 cap 総和: 26,750 + 3,100 = 29,850
- 27,200 × 1.10 = 29,920、余裕70

既存の `DEV_WAVE_AGGREGATE_BYTES = 25_200` は変更しない。ただし全 reference の実総量は現行25,198から26,946へ増える。増分1,748は A1〜A11の1,463 bytesと分割前置き285 bytesそのものであり、これを許すかは親の明示裁定が必要である。全体 ceiling を置かない案は勧めない。

移設の証拠は、base commit の各スライスと新ファイル側スライスの byte 数・SHA-256を一対一で insight に保存する。節 ID 集合だけでなく本文同値もこれで固定する。

## 2. `tools/check_docs.py` の変更

### 定数・識別子

| 現行位置 | 変更 |
|---|---|
| `tools/check_docs.py:57-61` | 新2ファイルを `LIVING_DOCS` に追加する。 |
| `tools/check_docs.py:167-180` | 裸の `REFERENCE_LIMITS` を `DEV_WAVE_PRIMARY_REFERENCE_LIMITS` に改名する。4 cap は変更しない。 |
| `tools/check_docs.py:181-203` | `DEV_WAVE_RISK_REFERENCE_ROOT`、`DEV_WAVE_RISK_REFERENCE_LIMITS`、族 ceiling を追加する。 |
| `tools/check_docs.py:253-257` | `DEV_WAVE_AGGREGATE_BYTES = 25_200` と `DEV_WAVE_REFERENCE_CAP_SUM_MAX_PERCENT = 110` を逐語で維持し、risk と全体用定数を別名で追加する。 |
| `tools/check_docs.py:374-395` | primary/risk の必須節 registry を分離し、dispatch allowlist を両者の和へ更新する。 |

識別子は次の意味に固定する。

- `DEV_WAVE_PRIMARY_*`: `docs/dev-wave/**` の4本。
- `DEV_WAVE_RISK_*`: `docs/dev-wave-risks/**` の新2本。
- `DEV_WAVE_ALL_REFERENCE_*`: 上記6本の横断上限。
- `PROVENANCE_*`: D110 の provenance family。変更しない。
- `DEV_WAVE_AGGREGATE_BYTES`: 既存互換のため名前を維持するが、primary 4本だけを意味するとコメントする。

併せて以下を改名する。

- `REQUIRED_REFERENCE_SECTIONS` → `REQUIRED_DEV_WAVE_PRIMARY_SECTIONS`
- 新設 `REQUIRED_DEV_WAVE_RISK_SECTIONS`
- `NORMATIVE_DISPATCH_ALLOWLIST` → `DEV_WAVE_DISPATCH_PATH_ALLOWLIST`
- ローカル変数 `all_limits` → `checked_text_limits`
- `reference_size` → `dev_wave_primary_size`
- `_check_dev_wave_reference_cap_sum` → 引数に label・percent を取る `_check_dev_wave_cap_sum`

新 registry は次で固定する。

```text
guards.md = O04, O06, O08, O09, O10, O11, O14
hang.md   = M06
```

### `DW-Oxx` のファイル分割

`tools/check_docs.py:351-353` の1ファイル前提を次に分ける。

```text
_PRIMARY_OPERATION_NUMBERS = (1, 2, 3, 5, 12, 13, 15, 16, 17, 18, 19, 20, 23)
_RISK_OPERATION_NUMBERS = (4, 6, 8, 9, 10, 11, 14)
_OPERATION_NUMBERS = sorted union
```

`tools/check_docs.py:415-421` に以下を置く。

- `_PRIMARY_OPERATIONS = "docs/dev-wave/operations.md"`
- `_RISK_GUARDS = "docs/dev-wave-risks/guards.md"`
- `_PRIMARY_MUTATION = "docs/dev-wave/mutation.md"`
- `_RISK_HANG = "docs/dev-wave-risks/hang.md"`
- `_OPERATION_REFERENCE_BY_NUMBER`
- `_ALL_OPERATIONS`: 上記 map から全20 IDの `(path, ID)` を作る

`tools/check_docs.py:423-484` は次を変更する。

- 段 5・6の `_ALL_OPERATIONS` はそのまま全20 IDを意味させる。
- 段 6の `DW-M06` だけ `_RISK_HANG` へ写す。
- 段 8の `DW-O04` を `_RISK_GUARDS`、`DW-O17`を primary にする。
- `CONDITION_DISPATCH_CONTRACT` は番号ごとに `_OPERATION_REFERENCE_BY_NUMBER[i]` を使う。
- `_OPERATION_NUMBERS` の外延は一切変えない。

### 閉包・予算

`tools/check_docs.py:2534-2551` の cap-sum helper を primary/risk/all に再利用できる形へする。呼出しは `tools/check_docs.py:2558-2562` に3本置く。

新 root の閉包は `tools/check_docs.py:2590-2611` の primary 閉包と provenance の `tools/check_docs.py:2613-2649` を先例に、別 helper として追加する。

検査順は次とする。

1. root 自体が symlink なら走査せず拒否。
2. `rglob("*")` で regular file と symlink 実体を列挙。
3. 実体集合－登録集合を未登録実体として拒否。
4. 登録集合－実体集合を member 不在として拒否。
5. `tools/check_docs.py:567-613` の `_safe_read_text` で親 component を含む symlink、非 regular、読取不能、invalid UTF-8を拒否。
6. `tools/check_docs.py:2651-2658` の予算対象へ新2本を追加。
7. `tools/check_docs.py:2685-2699` の個別 cap を適用。
8. risk 2本がともに読めた場合だけ合計2,900を検査。
9. primary/risk 6本がともに読めた場合だけ全体27,200を検査。

既存 primary 集計 `tools/check_docs.py:2701-2706` は4本だけを合計し、25,200を維持する。

### H2・三面一致

`tools/check_docs.py:2769-2792` の H2 検査を helper 化し、primary とriskを別 registryで呼ぶ。

- 必須 H2 count は exact 1。
- count 0/2以上を別 finding。
- registry にない H2 は孤児。
- `DW-Oxx` / `DW-Mxx` の番号は変更しない。

risk 三面一致は provenance の `tools/check_docs.py:2816-2866` と混ぜず、その直前に追加する。

- budget paths = `DEV_WAVE_RISK_REFERENCE_LIMITS`
- section paths = `REQUIRED_DEV_WAVE_RISK_SECTIONS`
- dispatch paths = stage/condition contract のうち `docs/dev-wave-risks/` 配下の path
- registered pairs = risk section registry の `(path, ID)`
- contract pairs = stage/condition dispatch の risk pair の和

path 三面と pair 閉包をそれぞれ独立 finding にする。これにより「同じ2 pathだが O14 だけ別ファイルへ誤配線」も検出できる。

`tools/check_docs.py:3014-3055` の command 表検査は既存構造を使い、allowlist を新名へ差し替える。

## 3. 境界テスト

主な編集面は以下である。

- 合成 fixture: `orchestrator/tests/test_check_docs.py:347-497`
- 予算 pin: `orchestrator/tests/test_check_docs.py:776-810,956-992,1279-1293`
- member 境界: `orchestrator/tests/test_check_docs.py:1385-1452`
- D110 型閉包テスト先例: `orchestrator/tests/test_check_docs.py:1555-1743,2137-2163`
- command 変異 fixture: `orchestrator/tests/test_check_docs.py:3357-3888`
- operation 外延 pin: `orchestrator/tests/test_check_docs.py:3891-3929`
- living docs 外延: `orchestrator/tests/test_check_docs.py:4325-4344`

### Fixture 更新

`_write_command_guard_docs()` は primary/risk の両 registry を描画する。`refs()` の operations 特例は単一 path の range を仮定せず、各 path の ID集合から range表現を作る。

`_OPERATION_CONDITION_KEYS` は `docs/dev-wave/operations.md` という path で抽出せず、section が `DW-O` で始まる condition keyを抽出する。

### Pin テスト

既存3テストは次のように更新する。

1. `test_dev_wave_reference_limits_pin_adjudicated_caps`

   新名 `DEV_WAVE_PRIMARY_REFERENCE_LIMITS` を使い、9,600 / 5,000 / 3,750 / 8,400を完全一致で固定する。

2. `test_dev_wave_reference_budget_pins_cap_sum`

   primary cap 総和を引き続き26,750に固定する。

3. `test_dev_wave_reference_budget_pins_aggregate_ceiling`

   25,200と110を固定し、併せて command の9,500 / 140、新族2,600 / 500 / 2,900、全体27,200を固定する。

これにより既存 cap・aggregate・command 予算を1 byteも上げていないことを機械で固定できる。変更前実装に対しては新名・新族定数が存在しないため、新テスト版は赤になる。

### 新規テスト

| テスト | 実装後にテストが緑となる条件 | 変更前実装で赤となる理由 |
|---|---|---|
| `test_dev_wave_risk_unregistered_member_is_rejected` | `docs/dev-wave-risks/extra.md` が未登録実体 finding 1件を生む | 旧 checker は sibling root を列挙せず target finding がない |
| `test_dev_wave_risk_registered_member_missing_is_rejected` | `guards.md` 削除で登録 member 不在を含む | 旧 checker に登録集合がなく、その finding がない |
| `test_dev_wave_risk_member_symlink_is_rejected` | `hang.md` を外部 symlink にすると target を開かず拒否 | 旧予算読取集合に新 member がない |
| `test_dev_wave_risk_root_symlink_is_rejected` | root symlink を走査せず拒否 | 旧 checker はrootの存在自体を知らない |
| `test_dev_wave_risk_required_h2_multiplicity_is_rejected` | `DW-O09` をH3化、または複製すると count 0/2 finding | 旧 checker にrisk H2 registryがない |
| `test_dev_wave_risk_orphan_h2_is_rejected` | `DW-O99` 追加を孤児として拒否 | 旧 checker は新ファイルのH2を検査しない |
| `test_dev_wave_risk_family_accepts_2900_and_rejects_2901` | 各 member cap内で2,900は緑、2,901は族 ceiling finding | 旧 checker に族集計がない |
| `test_dev_wave_risk_cap_sum_accepts_110_percent_and_rejects_plus_one` | cap総和3,190は緑、3,191は赤 | 旧 checker にrisk cap-sum gateがない |
| `test_dev_wave_all_reference_accepts_27200_and_rejects_27201` | primary≤25,200、risk≤2,900を保った境界で判定 | 旧 checker に横断 ceilingがない |
| `test_dev_wave_all_cap_sum_accepts_110_percent_and_rejects_plus_one` | 29,920は緑、29,921は横断 cap-sumだけ赤 | 旧 checker に横断 gateがない |
| `test_dev_wave_risk_registry_three_faces_asymmetry_is_rejected` | budget/section/dispatch の各1面だけを変える3 parameterが各1 finding | 旧 checker に比較 helperがない |
| `test_dev_wave_risk_dispatch_pair_closure_is_rejected` | path集合は同じまま O14 の所属だけ変えて拒否 | path集合だけでは検出できず、旧 checkerにもpair閉包がない |
| `test_dev_wave_risk_command_dispatch_path_mismatch_is_rejected` | O14をallowlist内の旧 operations pathへ戻して段/条件契約違反 | 旧契約はその旧 path を正解としていた |

負例テストは「checker が赤を返したので pytest テストは緑」という意味である。各テストは target finding と件数まで固定し、単なる非0では通さない。

`test_operation_contract_pins_exact_section_set` は全20 IDの literal setを維持し、各 ID の期待 path mapも固定する。段 5・6が `_ALL_OPERATIONS` 全体を消費すること、O23が primary のままであることも残す。

## 4. `.claude/commands/dev-wave.md` の差分

行番号は変更前ファイル基準。

### 段 dispatch

- `.claude/commands/dev-wave.md:66`

  primary: `O01`〜`O03`, `O05`, `O12`, `O13`, `O15`〜`O20`, `O23`

  risk: `docs/dev-wave-risks/guards.md` の `O04`, `O06`, `O08`〜`O11`, `O14`

- `.claude/commands/dev-wave.md:70`

  primary mutation: `M02`〜`M05`, `M07`, `M08`

  risk hang: `docs/dev-wave-risks/hang.md` の `M06`

- `.claude/commands/dev-wave.md:71`

  line 66と同じ operation 分割を「成立した全」条件に適用。

- `.claude/commands/dev-wave.md:74`

  `O17` は `docs/dev-wave/operations.md`、`O04` は `docs/dev-wave-risks/guards.md`。

`.claude/commands/dev-wave.md:62-63` の段 2・3 preflight は `O03` を移さないため変更しない。

### 条件 dispatch

第3列 pathだけを次で変える。

- `.claude/commands/dev-wave.md:87`: condition 04
- `.claude/commands/dev-wave.md:89`: condition 06
- `.claude/commands/dev-wave.md:90`: condition 08
- `.claude/commands/dev-wave.md:91`: condition 09
- `.claude/commands/dev-wave.md:92`: condition 10
- `.claude/commands/dev-wave.md:93`: condition 11
- `.claude/commands/dev-wave.md:96`: condition 14

いずれも `docs/dev-wave-risks/guards.md` へ変え、ID・発火条件・最遅期限は変更しない。

現行内容へ上記の exact rowsをメモリ上で適用した見積りは次である。

- 9,265 bytes ≤ 9,500、余裕235
- 最長137 chars ≤ 140、余裕3
- 変更行中の最長は130 chars
- 全体最長は変更しない現行 `.claude/commands/dev-wave.md:63`

## 5. A1〜A11 の統合案

各 bytes は記載文と末尾改行1 byteを含む。

1. **A1 — 144 bytes**

   `docs/dev-wave/operations.md:16-17` の「同名 artifact と共有しない。」直後。

   > 並列子ごとに専用 subdirectory と一意な prompt / log / `.done` / `-o` 出力を割り当て、2 子へ同じ path を渡さない。

2. **A2 — 163 bytes**

   `docs/dev-wave/operations.md:8` の `codex exec` wrapper 文直後。

   > background job へ置く場合も `codex exec` 自体は同 job の foreground で完走させ、launcher の return 後に子が生存すると仮定しない。

3. **A3 — 154 bytes**

   `docs/dev-wave/operations.md:120` の専用 handoff 文直後。

   > worktree から `qsub` する場合は `-o` / `-e` に job tmp の絶対 path を指定し、既定の `.o<ID>` / `.e<ID>` を root へ落とさない。

4. **A4 — 146 bytes**

   `docs/dev-wave/mutation.md:31-33` の `flock` fail-closed 文直後。

   > 他 wave が repo 単位 `flock` を保持中なら正常な相互排他として abort し、解放不能なら本走未実施と記録する。

5. **A5 — 103 bytes**

   `docs/dev-wave/workers.md:36` の実走範囲報告 bullet直後。

   > - build 不能時は、子の参照識別子を親が受入前に実 checkout で実在確認する。

6. **A6 — 138 bytes**

   `docs/dev-wave/core.md:29-30` の受入・実測環境確定文直後。

   > scope に新機構があれば brief 確定前に `DW-G01` の最安生死確認を行い、結果と driver を brief に記録する。

7. **A7 — 99 bytes**

   `docs/dev-wave/workers.md:12-15` の敵対レンズ説明直後。

   > exploit を作らせず、どの構文クラスが全拒否分岐を外れるか列挙させる。

8. **A8 — 134 bytes**

   `docs/dev-wave/core.md:38-39` の F35 stale 判定文直後。

   > 引数タスクが worklog 末尾で完了扱いなら brief を作らず、一次資料との照合結果を親の裁定へ返す。

9. **A9 — 147 bytes**

   `docs/dev-wave/core.md:32-36` の段1前提実測段落末尾。

   > 同じ前提を stdin heredoc 等の file を書かない実行で測れるなら一時編集より優先し、command と結果を記録する。

10. **A10 — 111 bytes**

    `docs/dev-wave/workers.md:43` の「親 docs が未 land」bullet直後。

    > - 親 docs 確定後の契約逐語だけを渡し、変更時は即同期して旧成果を採用しない。

11. **A11 — 124 bytes**

    `docs/dev-wave/mutation.md:7-10` の単一理由性段落直後。

    > 予算対象の変異は byte 中立だけを登録し、非中立は kill 理由が二重になるため登録しない。

A1/A2 は次の一規則として読む。

> 親が background に置く単位は「子ごとの専用 job」であり、その job 内の `codex exec` は foreground で完走する。job dir、`-o`、`.done` は子ごとに一意で、完了は `.done` と exit codeだけで判定する。

これなら「background jobを使う」と「launcherから二重に切り離さない」は衝突しない。

### 統合後の4ファイル

| file | 現行 | 移設 | A追加 | 見積り | cap | 余裕 |
|---|---:|---:|---:|---:|---:|---:|
| `core.md` | 8,537 | 0 | 419 | 8,956 | 9,600 | 644 |
| `workers.md` | 4,623 | 0 | 313 | 4,936 | 5,000 | 64 |
| `mutation.md` | 3,682 | -258 | 270 | 3,694 | 3,750 | 56 |
| `operations.md` | 8,356 | -2,212 | 461 | 6,605 | 8,400 | 1,795 |
| **primary 合計** | 25,198 | -2,470 | 1,463 | **24,191** | **25,200** | **1,009** |

特に workers と mutation の余裕が小さいため、逐語案を変更した場合は再計測が必須である。

## 6. [T-282] 残留検出

### P3を採る恒久 tool 案

新設面は以下。

- `tools/measure_test_residue.py:1`
- `orchestrator/tests/test_measure_test_residue.py:1`
- 実行場所分類: `tools/README.md:3-19`
- 自動 dispatch まで行うなら `tools/pegasus/dispatch_compute.py:53-74` と `docs/pegasus-runbook.md:315-343`

CLI案:

```text
measure_test_residue.py
  --root /tmp
  --prefix s8b-selector-
  --prefix izanagi-projected-
  --prefix izanagi-task-run-
  --report <shared-path>/residue.json
  -- python3 tools/run_tests.py
```

同一計算ノード・同一process treeで次を行う。

1. 実行前に `/tmp` 直下の自己UID entryを `(st_dev, st_ino, path)` で採取。
2. child commandを実行。
3. 終了直後に同じ snapshotを採取。
4. 新 pathまたは新 inodeだけを残留とする。
5. symlinkを追わず、同一filesystem内の apparent bytesを inode重複排除で数える。
6. longest-prefix matchで件数・bytesを集計し、未分類を必ず `<unclassified>` に入れる。
7. hostname、PBS_JOBID、UID、HEAD、command、開始終了時刻、child rc、raw entry一覧もJSONへ残す。
8. scan中の消滅・権限失敗は `complete=false` とし、0 bytesとして扱わない。

テストは、新規／既存entryの分離、prefix集計、未分類、symlink非追跡、消滅race、child rc伝播を固定する。

ただし `tools/pegasus/dispatch_compute.py:53-74` の task enum は tests/provenanceの閉集合で、`tools/README.md:14-17` は追加にD105 supersedeを要求している。恒久 tool単体では login nodeから正しい計算ノード `/tmp` を測れない。最小案は手動 `qsub` から toolを呼ぶこと、自動化案は別裁定を伴う4〜6ファイル変更になる。

### 推奨する「実測だけで閉じる」案

tracked toolを増やさず、wave専用 job tmpに一回限りのPBS scriptを置く。

1. `-o` / `-e` は job tmpの絶対 pathにする。
2. 同一の計算ノード job内で、実行前 snapshotをNUL区切りで保存する。

   ```text
   find /tmp -xdev -mindepth 1 -maxdepth 1 -uid <uid> \
     -printf '%D\t%i\t%p\0'
   ```

3. `IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py` を引数なしで実行する。
4. 終了後に同じ snapshotを採る。
5. `(device,inode,path)` 差分の各entryを `du -sb --apparent-size --one-file-system` 相当で測る。
6. static `rg` で列挙した `tempfile.*(prefix=...)` の prefix一覧を longest-matchで適用する。
7. `s8b-selector-`、`izanagi-projected-`、`izanagi-task-run-` を明示し、全てに一致しないentryも別欄へ残す。
8. prefix別 `new_entries/new_bytes`、全体合計、raw paths、test rcを insightへ保存する。

同一UIDの別jobが混ざるため、可能なら排他的割当を使う。排他が確認できない測定は上界として記録し、T-282を確定閉鎖しない。既存の自己所有 `/tmp` を削除して「clean」に見せてはならない。

`tools/run_tests.py:918-926` の未stage削除・RuleOps・submodule preflightは測定より優先される。rc=13等で止まった場合は「pytest未実施」と記録し、残留0でも全走測定として採用しない。`tools/run_tests.py:717-813` の sidecarも同じ前後差分へ自然に入る。

費用は、恒久案が新tool約200行前後＋テスト＋実行場所契約、実測案がjob tmpの短いprobeとinsightだけである。再現性は恒久案が高いが、現時点の要求は一回の全走測定なので実測案を勧める。

## 7. 変異事前登録候補

新 helperは単一 findingを返す粒度にし、次の byte中立置換だけを段4候補にする。

| gate | byte中立変異 | 単一理由となる fixture | 手前の検査 |
|---|---|---|---|
| 未登録実体 | `len(extra) != 0` → `== 0` | extra 1件、他は完全 | primary閉包 `tools/check_docs.py:2590-2611` は sibling rootを見ない |
| member不在 | `len(missing) != 0` → `== 0` | 1 memberだけ不在 | risk閉包 helperが最初の検査 |
| root symlink | `is_symlink()` → `is_file   ()` | directory symlinkを純粋列挙helperへ渡す | helper単体では `_safe_read_text` より前 |
| 必須H2 multiplicity | `count != 1` → `count == 1` | `##`→`# `でbyte数を変えず count 0 | closure・個別capはH2を見ない |
| 孤児H2 | `len(orphan) != 0` → `== 0` | 必須H2完備＋孤児1件 | multiplicityは孤児IDを必須集合として扱わない |
| risk cap総和 | `>` → `<` | 3,191、各文書実 bytesはcap内 | `tools/check_docs.py:2558` より前に同じ構成検査なし |
| risk族 ceiling | `>` → `<` | 合計2,901、各member cap内 | 個別capは通るよう配分 |
| 全体 ceiling | `>` → `<` | 合計27,201、primary/risk各ceiling内 | 先行する2 family gateは通る |
| 三面path一致 | `face_count != 1` → `== 1` | 1面だけ別集合 | physical closure・H2を整合させる |
| pair閉包 | `contract_pairs != registered_pairs` → `==` | path集合同一、O14だけ誤所属 | path三面は同じ集合なので通る |

`!=`/`==` は2 bytes、`>`/`<` は1 byte、`is_symlink` と空白込み `is_file   ` は同じ10 ASCII bytesである。

次は登録しない。

- member symlink: `_safe_read_text` の既存二層防護を再利用するため、新設 gateではない。
- 個別 cap: `tools/check_docs.py:2687` の既存 gateを再利用する。
- command段／条件比較: `tools/check_docs.py:3027,3040` の既存 gateであり、全 keyを巻き込む変異は単一理由にならない。
- operation path mapの文字列置換: path長が異なりbyte中立にできない。

これらは境界テストでは被覆するが、B-057事前登録には入れない。

## 8. 実装単位と依存順

1. **裁定 U0 — 親**

   `risks` 軸、O04追加、全体27,200 ceiling、P3不採用を確定する。ファイル編集なし。

2. **checker U1 — Codex author**

   所有: `tools/check_docs.py` のみ。

   定数、operation map、closure、予算、H2、三面一致を実装する。

3. **docs U2 — 親**

   所有: `.claude/commands/dev-wave.md`、既存4 reference、新2 referenceのみ。

   U0確定後はU1と並行可能だが、定数名・path・ID集合を変更しない。

4. **tests U3 — 別 Codex author**

   所有: `orchestrator/tests/test_check_docs.py` のみ。

   U1の公開識別子と finding 逐語が確定してから着手する。

5. **residue U4 — P3採用時だけ別 Codex author**

   所有: `tools/measure_test_residue.py` と `orchestrator/tests/test_measure_test_residue.py`。

   dispatch統合を行うならD105 supersede後の別単位とし、U1/U3へ混ぜない。

6. **統合・実測 U5 — 親**

   U1→U3とU2を統合し、静的 checker、計算ノードの関連テスト・全走、移設スライスhash、残留実測、記録を行う。

pytestは `pegasus02` で直接起動せず、親が `tools/run_tests.py` 経由で計算ノードへ送る。本 workerはテスト結果を緑と主張しない。

## 総括

(a) `docs/dev-wave-risks/{guards,hang}.md` へ2,470 bytesを移し、個別2,600/500、族2,900、横断27,200で閉じる案を勧める。  
(b) P1の「外側」は賛成、`rare` とP2の頻度軸は反対してrisk軸＋O04へ変更、P3恒久toolは反対して一回限りの同一計算ノード実測を勧める。  
(c) 親は全体予算の実質1,748 bytes増を裁定し、exact prose後のbytes、移設hash、入口9,500/140、排他的計算ノード上のprefix別残留を実測する必要がある。