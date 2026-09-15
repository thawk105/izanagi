# [T-1851] / [T-1946] / [T-2107] 単位 C3c — official 床値の許可表を resolved protocol の実 path へ束縛した

branch `worktree-dev-wave-t1851-c3c-protocol-binding`、base `f5423e2fff3adb164731963ca33e82ed08d08c4d`
(着手直前の local main)。commit は `7e73d448e` (brief と裁定) → `388a6a8fb` (実装) →
`0bbd5b5be` (共有 repo reader の登録)。

**official 床値 campaign は投入していない。** 実値域の供給は後続に残した (依頼の明示)。

---

## 1. 直した欠陥

2026-09-09 に sanctioned 経路で投入した史上初の official 床値 campaign `988501.nqsv` は、
起動証明書で `launch certificate: freeze allowlist hash 不一致:
output/s8b-freeze/floor_protocol.json` により driver rc=1 で止まった
(`output/insights/2026-09-09/t1851-unit-c3b-floor-range/README.md`)。D1936 項 11 の案 a を実装した。

`_floor_preflight_freeze_allowlist()` は allowlist を
`allowlist[legacy 固定 path] = 実行 protocol の canonical sha256` と置いていた。実行時に resolver が
選ぶのは世代別 protocol であり、2 file は `ccbench_pin` 1 field だけ違う。したがって legacy file の
bytes hash が resolved protocol の canonical hash と一致することは構造的にありえない。

親が着手時に worktree 上で実測した値:

| 量 | 実測値 |
|---|---|
| `resolve_current_floor_protocol().path` | `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json` |
| 同 file の sha256 | `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a` |
| legacy 固定 file の sha256 | `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac` |
| 2 file の差 | `ccbench_pin` 1 field のみ |

**これは 2026-09-14 の 1 構成の観測であり、世代別 protocol 全構成の性質ではない。** 世代別の導出は
`contract_sha256` と `ccbench_pin` の両方を置換しうるので、一般の説明では `H_legacy` / `H_resolved`
を使う。

## 2. 実装した形

設計判断は D1936 項 11 の案 a を具体化した 2 件 —
`docs/spool/decisions/2026-09-14-dev-wave-t1851-c3c-protocol-binding-2.md` の 2 項目。

- allowlist は legacy anchor へ**その file 自身の bytes hash**を、resolved protocol の実 path へ
  **実行 protocol の canonical hash** を束縛する。同じ path なら 1 entry に畳む。
- allowlist の key として新たに受理してよいのは、呼び手が渡した `protocol_relpath` と
  **exact 一致する 1 件だけ**。命名規則・正規表現・prefix 一致では受理しない。選ばれていない
  世代別 protocol は従来どおり chain record に残る。
- `protocol_relpath` は公開入口が保持した authority record からのみ取る。下位関数は resolver を
  呼ばない。新 keyword はすべて既定 `None` で、`None` のときの受理集合・分類・digest は変更前と同一。
- private core の official 分岐は record 不在で legacy anchor へ fallback する。**record 不在を理由に
  official を拒否する fail-closed は置かない** — 非 test 呼び手は公開入口 1 箇所だけで、その入口は
  解決失敗時に例外を投げるため、fail-closed は production で発火しない。
- `historical_protocol` 比較 (pre_oracle_head の Git blob との一致) と journal の
  `expected_header.protocol_sha256` は現状維持。digest schema `s8b-clean-scan-digest/v3` と
  preimage の構成も不変。

**legacy entry の保証について。** legacy entry は「`pre_oracle_head` の Git blob と一致することを
直前に検査した bytes を、その後の 2 回の clean scan へ束縛する」ものである。**独立検証ではない。**
capture 前から存在する改竄は allowlist ではなく `historical_protocol` 比較が拒否する。

**凍結保留について。** capture と scan の間で bytes が不変な fresh official 経路では、
`s8b-floor.protocol-bytes-expected-pin` の有無で最終受理可否は変わらない。停止位置・marker・
bytes が途中で変わる時系列、および hold 機構全体の効力は本 wave の証明対象外である。

## 3. 親の実測

