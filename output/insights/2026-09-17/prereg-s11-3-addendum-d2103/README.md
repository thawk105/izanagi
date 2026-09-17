# 事前登録 §11.3 の「生成器は本書を読まない (D1377)」を D2103 の現在地で追補訂正した

`authority: none`
`default_effect: no-state-change`

2026-09-17。wave `dev-wave-prereg-s11-3-addendum-d2103`、branch `worktree-dev-wave-prereg-s11-3-addendum-d2103`
(worktree dir は `.claude/worktrees/dev-wave-t2743-prereg-s11-3-addendum` のまま — 下記「段 4 再裁定」)。
起点 local main `abc7085ae6e1a69dc294c4f827ed7949e6df5305`。
**実装面 (D95 決定 2) の差分は 0。** 成果物は `docs/phase3-b4-reflux-ablation-preregistration.md` §11.3 への追記 1 箇所
(追加 17 行・削除 0 行)、worklog fragment、本スナップショットである。可変状態の正本は worklog 末尾と現行 phase doc であり、
本書ではない。job dir (log・brief・fold dry-run・受入受領証の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-prereg-s11-3-addendum-d2103/`。

## 依頼と答え

依頼 (worklog entry 1595 [T-2723] の残存項、台帳 ID 未起票): 事前登録 §11.3 末尾の「生成器は本書を読まない (D1377)」が
陳腐化しているので、§11 の「未裁定の案であり規範ではない」位置づけを保ったまま追補で訂正する。§5 の値セルと条件契約の
bytes は変えない。docs のみ・実装差分ゼロ、`check_docs.py` と凍結 hash test を通す。追補 1 箇所だけ。

答え: §11.3 第 3 項「材料レポート側の接続」の末尾、既存の [T-2424] (2026-09-08) 追記の直後に、D2103 の現在地を書いた
追記 1 箇所を置いた (`verbatim/prereg-s11-3.diff.txt`)。

- 現物確認で分かったこと: 依頼が名指す 1 行「現行の生成器は本書を読まず無条件に floor 不在を渡す (D1377)」は、
  同じ項の [T-2424] 追記が既に「現在の実装を表さない」と訂正している。したがって今回の純増は「読まず」の再訂正ではなく、
  T-2723 / D2103 (2026-09-17) 以降の読み方の変化である。
- 追記の内容: (a) floor セルの読取は文書全体の prefix 走査をやめ、`p3_b4_admission_record.py` から切り出した §5 固定表の解析
  (見出し境界・fence / comment 除外・12 非空行と exact header・10 label 集合・不可視文字拒否) と責任者行の 1 セル受理述語
  (D2079) を通る。(b) 不在は strip 後 raw の `未記入` だけ、NFKC 異体は拒否。(c) 他欄の sentinel と expectation 行は floor
  経路で検査しない。(d) D1377 の向き (生成器は floor を caller から受け取らない) は変わらず、floor は §5 固定表の pin から
  しか入らない。(e) §11.3 末尾項の条件「材料レポート側の floor 接続が裁定され実装されていること」は満たされたが、他の条件は
  未充足で §7.1 の 4 分類は実効化していない。
- 非規範性の維持: 追記は [T-2424] / [T-2465] 追記と同じ型の「§5.1 の解除条件も §6 の前提条件も 1 つも緩めず、`未記入` を
  有効な floor と見なさず、測定の開始も §5 の記入も本書の発効も許可しない」を含む。

## 段 4 再裁定 (段 5 で判明した新事実、DW-O12)

brief の (P1)「台帳 ID 未起票のため D70 の採番 (現存最大 T-2742 + 1) で T-2743 を起票する」は、`docs/spool/worklog/README.md`
の規則「次の一手として一度も登録されていない wave 自身に、fold 未実行時点の想像で T 番号を割り当てて `title:` へ書いては
ならない。wave slug と branch 名にも未採番の T 番号を使わない」に反証された。是正: 追記文から `[T-2743]、` を外し
(焦点走 1 の完了後)、branch を `worktree-dev-wave-t2743-…` から `worktree-dev-wave-prereg-s11-3-addendum-d2103` へ rename、
fragment の title と本 dir 名は角括弧 ID なし。worktree dir 名は EnterWorktree が付けたまま残る (dir / branch 不一致)。
`verbatim/s1-brief.md` は反証前の原文で、そこに現れる番号は撤回済みであり何も指さない。

## 実測 (login node、bounded local。計測 checkout = 本 worktree、docs 差分のみ)

| 検査 | 結果 |
|---|---|
| `python3 tools/check_docs.py` (追記後 2 回、`[T-2743]` 除去の前後) | 違反なし、rc=0 |
| §5 表 (行 154〜167) の sha256 | 変更前後で `1762b7cc5158e080…` が一致 (T-2465 wave が記録した値とも一致) |
| §5 全体 (`## 5.` 〜 `## 6.` 直前、§5.1 の解除条件を含む) の sha256 | 変更前後で `cf809f11d2f4a7ea…` が一致 |
| 文書の変更前 sha256 `d4ade414d59db81e…` の逆引き (DW-O09 / F370) | tracked file・`output/` ともに pin 0 件 |
| 凍結 hash の対象範囲 | `p3_b4_analysis_prereg_consumer.py` の §5.1.1 raw bytes (H4 見出しで切り出し)。§11.3 は範囲外 |
| 焦点走 1 (`[T-2743]` 入り bytes、実文書を直読 6 file + binding support 経由 4 file) | 826 passed、370.2 s |
| 焦点走 2 (最終 bytes、`test_p3_b4_analysis_prereg_consumer` / `_floor_artifact_issuer` / `_admission_record` / `_material_report`) | 207 passed、181.1 s |
| 焦点走 3 (記録 commit 後、`test_s8b_repo_scan_invariant` + `test_s8c_preregistration_invariant`) | 15 passed、6 skipped (全件 `IZANAGI_GROWTH_HOLD_V1` / `tracked_files`、走っていない)、35.4 s |
| 三軸語・placeholder の機械走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search` | rc=0 (hit なし) |
| `python3 tools/check_ai_provenance.py` (記録 commit 後、導入時点〜HEAD) | 10,908 件、新規違反なし |
| 変異 matrix | 実装面差分 0 につき免除 (DW-S04) |
| 受入全走 attempt 1 (`acceptance-final-1`、tested main `b4631a92e`、post-claim merge 後 tip `f994871c7`、07:23:59〜07:43:23) | **F945 型の非帰属赤**: 24,499 passed / 67 skipped / 2 error (shard-0 の `test_t1259_qsub_env_delivery_probe.py` 2 件が setup error)、子 rc=1、受領証未発行、待ち手 rc=70。junit.xml の traceback は `git -C <wave worktree> ls-files --others --exclude-standard -z` の 30.0 秒 TimeoutExpired |
| 同 tip・同 file の単独再走 (`run_tests.py --force-dispatch`、2828.nqsv、D612 の 3600/600 上書き) | 51 passed / 16.94 秒、job Elapse 23 秒、rc=0 (非再現) |
| 受入全走 attempt 2 (`acceptance-final-2`) | `DW-O18` に従い同型を 1 回だけ再走する。本記録 commit を含む tip に対して投入し、child-green でなければ land しない。受領証は job dir |

F945 の再発は failures fragment (`docs/spool/failures/2026-09-17-dev-wave-prereg-s11-3-addendum-d2103-1.md`) に追記した。
恒久対応は既報のまま (timeout 拡大・fixture の stub 化・除外・gate 新設はしない)。

## 段 8 (自己改善)

候補 1 件: 「未起票の依頼に T 番号を想像で採らず、branch・slug・title は主題だけにする (正本 `docs/spool/worklog/README.md`)」を
`DW-S01` (L1) へ 1 文統合する試行は `check_docs.py` の L1 unique footprint 10,771 > 予算 10,625 bytes で赤。D782 が委任する
D730 の原則 (予算に阻まれた項目は実施しない、例外は同型の実害が独立 3 例以上) に照らし、実害は spool README が記す 2 例
(2026-08-21 の見出し番号、2026-09-02 の branch 名) で、本 wave は land 前に是正した near miss につき例外に届かない。
実施せず編集を戻した。上限引き上げに至らないので報告のみで、裁定パッケージは作らない。

## 残存 (scope 外、記録のみ)

- §11.0「事実 (重要な限定)」段落にも同型の [T-2424] 追記があり、D2103 の反映は無い。依頼が「追補 1 箇所だけ」と定めるので触らない。
- §11.3 末尾項の条件列挙 (「かつ材料レポート側の floor 接続が裁定され実装されていること」) の本文は不変。充足は追記で述べた。

## 工数

codex 子 0 本 (docs-only、DW-C00 の既定軽量版)。親の実測は check_docs 2 回、sha256 照合、焦点走 2 本 (login)。
