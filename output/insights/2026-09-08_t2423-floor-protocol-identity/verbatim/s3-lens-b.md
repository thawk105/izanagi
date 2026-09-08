## 1. pin 閉包の漏れ

- **real 候補 — acceptance ledger の閉包が t2412 後を見ていない。**
  - file:line: `s2-plan.md:42,100-124,165-170,234`、`orchestrator/tests/acceptance_duration_ledger.json:9334,9343`、t2412 版同ファイル `:18,155,178`
  - t2412 は driver nodeid を台帳へ追加する。その後、本 wave は driver の schema test を改名し、`[protocol]` parameter と新 protocol test を追加し、issuer test も 2 件改名する。結果は少なくとも「未登録 5 nodeid、stale 3 nodeid」になる。
  - 影響: 未登録は既定 cost で実行され、90% gate `test_acceptance_schedule_order.py:704-714` の余裕を実数で証明していないため、受入と land が赤にならないという結論は未閉包。
  - 推奨: **must-fix**。t2412 取り込み後の収集集合で被覆率を再計算し、必要なら実測 JUnit から台帳を更新する。duration を推測して書かない。

- **refuted 候補 — それ以外の実行物 pin。**
  - file:line: `floor_pair_driver.py:56,263-278,1194-1214,1240-1256`、`test_floor_pair_driver.py:185-298,451-456,483-505,517-575,662-680,1072-1112`、`p3_b4_floor_artifact_issuer.py:736-804,860`
  - `floor-pair-spec/v3` literal は実行物では 2 件、`FloorPairSpec(` は constructor 1 件、`_derive_identity` の戻り値分解は 1 件だけ。dataclass test は field 数でなく default 不在のみを検査する。`receipt_has_protocol` も fixture 定義 3 箇所と呼出し 6 箇所で閉じている。
  - file:line: `test_p3_b4_floor_artifact_issuer.py:697-703`、`orchestrator/tests/README.md:105-120`
  - 自走 harness はファイル全体を pytest collection するため node 一覧更新は不要。`tools/check_docs.py:124-160` は事前登録を living doc に含めるが、floor spec の literal・field 同期規則は持たない。
  - 影響: 追加の production/test 編集面は見つからず、成果物・受入・land は変わらない。
  - 推奨: **nit**。段 2 の閉包表を維持し、台帳だけ例外として訂正する。

## 2. t2412 との衝突面

- **refuted 候補 — 定義どおりの「隣接」箇所は 0 件。**
  - file:line:

    | file | t2412 の exact 変更行、main 側 | 本 wave の実変更点 | 間の未変更行 |
    |---|---|---|---|
    | `floor_pair_driver.py` | `1190,1192` | `1198`、`1204` 後 | `1193` 以降あり |
    | 同 | `1229,1235-1238` | `1251` 後 | `1239-1251` あり |
    | `test_floor_pair_driver.py` | `309-343`、`423` 後、`472-475`、`698` | `185-298,484,528`、新 test、`1072-1112` | 各区間に未変更行あり |
    | `test_p3_b4_floor_artifact_issuer.py` | `109`、`509` 後へ追加 | `40-84,217-250,473-497,504-506,537` 後 | `507-509` が残る |

  - `s2-plan.md:195-199` は context 付き hunk を変更行と取り違えている。brief N6 の issuer `66` は t2412 差分に存在せず、実差分は `109` と `509` 後だけ。
  - 影響: text merge の即時衝突は予測しないが、広い no-touch 範囲を信じると統合時レビューが不正確になる。
  - 推奨: **nit**。t2412 land 後の行番号へ再アンカーし、context と変更行を区別する。

- **refuted 候補 — protocol 追加 bytes と t2412 偽 VCS の意味的衝突。**
  - file:line: t2412 `test_floor_pair_driver.py:307-343,406-411,422-443`、t2412 `test_p3_b4_floor_artifact_issuer.py:53-66,109,510-515`
  - t2412 の `_install_git` は `spec_relpath` 引数を追加していない。変更は `head_overrides` から `blob_overrides` と ancestor 応答の追加であり、`git show` は既定で `(root / relpath).read_bytes()` を返す。spec は `_install_git` より先に canonical 化して書かれるため、新しい protocol bytes がそのまま偽 tracked blob になる。実 Git fixture も更新後の `_valid_document` から spec を書いて commit する。
  - 影響: 通常の両 wave 統合では spec byte mismatch や loaded-head mismatch で赤になる経路はない。
  - 推奨: **nit**。統合後焦点走で確認するが、意味的衝突を must-fix にしない。

## 3. 変異の帰属

