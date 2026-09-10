# 段 4 裁定 + plan v2 — [T-816] 手順 4 (dev-wave-t816-step4-impl)

base main `a70a5acd` / branch `worktree-dev-wave-t816-step4-impl`。
本書が段 5 実装子・段 6 レビュー子の上位契約である。**file:line は前 wave (base `23c8e7c4`) 時点の
ものを含む。実装子は本 wave の HEAD で必ず再確認し、ずれていたら行番号でなく識別子で同定すること。**

## 0. 上位裁定 (ユーザー確定・攻撃対象外)

正本 = branch `worktree-rulings-20260812-coarse-provenance` の worklog fragment [T-816] 項
(基準 = {{D:coarse-provenance-standard}})。

- **Q1** = trace は **v2 専用**。赤になる凍結 v1 証拠テストは**退役** (歴史記録は日付級の 1 行)。
  **v1 読み手の hash 束縛例外機構は作らない。**
- **Q2** = **検査で現用の校正 pin だけ**を新 gitlink で機械的に再 pin し、**未使用は退役**。
  **恒久の同一性証明機構は作らない。**
- 乗せ直しは省略、gitlink を `511c9538` へ直接前進。[T-837] は終端。

不変: 絶対規律 1〜6。**受理集合を緩める方向の変更は一切しない** (本 wave は縮小方向のみ)。

## 1. 親の実測 (一次資料 = 本 job dir)

| # | 事実 | 値 | 出所 |
|---|---|---|---|
| 1 | gitlink 現在値 | `d706650c…` | `git ls-tree HEAD external/ccbench` |
| 2 | `511c9538` は push 済み | 真 (`refs/heads/izanagi-trace-t816-fn2`) | `git ls-remote` |
| 3 | pin 前進の submodule 差分 | **`cc/silo/transaction.cc` 1 file / +14 -1 のみ** | `git diff --stat` |
| 4 | gitlink + 承認定数 2 個だけの赤 | **`10 failed, 78 passed, 1 error in 23.96s`** | `measure-pin-advance.log` |
| 5 | 赤 10 件の所在 | **全件 `test_s8a_trigger_sweep.py`** (原因 1 つ = 校正 JSON の `ccbench_commit`) | 同上 |
| 6 | error 1 件 | `test_s8b_approved.py` の **collect error = 偽赤** (`No module named 'tests'`、DW-O18) | 同上 |
| 7 | s1-freeze 2 本・`test_frozen_artifacts`・rung1 evidence | **pin 前進だけでは緑** (実 artifact を検査が読まないため) | 同上 |
| 8 | tracked な trace ログ | **4 本のみ** (凍結 rung1 raw bundle の `trace_0..3.log`、v1) | `git ls-files` |
| 9 | 実 v1 bytes を verifier へ通す test 経路 | `test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` (helper `_assert_raw_correctness:1061`) | 静的同定 |
| 10 | 同じ再検証の production 経路 | `silo_ladder_rung1.py:2858-2860` (`validate_raw_bundle`)。呼び手は自分の campaign flow のみ (`:4800`, `:4857`) → 新規 bundle は前進後 v2 | 静的同定 |
| 11 | TRACE=0 preprocess 同一性 (g++-12) | `identity-g++-12.log` (段 5 投入前に rc=0 を確認) | 親実行 |

## 2. 親の裁定 (P 付きは provisional = 段 6 レビューの攻撃対象)

### R1 — 「現用 = 機械再 pin」の対象 (Q2 の適用)

| artifact | 判定 | 根拠 |
|---|---|---|
| `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json` | **現用 → 再 pin** | 実測 5 (検査 10 件が赤)。`s8a_trigger_sweep.py:151` が live `PIN` と exact 比較 |
| `output/s1-freeze/known_axes_freeze.json` | **現用 → 再 pin** (P1) | `s1_known_axes_freeze.py:869` が実 submodule HEAD と比較。生きた呼び手 `s8b_oracle_driver.py:429` (段 8b oracle は現行作業) |
| `output/s1-freeze/measurement_freeze.json` | **現用 → 再 pin** (P1) | `s1_measurement_freeze.py:429` が `pin.CURRENT_PIN` と比較。生きた呼び手 `s1_report.py:790` |
| `patches/ledger.json:10` `base_commit` | **現用 → 再 pin** | `silo_ladder_rung1_contract.py:543` が exact 比較 |

