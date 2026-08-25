---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1606-known-violation-entries
seq: 2
---

## 新規

### {{F:gate-defined-but-not-wired}}. 防壁の代替として必須化した検査を、本番監査経路へ配線せず test からしか呼んでいなかった [恒真ゲート] [手順漏れ]

- 事象: 逐語 mirror を畳む条件として append-only 履歴検査を必須と裁定し、実装子は
  公開関数として正しく実装した。しかし呼出しは pytest node だけで、`main()` からは
  呼ばれていなかった。**land の全史監査関門でも発火しない**状態で、焦点走は 353 passed の
  緑だった。段 6 の敵対レビュー 2 本が独立に同じ穴を指摘して初めて判明した。
- 根本原因: 親の裁定文が「検査を置く」とだけ書き、**どの経路から呼ぶか**を書いていなかった。
  実装子への指示にも呼出し点の指定が無く、「関数を用意する」で契約が閉じてしまった。
  テストが公開関数を直接呼ぶため、未配線でも緑になる。
- 恒久対応: 防壁の代替として検査を新設する裁定では、**呼出し点 (どの CLI 経路・どの分岐から
  呼ぶか) を裁定文へ明記**し、`main()` から呼ばれることを固定する test を同じ wave で置く。
  本 wave では `test_authoritative_main_invokes_append_only_history` と
  `test_authoritative_main_folds_append_only_failure_into_rc2` を置き、配線除去の変異が
  この 2 本に殺されることを確認した。
- 再発検知: 新設した検査関数を repo 内で grep し、**production 側の call site が
  0 件でないこと**を確かめる。call site が test file にしか無ければ本 F。

### {{F:append-only-blind-to-evil-merge}}. append-only 検査が merge commit 自身の改変を見なかった [変異] [テスト代表性]

- 事象: `git log --no-renames --diff-filter=MD -- <dir>` で着地済み file の変更を拒否する
  検査を置き、merge 経由の改変・削除・rename の負例も用意して全部緑にした。
  しかし変異検査で `-m` を外す変異が**生存**した。実測すると、既存の merge 負例は
  **side branch 側の commit が改変を持つ**形なので `--full-history` だけで捕まり、
  `-m` の有無に依存していなかった。**merge commit 自身が entry を改変する evil merge** は
  `-m` が無いと完全に不可視で、現行 command が 4 行出力するところ 0 行だった。
- 根本原因: 負例を「merge を経由するか」で設計し、「**改変を持つ commit が merge 自身か
  親側か**」で分けていなかった。path 限定 `git log` は既定で merge の差分を出さないため、
  この 2 つは別の経路である。この repo では親が作る merge commit が日常的であり、
  evil merge は最も現実的な偽造経路だった。
- 恒久対応: merge を含む履歴検査の負例は、**改変の所在 (merge commit 自身 / 親側 commit)**
  で必ず 2 分する。`-m` と `--full-history` はそれぞれ別の経路を担うため、両方に単独の負例を置く。
  file type 変更 (`T`) も `MD` に入らないため diff-filter へ明示する。
- 再発検知: 履歴検査の変異で option を 1 つずつ外し、**それぞれに専用の kill node があるか**を
  見る。option を外しても死なない検査は、その option が守る経路の負例が無い。

## 再発

### F217

- **再発: 2026-08-25** — 段 3 の敵対相談 lens B が `evidence_status=invalid` /
  `accepted=false` で **4 回連続**不採用になり、完成済み成果物 4 本 (22923 / 20446 / 19932 /
  20051 bytes) と約 70 分を失った。**既知の 2 原因を両方とも反証した。**
  (1) web 検索は全 4 件で使用ゼロ。1 件で文字列が hit したが中身は子が走らせた test の nodeid
  (`..._is_rejected[web_search]`) であり実検索ではない。
  (2) 非 NFC でもない — 失敗 2 件・成功 1 件とも `is_normalized('NFC')=True`、結合文字 0。
  さらに最終 artifact は判定条件を全部満たしていた (session_meta 1 / turn_context 1 /
  model・effort・cwd 一致 / 不正 JSON 0 / 最長行 474727・210887 で上限 4MiB 未満 / 末尾改行あり)。
  **成功した run の方がむしろ大きい** (rollout 6615347 bytes、最長行 2240502)。
  したがって `invalid` は最終 artifact の性質ではなく、**tailing 中に立った sticky flag** であり、
  外部から最終 artifact を見ても再現できない。**第 3 の原因が存在する。**
  回避できた手段は prompt の縮約だけで、重い command を禁じ調査範囲を絞った版は 6 分で rc=0 に
  なった (因果は未証明)。4 回目の stderr には guard_bash が repo 全体の `rg` と
  checker の import を 4 回拒否した記録が残っていた。
