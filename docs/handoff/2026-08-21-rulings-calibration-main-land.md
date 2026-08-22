# 2026-08-21 rulings / rr80-rr20 calibration dev-wave / main land handoff
- 目的: rr80/rr20 calibration を AI/ツール側で安全に登録できる dev-wave 経路を裁定・準備し、裁定と tooling を local main へ land する。rulings session から実測を直接起動しない
- 状態: 作業中
- 最終更新: 2026-08-22
- 基準コミット: a0937f4e0fd8b8e71f1902f41a5cd2c9d3e82dfa (worktree: worktree-rulings-20260821-calibration-registration、branch tip)

## 2026-08-22 追記 (別セッションによる受入・land 引き継ぎ)

- 引き継ぎ時、job dir に残っていた直近受入全走 (attempt 1, wave_tip=42343ef0) が
  `attributable-red` (3 ノード) だったことを一次資料から発見。後続 fixture fix (f8d32b0e) で
  解消済みと個別実走で確認したが、修正後の受入全走は未再走だった。
- 段6敵対レビュー2本 (Codex) + 親の手動変異検査により、`calibration_rratio` binding 一致検査に
  不一致拒否を確認するテストが皆無 (SURVIVED) と判明。Codex fix 子がテストを追加 (commit
  a0937f4e)、同じ変異で KILLED を確認した。
- レンズA 指摘の `--job-script` override 経由 ratio 詐称は既存 [T-424] の scope として scope 外。
- 本 wave と無関係に `check_ai_provenance.py` の全史監査で commit `09ce607b`
  (ccbench pin bump、AI-Agent trailer 皆無) を発見。ユーザー判断待ちとして
  `{{T:legacy-ccbench-pin-bump-missing-provenance}}` を worklog fragment (seq2) へ記録した。
- 詳細は `docs/spool/worklog/2026-08-22-rulings-20260821-calibration-registration-2.md`。

## dev-wave 改善候補 (段8 用)

1. handoff の「検証済み」記述は、直前の受入全走 receipt/red-check の有無と status を明示
   参照すべき。今回、handoff 本文には targeted test の pass しか書かれておらず、job dir に
   残っていた attributable-red な受入全走の存在が本文からは分からなかった (F1 の型に近い、
   一次資料未照合のまま docs を根拠にした事例)。段7 記録時、直前受入全走の
   receipt/red-check ファイルパスと status を handoff へ 1 行明記する運用を検討する。
2. 段6 read-only codex レビューが稼働中に、親が同じ tracked file へ一時変異 (mutation testing)
   を加えると、レビュー対象がレビュー中に dirty tree へ変わりうる。今回はレビュー側が
   committed HEAD 基準で判定して事なきを得たが、これは保証された挙動ではない。親の
   tracked file 一時変異検査は、同じファイルを読む read-only レビューの完了後か、
   明確に別タイミングで行う運用を検討する。

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- `/rulings all` のユーザー裁定内容を確認し、AI/ツール側の calibration 登録方針を明文化した。
- `tools/pegasus/submit_certify.sh` と `tools/pegasus/certify_calibration.sh` の rr80/rr20 workload
  binding tooling、および `orchestrator/tests/test_pegasus_calibration_workload.py` の targeted test を準備した。
- `python3 tools/run_tests.py orchestrator/tests/test_pegasus_calibration_workload.py` は 5 passed。
- `python3 tools/check_docs.py` と `python3 tools/spool_fold.py --dry-run --show-diff` は成功。

## 未完の作業と次の一手 (具体的に)

既存の推奨方針は受け入れる。ただし rr80/rr20 calibration の取得・検証・登録を人間の手作業に
残すことは受け入れない。既存の自己比較、schema、acquisition receipt、hash binding、fail-closed
gate を維持したまま、AI/ツールが計算ノードで測定し、自動 publish できる dev-wave 経路を用意する。
この rulings wave はその裁定と tooling を main に land するだけで、実測・collector・登録 job は起動しない。

正式 H1/H2 launch、g1→g2 activation、D145/T-424/T-272 の別の承認・閉包をこの較正登録だけで
代行したとは扱わない。

## 現状確認

- `output/env/pegasus/calibration/registered/` の既存2件は rr50。rr80/rr20 は未登録。
- `tools/pegasus/submit_certify.sh` と `tools/pegasus/certify_calibration.sh` は workload を rr50 に固定。
- `pegasus02` は login node として重い計測を直接行わない。queue `gen_S` は利用可能で、計測は PBS job body で行う。
- land lease は別 holder が保持中。holder を奪わず、空くまで land を保留する。
- 直接投入した `930578.nqsv` (rr80) / `930579.nqsv` (rr20) は Queued のままキャンセル済みで、登録 artifact は生成していない。

1. tooling の commit、関連テスト、provenance、docs check を完了する。
2. canonical acceptance を通したうえで、spool fragment を land lock の中で fold し local main へ ff-only land する。
3. rr80/rr20 の submit・計測・collector・登録確認は、別 dev-wave の scope として起票する。
4. push は行わない。remote への反映は人間が行う。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- `pegasus02` では重い計測を直接起動しない。queue `gen_S` は確認済みだが、投入は login-side submitter、
  build/calibration は PBS compute job body の責務。
- land lease は別 holder が保持中 (`holder=b73c0a8f1038`、2026-08-21確認)。holder を release/steal せず、
  空くまで land を保留する。
- 既存登録2件は rr50。rr80/rr20 の artifact は未登録であり、今回の rulings wave では投入しない。
  別 dev-wave で走らせる場合も、rejected attempt の JSON を修正して登録してはならない。