(P1) の理由: 裁定文の「検査で現用」を*検査が赤にするもの*に限ると、s1-freeze 2 本は再 pin されず
段 8b oracle / s1 report が実行時に fail-closed refusal を出す。実測 7 の「緑」は**検査が実
artifact を読まないため**であって未使用の証拠ではない (前 wave も同じ結論)。再測定はしない —
実測 3 + 11 (差分は `#if TRACE` 内のみ、TRACE=0 の preprocess 出力が同一) が根拠。
**恒久機構は作らない** — 一度きりの値の書き換えだけで、pin 集合を持つ gate も同一性証明 field も
新設しない。

### R2 — 「未使用 = 退役」の対象 (再 pin しない)

`s8a_trigger_gating_coverage.json` / `s5_permutation_coverage.json` / `s1_verify_extime.json` は
`d706650` を持つが pin を比較する consumer が存在しない (実測: producer 以外の参照ゼロ)。
**値を触らず、歴史記録として据置**。docs に日付級 1 行だけ残す (親が書く)。
`output/campaigns/**` の 216 file 群は各 campaign 自身の pin を記録する歴史記録であり対象外。

### R3 — 凍結 v1 証拠の退役 (Q1 の適用)

- **凍結 raw bundle の bytes は 1 byte も変えない** (proof chain を書き換えない)。
- 退役するのは**実 v1 bytes を現行 verifier へ通す再検証だけ**。実測 9 の 1 経路が該当。
  `_assert_raw_correctness` から `verify_trace_dir` の再計算と
  `recomputed == recorded_result` の assert を外し、**記録済み `verifier.json` を読む
  `_correctness_passes` は残す**。build / compile_commands / attestation / seal の検査は全て残す。
- 退役箇所には日付級 1 行のコメントを置く:
  「2026-08-12 [T-816] trace v2 専用化により、この凍結 bundle (d706650 期・v1) の trace 再検証は退役。
  bytes と記録済み verifier 結果は不変。」
- **合成 fixture (test_silo_ladder_rung1_driver.py 等) は退役せず v2 へ移行する。**
- 裁定文の「4 本」は凍結 raw trace が 4 本であることに由来すると解する。退役対象は
  「v2 専用化で赤になるもの全部」であり、件数は段 6 の実測で確定して worklog へ書く
  (実測と裁定文の件数が違っても、**多い側に合わせて全部退役**する。少ない側で止めない)。

### R4 — 歴史再現 driver (`s2_verify_calibration.py`)

自分の literal pin `dff0f1e` (v2 以前) から build するため出力は必ず v1 で、v2 専用化後は
correctness leg が再現不能になる。ただし**検査は赤にならない** (test は subprocess を mock する)。
コードは触らず、`docs/phase3.md` の再現経路記述に日付級 1 行を足す (親)。
**削除しない** — `materializer_admission.py:32` / `test_p3_build_authority_cli.py:67` /
`test_build_site_gate.py` が build-site gate の実体として参照しており、削除は scope 外の破壊になる。

### R5 — 段 3 の real 所見 6 件

