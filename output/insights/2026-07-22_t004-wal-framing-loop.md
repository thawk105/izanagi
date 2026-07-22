# [T-004] WAL byte framing + resume 物理修復 ([T-007][T-008] 同梱) — 実装 wave 逐語 (2026-07-22)

ハイブリッド標準ループ (/dev-wave) の逐語凍結。設計判断は D77、変異台帳は
`2026-07-22_t004-wal-framing-mutation-ledger.md`、時系列は worklog 2026-07-22 (6)。

工程: brief (P1..P6、裁定前提 6 種の実測確認つき) → codex プラン起草 (max、GO) → 敵対相談 X/Y
並列 (max、**両方 NO-GO**、計 21 所見) → 親裁定 (rulings v2、採用/部分採用/棄却) → 実装 3 単位
(A 先行 → B1/B2 並列、high) → 親統合 + 継ぎ目 1 件親修正 → 受入全走緑 → 変異 matrix 1 巡目
(15 変異) → 敵対レビュー R1/R2 並列 (max、**両方 NO-GO**、計 21 所見、R1/R2 衝突 1 件は親が
コードで裁定) → fix (codex max、F-A..F-M) → 親再検収 (全走 2618 緑) → 変異 matrix 再構成
18 変異 (ハーネスバグ 1 件を検出・修正 = F33) → 全件設計どおり。

セッション中に /rulings 割り込み 1 回 (裁定 4 件確定、worklog 2026-07-22 (5))。

# [T-004] wave brief — WAL byte 単位 record framing + resume 物理修復 ([T-007][T-008] 同梱)

## scope (確定ユーザー裁定、2026-07-21。正本 = worklog / D68 (8))

- [T-004] generic WAL (`orchestrator/campaign/wal.py`) の byte 単位 record framing と resume の物理修復。
  同類 4 件を含む: 末尾断片への `O_APPEND` 直結 / 改行欠落だけの完全 JSON / multibyte 途中切れの
  `UnicodeDecodeError` / `os.write()` short write 未検査
- [T-007] 未知 stage は拒否する (fail-closed)。stage 追加時は検査側更新を要してよい
- [T-008] payload 型を writer 側でも強制する (追記専用台帳は後から直せないため入口で止める)
- scope 外 (裁定済み・触るな): hash chain / 外部 anchor ([T-003] 裁定 = 作らない)。s8b resume の
  WAL-bytes 拒否 (`wal_bytes_present`) の緩和。terminal 位置 gate・duplicate-key・exact-5-key の変更

## 親の実測 (2026-07-22、実 wal.py + scratch dir、模擬なし)

- (A) 末尾断片後の append は **黙って消える** (fail-open 喪失): 断片+新 record が 1 行に融合し、融合行が
  末尾なら truncated_tail として捨てられ、さらに追記すると中間行汚染で checked reader は恒久 crash
- (B) 改行欠落の完全 JSON 末尾は **正規 record として受理される** (torn write を durable と誤認)
- (C) multibyte 途中切れは `iter_lines` の `readlines()` で UnicodeDecodeError が未処理伝播し、
  collected/checked 両 reader とも crash — **resume 不能** (構造化 anomaly にならない、規律 3 違反状態)
- (D) `wal.py` append の `os.write` 戻り値未検査 (コード読解)
- (E) NaN payload と int key payload が preflight を通過し durable に書かれる (int key は黙って str 化)
- (F) `parse_line` は未知 stage を受理 (`sess1on-typo` が通る)
- 実在 WAL 30 本 / 3,086 record: stage は 7 種のみ (6 pipeline + `s1-session`)、非有限 float 0、
  末尾改行欠落 0、undecodable 0 → 下記白名簿・NaN 拒否での **parse 回帰ゼロを実測済み**
- `wal.py` の bytes を pin する凍結台帳・FROZEN_MANIFEST 項目は無し (F30 対策の全列挙済み)。
  submodule init 済み

## 親の provisional 裁定 (攻撃対象。brief 自身の誤りも所見に含めること)

- (P1) stage 白名簿は `parse_line` の record 契約に入れる。正準集合は `model.py` に集約
  (6 pipeline stage + `s1-session` + `s8b-oracle-session` の 8 種)。`s1_direct_comparison.py` /
  `s8b_oracle_driver.py` / `s8b_oracle_report.py` の `SESSION_STAGE` 定義は model からの import に寄せる。
  D68 (1) の「stage 白名簿は consumer の責務として入れない」は T-007 裁定 (後発) が上書きしたと読む
- (P2) framing 意味論: record frame = `b"\n"` 終端。無終端 tail は JSON 完全でも undecodable でも
  truncated_tail。終端済み行の decode/parse 失敗は crash 遺物ではない → checked では伝播、collected では
  line_issue。根拠 = 正規 writer は行内に生改行 byte を出せない (json.dumps は制御文字を必ず escape)
- (P3) 物理修復は明示関数 (例 `repair_truncated_tail(layout)`) — 最終 frame 境界へ truncate + fsync し、
  除去 byte 数等を構造化返却 (規律 3)。resume 経路が append 再開前に呼ぶ。加えて `append()` は追記前に
  末尾 byte を検査し `b"\n"` 以外なら fail-closed 拒否 (append 自身は自動 truncate しない —
  破壊操作は明示経路のみ)
- (P4) [T-008] = serialize 前の深部型検査: key は str のみ (coercion 拒否)、値は JSON native のみ、
  float は有限のみ、tuple 等の黙変換も拒否。reader 側も `parse_constant` で NaN/Inf を拒否 (両入口)
- (P5) 実装単位: 単位 A (`wal.py` + `model.py` + `test_campaign.py`) を先行完了 → 所有ファイル限定 patch
  展開後、単位 B (consumer 配線 + consumer tests) を投入。B が十分小さければ 1 単位へ統合してよい
- (P6) repair 呼び出しの網羅対象は「既存 WAL に追記しうる resume 経路」= `loop.py` /
  `p3_s4_loop*.py` / `guided.py` / `s1_direct_comparison.py`。s8b oracle driver は resume 拒否のまま対象外

## 不変条件

- 既存 3,086 record の parse 結果 (stage 分布・record 数) 不変 — 受入で再実測する
- D68 契約維持: `WalLineError` ⊄ `JSONDecodeError`/`KeyError`、duplicate-key 拒否、exact 5 key、
  writer preflight、terminal 位置 gate。black-box 迂回を新設しない
- fail-closed: 黙殺経路を増やさない。修復は明示呼び出しのみ。診断は構造化して返す (規律 3)
- 「改竄耐性」「改竄不能」「証明可能」とは書かない (T-060 / D68 (6))
- 凍結成果物・`output/` 配下・docs に触れない (docs は親が書く)

## 成果物の形

- 実装子: コードとテストのみ。親: 統合 commit、変異 matrix 実測、受入全走 (baseline: 直近 branch 緑)、
  D77 起草、worklog、insights 逐語 + 変異台帳


---

## 段 2: プラン起草 (codex max、逐語)

現行コードを追った結果、wave は GO です。ただし P4 は `parse_constant` だけでは不足し、P6 は `screening_driver.py` が漏れています。また P1 の重複解消対象には `s1_report.py` も加えるべきです。

## 設計判断

1. P1 は基本同意。ただし `model.STAGES` は pipeline 6 種という既存意味を維持する。

   - `STAGE_S1_SESSION`
   - `STAGE_S8B_ORACLE_SESSION`
   - `WAL_STAGES = STAGES + 上記2種`

   を追加する。`layer3_report.STAGES` や `s8b_outcome_stage_contract.PIPELINE_STAGES` は consumer 固有の semantic subset なので統合しない。これにより、新 stage 追加時に consumer 側検査の更新が必要という T-007 の fail-closed 性を保てる。

2. P2 に同意。frame 判定は UTF-8 decode より前に binary で行う。

   - `b"\n"` 終端あり: decode/parse 対象。
   - 終端なし: 内容が完全 JSON、壊れた JSON、multibyte 途中切れのいずれでも `truncated_tail`。
   - 終端済みの decode/JSON/record 契約違反: tail 扱いしない。checked reader は伝播、collected reader は `line_issue`。
   - `iter_lines()` は既存 tuple APIを保つ strict adapter とし、無終端 tail では専用 `WalFramingError` を送出する。内部 reader は private binary frame iterator を使う。

3. P3 に同意。`repair_truncated_tail()` は明示的な破壊操作とし、`append()` からは呼ばない。

   返却値は `WalTailRepairResult` のような frozen dataclass とし、少なくとも `status`、`original_size`、`final_size`、`removed_bytes`、`path` を持たせる。最後の `b"\n"` より後だけを `ftruncate` し、変更時だけ file `fsync`。終端済みの不正行は削除しない。

4. P4 は補強が必要。

   - writer: payload root は exact `dict`、key は exact `str`、値は exact JSON native (`None/bool/int/finite float/str/list/dict`) のみ。tuple、set、bytes、enum/subclass、循環参照、非有限 float を深部まで拒否。
   - `payload or {}` は廃止し、`None` のみ `{}` にする。
   - reader: `parse_constant` で `NaN/Infinity/-Infinity` を拒否する。
   - 加えて parse 後も同じ深部有限性検査を行う。`json.loads('1e999')` は `parse_constant` を通らず `inf` になり得るため、P4 のままでは payload 内の overflow 非有限値が残る。
   - serializer にも `allow_nan=False` を置く。

5. P5 は A/B の直列分割を維持する。P6 の漏れを補うと B は小さくないため、1単位には統合しない。

6. P6 は修正する。

   - 対象: `loop.py`、`guided.py`、`s1_direct_comparison.py`、P3 loop の共有 reject writer、さらに `screening_driver.py`。
   - `p3_s4_loop_sort.py` / `p3_s4_loop_trigger_gating.py` は共有 `record_diff_reject()` と `loop.run_campaign()` を通るため、個別 repair 呼出しは不要。
   - s8b oracle driver は `wal_bytes_present()` で再開を全拒否するため修復しない。
   - repo 内の `pipeline.evaluate()` の production 呼出しは loop / screening / S-1 / s8b に収束しており、上記で覆える。漏れがあっても `append()` の末尾 gate が最終防壁として追記を拒否する。

## 変更一覧 (file:line)

