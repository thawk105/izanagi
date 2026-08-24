---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1462-t1464-checkpoint-integrity
seq: 1
title: '[T-1462]+[T-1464] checkpoint値チャネルの整合性を修正した (コード+テスト、branch worktree-dev-wave-t1462-t1464-checkpoint-integrity、変異matrix = baseline PASSED・MUT-1 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

裁定根拠は2026-08-21ユーザー裁定「推奨通りで」、一次資料は
`output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md` §1・§4。

- [T-1462] (§1択b): `orchestrator/campaign/p3_s4_loop.py` の `project_whiteboard()` に、
  `state_from_dict`/`layer3_report.build_report`が既に使う共有validator
  `assert_whiteboard_value_domains()`をそのまま呼ぶ形で値域検査を追加した ({{D:t1462-project-whiteboard-value-domains}})。
  D607がproducer側 (in-memory射影経路) を明示的にscope外とした残余を閉じる続き。
  3 driver共有の単一関数のため12呼出し全てを一度に閉じる。docstring5箇所を実態に合わせて更新。
- [T-1464] (§4択c): `_redacted_transport_error()`の早期return (transport_receipt is None時に
  secret置換より前に即returnしていた) を除去し、secret置換の後に制御文字除去+500文字cap
  (truncation marker付き) を両分岐共通で適用した ({{D:t1464-redaction-mechanism-deviation}})。
  9呼出し全てがこの一箇所の拡張で保護される。

command引数原文の「length-cap付きrepr」からの逸脱: 段2プラン・段3敵対相談 (両レンズ独立) が、
無条件`repr()`は既存exact-match test 3件と衝突し`:2237`→`:4627`の二重処理経路で非冪等になると
実測確認したため、制御文字除去+length-capへ変更した。詳細と却下理由は
{{D:t1464-redaction-mechanism-deviation}}参照。目的 (未信頼値の運搬量上限化・保存形式衛生化)
は原案と同値だが、規律6が理想とする「prompt-injection遮断」までは達成しないと敵対レビューが
指摘した — この区別を正直に記録する (達成できるのは保存形式の構造衛生と運搬量の上限化)。

段3敵対相談2レンズが、trigger driver (`_assert_trigger_proposal_contract()`) と8c自動経路
(`parse_planner()`) は既存の別防壁で既に無効値を止めており、T-1462の新設gateが実際に
無効値を止めるのはcore/sort driverのhuman-supervised経路に限ることを実測で検出した。

段6敵対レビュー2本がreal所見2件を検出 (docstring1箇所の記述残存、T-1464新設テストの
境界値(500/501文字)不足) し、fix1巡で両方closedにした。fix子の投入前に統合snapshot patchを
job dirへ退避した (DW-S06-B)。

段5実装子・段6レビュー2本・fix1本の計4回、`evidence_status=invalid`/`launcher_rc=1`で
`-o`成果物が書かれない事象に当たった。`codex_exit_code=0`で内容は健全
(`check_codex_output.py` rc=0) であり、`attempt-0001.output.md`から復旧して採用した。
原因はF217 (web_search重複key) でもF223 (非NFC行) でもない新しい変種と判明し
{{F:codex-jsonl-backslash-unterminated-string}}として登録した。

実装commit (`b66cca12`) は AI-Agent trailer 3行 (researcher/reviewer/author、いずれも
`product=codex; model=gpt-5.6-luna; reasoning=max`) + manager (`product=claude;
model=claude-sonnet-5; reasoning=default`) で記録した。

親の焦点走 (`test_p3_s4_loop.py`+`test_p3_autonomous_workload_trial.py`+
`test_p3_s4_loop_trigger_gating.py`、459件) は緑 (52.68秒、失敗0件)。変異事前登録MUT-1
(project_whiteboard内のvalidator呼出しbypass) はbaseline PASSED (120件緑)・MUT-1 KILLED
(期待node3件 `test_project_whiteboard_rejects_invalid_{direction,magnitude,result}` と
完全一致、他への副作用なし)。

Pegasus計算ノードのqueue混雑 (待ち70件超まで悪化した時間帯があった) により、親の焦点走・
変異matrix・provenance監査のdispatchが複数回queue-wait-timeoutで失敗し、都度
`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`で猶予を延ばして再試行した (最終的に
queue改善後に成功)。混雑対応中に「lease coordination compute saturation」
セッションから2点の重要な共有を受けた: (1) 自分のPBS job (qdel実施状況) の実態確認要請へ
receipt.json全件を突き合わせて回答し、孤児0件・並行dispatch2本を確認して以後逐次化した、
(2) `dev_wave_wait.py acceptance`の`preclaim-history-provenance`段が固定300秒timeoutで
`check_ai_provenance.py`のPBS jobをqdelせず孤児化するバグが見つかり、修正が入るまで
**受入の新規投入を一時停止**するよう要請された。本waveはまだ受入段階に達していなかったため
直接の影響はないが、段9のland前に解除確認が必須。プレーンな`run_tests.py`直接呼出しは
この制約の対象外。