| # | 所見 | 裁定 | 成果物影響 (DW-G05) |
|---|---|---|---|
| 1 | 負 txid で false-green certified (`parse.py:213`) | **real / 採用 / scope 内** | 未対応なら負 txid trace が `certified=True` になり、**偽の certified 選択結果**が台帳へ入る |
| 2 | cycle と framing 共存時の verdict 優先順位 | **real / 採用** = cycle 優先 (`model.py` 現行分岐順を維持) を正式契約にする | verdict 文字列が入れ替わると選択レポートの根拠記述が変わる。`certified=False` は両方で不変 |
| 3 | X/I 行を件数に数える誤り | **real / 採用** = R/W のみ計数、負例を追加 | 誤計数は clean な trace を framing 違反にし、**正しい variant を不当に落とす** |
| 4 | 直後でない重複 `E` が `ParseError` | **real / 部分採用** = 挙動は `ParseError` のまま (fail-closed で受理集合は安全側)。**テストで固定するだけ**とし構造化 issue へ格上げしない | 受理集合は不変。診断の粒度のみ |
| 5 | fixture 16 本の移行ミスが緑で残る | **real / 採用** = 全 fixture に `framing_violations == 0` を固定 | 移行ミスを見逃すと、以後の anomaly 検出力が静かに落ちる |
| 6 | `patches/README.md:356` の trace 形式記述が v1 | **real / 採用** (親が docs 編集) | 契約文書と実装の食い違いは次の実装者を誤らせる |

## 3. 実装単位と所有 (DW-S05-A、素集合)

**親が先に行う**: gitlink 前進 (`external/ccbench` を `511c9538` へ) を単独 commit。
実装子はこの commit を含む branch から worktree を作る。

- **単位 A = verifier v2 専用化** (所有):
  `orchestrator/verifier/parse.py`, `model.py`, `core.py`, `report.py`,
  `orchestrator/tests/test_verifier.py`, `orchestrator/tests/fixtures/**`
- **単位 B = pin 閉包 + 退役 + 下流 consumer** (所有):
  `orchestrator/campaign/**` (pin.py, s8b_approved.py, silo_ladder_rung1.py,
  silo_ladder_rung1_contract.py ほか), `patches/ledger.json`,
  `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json`,
  `output/s1-freeze/*.json`,
  `orchestrator/tests/` のうち **test_verifier.py 以外**

境界の契約 (両単位が守る): 新 integrity counter の名前は **`framing_violations`** (int、既定 0)、
`Integrity.clean()` に `framing_violations == 0` を追加。単位 B はこの名前を前提に
consumer 側 (exact key-set、acceptance、mirror) を閉じてよい。

## 4. 単位 A の実装契約

前 wave の段 2 プラン `output/insights/2026-08-12_t816-step4-blockers/verbatim/s2-plan.md` の
**§2 (parser/integrity)、§3 (fixture 16 本の機械移行)、§4 (test_verifier.py)** を**そのまま継承**する
(絶対パスで読むこと)。差分は次のとおり。

1. **v1 互換分岐・legacy reader を作らない** (Q1 で例外機構が否決された)。`C` は exact 7-field、
   5-field は専用 `ParseError`。
2. **R5-1 を追加**: `txid` は非負整数のみ受理。`C -1 …` は `ParseError`。
   負例 `{-1, 1}` (負値が `max(txid)+1` の欠番計算を相殺する形) を必ず入れる。
3. **R5-3**: `X` / `I` は R/W 件数に数えない。数えないことを固定する負例を入れる。
4. **R5-4**: 直後でない重複 `E` は `ParseError` のままとし、その挙動をテストで固定する。
5. **R5-5**: 移行した 16 fixture 全部に `framing_violations == 0` を固定する。
6. §3 の一時 converter は commit に含めない (実行・検証後に削除)。

## 5. 単位 B の実装契約

同 s2-plan の **§1 (pin 閉包の分類表 A=23 / B=19)、§5 (test_campaign.py の trace literal)** を継承し、
次を加える。

1. **pin 値**: 短 pin `511c953`、full `511c9538e4e8efa54b45cda62e72389ed3b706ec`。
   A 分類 (前進必須) だけを更新し、**B 分類 (歴史 preimage・固定 fixture・凍結 golden) は 1 文字も
   触らない**。`PREVIOUS_PIN` / `KICKOFF_PIN*` は据置。