| 対象 | 変更内容 | 新旧挙動・影響 consumer | 必要なテスト |
|---|---|---|---|
| `orchestrator/campaign/model.py:20-28, 85-97` | session stage 2 定数と `WAL_STAGES` を追加。既存 `STAGES` は6種のまま。`WalRecord.stage` コメントを更新 | 旧: 任意文字列。新: generic WAL wire contract は8種。pipeline subset の意味は不変 | exact 8 種、6種 `STAGES` 不変、各 consumer alias 一致 |
| `orchestrator/campaign/wal.py:31-45` | `WalPayloadTypeError`、`WalFramingError`、`WalTailRepairResult` を追加 | すべて `WalLineError` 系とし、`JSONDecodeError` / `KeyError` との非継承を維持 | 例外階層と構造化属性 |
| `wal.py:48-82` | `parse_constant`、stage 白名簿、decoded payload の深部 JSON-native/有限性検査 | 旧: typo stage、payload NaN/`1e999` を受理。新: checked は伝播、collected は line issue | 未知 stage、NaN/Inf/`1e999`、既存 duplicate/exact-5-key 回帰 |
| `wal.py:85-92, 133-140` | shared deep validator、`allow_nan=False`、`payload is None` のみ `{}` 化 | 旧: tuple→list、int key→str、falsy list→`{}`。新: serialize 前に専用例外、WAL未作成/既存bytes不変 | nested int key、tuple、set、bytes、循環、非有限、正常 native tree |
| `wal.py:95-104, 145-195` | binary frame iteratorを追加し、終端判定後だけUTF-8 decode。`iter_lines()` は strict adapter。両 reader を frame 基準へ変更 | 旧: 完全JSON無改行を受理、multibyte tailで全reader crash、最終の終端済みJSONエラーをtail扱い。新: 無終端は一律tail、終端済みエラーは異常 | 完全JSON無改行、multibyte tail、終端済みdecode/JSONエラー、blank line |
| `wal.py:107-130` | `repair_truncated_tail()`、末尾境界の後方chunk探索、append末尾byte gate、short-write完遂 loop | 旧: fragmentへ直結、short writeを成功扱い。新: appendは無終端既存WALを無変更で拒否。repair後のみ再開可 | 拒否時bytes不変、0境界/最終改行境界、fsync、partial/zero write |
| `orchestrator/campaign/loop.py:57-68` | lock作成/照合後、`replay()` 前に repair | 旧: replayでtailをmemory上だけ捨て、後続appendが融合。新: identity確認後に物理境界を復元 | tail付き既存campaign再開、lock mismatch時はtail不変 |
| `orchestrator/campaign/screening_driver.py:69-96, 122-145` | `_ensure_campaign_lock()` 後、baseline callback/readおよび candidate replay前に repair | P6 の実漏れ。prepare callback と `evaluate_candidate()` の両方が既存WALへ追記し得る | 2入口それぞれにtailを置き、正常frame列として再開 |
| `orchestrator/campaign/guided.py:129-154` | `_read_meta()` 成功後、既存WAL読取り・`_log_eval()` 前に repair | `start` は既存WAL拒否のため対象外。`evaluate` のみ再開修復 | 既存commit+tailから次genomeを4 frame追記 |
| `orchestrator/campaign/p3_s4_loop.py:213-227` | 共有 `record_diff_reject()` の最初で repair | dry/reject は `run_campaign()` を通らないため必要。build/pass は `loop.py` 側で修復 | base/sort/trigger のreject各1本 |
| `p3_s4_loop_sort.py:221-253` / `p3_s4_loop_trigger_gating.py:377-409` | production codeの個別変更なし | rejectは共有 helper、buildは `run_campaign()` で覆われる。重複repairを置かない | 各consumer testで共有配線を実証 |
| `orchestrator/campaign/s1_direct_comparison.py:29-43, 232-259, 589-645` | `SESSION_STAGE` をmodel importへ。非dry-runでは `_ensure_campaign()` 後、最初のappend前にrepair。ScheduleDeviation記録経路も先にidentity確認+repair | dry-runは非破壊のまま。通常再開とdeviation記録の双方でfragment融合を防止 | 中断session再開、dry-run非変更、lock mismatch非修復 |
| `orchestrator/campaign/s1_report.py:30-40, 173-175` | hard-coded `"s1-session"` をmodel定数へ | P1 の重複取り残しを解消 | `_event()` が正準定数だけを見ること |
| `orchestrator/campaign/s8b_oracle_driver.py:25-52` | `SESSION_STAGE` をmodel importへ | `wal_bytes_present()` のresume拒否は一切変更しない | fragment/完全JSON無改行/multibyte tailの全てを引き続き拒否 |
| `orchestrator/campaign/s8b_oracle_report.py:23-34, 925-955` | session定数をmodel importへ。collected reader APIは維持 | 無終端完全JSONも `truncated_tail` protocol violation。終端済みdecode/parse失敗はline issue | 既存anti-maskingに完全JSON無改行を追加 |
| `orchestrator/campaign/layer3_report.py:81-107` | strict `iter_lines()` の `WalFramingError` を `Layer3ReportError` にcause付きで翻訳 | genericで既知のsession stageもlayer3 semantic subsetでは引き続き拒否 | 完全JSON無改行、multibyte tail、既知sessionのsemantic拒否 |
| `tools/plotting/plot_backoff.py:110-124` | 読取ロジック変更不要。strict化した共有 `iter_lines()` の挙動を継承 | 完全JSON無改行を図データに採らず、`WalFramingError` で全体停止 | backoff consumer testにunframed tail追加 |

`pipeline.py`、terminal位置 gate、duplicate-key、exact 5 key、s8b `wal_bytes_present()` は変更しない。

## 赤くなる既存テストと対処

| 既存テスト | 赤くなる理由 | 変更後の期待 |
|---|---|---|
| `orchestrator/tests/test_campaign.py:421-425 test_wal_log_keeps_baseline_falsy_payload_normalization` | `payload=[]` を `{}` に変換しなくなる | `WalPayloadTypeError`、WAL未作成。別assertで `payload=None` は `{}` として成功 |
| `test_campaign.py:449-456 test_wal_writer_rejects_json_key_collision_before_writing` | int key をserialization後のduplicateとしてではなく、serialization前の型違反として止める | `WalPayloadTypeError` と payload path、WAL未作成。raw duplicate reader testは維持 |
| `orchestrator/tests/test_layer3_report.py:140-143 test_unknown_stage_fails_closed` | 拒否位置がlayer3独自判定からshared `parse_line()` に前倒しされ、診断文が変わる | cause が `WalLineError`、`unknown WAL stage` を明示。さらに既知 `s1-session` がlayer3固有subsetで拒否される別testを追加 |

`test_s1_session_unknown_stage_is_safe_for_existing_wal_consumers` は赤くならないが、名称が新契約と逆になるため `test_s1_session_stage_is_in_shared_wal_contract` へ改名する。

以下は期待値を変えない。

- `test_wal_tolerates_truncated_last_line`
- s8b driver の `test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records`
- s8b report の truncated-tail / anti-masking 群
- duplicate-key、exact-5-key、blank-line、terminal-position 群

## 新規テスト一覧

`orchestrator/tests/test_campaign.py`:

- 完全な5-key JSONでも最終 `b"\n"` がなければ record 0件 + `truncated_tail=True`。
- multibyte途中切れ tail はdecodeせず、checked/collectedとも prior recordsを返す。
- newline終端済みの不正UTF-8は checked で `UnicodeDecodeError`、collectedで行番号付きissue。
- newline終端済みの壊れたJSON最終行はtailでなく checked例外 / collected issue。
- fragment、完全JSON無改行、multibyte tailの各既存末尾に対しappendがbytes不変で拒否。
- repairが最後のframe境界へ切り戻し、その後のappendで全recordを読める。
- 改行が一つもないWALは0 byteへ修復。
- missing / empty / 正常終端WALではrepair no-op。
- repair変更時にfile `fsync` が呼ばれる。
- `os.write()` が実際に一部だけ書いて短い戻り値を返しても、最終frameが一度だけ完全に残る。
- `os.write()==0` は成功扱いしない。
- `WAL_STAGES` が正確に8種で、未知stageをparse/writer双方が拒否。
- 深部の非str key、tuple、set、bytes、custom subclass、循環参照、NaN/Infをopen前に拒否。
- native JSON treeは受理。
- raw payloadの `NaN` / `Infinity` / `-Infinity` / `1e999` をreaderが拒否。
- loop resumeがidentity照合後にtailを修復し、lock mismatchではbytesを変えない。

`orchestrator/tests/test_screening_driver.py`:

- `prepare_screening_campaign()` のbaseline callback前にtailが除去される。
- `evaluate_candidate()` のreplay/evaluate前にtailが除去される。

`orchestrator/tests/test_guided.py`:

- `cmd_evaluate()` が既存commit+tailを修復し、次の4 recordsを独立frameとして追記する。

`orchestrator/tests/test_p3_s4_loop*.py`:

- base/sort/triggerのquarantine reject経路を各1本。tail後のrejectが `build_start` / `abort` の2 frameになる。
- build/pass経路は `run_campaign()` の共通修復を使うことを1本で固定。

`orchestrator/tests/test_s1_direct_comparison.py`:

- `session-start` 後のtailから再開し、retry/session-resultが独立frameになる。
- dry-runはtailを物理変更しない。
- session constant testを正準契約名へ改名。

`orchestrator/tests/test_s8b_oracle_driver.py`:

- V5を fragment / 完全JSON無改行 / multibyte tail でparameterizeし、すべて `wal_bytes_present` 拒否を維持。

`orchestrator/tests/test_s8b_oracle_report.py`:

- completed terminal後の完全JSON無改行を `truncated_tail` の単一protocol reasonとして扱う。
- newline終端済みJSON構文違反はline issueになり、correctness-redをmaskしない。

`orchestrator/tests/test_layer3_report.py` / `test_backoff_consumers.py`:

- 完全JSON無改行とmultibyte tailの双方を拒否。
- layer3ではcause型も固定。
- plottingでは部分的なplot dataを返さない。

`test_campaign.py` の追加testは素のrunner契約を壊さないよう、pytest専用fixtureに依存させず `_tmp_dir()` と手動patch復元を使う。

## 変異登録候補

| ID | 無効化する1箇所 | 単一理由で赤くなるテスト |
|---|---|---|
| M01 | `wal.py:95-104` 相当の `raw.endswith(b"\n")` 判定を常にtrue化 | 完全JSON無改行がrecordとして復活 |
| M02 | 同frame scannerで終端判定より先にUTF-8 decode | multibyte tail testが `UnicodeDecodeError` |
| M03 | `wal.py:109-122` 相当のappend末尾byte gateを削除 | append拒否testでbytesが融合・変化 |
| M04 | `repair_truncated_tail()` の `ftruncate(last_newline+1)` をno-op化 | repair後append testが `WalFramingError` |
| M05 | short-write loopを現行の単発 `os.write()` に戻す | partial-write testで完全recordが残らない |
| M06 | `parse_line()` の `stage in WAL_STAGES` を削除 | typo stageのparse/writer拒否test |
| M07 | deep validatorの `type(key) is str` を削除 | `{1: "value"}` が `"1"` にcoerceされるtest |
| M08 | deep validatorでtupleをlist相当として許可 | tuple拒否testがdurable writeまで到達 |
| M09 | decoded payloadの有限float検査を削除 | raw `1e999` が `inf` として受理されるtest |
| M10 | `screening_driver.py:130-134` 後のrepair呼出しを削除 | candidate resume testがappend末尾gateで停止 |

`parse_constant` 削除についても、NaNの専用診断が深部有限性エラーへ後退する診断pinとして登録できる。ただし受理集合は深部検査でも閉じるため、kill件数には混ぜない。

## 実装単位分割案

1. 単位A — generic WAL契約

   - `model.py`
   - `wal.py`
   - `test_campaign.py`

   framing、repair API、short-write、stage、payloadを完成させる。既存 reader APIの戻り値形は維持する。確認は WAL focused pytest と `python3 orchestrator/tests/test_campaign.py`。

2. 単位B — consumer配線

   - `loop.py`
   - `screening_driver.py`
   - `guided.py`
   - `p3_s4_loop.py`
   - `s1_direct_comparison.py`
   - `s1_report.py`
   - s8b driver/report
   - `layer3_report.py`
   - 各consumer tests

   sort/trigger本体と plotting は共有経路を使うため、必要以上の重複実装を置かない。

