静的レビューの結論は **must-fix 1 件、should-fix 3 件、nit 2 件**です。pytest は実走しておらず、緑とは判定しません。

## 裁定契約との照合

### plan v2 1: `s8b_holdout_freeze.py`

| 要求 | 判定 | 根拠 |
|---|---|---|
| 同一 `(env_tag, proto8)` の earlier `<TS>` のみ列挙 | 実装あり | `s8b_holdout_freeze.py:1704-1763`。`ts >= selected.ts` を除外している。 |
| worktree を nofollow で列挙 | **部分違反** | `:1717-1723` の `lstat` 後、`:1725` で path を再利用する check-then-use。dirfd に束縛されず、親 directory の transient symlink 置換を防げない。 |
| earlier の derived bit を admission から導出 | 実装あり | `:1766-1835`。`inspect_floor_holdout_admission_evidence` の戻り値だけを使用。 |
| reported `eligible_for_refreeze` を使わない | 遵守 | earlier result は bytes 捕捉のみで、field を parse していない。`test_s8b_holdout_freeze.py:1892-1905` に負例あり。 |
| derived True は競合、導出不能は fail-closed | 遵守 | `s8b_holdout_freeze.py:1847-1857`。 |
| result の `protocol_sha256` を読んで除外しない | 遵守 | `_derive_floor_selection_eligibility` に result parse がない。 |
| selected certificate と path 秒を束縛 | 実装あり | `:1654-1677`。既存 `validate_launch_certificate` を再利用。 |
| 既存 gate 順序を維持 | 遵守 | `_validate_floor_inputs` 完了後の `:1951-1961` に新 gate、closure は `:1973` 以後。 |
| 戻り値の意味を変えない | **厳密には違反** | `_validate_floor_inputs` は 6 tuple から 7 tuple へ変更された `:1373-1375,1648-1651`。既知 caller は 1 件だけだが、裁定文には合わない。 |
| projector を共有 private helper 化 | 遵守 | `:1349-1370`。 |

### plan v2 2: `s8b_ratified_freeze.py`

| 要求 | 判定 | 根拠 |
|---|---|---|
| loader は投影 equality のみ | 遵守 | `s8b_ratified_freeze.py:1054-1085`。filesystem namespace、admission policy は参照しない。 |
| current launch のみ選択 identity | 遵守 | `:3303-3322` の `result_type is LaunchValidatedFreeze` 分岐内だけ。 |
| `ReverifiedFreeze` に適用しない | 遵守 | 同分岐外。正例は `test_s8b_ratified_verify.py:872-877`。 |
| `EQUALITY_CHAIN_ADJACENCY` 不変 | 遵守 | 現行定義 `s8b_ratified_freeze.py:149-182` に差分なし。 |

### plan v2 3: fixture / test

- 実 certificate は test-local に構築されている: `s8b_v2_freeze_fixture.py:82-98`。
- floor 期待投影も production helper を使わない: `test_s8b_ratified_freeze.py:229-240`。
- 登録負例は概ね存在する。ただし resume earlier 正例は、実 admission 導出と candidate の組合せを 1 本で通していない。詳細は D1124 節。

### 禁止事項 13 件

| # | 禁止事項 | 判定 |
|---:|---|---|
| 1 | 既存資格検査を緩めない | 遵守。既存 gate は `s8b_holdout_freeze.py:1417-1647` に残る。 |
| 2 | skip を追加しない | 遵守。変更行に skip 追加なし。 |
| 3 | xfail を追加しない | 遵守。変更行に xfail 追加なし。 |
| 4 | 期待値反転・削除をしない | 遵守。既存 assert の削除なし。fixture 正規化のみ。 |
| 5 | `floor_protocol.json` bytes 不変 | 遵守。SHA-256 は `261cec1c...74aac`、HEAD blob と同一。 |
| 6 | `holdout_freeze.json` bytes 不変 | 遵守。SHA-256 は `315b1eb8...bc688`、HEAD blob と同一。 |
| 7 | `_PROTOCOL_KEYS` 不変 | 遵守。`s8b_floor_contract.py:52-58` に差分なし。 |
| 8 | `_RESULT_KEYS` 不変 | 遵守。`s8b_floor_contract.py:81-87` に差分なし。 |
| 9 | `V2_TOP_LEVEL_KEYS` 不変 | 遵守。`s8b_holdout_freeze.py:910` と批准側定義に差分なし。 |
| 10 | `EQUALITY_CHAIN_ADJACENCY` 不変 | 遵守。`s8b_ratified_freeze.py:149-182`。 |
| 11 | 公開 CLI・artifact 種別・schema version を増やさない | 遵守。新 CLI/parser/schema key なし。 |
| 12 | 署名・nonce・一回性台帳・予約番号・墓標を作らない | 遵守。既存 admission は read-only inspector として再利用。 |
| 13 | docs を編集せず commit しない | 遵守。差分は指定 6 file のみ、staged 差分なし、HEAD は `6ee1f1413...`。 |

## 恒真性

