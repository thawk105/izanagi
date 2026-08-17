静的検査のみ。pytest は未実走である。

### B-01 / must-fix — v5 移行と seed が稼働中 wave と自己 land を詰ませる

根拠: `s2-plan.md:28-52,104-143`、`tools/dev_wave_wait.py:232,2971-3000`、`tools/dev_wave_land.py:70-97,573-583,674-805`、`docs/pegasus-runbook.md:833-858`、`tools/dev_wave_land.py:2966-3088`。

失敗シナリオ:

- v5 の land 側が先に main へ入る。
- 既に v4 receipt を取得済みの wave は、`_receipt_object` の exact schema/field 検査で拒否される。
- land は receipt 検査より先に D254 の全史 provenance を実行するため、最大 480 秒の監査、lock の解放・再取得、計算資源を消費してから拒否される。
- 6 本が同時に撮り直す場合、受入だけでも D253 の実測 1055--1338 秒を 6 倍、すなわち 6330--8028 秒消費する。平均「1 時間に 1 本」は最大待ち行列長や land 待ちを保証しない。
- 自己 wave も、main waiter を実行して v4 receipt を発行してしまえば、v5 land に拒否される。seed が有効なのは「tested_main に marker がなく、tested_tip に marker が一つあり、tip 側が v5 writer」である場合だけである。

提案する修正:

v5 land を先に有効化しない。最小案は、v4 receipt を持つ全 wave を旧 consumer で land してから、waiter と land を同一変更で切り替えること。分割できない場合は、seed receipt を識別する明示的な transition version と対象 commit を追加し、D254 の高価な監査前に安価な schema 判定を置く。

自己 land の時系列は次の条件なら成立する。

1. main は旧 waiter、tip は marker 一つの v5 waiter。
2. seed 判定で tip source を実行し、v5 receipt を発行。
3. land が seed protocol と tip の raw source hash を検証。
4. land 後、main は marker 一つの v5 waiter。
5. 次回以後は active 判定で main source を実行。

この順序、特に v5 と marker の結び付きを実装で保証できない限り NO-GO である。

### B-02 / must-fix — `os.execve` が全体 deadline と attempt 数をリセットする

根拠: `s2-plan.md:72-100`、`tools/dev_wave_wait.py:4078-4115`、`docs/pegasus-runbook.md:833-847`。

失敗シナリオ:

queue 待ち、merge、または D254 関連処理で既に時間を使った後、active mismatch が発生する。`os.execve` は元の argv だけを渡し、絶対 deadline、attempt 番号、既使用時間を渡さない。新しい Python process は deadline を最初から開始し、最大 2 attempt を再び許す。結果として、runbook の実行上限と D253 の lease TTL を越えた再試行が発生する。

提案する修正:

bootstrap 用環境変数に invocation id、絶対 deadline、attempt 数、bootstrap 済みフラグを渡し、子 process が検証して同じ deadline を使う。残り時間が不足する場合は exec せず fail closed にする。環境変数を信用するだけでなく、receipt と lease 状態にも同じ invocation id を結び付ける。

### B-03 / must-fix — temp source の path/inode 契約が現行 binding と衝突する

根拠: `s2-plan.md:54-78`、`tools/dev_wave_wait.py:105-180`、`tools/dev_wave_wait.py:735-825`。

失敗シナリオ:

計画は外部 temp file を `python3 -I <temp>` で実行し、binding 後に pathname を unlink する。しかし現行 binding は basename が `dev_wave_wait.py`、親 directory が `tools`、regular file、同一 inode であることを要求する。通常の temp path はこの条件を満たさず、exec 直後に source unavailable、rc70 となる。pathname を exec 前に unlink すれば、子 process が `__file__` を開けない。

提案する修正:

専用 temp directory の下に厳密に `tools/dev_wave_wait.py` を作り、file と directory を fsync する。子 process が binding を完了するまで pathname を残し、子 process 内でのみ unlink する。外部 path を許可するなら、許可 root、mode、inode、symlink 不可、content hash、module origin を明文化する。実 worktree を変更しない実 subprocess test を必須にする。

