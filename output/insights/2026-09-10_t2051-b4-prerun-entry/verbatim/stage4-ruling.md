# 段 4 裁定 — [T-2051]

wave `dev-wave-t2051-b4-prerun-entry` / 起点 main `7f17e1c63`。
入力は段 1 brief、段 1 追補、段 2 plan、段 3 レンズ A / B、および親の実測。

## 0. P1 の帰結

**P1 (「本 wave に、今日発火する実装面の純増は無い」) は倒れた。** ただし倒した理由は
段 3 の 2 レンズが挙げた理由と異なる。

- レンズ B は manifest membership を実装候補に挙げた。
- レンズ A は「母集合を manifest 201 行にするか registry 全行にするかが未裁定だから
  実装へ送るな」として保留を求めた。
- **親が台帳を引いたところ、この点は D1880 (2026-09-09) で裁定済みだった。**
  「formal B-4 の母集合を analysis manifest の 201 行に固定する。scheduled attempt registry の
  全行は母集合にしない。manifest 外の registry 行は、hash が一致しても実行しない。」
- したがってレンズ A の保留理由は**現物で refuted**。レンズ B の候補は採用する。

**採用の理由は「発火するから」ではない。** 今日 formal B-4 が発火しないことは変わらない
(admission record 3 件不在、§5 の 7 欄未記入、§6 の前提 1 / 6 / 8 未充足)。採用の理由は
**裁定済みで未実装の決定が存在し、その未実装が事前登録 §7.1 が禁じる file-drawer 経路を開いたまま
にしている**ことである。T-2101 が受理された形 (実走前に実在する非恒真述語を閉じる) と同型である。

## 1. 採用 (段 5 で実装する) — 1 単位

**D1880 の実装。** `orchestrator/campaign/p3_s4_loop.py` の
`require_b4_proposal_registry_binding()` (:478-507) に **analysis manifest membership の要求**を足す。

- 現状: 期待 hash を `publication.registry.scheduled_attempts` から引くだけで
  (`_require_b4_registry_attempt_hash`)、`publication.manifest.rows` を見ない。
- 変更後: 同じ attempt_id が manifest の行にちょうど 1 件存在することを要求し、
  無ければ `B4ProtocolError` で campaign 副作用より前に拒否する。
- 呼び手は 3 driver 共通 (`p3_s4_loop.py:2244`、`p3_s4_loop_sort.py:494`、
  `p3_s4_loop_trigger_gating.py:974`)。共通関数 1 か所の変更で 3 driver に効く。
- 併せて `B4_PROPOSAL_BINDING_NON_GUARANTEES` (:172-183) の項目 3
  「manifest membership は検査しない (裁定パッケージ 3)。」を、D1880 の実装に合わせて更新する。
  **exact tuple pin が `orchestrator/tests/test_p3_b4_proposal_binding.py:520` にある**ため、
  同じ変更単位で直す。

### DW-G05 — 放置した場合の成果物影響

放置すると、manifest 外の registry 行を attempt id に指定した formal bootstrap が**受理され**、
build と WAL が進む。その結果は raw record producer の `_manifest_row()`
(`p3_b4_raw_record_producer.py:945-954`) が後から拒否するため、**走ったのに §7.1 の全件報告に
現れない campaign** が作れる。これは事前登録 §7.1 が名指しで禁じる file-drawer 経路である。
実装すると formal bootstrap の受理集合が manifest 201 行へ狭まる。

### 規律 2 との関係

本変更は受理集合を**狭める**方向であり、正しさゲートを緩めない。verdict の定義も
受理集合の拡大も行わない。

## 2. 不採用 (scope 外。裁定パッケージまたは carry へ)

| # | 所見 | 判定 | 扱い |
|---|---|---|---|
| a | D1881 (事前登録が publication root を 1 つ名指しし、発行器が他を拒否する) | real・裁定済み・未実装 | **本 wave では実装しない。** 凍結事前登録の編集を伴い、本 wave の不変条件と衝突する。未実装の裁定として次の一手へ立てる |
| b | `p3_b4_prerun_issuer.py:54` の `formal_launcher_not_wired_to_require_this_receipt` が陳腐化 | real | 記録のみ。凍結 receipt field なので erratum が要る |
| c | `p3_b4_raw_record_producer.py:63` の `initial_proposal_sha256` 非保証が部分的に陳腐化 | real (前段のみ) | 記録のみ。後段 (束縛は転記に留まる) はなお真でありうる。report へ射影されるので独立の裁定が要る |
| d | 事前登録 §7.2 / §10 の「正式 launcher への必須配線も無く」が陳腐化 | real | 記録のみ。凍結文面は本 wave で書き換えない |
| e | certified 選択への必須配線 (T-2139) | real・未達 | 再開条件 4 項目のうち無条件 3 件が未成立。実装しない |
| f | material report を「§7.1 全件 report」と呼べない | real | 記録のみ。成果物自身が `section_7_1_four_classifications_operationalized: false` と宣言する |
| g | 「不変な結果 artifact の writer」は create-only であって不変ではない | real | 記録のみ。削除後の別 bytes 再発行を排除しない |
| h | continuation の提案束縛 (T-2101 裁定パッケージ 1) | real | 本 wave の scope 外 |

