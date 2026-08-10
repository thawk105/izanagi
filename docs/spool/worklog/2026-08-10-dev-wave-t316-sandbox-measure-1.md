---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t316-sandbox-measure
seq: 1
title: [T-316] 計測段を計算ノードで実走し、build profile が std::system を封じ込めないことを 2 ノードで再現した (コード + docs、計測 ID 0:900383.nqsv と 0:900427.nqsv、変異 8/8 KILLED、branch worktree-dev-wave-t316-sandbox-measure)
---

## 本文

- **依頼 = [T-316] の計測段。** 裁定パッケージ R3-1 (計算ノード backend の決定的計測) と
  R3-2 の計測半分を実走し、意味 gate 実装段への判定材料を返す。ユーザー裁定 R2-b (独立 oracle)
  は既定として動かしていない。判定材料は
  `output/insights/2026-08-10_t316-sandbox-measurement/package.md`。
- **前提の訂正 1 件 (依頼文に対して)。** 依頼は「[T-184] は land 済み」としていたが、
  worklog 363 が land したのは reasoning 面だけで、`docs/phase3.md` は
  「reasoning 面の採用を [T-316] の待ち解除根拠にしてはならない」と明記している。
  R4 の [T-184] 依存は実装段の docs 配置の話であり計測段の前提ではないので計測は実行し、
  実装段が依然 blocked である事実を判定材料へ明記した。
- **決定的所見 = build profile が `std::system` を封じ込めていない。** sandbox 内で payload が
  `REACHED` を返し副作用まで観測され、同一 path の外側正例も成立しているので帰属は確実。
  runtime profile では封じ込められている。**1 走目 bnode085 / 2 走目 bnode027 で独立再現。**
  機序は段 6 レビューが事前に指摘したとおり build profile が host `/bin` を bind するため。
  R1 の「(ii) を全軸の host-security boundary とする」は現行 profile 案のまま build 段で成立しない。
  対処は非同値な設計択一 (shell 排除 / 主張を run 段へ限定 / 残余として台帳明示) なので
  親は決めずユーザーへ返す。
- **性能の懸念は stock について実測で否定された。** 同一 binary・trace-disabled・48 thread・
  numactl・perf stat・warmup 分離・内外の順序反転 6 対で、wall elapsed の overhead 比は
  中央値 0.9991 / MAD 0.0067。receipt の `metric_semantics` が「TPS でも CC throughput でも
  floor 再較正の判断でもない」と明示する。
- **DNS 遮断は帰属できなかった。** 計算ノードは sandbox の外でも DNS を引けず外側正例が成立しない。
  probe の欠陥ではなく node の性質として `NODE_CAPABILITY_UNAVAILABLE` で記録した。
- **段 6 は敵対レビュー 2 本と焦点再レビュー 1 本がいずれも当初 NO-GO。** fix を 3 巡当てた。
  閉じた偽 GO 経路は、非 0 終了の封じ込め読み替え、無限ループ制御の恒真、S4 の子孫消滅未検査、
  S3 write の `O_EXCL` 恒真、計測 ID の未束縛、部分結果の非永続化など。
  **fix 第 2 巡は正例を通すために封じ込め要求を外す回帰を作り、焦点再レビューがそれを捕まえた。**
- **変異が静的レビュー 3 本の後で検査の穴を見つけた ({{F:discharge-overrejection-unguarded}})。**
  初回走行は KILLED 3 / MISMATCH 4 / SURVIVED 1 で、生存した M7 は
  「S7 の discharge を丸ごと無効化しても誰も気づかない」= 過剰拒否方向の無検査だった。
  テストを 2 件足して 2 走目は 8/8 KILLED (SURVIVED 0 / MISMATCH 0)。初回台帳は erratum として残す。
  MISMATCH 4 件はいずれも実測 failure が非空で、親の静的予測が外れただけである
  (M1 と M5 は予測より多くのテストが検出していた)。
- **機体固有の新事実 ({{F:renameat2-einval-on-work}})。** この機体の `/work` では
  `renameat2(RENAME_NOREPLACE)` が**通常ファイルに対しても EINVAL** を返す (tmpfs では成功する)。
  receipt の出力先は `/work` 配下なので、単体テストが tmpfs で緑でも実機の publish だけが落ちる。
  親が実測して `os.link` による create-only publish へ置き換えた。runbook は directory についてしか
  記録していなかった。
- **エージェント工数: 親 1、Codex 子 10** (段 5 実装 1、段 6 敵対レビュー 2、fix 5 巡 + 検査穴 fix 1、
  焦点再レビュー 1、受入赤 fix 1。実装系は `-s workspace-write`・`reasoning=high`、
  レビュー系は `-s read-only`)。
- **受入は 3 走した。採用値は land 対象 tip `f332271e` の 3 走目 = `8129 passed / 20 skipped /
  511.96 秒 / rc=0`。**
  - 1 走目 (tip `cad2192f`、2 failed / 8097 passed / 20 skipped / 508.47 秒) の赤 2 件は
    本 wave の登録漏れで、`test_claude_transport` の policy registry 独立 literal 閉集合と
    `test_plain_runner_coverage` の自走 harness 契約だった。追加のみで閉じた。
  - 2 走目 (tip `0561b2ee`、1 failed / 8127 passed / 20 skipped) の赤 1 件は
    `test_codex_worker_launch.py::test_check_receipt_rechecks_all_manifest_header_fields[base_commit]`。
    本 wave の差分が到達しないファイルであり、`DW-O18` に従い単独再走したところ
    **3 passed、ファイル全体でも 77 passed で再現せずフレークと確定**した。落ちた述語は
    `process_group_residual` と `termination_verified` で、並行 session の codex 子が居る間に
    出る既知の外乱感受型と整合する。
- **取り込み時の provenance で 2 種類の赤を切り分けた ({{F:stale-checker-range-audit}})。**
  1 つ目は偽陽性で、他 wave の merge 4 件は main 側 checker に既知違反として登録済みなのに、
  取り込み前の古い checker で `HEAD..main` を測ったため赤が出た (`DW-O17` の
  「correction を含むときは full 監査だけが権威」)。2 つ目は実害で、**本 wave の merge commit の
  combined diff が実装面 path (テスト 2 件) を含むのに Codex `role=author` 行が無かった**。
  実装面を書いたのは本 wave の Codex 子なので併記して amend し、全走 rc=0 を確認した。

## 次の一手差分

### 更新

- [T-316] **P1・計測段を完了 ((本エントリ)) → 実装段は依然 blocked、うち 1 件はユーザー裁定待ち**:
  R3-1 の計算ノード実測を discharge した (計測 ID `0:900383.nqsv` / `0:900427.nqsv`)。
  namespace 起動・network 遮断・資格情報不可視化・source RO・process-tree timeout・
  sandbox 内 CCBench build はいずれも成立。**build profile の `std::system` 封じ込めだけが破れ、
  2 ノードで再現した。** 対処 3 案 (shell 排除 / 主張を run 段へ限定 / 残余として台帳明示) は
  非同値な設計択一なのでユーザー裁定へ返す。実装段の残り blocker は
  [T-184] の canonical stage matrix 未発行、R3-3 field mapping、R3-4 sandbox execution receipt と
  WAL topology、R3-5〜R3-9、および R2-b の独立 oracle 本体。
  未 discharge の R3-1 項目は stock/variant 双方の性能差・trace 実行・floor 再較正要否。
  判定材料は `output/insights/2026-08-10_t316-sandbox-measurement/package.md`
  base: 1d6079b8eb8e5168712d2f90e1a2d63ee8d306cbd4cd8cd2559abf8109a49a76