3. 親の統合・受入

   - 30 WAL / 3,086 recordsを再走査し、record数・stage分布・各record内容が変更前snapshotと一致。
   - 全WALが `truncated_tail=False`、undecodable 0。
   - focused consumer tests → 全suite → `check_codex_agents.py` → `check_docs.py`。
   - 事前登録した変異matrixを実測。
   - その後に親だけがD77、worklog、insights、変異台帳、統合commitを扱う。

凍結成果物、`output/`、docs、hash chain、terminal gate、s8b resume拒否には触れません。今回のプラン作成ではファイル変更も行っていません。

---

## 段 3: 敵対相談 X — 正しさ境界レンズ (max、逐語。判定 NO-GO)

framing 前提そのものは攻撃しても崩れなかった。`json.dumps(..., ensure_ascii=False, indent=None)` は、深部の文字列と key に含まれる U+000A を `\\n` に escape する。`ensure_ascii=False` が無効にするのは非 ASCII の強制 escape であり、制御文字 escape ではない。現行 producer も、tuple 版番号を list 化する verifier、dict/list/数値で組む pipeline、`dict(event)` を使う S-1/s8b まで追ったが、正常に UTF-8 encode できた writer 出力へ payload 由来の生 `0x0a` が入る経路はない。[wal.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:85) [verifier/report.py:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/verifier/report.py:15) [pipeline.py:329](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/pipeline.py:329)

以下はそれでも残る blocker である。

1. `[severity high] / 対象: brief P1・設計判断1`

   - 壊れ方: `WAL_STAGES = pipeline 6種 + session 2種` は「既知」と「この campaign で許可」を混同する。通常の P2 WAL に `stage="s8b-oracle-session"` を混ぜると shared parser は受理し、`replay()` は terminal でない inert stage として取り込み、P2 report/critic は分岐に該当しないため黙って無視する。逆に s8b WAL 内の `s1-session` も terminal より前なら session/pipeline のどちらにも分類されず protocol violation にならない。
   - 根拠: [wal.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:204)、[p2_2_report.py:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p2_2_report.py:63)、[s8b_oracle_report.py:255](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:255)
   - 最小修正案: global recognition set と campaign profile を分離する。writer/read/replay に `allowed_stages` を必須で渡し、pipeline、S-1、s8b の相互 stage 注入をすべて拒否するテストを置く。D68 (1) の consumer 責務は T-007 後もこの文脈認可について残る。

2. `[severity high] / 対象: brief P3・P6、プラン「repair_truncated_tail」`

   - 壊れ方: repair と append を排他する WAL lock がない。二つの resume が同じ cut offset を得て、A が truncate→正当な record を append+fsync した後、B が古い offset へ truncate すれば A の durable record を削除する。`campaign.lock` は内容照合ファイルで、保持される mutex ではない。
   - 根拠: [loop.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:57)、[wal.py:254](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:254)、[lock.py:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/lock.py:42)
   - 最小修正案: 安定した per-WAL sidecar lock を設け、repair の scan→`ftruncate`→file `fsync` と append の gate→全 write→file `fsync` を同じ exclusive lock 内に置く。reader も安定 snapshot が必要な入口では shared lock を取る。二重 repair と repair-vs-append の deterministic multiprocessing test が必要。

3. `[severity high] / 対象: brief P3、プラン「append末尾byte gate」「short-write完遂 loop」`

   - 壊れ方: gate と write の間が TOCTOU である。A が正常 LF を確認後に停止し、B が partial tail を書き、A が `O_APPEND` で record を書けば融合する。また A の write が短く、A-prefix→B-full-frame→A-suffix の順になると、`O_APPEND` は各 syscall の EOF 選択しか原子化しないため、二つの append が成功・fsync 済みでも WAL は壊れる。
   - 根拠: 現行の path 判定と別 syscall は [wal.py:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:109)。特に `new_file = not exists` も [wal.py:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:115) で競合する。
   - 最小修正案: 上記 per-WAL lock 下で同じ fd を `pread`/`fstat` して gate し、そのまま write loop と fsync を完了する。新規作成判定は `O_CREAT|O_EXCL` で得る。強制 short-write を二 writer で交差させるテストを追加する。

4. `[severity high] / 対象: brief P3・P6、プラン consumer 配線`

   - 壊れ方: identity admission が不十分である。`loop`、screening、S-1 は lock 不在なら、既存 WAL bytes があっても新しい lock を作る。その後 repair すれば、identity 不明の WAL を現在 campaign のものとして破壊・採用する。さらに `record_diff_reject()` は cfg/preimage を受けず、S6/S8a/P3 の reject 経路では `run_campaign()` の照合前に呼ばれる。プランどおり helper 冒頭で repair すると mismatch 検査不能のまま truncate する。
   - 根拠: [loop.py:59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:59)、[screening_driver.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/screening_driver.py:60)、[s1_direct_comparison.py:232](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:232)、[p3_s4_loop.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop.py:213)、[s6_sort_sweep.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s6_sort_sweep.py:306)
   - 最小修正案: 「lock 不在かつ WAL byte あり」は自動 lock 作成せず拒否する。repair には照合済み identity/profile capability を要求し、context-free helper 内からは呼ばない。lock missing、mismatch、最初の候補が reject の三ケースで bytes 不変を固定する。

5. `[severity high] / 対象: brief P2、不変条件 fail-closed、プラン reader 節`

   - 壊れ方: `read_records()` は今後も `truncated_tail` を捨てる。完走済み S-1 WAL の後ろに完全 JSON 無改行または multibyte tail を置くと、dry-run は「schedule照合済み」で成功し、`s1_report` は schedule gate を pass にできる。プランが strict 化するのは `iter_lines()` consumer と s8b collected readerだけで、この false-green は残る。
   - 根拠: [wal.py:198](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:198)、[s1_direct_comparison.py:243](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:243)、[s1_direct_comparison.py:609](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:609)、[s1_report.py:329](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:329)
   - 最小修正案: anomaly を捨てる API を `read_records_prefix_for_recovery()` のように明示隔離する。report、dry-run、critic は checked/collected 結果を必ず消費し、tail を構造化 refusal にする。

6. `[severity medium] / 対象: brief P3、プラン repair 対象判定`

   - 壊れ方: `bad-terminated-frame\n` の後に unframed tail がある場合、repair は tail を削るが、prefix の framed corruption により resume は依然失敗する。回復不能なのに証拠だけ破壊する。また destructive open に `O_NOFOLLOW`・regular-file/inode 検査が明記されていないため、`wal.jsonl` が symlink/hardlink なら別ファイルを truncate し得る。
   - 根拠: 終端済み異常を伝播する契約は [wal.py:176](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:176)。repo 内の別 durable-open は既に `O_NOFOLLOW` を必須にしている [layout.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/layout.py:130) が、現 WAL open は raw path [wal.py:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:117)。
   - 最小修正案: lock 下で framed prefix 全体を profile-aware に検証し、別異常が一つでもあれば無変更拒否する。`O_NOFOLLOW|O_CLOEXEC`、`fstat` regular-file、same-fd scan/truncate を必須化する。invalid-prefix+tail、symlink、chunk 境界のテストを追加する。

7. `[severity medium] / 対象: brief P3、不変条件「診断は構造化」、プラン返却 dataclass`

   - 壊れ方: `removed_bytes` を返すだけでは「なぜ壊れたか」を保持しない。特に旧 short-write writer が完全な abort JSON まで fsync し LF だけ欠いた状態では、repair は correctness-red の全内容を消す。`ftruncate`/fsync 後、返却または caller の出力前に crash すれば、次回は no-op となり repair が起きた事実すら失われる。
   - 根拠: 規律3は理由の構造化を要求する [CLAUDE.md:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/CLAUDE.md:71)。現 collected 診断も `(line, string)` に縮退している [wal.py:145](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:145)。
   - 最小修正案: cut offset、inode、original/final size、tail SHA-256、分類、bounded preview を持つ durable repair intent/receipt を truncate 前に fsync し、再入時に完了状態を判定する。各 caller が結果を構造化出力することもテストで固定する。

8. `[severity medium] / 対象: brief P4、設計判断4`

   - 壊れ方: exact `str` は lone surrogate を含み得る。`{"x":"\ud800"}` は深部型検査を通り、`json.dumps(..., ensure_ascii=False)` 後の UTF-8 encode で失敗する。encode が現状どおり open 後なら空 WAL を作る副作用も残る。raw JSON の escaped lone surrogateは reader が受け、writer が再生成できないため受理集合が閉じていない。
   - 根拠: [wal.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:85)、encode が filesystem open 後にある [wal.py:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:117)
   - 最小修正案: frame bytes を全検証・UTF-8 encode してから filesystem に触る。lone surrogate を path 付き型例外で拒否するか、serialization 方針を明示変更する。`allow_nan=False` も typed record validation 後に置き、generic `ValueError` へ診断を後退させない。

9. `[severity medium] / 対象: プラン short-write テスト・consumer 例外境界`

   - 壊れ方: first write が `k>0` を書き、second write が例外または 0 を返すケースがない。partial tail が残ると、`run_campaign()` は evaluate 例外を捕まえて同じ WAL に abort を書こうとし、末尾 gate の二次例外が元の write failure を覆う。fsync 失敗の場合は「frame は存在するが durability 不明」で、blind retry は duplicate を作り得る。
   - 根拠: [wal.py:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:119)、[loop.py:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:124)、[screening_driver.py:143](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/screening_driver.py:143)
   - 最小修正案: `WalAppendError(path,total,written,phase,durability,cause)` を設け、WAL I/O failure を捕捉した caller は同じ WALへ診断追記しない。partial→error、full-frame→fsync error、repair再入をテストする。

10. `[severity low] / 対象: brief P4、設計判断4の exact subclass 拒否`

    - 壊れ方: `collections.OrderedDict({"x":1})` や副作用のない `dict` subclass は現在 canonical JSON を書け、reader も受理するが、新 exact-class rule は拒否する。実 WAL を再parseしても元が dict、OrderedDict、tuple のどれだったかは既に消えているため、3,086 record の scan は writer 互換性の証拠にならない。
    - 根拠: 現 writer は JSON encoder に委ねる [wal.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:85)、公開入口の注釈は exact type を要求していない [wal.py:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:133)
    - 最小修正案: tuple/non-str key/nonfinite の「黙変換拒否」と subclass 全拒否を別裁定にする。exactness を維持するなら breaking contract と明記し、producer inventory と互換テストを追加する。cycle validator は global visited ではなく active recursion stack を使い、共有 DAG (`x=[]; {"a":x,"b":x}`) を誤拒否しないテストも要る。

11. `[severity medium] / 対象: プラン「赤くなるテスト」「変異登録候補」`

    - 壊れ方: matrix はまだ F28 条件を満たさない。M02 は受理集合変異ではなく decode 順序による liveness/診断変異で、しかも「一箇所」が実装前には特定されていない。M04/M05/M10 も repair/durability/wiring であり acceptance kill と同じ母数にできない。M06 の一テストで parse と writer の双方を検査すると、先に落ちた assert しか実証しない。さらに最重要の per-WAL lock、foreign-known-stage profile、missing identity、S-1 tail false-green に対応する mutant がない。
    - 根拠: F28 は「手前の同一検査なし」「一理由」をコードで確定してから登録するよう要求する [docs/failures.md:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:343)。
    - 最小修正案: 単位A実装後の exact source location で再登録し、acceptance、durability、diagnostic、wiring を別集計にする。parse/writer は独立テストへ分割し、lock除去・profile除去・identity照合除去・tail flag無視の mutant を追加する。

