---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t756-fn2-trace-v2
seq: 1
title: [T-816] FN-2 trace v2 の C++ 半分を作った — silo の C 行に R/W 件数と E 終端を入れ、旧/新 pin の TRACE=0 同一性 checker を新設した (コード + docs、submodule は local commit のまま gitlink 不変、変異 6/6 KILLED + drift control SURVIVED、branch worktree-dev-wave-t756-fn2-trace-v2)
---

## 本文

[T-816] Q1〜Q3 全問 (a) の裁定に従う wave。**担ったのは 4 段手順のうち 1・2 だけ**で、
手順 3 (push と承認定数の更新) は人間手番、手順 4 (gitlink 前進・v1 拒否・characterization 反転) は
承認後の別 wave である。CCBench の gitlink は `d706650` のまま 1 bit も動かしていない。

**新 commit = `511c9538e4e8efa54b45cda62e72389ed3b706ec`** (submodule branch `izanagi-trace-t816-fn2`、
親は現行 pin `d706650`)。編集面は `cc/silo/transaction.cc` の 1 ファイルだけで、
`include/trace.hh` と `cc/si/transaction.cc` は 1 byte も変えていない。

**編集面の壁を D41 の先例どおり迂回せずに越えた。** `hooks/guard_write.py` の
`EVOLVE_BLOCK_SOURCES` は CCBench の編集面を `include/backoff.hh` と `cc/silo/transaction.cc` に
限定しており、裁定パッケージが挙げた `trace.hh` は書けない。D41 では同じ壁に対する
scratch copy + `git apply` の迂回が却下され、「transaction.cc 内で既存 `izanagi_trace::stream()` を
直接呼ぶ」形へ設計変更した先例がある。本 wave もそれに倣い、v2 の C 行と E 行を
transaction.cc 内で直接書いた。**helper `emit_commit` の呼び出しは残置せず置換した** —
残すと同一 txn に v1 と v2 の C が 2 本出る (段 6 レビューが指摘)。

**worktree 撤去で成果が消えない形にした。** submodule の gitdir は worktree 固有領域にあるため、
local commit だけでは wave 終了時に失われる。完全な履歴を含む bundle
(`izanagi-trace-t816-511c953.bundle`、sha256 = `3a36b530…`) を repo 外へ出し、
**新規 clone から実際に復元して HEAD 一致とファイル内容を確認した。**

### 実測

1. **規律 1 の機械検証**: 旧 `d706650` 対新 `511c953` で、TRACE=0 の正規化 preprocess 出力と
   include 活性が **16 context (8 genome × 2 overlay) 全件一致**。`g++-11` / `g++-12` /
   **bundle 復元 clone** の 3 本すべて `result: pass`。差分 path は `--expect-paths` で
   `cc/silo/transaction.cc` に固定した。
2. **emitter の実測 (計算ノード、request 903846)**: bundle 復元木を TRACE=1 でビルドして
   YCSB を 1 本走らせ、trace 4 ファイル・**committed txn 244,971 件**を raw で照合した。
   framing 違反 0 件、v1 (5 token) C 行 0 件。C が宣言した read/write 件数と実 R/W 行数が全件一致し、
   各 txn の末尾に E がちょうど 1 本。**1 回目の probe は依存 (gflags) 不足で不成立**だったので、
   pinned ソースから prefix へ static install する形に直して取り直した。
3. **焦点走**: fix 後 38 passed / 0 failed。
4. **変異**: 通算 **KILLED 6/6、SURVIVED は drift control 1 件のみ** (2 巡、詳細は下記)。

### 敵対検証と変異が捕らえたもの (全件 real と裁定)

- **承認済み・未 push の pin `c9c1a9c` ([T-167]) が存在する** — 段 3 レンズ A が指摘し、親が
  archive worklog で裏取りした。新 commit を `d706650` から生やすと `c9c1a9c` と兄弟になり、
  単一 pin で両方を得られない。本 worktree の submodule は origin からの fresh clone で
  `c9c1a9c` に到達できない (`git cat-file -t` が fatal) ため、共有 checkout から未監査 object を
  取り込むより d706650 を親にして**最終 topology を裁定へ返す**方を選んだ。
- **`git diff-tree --raw` は `-r` が要る** — 無いと tree 単位の M 1 行しか返らずファイルに届かない
  (親が 028f34d→d706650 で実測)。
- **`g++-13` はこの環境に無い** — 段 2 プランが実走条件に据えていた。runbook §7 の記述と一致。
- **context 集合が空でも pass が出る fail-open** — 比較 0 件の緑。列挙元から期待数を導出して塞いだ。
- **header の変更が死角** — `-E -P` は `#define` 行を出力に残さないため、header 内のマクロ定義変更が
  正規化出力から消える。header を含む差分は fail-closed で拒否する形にした。
- **JSON の old/new digest が旧側の複製**だった — 判定自体は独立だが、JSON 単体では
  「新側を計算した」証拠にならない。独立計算へ。
- **新テストの自走 harness が meta-test の literal に当たらず実際に赤だった** — 子は
  「harness あり」と報告していたが、親の焦点走が offender として検出した。存在の申告と効力は別物である。

### 変異 2 巡の内訳 (1 巡目は erratum として保存)

