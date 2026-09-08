# 段 6 裁定 — レビュー所見の real/refuted と採否

対象 commit `0df429a21`。親の実走は consumer 16 passed、launcher 契約 6 passed、
official perf closure 7 passed、hooks 474 passed / 1 skipped。すべて rc=0。
**レビューが示したのは「親の緑がこれらの入力を通っていない」ことである。**

## must-fix (成果物影響あり)

| # | 所見 | 出所 | 成果物影響 (DW-G05) |
|---|---|---|---|
| F1 | 型付き CMake define (`-DCCBENCH_BACKOFF_NOINLINE:STRING=1`) が診断 build 検査を素通りする | A-1 | 診断 build の throughput が headline 適格として `accepted` になる。D20 に正面から反する |
| F2 | bench executable の検査が argv 内に token が 1 回現れるだけで通る。`/bin/true` や `/bin/echo` を先頭に置いた command を受理する | A-3 と B-2 が独立に指摘 | 性能 binary で測っていない値を「性能 build receipt と対応した」と結論する |
| F3 | toolchain manifest と record digest が束縛されていない。**現行の正例 fixture 自身が不整合な root である** (`_TOOLCHAIN` の canonical digest は `fb534797...` だが `"3"*64` を記録して accepted を期待) | B-1 | 「toolchain manifest と record digest が一致した」という戻り値が偽になる。かつ負テストの前提 (自己整合 root) が崩れている |
| F4 | `verify_done` だけ env tag の一致検査から外れている | B-3 | 「両 arm の env tag が一致した」が偽になる |
| F5 | attempt に属さない `verify_done` (anomalies=1) を足すと素通りする | A-2 | **規律 2 の迂回。** anomaly が WAL に明記された variant を headline 適格と結論しうる |
| F6 | 診断 knob を持つ off-pair genome があっても受理する。束縛した job body が生成できない root を正例にしている | A-4 | 「束縛済み sanctioned producer の complete output」という provenance 結論が偽になる |
| F7 | global admission failure の arm を一律 `baseline` に帰属させる | A-5 | 規律 3。target 由来の拒否を baseline と誤記録し、再検証可能な帰属を失う |
| F8 | submit receipt の schema literal `t1998-balanced-stock-inline-submit-event/v1` をどのテストも固定していない | B-5 | job body digest では投入器を区別できないので、この receipt が投入器 provenance の唯一の記録である。無検出で identity が変わる |
| F9 | `_arm_decision()` 内の `expected_genome` に対する `BACKOFF_NOINLINE=1` 検査が恒偽 (呼出し側から固定定数しか渡らない) | A の dead branch 指摘 | 恒真・恒偽の検査を保護と数えない (F6 の直しに統合する) |

## nit / backlog (must-fix にしない)

- **queue preflight が `gen_S` / `ENA` / `ACT` を出力全体で独立検索する (A-6)。** real である。
  ただし `gen_S` が停止していれば qsub が失敗するだけで、誤った成果物は生まれない。
  **同じ書き方は既存の A-5 投入器と B-10 投入器にもあり**、本 wave の新 file だけ直すと
  既存 2 本と挙動が分かれる。3 本まとめて直すのは scope 外なので**裁定パッケージへ送る**。

## scope 外・裁定パッケージへ送る

1. **F251 の残余 (B-4)。** 新 submitter は 1 invocation 1 job なので**同一 invocation 内の
   兄弟競合は構造的に起きない**が、別 invocation どうし、あるいは既存 A-5 job と同時に走る場合は、
   再利用している job body の global `git worktree prune --expire now` が別ノードの worktree 登録を
   消す経路が残る。**commit `0df429a21` の message は「経路が成立しない」と書いたが、
   正しくは「同一 invocation 内では成立しない」である。** 本裁定と worklog で訂正する
   (規律 7 に従い追記で訂正し、過去 commit の message は書き換えない)。
   恒久対応は A-5 job body の shared gitdir ownership の変更であり、F251 として既にユーザー裁定待ちである。
2. **3 投入器に共通する queue preflight の行単位検査。** 上記 nit と同じ。

## 冗長 gate の明記 (DW-M03、変異の証拠から外す)

レビュー A の表に従い、次は上流が先に同じ入力を拒否するため単独では発火しない。
source の comment に冗長 gate と明記し、変異事前登録から外す。

- `pair-cardinality`、`producer-rejected-variant` の receipt 欠損 / abort / stage 欠損部分
- WAL gitlink の一致 (admission が `source.ccbench_commit == lock.ccbench_commit` を先に要求)
- COMMIT の environment contract digest (admission が lock 一致を先に要求)
- `producer-artifact-binding-mismatch` のうち `admission.lock_sha256` / `admission.wal_sha256`
  (同じ bytes から view が算出済み。TOCTOU guard として残す)

## 変異事前登録の改訂 (DW-M01 / DW-M07)

段 4 の M1〜M9 を次へ差し替える。実装後に anchor を確定し、単一理由性を確認してから本走する。

| ID | 変異位置 | 期待 | 単一理由性の根拠 |
|---|---|---|---|
| M1 | arm 別 source digest 比較を無条件 true にする | KILLED | 事前登録 digest を見る層は他に無い |
| M2 | sibling failure receipt の存在検査を削る | KILLED | 上流は failure receipt を読まない |
| M3 | gitlink の 40 桁 exact / 短縮 prefix の分岐を無条件 true にする | KILLED | result / reservation の 40 桁比較は他層に無い |
| M4 | `unstable` の分岐を `accepted` 側へ倒す | KILLED | 上流 admission は unstable を拒否しない |
| M5 | target の選択を fixed-5 固定から argmax へ変える | KILLED | 上流は 8 点全部を通す |
| M6 | 拒否 payload から `expected` / `actual` を落とす | KILLED | 規律 3 の証拠投影はこの層だけ |
| M7 | job body digest の比較を削る | KILLED | 事後に script digest を見る層は他に無い |
| M8 | launcher の投入 workload を balanced 1 本から 2 本 fan-out へ変える | KILLED | 契約テストがこの層だけを見る |
| M9 | launcher の出力 parent が repo 外であることの検査を削る | KILLED | 新 submitter 固有の検査 |
| M10 | **(新)** CMake define の正規化を削り literal 一致だけに戻す | KILLED | F1 の直しはこの層だけ |
| M11 | **(新)** bench executable の argv 位置検査を「token がどこかにある」へ戻す | KILLED | F2 の直しはこの層だけ |
| M12 | **(新)** toolchain manifest の canonical digest 再計算を削る | KILLED | F3 の直しはこの層だけ |
| M13 | **(新)** `verify_done` を env tag 集合から外す | KILLED | F4 の直しはこの層だけ |
| M14 | **(新)** anomaly / 非 serializable の全 record 走査を削る | KILLED | F5。上流は attempt 非帰属 record を見ない |
| M15 | **(新)** 診断 knob を持つ genome の全走査拒否を削る | KILLED | F6。上流 finalizer は fixture root には効かない |
| M16 | **(新)** submit receipt の schema literal を別文字列へ変える | KILLED | F8。契約テストがこの層だけを見る |