| 検査 | 結果 |
|---|---|
| 新規 5 nodeid (`-k "public_official_preflight or freeze_allowlist_path_rejects_unselected"`) | **5 passed** / 40.42s |
| `test_s8b_ratified_freeze.py` (fail-closed 初稿) | **28 failed** — Pegasus `996095.nqsv`、Elapse 11S |
| `test_s8b_ratified_freeze.py` (裁定 8 の fallback 後) | **82 passed** / 17.81s |
| 共有 repo reader 登録簿の gate 4 種 | **9 passed / 1 skipped** / 54.34s |
| `test_real_repo_serialization.py` 単独 | 55 passed / **1 failed** / 1 skipped |
| 同 file + `test_p3_s4_loop.py` の 2 file | **467 passed / 1 skipped** (赤が消える) |
| 実装前後の内容一致 (author worktree の tracked 24676 file) | 変更 **4 file** のみ、欠落 0、hash エラー 0 |

**`test_real_repo_serialization.py` の 1 failed は本 wave に帰属しない。** 変更面を基底
`7e73d448e` へ全部戻した状態でも同じ nodeid が 1 failed になり、対象 module を一緒に収集すると
消える。機序は F 台帳の新規項に記録した。

## 4. 変異 matrix

`tools/mutation_harness.py` の直接経路で 2 走した。**wrapper (`tools/mutation_worktree.py`) は
共有木の事後検査で rc=125 になり使えなかった** — 並行 session の churn が原因である。

- probe 走 (全件 SURVIVED 登録、実 node 集合の採取用): spec sha256
  `ddec9357ac15829702b9d2dc5a58d7e3c27c497a9dcacce875373062303a5d9e`。
- 本走: spec sha256 `e921aad50fe3911718bc2a82e1df662a6770589a9d43fce739332dfbc56b6073`、
  **baseline PASSED (失敗 0)、6/6 KILLED、期待 node 完全一致、rc=0、復元成功。**

逐語 spec と両走の結果は `mutation/` に無損失で収録した。nodeid の接頭辞は
`orchestrator/tests/test_s8b_floor_campaign.py::` で、略号は
P1=`test_public_official_preflight_accepts_versioned_protocol`、
P2=`test_public_official_preflight_accepts_legacy_protocol`、
N1=`test_public_official_preflight_rejects_resolved_protocol_byte_drift`、
N2=`test_public_official_preflight_rejects_legacy_byte_drift_after_capture`、
N3=`test_freeze_allowlist_path_rejects_unselected_versioned_protocol`。

| # | 変異 | 観測赤 node | 単一理由性 |
|---|---|---|---|
| M1 | 公開入口が authority record を渡さない | P1, N1, N2 | **不成立。** 公開配線の検査として記録する |
| M2 | legacy entry を削除し resolved への単純置換に戻す | P1, N1, N2 | **不成立 (冗長 gate)** |
| M3 | validator を世代別命名規則の族受理へ緩める | N3 | **成立** |
| M4 | resolved entry の期待値を capture の自己 hash にする | N1 | **不成立 (冗長 gate)** |
| M5 | 走査時の hash 比較そのものを無効化する | N1, N2 | **成立** |
| M6 | 選択された世代別 protocol を常に chain 分類へ落とす | P1, N1, N2, N3 | **不成立。** P1 の集合一致 gate へ限定して記録する |

**単一理由の kill として数えるのは M3 と M5 の 2 件だけである。** 他 4 件は変異を検出しているが、
赤の到達点が別の assertion なので、単独変異による特定 gate の証拠には数えない (DW-M03)。

**P2 はどの変異でも落ちない。** legacy resolution の経路が本変更で 1 bit も変わっていないことの
機械的な裏取りである。

**逐語の登録手順。** 段 4 は変異の位置と意味を登録した。置換用の逐語は実装後にしか確定しないので、
いずれの変異走よりも前に逐語を固定し、対象 file 内の出現が exactly 1 であることを機械検査した
(6/6)。焦点子が同じ計数を独立に再実行し一致した。

## 5. 段 3 と段 6 の所見

段 3 (敵対相談 2 レンズ) は real 6 / refuted 5、段 6 (敵対レビュー 2 レンズ) は real 5 / refuted 7。
**scope 外の real 所見は段 3・段 6 とも 0 件で、ユーザーへ返す裁定パッケージは無い。**
全所見の裁定は `s4-adjudication.md` にある (裁定 1〜7 が段 4、裁定 8 が実測で覆った前提の訂正、
裁定 9〜13 が段 6 所見の裁定)。

