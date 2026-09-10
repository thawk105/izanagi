## 1. 所有と bytes 不変

- **refuted 候補 — 所有外変更。**
  - file:line: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:33,746-792,831-837`、`orchestrator/tests/test_floor_pair_driver.py:52-76,155-203`、`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:9-18,42-80,206-254,477-564`
  - `git diff HEAD --name-only` は裁定 §3 の 3 file だけ。`orchestrator/campaign/floor_pair_driver.py` の差分は空で、`git diff --check` も rc=0。
  - 影響: 所有外 bytes、schema、production driver は変わらず、成果物形式や land 面は増えない。
  - 推奨: **nit**。現状維持。

- **refuted 候補 — 既定 receipt bytes の変化。**
  - file:line: `test_floor_pair_driver.py:31-38,52-76,110-152,155-203,1093-1109`
  - 既定値では `g_new(tag,None) = json.dumps({"fixture":tag}, sort_keys=True, separators=(",",":")) = g_old(tag)`。従って `variant_id_new = sha256(f"{g_new}|src={src_token}")[:12] = variant_id_old`。binding、receipt、返却辞書の挿入順は不変で、外側も同じ `_canonical(record) + b"\n"`。さらに `_canonical` は `sort_keys=True` なので、JSON key 順にも差は出ない。
  - 読み取り専用計算でも candidate は 3095 bytes / `ce43374176abdad407277a6ea57cebdd8764c3b329401de0454c57307999886a`、reference は 3095 bytes / `f1795d7826746e7fa796beb034b9b3a09853659b95b992907a1ed120dd9675be` で、完了報告と一致。
  - HMAC golden は `test_floor_pair_driver.py:1093-1109` で `_write_inputs(tmp_path)` を追加引数なしで呼ぶため、receipt hash、spec bytes、spec SHA、HMAC 入力の全てが従前と同一。
  - 影響: golden 順序、既存 driver test、成果物 bytes は変化しない。
  - 推奨: **nit**。追加修正不要。

## 2. pin 閉包

- **real 候補 — 台帳には新 5 nodeid が未登録。**
  - file:line: `acceptance_duration_ledger.json:9334,9343,19765`、`test_p3_b4_floor_artifact_issuer.py:206,477-518,546`
  - 変更後 nodeid は次の全 5 件:
    - `...::test_real_finalize_floor_summary_is_issued_with_receipt_protocol`
    - `...::test_identity_is_not_a_caller_surface_and_noncanonical_genomes_are_rejected[json-fixture]`
    - `...::test_identity_is_not_a_caller_surface_and_noncanonical_genomes_are_rejected[unsorted-flags]`
    - `...::test_mixed_receipt_protocols_are_rejected`
    - `...::test_authority_value_rejects_nonempty_missing_protocol_with_valid_identity`
  - 台帳には旧 2 件 `...accepted_before_missing_protocol_blocks_issue` と `...missing_protocol_is_named` が残る。新 5 件は存在しない。
  - 自走 harness はファイル全体を pytest 収集するため名前 pin ではない (`test_p3_b4_floor_artifact_issuer.py:774-780`)。README も一般規則のみ (`README.md:105-120`)。`test_ccbench_spawn_sites.py:29-32,518-529` は production tree、`test_official_perf_closure.py:619-644` は別の明示 authority 群を走査する。issuer 内 source 走査と呼ばれた test も実際には変更のない `floor_pair_driver.py` だけを読む (`test_floor_pair_driver.py:3112-3121`)。
  - 旧名は `output/insights/2026-09-08_b4-floor-issue-wire/mutation-spec-final.json:179` 等にも残るが、履歴証拠であり現行自走 pin ではない。
  - 影響: duration は新 5 件で既定値になるが、収集・実行自体は失われない。
  - 推奨: **nit**。裁定どおり台帳は触らず、受入時の実収集で再確認する。

- **refuted 候補 — 5 件の未登録で 90% gate を割る。**
  - file:line: `test_acceptance_schedule_order.py:704-714`
  - 現台帳は宣言値・実 key 数とも 19,761。旧 2 件を失い新 5 件へ置換した wave 差分計算は `19,759 / 19,764 = 99.974701%`。t2412 の台帳 snapshot 19,764 を基準に合成しても `19,762 / 19,767 = 99.974704%`。
  - 影響: 本 wave の nodeid 差分だけでは 90% gate を割らず、台帳無編集は land blocker にならない。
  - 推奨: **nit**。これは静的な差分計算であり、pytest collection は未実走と明記したままにする。

## 3. t2412 との衝突面

- **refuted 候補 — exact 変更行の隣接衝突。**
  - file:line: `test_floor_pair_driver.py`、`test_p3_b4_floor_artifact_issuer.py`
  - `-U0` の base-side hunk は次のとおり。
    - t2412 driver test: `-14,0; -26,2; -309,3; -315,0; -323; -325,5; -331,0; -364,0; -372; -379; -423,0; -472,3; -698; -704,0; -721; -737,3; -742; -747,0; -749; -996,12; -1009; -2003,3; -2014`
    - 本 patch driver test: `-56,0; -60,2; -152; -168; -174`
    - t2412 issuer test: `-109`、`-509,0`
    - 本 patch issuer test: `-8,0; -16,0; -39,0; -48; -52; -56,8; -67,18; -217; -222,0; -244,7; -473; -475,0; -486; -499,0; -505; -557; -578; -623; -652`
  - driver 側の最短でも base 27 と 56 の間に 28 行、issuer 側は base 505 と 509 の間に 506-509 の未変更行がある。定義どおりの隣接は 0 件。
  - 影響: 通常の three-way merge で直近行競合になる箇所はなく、land の text conflict は予測しない。
  - 推奨: **nit**。統合後に同じ `-U0` 検査を再実行する。

- **refuted 候補 — `_install_git` と `loaded_head` の意味的破壊。**
  - file:line: `test_p3_b4_floor_artifact_issuer.py:65-73,93-99,567-600`、t2412 base `test_floor_pair_driver.py:309-343`、t2412 base issuer test `:109,509`
  - t2412 は `_install_git` を `blob_overrides` / `ancestor_returncode` 付きへ変更するが、本 patch の caller は `_install_git(monkeypatch, root)` の位置引数だけ。新 `_write_inputs(root, *, genome_canonicals=None)` も既存 t2412 caller と後方互換。
  - t2412 の `loaded_head = driver_tests.HEAD` は、同じ偽 Git が返す resolved HEAD と一致する。追加される `parsed_spec.loaded_head` 検査も、canonical receipt を含む同一 spec bytes を読む。
  - 影響: 両 wave 着地後も spec byte、receipt byte、loaded-head の結合は壊れず、追加 assertion は成立する見込み。
  - 推奨: **nit**。統合後焦点走でのみ最終確認する。

## 4. 変異の帰属と anchor

以下の anchor は全て対象 production file 内で 1 件だけだった。mutation harness は `tools/mutation_harness.py:1081-1089` で一意性を、`:2097-2099` で失敗 node 集合の完全一致を要求する。

- **M1 refuted 候補** — `p3_b4_floor_artifact_issuer.py:780`、count=1。完全集合は正例 `test_real_finalize_floor_summary_is_issued_with_receipt_protocol` だけ (`test...py:206,242-254`)。
  - 影響: env tag 置換は mocc assertion が確実に殺し、予測外赤は見当たらない。
  - 推奨: **nit**。

- **M2 refuted 候補** — 同 `:780`、count=1。定数 `silo` も同じ正例 1 node が殺す。
  - 影響:期待集合は完全。
  - 推奨: **nit**。

- **M3 refuted 候補** — `p3_b4_floor_artifact_issuer.py:791`、count=1。完全集合は `test_mixed_receipt_protocols_are_rejected` (`test...py:518-543`)。
  - 影響: mixed set が identity 化されるため当該 node だけが赤になる。
  - 推奨: **nit**。

- **M4 refuted 候補** — `p3_b4_floor_artifact_issuer.py:780`、count=1。完全集合は `[unsorted-flags]`。JSON fixture は `_identifier` の canonical ID 検査 (`issuer.py:268-272`) でも拒否される。
  - 影響: naive split の固有検出力は未整列 case が保持する。
  - 推奨: **nit**。

- **M5 refuted 候補 — 登録可能という主張。**
  - file:line: issuer anchor `:767` は count=1 だが、producer が先に `_read_tracked_bound` で SHA を拒否する (`floor_pair_driver.py:581-597,1101-1107`)。
  - 影響: public 経路では issuer anchor に到達せず、登録すれば帰属偽陽性になる。
  - 推奨: **nit**。完了報告どおり登録しない。将来別 wave で扱うなら producer 側 `floor_pair_driver.py:590` が代替照準。

- **M6 real 候補 — expected node 集合が不足。**
  - file:line: anchor `p3_b4_floor_artifact_issuer.py:932`、tests `test...py:206-254,644-666`
  - segment 削除は `test_authority_filename_contains_all_five_derived_components` に加え、正例の `assert "__protocol-mocc" in ...` も赤にする。完全集合はこの 2 node。
  - 影響: 1 node だけで登録すると mutation harness は KILLED でなく MISMATCH となり、受入証拠を閉じられない。
  - 推奨: **must-fix**。M6 の expected nodes に正例 node を追加する。

- **M7 refuted 候補** — anchor `p3_b4_floor_artifact_issuer.py:900`、count=1。完全集合は guard test (`test...py:546-564`)。
  - 影響: 有効 identity を使うため downstream crash に過剰決定されず、意図した guard だけを検出する。
  - 推奨: **nit**。

- **M8 real 候補 — mutant 定義と expected node 集合が不完全。**
  - file:line: anchor `p3_b4_floor_artifact_issuer.py:792`、negative tests `test...py:477-515,518-543`
  - 「全 receipt 失敗時に空 protocol identity」を正しく作れば、JSON と unsorted の両 parameter node が赤になる。単に `missing.append("protocol")` を削除すると `next(iter(protocols))` (`issuer.py:807`) が `StopIteration` となり、両 parameter nodeに加えて mixed node も赤になる。
  - 影響: 現報告の `[json-fixture]` 1 件では MISMATCH になり、しかも単純削除では狙った空 identity の帰属を証明しない。
  - 推奨: **must-fix**。`if protocol_failed or len(protocols) != 1:` と `protocol=next(iter(protocols))` を組み合わせた明示的な 2-anchor mutantにし、少なくとも両 parameter node を期待集合へ入れる。

## 5. 完了報告の裏取り

- **refuted 候補 — 実走数、bytes、所有、波及の虚偽。**
  - file:line: `s5-author.md:15-19,27-47,70-79`
  - issuer の静的 node 数は AST 上 23。実走は報告どおり 0 で、pytest 緑は申告されていない。既定 bytes、3-file 所有、`floor_pair_driver.py` 無変更も現物と一致する。
  - 影響: テスト未実走という留保を維持する限り、land 状態を過大申告していない。
  - 推奨: **nit**。

- **real 候補 — M6/M8 の完了報告が現物と食い違う。**
  - file:line: `s5-author.md:63-68`、`test_p3_b4_floor_artifact_issuer.py:206-254,477-543,644-666`
  - M6 は 2 node、M8 は意図した mutant でも 2 node が必要で、報告の各 1 node は不完全。
  - 影響: そのまま変異登録すると land 用 mutation evidence が MISMATCH。
  - 推奨: **must-fix**。§4 の完全集合へ訂正する。

- **real 候補 — malformed／欠落／artifact 空の到達性説明が広すぎる。**
  - file:line: `s5-author.md:10`、`p3_b4_floor_artifact_issuer.py:839-869`、`floor_pair_driver.py:581-597,700-701,1052-1107`
  - public loader は `_derive_identity` より先に producer validator を通すため、壊れた JSON、binding 欠落、artifact 空は通常 `missing=("protocol",)` ではなく spec rejection。noncanonical genome、mixed、検証後の TOCTOU は missing 経路に到達する。
  - 影響: fail-closed 性は弱まらないが、受理済み summary として返る範囲を報告が過大に記述している。
  - 推奨: **nit**。内部 helper の防御挙動と public 到達経路を分けて記載する。

- **refuted 候補 — docstring の根拠不一致。**
  - file:line: issuer `:746-751`、driver `:759-776,1136-1147`、issuer `:412-433`
  - cells は nonempty、全 cell の threads/workload は同一 verified calibration に一致し、campaigns は nonempty。現物は docstring の主張と一致。
  - 影響: threads/workload/campaign の missing 分岐削除は受理集合を広げない。
  - 推奨: **nit**。

## 6. 循環 import と実行経路

- **refuted 候補 — 直接 CLI または package import の破壊。**
  - file:line: `p3_b4_floor_artifact_issuer.py:28-33`、`genome.py:17,223-251`、`model.py:14-20`
  - 直接 CLI は repo root を `sys.path` に入れ、`__package__ = "orchestrator.campaign"` を設定してから両 relative import を行う。package import も同じ相対解決になる。`genome.py` は `model.py` を importするだけで、両 file から issuer への逆 import はない。
  - 読み取り専用 smoke でも直接 `--help` と package import はともに rc=0。
  - 影響: 循環 import や起動前失敗で issuer CLI、受入、land が壊れる経路は見つからない。
  - 推奨: **nit**。

## 総括
- must-fix 候補は **2件**: M6 の期待集合不足、M8 の mutant 定義と期待集合不足。
- 最大の懸念は M8 が狙った意味を作らず、複数の予測外 node を赤にして MISMATCH になる点。
- 完了報告との食い違いあり: M6/M8 の expected nodes。bytes、所有、静的 23 node、未実走申告は一致。
- 裁定パッケージ候補あり: protocol allowlist / source 束縛のみ。現 wave では実装対象外。