1 巡目 (spec A、7 件): M1 (`--expect-paths` 厳密一致) / M3 (include 活性比較) / M4 (header 拒否) /
M6 (compiler 不在拒否) が KILLED、drift control が SURVIVED。**M2 は MISMATCH、M5 は SURVIVED。**

- **M2** は検出自体はされており、親の期待 node が 1 件ずれていた (実測では
  `test_non_cpp_changed_path_is_rejected` でなく `test_every_modified_cpp_source_is_checked_without_expected_paths`
  が落ちる — suffix gate が先に拒否するようになったため)。2 巡目で実測値へ訂正し KILLED。
- **M5 の SURVIVED は変異が本来の仕事をした結果である。** 既存テストが到達していたのは
  「context 列挙が空」を拒否する gate で、「実際に積んだ件数が期待数と一致しない」gate には
  テストが 1 件も無かった。production を変えずテストだけを足し、2 巡目で KILLED になった。

**変異 harness の制約を 1 つ実測した。** 失敗 node が多い変異は失敗 digest が予算で切り詰められる
(`-r` を落とす変異は 26 件失敗するが digest は 12 件しか出さず `omitted_failures=14`)。
期待 node の完全集合を記録できないので、この変異は KILLED 勘定から外し、実測値だけを証拠として残した。
narrow な gate へ再照準するのが正しい扱いである。

### 閉じた範囲と閉じていない範囲 (正直に)

FN-2 v2 が閉じるのは「**C が宣言した件数に対する R/W framing の欠落**」だけである。次は閉じない。

- **同時欠落** (`write_set_` から要素が消えれば件数も W 行も同時に減る) — 独立 witness =
  [T-152] write-intent shadow (`c9c1a9c`、[T-167] で承認済み・未統合) の領分。
- **X 行の中間欠落** — C は X の件数を宣言しない。
- **内容の置換** — 件数が合ったまま R/W の中身が別物になる形。
- **実行の完了** — W 行は実データ更新より前に出るので、E は write loop 終端到達を示すだけ。

checker の保証も「翻訳単位の同一性」ではなく「**選定した macro context における TRACE=0 正規化
preprocess 出力の同一性、および include 活性の同一性**」に限定して名乗る。

設計判断は {{D:trace-v2-in-editable-surface}} と {{D:trace0-preprocess-identity-gate}}。

## 次の一手差分

### carry

- [T-167]

### 更新

- [T-756] **P1・FN-1 は (428) で land 済み。FN-2 の C++ 半分は本エントリで完了**:
  emitter (silo の v2 C/E) と TRACE=0 同一性 checker が揃い、実 trace 244,971 txn で framing を実測した。
  残るのは手順 3 (人間の push と承認定数更新) と手順 4 (gitlink 前進・v1 拒否・
  `test_characterization_txn_tail_loss_is_false_green` の反転)。characterization は本 wave でも
  **期待値を変えていない**。
  base: ccb436a11553d671d3bec7d39ee339f9ef44924b2ef5c8b16cab416c34007ec5
- [T-816] **P1・手順 1・2 完了 → 手順 3 (人間手番) 待ち**:
  新 commit `511c9538e4e8efa54b45cda62e72389ed3b706ec` (bundle =
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/izanagi-trace-t816-511c953.bundle`、
  sha256 `3a36b53094243234fe119d746396fc9bf56259a07b25c968a225774297dbb82b`)。
  旧/新 pin の TRACE=0 同一性は g++-11 / g++-12 / 復元 clone の 3 本で pass。
  **ユーザー手番** = bundle から取り込んで `origin/izanagi-trace` へ push し、新 pin を承認する。
  承認後の別 wave が gitlink 前進と v1 拒否を実装する。
  base: 456fb61bd68a0291f3c0d14836562c877c94f171a011825632d7a7d073ecb4af

### 新規

- {{T:trace-v2-commit-topology}} **P1・新規 (ユーザー裁定待ち)**: 新 commit `511c953` は現行 pin
  `d706650` を親にしたため、承認済み未 push の `c9c1a9c` ([T-167]) と**兄弟**である。単一 pin で
  両方を得るにはどちらかへ乗せ直す必要がある。checker は (old, new) の 2 commit を引数に取るので、
  topology を変えても**再走 1 回**で済み設計はやり直しにならない。正本 =
  `output/insights/2026-08-11_t816-fn2-trace-v2/verbatim/ruling-package.md`
- {{T:trace-v2-step4-protocol-gate}} **P1・新規 (手順 4 の hard block 条件)**: 手順 4 の
  「v1 拒否」を protocol 無差別に適用すると SI (`cc/si/transaction.cc`、v1 のまま・編集面外) の
  trace が検証不能になる。三択 — SI も v2 化するため編集面を広げる / verifier 入力へ protocol を
  束縛して Silo v1 だけ拒否する / v1 拒否を延期する — を裁定へ返す。同 insights が正本
- {{T:trace-v2-emitter-verifier-wiring}} **P2・新規**: 現行 verifier の parser は C を固定 5 field で
  unpack し未知 tag を `ParseError` にするため、v2 trace は fail-closed で拒否される
  (certified が偽で出ることはない)。手順 4 で parser・model・core・report の 4 層へ
  v2 (件数照合と E 終端) を配線する