## 3. 親 brief の訂正 (両レンズと親の実測で確定)

| ID | 訂正 |
|---|---|
| M1 | CLI の実在と拒否枝の実測であって、valid 入力から report が出る成功経路の証明ではない |
| M2 / M3 | 「4 項目中 3 項目着地」は `p3_b4_analysis_path.py` docstring の 5 語台帳の中の話。依頼の文言 (§7.1 全件・不変・chain 全体の起動口) に照らすと未達。集計を撤回する |
| M4 | T-2139 の再開条件は無条件 3 件 + 順方向を含める場合 1 件 = 4 項目 |
| M6 | 「production 成果物 0 件」は検索 root `/work/1/SFC/tanab/izanagi/output` の範囲での実測。issuer は任意の絶対 root を許すので全称主張はできない |
| M7 | `campaign.lock` は 30 → 32 (並行 wave による時点差)。`b4_reflux_ablation` hit 0 は不変 |
| M8 | 「publication が最初の停止点」は誤り。admission record 検証が先に走る |
| M9 | 「呼び手 0 件」は production 呼び手 0 件の意。test / support 呼び手は複数ある |
| M11 | 機械条件は「201 件の適格な型付き registry 行」。実 precursor artifact の存在を再導出しない |
| M12 | `REJECTED` + 赤 class は必要条件であって全条件ではない |
| M13 | 赤 precursor は 0 件でなく最大 3 件 (`s4_rejections_digest.txt`)。適格確認は 0 件。権威母集合が未同定なので全称の 0 は言えない |
| M14 | §5 の `未記入` を含む値セルは 6 行でなく **7 行** |
| M18 | 「未 commit 差分 hit 0 ⇒ 編集面重複なし」は commit 済み作業面を見ない。親は追加で全 worktree の `p3_s4_loop.py` を内容 hash で照合し、main HEAD と異なる 9 件がいずれも**古い基点による差**であることを確認した |

## 4. 停止地点の構造 (段 7 の成果物。両レンズの must-fix を反映)

直列 L1〜L5 をやめ、6 層 × 3 状態で書く。状態は
`observed stop` (実測した拒否) / `unreached` (入力を作っていないので拒否も観測していない) /
`static expected rejection` (コードから読める予測) を必ず区別する。

| 層 | 状態 | 根拠 |
|---|---|---|
| 1 規範・admission | **observed stop** | `p3_b4_launcher.py bootstrap` 実走で `[admission-record] record is unavailable` rc=1。admission record 3 件不在。§5 の 7 欄未記入 |
| 2 権威ある母集合 → 予定表 producer | **unreached** | 権威 producer が存在しない (`p3_b4_analysis_ledgers.py:1-6` が自ら宣言)。赤 precursor 最大 3・適格確認 0 |
| 3 publication 発行 | **unreached** + static expected rejection | production 呼び手 0。適格 201 行未満なら `design_not_feasible` (`:1076,1158`) だが、実際の拒否 receipt は存在しない |
| 4 全 block・全 arm 実行調停 | **unreached** | launcher は単一 arm の driver 起動までしか覆わない |
| 5 driver 終端 → raw writer | **unreached** | 接続する production 呼び手が 0 |
| 6 report → certified 選択 | **unreached** | `report.complete` 0、report 後の正規呼び手 0、耐久判定先 0 |

## 5. 変異事前登録 (DW-M01。実装前に固定する)

対象 file: `orchestrator/campaign/p3_s4_loop.py`。harness は `tools/mutation_harness.py`。

| ID | 変異 | 期待 |
|---|---|---|
| M1 | manifest membership の要求を削除する | KILLED (負例 test が赤) |
| M2 | membership 判定を `registry.scheduled_attempts` の走査へ置換し恒真化する | KILLED |
| M3 | membership の件数要求を `>= 1` から `>= 0` へ緩める | KILLED |
| M4 | `B4_PROPOSAL_BINDING_NON_GUARANTEES` の項目 3 を旧文言へ戻す | KILLED (exact pin test) |
| M5 | membership 検査を hash 照合の**後**へ移す | SURVIVED を期待 (順序は受理集合を変えない。等価変異として登録) |

期待 node は段 6 の probe 実測から機械生成し、初回登録は probe ledger に残す (DW-M08)。

## 6. 段 5 の分割

実装は 1 単位。編集 path は
`orchestrator/campaign/p3_s4_loop.py` と `orchestrator/tests/test_p3_b4_proposal_binding.py` のみ。
Codex `role=author`、`sandbox=workspace-write`、`reasoning=xhigh`。親は実装面を直接編集しない。