### B-04 / must-fix — lease を保持した exec の失敗時に lease ownership が壊れる

根拠: `s2-plan.md:88-100`、`tools/dev_wave_wait.py:2782-2815`、`tools/wave_land_window.py:640-845`、`docs/decisions.md:11614-11671`。

失敗シナリオ:

- `ACQUIRED` で release 成功後に exec が失敗すると、queue ticket と lease を失う。再試行は queue の後ろからになり、別 wave が同じ lease を取得できる。
- release の結果が不明なのに exec すると、旧 lease が残ったまま新 process が `HELD_SELF` になる可能性がある。
- 失敗処理と外部 retry が重なると、同じ holder 名に fencing token がないため、旧側の release が新側の lease を消す lease-loss 経路がある。
- `HELD_SELF` を保持したまま exec すると、D253 の保持意味論は守れるが、child が元の owner、TTL、heartbeat の世代を知らない。exec 失敗時に誰が release するかも未定義である。

提案する修正:

`os.execve` を lease handoff として正式化し、owner id、lease generation、取得 main、TTL deadline を引き渡す。release 結果が不明なら exec しない。`HELD_SELF` は新 process で再 claim せず同一 generation を renew する。可能なら lease を跨ぐ exec ではなく、同一 process 内で authority source を切り替える。

### B-05 / should-fix — exact consumer の更新範囲が不足している

根拠: `tools/dev_wave_land.py:70-97,573-583,682-683,674-805`、`tools/dev_wave_wait.py:232,2971-3000`、`orchestrator/tests/test_dev_wave_wait.py:2125-2145,3833,8903,9530`、`orchestrator/tests/test_dev_wave_land.py:215-260,740-825,1002`、`docs/pegasus-runbook.md:840-872`。

更新対象は waiter と land だけではない。receipt builder、land の exact field set、waiter の v4 literal、land fixture、schema rejection tests、runbook の v3 retry 説明と v4 説明を全て更新する必要がある。

一方、`tools/run_tests.py` と `tools/check_acceptance_reds.py` は outer receipt v4/v5 の consumer ではない。ただし独自 schema と acceptance argv 判定を持つため、変更対象外であることをテストで固定すべきである。`tools/check_docs.py:320` は waiter path pin であり receipt schema consumer ではない。

提案する修正:

v5 の consumer census を作り、path key、schema key、field key、role key、source hash key の全てを列挙する。D487 は過去の正本なので直接改変せず、新しい決定で v5 移行と v4 発行済み receipt の扱いを明示する。

### B-06 / should-fix — 12 改訂 + 17 新設は二重管理を増やす

根拠: `s2-plan.md:165-217`、`tools/dev_wave_land.py:74-97`、`orchestrator/tests/test_dev_wave_wait.py:2125-2145,9532`、`docs/failures.md:7579-7605`、`docs/failures.md:4473-4486`。

field 集合、schema version、marker 個数、lease state を各テストに逐語で複製すると、producer、consumer、fixture、台帳テストの四重管理になる。F290 と F146 は、まさにこの種の重複が acceptance を落とした既往である。

失敗シナリオは、waiter は v5、land fixture は v4、または field list の一部だけ旧版という状態である。単独テストは通っても acceptance full run が長時間後に unrelated red となり、受入を余分に消費する。

提案する修正:

wire contract の独立した golden fixture は一つだけ残す。他のテストは fixture factory を使い、挙動だけを検証する。17 本は、seed、active、exec failure、lease、source binding、land acceptance、downgrade rejection という独立 mutant に対応するものだけに縮小する。各テストを残す理由を mutation 対応表で示せないものは段 4 の上限から外す。

### B-07 / should-fix — 実測値の母集団と期間が再現できない

根拠: `brief.md:33-38`、`handoff.md:30-35,62-69`、`handoff.md:77-94`。

