## 所見一覧

[重大度 must-fix] registry の class 変更だけでは段 9 後の収集は unblock されない

- どこ: `tools/collect_wave_usage.py:187-211`、`orchestrator/campaign/site_policy.py:95-98`、`hooks/guard_bash.py:268-289,604-615,1195-1205`
- 何が現に効かないか: `collect_wave_usage.py` は registry を読まず、`site_policy.refuses_heavy_work(site)` だけで login/suspect を `blocked` にする。現在の `unknown` は hook でも拒否される。class を `local-ok` に変えても、非 Pegasus パスの `local-ok` は registry loader と hook wrapper が拒否する。仮にそこを緩めても、collector 自身が再び site policy で blocked にする。
- 根拠: registry loader は非 `tools/pegasus/` の `local-ok` を拒否し、collector には registry lookup が存在しない。
- 対応案: login での収集を本当に認めるなら、registry、hook、site policy、collector の受理契約を結線し、受理集合を広げる必要がある。これは現プランの metadata 修正を越えるため、**裁定パッケージへ返す**。本 wave の目的を evidence/class の修正だけに限定するなら、brief の「収集が blocked のままにならない」という主張を修正する。

[重大度 must-fix] evidence 案の単位とコマンド成否が不正確

- どこ: `measure-evidence/README.md:8-29`、raw の `run-0`/`run-2` job log、`s2-plan.md:177-181`
- 何が食い違うか: 正の delta は 6 走中 5 走で、1 負 delta の除外数は合っている。しかし最大値は `20,635,648` bytes = 約 `19.7 MiB`（約 `20.6 MB`）であり、案の `20.6 MiB` ではない。さらに ledger の 5 走はすべて collision による `rc=2` で、成功した収集結果の「valid runs」と読める。
- 根拠: run-0 は `+19.7/+11.6/+11.9 MiB`、run-2 は `+18.1/negative/+11.5 MiB`。`+128 MiB` を MiB で加えるなら最大値は約 `147.7 MiB` であり、`148.6 MiB` も単位混在である。
- 対応案: `shared nqs-jsv.service`、専有 cgroup なし、`§7.0` 非準拠、`rc=2` の5正 delta sample、負 delta 1走除外を明記した evidence に直す。**本 waveで直す**。

[重大度 should-fix] P2 は実質的に measured-table の sentinel 回避である

- どこ: `tools/check_docs.py:2992-3026`、`3029-3075`、`s2-plan.md:187-191`
- 何が現に起きるか: measured 表の期待集合は evidence が文字列 `runbook §7.0 実測` と完全一致する entry だけで作られる。別の文字列にすれば ledger は表の期待集合から外れる。checker は custom evidence の測定方法、raw 数値、`non-certifying` の真偽を検証しない。
- 根拠: `reason` は projection 対象外だが、`class` と `evidence` は完全一致検査される。したがって機械的な P2 の読みは正しいが、これは実測の妥当性検査ではない。
- 対応案: custom evidence を使うなら、文字列に明示的に `not §7.0 isolated-scope evidence` を含め、実測表から外した理由も読者に分かるようにする。checker に非正本測定の schema 検査まで持たせるなら、**裁定パッケージへ返す**。

[重大度 should-fix] `reason` は projection 外でも自由ではない

- どこ: `s2-plan.md:176-189`、`tools/check_docs.py:2916-2926`、`orchestrator/tests/test_hooks.py:1753-1759,2413-2424`
- 何が食い違うか: check_docs の projection は `path/class/evidence` だけを見るため、その意味では `reason` は projection 外である。しかし hook テストは registry 全 entry の `reason` と `primary_gate` を含む完全な golden と比較する。
- 根拠: registry の reason を変更すると、check_docs は通っても `test_hooks.py` の固定期待値が古いままになる。
- 対応案: reason を変更するなら hook golden と関連説明を同時更新する。**本 waveで直す**。プランの「自由に変えてよい」は「projection だけでは検出されない」に限定する。

[重大度 should-fix] DW-S09 の rc 非 0 が安全だという保証が不足している

- どこ: `docs/dev-wave/core.md:107-112`、`docs/decisions.md:10385-10394`、`tools/check_docs.py:4553-4579`
- 何が食い違うか: D220 の「収集は development-flow gate ではない」という引用は正しい。したがって段 9 完了後に collector が `rc=1/3` でも、完了済みの DW-O23 を論理的に取り消すものではない。ただし check_docs が保証するのは helper、経路、文言順序だけで、collector の rc を無視して後続処理することまでは検査しない。
- 根拠: DW-S09 の固定検査は `tools/dev_wave_land.py` の経路と受入文言を見ており、collector の失敗を gate にしないことは見ていない。
- 対応案: DW-S09 と `--help` に「収集は post-gate の記録であり、失敗は wave 完了を覆さない」と明記し、呼び出し側もその契約を守る。文言だけなら **本 waveで直す**。stage 9 の実行制御自体を変更するなら **裁定パッケージへ返す**。

