# 段 4 裁定 — [T-2067] (a) oracle report / verdict / judge へ選択 identity の強制

親が段 2 プランと段 3 敵対相談 2 本 (レンズ A = 正しさ境界 / レンズ B = 閉包と取り残し) を読み、
争点を現物で検算した上で裁定する。**この file が段 5 以降の正本である。**

## 0. 用語の注意

レンズ B は `real` / `refuted` の向きを親の指定と逆に使っている
(親の指定: real = 親の前提は誤り / refuted = 親の前提は妥当)。
**以下の判定は親が内容で読み直したものであり、子のラベルをそのまま採らない。**

## 1. 採用する所見 (must-fix)

### MF-1 負例の earlier result は走査中立にする (レンズ A 所見 1、親が検算して採用)

- **判定: real。** プラン `## 変更 2` ほかは、選択済み `result.json` の bytes をそのまま
  earlier path へ複製する。
- **親の検算**: `orchestrator/campaign/s8b_ratified_freeze.py:3516-3543` で
  `_launch_validate` は `search_repository` の全 repo 走査 hit と closure 導出 hit の
  **完全一致**を要求し、不一致で `closure-hit-mismatch` を投げる。
  複製した result は workload 軸の語を含むため未申告 hit になる。
- **なぜ問題か**: 3 経路は強制の直後に `reverify_published_freeze` を呼ぶ。
  強制の 1 行を消しても reverify が同じ入力を拒否するので、負例が
  「この 1 行を消すと受理される入力」にならない。DW-M01 の単一帰属 (前後・内側に
  同じ入力を拒否する層が無いこと) が成立しない。
- **既存先例がなぜ緑か**: `test_s8b_oracle_manifest.py:1499` の先例は
  `build_approved_manifest` 経路で、reverify を呼ばないため走査に当たらない。
  **先例をそのまま写すと本 wave では壊れる。**
- **裁定**: earlier path へ置く bytes は走査中立にする
  (`orchestrator/tests/test_s8b_ratified_verify.py:838-855` が使う `b"{}"` が先例)。
  eligibility は `_derive_floor_selection_eligibility` の差し替えで True にするので、
  内容が空でも負例は成立する。
  **実装子は、強制の 1 行を消したときに当該入力が受理される (rc=0 まで到達する) ことを
  実際に確かめてから負例を確定すること。** 確かめられない経路があれば止めて親へ報告する。

### MF-2 verdict の既存 2 テストは純 no-op でなく D1504 の記録 stub にする (レンズ A 所見 2 / レンズ B、採用)

- **判定: real。** プラン `## 変更 6` は
  `test_cli_rejects_non_verdict_oracle_schema_without_output` (1131 行) と
  `test_cli_rejects_freeze_identity_mismatch_before_consumers` (1195 行) で
  選択強制を**単純 no-op** へ差し替えることを提案している。
- **親の検算**: 両テストは `orchestrator/tests/test_s8b_verdict.py:1147-1152` で
  `load_ratified_freeze` を `lambda root: object()` へ差し替えている。
  実強制を入れると `object()` が exact 型検査 (`s8b_ratified_freeze.py:3583-3588`) で落ち、
  `rc == 2` は満たすが理由が別物になる (偽陽性)。プランの指摘自体は正しい。
- **決定済みの裁定がある**: **D1504** が同型を既に裁定している。
  「選択 assert だけを『呼出しを記録して何もしない stub』へ差し替えて、各 test に
  呼出し回数と引数を検査させる」ことを決め、**「loader と選択 assert の両方を stub する —
  機構を一度も通らない緑になる」を名指しで却下**している。
- **裁定**: 純 no-op は不可。**呼出しを記録する stub** にし、各テストで
  `selection_calls == [(loaded_ratified, root)]` を検査する
  (`loaded_ratified` は loader stub が返したその object であること、
  `root` は `Path` として完全一致であることを明示する)。
  機構そのものの証明は MF-1 で直す実 g1 の正例・負例が担う。
  **これは規律 2 に抵触しない** — production の gate は一切弱めず、
  既存の単体テストが本来の検査点へ届くようにするだけで、かつ呼出し記録という検査点を増やす。

### MF-3 変異の期待 node に pin test を含める (レンズ B 所見 2、採用)

- **判定: real。** 親の追補 §1 と F226 のとおり、`s8b_oracle_report.py` /
  `s8b_oracle_judge.py` への**どんな**変異も `PIN_GATE_SPEC_RAW` の golden を巻き込む。
- **裁定**: 変異事前登録 (下記 §4) で、R / J の全変異の `expected_nodes` に
  `test_s8b_oracle_manifest.py::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal` と
  `test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`
  を含める。V の変異には含めない (`s8b_verdict.py` は `_GENERATOR_SOURCES` 外)。
  期待 node の確定値は probe 走の実 collection から取る (推測で書かない)。

