## 総括

**登録簿 +2 は実測を条件に維持できますが、「配線 3 行で成果物の未確立一覧が縮む」という計画は修正が必要です。** 最大の見落としは S6 の admission が保存されないことです。official 同形供給についても、既存 login ログは証拠になりません。

必読 4 資料と指定コード・関連テストを静的に確認しました。変更、pytest、compiler、計算ノード実走はしていません。

## 主要所見

### B1．S6 の admission は成果物へ届かない

**real／scope 内／must-fix**

[s6_sort_sweep.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/s6_sort_sweep.py:309) は `_preflight_condition_gate(sub, patch)` の返り値を捨てています。`:498` の `_write_provenance` にも condition record の保存欄はありません。plan が挙げた `:244–247` は helper の返却辞書であり、成果物への保存ではありません。

- 最小案：S6 の配線を今回から外し、D1492 に従って理由を記録する。
- S6 も完了対象にする案：admission の保存先・参照側・再開時の扱いまで編集面へ追加する。「1 行変更」のまま扱わない。

**放置時の影響：S6 の拒否集合だけが変わり、成果物上の未確立一覧の縮小を示せない。**

P3 sort も限定が必要です。`:430` の返却値は `drive_iteration` へ届きますが、CLI `:802` 以降は outcome 等だけを表示し、condition record を保存しません。**API 返却値での縮小は確認できるが、永続成果物での縮小は別途示す必要があります。** 一方、rung1 は `:4635` の `condition_gates` へ保存する経路があります。

### B2．login と official の供給は実際に異なる

**real／scope 内／must-fix**

親の `pre-*.stdout.jsonl` の configure evidence は、全件が次の形です。

- `CMAKE_PREFIX_PATH` あり。
- `FETCHCONTENT_SOURCE_DIR_*` 3 本あり。
- **`FETCHCONTENT_BASE_DIR` なし。**
- meaning はすべて `unestablished`。

対して [s8b_floor_campaign.py:3480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/s8b_floor_campaign.py:3480) の現行経路は BASE_DIR＋SOURCE_DIR 3 本です。`prepare_kwargs` に dependency prefix を設定していないため、ここでは PREFIX_PATH は空です。`test_s8b_floor_campaign.py:3878` 付近も **4 引数**を pin しています。

official の経路は、依存 source 検証 → masstree prebuild → binding 作成 → `floor_prepare` → S1 capture → meaning 独立 configure／前処理です。meaning が赤なら S1 が prepared cell を拒否します。供給側だけ緑でも、独立 meaning build の `config.h` 可用性は保証されません。

段 6 の完了条件に、**最終 production 登録簿で、official が生成する実引数列と準備順を使った SORT の supply・meaning・family 1 cell**を明記してください。段 5 の shadow 成功だけでは代用できません。

**放置時の影響：従来受理された official sort_best cell が依存不足で拒否され、意味検査の成功として報告した証拠と実経路が食い違う。**

P3/S6 の capture に offline 引数がない問題まで直す場合は、配線 1 行を超える依存供給変更です。別の編集面・検証条件を持つ裁定パッケージに分けるべきです。

### B3．consumer 回帰の列挙に oracle 側が抜けている

**real／scope 内／must-fix**

plan の共通 SORT fixture 修正は正しいですが、回帰先が不足しています。

`test_s8b_oracle_driver.py:2811` は、`test_s1_direct_comparison._issued_condition_records` を呼びます。その helper は実 `_condition_records_for_genome` を実行します。S1 の autouse fixture は compiler を完全には消しておらず、登録後は SORT meaning の実 configure／前処理が増えます。

最低限の参照閉包は次です。

| 参照経路 | 回帰対象 |
|---|---|
| gate の登録・factory・fixture | `test_condition_meaning_gate.py` |
| 配線 driver | `test_p3_s4_loop_sort.py`、`test_s6_sort_sweep.py`、`test_silo_ladder_rung1_driver.py` |
| 共通 `SORT_VARIANT_SOURCE` | `test_p3_exploration_namespace.py`、`test_p3_build_authority_cli.py`、`test_sort_swo_oracle.py` |
| S1 の実 record 発行 helper | `test_s1_direct_comparison.py`、**`test_s8b_oracle_driver.py`** |
| official の供給引数・header fixture | `test_s8b_floor_campaign.py` |
| source inventory／binding | B-4、known-axes、rung1 evidence、oracle manifest の各テスト |

**放置時の影響：S1 の fixture／record 変更が oracle の受理テストへ伝播するのに、完了検査から漏れる。**

全体 5 分超過そのものは **判定不能／scope 内／nit**。静的には増分があり、既存 helper の `lru_cache` もありますが、所要時間は確定できません。実 compiler 正負例を全 consumer で重複展開せず、機械テストの既存 stub を維持したうえで、author が規定の全体時間を確認する必要があります。

## pin・閉包の照合

以下は「変更で必ず赤になる pin」と「参照しているが更新不要な pin」を分けた一覧です。