2026-08-24 に別 context が本 wave を引き継いだ。未着地のまま 529 commit 遅れていた branch へ
local main tip `f02b4d62` を取り込み、受入全走と land へ進めた。以下はその再開 context の記録で
ある。受入全走は本記録 commit を tip として投入するため、その結果は本文に書かず receipt を
一次資料とする。

2026-08-22 に別セッションから受けた「受入の新規投入を一時停止」要請は、原因が解消済みであることを
実測で確認してから投入した。`tools/dev_wave_wait.py` の `_STAGE_TIMEOUT_SECONDS` は 300 秒から
1200 秒になり、stage subprocess の打ち切りは SIGKILL 即時でなく SIGTERM 先行 +
`_STAGE_GRACEFUL_TERMINATION_SECONDS` = 100 秒の猶予に変わっている。これは
`dispatch_compute.py` の qdel を含む cleanup を発火させるための変更で、孤児化の経路が塞がれた
ことを意味する。停止要請から本 wave 再開までの間に main が 529 commit 進み、その多くが受入緑を
必須とする land である点も傍証になる。

依頼が名指しした `p3_autonomous_workload_trial.py` の編集面重複を先に再検査した。main 側で
この file を触った commit は `74b3854f` の1本だけで `_finish_trial()` 付近 (3104行付近)、
本 wave は `_redacted_transport_error()` (2197行付近) で交差しない。全 registered worktree を
走査した結果、同 file を触る生存 wave は `worktree-dev-wave-t1611-terminal-reason-match` の1本
だけで、こちらは1320行と4041行だった。行・関数とも重複なしと確定した。

merge は自動で競合ゼロだったが、両親が同じ実装面 file を触るため
`check_ai_provenance.py --message-file` が Codex `role=author` を要求した (rc=1)。
staged merge のままでは launcher の authority gate が rc=2 で子を拒否するため、
{{D:merge-author-two-commit-split}} の 2 commit 分割を採った
({{F:staged-merge-blocks-codex-author-launch}})。一発 merge した index の `git write-tree`
`0a4644213e665de28840bd6cc0e364b02c37dcc0` を先に控え、2 commit 後の `HEAD^{tree}` が
同一であることを照合した。分割が内容を変えていないことは機械で示せている。

合成監査の Codex `role=author` 子は「破れなし」と判定し、patch を byte 同一で再適用した。
子が実測で確かめた点: `_redacted_transport_error()` の呼出しは9箇所で、consumer は message を
構造解析せず journal / report / cell 間の同一性だけを検査するため受理集合は変わらない。
exact 一致を検査する既存 test 4箇所はいずれも短い単一行で値が変わらない。main 側 `74b3854f` が
追加した `AutonomousTrialError` の文言は `run_trial()` では sanitizer を通らず、
`run_origin_trial()` 経由でも短い単一行なので不変。切詰めの最終長は常に500字 (marker 14字 +
先頭486字) で、除去対象は U+0000〜U+001F・U+007F〜U+009F・U+2028・U+2029、U+0020 は残る。

段8の自己改善候補は1件だった。DW-O17 は「実装面 path が両親と異なれば Codex `role=author` へ」と
書くが、その状態で子を起動する手順を持たない。本文への統合は L2 単節予算 1000 bytes に対し
DW-O17 が既に 974 bytes を使っており入らないため、予算値の引き上げ可否をユーザー裁定へ返し、
手順自体は decisions と failures へ routing した。

再開 context の子は Codex `role=author` 1本のみ。1回目は staged merge のため launcher rc=2 で
起動前に拒否され、2回目は `evidence_status=invalid` で不採用になった (本 wave の
`{{F:codex-jsonl-backslash-unterminated-string}}` の5回目の再発。今回は仕事自体が正規表現
リテラルを扱う内容だったため決定的に再現した)。台帳に記録済みの recover 手順で成果物を回収した。
待ち手 `dev_wave_wait.py producer` は2回とも rc=70 を返したが、いずれも子は既に終了して
`.done` を書いており、rc=70 を子の失敗と読まず現物照合で救えた。

## 次の一手差分

### 完了

- [T-1462] project_whiteboard()にvalidatorを追加し値域検査を閉じた。
  remaining: none
  base: 99ebd1fa142d971b9be33a4b929c821b8e61eee93617622cd96bdaf421874e19
- [T-1464] _redacted_transport_error()を早期return除去+制御文字除去+length-capへ拡張した。
  remaining: none
  base: f2a7a02d207327c732b8f2d97e75005533415259f403c9d021940a558caca544

### 新規

- {{T:dw-o17-merge-author-launch-procedure}} **P2・新規**: 両親が同じ実装面 file を触る merge で
  Codex `role=author` 子を起動する手順を DW-O17 へ統合する。L2 単節予算 1000 bytes に対し
  DW-O17 が既に 974 bytes を使っており入らない。予算値の引き上げか、DW-O17 の可逆な圧縮か、
  台帳ポインタのみで済ませるかをユーザー裁定にかける。