- `_assert_floor_selection_identity` は、earlier が空または全て derived False なら `eligible` が selected だけなので恒真です。`s8b_holdout_freeze.py:1843,1858-1860`。
- 述語全体は恒真ではありません。非恒真入力は、同一 namespace に次の 2 run が存在する場合です。

  - A: `20260810T235900Z-<proto8>`、derived True
  - B: `20260811T000000Z-<proto8>`、selected

  この場合 `min` は A となり、B を `:1860-1864` だけが拒否します。既存 gate は selected B しか検査しないため先行拒否しません。負例は `test_s8b_holdout_freeze.py:1950-1980` ですが、derived bit は monkeypatch です。

- certificate 束縛も非恒真です。selected result 自体が正常で、certificate の `started_utc` だけ 1 秒ずれた入力を `:1654-1677` だけが落とします。負例は `test_s8b_holdout_freeze.py:2028-2050`。
- loader 投影 equality は candidate producer 内では構造上恒真です。ただし loader は独立に批准された g1 を読むため、`floor_source=A`、`generation.floor=project(B)` を構成できます。transition table は `/floor` と `/floor_source` を独立に許すため、既存 gate は落としません。負例は `test_s8b_ratified_freeze.py:1477-1488`。したがって loader 述語は非恒真です。
- 静的 symlink 述語は非恒真ですが、TOCTOU 下では実効性がありません。静的負例 `test_s8b_holdout_freeze.py:2053-2074` は directory の検査後差替えを扱いません。

## 適格性導出の権威

earlier の自己申告 `eligible_for_refreeze` は読んでいません。`result_before` は `s8b_holdout_freeze.py:1784-1786` で bytes 捕捉されるだけです。

inspector 引数の起源は次のとおりです。

- earlier 固有: manifest hash `:1812`、run ID `:1813`、run path `:1814`、earlier journal sessions `:1793-1799,1815`。
- 共有 authority: protocol、freeze document、そこから導出した cells/schedule `:1801-1816`。
- selected result、selected manifest、selected journal の値は混入していません。
- ただし launch 経路の `v1=ratified.document` は物理的には selected generation document です `s8b_ratified_freeze.py:3305-3309`。holdouts は transition で v1 と同値に保護されているため、現コード上の membership 改変にはなりません。
- `proto8` 衝突で earlier の full protocol が異なる場合、共有 protocol と admission row の full hash が合わず「導出不能」となり fail-closed します。これは裁定の「衝突は過剰包含、拒否側」と整合しますが、その専用テストはありません。

## D1124 の非再発

コード上は再発していません。derived False の earlier は `eligible` に追加されず `s8b_holdout_freeze.py:1856-1858`、later selected だけで `min` が決まります。

テストは二分されています。

- 実 admission marker から resume を False と導出: `test_s8b_holdout_freeze.py:1908-1942`
- earlier を False と仮定して later candidate を受理: `:2005-2025`

後者は `_derive_floor_selection_eligibility` を monkeypatch し、earlier fixture には manifest/journal がありません。したがって「実 resume earlier を列挙し、その実 admission から False を導出し、later candidate を最後まで作る」正例そのものは存在しません。現実装の流れは正しいものの、統合配線の回帰を完全には殺せません。

## certificate 束縛と historical

candidate と批准 launch はともに `s8b_launch_cert.validate_launch_certificate` を使います。

- candidate: `s8b_holdout_freeze.py:1668-1675`
- 批准 launch: `s8b_ratified_freeze.py:3217-3222`
- 共通正規化: `s8b_launch_cert.py:74-124`

共通 helper は UTC offset 0 を要求し、microsecond を落として run ID の秒と比較します。批准側の equality node `s8b_ratified_freeze.py:3332-3342,3385-3392` と受理集合のずれはありません。

historical への選択 identity 漏れもありません。

- loader の追加検査は H-pure 投影だけ。
- current build policy は既存どおり `LaunchValidatedFreeze` のときだけ `s8b_ratified_freeze.py:3228-3231`。
- 選択 identity も同じ current 分岐だけ `:3303-3309`。
- `ReverifiedFreeze` 正例が `test_s8b_ratified_verify.py:872-877` にあります。

## 既存挙動の破壊

- 既存 assert、期待 reason、skip/xfail の変更はありません。
- `s8b_v2_freeze_fixture.py` の `{}` certificate は、新しい candidate 境界を通る正規 certificate へ修正されています。certificate は closure の dedicated path なので、既存 closure 集合の意味を広げません。
- `_FLOOR_SOURCE_STUB` は JSON result 形へ直され、g1 の `floor` も test-local 投影へ追随しています `test_s8b_ratified_freeze.py:214-240,1403-1414`。新 gate を甘くする変更ではありません。
- `s8b_v2_freeze_fixture.py` 自体は oracle driver/manifest/report tests から import されていますが、今回変更した certificate builder と `candidate_repository` の直接 consumer は `test_s8b_holdout_freeze.py` だけです。
- pytest は実走していないため、既存 consumer が実際に通るとは報告しません。