| 対象 | 判定・必要な扱い |
|---|---|
| `_COMPILE_TIME_BRANCH_MACROS` と `T:978` | **real／内／must-fix**。+2 を既存順序の末尾へ追加。未修正なら登録簿一致検査が赤。 |
| `_patch_added_branch_declaration`、`T:245,988` | **real／内／must-fix**。REPORT の複合 directive を独立した期待逐語で扱う。単純 `#if {macro}` 前提では fixture／patch pin が赤。plan は捕捉済み。 |
| `MEANING_SUPPORTED_MACROS`、`T:2692` | **refuted／内／nit**。「別の集合リスト修正が要る」は否定。tuple 展開から更新される。旧宣言の BACKOFF_FIXED 限定は残す。 |
| REPORT owner target、共通 SORT 二重 directive | **real／内／must-fix**。前者は owner command 不在、後者は `start-not-unique`。plan は捕捉済み。 |
| B-4 module 数 `47`、`.start` heuristic | **refuted／内／nit**。今回の辞書追加・既存 import 経由の呼出し置換は import 集合も import-time `.start` 呼出しも増やさない。数値の追随更新は不要。 |
| known-axes の歴史 source hash | **refuted／内／nit**。「sort driver 編集で凍結 bytes を更新する」は不要。`_HISTORICAL_CODE_PATHS` の例外は特定の既知歴史文書に限定される。任意 manifest 全体の免責ではない。 |
| rung1 自己 hash | **real／内／nit**。`:2629` の submit binding、`:3739` の current binding は現行 driver bytes を読む。旧 submit receipt の再利用は拒否される。既存歴史 evidence test は歴史 driver hash と現在との差を要求しており、歴史値を更新しない。 |
| rung1 contract／ledger | **refuted／内／nit**。driver path・patch hash・macro 等の契約は今回不変。driver 1 行の変更だけを理由に ledger／歴史 evidence を再発行しない。 |
| oracle manifest source 列挙 | **refuted／内／nit**。`_GENERATOR_SOURCES` は S1 materializer、report、judge、outcome-stage contract、artifacts の 5 本。今回の production 4 files は含まれず、S1 bytes も変更しないため、この pin の更新は不要。 |
| `check_docs.py` | **refuted／内／nit**。今回の 4 production files の現行 hash を固定する専用 pin は確認できない。rung submitter の grandfather 宣言は別契約。docs 追記の通常検査は必要。 |
| `check_ai_provenance.py` | **real／内／must-fix**。hash の追随更新ではなく author 契約。production・test とも実装面なので Codex author の provenance を維持する。欠落すれば commit の監査受理が変わる。 |

B-4 や oracle の source 列挙を広げる変更は、本 wave の必要差分ではありません。列挙外依存を含む完全なコード閉包を要求するなら **scope 外／backlog** の裁定事項です。

## 削減案と親の一般化

| 攻撃案・主張 | 判定 |
|---|---|
| 配線を全部後送し登録簿だけにする | **refuted／内／nit**。S1 は自動発火するが、REPORT の consumer は未宣言のまま。REPORT の成果物縮小を失う。S6 だけ後送する案は B1 の最小修正として妥当。 |
| probe を省き production CLI だけで測る | **refuted／内／nit**。未登録時の CLI は新規 meaning を発行できない。採否前に測るには shadow 等が必要。採用後の SORT/REPORT 確認は production CLI に寄せられる。 |
| SS2PL 3 件の meaning 実測を省く | **real／外／backlog：scope 縮小案**。今回の受理集合縮小には直接寄与しない。ただし親の「各件を実測して決着」という成果物契約を変えるため、無断で削らない。不採用理由を静的制約へ限定する案として返す。 |
| 計算ノード 1 本を足す | **判定不能／内／nit**。過去の S2 bytes 一致は今回の供給を保証しないが、今回の不具合も未実証。追加するなら B2 の最終 production・official 同形 cell と兼ね、同じ login 条件の重複測定にはしない。 |
| 5 file の sha 比較で稼働 wave と重複なし | **real／内／nit：結論の過大一般化**。ある時点の bytes 一致は将来の編集予定を示さず、plan で追加した共通 fixture 等も走査対象外。実際の衝突は判定不能。編集所有 path の照合として補う。 |
| `output/` に SORT gate record がないので影響なし | **refuted／内／nit**。record 不在からコード参照・受理経路の不存在は導けない。既存 freeze／WAL には SORT の参照があり、S1 は登録追加だけで発火する。record の不存在自体は走査範囲付きで記録する。 |

P3～P5 の不採用理由は plan の修正を支持します。特に IMPL/WFG は「機構上観測不能」ではなく、代表枝の採用範囲と consumer の supply 拒否を区別してください。

段 4 で確定すべきなのは、**S6 を外すか保存契約まで含めるか、P3 の成果物を API 返却値とするか永続記録とするか、最終 official 同形 cell をどこで通すか**の 3 点です。