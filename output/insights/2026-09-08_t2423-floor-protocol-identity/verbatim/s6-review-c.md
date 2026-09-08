## 1. 受理集合の向き

- **real 候補**
- file:line: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:761-792`、`orchestrator/campaign/genome.py:223-251`、`orchestrator/campaign/model.py:49-59`
- 変更前の public 発行集合は実質空だった。実 receipt に top-level `protocol` はなく、仮に追加しても portable record の exact-key 検査で producer loader が拒否する。変更後は、全 artifact の strict 検証済み receipt が、同一の canonical genome protocol を持つ場合へ意図どおり拡張された。
- ただし複数の `|` に穴がある。例えば `mocc|A|B=1` は、追加の `|` が flag 名に入り、`Genome(protocol="mocc", flags={"A|B": 1}).canonical()` と一致するため helper を通る。protocol の `mocc` も `_ID_RE` を通り、権威成果物を発行できる。
- 成果物影響: malformed な複数 separator genome から `__protocol-mocc` の権威 floor が発行され、材料レポートと受理集合へ流入する。
- 推奨: **must-fix** — issuer で separator が exact 1 個であることを要求し、その public 発行拒否 test を追加する。allowlist や source scan は不要。

- **refuted 候補**
- file:line: `orchestrator/campaign/floor_pair_driver.py:1052-1080,1092-1107`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:766-790`
- その他の経路は fail-closed である。

| 入力 | public 経路 | issuer 分岐へ直接到達した場合 |
|---|---|---|
| record / `binding` が dict でない | producer loader が `spec_rejected_by_producer` | `protocol_failed=True` |
| genome が非 str / 空 | receipt validator が先に拒否 | `ValueError` を捕捉して `protocol_failed=True` |
| 通常の不正な複数 `\|` | helper が拒否 | `protocol_failed=True` |
| protocol 部が `_ID_RE` 不一致 | `_identifier()` を捕捉 | `protocol_failed=True` |
| receipt SHA 不一致 | `_read_tracked_bound()` が先に拒否 | issuer 自身も `protocol_failed=True` |
| receipt が非 JSON | producer loader が先に拒否 | JSON error を捕捉して `protocol_failed=True` |

`protocol_failed` は sticky であり、一部 artifact が成功して `len(protocols)==1` になっても発行されない。raw 例外の public 漏出や黙った skip は確認できない。

- 成果物影響: 上記の複数 separator 例以外では、不正 receipt が権威成果物や材料レポートへ追加されない。
- 推奨: **nit** — 現行維持。

## 2. binary への束縛

- **refuted 候補**
- file:line: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:839-869`、`orchestrator/campaign/floor_pair_driver.py:581-597,1052-1107,1228-1234`、`orchestrator/campaign/s8b_binary_admission.py:131-147,356-369,397-423`
- issuer は validator を直接呼ばないが、public 経路では `_derive_identity()` より先に `load_frozen_spec()` が必ず実行される。同 loader は spec の同じ `BoundReference.path` を読み、spec 内 SHA、HEAD blob、portable validator、binary SHA を検査する。その後 issuer は同じ resolved root、同じ path を再読し、同じ receipt SHA を再照合してから genome を取得する。
- load 順は `load_frozen_spec()` 完了後の `_derive_identity()` で固定されている。途中で bytes が変わっても、同じ SHA を持たない限り issuer 側で `protocol_failed` になる。
- 成果物影響: public issuer が「validator を通っていない別 record」から protocol を採用する経路はなく、binary-bound identity は維持される。
- 推奨: **nit** — validator の重複呼出しは不要。現在の依存関係を維持する。

## 3. fail-closed の実効性

- **refuted 候補**
- file:line: `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:477-543`、`orchestrator/tests/test_floor_pair_driver.py:61-151`
- JSON fixture と未整列 `mocc|B=1,A=2` は、fixture が `genome_sha256`、`variant_id`、`binding_sha256`、materialization binding、receipt outer SHA を一貫して再計算するため receipt validator を通る。その後 issuer の helper 分岐で拒否される。fixture 構築や producer validator が先に落とす負例ではない。
- 混在 test も両 receipt が正規 canonical genome であり、issuer の `len(protocols) != 1` だけで拒否される。
- file:line: `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:546-564`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:899-904`
- guard 正例は、まず有効 identity を取得し、その identity を保ったまま非空 missing を差し込んでいる。`_authority_value()` の missing guard が単独理由になる。
- 成果物影響: 非 canonical、混在、内部破損 summary は発行前に止まり、権威 floor と材料レポートは増えない。
- 推奨: **must-fix、1 と同一** — `mocc|A|B=1` 型だけが未被覆なので追加する。

## 4. テストの弱体化