pytest は依頼どおり実行していない。以上の high 所見、とりわけ stage profile、repair/append 排他、identity-before-repair、silent reader が未解決なので、判定は **NO-GO**。

---

## 段 3: 敵対相談 Y — 整合・実効性レンズ (max、逐語。判定 NO-GO)

結論は **NO-GO** です。静的読解だけで、T-004/T-007 が全 production consumer に効かない経路、repair による identity 照合前の破壊、並行 writer で元の融合破損が再発する経路が残っています。

## 所見

1. **[severity high] / 対象: brief P1・P2・P6、プラン「consumer 配線」**

   - 壊れ方: `s1_known_axes_freeze.py` は generic WAL を共有 parser 経由で読まず、`read_text().splitlines()` → `json.loads()` しています。したがって、完全な5-key `commit` JSONを末尾改行なしで置くと、P2では `truncated_tail` であるべき record が通常 record として argmax 計算に入ります。未知 stage は拒否されず単に無視され、duplicate key は後勝ち、multibyte tail は未捕捉の `UnicodeDecodeError` になります。
   - 根拠: [_wal_records()](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:128)、[_commit_rows()](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:170)。
   - さらに、この reader 自身の bytes は freeze の generator hash に束縛され、変更すると既存 freeze の検証が落ちます: [generator hash 検査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:713)、[D68 (7)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2616)。
   - 最小修正案: 現 wave では解消不能です。「T-004/T-007 は共有 `wal.py` 利用 consumer に限定する」という明示的な裁定変更を得るか、freeze 再発行を許可した別 wave に `s1_known_axes_freeze.py` の共有 reader 収束を移してください。現在の「generic WAL 全体」と「凍結成果物に触れない」は両立しません。

2. **[severity high] / 対象: brief P2・fail-closed 不変条件、プラン「既存 reader API の戻り値形を維持」**

   - 壊れ方: `read_records_checked()` が新たに「完全JSON無改行」「multibyte tail」を `truncated_tail=True` にしても、`read_records()` はその bool を捨てます。正常 prefix＋無改行の新しい高性能COMMITを読むと、`s1_report`、critic、P2 report 等は異常を一切出さず古い prefix から結果を生成します。multibyte tail は現状の crash から、黙った prefix 採用へ変わります。
   - 根拠: bool を捨てる [wal.py:198-201](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:198)。実 consumer は [s1_report.py:359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:359)、[critic/digest.py:201](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/critic/digest.py:201)、[p2_2_report.py:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p2_2_report.py:65) 等です。
   - 最小修正案: resume writer は identity 照合後に repair してから読む、read-only report/digest は checked API を使い `truncated_tail` を明示エラーまたは protocol reason にする、と用途別に移行してください。bool を捨てる API を未移行の production reader に残したまま「黙殺経路を増やさない」は成立しません。

3. **[severity high] / 対象: brief P3、プラン「append 末尾 gate」「short-write 完遂 loop」**

   - 壊れ方: 末尾検査と追記が排他区間にありません。

     具体的には、AとBがともに改行終端を確認後、Bが record の前半だけ short-write、Aが全recordを追記、Bが後半を追記すると、`B前半 + A全体 + B後半` に交錯します。別順序では、Aの末尾検査後にBが断片を残して停止し、Aが断片へ直結します。元の T-004 融合破損が再発します。repair が稼働中 writer の断片を truncate する競合もあります。
   - 根拠: 現 append は [wal.py:109-120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:109)。通常の `campaign.lock` は identity ファイルで、排他ロックではありません: [loop.py:57-63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:57)、[wal.py:254-266](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:254)。
   - 最小修正案: append と repair が共通に取得する `flock(LOCK_EX)` を設け、同じ fd 上で `lock → fstat/pread末尾検査 → 全byte write → fsync → unlock` を行ってください。制御した二 writer の交錯テストも必要です。

4. **[severity high] / 対象: brief P3・P6、プラン「`record_diff_reject()` 冒頭で repair」**

   - 壊れ方: `record_diff_reject()` は `CampaignConfig` を受けず、identity 照合を一切できません。別 campaign の `campaign.lock` と unframed tail がある layout を渡すと、プランどおりなら不一致を検出する前に tail を物理削除し、そのまま reject record を書きます。
   - 根拠: helper は layout しか受けない [p3_s4_loop.py:213-227](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop.py:213)。base 経路も `layout.ensure()` 後すぐ reject へ行き、`run_campaign()` の identity gate を通りません: [p3_s4_loop.py:617-648](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop.py:617)。
   - consumer 列挙も不完全です。同じ helper は plan が挙げた base/sort/trigger だけでなく [s6_sort_sweep.py:311](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s6_sort_sweep.py:311) と [s8a_trigger_sweep.py:357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8a_trigger_sweep.py:357) からも呼ばれます。つまり未列挙の二経路にも identity 前 truncate が波及します。
   - 最小修正案: `cfg + layout` を受けて identity 照合済み token を返す共通 resume preflight を作り、その token なしでは repair/reject append できない契約にしてください。5 caller 全部に lock-mismatch＋tail 不変テストが必要です。

5. **[severity medium] / 対象: brief P3・P6、プラン `guided.py` 行**

   - 壊れ方: プランは `_read_meta()` 成功を repair 前の関所としていますが、これは JSON を読むだけです。trial X の directory に trial Y の正常な `meta.json` と tail 付き WALをコピーすると、`cmd_evaluate --trial X` は meta の `trial` 不一致を検査せず tail を削り、Y の workload で X の WALへ追記します。
   - 根拠: `_read_meta()` は無検査 [guided.py:62-64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/guided.py:62)、`cmd_evaluate()` も `meta["trial"] == args.trial` を確認しません: [guided.py:129-153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/guided.py:129)。
   - 最小修正案: meta の exact schema・trial・workloadを検査し、現在の引数と一致した後だけ repair してください。可能なら immutable identity preimage を導入してください。

6. **[severity high] / 対象: brief P5、プラン「単位A先行→B」**

   - 壊れ方: Aは独立完了できません。

     - Aの新規 `test_campaign.py` 一覧に「loop resume が repair」を入れていますが、`loop.py` はB所有です。A終了時点では [loop.py:57-68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:57) に repair がなく、そのテストは通りません。
     - Aで `parse_line()` に stage gateを入れると、未知 stage の拒否位置と文言が変わり、Bで直す予定の既存 [test_layer3_report.py:140-143](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_layer3_report.py:140) がA直後から赤になります。

   - 最小修正案: loop integration test と layer3期待変更をBへ移し、Aは「full-suite 緑ではない中間commit」と明記するか、最低限の consumer shimをAへ含めてください。「Aを先行完了」は現行分割では偽です。

7. **[severity medium] / 対象: brief P4、プラン parse_constant 契約**

   - 壊れ方: `parse_constant` callback が通常の `ValueError` を投げる実装だと、collected reader の捕捉外です。correctness-red の後に改行終端済み `NaN` record があると、s8b report は valid prefix の評価をせず、全行を単一の「WALを読めない」へ潰します。
   - 根拠: collected reader は現在 `JSONDecodeError` と `WalLineError` だけを行単位捕捉します: [wal.py:159-172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:159)。s8b の外側 catch は全評価を早期 return します: [s8b_oracle_report.py:937-954](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:937)。既存テストも NaN を `WalLineError` として要求します: [test_campaign.py:388-400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_campaign.py:388)。
   - 最小修正案: callback は必ず `WalPayloadTypeError(WalLineError)` を投げる、とAのAPI契約に明記してください。decodeも collected reader の行単位 `try` 内で実行する必要があります。

8. **[severity medium] / 対象: brief P4、プラン writer preflight**

   - 壊れ方: exact `str` 検査だけでは UTF-8 書込み可能性を保証しません。payloadまたはvariantに lone surrogate `"\ud800"` を入れると、`json.dumps(..., ensure_ascii=False)` は文字列を作れても `.encode("utf-8")` が失敗します。現コードの順序ではファイルを open/create した後なので、preflight 違反入力が空WALを残せます。
   - 根拠: serializer [wal.py:85-88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:85)、encode は open 後 [wal.py:111-120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:111)。
   - 最小修正案: 完成した line を UTF-8 bytesへ変換するところまでを mkdir/open 前に行うか、`ensure_ascii=True`、または surrogate を validator で構造化拒否してください。新規WALが作られないテストも必要です。

9. **[severity medium] / 対象: brief P3、プラン consumer 配線**

   - 壊れ方: `WalTailRepairResult` を返しても、各変更表は単に repair を呼ぶだけで、返却値を log・summary・上位結果へ伝える契約がありません。tailを32 byte削って正常再開した実行と、修復不要だった実行が外部から同じ成功に見えます。
   - 根拠: loopには構造化 repair result の受け皿がなく、現 summary/log 経路は [loop.py:64-84](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:64)。他 consumer の変更表にも返却値処理がありません。
   - 最小修正案: 全 caller が結果を捕捉し、`status != no-op` を構造化 callback・summary・明示診断のいずれかへ必ず伝える契約とテストを追加してください。

10. **[severity medium] / 対象: プラン「親の変異matrix実測」**

   - 壊れ方: matrix実行の排他・復元・timeoutが未定義です。旧ハーネスが残った状態で次の matrix が始まれば、別変異を同時に production sourceへ当て、誤ったkill帰属または残留変異を作れます。
   - 根拠: この失敗と必須対策は [F32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:400) に既出です。現repoにはこのwave用の永続 mutation harness もありません。
   - 最小修正案: 単一走行 `flock`、変更前bytesとの内容比較による復元確認、各変異timeout、異常終了時の復元を受入手順へ事前登録してください。

## production WAL 経路の再列挙

追記経路は次です。

- `pipeline.evaluate()` 内: [pipeline.py:354](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/pipeline.py:354) ほか。production caller は loop、screening、S-1、s8b の4系統です。
- pipeline外の直接 writer: [loop.py:108](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/loop.py:108)、[screening_driver.py:152](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/screening_driver.py:152)、[guided.py:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/guided.py:81)、[p3_s4_loop.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop.py:221)、[s1_direct_comparison.py:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:259)、[s8b_oracle_driver.py:445](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:445)。
- productionからの直接 `wal.append()` 呼出しはありません。
- P3 reject helper の caller は base、sort、trigger、s6、s8a の5系統です。プランの列挙は後二つを落としています。

共有APIの読者は loop、screening、guided、backoff sweep/repro、P3 base/sort/trigger、s6、s8a、S-1 driver/report、s8b driver/report、`replay.py`、`p2_2_report.py`、`critic/digest.py`、layer3、plottingです。加えて `records_by_stage()` 経由で p3 kickoff/red も読みます。

共有APIを迂回する実質的な production reader は前述の `s1_known_axes_freeze.py` です。`s8b_floor_campaign` と prediction runner の journal は別フォーマットであり、generic campaign WALには数えていません。

## 変異10件の実効性監査

| ID | 前段で同じ入力を落とす検査 | 判定 |
|---|---|---|
| M01 | なし | 有効。完全JSON無改行が受理へ戻る |
| M02 | なし | 意味上は有効。ただし「decodeを前へ移す」は単一の exact diff が未定義で、現状は事前登録として曖昧 |
| M03 | なし | 有効。直接append fixtureなら bytes 変更で落ちる |
| M04 | なし | 有効。ただし direct truncate assert と後段append gateの二重検出にしないよう、kill理由を一つへ固定すべき |
| M05 | なし | 有効。mockが実際に部分byteだけ書くという条件も適切 |
| M06 | なし | 有効。writerも共有preflight経由で受理集合が開く |
| M07 | なし | 有効。`json.dumps` が int key を文字列化する |
| M08 | なし | 有効。serializerが tuple を配列化する |
| M09 | なし | 有効。`1e999` は `parse_constant` を通らず `inf` になる |
| M10 | `_ensure_campaign_lock` はtailを拒否しない | 条件付き有効。candidate入口の直前、特にprepare完了後にtailを再注入しない fixtureなら、prepare側repairに食われて等価変異になる |