採用した主な是正。

- **受理集合の説明を訂正した。** allowlist key として受理する path は resolved path 1 件ぶん増える。
  「受理集合は 1 bit も広がらない」という初稿の表現は誤りだった。増える 1 件は resolver の権威
  (`_require_supplied_protocol_authority` と index scan の bytes 一致検査) が既に固定した path である。
- **plan v2 の fail-closed を撤回した** (裁定 8)。前提「official は必ず公開入口経由」が実測で偽だった。
- **共有 repo reader の登録簿を拡張した** (裁定 11)。新規 4 テストは実親 repo と実共有 submodule を
  clone 元として読むのに未登録だった。同 file の同型テストは既に登録済みで、未登録は慣例違反である。
- **正例の到達範囲を訂正した** (裁定 9)。実装が到達するのは launch certificate の構成と 2 回の
  clean scan と strict 検証までで、**証明書 file の発行段には到達しない。**
  テストは拡張しなかった — 988501 を止めた gate は preflight の allowlist であり、親と焦点子が
  独立に「preflight 以後に legacy 固定 path を束縛する consumer は無い」ことを確認した。

棄却した所見: legacy entry の自己 hash 化による恒真化 (必須経路の `historical_protocol` 比較が残る)、
世代別 protocol を有界集合へ移すことによる被覆欠落、負例が先行 gate に必ず遮られる、
裁定 8 の fallback が production を弱める、既存期待値の強制置換。

## 6. セッション異常

- **段 6 の fix 子 1 本目が model call 上限 100 に当たり、報告を出さずに終了した**
  (`limit_trigger=max_model_calls`、`codex_exit_code=-15`、`failure_class=f45_missing_output`)。
  編集は正しく入っていたので、親が差分を現物監査 (裁定 8 の署名どおり・他の変更ゼロ・テスト file は
  byte 一致) して採用し、段 6 のレビュー 2 本と焦点子へ裏取りさせた。
  2 本目は `--max-model-calls 300` で完走した。
- **段 6 のレビュー投入 1 回目が rc=2 で即死した。** `--lane` は `--stage consult` でだけ指定できる。
- **変異 wrapper が共有木の事後検査 rc=125** になった (既知の型)。harness 直接経路へ切り替えた。

## 7. 到達範囲と非保証

- 本 wave は **official 床値 campaign を投入していない。** 契約 9 節が要求する試行台帳側 gate の
  実値域は依然として未取得である。
- 新規テストは公開入口から **launch certificate の構成と strict 検証まで**を通す。
  **証明書 file の発行と発行後再検査には到達していない。**
- 凍結 23 件の bytes、`FORMULA_ID`、result schema の既定、凍結保留の全体、
  `launch_floor_attempt` / `launch_probed_floor_attempt` の署名、`tools/pegasus/` の shell は
  いずれも不変である (レビューが manifest 23 件の HEAD との byte 一致を独立に確認した)。
- 被覆の全単射照合 (B2 inspector)、試行台帳の slot 一意性、本番共有 root の fixture 残存には
  触っていない (D1936 項 12 / 項 13 と依頼で scope 外)。
- fix 前後の比較は親 1 主体の監査であり、独立主体の裏取りではない。レビューへ渡した差分は
  既に fix 後だったため、レビューが確認できたのは「統合後の現物と記録した差分の byte 一致」である。

## 8. 収録物

- `s1-brief.md` — 段 1 brief ((P1)〜(P4) が段 3 の攻撃対象)
- `s4-adjudication.md` — 段 4 裁定と追記 (裁定 8〜13)
- `verbatim/` — 段 2 plan、段 3 敵対 2 本、実装子、段 6 レビュー 2 本、fix 子 2、焦点子の逐語 (gzip)
- `verbatim/prompts/` — 全子へ渡した prompt の逐語 (gzip)
- `verbatim/s5-implementation.diff.gz` — 統合後の差分
- `verbatim/s5-prefix-snapshot.diff.gz` — 裁定 8 の fix 前 snapshot
- `mutation/` — probe と本走の spec・結果 (gzip)