## 2. 採用する所見 (記録の訂正、コード変更なし)

### C-1 非 g1 は「受理される」ではない (レンズ A 所見 3、採用)

- **判定: real。** 親の brief は「`generation_number != 1` は素通りするので受理は変えない」と書いた。
  素通りするのは強制関数だけで、その直後の `reverify_published_freeze` が
  `s8b_ratified_freeze.py:3126-3129` で非 g1 を `certificate-generation-scope` として拒否する。
- **裁定**: コードは変えない。**worklog と受理集合の記述を訂正する。**
  正しい記述は「本強制は非 g1 では何も観測せず返る。非 g1 が 3 経路で受理されないのは
  従前どおり後段 reverify の責務であり、本 wave はそこを変えない」。
  実装子は非 g1 を「正例」として書かないこと。

## 3. 却下する所見

### R-1 新規 node の real-repo 登録は本 wave では不要 (レンズ B 所見 1、却下)

- **子の主張**: `build_production_emitter_g1` は親 working tree を読むので、新規 node を
  `conftest.py` の real-repo 登録簿と `test_real_repo_serialization.py` の独立 golden へ
  登録する必要があり、R/J/V の編集面が素集合でなくなる。
- **親の検算**: ヘルパが `_ROOT` を読むのは事実である
  (`orchestrator/tests/test_s8b_ratified_freeze.py:613-637`)。
  **しかし登録が要るという結論は現物と矛盾する。**
  - `orchestrator/tests/conftest.py` に `test_s8b_ratified_freeze.py::` の node は 1 件も無い。
    ヘルパを持つ suite 自身が未登録である。
  - 既存の先例 `test_s8b_oracle_manifest.py::test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate`
    (1485 行) と `..._real_g1_rule_mismatch_preserves_selection_reason` (1499 行) も未登録である。
  - 登録簿は `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
    が独立 golden と **exact 一致**で検査しており、今日緑である。
    登録が要るなら既存 2 件で既に赤になっているはずである。
- **裁定**: **本 wave の must-fix にしない。** 同じヘルパを使う既存 node と同じ扱いにする。
  子が挙げた「走行中に land が bytes を変える」懸念は、既存先例にも等しく当てはまる
  既存の性質であり、本 wave が持ち込むものではない (DW-G03: 族一般化は独立 2 例が要る)。
- **ただし実測で確かめる**: 段 6 の焦点走に
  `orchestrator/tests/test_real_repo_serialization.py` を必ず含める。
  ここが赤なら判断が誤りなので、その時点で親へ戻す。**静的読解の判断であり実測ではない。**

### R-2 public library 経路の迂回は残件 (c) の射程 (レンズ B 所見 3 / 取り残した層、本 wave では却下)

- **子の主張**: `verify_manifest` が選択未強制の freeze から封印 token を発行でき、
  `build_observations` → `judge_oracle` → `verify_oracle_verdict` → `judge_combined` を
  library として呼べば 3 CLI の gate を通らずに同種の official artifact へ到達できる。
  レンズ A も「API 非対称は実在する」と同じ結論を独立に出した。
- **親の判定**: **指摘自体は real。** しかし本 wave の scope 外である。
  - D1526 が名指ししたのは report / verdict / judge の 3 経路である。
  - 公開迂回口の一般化は**残件 (c)** (`build_manifest` / `write_manifest` の公開迂回口) の主題で、
    「(a) の着地後に続く」と台帳で決まっている。
  - repo 内の production caller は現に 3 CLI に閉じており
    (`test_s8b_oracle_manifest_contract.py` の `VERIFY_EXPECTED_CONSUMERS` が
    4 file の完全一致で pin しているので、新 consumer は inventory を赤にする)。
- **裁定**: 実装しない。**worklog の残件 (c) へ、両レンズが独立に同じ非対称を指摘した事実と
  到達経路 (上記の 4 段) を書き残す。** 「全層の非対称を閉じた」とは主張しない。

## 4. 割れうる前提の確定

- **(P1) `verify_manifest` に選択 token を要求させない — 確定。**
  両レンズとも「API 非対称は実在するが、D1526 の 3 経路実装へ token 化を足す根拠にはならず、
  公開 API 閉包は残件 (c) 側」と独立に結論した。親もこれを採る。
  追加材料として、token 化は
  `test_s8b_oracle_manifest_contract.py::test_verify_manifest_public_and_seal_wrapper_signatures_require_approved_spec`
  の signature pin と 4 file 全部の呼出しを巻き込む。
  **D1526 の「防壁の非対称を残す」という理由に対しては、R-2 のとおり
  「3 経路は閉じた、library 経路の非対称は残っており (c) の主題である」と正直に記録する。**
- **(P2) verdict は凍結 pin を動かさない — 確定。** 両レンズが独立に同じ結論。
  `_GENERATOR_SOURCES` は 5 file だけで verdict を含まず、verdict の source hash を焼く
  literal も repo に無い。
- **(P3) 挿入位置は `load_ratified_freeze` 直後 / `reverify_published_freeze` の前 — 確定。**
  両レンズが独立に同じ結論。reverify 内部へ移すと D1503 と
  `test_s8b_ratified_verify.py:1173-1178` の historical 成功契約を壊す。
  後段へ置くと別理由が先に発火して到達と理由を固定できない。

## 5. 変異の事前登録 (DW-M01、実装前に確定)

本 wave は**受理集合を縮小する**ため、負例に加えて**過剰拒否の正例 (positive control)** も登録する。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| MUT-T2067A-R1-REMOVED | `s8b_oracle_report.py` 強制行 | 行を `pass` へ | KILLED |
| MUT-T2067A-R2-DOCUMENT-ARG | 同上 | 第 1 引数を `ratified.document` へ | KILLED |
| MUT-T2067A-R3-WRONG-ROOT | 同上 | 第 2 引数を別 path へ | KILLED |
| MUT-T2067A-J1-REMOVED | `s8b_oracle_judge.py` 強制行 | 行を `pass` へ | KILLED |
| MUT-T2067A-J2-DOCUMENT-ARG | 同上 | 第 1 引数を `ratified.document` へ | KILLED |
| MUT-T2067A-J3-WRONG-ROOT | 同上 | 第 2 引数を別 path へ | KILLED |
| MUT-T2067A-V1-REMOVED | `s8b_verdict.py` 強制行 | 行を `pass` へ | KILLED |
| MUT-T2067A-V2-DOCUMENT-ARG | 同上 | 第 1 引数を `ratified.document` へ | KILLED |
| MUT-T2067A-V3-WRONG-ROOT | 同上 | 第 2 引数を別 path へ | KILLED |
| MUT-T2067A-P1-STALE-PIN | `test_s8b_oracle_manifest.py` の report hash literal | 旧値へ戻す | KILLED (pin 2 node) |
| MUT-T2067A-PC1-OVER-REJECT | `s8b_ratified_freeze.assert_g1_floor_selection_identity` 冒頭 | 無条件に `RatifiedFreezeError` を投げる | KILLED (過剰拒否の正例。**期待 node は広い** — この関数を通る全テストが赤になる) |

規則:

- **R* と J* の `expected_nodes` には MF-3 の pin 2 node を必ず含める。**
- **V* には含めない。**
- `expected_nodes` の確定値は **probe 走の実 collection から取る**。手で数えて書かない
  (無名 parametrize の自動採番がずれる型がある)。
- 各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する。
  MF-1 を直さないと R1 / J1 / V1 でこれが成立しない。
- 変異走行中は repo を 1 byte も触らない。spec と out は checkout の外へ置く。

## 6. 段 5 の分割 (確定)

| 単位 | 所有 path |
|---|---|
| R | `orchestrator/campaign/s8b_oracle_report.py`, `orchestrator/tests/test_s8b_oracle_report.py` |
| J | `orchestrator/campaign/s8b_oracle_judge.py`, `orchestrator/tests/test_s8b_oracle_judge.py` |
| V | `orchestrator/campaign/s8b_verdict.py`, `orchestrator/tests/test_s8b_verdict.py` |
| P | `orchestrator/tests/test_s8b_oracle_manifest.py` (再 pin のみ) |

- R / J / V は並列。**P は R と J の source bytes が確定してから親が投入する。**
- 共有ヘルパ (`test_s8b_ratified_freeze.py`、`s8b_holdout_freeze.py`、
  `test_s8b_oracle_report.py::_ratified_cli_manifest`) は**読み取り利用だけ**とし、
  どの単位も編集しない。J / V が report test の helper を import する場合も signature を変えない。
- 新しい test file を作らない (自走 harness と所要時間台帳の登録が要るため)。既存 file へ足す。

## 7. 不変条件 (再掲、実装子が守る)

- 規律 2 を緩めない。正しさゲートは強くする方向にしか動かさない。
- D1241 / D1313 の advisory / non-certifying 上限を解除しない。
- 仮想リスク向けの gate・検査・台帳・framework を足さない。本題の実装だけ。
- テストを甘くして緑にしない。再 pin は「実 file から再計算した値へ更新する」形にする。
  golden を live 計算へ置き換えて自己追随させることは禁止。
- 残件 (b) (c) (d) を実装しない。
- docs 編集・commit・push はしない (親が行う)。
