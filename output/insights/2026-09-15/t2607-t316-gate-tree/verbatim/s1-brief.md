# 段 1 brief — [T-2505][T-2519][T-2607] t316 の条件関門と build 木の一致回復

wave: `t2607-t316-gate-tree` / branch: `worktree-dev-wave-t2607-t316-gate-tree`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2607-t316-gate-tree`
基準: `0600887d92538b3f34d894f9674d202d0a29a578` (local main)

## 研究前進 (土台)

t316 probe の S6 は 2026-09-14 の計算ノード 2 走 (`0:996644.nqsv` / `0:996829.nqsv`) とも
条件関門の例外で `attempted=false` / `reason="S6 raised"` になり、S7 も未実行のまま overall=no-go。
sandbox backend を計算ノードで採れるかの go/no-go が実測で確定できない状態が続いている。
最小差分 = 関門が検査する木と probe が build する木を一致させ、S6 を最後まで走らせること。
完了判定 = t316 の実経路で S6 が例外でも `S6_CONDITION_GATE_UNPROVEN` でもなく終端まで到達する。

## 確定済みユーザー裁定 (本 wave の起動引数)

3 件は同一欠陥として 1 wave で扱う。解消案は複数ありうるので、どれを採るかを実測で決めてから実装する。
規律 2 を緩めない。実装面は Codex `role=author` (D95)。本題の修正だけで、仮想リスク向けの
gate・検査・台帳・一般化の追加は scope 外。
**この裁定は D1994 / D1864 の「直し方は定めない・ユーザー裁定へ返す」を上書きする。**
上書きされたのは「誰が決めるか」だけで、却下済みの案は却下のまま (下記)。

## 既裁定により復活させない 3 案 (D1994 の却下欄)

(a) 未使用変数 3 件だけの削除 — `CCBENCH_BACKOFF_FIXED` が残るので赤は解けない。
(b) 関門へ patch 木を渡し probe は素の木を build する — 検査する木と build する木が別物になる。
(c) 関門の stderr 非空判定の緩和 — 共有の正しさ防壁の受理集合を広げる。規律 2 違反。

## 残る択一 (実測で決める)

- **案 A**: t316 が patch 由来 define を渡すのをやめ、素の木に合う configure へ揃える。
  関門被覆義務は source 中の patch macro 出現から導かれる (`test_ccbench_spawn_sites.py`) ので
  義務自体が消える。ただし `verdict_s6` の `S6_CONDITION_GATE_UNPROVEN` 枝と
  `_condition_gate_family_valid` と専用 test 群を落とすことになり、S6 の受理集合は広がる。
- **案 B**: A-2 先例 (`output/insights/2026-09-02/a2-condition-gate-patched-root/README.md`) に倣い
  `patchharness.checkout` の使い捨て木へ patch を当て、関門も build も同じその木を使う。
  受理集合は広がらないが、S6 の build 対象が素の木から patch 木へ変わる。

## 不変条件

1. 検査する木と build する木は同一であること (A-2 insight の逐語。この族の不変条件)。
2. 規律 2 — 関門を通すためだけに受理集合を広げない。`condition_meaning_gate._run_process` の
   stderr 規則、`_INERT_CONDITION_GATE_PAIRS`、`verdict_s6` の拒否枝は緩めない。
3. 既存テストの期待値を甘くして緑にしない。赤なら実装側が誤りとする。
4. `CCBENCH_TRACE=0` の trace-disabled 検査と `source_identity` 検査は維持する。
5. D1995 で入れた「拒否理由を job stderr へ出す」挙動と、受領証 schema は変えない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1-1) 案 A が S6 の受理集合を広げるのは事実だが、関門が検査していた条件そのものが
  存在しなくなるので「防壁の弱体化」ではない、と親は暫定裁定する。これを攻撃せよ。
- (P1-2) 案 B を採ると A-2 の 2 層目 (masstree の `config.h` 不在) が次に出る見込み。t316 は
  `FETCHCONTENT_SOURCE_DIR_*` を渡すので A-2 の `FETCHCONTENT_BASE_DIR` 解と同型にならない。**未実測。**
- (P1-3) `-DCCBENCH_BACKOFF_FIXED=-1` は素の木では binary を変えない (F934 が認定経路で sha256 一致を
  実測済み)。**t316 経路では未実測。**

## 成果物の形

t316 probe と対応 test の変更 (Codex author)、択一を決めた login node の使い捨て生死確認の実測記録、
insight (逐語 + 変異台帳)、worklog / decisions / failures の spool fragment。

## 実測環境

択一の生死確認は Pegasus login node の 100 行以内の使い捨て driver (DW-G01)。
t316 実経路の確認走が要る場合だけ計算ノード (`tools/pegasus/admission_registry.json` に登録済みで
新規実行体は不要)。

## 分割方針

実装面があるので軽量版にしない。段 2 plan 1 本、段 3 敵対 2 レンズ並列、段 5 実装子、
段 6 レビュー 2 本 + fix。変異 matrix は免除しない。

## 変更面の実アンカー表

| path | anchor | 役割 |
|---|---|---|
| `tools/pegasus/probes/t316_sandbox_backend_probe.py` | `_execute_ccbench_build` の `configure` list | build する configure。`-DCCBENCH_BACKOFF_FIXED=-1` と CCBench 非参照 3 変数を含む |
| 同上 | `_require_condition_gate` | 関門呼び出し。`configure[5:]` から define だけ除き `shutil.copytree` の control 木を渡す |
| 同上 | `_condition_gate_family_valid` / `_INERT_CONDITION_GATE_PAIRS` / `verdict_s6` | S6 verdict が関門緑を要求する箇所 |
| `orchestrator/tests/test_t316_sandbox_probe.py` | `test_condition_gate_dominates_ccbench_configure` ほか inert pair 系 | 現行の受理・拒否を固定する test |
| `orchestrator/campaign/backoff_sweep.py` | `patchharness.checkout` / `patchharness.applied` の組 | 緑に到達している対照実装 |
| `orchestrator/campaign/condition_meaning_gate.py` | `_run_process` の stderr 規則 / `_configure_compile_commands` | 関門本体。**本 wave では変更しない** |
