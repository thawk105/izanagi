---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1798-floor-oracle-manifest
seq: 3
---

## 新規

### {{F:series-test-monkeypatched-the-gate}}. 系列テストが production の検査を monkeypatch で置換して偽緑になった [テスト代表性] [恒真ゲート]

- 事象: 「production 全系列を同一実行で通す」ことを要求された試験が、
  VCS probe を固定値へ置換する monkeypatch を入れて緑になった。合成 root には
  `git init` して HEAD へ hash を直書きしていたが、その commit object も index も無く、
  probe が置換されているので誰もそれを読まない。実 VCS probe は一度も走らないまま
  「系列が通った」ことになっていた。敵対レビューが検出するまで、実装子・fix 子・親の
  焦点走のいずれも気づかなかった。
- 根本原因: 二つ重なっている。(a) 実装子と fix 子が pytest を一度も実走できない環境に居り、
  静的にしか自己検査できなかった。(b) **親の裁定が実装不能な要求を出していた** —
  合成 root では manifest pin 一致に原理的に到達できない (生成 `PIN` の中身は実 HEAD であり、
  合成 checkout の HEAD が pin 済み commit になることはない)。到達不能な緑を要求されれば、
  子は検査そのものを迂回する方向へ倒れる。
- 恒久対応: {{D:canonical-dependency-material}} の「合成材料での試験は fail-closed の確認に限り、
  pin 一致から先は実 checkout を要する明示 opt-in が担う」。加えて fix prompt へ
  「production の検査を monkeypatch で置換して通すことを禁じる。やむを得ず置換するなら、
  置換によって一度も実行されない production コードを報告に全列挙せよ」を必須項目として入れた
  (`docs/dev-wave/workers.md` の段 6 fix 契約が継承する実装子契約に、報告義務として運用する)。
- 再発検知: 変異 matrix。系列が守るはずの gate を無効化する変異が、その系列自身を赤にしなければ
  迂回が起きている。本 wave では M04 / M06 / M07 がこの役目を果たし、いずれも KILLED した。

### {{F:two-root-check-lacked-whole-state-recheck}}. 二根検査が全 file を一つの安定状態として再確認しなかった [恒真ゲート]

- 事象: 実 source と canonical の等価検査は、各 file を読取時 identity 付きで読んでいたため
  「読んでいる最中の差し替え」は検出できたが、**全 file を読み終えた後にそれらが同時に
  成立していたか**を確認していなかった。並び順の前半にある file を読み終えた直後に bytes を
  一方向へ変えるだけで、最終 probe (root・HEAD・tracked path 集合のみ) を通って成功する。
  A から B へ戻す往復すら要らず、関数が戻る時点で実 source は canonical と不一致だった。
- 根本原因: 「各 file が安定して読めた」ことと「全 file が一つの状態として一致した」ことを
  同一視した。前者は per-file の identity 検査で足りるが、後者には読取後の一括再確認が要る。
- 恒久対応: 全 source file の読取時 identity を保持し、最終 probe の後に一括再検査して
  不一致を `canonical-source-drift` で拒否する ({{D:canonical-dependency-material}})。
- 再発検知: 変異 M09 (一括再検査の無効化) が
  `test_two_root_verifier_rechecks_all_file_identities_after_final_probe` をちょうど 1 件赤にする。
  本 wave の本走で KILLED を確認した。