- **refuted 候補**
- file:line: `orchestrator/tests/test_floor_pair_driver.py:52-76,93-151,155-203`、`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:53-81,206-254`
- fixture は genome を受け取ると既存生成ロジックで全関連 hash を再計算し、実 validator を通す。validator stub、期待 hash の後付け、skip、xfail は追加されていない。
- `test_real_finalize...` の新しい monkeypatch は fixture helper への canonical genome 注入だけであり、validator、spec loader、finalizer、issuer は置換していない。calibration stub は既存経路である。
- 既存 test の期待変更は次の全件である。

  1. `test_real_finalize_floor_summary_is_accepted_before_missing_protocol_blocks_issue` を改名し、`missing=("protocol",)` と発行拒否から、identity protocol `mocc`、発行成功、filename、authority protocol の検査へ変更。
  2. `test_identity_is_not_a_caller_surface_and_missing_protocol_is_named` を改名・parameterize。既存 JSON case の期待値は不変で、未整列 genome caseを追加。
  3. 既存の発行・resolver test 5 箇所は入力 fixture を偽 top-level `silo` から実 canonical `mocc` receipt へ変更したが、assert / raises の期待値は変更していない。

- 裁定 §3 が名指しした改名・書換え以外の期待値変更はない。
- 成果物影響: 偽 top-level protocol と validator 迂回が除去され、test が実 receipt 由来の成果物を検査する方向へ強化された。
- 推奨: **nit** — 現行維持。

## 5. 変異 M1〜M8 の帰属

production file 内では、下記 anchor の逐語は各 1 箇所である。

| ID | 判定、anchor | 殺す test と帰属 | 成果物影響 | 推奨 |
|---|---|---|---|---|
| M1 | **real 候補** `p3_b4_floor_artifact_issuer.py:780` | `test_real_finalize...` が `mocc != synthetic-env` で赤。先行拒否なし | env tag を protocol とした誤名成果物 | **nit** 現行登録でよい |
| M2 | **real 候補** 同上 | 同 test が `mocc != silo` で赤。先行拒否なし | mocc binary を silo と表示 | **nit** 現行登録でよい |
| M3 | **real 候補** `:791` | 混在 test は両 receipt が valid なので identity 非 None となって赤 | 異 protocol 対を権威 floor として発行 | **nit** 現行登録でよい |
| M4 | **real 候補** `:780` | 未整列 case は validator を通り、置換後だけ受理されて赤 | 非 canonical genome を発行 | **nit** 現行登録でよい |
| M5 | **refuted 候補** `:767-769` | producer loader が SHA 不一致を先に拒否する。加えて `continue` だけ消しても `protocol_failed=True` が `:791` を支配し、issuer 内でも同値 | 成果物集合は変わらない | **nit** 未登録維持。再登録するなら sticky flag も含む別変異が必要 |
| M6 | **real 候補** `:932` | filename test と real-finalize test が protocol segment 欠落だけで赤 | protocol を欠いた名前を発行 | **nit** 現行登録でよい |
| M7 | **real 候補** `:900` | valid identity + missing の直接 guard test が単独理由で赤 | 内部破損 summary を authority 化 | **nit** 現行登録でよい |
| M8 | **real 候補は行削除に限定** `:792` | JSON fixture は issuer まで到達するが、行削除後は空 protocol identity ではなく `next(iter(protocols))` の `StopIteration` で赤 | 発行ではなく未処理例外になる | **nit** 登録文を「append 削除による例外」に直すか、空 protocol 発行まで作る exact 変異を別途定義する |

M4 は未整列 split 変異を正しく殺すが、現実装に残る複数 separator の穴は殺さない。

## 6. 非保証の記述

- **refuted 候補**
- file:line: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:746-751,831-836,899-904`
- docstring は protocol の出所を「accepted build receipt の binding genome」と限定しており、CCBench source を走査・確認したとは書いていない。エラー文も `summary-bound spec/receipt` からの導出とだけ述べ、source 確認を主張しない。
- 成果物影響: 現行文言により検査していない source protocol を検査済みと誤表示する直接の変更はない。
- 推奨: **nit** — 現行維持。さらに明示するなら「CCBench source の protocol を再検査しない」を docstring に加える程度に留める。

- **裁定パッケージ候補**
- protocol allowlist、実 source scan、source protocol との独立照合は現裁定の scope 外であり、本 patch の must-fix にしない。
- 成果物影響: 将来採用すれば受理集合をさらに狭めるが、現成果物の保証内容と schema の再裁定が必要になる。
- 推奨: **裁定パッケージ候補**。

## 総括

- must-fix 候補は重複をまとめて 1 件: 複数 `|` を含む genome の受理穴。
- 最大の懸念は `mocc|A|B=1` が strict receipt 経路を通り、権威 floor を発行できること。
- 裁定 §3 の主要構造から逸脱はないが、意図した canonical 拒否集合に上記の穴がある。
- 裁定パッケージ候補あり: protocol allowlist / CCBench source 束縛。pytest は実行していない。