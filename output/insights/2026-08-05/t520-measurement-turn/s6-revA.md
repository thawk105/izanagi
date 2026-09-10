## 1. 受理集合の不変性

### ADM-01 / should-fix

- 対象: [docs/pegasus-runbook.md:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:373)、[decision fragment:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:25)
- 引用: 「未実測の 4 本は grandfather として追認済み」「昇格は…実測してから」
- 実読した事実: hook 上の4本は既に `class=local-ok` で、未実測なのは `evidence` である（[hooks/guard_bash.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/hooks/guard_bash.py:202)、[hooks/guard_bash.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/hooks/guard_bash.py:292)）。
- 何が壊れるか: 「昇格」が class の昇格なのか evidence の更新なのか曖昧である。将来のセッションが、grandfather 4本を実測まで拒否対象だと解釈して受理集合を縮める、または `legacy-admitted` を一般的な昇格根拠と誤解する可能性がある。
- 修正案:  
  「未実測4本は grandfather 例外として `class=local-ok` を維持し、`evidence=legacy-admitted (未実測)` とする。新規・`unknown` entry を `local-ok` へ変更するにはユーザー実測を要する。4本の再実測時に更新するのは evidence であり、grandfather 自体を実測証拠として流用しない。」

## 2. 事実整合

### FACT-01 / must-fix

- 対象: [tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29)
- 引用: 「分類 registry も、実行直前に未分類を拒否する gate も存在しない」
- 実読した事実: registry は [hooks/guard_bash.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/hooks/guard_bash.py:183) に存在し、未登録を拒否へ倒す処理も [hooks/guard_bash.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/hooks/guard_bash.py:596) に存在する。D175 決定1も同じ事実を規範化している。
- 何が壊れるか: 将来のセッションが機械防壁は存在しないと判断し、Pegasus 実行体の追加時に registry 更新や拒否確認を省く。結果は hook 拒否、または文書と防壁の再ドリフトになる。
- 修正案:  
  「機械強制は部分的である。`tools/pegasus/` 配下には `hooks/guard_bash.py` の admission registry と未登録 fail-closed gate があるが、全 tools・全実行面を覆うものではない。`tools/check_docs.py` の保証範囲も限定される。」
- 補足: worklog fragment 自身がこの矛盾を「scope 外 real 所見」と認めている（[worklog fragment:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:24)）。既存 registry の事実を直すだけであり、machine-readable 化の設計へは踏み込まないため、land をまたいで残す理由にはならない。

### FACT-02 / must-fix

- 対象: [docs/decisions.md:8624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/decisions.md:8624)、[docs/decisions.md:8638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/decisions.md:8638)、[docs/failures.md:2779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/failures.md:2779)、[decision fragment:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:16)
- 引用: D175「grandfather を追認するかはユーザー裁定に残す」、F123「恒久的な測定経路は [T-520] として裁定へ返す」
- 実読した事実: 新 fragment は D175 決定4の「裁定待ち」だけを明示的に解消している。D175 決定2とF123の古い pending 記述について、どの裁定が supersede したかを記録していない。
- 何が壊れるか: 将来のセッションが D175/F123 だけを引き、grandfather または測定手番を未裁定として再度停止・再裁定へ送る。さらに grandfather を撤回して受理集合を変えるおそれがある。
- 修正案: decision fragment に次を明記する。  
  「本決定は D175 決定4およびF123恒久対応末尾の『測定経路は裁定待ち』を supersede する。D175 決定2末尾の grandfather 裁定待ちは、2026-08-05 の [T-522] 裁定により追認へ supersede 済みである。」

512 MiB、三値分類、certified peak の式、exact task 表については所見なし。§7.0 の該当箇所は変更されておらず、相互にも整合している。

## 3. 手番の実効性

### TURN-01 / should-fix

- 対象: [docs/pegasus-runbook.md:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:386)、比較対象 [同:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:348)
- 引用: 「commit / argv / 入力の総 bytes と件数 / 繰り返し数」
- 実読した事実: 記録契約には、これらに加えて `memory.max`、測定日、観測ピークが必要である。
- 何が壊れるか: 将来のAIが列挙された項目だけで依頼し、ユーザーから分類記録として不完全な結果が返る。後続セッションが不足情報を推測して certified peak を登録するか、再測定を要求して手番が空振りする。
- 修正案:  
  「§7.0 の測定手順と記録項目一式を指定し、commit / exact argv / 入力の総 bytes と件数 / `memory.max` / 繰り返し数 / 測定日、および各回の観測ピークを返してもらう。」

既に記録済みの `local-ok` 経路の通常利用を禁止する記述はなく、この点は所見なし。

## 4. 迂回の誘発

### BYPASS-01 / must-fix

- 対象: [docs/pegasus-runbook.md:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:383)、[同:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:392)、[decision fragment:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:34)、[worklog fragment:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:45)
- 引用: 「hook が未配線の実行面 (…)」「迂回 4 系統 (…)」
- 実読した事実: 新規本文とfragmentが、未閉鎖の具体的な実行面・綴りを列挙している。
- 何が壊れるか: 将来の自動化がこの列挙を利用可能な抜け道の inventory と解釈し、そこで得た値を分類証拠へ持ち込む。禁止文を併記しても、攻撃面の具体化自体は不要である。
- 修正案: 個別名を除き、次のように抽象化する。  
  「hook が未配線または解析できない実行面を分類測定に使ってはならない。」  
  T-518については「[T-518] に記録済みの未閉鎖系統」とだけ参照し、runbook・decision・worklogに再列挙しない。

## 5. scope

所見なし。変更は手番の明文化、(c) の不採用記録、grandfather 裁定の事実反映に留まり、machine-readable registry の設計・コード・hook・test は変更していない。FACT-01の文面訂正も既存実装の事実反映であり、族再設計そのものではない。

## 6. spool fragment の整合

FACT-01、FACT-02、BYPASS-01が該当する。加えて以下がある。

### SPOOL-01 / should-fix

- 対象: [diff.patch:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t520-measurement-turn/diff.patch:57)
- 引用: 「`?? docs/spool/...`」
- 実読した事実: `diff.patch` は2 fragmentを未追跡ファイルとして列挙するだけで、本文差分を収録していない。
- 何が壊れるか: 後続のland前レビューが patchだけを証拠にすると、decision/worklog fragmentを未読のまま受理する。
- 修正案: 2 fragmentを含む完全な patch を再生成する。

worklog fragmentが「完了」ではなく「更新」として残余(b)を保持している点は、runbook・briefと整合しており所見なし。

## 総括

1. **land 可否: NO-GO**
2. **must-fix: 3件**
   - FACT-01: `tools/README.md` が実在する registry / fail-closed gateを不存在と記述。
   - FACT-02: D175決定2・4およびF123の古い「裁定待ち」の supersede が不完全。
   - BYPASS-01: 新規本文とfragmentが未閉鎖の実行面・綴りを具体的に列挙。
3. 読めなかった指定物はない。sandbox制約に従いテストは実行しておらず、worklog fragmentが主張するテスト結果・commit対応は独立確認していない。動的なhook発火も未確認で、判断は hook source、D175、F123、変更後文書の静的実読に基づく。