`parse_constant` 削除をkill件数から外した判断は必要です。深部有限性検査が同じ NaN を拒否するため、受理集合は変わらず診断pinにしかなりません。ただし10件すべてがkillされても、上記の並行writer、identity前repair、raw frozen reader、silent `read_records()` は検査されません。

## その他の照合

- `model.py` は標準ライブラリしかimportしていないため、session定数と `WAL_STAGES` を置くこと自体に import循環はありません: [model.py:14-17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/model.py:14)。
- T-003、T-060、s8bの `wal_bytes_present()` 拒否に反する追加は見つかりません。[s8b拒否位置](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:818) は維持されています。
- shared parser内の exact-5-key、duplicate-key、`WalLineError` 非継承、terminal位置 gateを直接壊す変更案はありません。ただし raw frozen reader がそれらを迂回したままです。
- 既存テスト影響一覧は、少なくとも `parse_constant` の例外型とA/B境界を確定するまで完全ではありません。

**最終判定: NO-GO**

再判定には、少なくとも frozen raw reader のscope裁定、WAL単位の排他、identity-aware repair、silent reader移行、A/B境界の再分割が必要です。
# [T-004] 段 4 親裁定 — プラン v2 (2026-07-22)

X/Y 両相談 NO-GO。全 21 所見を裁定する。確定ユーザー裁定 (T-004/T-007/T-008) は不変。

## 所見の裁定

| # | 所見 | 判定 | 採否 / scope |
|---|------|------|--------------|
| X1 | 白名簿の「既知」vs「campaign 許可」混同 (cross-campaign 注入 inert) | real | **部分採用**: global 白名簿 (T-007 どおり) + s8b report に inert-record 拒否 (session でも pipeline でもない record → protocol violation、A3-b の DFA 拡張)。campaign 種別 profile (writer/read への allowed_stages 必須化) は **scope 外 → 裁定パッケージ U-B1** |
| X2/X3/Y3 | repair/append の排他なし、TOCTOU、交錯 short-write | real | **採用**: WAL fd 上の flock(LOCK_EX) で「末尾検査→write loop→fsync」を排他。append は O_RDWR\|O_APPEND\|O_CREAT\|O_NOFOLLOW\|O_CLOEXEC + fstat regular 検査。reader の shared lock は**不採用** (prefix 容認 reader の意味論は現状維持、scope 外) |
| X4/Y4 | identity 照合前の repair 禁止、lock 不在+WAL bytes = 拒否、reject helper 5 caller | real | **採用**: repair は照合済み identity の後のみ。`ident.ensure_resumable_wal(cfg, layout)` を新設 (lock 不在+bytes あり→fail-closed 拒否 / 照合→repair→receipt 返却)。`record_diff_reject` では **repair しない** — 未修復 tail は append 末尾 gate が構造化拒否 (5 caller 全系統でテスト固定) |
| Y5 | guided の meta 無検査 repair | real | **採用**: `cmd_evaluate` は meta の trial 一致検査後のみ preflight |
| X5/Y2 | read_records() の黙殺 (production 約 30 caller) | real | **部分採用**: s1_report.py:359 と s1_direct_comparison.py:246/544 を checked 化し truncated_tail を構造化拒否へ。layer3/plot はプラン通り strict iter_lines。**残り caller (critic digest / p2_2_report / backoff_repro / replay.py / p3 系ほか) は recovery・exploration の prefix 容認 reader と docstring 明記し、全面移行は裁定パッケージ U-B2** |
| Y1 | s1_known_axes_freeze.py の raw WAL reader (freeze pin 下で本 wave は触れない) | real | **既知事実** (D68 (7) が撤回済みと記録、収束は S-1 系再裁定 [T-005] の守備範囲)。wave は止めず、**D77 に「本 wave の射程 = 共有 wal.py 利用 consumer」と明文化**。新規裁定は不要 |
| X6 | repair の symlink/inode、prefix 検証 | real | **部分採用**: O_NOFOLLOW\|O_CLOEXEC + fstat regular + same-fd scan/truncate。prefix 全検証は**不採用** — 証拠保全は receipt (X7) が担い、framed 破損は reader が fail-closed |
| X7/Y9 | repair receipt の耐久化と caller 表出 | real | **採用 (軽量形)**: truncate **前**に receipt JSON (cut offset / removed bytes / sha256 / bounded preview / 新旧 size) を runs_dir へ書き fsync。resume caller は非 no-op を log/summary へ必ず表出 (テスト固定)。完全な intent/再入機構は不採用 |
| X8/Y8 | lone surrogate、encode が open 後 | real | **採用**: validator で surrogate を構造化拒否。検証 + UTF-8 encode を mkdir/open **前**に完了 (拒否時にファイル副作用ゼロ、テスト固定) |
| X9 | WalAppendError + WAL I/O 失敗後の同 WAL 診断追記禁止 | real | **採用**: `WalAppendError` (path/total/written/phase/cause)。loop/screening の catch-and-abort は WAL I/O 例外なら abort 追記を試みず伝播 |
| X10 | subclass 全拒否は breaking、cycle 検査は active stack | real | **採用**: isinstance ベース (OrderedDict 等 dict subclass 容認、IntEnum は int)。tuple/set/bytes/非 str key/非有限 float は拒否。cycle は active recursion stack (共有 DAG 容認、テスト) |
| Y6 | A/B 境界: A は独立完了できない | real | **採用**: loop resume 統合テストと layer3 期待変更は B へ。A 完了時の**期待赤集合を事前明示** (下記) |
| Y7 | parse_constant の例外型と collected の行単位 decode | real | **採用**: parse_constant は `WalPayloadTypeError(WalLineError)` を送出。collected reader は decode も行単位 try 内 |
| X11/Y10 | 変異 matrix の F28/F32 規律 | real | **採用**: 下記の事前登録 (candidate)。confirmed 化は実装 land 後に file:line で親が確認。集計 4 分離 + F32 ハーネス規律 |

## A→B API 契約 (exact — 契約不一致は恒真ゲートを生む型)

- `class WalFramingError(WalLineError)` — 無終端 tail に strict 経路で遭遇
- `class WalPayloadTypeError(WalLineError)` — writer 深部型違反 / parse_constant 拒否。属性 `path` (payload 内パス文字列、無ければ None)
- `class WalAppendError(RuntimeError)` — 属性 `wal_path, total_bytes, written_bytes, phase ("tail-gate"|"write"|"fsync"), cause`。JSONDecodeError/KeyError/WalLineError の subclass にしない
- `@dataclass(frozen=True) class WalTailRepairResult` — `status ("noop"|"repaired"|"missing"), original_size, final_size, removed_bytes, removed_sha256 (noop 時 None), preview (str, ≤256 byte 相当), receipt_path (noop 時 None)`
- `def repair_truncated_tail(layout) -> WalTailRepairResult` — identity 非関知の機構。flock 下で scan→receipt 書込 fsync→ftruncate→fsync。symlink/非 regular は拒否
- `model.STAGE_S1_SESSION = "s1-session"`, `model.STAGE_S8B_ORACLE_SESSION = "s8b-oracle-session"`, `model.WAL_STAGES = STAGES + 上記 2 種` (既存 `STAGES` は 6 種のまま)
- B 新設: `ident.ensure_resumable_wal(cfg, layout) -> WalTailRepairResult` (ident→wal import、循環なしを確認済み)

## 実装単位 (直列 A → 並列 B1/B2)

- **A**: `wal.py` + `model.py` + `test_campaign.py`。framing / repair / flock append gate / short-write /
  白名簿 / payload 深部型。full-suite 緑ではない中間状態と明記
- **B1** (A patch 展開後): `ident.py`, `loop.py`, `screening_driver.py`, `guided.py`,
  `s1_direct_comparison.py`, `test_guided.py`, `test_screening_driver.py`, `test_s1_direct_comparison.py`,
  `test_campaign.py` (A から所有移転 — loop resume 統合テスト)
- **B2** (A patch 展開後、B1 と素集合): `s1_report.py`, `s8b_oracle_report.py`, `s8b_oracle_driver.py`,
  `layer3_report.py`, `test_s1_report.py`, `test_s8b_oracle_report.py`, `test_s8b_oracle_driver.py`,
  `test_layer3_report.py`, `test_backoff_consumers.py`, `test_p3_s4_loop.py`, `test_s6_sort_sweep.py`,
  `test_s8a_trigger_sweep.py` (reject 5 系統の append-gate fail-closed テスト)

## A 完了時の期待赤集合 (これ以外の赤 = 回帰)

1. `test_layer3_report.py` unknown-stage 系 (拒否位置が parse_line へ前倒し、診断文言変化)
2. `test_s1_direct_comparison.py` の session 定数/未知 stage 系 (契約反転)
3. consumer テストのうち NaN・未知 stage・falsy payload (`[]`)・改行欠落 fixture を使うもの
   (A 実装後に親が全走して実測し、この 3 分類に帰属できることを確認する)

## 変異事前登録 (candidate — confirmed は land 後に file:line で親が確認、B-057/F28)

**acceptance 枠**: M01 (endswith(b"\n") 恒真化 → 改行欠落 JSON が record 復活)、M06 (stage 白名簿削除)、
M07 (非 str key 検査削除)、M08 (tuple 拒否削除)、M09 (decoded 深部有限性検査削除 → 1e999 受理)、
M13 (s8b inert-record 拒否削除 → 外来既知 stage が黙過)、M14 (s1_report torn-tail 拒否削除)
**durability 枠**: M03 (append 末尾 gate 削除 → bytes 融合)、M04 (ftruncate no-op 化 → repair 後 append 失敗。
kill 理由は「repair 後 append 成功」の 1 本に固定)、M05 (short-write loop → 単発 os.write)、
M11 (append の flock 除去 → 交錯テスト赤)、M12 (lock 不在+bytes 拒否の除去)
**diagnostic pin 枠 (kill 集計外)**: parse_constant 削除 (深部検査が受理集合を閉じたまま診断が後退)
**取り下げ**: M02 (単一 exact diff 不成立 — 設計ノートへ)、M10 (fixture が prepare 後 tail 再注入形に
できる場合のみ復活)

## scope 外 → 裁定パッケージ (実装しない、ユーザーへ返す)

- **U-B1**: campaign 種別 stage profile (writer/read/replay への allowed_stages 必須化と全 consumer 配線)
- **U-B2**: prefix 容認 reader 約 25 caller (critic digest / p2_2_report / replay.py / p3 系ほか) の用途別移行
- (参考) reader shared lock・repair の durable intent/再入機構・prefix 全検証は上記裁定で不採用と整理済み


---

## 段 5: 実装単位 A 完了報告 (codex high、逐語)

実装単位 A を完了しました。変更は所有 3 ファイルのみで、commit は作成していません。

変更一覧:

- [model.py:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-a/orchestrator/campaign/model.py:29)
  - session stage 2 定数と、正確に 8 種の `WAL_STAGES` を追加。既存 `STAGES` は 6 種を維持。