2. **artifact の機械再 pin** (R1 の 4 件)。`output/s1-freeze/*.json` を書き換えたら
   `orchestrator/tests/test_frozen_artifacts.py:39,41` の `FROZEN_MANIFEST` の byte SHA も同時更新する
   (**hash を甘くするのではなく、実 bytes から再計算する**)。
3. **campaign-id / golden の再導出**: s2-plan §1 実装順 5・6 に従い、historical 集合を保持したまま
   current 集合だけを新 pin から再導出する。
4. **R3 の退役**を実装する (上記 R3 の逐語どおり。**他の assert を 1 つも消さない**)。
5. **下流 consumer**: s2-plan「report と downstream schema」の campaign 側
   (`silo_ladder_rung1.py` の acceptance と exact integrity key-set、
   `test_silo_ladder_rung1_driver.py`、`test_t152_write_intent_coverage.py`) を閉じる。
6. **合成 trace literal の v2 移行**: `test_silo_ladder_rung1_driver.py` ほかで
   `validate_raw_bundle` に渡す合成 trace も v2 化する (退役ではない)。

## 6. 変異事前登録 (DW-M01、B-057 harness)

段 6 の fix 後 anchor で old 逐語と**期待 node の完全集合**を再導出してから本走する (DW-M07/M08)。
各変異は「同じ入力を拒否する層が前後に無い」ことを実装子の完了報告と親の目視で確認してから登録を確定する。

| ID | 変異 (無効化する gate) | 期待 kill の性質 | 単一理由性 |
|---|---|---|---|
| M1 | `C` の 7-field 検査を 5-field も受理へ戻す | v1 拒否テストが緑→赤 | 前後に v1 を拒否する層は無い (parser が唯一) |
| M2 | 宣言 read/write 件数の照合を無効化 | 件数不一致テスト | 照合は `_parse_file` の 1 箇所のみ |
| M3 | EOF 時の `missing-end` 記録を落とす | E 欠落テスト | 他層に E 必須の検査は無い |
| M4 | 直後の重複 `E` の検出を落とす | 重複 E テスト | 同上 |
| M5 | `txid >= 0` の構文検査を外す | 負 txid 負例 (R5-1) | 欠番検査は相殺されるため後段は発火しない = 唯一の層 |
| M6 | `Integrity.clean()` から `framing_violations == 0` を外す | clean/verdict/certified 固定テスト | clean 判定は 1 箇所 |
| M7 | **正例 (過剰拒否検出)**: `C … 0 0` + `E` を拒否する変異 | `test_zero_read_zero_write_frame_is_valid` | 受理集合を縮小する wave の必須正例 (DW-M01) |
| M8 | `s8a_trigger_sweep.py:151` の `artifact_commit != PIN` を無効化 | 再 pin した校正 artifact の gate | pin 比較はこの 1 箇所 |

## 7. 想定赤と判別基準

s2-plan §6 の表を継承する。追加:

| 赤 | 分類 | 判別 |
|---|---|---|
| `test_s8b_approved.py` の collect error (`No module named 'tests'`) | **偽赤** (DW-O18) | import path 確立後に単独再走して消えること |
| rung1 evidence の correctness leg | **意図した退役** | 退役後は再検証せず、記録済み verifier JSON の検査だけが残る |
| s1-freeze verify の pin 不一致 | **意図した機械再 pin 漏れ** | 4 件全部を再 pin し `FROZEN_MANIFEST` も更新したか |
| 負 txid が certified のまま | **回帰** | R5-1 未実装。`ParseError` にする |

## 8. 停止条件 (この wave 固有)

- TRACE=0 同一性検査 (実測 11) が rc≠0 なら **R1 の (P1) が崩れる** → 段 5 へ進まず裁定へ戻す。
- 実 v1 bytes を verifier へ通す経路が実測 9 の 1 本より**大幅に多い** (例: 10 本超) と判明したら、
  退役規模が裁定の想定 (「4 本」) を大きく超えるため、親が止めてユーザーへ再確認する。
- 受理集合を**広げる**変更 (v1 を通す例外、gate の緩和、期待値の反転) は、どの単位でも即差し戻す。