- **real 候補 — M11 の fixture は downstream crash に過剰決定される。**
  - file:line: `s2-plan.md:112-114,217`、`p3_b4_floor_artifact_issuer.py:890-901`
  - 計画の `identity=None, missing_identity_elements=("protocol",)` で guard を消すと、`_identity_value(None)` が `AttributeError` を投げる。発行は依然拒否され、変わるのは例外型だけなので、受理集合を変える M11 の証拠にならない。
  - 影響: mutation は「KILLED」でも規律 2 の検出力を証明せず、変異台帳と land 証拠が偽陽性になる。
  - 推奨: **must-fix**。有効な identity と nonempty missing tuple を組み合わせ、guard 削除時に値が通る入力へ直すか、M11 を登録から外す。

- **real 候補 — M2 は単一理由だが失敗 node が広い。**
  - file:line: `s2-plan.md:208`、`floor_pair_driver.py:403-415,1194-1201`、`test_floor_pair_driver.py:185-298`
  - expected key 集合から protocol を落とすと、共有 `_valid_document` を使う全正例が同じ exact-key 理由で落ちる。表にある 1 node だけを期待集合にすると `DW-M08` の完全一致を満たさない。
  - 影響: full-file mutation では予測外 node が大量に赤となり、KILLED 判定が MISMATCH になる。
  - 推奨: **nit**。対象 node だけを走らせるか、probe 後に完全な失敗 node 集合を登録する。

- **refuted 候補 — M1、M3-M10。**
  - file:line: `floor_pair_driver.py:426-436,1194-1214,1240-1256`、`p3_b4_floor_artifact_issuer.py:736-804,880-926,1007-1025`
  - M1 は literal、M3 は空白入りと129文字、M4 は旧 v3、M5-M7 は互いに異なる `silo`・`mocc`・`synthetic-env`、M8 は protocol を持たない実 receipt、M9 は authority parser の exact identity、M10 は filename segment がそれぞれ直接殺す。M3 の空文字だけは `_exact_text` も拒否するが、残り2入力が区別する。
  - 親 M6、threads/workload/campaign missing、issuer 側 canonical 緩和を帰属不成立として除外した `s2-plan.md:219-224` は正しい。
  - 影響: fixture が先に別理由で例外を投げる経路は、M11 以外では見つからない。
  - 推奨: **nit**。M2 の期待 node 集合だけ実走前に閉じる。

## 4. golden の再固定

- **refuted 候補 — 再固定そのものは F27 ではない。**
  - file:line: `floor_pair_driver.py:1259-1274,1298-1337`、`test_floor_pair_driver.py:1072-1138`
  - golden が守る性質は、固定 seed・spec schema・spec SHA・window/pair/sample/role から HMAC rank が決める exact permutation である。v4 化と protocol 追加は HMAC preimage の `spec.schema` と `spec.spec_sha256` を意図的に変えるため、順序変更は正当な入力追随である。全順序と独立な pair/role/index 不変条件は再固定後も残る。
  - 影響: 正しく再導出すれば HMAC field の削除・順序変更・role 混同に対する検出力は落ちない。
  - 推奨: **nit**。golden 更新自体は維持する。

- **real 候補 — 段 2 は再導出手順を定めていない。**
  - file:line: `s2-plan.md:108-109,230`、`docs/failures.md:872-886`
  - `make_measurement_plan` の実走結果をそのまま貼ると、同時に混入した実装欠陥まで正解化でき、F27 型になる。
  - 影響: テストは緑でも exact-order regression の独立性が失われ、land 後の変異を見逃す。
  - 推奨: **must-fix**。v4 fixture の canonical bytes と SHA を先に固定し、production の `_hmac_rank` と `make_measurement_plan` を呼ばない別計算で、NUL 区切り・HMAC-SHA256・各 literal field tuple から順位を導出してから golden へ転記する。

## 5. 親 brief の実測値と一般化

- **real 候補 — N5 の伝播説明は誤り。**
  - file:line: `brief-s1.md:14`、`floor_pair_driver.py:1302,1316,1328,1405-1419,2190-2198,3004-3010,3047-3055`
  - `spec.schema` は plan/window へ schema field として直接書かれない。HMAC preimage と spec SHA に入り、plan は `PLAN_SCHEMA`、window は `WINDOW_SCHEMA`、summary は `SUMMARY_SCHEMA` を書く。ただし spec SHA、順序、plan SHA が伝播するため downstream bytes が変わる結論自体は正しい。
  - 影響: production instance がなくても active golden `test_floor_pair_driver.py:1072-1112` は赤になる。段 2 はこれを補足済みなので実装面の漏れは回避されている。
  - 推奨: **nit**。段 4 では親 brief の「直接書かれる」を訂正する。