## TOCTOU と波及

### TOCTOU

`_require_nonsymlink_directory_chain` は inode を保持せず Path を返すだけです `s8b_holdout_freeze.py:1680-1701`。その後の `os.scandir(namespace)`、certificate capture、manifest/journal capture は path を再解決します。

具体的には、selected run directory を検査後だけ symlink に差し替えると、`_capture_regular_nofollow` の `O_NOFOLLOW` は leaf にしか効かず、親 symlink を通った certificate を読めます。その後 directory を戻せば、後段の chain 再検査も通ります。よって「official path に実在する certificate」の検査になっていません。

再捕捉については、

- manifest と journal は inspector 入力なので `:1822-1831` の byte 再捕捉に意味があります。
- result bytes は eligibility 計算に一度も使われないため、result の byte equality は「存在が途中で変わらなかった」以上の保証をしません。
- admission filesystem は inspector 内の shared lock 中だけ安定します。
- namespace は `entries = tuple(scan)` の一回だけで、再列挙がありません `:1725-1726`。
- directory chain の最後の再検査 `:1832-1834` も、途中の transient symlink 置換を検出できません。

### 所有外 caller と consumer tests

変更面の所有外 caller は以下です。

- `load_ratified_freeze`:
  `p3_autonomous_workload_trial.py:4640`、
  `s8b_oracle_manifest.py:1205`、
  `s8b_oracle_driver.py:488,636,1328`、
  `s8b_oracle_report.py:2455`、
  `s8b_oracle_judge.py:749`、
  `s8b_verdict.py:828`、
  `s8c_result_judge.py:2108,2188`
- `launch_validate`:
  `s8b_oracle_driver.py:656,1344`
- `reverify_published_freeze`:
  `s8b_oracle_report.py:2456`、
  `s8b_oracle_judge.py:750`、
  `s8b_verdict.py:829`
- candidate:
  `s8b_holdout_freeze.py:2098,2153` の generator/CLI

壊れる可能性がある代表 consumer test は次です。

- 直接 loader/launch: `test_s8b_ratified_freeze.py:1446`、`test_s8b_ratified_verify.py:822-824`
- oracle driver: `test_s8b_oracle_driver.py:5490-5496`
- oracle report: `test_s8b_oracle_report.py:1553-1563`
- verdict: `test_s8b_verdict.py:556-562`
- autonomous workload: `test_p3_autonomous_workload_trial.py:8445`
- oracle manifest: `test_s8b_oracle_manifest.py:1328-1335`
- s8c judge: `test_s8c_result_judge.py:461-469`

後ろ 3 件は loader を monkeypatch しており、新しい loader semantics の実効検査にはなりません。また `s8b_oracle_judge` の実 loader/reverify 経路を直接通す consumer test は参照検索では確認できませんでした。

## must-fix / should-fix / nit

### must-fix

1. **nofollow が check-then-use で、parent directory の transient symlink 差替えを防げない。**  
   `s8b_holdout_freeze.py:1680-1726,1781-1834`。dirfd に束縛した列挙・open、または同等の原子的捕捉が必要です。

   放置時の成果物影響: official path 上の certificate が不正でも別 directory の certificate で candidate が受理され、また earlier A を列挙から隠せば `floor_source` と `floor` が required A ではなく selected B を参照します。

### should-fix

1. D1124 正例を、実 resume earlier の manifest/journal/admission を使う end-to-end test にする。現状は実導出と candidate 受理が monkeypatch 境界で分断されています。
2. `_validate_floor_inputs` の 6 tuple から 7 tuple への変更は「戻り値の意味を変えない」に反します。既知 caller は 1 件でも、path info の再 parse または別 helper で既存契約を保つべきです。
3. launch 側は `_assert_floor_selection_identity` の underivable 以外の全 `FreezeError` を `floor-selection-rule-mismatch` に潰します `s8b_ratified_freeze.py:3310-3322`。symlink、namespace I/O、path 異常まで選択不一致として報告され、consumer の reason/cause が不正確になります。

### nit

1. `FLOOR_SELECTION_RULE_VERSION` は underscore なしの新しい module 公開名です `s8b_holdout_freeze.py:53`。公開 API 面を増やさない意図なら private 名にするのが一貫します。
2. parametrized id `use-reported-eligible` のケースは `_derive_floor_selection_eligibility` 自体を monkeypatch しており、そのテスト単体では reported/derived 変異を殺しません `test_s8b_holdout_freeze.py:1945-1968`。別テスト `:1892-1905` が実際の変異を殺しているため、id が誤解を招きます。

## 総括

選択 identity、derived eligibility、loader 投影、certificate 秒束縛、historical 分離の主要ロジックは裁定どおりで、恒真な主要 gate はありません。

ただし、裁定が要求した nofollow は inode に束縛されておらず、certificate と namespace の検査を TOCTOU で迂回できます。これは受理集合と `floor_source` 参照を変える must-fix です。静的 symlink 負例だけではこの欠陥を検出できません。テスト実走は 0 件です。