- [wal.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-a/orchestrator/campaign/wal.py:44)
  - 例外階層、byte framing、stage/payload 検査、strict/collected reader を実装。
  - flock、末尾 gate、short-write loop、構造化 `WalAppendError` を実装（主要箇所: 282）。
  - receipt-first、same-fd scan/truncate/fsync の `repair_truncated_tail()` を実装（418）。
- [test_campaign.py:426](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-a/orchestrator/tests/test_campaign.py:426)
  - v2 の期待値変更と、framing、repair receipt、排他、short write、stage、深部型、OrderedDict、共有 DAG、lone surrogate 等のテストを追加。
  - loop resume 統合テストは追加していません。

実行結果:

- `python3 -m pytest orchestrator/tests/test_campaign.py -q`
  - `142 passed, 9 skipped`
- `python3 orchestrator/tests/test_campaign.py`
  - `142 passed, 0 failed, 9 skipped`
- `python3 tools/check_codex_agents.py`
  - OK
- `python3 tools/check_docs.py`
  - 違反なし
- `git diff --check`
  - 問題なし

Full suite:

- `python3 tools/run_tests.py`
  - `4 failed, 2556 passed, 29 skipped`

赤の完全な一覧と帰属:

1. `test_layer3_report.py::test_unknown_stage_fails_closed`
   - 親の期待赤分類 1。拒否位置が shared `parse_line()` へ前倒しされ、英語診断へ変化。
2. `test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls@real-repo`
   - 期待赤集合外。sandbox が submodule の `.git/.../index.lock` を read-only にしており、fixture の `git checkout` 復元が失敗。
3. `test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null@real-repo`
4. `test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification@real-repo`
   - いずれも期待赤集合外。2 の復元失敗で同一 worker 上の submodule bytes が一時的に汚れたことによる cascade。
   - submodule を実行前 bytes に戻した後、この 2 件を単独実行して `2 passed` を確認。

最終状態では submodule は clean で、差分は指定された 3 ファイルだけです。

---

## 段 5: 実装単位 B1 完了報告 (codex high、逐語)

実装単位 B1 を完了しました。所有外の実装・docs・commit は変更していません。A の `wal.py` / `model.py` 差分はそのまま維持しています。

変更一覧:

- [ident.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/campaign/ident.py:106): `IdentityMismatch.reason` と `ensure_resumable_wal()`。lock 不在+bytes、lock mismatch は修復前に拒否。
- [loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/campaign/loop.py:59): replay 前 repair、receipt の構造化ログ、WAL 例外後の abort 追記禁止。
- [screening_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/campaign/screening_driver.py:59): prepare/evaluate 両入口の repair と構造化ログ、WAL 例外伝播。
- [guided.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/campaign/guided.py:74): exact meta/trial 検査、start 時の identity lock、evaluate 時の repair。
- [s1_direct_comparison.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/campaign/s1_direct_comparison.py:42): session stage re-export、checked reader 化、resume repair、dry-run 非破壊。
- [test_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/tests/test_campaign.py:295): lock 不在/mismatch 非破壊、loop resume、repair 表出、WAL 例外テスト。
- [test_screening_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/tests/test_screening_driver.py:108): screening 2 入口と abort 非追記テスト。
- [test_guided.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/tests/test_guided.py:208): commit+tail resume と meta 検査順テスト。
- [test_s1_direct_comparison.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b1/orchestrator/tests/test_s1_direct_comparison.py:440): stage 契約、resume、dry-run 非破壊テスト。

テスト結果:

- focused pytest: `190 passed, 9 skipped`
- `python3 orchestrator/tests/test_campaign.py`: `146 passed, 0 failed, 9 skipped`
- `python3 orchestrator/tests/test_guided.py`: `14 passed, 0 failed`
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: 問題なし

全 suite (`python3 tools/run_tests.py`):

- `2567 passed, 29 skipped, 5 failed`
- `test_layer3_report.py::test_unknown_stage_fails_closed`: B2 所有の期待文言未更新。
- `test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls@real-repo`: sandbox が submodule の `.git/index.lock` を作れず cleanup 失敗。
- s8b 2 件: 上記 p3 テストの並列汚染。submodule cleanup 後の単独再試験は `2 passed`。
- `test_dev_waves_integration.py::test_artifact_aggregate_cap_stops_before_next_wave_side_effect`: 一時ファイル `lstat` race。単独再試験は `1 passed`。

全 suite が残した submodule patch は復元済みで、最終 `external/ccbench` は clean です。

---

## 段 5: 実装単位 B2 完了報告 (codex high、逐語)

実装単位 B2 を完了しました。所有外の A patch・B1 ファイル・docs・git commit には触れていません。

変更点:

- [s1_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/campaign/s1_report.py:174): S1 stage を model 定数化。[checked reader と構造化 tail refusal](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/campaign/s1_report.py:359)を追加。
- [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/campaign/s8b_oracle_report.py:33): session 定数を re-export。[inert-record 拒否](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/campaign/s8b_oracle_report.py:316)を追加。
- [s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/campaign/s8b_oracle_driver.py:52): session 定数を re-export。resume 拒否は不変。
- [layer3_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/campaign/layer3_report.py:102): `WalFramingError` を cause 付き `Layer3ReportError` へ翻訳。
- S1、8b anti-masking、layer3、plot_backoff の framing テストを追加。
- [P3 base/sort/trigger](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/tests/test_p3_s4_loop.py:150)、[S6](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/tests/test_s6_sort_sweep.py:203)、[S8a](/home/SFC/tanab/github/izanagi/.claude/worktrees/t004-unit-b2/orchestrator/tests/test_s8a_trigger_sweep.py:170)の reject append-gate を固定。拒否時の WAL bytes 不変・repair receipt 不在を検査。

検証:

- B2 focused pytest: `352 passed, 2 skipped`
- `python3 tools/run_tests.py`: `2572 passed, 29 skipped, 3 failed`
- 連鎖した8b 2件の単独再試験: `2 passed`
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: OK
- submodule: clean

Full-suite 赤の完全一覧:

1. `test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls`  
   sandbox が submodule の `index.lock` を作れず、patchharness の巻き戻しが失敗。
2. `test_real_freeze_gate_lists_floor_and_budget_null`  
   1 の未巻き戻し bytes による連鎖赤。復旧後は PASS。
3. `test_tampered_freeze_fails_source_verification`  
   同じ連鎖赤。復旧後は PASS。

submodule は inverse patch で完全に clean へ復旧済みです。B1 帰属の赤はありません。補助的な素の `test_p3_s4_loop.py` は新規テストを含む15件通過後、既存runnerが `pytest.skip`を捕捉せず exit 1 になりました。

---

## 段 5: 親統合の継ぎ目修正 (親直書き)

統合全走 1 巡目の唯一の赤 = s1_report の理由帰属 (B1 の ScheduleDeviation が B2 の特定 reason を
先取りする過剰決定)。親が `_TruncatedWalTail` sentinel で特定 reason へ写像する修正を直書きした。
この親 hunk は段 6 レビューで名指し対象とし、R1/R2 双方から real 所見 (framing-only でない /
prefix 証拠の喪失) を受けて fix で再設計された (最終形は F-H)。

---

## 段 6: 敵対レビュー R1 — 正しさ境界・fail-closed (max、逐語。判定 NO-GO)

重大な fail-closed 違反が複数ある。

## 所見

- [high] / `orchestrator/campaign/ident.py:137-152`, `orchestrator/campaign/wal.py:582-621` / lock 作成が非原子的かつ非耐久。32-bit campaign-id collision を持つ cfg A/B を同時起動すると、双方が lock 不在・WAL 空を通過し、`open("w")` の上書き順次第で双方が自己 preimage を読んで検証成功し、同じ WAL へ混在追記できる。単独起動でも lock を fsync せず WAL だけ fsync した後の電源断で「WAL あり・lock 消失」となり、次回は永久拒否される / `acquire_lock_atomic` 相当を short-write 検査込みで堅牢化し、file と親 directory の fsync 後にのみ identity 確定とする。競合 loser は既存 lock を再読して照合する。

- [high] / `orchestrator/campaign/wal.py:625-635`, `orchestrator/campaign/ident.py:139`, `orchestrator/campaign/s8b_oracle_driver.py:818-823` / `wal_bytes_present()` は `ENOENT` 以外の全 `OSError` も「byte 無し」に変換する。既存の改行終端済み WAL に対する `getsize()` が一度だけ EIO になれば、generic resume は新 lock を作って旧 record を別 identity として採用し、s8b は resume 拒否を抜けて campaign-start を既存 WAL へ追記する / `FileNotFoundError` だけを False とし、EIO・権限・symlink・非 regular は構造化拒否へ送る。同 fault-injection を s8b の V5 に追加する。

- [high] / `orchestrator/campaign/p3_s4_loop.py:625-648`, `p3_s4_loop_sort.py:239-249`, `p3_s4_loop_trigger_gating.py:395-405` / fresh campaign の最初の proposal が diff-quarantine reject だと、`record_diff_reject()` が lock 作成前に framed WAL を書く。次の正常 proposal は `ensure_resumable_wal()` の `missing-lock-with-wal-bytes` で停止し、campaign が自分で再開不能になる。非 screening の s6/s8a にも同型がある / repair を伴わない identity-only preflight を全 5 caller の最初の WAL write 前に置く。既存 tail の reject 経路は裁定どおり append gate で拒否し、評価へ進む経路だけ repair する。

- [high] / `orchestrator/campaign/wal.py:333-348`, `loop.py:136-143`, `screening_driver.py:155-161`, `s1_direct_comparison.py:746-777`, `s8b_oracle_driver.py:1145-1204` / `WalAppendError` が end-to-end で保全されない。主 fd の `os.close()` エラーは raw `OSError` のままなので loop/screening は同じ WAL へ abort を試みる。また S-1 と s8b は正規の `WalAppendError` まで広い `except Exception` で retry/偽 EvalResult に変換し、session-result・deviation・terminal を同じ WAL へ続けて書く。partial write なら二次 tail-gate が元例外を隠し、fsync failure なら耐久性不明の台帳を継続する / close を含む全 append I/O を `WalAppendError` に写像し、全 consumer で同型を即再送出して以後の WAL write を禁止する。

- [high] / `orchestrator/campaign/wal.py:298-348` / 新規 file の directory fsync が flock 解放後。writer A が file fsync・close した直後に停止し、writer B が同 inode を追記して `new_file=False` で返り、その後 A が directory fsync 前に死亡すると、B は成功を返したのに directory entry は未耐久のままになる / directory fsync まで排他区間に含める。失敗した creator の後続 writerも保証できるよう、少なくとも全 append で runs directory を fsync してから lock を解放する。

- [high] / `orchestrator/campaign/wal.py:290-305,379-455`, `orchestrator/campaign/layout.py:197-200` / `O_NOFOLLOW` は最終 component しか守らない。campaign A の `runs` を campaign B の `runs` への symlink にすると、A の lock を照合した後で B の WAL を truncateし、receipt と A の record も B へ書く。WAL 自体の hardlink も regular-file 検査を通る / symlink-free に検証した directory fd から `openat` で WAL/receipt を開き、必要なら `st_nlink == 1` も要求する。path 文字列から再 open しない。