- **refuted 候補 — insights に active spec golden がある。**
  - file:line: `output/insights/2026-09-07_b4-paired-session-driver/mutation-ledger.json:259`、同 `mutation-ledger-probe-round2.json:35`
  - `floor-pair-spec/v3` は失敗 stdout 内の dataclass repr であり、JSON の top-level `schema` を持つ spec bytes ではない。この2ファイルの exact path を読む現行 test・tool もない。
  - 影響: 歴史記録を v4 へ書き換える必要はなく、成果物・受入・land は変わらない。
  - 推奨: **nit**。歴史記録として不変にする。

- **real 候補 — N6 の exact anchor は一部不一致。**
  - file:line: `brief-s1.md:15`、t2412 `test_p3_b4_floor_artifact_issuer.py:109,510-515`
  - issuer `66` は t2412 の変更行ではない。driver の `1163-1195`、`1227-1240` も context 込み範囲で、exact 変更行とは一致しない。
  - 影響: no-touch 判断を範囲で行うと、必要な loader key 変更まで衝突扱いする。
  - 推奨: **nit**。段 2 の `-U0` 基準へ統一する。

## 6. 実効性

- **real 候補 — 本 wave 単独では production 発行可能にならない。**
  - file:line: `floor_pair_driver.py:1235-1238`、`docs/decisions.md:53884-53907`
  - 現行 HEAD では `source_commit == loaded_head` が必要な不動点が残る。t2412 が着地しない限り production spec を load できず、issuer へ到達しない。実 v4 spec instance と測定済み window/summary もまだ存在しない。
  - 影響: t2423 だけ land しても authority artifact は生成されない。
  - 推奨: **nit**。scope は広げず、受入条件を「t2412 取り込み済みの main 上で発行可能」に限定する。段 2 `:201` の統合順は維持する。

- **refuted 候補 — protocol 以外の identity 前提も欠ける。**
  - file:line: `floor_pair_driver.py:736-776,830-852,1136-1147,2944-3037,3062-3093`、`p3_b4_floor_artifact_issuer.py:411-468,665-728,736-804`
  - `floor-pair-summary/v3` の実 producer と CLI finalize は存在する。cells/workload は nonempty、全 cell の threads/workload は単一 calibration に一致し、campaigns は nonempty・一意・canonical である。成功した producer loader 出力では、現在の missing 候補のうち protocol だけが残る。
  - 影響: t2412 と実入力が揃った条件下では、本 wave が identity 発行の最後のコード上の欠落を閉じる。
  - 推奨: **nit**。D1696 の人手確認9項目、実 spec 作成、実測実施は scope 外の運用前提として明記するだけに留める。

## 7. docs の整合

- **real 候補 — 「spec instance が無いから erratum 対象が無い」という論法は誤り。**
  - file:line: `brief-s1.md:10,20`、`docs/decisions.md:53602-53622,54183-54201`
  - D1765 は発効前でも、B-4 事前登録の記述が現在地と食い違えば追記 erratum を要求する。D1789 は発効後の事前登録 bytes を触らない規則である。どちらも「凍結 spec 一般」の schema 改訂手続きではない。
  - 影響: N1 を一般免除として残すと、将来 prereg が実際に陳腐化しても追記を省く誤った先例になる。
  - 推奨: **must-fix**。段 4 では「instance 不在」と「prereg 陳腐化」を別判定に直す。

- **refuted 候補 — 本 wave で事前登録本文への追記が必要。**
  - file:line: `docs/phase3-b4-reflux-ablation-preregistration.md:34-36,979-992,1075-1079`、`docs/decisions.md:50331-50349`
  - 事前登録は発効前だが、spec schema 名や top-level key 集合を記述していない。対象 protocol と成果物名の protocol 要素はすでに要求され、(a) は D1641 の5要素を変えない。したがって現在地との食い違いは発生しない。
  - 影響: prereg 無編集で成果物・受入・land の整合は保たれる。結論は親と同じだが理由が違う。
  - 推奨: **nit**。本文は編集せず、段 4 の理由だけ訂正する。protocol allowlist/source 束縛は D1696 の再訪条件が成立した場合だけの**裁定パッケージ候補**とする。

## 総括

- must-fix 候補は **4件**: ledger 閉包、M11 帰属、golden 独立導出、erratum 論法。
- 最大の懸念は、t2412 が追加する driver 台帳 pin を段 2 が認識せず「編集不要」と確定した点。
- 親 brief への反証あり: N5 の伝播説明、N6 exact anchor、N1 から erratum 不要を導く一般論。
- 裁定パッケージ候補あり: protocol allowlist/source 束縛のみ。D1696 再訪条件は未成立。
- pytest は実行しておらず、以上は指定された read-only 静的検査の結果。