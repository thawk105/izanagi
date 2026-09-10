静的検査のみで、pytest は実行していない。したがって緑とは主張しない。

## 正しさゲート差分 — 非所見

計画どおりの編集面だけなら、`verify_manifest` / `load_approved_spec` / `validate_approved_spec_snapshot` の受理集合は広がらない。

- **触る production 行:** 新規 `orchestrator/campaign/s8b_oracle_spec_candidate.py` のみ (`plan.md:9-16`)。
- **触らない行:** `s8b_oracle_spec.py:18-41,98-180,183-201,204-276`、`s8b_oracle_manifest.py:1018-1166,1198-1260`。
- **負の対照:** producer が候補 bytes `B` を返しても `APPROVED_SPEC_SHA256=None` なら、`load_approved_spec` は `no-approved-spec` (`s8b_oracle_spec.py:183-186`)、snapshot validator も同じ (`:204-216`)、`verify_manifest` はその拒否を `ManifestError` にする (`s8b_oracle_manifest.py:1123-1130`)。
- **成果物影響:** この wave のままでは certified 選択・report・ledger の受理集合は前後とも空。将来の `None→h` 遷移は別であり、S1 の対象。

## S1 — 「批准前 binding を権威にしてよいか」は裁定だけでなく、producer の trust-root 欠落でも壊れる

- **file:line:** `plan.md:41-44`; `s8b_ratified_freeze.py:63-65`; `s8b_oracle_spec.py:161-166`; `s8b_oracle_manifest.py:515-565,800-802,1140-1147,1220-1253`; `s8b_oracle_driver.py:1603-1615`。
- **壊れる具体的な入力・状態と誤出力:** `output/s8b-freeze/holdout_freeze.json` を同じ cell 集合のまま別 variant entry へ改変する。計画は canonical path を parse するだけで、既存の `V1_FREEZE_SHA256` と照合しないため、改変 entry から binding を materialize し「検証済み候補」を返す。将来その hash が pin されると loader は受理し、active v2 の cell 集合だけが一致すれば manifest candidate と `verify_manifest` も通る。binding と active freeze の実体突合は driver まで遅れ、そこで初めて `binding-refused` になる。
- **成果物影響:** approved spec と official manifest の `binding_identity` / `spec_sha256` が未批准材料を参照し、実走は全 row 未解決となって certified 選択・report・ledger が発行不能になる。

`None→h` は確かに受理集合を 0 件から1件へ広げる。これは D355 型のユーザー裁定事項である。一方、「その `h` の bytes が承認済み v1 trust root から導出されたか」は既存 hash で機械判定できる実装問題であり、すべてを「裁定事項」と分類するのは誤り。

## S2 — 親実測の「生成不能」への一般化は成立しない

- **file:line:** `blocker-correction.md:13-24`; `s8b_materialization.py:98-146`; `s8b_oracle_spec.py:25-41,105-180`; `s8b_oracle_manifest.py:673-703,1198-1216`。
- **壊れる具体的な入力・状態と誤出力:** 現在の v1 freeze は `floor=null` / `budget=null`、active v2 も不在だが、spec schema に floor/budget は無く、binding は v1 entry と materializer だけで導出できる。したがって compute node と正しい設計入力があれば reviewed-spec candidate は生成できる。「今日 bytes を作れない」という旧 handoff の一般化が誤出力である。
- **成果物影響:** candidate/承認手番を不必要に停止させる一方、official manifest と certified 選択は floor/budget および active v2 が無いため依然として発行不能。

`blocker-correction.md` は materialization の中心誤認を正しく撤回済み。残る境界は「candidate は作れる」「official manifest はまだ作れない」である。

## S3 — 計画は訂正済みの導出可能値を再び外部入力へ戻し、非実行可能 spec を生成する

- **file:line:** `plan.md:22-35`; `measurements-2.md:6-18`; `s8b_oracle_manifest.py:424-455`; `s8b_oracle_spec.py:140-178`; `s8b_approved.py:57-67`; `s8b_floor_contract.py:523-528`; `env_contract.py:99-177,916-923`; `s8b_oracle_driver.py:930-957`; `s8b_oracle_report.py:1390-1400`。
- **壊れる具体的な入力・状態と誤出力:**
  - 正しい `ccbench_pin` を使う一方、`env_tag="pegasus"`、`clocks=1800`、`contract_sha256="0"*64` とする。型・64hex・固定 reps/extime 等は満たすため producer/spec/manifest validator は通り、approved manifest candidate まで作れるが、driver は env authority との不一致で拒否する。
  - 正しい run contract に `allowed_excluded_reasons=["slow-result"]` を与える。spec validator は非空・重複なししか見ないため受理し、report は `"slow-result"` を許可済み除外として扱う。既存の権威は固定4理由である。