- [medium] / `orchestrator/campaign/wal.py:351-362,439-443` / repair は除去 tail 全体を `chunks` と `b"".join()` に保持する。改行のない巨大・sparse WAL では receipt 前に OOM し、構造化結果も証拠も残らない / SHA-256 を chunk 単位で更新し、preview の先頭128 byteだけ保持する。binary reader の巨大無終端 frame も同じ上限方針にする。

- [medium] / 親直書き `orchestrator/campaign/s1_report.py:344-408` / try 先頭は framing-only 検査ではなく full parser。`valid\n` + 終端済み不正 JSON + 無終端 tail を与えると、先行 JSON 例外で走査が止まり、`schedule_ledger_invalid` だけになって `wal_truncated_tail` を失う。「終端済み破損を下流へ流す」というコメントとも実経路が一致しない / byte framing と record parse を分けるか collected reader で両 anomaly を保持し、reason の優先順位または併記を固定する。なお `_TruncatedWalTail` が generic `Exception` より先なのは正しい。

- [medium] / `orchestrator/campaign/s1_report.py:347-351`, `orchestrator/tests/test_s1_report.py:261-282` / M14 は acceptance kill ではない。親の tail 分岐だけを削除しても直後の `read_session_ledger()` と `validate_session_ledger()` が同じ tail を再拒否し、変わるのは reason だけ。さらに fixture 自体が `deviation` event なので、framing を受理しても独立条件で schedule が落ちる / M14 を diagnostic pin 枠へ移す。acceptance fixture は既存の正常な最終 frame から改行だけを落とし、変異対象も実効な共通 framing gate に置く。

- [medium] / `test_p3_s4_loop.py:150-174`, `test_s6_sort_sweep.py:203-224`, `test_s8a_trigger_sweep.py:170-195` / 「5 caller」テストは全件が同じ `L.record_diff_reject()` を直接呼ぶだけ。sort/trigger の production caller は一度も呼ばれず、S6/S8a の public sweep は実際には `WalAppendError` を `driver-error` 文字列へ潰して続行するため、この差を検出できない / 各 public caller を quarantine-failure 注入で通し、例外 object の伝播、byte 不変、receipt 不作成を固定する。

- [medium] / `orchestrator/tests/test_campaign.py:498-506,775-795`, `orchestrator/campaign/wal.py:147-157` / M07「non-str key 検査削除」も acceptance mutation にならない。検査だけ消すと `_validate_string(int)` の `TypeError` で依然拒否される。主 fixture `{1:..., "1":...}` は coercion 後 duplicate という独立拒否も持つ / 単独 `{1: "int"}` を使い、non-str key が実際に serialize/parse を通る変異へ再定義する。現候補の kill は診断後退であって受理集合変更に数えない。

- [low] / `test_s1_direct_comparison.py:440-443`, `test_s8b_oracle_driver.py:1900-1901`, `test_s8b_oracle_report.py:413-416` / shared stage authority の `==` assert は current literal への再直書きでも通るため恒真。T-007 の「model から import」を固定していない / model 定数を変更して module reload する検査、または AST/import 検査で reliteralization を殺す。

通常の regular-file 入力では duplicate-key、exact-5-key、terminal 位置、未知 stage、s8b inert-record の拒否は維持されている。`WalTailRepairResult` も主要 resume caller で表出されている。しかし上記の identity・durability・caller 境界が残るため受入不可。

pytest は指示どおり未実行。`git diff --check` のみ clean を確認。

**NO-GO**

---

## 段 6: 敵対レビュー R2 — 回帰・情報保存・網羅 (max、逐語。判定 NO-GO)

結論は **NO-GO**。実装上の blocker 4 件、耐障害性 2 件、変異台帳の誤帰属 2 件を確認した。

## 所見

1. **[high] / 対象:** [p3_s4_loop.py:633](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop.py:633)、[p3_s4_loop_sort.py:140](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop_sort.py:140)、[p3_s4_loop_trigger_gating.py:285](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop_trigger_gating.py:285)、[s6_sort_sweep.py:311](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s6_sort_sweep.py:311)、[s8a_trigger_sweep.py:357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8a_trigger_sweep.py:357)、[ident.py:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/ident.py:137) / **壊れ方:** 新規 campaign の最初の候補が quarantine/auditor reject になると、`record_diff_reject()` が `BUILD_START→ABORT` を書く一方、`campaign.lock` はまだ無い。次の候補が通過して `run_campaign()` に到達すると、`ensure_resumable_wal()` が「lock 無し・WAL bytes あり」で `IdentityMismatch` を出す。5 系統すべてが一度の正常な reject で自己封鎖される。`--no-build` の dry reject でも後の実走を毒せる。追加テストは既に壊れた tail への append 拒否しか見ておらず、この fresh reject→次回 resume を通していない。 / **最小修正案:** repair を伴わない identity-only preflight を新設し、5 系統とも最初の reject 可能点より前で lock 作成/照合する。既存 tail は修復せず append gate で拒否する。

2. **[high] / 対象:** [s1_direct_comparison.py:746](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:746)、[s8b_oracle_driver.py:1147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1147)、[s8b_oracle_driver.py:1199](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1199)、[s6_sort_sweep.py:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s6_sort_sweep.py:259)、[s8a_trigger_sweep.py:304](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8a_trigger_sweep.py:304) / **壊れ方:** `os.write()` が一部を書いてから EIO になった場合、S-1 は `WalAppendError` を retryable に変換し、直後に `session-result` を同じ WAL へ追記して tail-gate の二次例外で元例外を覆う。s8b も evaluate 例外へ畳み、prefix reader で partial tail を捨てた後、`deviation` または `trial-result` を同じ WAL へ書く。fsync 失敗なら full frame が残り得るため、診断追記と再試行が重複記録を作る。さらに s6/s8a は loop/screening が正しく再送出した例外を `driver-error` に変換して次候補へ進み、自動 repair 後に同じ WAL へ再追記する。 / **最小修正案:** 全 broad catch の先頭で `WalAppendError` と同一 WAL 由来の `WalFramingError` をそのまま再送出する。s6/s8a は sweep 全体を停止する。partial→EIO と full-frame→fsync EIO の実注入テストを各上位入口に置く。

3. **[high] / 対象:** 親直書き [s1_report.py:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:347)、[s1_report.py:397](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:397)、[test_s1_report.py:261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_report.py:261) / **壊れ方:** 有効な全 session prefix の後に 1 byte の無終端 tail があるだけで `_TruncatedWalTail` が先頭から脱出し、`expected_sessions=None`、開始数未算出、samples/retries/budget refusals 空、commit 集計ゼロになる。B2 元設計は [integrated_snapshot.patch:379](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t004-wal-wave/integrated_snapshot.patch:379) の後段 inline 検査で、tail を理由に追加しつつ durable prefix の解析を継続していた。親 hunk は判定を fail に保つ代わりに証拠を捨てている。新テストも理由が一つだけであることしか検査せず、この情報喪失を固定している。 / **最小修正案:** 先に得た `records` から ledger events を構築・検証し、tail reason を追加して status は fail のまま全 prefix 集計を継続する。sentinel による全処理スキップを除く。

4. **[high] / 対象:** [guided.py:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/guided.py:149)、[ident.py:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/ident.py:137)、[wal.py:582](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:582) / **壊れ方:** 同じ trial 名で workload/seed の異なる二つの `start` が並行すると、双方が WAL 不在を確認し、meta を上書きし、非原子的な `exists→open("w")` を通れる。一方が自分の lock を検証して進んだ後、他方が lock を truncate・上書きして進めば、WAL の byte framing は flock で守られても二つの identity の record が一つの campaign に混ざる。`write_lock()` は file/parent fsync もなく、電源断で WAL だけ残れば次回は missing-lock-with-bytes で自己封鎖される。 / **最小修正案:** identity lock を `O_EXCL`、full-write、file+directory fsync の原子的 primitive で確立する。guided は勝者だけが meta を atomic publish し、敗者は meta/WAL を触らず拒否する。

5. **[medium] / 対象:** [ident.py:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/ident.py:137)、[wal.py:625](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:625) / **壊れ方:** `wal_bytes_present()` は全 `OSError` を「bytes 無し」に変換する。例えば `runs/` だけ一時的に EACCES の campaign では、既存 WAL を確認できないまま新しい identity lock を書き、repair は後で失敗する。権限回復後、その既存 WAL は今書いた config のものとして照合を通り、修復対象になる。zero-size symlink/FIFO でも同様に lock の副作用が先行する。 / **最小修正案:** `FileNotFoundError` だけを「無し」にし、その他の stat エラーは伝播させる。`lstat/fstat` で symlink・非 regular を lock 作成前に拒否する。

6. **[medium] / 対象:** [wal.py:351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:351)、[wal.py:439](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:439) / **壊れ方:** repair は境界を chunk scan した後、除去対象 tail 全体を `chunks` と `b"".join()` に展開する。改行のない数 GB の partial WAL では receipt 作成前に OOM/`MemoryError` となり、まさに repair が必要な campaign が再開不能になる。 / **最小修正案:** SHA-256 は streaming update、preview は先頭 128 bytes のみ保持し、removed count は offset 差から算出する。

7. **[medium] / 対象:** [mutation_harness.py:54](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t004-wal-wave/mutation_harness.py:54)、[mutation_ledger.json:84](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t004-wal-wave/mutation_ledger.json:84)、[test_campaign.py:498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_campaign.py:498) / **壊れ方:** M07 は非 str key guard だけを消すが、直後の `_validate_string(key, ...)` が int に対して `TypeError` を出すため、mutant は依然として write 前に拒否する。さらに fixture `{1: ..., "1": ...}` は、そこも迂回できた場合に duplicate `"1"` gate で拒否される。赤は「非 str key が durable に coercion された」の kill ではなく、診断型または別 gate の赤であり、acceptance kill の誤帰属・過剰決定である。 / **最小修正案:** `{1: "value"}` の一意キーを使い、key 型防壁全体を外して実際に `{"1":"value"}` が durable になる mutant にする。現状の acceptance 7 kill は少なくとも 1 減らす。

8. **[medium] / 対象:** [mutation_ledger.json:73](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t004-wal-wave/mutation_ledger.json:73)、[mutation_harness.py:48](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t004-wal-wave/mutation_harness.py:48)、[mutation_m06ab.py:23](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t004-wal-wave/mutation_m06ab.py:23)、[test_campaign.py:740](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_campaign.py:740) / **壊れ方:** M06b は実際に `SURVIVED` のままで、ledger に equivalent 状態も M06ab 証拠も無い。補助 M06ab は同じ複合テストを走らせるが、reader の最初の assertion で停止するため writer 部分には到達せず、「両 gate を外すと writer が未知 stage を書く」という kill を証明しない。handoff の「M06ab kill で裏取り」は帰属不能である。 / **最小修正案:** reader-only と writer-only を別 node に分ける。M06b は parse-line preflight に支配される equivalent と ledger に正式記録し、二重 mutant は writer-only test の結果を独立エントリとして保存する。

9. **[low] / 対象:** [replay.py:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/replay.py:113)、[p2_2_report.py:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p2_2_report.py:63)、[critic/digest.py:192](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/critic/digest.py:192)、[backoff_repro.py:77](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/backoff_repro.py:77) / **壊れ方:** v2 は残る prefix-tolerant caller に用途を docstring 明記すると裁定したが、変更されたのは共有 `read_records()` の docstring だけ。例えば P2 WAL の最後の完全 JSON commit に LF が無い場合、`load_landscape()` はその commit を捨てて後段 `assert_complete()` で落ちるが、公開関数の契約から prefix policy を判別できない。 / **最小修正案:** 各 public consumer に明記するか、名前付き `read_records_prefix()` wrapper に集約して意図をコード上に出す。