「23 receipt 中 22 child-green」「24 commit」「凍結 pin 0」は、集計 predicate が記録されていない。artifact tree には outer receipt、retry/nested receipt、red-check sidecar、v3/v4 receipt が混在している。例えば `rulings-full6-20260817/acceptance-receipt-1.json:1` は v4 だが、別の同日 receipt は v3 である。したがって、top-level のみか、nested を含むか、sidecar を除くか、retry を deduplicate したかで母数が変わる。

24 commit も全 ref、merge commit、実際の対象編集を区別しなければ編集頻度ではない。

提案する修正:

23 行の集計 manifest を保存する。各行に path、outer/sidecar、attempt、schema、verdict、wave id、tested_main、tested_tip、受付時刻、queue wait、child duration を記録する。commit 集計は main と各 wave ref を分け、merge を除外した unique edit と acceptance rework を別集計にする。

### B-08 / should-fix — 「凍結 pin 0 件」は識別子 key を落とす可能性がある

根拠: `brief.md:43-45`、`handoff.md:72-94`、`orchestrator/tests/test_frozen_artifacts.py:41-111,236-245`、`tools/check_docs.py:320`。

`FROZEN_MANIFEST` は output path を key にする manifest であり、対象四 file がないことは path-key pin の不在しか示さない。`dev-wave-acceptance-receipt/v4`、role 名、`waiter_blob_sha`、`_ACCEPTANCE_RECEIPT_FIELDS`、source hash、file-set digest のような識別子 key は別検索が必要である。

反証手順:

- 対象 root と cutoff を固定する。
- 四 path の全文検索を行う。
- schema 名、field 名、role 名、source hash 名、generator 名、manifest key を構造化 file に対して key/value 両方で検索する。
- `git -S` で導入・削除履歴も確認する。
- path-key pin と identifier-key pin を一つずつ既知の positive control とし、scanner が両方検出できることを確認する。
- live code、active docs、test fixture、historical archive を分類する。

この証拠がない限り「0 件」は結論ではなく未検証である。

### B-09 / nit — runbook の byte 予算は実装停止理由にならない

根拠: `docs/pegasus-runbook.md:791-960`、`tools/check_docs.py:183-205,253-260,560-590,2550-2675,4366-4405`。

`check_docs.py` の byte budget は command file、dev-wave skill、reference layer 等にあり、`docs/pegasus-runbook.md` §7.3 用の byte budget はない。従って、§7.3 の改訂量だけを理由に実装を止める必要はない。

ただし、現在の runbook には v3 retry 説明と v4 receipt 説明が併存している。v5 化では両方を更新し、§7.0 の dispatch 構造と waiter path pin を壊さないこと。

### B-10 / should-fix — `waiter_source_sha256` は独立証明ではない

根拠: `s2-plan.md:104-129`、`brief.md:49-53,58-68`、`docs/decisions.md:16921-16954`。

新 field は actual execution source の自己申告であり、D403 の tip blob gateとは異なる。実行側が誤った source を使った場合でも、期待値を自己申告できる実装なら、land は独立に検証できない。

提案する修正:

この field を「独立証明」ではなく defense-in-depth と明記する。source binding の実測 hash、expected main/tip blob、temp inode binding を別々に検証し、self-report だけで acceptance narrowing を主張しない。

判定: **NO-GO**。最小の是正は、v5/seed を lease handoff と deadline 引き継ぎ込みで設計し直し、v4 稼働 wave の移行手順と独立した receipt consumer census を先に確定すること。

## 総括

所見は 10 件（must-fix 4、should-fix 5、nit 1）。

最大の阻害要因は v5 移行時の v4 receipt 巻き添えである。

自己 wave は seed の時系列を正しく実装すれば land 可能だが、現計画だけでは保証されない。

temp binding、deadline、lease handoff のいずれか一つでも未定義なら恒久的な restart loop になる。

pytest は未実走であり、この報告は静的検査結果である。

GO/NO-GO: **NO-GO**。