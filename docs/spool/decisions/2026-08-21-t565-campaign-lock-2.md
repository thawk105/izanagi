---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: t565-campaign-lock
seq: 2
---

## {{D:campaign-lock-scope}}. campaign単位advisory flockの配置・scope境界・既知の限界

**決定 (1): `campaign.flock` (実行時advisory flock) は campaign root の外、新設する兄弟ディレクトリ
`output/campaign-locks/` へ置く。** ファイル名は `layout.root` の絶対path正規化
(`os.path.realpath`) をSHA-256し先頭20 hex文字を使う。`campaign.lock` (identity v1/v2 envelope、
`orchestrator/campaign/campaign_lock.py`のcodec対象) とは責務・置き場所とも完全に分離する。

**決定 (2): 保護対象は `run_campaign()` の呼び出しに限定する。** direct-evaluate producer
(`screening_driver.py`, `guided.py`の`cmd_start`/`cmd_evaluate`, `s1_direct_comparison.py`,
`s8b_oracle_driver.py`) と、s4/8c driver自身がcampaign-wide副作用 (WAL recovery・provenance
header・loop_state書き込み) を個々の`run_campaign()`呼び出しの外で行う経路は対象外とする。

**決定 (3): `campaign_claim.py`のclaimがCampaignBusy後にorphanする経路へ、release/cleanup機構を
追加しない。** 既存の手動回収運用モデルに従う。

**決定 (4): cross-node flock保証済みの範囲、cfg_hash衝突・非正規化output_rootの限界を明記する。**
これらはcampaign identity方式・campaign_claim.py既存docstringが既に認めている既存の限界であり、
本waveが新規に導入する劣化ではない。

**理由:**
- `orchestrator/campaign/layer3_report.py:193-198 _artifact_refs()` と
  `orchestrator/campaign/autonomous_trial_completeness.py:2924-2943,2986-2992`
  (`_cross_binding_campaign_files`/`_cross_binding_artifact_refs`) は、campaign root配下の
  全regular fileを`rglob`し、後者は永続化済み`artifact_refs`との完全一致を要求する
  (`declared_paths != current_files`で拒否)。段3敵対相談2レンズが独立に発見: `campaign.flock`を
  campaign root内に置くと、本機能デプロイ前に一度でもcompleteness checkを通過した既存campaignを
  resumeした際、新規作成される`campaign.flock`が旧reportの`artifact_refs`に無く、正しい
  campaignがfail-closeで誤って拒否される。root外に置けば両関数の`rglob`対象に構造的に入らず、
  この回帰が原理的に起きない。
- `orchestrator/tests/test_campaign.py:4770-4792`のAST inventoryが、`run_campaign()`を通らない
  direct sinkが複数実在することを裏付ける。`docs/decisions.md` D528決定(9) (2026-08-18) が
  同型の境界 (「`run_campaign`を通らないproducerのruntime gateは本Dで作らない」) を既に確定して
  おり、本waveも同じ構造の境界に整合させた。scopeを拡張すると変更面が
  (direct-evaluate sink 4系統 + driver family全体) に大きく広がり規律5に反する。
- `orchestrator/campaign/campaign_claim.py:383 acquire_claim()`のdocstringが「claimはcrash後も
  残す。stale判定、自動削除、releaseは意図的に存在しない」と明記している。`loop.py`側で
  best-effort unlink等のcleanupを足すことは、この既存契約を側面から回避する行為であり、
  2026-08-18 rulingsのユーザー原則 (「条件を迂回する機構を作らない」) に反する。`CampaignBusy`は
  claim取得後に起こりうる**既存の**post-claim failure集合 (build失敗・WAL破損等) に1つ加わる
  だけであり、質的に新しい危険を導入しない。
- cross-node flockの実測根拠はT-361 (worklog 149) とT-402 (worklog 571、
  `output/insights/2026-08-16_t402-flock-execution-host/RESULT.md`) の2 host pair
  (bnode001/bnode005、bnode003/bnode004)・`/work`・`/home`に限られ、同RESULT.md §5が
  「1 host pairの1回の観測は十分条件ではない」と明記している。sanctioned probe driverの
  投入枠 (`FLOCK_LEG_ONLY_SUBMISSION_LIMIT=1`) はT-402で消費済みのため、本waveでの
  新規cross-node実測はしない。cfg_hashは32-bit prefix (SHA-256先頭8 hex) のみで、
  衝突時は`IdentityMismatch`がflock取得後に初めて検出される既存の限界であり、
  `campaign_claim.py`自身のdocstringも「clone毎に別out_rootを与えた実行同士はこのleafでは
  排他できない」と同種の限界を認めている。

**却下した選択肢:**
- `campaign.flock`をcampaign root内 (`CampaignLayout.flock_file` property) に置く — 段2 codex
  planの当初案。上記のとおりcompleteness check回帰を招くため不採用。
- `layer3_report.py`/`autonomous_trial_completeness.py`へ`campaign.flock`のbasename除外ロジックを
  追加する — 証拠chain・completeness判定という規律2隣接領域への変更面拡大が大きく、
  `campaign.lock`/`wal.jsonl`は現状無除外でも実害が無いため一貫性の悪い変更になる。root外配置
  なら変更不要。
- scopeを拡張しdirect-evaluate producer・driver familyもcampaign_lockで保護する — D528決定(9)の
  先例に反し、変更面が大きく規律5 (段階導入・盛らない) に反する。scope拡張を望む場合は別taskで
  起票できる。
- `campaign_lock()`実装を`bench_lock()`と共通化する — `bench_lock`の既存blocking/default/error
  契約まで変更するため、小さい独立実装を追加する方を選んだ。