## 網羅・互換性の確認

- loop、screening の prepare/evaluate 両入口、guided evaluate、S-1 non-dry resume の repair 順序自体は identity 照合後・append 前になっており、実 repair の結果も表出される。P3 の build/pass は `run_campaign()` 経由で覆われる。欠落は reject 前の identity と上位例外境界。
- 約 18 の直接 `read_records()` production site と、その wrapper caller を追った。無終端 tail だけで `WalFramingError` が prefix callerへ直接漏れる経路はない。`read_records()` が flag を捨てて prefix を返すためである。strict な layer3/plot と checked 化された S-1 は裁定どおり別挙動。
- 終端済み未知 stage・NaN/overflow から `WalLineError`/`WalPayloadTypeError` が伝播する変更は T-007/T-008 の意図どおり。親実測の 30 WAL・3,086 record が 7 既知 stage、非有限値・framing 異常なしなら既存実 WAL の parse 回帰はない。production writer payload も静的追跡上は dict/list/JSON native に収束している。
- guided の既存「lock 無し・WAL bytes あり」campaign が今後 evaluate-resume 不能になる点は、B1 追加判断どおりの意図的 breaking change。`trial_result()` の読取りは残る。meta は exact 4 top-level keys と trial 一致を repair 前に検査しており、裁定で定義された exact 範囲は満たす。
- 変異のうち M01/M03/M04/M05/M06a/M08/M09 の reader kill/M11/M12/M13/M14a/M14b/DP1 は帰属上妥当。M14b の二点 coupled mutationも必要な結合であり過剰決定ではない。問題は M07 と M06b/M06ab。
- pytest は指示どおり未実行。親の実測値を前提に静的追跡し、`git diff --check` のみ clean を確認した。

**最終判定: NO-GO**

---

## 段 6: 親裁定 + fix 指示 (F-A..F-M、逐語)

あなたは [T-004] wave の fix 実装者である。作業ディレクトリ (worktree) には統合済みの未 commit 差分
(WAL byte framing + resume 物理修復 + T-007/T-008) がある。敵対レビュー 2 本の所見を親が裁定した。
以下の採用所見をすべて実装せよ。docs/** の編集・git commit・output/ への書込は禁止。

## 採用所見と設計裁定 (この指示が正本)

**F-A (lock 非原子・非耐久)**: `ident.ensure_resumable_wal` の初回 lock 作成を `wal.write_lock` から
`wal.acquire_lock_atomic` (既存: O_EXCL + file/dir fsync) へ替える。False (既存あり) なら read_lock →
verify_against_lock。guided `cmd_start` も同経路にし、敗者は meta/WAL に触れず構造化拒否
(meta の書込は lock 獲得の勝者だけが行う — 順序: 既存 WAL 拒否 → acquire_lock_atomic → meta 書込)。

**F-B (wal_bytes_present が全 OSError→False)**: `FileNotFoundError` だけを False とし、他の OSError は
伝播させる。呼び出し側 (ident / s8b driver の resume 拒否) が fail-closed に停止することをテストで固定
(EIO 注入)。lock 作成前に lstat/fstat で symlink・非 regular の WAL を拒否する。

**F-C (fresh-reject 自己封鎖 — 最重要)**: repair を伴わない identity-only preflight
`ident.ensure_campaign_identity(cfg, layout)` を新設 (lock 確立/照合のみ。lock 無し + WAL bytes あり
→ 拒否。作成は acquire_lock_atomic)。`ensure_resumable_wal` はこれを呼んでから repair する構造に
整理。**reject を書きうる 5 系統 (p3_s4_loop base / p3_s4_loop_sort / p3_s4_loop_trigger_gating /
s6_sort_sweep / s8a_trigger_sweep) の最初の WAL write より前**に ensure_campaign_identity を配線する
(cfg は各経路に実在する)。テスト: fresh campaign → 初回 reject → 次候補の resume が成功する、を
5 系統ぶん public caller 経由で固定 (helper 直呼びだけのテストは不可)。

**F-D (WalAppendError の end-to-end 保全)**: (i) `wal.append` の os.close 失敗も WalAppendError へ写像
(phase 集合に "close" を追加)。(ii) s1_direct_comparison の retry/deviation 経路、s8b_oracle_driver の
evaluate 例外畳み込み、s6/s8a の driver-error 変換は、**broad except の先頭で WalAppendError /
WalFramingError を再送出**し、同一 WAL への後続書込 (session-result / deviation / trial-result /
再 reject) を行わない。s6/s8a は sweep 全体を停止。テスト: partial-write EIO 注入と full-frame 後
fsync EIO 注入を上位入口 (S-1 run_role 系、s8b driver、s6/s8a sweep) で各 1 本。

**F-E (dir fsync が flock 外)**: append の runs dir fsync を **flock 解放前 (os.close 前)** に移し、
新規作成時だけでなく毎 append で行う (耐久性 > 追加 fsync 1 回のコスト)。

**F-G (repair の OOM)**: 除去 tail を全 bytes 保持しない — sha256 は chunk streaming、preview は
先頭 128 bytes のみ、removed_bytes は offset 差で算出。

**F-H (親 hunk の証拠喪失 — s1_report 再設計)**: `_TruncatedWalTail` sentinel による全処理スキップを
やめる。`wal.read_records_collected(layout)` を try 先頭で 1 回呼び、(a) truncated_tail なら
`wal_truncated_tail` reason を積み status=fail 固定、(b) line_issues が非空なら件数と先頭数件を持つ
`wal_line_issues` reason を積み status=fail 固定、(c) **いずれの場合も prefix records で解析を継続**
(expected_sessions / starts / samples / retries / budget_refusals / commit 集計を捨てない —
D68 (4) の anti-masking と同じ原則)。そのために s1_direct_comparison の event 構築・schedule 検証を
records 入力の純関数 (例 `session_events_from_records(records)` / schedule 検証の events 入力版) へ
抽出し、s1_report は raising wrapper でなくそれを使う。s1_direct 自身の raising 版
(read_session_ledger / validate_session_ledger) の外部挙動は不変に保つ。
テスト再設計: torn-tail fixture は **完走済み prefix + 無終端 tail** (deviation event を使わない —
過剰決定の除去) とし、「reason に wal_truncated_tail を含む + status fail + prefix 解析値が
維持される」を固定。line_issues 併存 fixture (正常行 + 終端済み不正 JSON + 無終端 tail) で
両 reason の併記を固定。

**F-J (M07 帰属不能)**: 非 str key の acceptance fixture を `{1: "int-key"}` 単独キーへ差し替え
(coercion 後 duplicate の独立赤を除去)。key 型防壁は「isinstance guard + _validate_string(key)」の
二層であることをコメントで明示 (変異登録は親が行う)。

**F-K (M06 検査の混在)**: `test_wal_stage_contract_is_exact_and_unknown_stage_fails_closed` を
reader 検査と writer 検査の**別テスト node** に分割する (assert 内容は不変)。

**F-L (prefix 容認方針の明示)**: replay.load_landscape / p2_2_report / critic digest / backoff_repro の
read_records 使用箇所に「prefix 容認 (crash tail は黙って捨てる) — 公式判定に使わない」旨の
docstring/コメント 1 行を置く ([T-082] の移行対象マーカー)。

**F-M (定数 assert の恒真)**: stage 定数の共有 assert を `is` 同一性 (re-export が同一 object で
あること) に替える。CPython の literal 非 interning ('-' 含み) に依存する旨のコメントを 1 行付す。

## 棄却済み (実装するな)

- runs dir symlink 経由の他 campaign truncate 対策 (openat 全面化・st_nlink 検査) — 脅威境界外
  (D68 (6): 改竄耐性は謳わない)。親が台帳へ記録する
- reader への shared lock、repair の durable intent/再入機構 — 裁定 v2 どおり不採用のまま

## 規律

- テストを甘くしない。期待値へ揮発値を焼き込まない。既存の受入緑 (2598 passed) を、上記で明示した
  期待値再設計以外で壊さない。所有制限は今回なし (上記ファイル群 + そのテスト)。ただし
  s1_known_axes_freeze.py / test_s1_known_axes_freeze.py / docs/** / output/** は絶対に触らない
- 完了報告: 変更一覧 (file:line)、走らせたテストと範囲、全 suite の赤の完全一覧と帰属

---

## 段 6: fix 完了報告 (codex max、逐語)

実装完了です。採用所見 F-A〜F-M をすべて反映し、全 suite は緑です。

### 変更一覧

- [wal.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:61): close 失敗の構造化、flock 内・毎 append の dir fsync、tail hash の streaming 化、WAL の lstat/fstat 検査と EIO 伝播（L61, 148, 283, 380, 472, 659）。
- [ident.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/ident.py:128) / [guided.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/guided.py:149): atomic identity-only preflight と guided 勝者限定 meta 書込。
- reject-first 自己封鎖対策:
  [p3_s4_loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop.py:627),
  [p3_s4_loop_sort.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop_sort.py:241),
  [p3_s4_loop_trigger_gating.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p3_s4_loop_trigger_gating.py:397),
  [s6_sort_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s6_sort_sweep.py:257),
  [s8a_trigger_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8a_trigger_sweep.py:302)。
- WAL 例外の end-to-end 保全:
  [s1_direct_comparison.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:760),
  [s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1176),
  s6/s8a の sweep 全体停止。
- S-1 prefix 証拠保持:
  [s1_direct_comparison.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:239) に純関数を抽出し、
  [s1_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:341) で truncated tail・line issues を併記しつつ解析継続。
- T-082 マーカー:
  [replay.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/replay.py:123),
  [p2_2_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/p2_2_report.py:65),
  [backoff_repro.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/backoff_repro.py:77),
  [critic/digest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/critic/digest.py:201)。
- F-J/K/M と回帰:
  [test_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_campaign.py:296)（非 str 単独 key、reader/writer node 分割、耐久性・EIO・streaming）、
  [test_s1_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_report.py:261)、
  [test_guided.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_guided.py:268)、
  [test_s6_sort_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s6_sort_sweep.py:292)、
  [test_s8a_trigger_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8a_trigger_sweep.py:282)、
  [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1818)。

### 検証結果

- 指定 focused 回帰: 27 node 緑。
- 変更対象 11 suite: `548 passed, 10 skipped`。
- 全 suite: `2610 passed, 26 skipped, 0 failed`（193.11秒）。
- `python3 tools/check_codex_agents.py`: OK。
- `python3 tools/check_docs.py`: 違反なし。
- `git diff --check`: OK。
- `external/ccbench`: clean。

### 全 suite の赤と帰属

赤はありません。変更起因・既存・環境起因ともに 0 件です。

`docs/**`、`output/**`、指定 freeze ファイルは編集していません。開始時から存在した未追跡 handoff は未変更です。git commit も作成していません。

---

## 受入 (親実測)

- 統合全走 (fix 前): 2598 passed / 19 skipped / 0 failed
- fix 後の親独立全走: **2618 passed / 18 skipped / 0 failed**
- 実 WAL 回帰 (fix 後再走): 30 本 / 3,086 record、stage 7 種の分布完全一致、line_issues 0、
  truncated_tail 0 — **PASS**
- 変異 matrix: 台帳 insight 参照 (acceptance 8 kill / durability 6 kill / wiring 1 kill /
  diagnostic-pin 2 / equivalent 1)