[重大度 should-fix] consumer の更新面が一部暗黙である

- どこ: `orchestrator/tests/test_collect_wave_usage.py`、`orchestrator/tests/test_claude_session_ledger.py`、`orchestrator/tests/test_hooks.py`、`orchestrator/tests/test_check_docs.py`、`docs/README.md`、`docs/dev-wave/core.md`
- 何が取り残され得るか:
  - collector の現在の `main() == 0` 前提、blocked/error/missing の rc、分割形式の `--project` argv 期待。
  - ledger の `population.request_identity` 固定値、cross-file の request/message collision fixture、strict issue matrix。
  - hook の registry 全体 golden。class を変えない場合でも reason/evidence 変更で影響する。
  - check_docs の synthetic projection、measured sentinel、期待 path 集合のテスト。
  - README は詳細を `--help` に委譲しており schema の直接 reader ではないが、DW-S09 は collector の非 gate 契約を補足すべき。
- 根拠: repository 内に wave usage artifact の本番 reader や receipt validator は見当たらない。Codex の `receipt.json` と `tools/mutation_fanout_contract.py` の generic な `status` は別 schema であり、更新対象ではない。
- 対応案: 上記の実際のテストと docs の契約を更新する。receipt 系まで変更するのは **裁定パッケージへ返す**。

[重大度 should-fix] `unknown` の採用は妥当だが、測定対象 argv の範囲を過大評価してはいけない

- どこ: `tools/claude_session_ledger.py:29-38`、`tools/collect_wave_usage.py:94-106`、`docs/pegasus-runbook.md:411-423`
- 何が食い違うか: ledger には `DEFAULT_MAX_FILES=25`、総 bytes、line、record、request などの hard cap が存在するので、現 reason の「input caps が incomplete」は「cap が存在しない」という意味なら不正確である。一方、raw は default `--json`/25 files の測定であり、collector の通常 argv は `--max-files=1000` も渡し得る。default 測定を任意 argv の local-ok 根拠にはできない。
- 根拠: §7.0 は記録した argv/input にだけ保証を限定し、canonical な専有 scope 測定でなければ local-ok にしない。
- 対応案: hard cap は存在するが、cap 境界と production argv の専有測定が未完了、と reason/evidence を書く。**本 waveで直す**。将来の argv 別 admission は **裁定パッケージへ返す**。

[重大度 nit] L1 byte 予算のプラン記述は実コードと一致する

- どこ: `tools/check_docs.py:256`、`docs/dev-wave/core.md:109-112`、`s2-plan.md:44-50`
- 検証結果: 上限は `10,625` bytes、現在の L1 は `10,624` bytes で余白は1 byte。プランの短縮置換後は `10,614` bytes。固定 literal の route/acceptance/helper は各1箇所のままで、検査を壊さない。
- 対応案: この主張は維持してよい。**本 waveで直す**対象は計画どおりの文言圧縮のみ。

## scope 外だが real な所見 (裁定パッケージ候補)

- 段 9 収集を login で実際に受理するには、registry の分類変更だけでなく、hook の非 Pegasus 例外、site policy、collector の admission 消費を一つの安全な契約にする必要がある。これは現在の三 scope では未分離である。
- D233 の「分類測定はユーザー端末の手番」は、ユーザーが AI に「適切な場所を選ぶ」ことの委任で自動的に解除されない。AI が §7.0 の専有測定を自分で再実行してよい、と変更するなら F159/F160 の再裁定が必要である。
- 「任意 argv を分類済み」とする admission は §7.0 の記録範囲を越える。`--max-files=25` と `--max-files=1000` を同一 class で扱うなら、argv 範囲の定義が必要である。

## 親 brief への反論 (P1〜P5 のどれに、なぜ)

- **P1**: `unknown` を維持する判断自体は妥当。ただし class を変更しても collector の site-policy blocker は残るため、「registry barrier を直せば段 9 収集が unblock する」という含意には反論する。
- **P2**: sentinel の完全一致が実測表への入口である、という読みは正しい。しかし custom evidence は検査を回避できるだけで、方法論を検証しない。非正本測定であることを明示した代替文字列が必要。
- **P3**: message replica の dedup 方針は方向として妥当。ただし raw には `request_id_collision` も存在するため、同一 message replica と説明できる場合だけ requestId collision を抑制し、それ以外は従来どおり fatal に残す必要がある。
- **P4**: rc 分離は D220 と整合する。だが、collector を post-gate の記録として扱う実行側の保証は check_docs にはない。
- **P5**: 内側の equals 形式だけでなく、外側の parser が `-` で始まる project slug を option と誤認する問題も実在する。プランが外側の正規化を追加する点は必要である。

## 総括

最大の must-fix は、registry class の変更と段 9 収集の unblock が結線されていないこと、そして evidence 案の単位・rc 表現が不正確なことである。`check_docs.py` は現状静的には違反なしだったが、pytest は実走していない。実装変更は行っていない。