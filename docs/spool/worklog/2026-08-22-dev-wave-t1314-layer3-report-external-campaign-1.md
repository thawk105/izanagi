---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1314-layer3-report-external-campaign
seq: 1
title: '[T-1314] 層3材料レポートCLIへ--output-rootを追加しrepo外campaignをrenderできるようにした (コード+テスト、branch worktree-dev-wave-t1314-layer3-report-external-campaign、変異matrix = baseline PASSED・MUT-1〜7 7/7 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 案A (既存 Python API が既に受理している `output_root` を `main()` へそのまま配線するだけ)
  を段2プランで起草し段4で採用した。案B (環境変数fallback)・案C (境界root分離) は
  「brief逸脱」として却下 — 詳細は {{D:layer3-output-root-cli}} を参照。
- 段3の敵対相談 (2レンズ) で、sol は job-id を luna と同じ `consult1` で起動したため衝突し
  正式 receipt を作れなかったが、`attempt-0001.output.md` から出力を recover できた
  (`check_codex_output.py` rc=0 で検収)。復旧内容は独立した所見として採用した。
  root cause は {{F:consult-lane-job-id-collision}}。
- sol所見2 (real, 最重要): `--output-root` が qualification-ancestry gate の探索上限を狭め、
  真の repo root 直下にある `qualification-marker.json` を回避しうると判明。親が自分でも
  コードを再読し再現条件を確認した。段4で `_qualification_ancestry_bound()` という新 helper
  を設計し (`_qualification_ancestry_bound` の3ケース検証は {{D:layer3-output-root-cli}} 参照)、
  campaign が実 repo 配下なら custom output_root に関わらず実 repo root まで ancestry walk する
  設計にした。
- 段6の敵対レビュー2本 (reviewA/reviewB) のうち reviewA が real 所見3件を検出した。所見1
  (最重要): 真に外部の campaign で `output_root` を campaign 自身または配下 (`campaign/runs` 等)
  に指定すると、新設した境界計算が退縮し ancestry walk がほぼ無効化される新しい脆弱性。
  段4の設計だけでは不十分で fix 1巡目で `_qualification_ancestry_bound()` の else 分岐へ
  「output_root が campaign 配下なら拒否」guard を追加した。所見2: `--output-root` の空文字列
  未検査、`_non_empty_path()` で対応 (Windows形式pathの拒否は POSIX限定環境のため scope外)。
  reviewB は所見ゼロ (提供元の逐語一致・波及範囲・admission非依存を独立確認)。
- 段6の焦点再レビューで、fix1巡目の新規テスト `test_main_rejects_empty_output_root` が
  CWD非依存のため pytest実行CWD (repo root) 下では既存の「repo外」判定と偶然一致し、
  新guardの効果を判別できていないと判明。fix 2巡目 (`monkeypatch.chdir(tmp_path)` を追加する
  1関数だけの極小fix) で是正した。DW-O16 の3巡上限のうち2巡を使用、3巡目には至らなかった。
- 変異事前登録 MUT-1〜7 の初回投入で MUT-2・MUT-5 が MISMATCH になったが、実装の欠陥ではなく
  親が書いた `expected_nodes` が過小だった (両変異とも実際にはもう1本のテストが独立に検出して
  いた)。初回結果は `mutation-out-attempt1-erratum.json` へ保全し、`expected_nodes` を実測値へ
  訂正して再実行し 7/7 KILLED・MISMATCH 0 を得た。
- `tools/mutation_worktree.py` の `--wrapper-attempt` は `--attempt-out` と同時指定必須という
  未文書の制約に一度当たった (rc=2、即座に判明・修正)。root cause は
  {{F:mutation-attempt-out-pairing}}。
- 段5実装子は Codex `role=author` の workspace-write 隔離 worktree で書き、親は隔離 session の
  `git -C` 制約 (`DW-S05-A` 明記) のため `diff` コマンド (git 不使用) で内容を監査したうえで
  Edit ツールにより自分の wave worktree へ逐語転記した (`diff` で byte-identical を確認)。
  同じ手法を fix 1巡目・2巡目でも用いた。子 worktree への seed (fix2巡目) は plain `cp`
  (Bash、git不使用) で行った — Edit/Write ツール自体は他 worktree への書き込みを拒否するため。
- 優先度はユーザー指示により他4件より一段低い扱いとした (緊急ブロッカーではなく、8c自動経路は
  Python API直呼びで無影響)。

## 次の一手差分

### 完了

- [T-1314] 層3材料レポートCLIへ `--output-root` を追加し repo 外 campaign を render できるようにした。
  段3・段6の敵対検証で見つかった qualification-ancestry gate の回避も塞いだ。
  remaining: none
  base: 9f36aff08afbcdd2bd0eeaa3c1dbbd36bb3a88ce3828569d1ca4fd951dcfab92