- **成果物影響:** 前者は全実走を止め、後者は report が除外として許す行集合を広げ、certified 選択の母集団を変えうる。

`measurements-2.md` が訂正したとおり、外部自由軸は5つであり、計画の「exact 6 keys、run_contract 全体と reasons を caller 入力」はその訂正を反映していない。

## S4 — approved lifecycle の正例はあるが、`(h, fileなし)` 枝は未発火のまま

- **file:line:** `plan.md:92-107,119-145`; `parent-design-note.md:34-43`。
- **壊れる具体的な入力・状態と誤出力:** helper を「pin があり、見つかった file にだけ hash 検査する」と誤実装すると、`(h, empty)` を受理してしまう。計画された4テストは exact pinned file、未承認 file、hash mismatch、extra file だけなので全部通る。実 repo test も現在は `(None, empty)` であり、この欠陥を踏まない。64hex でない pin の正例・負例も無い。
- **成果物影響:** hash だけを書いて canonical spec を置き忘れた承認 commit が acceptance を通り、runtime loader は `approved-spec-unreadable`、certified 選択・report・ledger は全停止する。

したがって「承認済み枝が一度も発火しない」問題自体は `test_durable_reviewed_spec_lifecycle_accepts_exact_pinned_file` で解消されるが、状態機械全体の保証にはなっていない。

## S5 — canonical spec の symlink を許すと、repository diff に存在しない bytes が「承認済み」として通る

- **file:line:** 現行 `test_s8b_oracle_manifest_contract.py:130-142`; `plan.md:94-107`; `s8b_oracle_spec.py:190-201,259-270`; `s8b_oracle_artifacts.py:104-133`。
- **壊れる具体的な入力・状態と誤出力:** `reviewed_spec.json` を `/shared/unreviewed.json` への tracked symlink とし、pin をその target bytes `B` の SHA-256 にする。`Path.is_file()` と `read_bytes()` は symlink を追うため、lifecycle と loader は `B` を受理する。しかし staged diff に入るのは symlink のリンク文字列だけで、`B` 自体は査読対象に含まれない。
- **成果物影響:** repo 外の未査読 `B` が approved spec の schedule/run contract/reasons/binding 権威となり、certified 選択・report・ledger の値を `B` に従わせられる。

補足すると、loader は一度読んだ raw bytes を snapshot 化するため、読込後に別 hash の target へ差し替える通常の TOCTOU は hash mismatch で止まる。固定 `SPEC_REL` により相対 path 注入もなく、現在の Linux では大文字違いは別 sibling である。duplicate key と非canonical JSON も拒否される。見つかった具体的な穴は nofollow/lstat 不在による「査読対象外 target」の受理である。

## S6 — 親 brief の「pin 閉包全件列挙」は path 参照だけで、bytes・schema・role pin を落としている

- **file:line:** `test_s8b_oracle_manifest.py:39-63,66-100,1157-1178,1366-1369`; `s8b_oracle_spec_fixture.py:54-71`; `test_s8b_materialization.py:335-360`; `s8b_oracle_driver.py:77-80`; `s8b_oracle_report.py:1245-1248`。
- **壊れる具体的な入力・状態と誤出力:** `_GENERATOR_SOURCES` の role/path、binding key、schema literal、または canonical serializer 出力を変えても、brief §3 の8箇所だけを監査すれば「閉包維持」と誤報できる。実際には `PIN_GATE_SPEC_RAW`、`PIN_GATE_SPEC_SHA256`、`PIN_GATE_SCHEDULE_SHA256` と独立 role/key golden が追加 pin である。
- **成果物影響:** hidden pin の更新漏れで受入が後から赤になり、spec/manifest 発行と certified 選択が停止するか、逆に独立 golden を同時更新して検出力を自己追認化する。

## S7 — 変異事前登録の一部は期待 node への帰属が成立しない

- **file:line:** `plan.md:203-215`; `s8b_oracle_spec.py:123-170`; `s8b_materialization.py:98-146`。

| 変異 | 静的な帰属判定 |
|---|---|
| holdout sort 削除 | fake freeze が最初から `rr20, rr80` 順なら出力不変で、予定 node は落ちない。逆順 witness の明記が無い。 |
| configuration 集合一致検査削除 | 一方の holdout から cell を欠かすと、明示検査ではなく `prepare_binding` の「freeze binding がない」で落ちうる。過剰決定。 |
| generator SHA を固定/caller 入力化 | stale 固定値なら spec validator の live hash 検査で先に落ちる。fixture と同じ固定値なら source bytes を変える正の対照が無い限り node が落ちない。 |
| schedule hash を入力/別 object hash化 | 不一致値は `validate_reviewed_spec` の再生成照合で先に落ちる。正しい hash を caller が与えれば変異は観測されない。 |
| validator 呼出し削除 | `calls...exactly_once` は削除そのものを捕捉する。ただし捨て document への形式的1回呼出しは防げない。 |
| `root/SPEC_REL` へ書込み | 永続 file を残す exact 変異は捕捉できる。作成後に unlink する transient write は namespace の事後 snapshot だけでは落ちない。 |
| unapproved で file 許可 | 予定負例に直接帰属し、妥当。 |
| approved hash 比較削除 | hash mismatch 負例に直接帰属し、妥当。 |
| manifest candidate dir を列挙外 | extra-file test が spec sibling を置けば変異後も拒否され、node は落ちない。candidate dir/sibling/subdirectory を別々に発火させる記載が無い。 |

- **壊れる具体的な入力・状態と誤出力:** 上表の sorted fake freeze、非uniform freeze、stale generator literal、正しい caller schedule hash、spec sibling extra file が具体的 witness。変異が生存するか、別例外で KILLED と誤計上される。
- **成果物影響:** producer の derivation と durable namespace 閉包が実際には検証されないまま「変異 KILLED」と報告され、誤った spec candidate または壊れた承認状態を受入へ流す。

## S8 — 新規 test file は計画どおりだと横断 meta-test で必ず赤になる

- **file:line:** `plan.md:64-74,227-239`; `test_plain_runner_coverage.py:25-27,44-74`; `orchestrator/tests/README.md:150-184`; `docs/failures.md:1600-1637`。
- **壊れる具体的な入力・状態と誤出力:** 計画された `test_s8b_oracle_spec_candidate.py:1-240` には self-run harness の行がなく、編集面にも README allowlist が無い。そのまま追加すると `test_every_test_file_is_self_runnable_or_allowlisted` が offender として拒否する。
- **成果物影響:** wave acceptance が赤で land できず、candidate producer・承認 spec・certified 選択は一件も発行できない。

## S9 — production/CLI/docs/受入のうち、運用可能性を閉じる層が scope 外のまま

- **file:line:** `plan.md:60-62,138-147,225-235`; `blocker-correction.md:30-37`; `s8b_oracle_manifest.py:1198-1282`; `docs/decisions.md:15565-15579`。
- **壊れる具体的な入力・状態と誤出力:** Pegasus login node で将来の承認者が preview CLI を実行すると、既知の compiler 不在により実 materialization へ到達できない。専用テストは materializer spy で、実 v1 freeze×12 cell の CLI 正例は受入集合に無い。加えて durable install、hash 記入、regular-file 確認、generator pin rollover の手順を置く docs 編集も計画に無い。
- **成果物影響:** code が land しても査読対象 bytes/hash を再現できず、または数日後の generator drift で失効し、certified 選択・report・ledger の参照元が発行されない。

裁定パッケージ候補として残すべき層は次のとおり。

| 層 | 計画の状態 | 裁定対象 |
|---|---|---|
| production candidate producer | scope 内 | v1 trust-root 照合と、active v2 以前の binding を権威候補にしてよいか |
| runtime lifecycle | scope 外、contract test のみ | runtime でも symlink/extra durable file を拒否するか |
| approval/install CLI | 意図的に無し | detached review trust root、または staged regular bytes の運用契約 |
| docs/runbook | 編集面無し | compute-node 実行、exact bytes 保存、pin diff、rollover/失効手順 |
| acceptance | spy 中心 | 実 materializerを使う end-to-end candidate 正例を要求するか |

## 総括

- **must-fix:** S1、S3、S4、S5、S6、S7、S8。特に S1/S5 は「未批准・未査読 bytes を approved 権威へ運ぶ」具体経路、S3/S4 は発行後に必ず止まる spec を acceptance が通す経路。
- **nit:** なし。各所見は受理集合、approved参照、または certified 選択の可用性へ1行で影響を結べる。
- **親 brief への反対:** 不変条件4の「全件列挙」は偽で、P3 の「repo 権威から導出できない」も run contract/reasons について過大。旧 materialization blocker は訂正どおり撤回が正しい。
- **裁定パッケージへ送る項目:** S1 の v1 binding authority、S5/D356 の regular-file・外部 trust-root 境界、S9 の compute-node発行手順・実E2E受入・generator rollover・runtime lifecycle 配線。