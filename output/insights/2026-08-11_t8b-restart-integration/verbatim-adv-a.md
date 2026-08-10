静的検査のみを実施し、ファイル編集・pytest 実走・緑判定は行っていない。判定は **NO-GO** である。

### A-1 — 固定 FD は scheduler spool の証拠にならない

- **所見 ID**: A-1
- **区分**: BLOCKER
- **主張**: `9<"$0"` は caller が選んだファイルを開くだけであり、scheduler が実行した spool bytes との独立照合を恒真化する。
- **具体的な失敗経路**: プランは [plan.md:86](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:86) で committed blob・receipt hash・FD 9 bytes の一致を要求するが、FD の供給は [plan.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:94) の shell redirection にすぎない。有効な floor job の計算ノード内で nonce・`PBS_JOBID`・reservation 環境を継承した子が、wrapper を経ず `python3 ...s8b_floor_campaign.py ... 9<tools/pegasus/floor_campaign.sh` と起動すれば、FD・receipt・commit の三者はすべて同じ committed bytes になり admission を通る。現 admission が scheduler identity として読むのも環境の nonce/job ID だけである ([certified_writer_admission.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/certified_writer_admission.py:64))。これは scheduler record/spool を独立取得せよという [brief-addendum.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/brief-addendum.md:30) を満たさない。
- **成果物への影響**: spool wrapper を通っていない起動が `mode=official` と `eligible_for_refreeze=true` を得て、偽の floor 値が freeze v2、oracle レポート、最終 certified 選択へ流入できる。

### A-2 — receipt が認可と revision authority に格上げされている

- **所見 ID**: A-2
- **区分**: BLOCKER
- **主張**: receipt を「必要十分な unlock」とする設計は、D86(8) が禁じた「記録があるから認可済み」を再導入し、独立に承認されていない任意の clean revision まで official にする。
- **具体的な失敗経路**: `submit_floor.sh` は現在の任意の clean `HEAD=R` を `SOURCE_COMMIT` にし ([submit_floor.sh:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/submit_floor.sh:193))、同じ値を receipt に書く。一方プランの revision gate は `HEAD == receipt.source_commit` であり ([plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:75))、承認済み revision、main ancestry、ユーザー指示が指した revision のいずれとも比較しない。したがって無人 background process が任意の clean commit `R` で実 qsub すれば、正規 spool job であっても全条件を通る。artifact は人間実行と AI 実行を byte-level で区別できず、認可の実体ではないことが [decisions.md:3797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/docs/decisions.md:3797) と [brief-addendum.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/brief-addendum.md:45) に明記されている。
- **成果物への影響**: official の受理集合が「ユーザーが指示した revision」ではなく「receipt を自己生成できる全 clean revision」へ広がり、そのコードが作る floor・freeze・レポートが正規成果物として扱われる。

### A-3 — private core が public 13 seam 拒否を迂回する

- **所見 ID**: A-3
- **区分**: BLOCKER
- **主張**: admission を `_run_campaign_core` に置いても、public wrapper だけで seam を拒否する限り、official 測定値を caller 注入関数で作れる。
- **具体的な失敗経路**: public `run_campaign` は 13 seam を拒否する ([s8b_floor_campaign.py:2763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2763)) が、直接呼べる `_run_campaign_core` は `build_fn` 以外の `measure_fn`、`probe_fn`、`prepare_fn`、`execution_receipt_fn` 等を受理する ([s8b_floor_campaign.py:2805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2805))。プランはここから `_floor_preflight_fn` を除くだけである ([plan.md:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:110))。有効な admission 状態で `_run_campaign_core(..., mode="official", measure_fn=fake)` を直接呼べば、自己検査は同じ fake sessions から floor を再計算するため整合して通り、最終的に mode だけから eligibility が立つ ([s8b_floor_campaign.py:3219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:3219))。
- **成果物への影響**: caller が選んだ throughput が正規 `result.json`、floor、freeze v2 の `floor`、oracle の閾値へ入り、certified 選択を変える。

### A-4 — `VerifiedFreeze` は forgeable かつ可変である

- **所見 ID**: A-4
- **区分**: BLOCKER
- **主張**: exact `VerifiedFreeze` 型の確認だけでは、検証した freeze bytes と実行に使う document の同一性を保証できない。
- **具体的な失敗経路**: `VerifiedFreeze` は公開 constructor を持つ frozen dataclass だが、内部の `document` は mutable `dict` である ([s8b_freeze_io.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_freeze_io.py:30))。caller は `VerifiedFreeze(document=改変済みdict, sha256=承認済みv1 hash)` を直接構築でき、また admission 後に別 thread から dict を変更できる。disk 側の allowlist/preflight が正規 bytes を検査しても、core はその後 `freeze_doc.document` を直接使って cell を列挙する ([s8b_floor_campaign.py:2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2881))。プランの「exact `VerifiedFreeze`」条件 ([plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:79)) には object と captured raw bytes の同一性、sealed constructor、deep freeze がない。
- **成果物への影響**: certificate には正規 v1 SHA が記録される一方、実測 cell・configuration・floor は別 document 由来となり、freeze proof chain とレポートが虚偽の参照を持つ。

### A-5 — admission が downstream proof chain から消える

- **所見 ID**: A-5
- **区分**: BLOCKER
- **主張**: 非直列化 snapshot と certificate v1 不変を同時に採ると、ratified verifier は W-1 admission を一度も検証せず official artifact を受理する。
- **具体的な失敗経路**: プランは snapshot を直列化せず ([plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:73))、certificate v1 と resume schema を変えない ([plan.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:91))。現 certificate は freeze SHA、clean digest、protocol SHA、時刻、run ID の5値だけである ([s8b_floor_campaign.py:1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1759))。journal の exact schemaにも submission receipt、source commit、spool hash はなく ([s8b_ratified_freeze.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:223))、ratified equality chainにも対応する edge がない ([s8b_ratified_freeze.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:146))。したがって A-3 等で作った self-consistent artifact と真に admitted な artifactを downstream は区別できない。
- **成果物への影響**: 一度候補が人間承認されれば、ratified freeze、oracle report、budget ledger、certified 選択のすべてが admission 証拠なしで緑になる。certificate v2／journal／ratified verifier の変更は現 brief の scope 外なので、明示的な再裁定候補である。

### A-6 — T-749 の fallback に二度目の読込み窓がある

- **所見 ID**: A-6
- **区分**: MUST
- **主張**: captured raw と receipt が不一致のとき legacy `verify()` へ戻す設計は、ファイル差替えにより receipt にない drift を CLI だけ緑にできる。
- **具体的な失敗経路**: canonical path に、現行 source/head へ合わせた legacy verifier 合格文書 `D` を置いて helper に capture させる。その後、T-080 の正規 bytes `L` へ atomic swap すると、`verify_receipt()` は canonical file を再読して `active-valid` を返す ([t080_freeze_migration.py:1957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:1957))。captured `D` は receipt と不一致なので、プランの step 8 ([plan.md:156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:156)) により legacy fallback へ進む直前に `D` を戻せば、`verify()` が path を再読し ([s8b_holdout_freeze.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:826)) 合格する。また adapter 自体も非発火時に既存 observation を返すため ([t080_freeze_migration.py:2091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:2091))、誤って mismatch 時にも呼べばさらに直接的な恒真化になる。
- **成果物への影響**: 単体 verify の rc／検証報告は未受領 drift に対して赤から緑へ変わる。programmatic oracle gate は不変なので certified 集合は直接変わらないが、運用 preflight・worklog・人間の発効判断が偽の緑を参照する。

### A-7 — W-3 は実際の producer を proof chain に記録しない

- **所見 ID**: A-7
- **区分**: BLOCKER
- **主張**: 新 `s8b_freeze_candidate.py` が v2 を生成するのに、成果物は旧 `s8b_holdout_freeze.py` を generator と記録する。
- **具体的な失敗経路**: transition table は v1→g1 で `/generator/sha256` だけを許し、path の変更を拒否する ([s8b_ratified_freeze.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:127))。プランもこの不一致を認識しながら旧 path を残す ([plan.md:442](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:442))。verifier は記録された旧 path の blob hashだけを検査する ([s8b_ratified_freeze.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:963)) ため、実際に v2 bytes を作った新 module はどの edge にも束縛されない。
- **成果物への影響**: generation document と ratified proof chain が実 producer を偽って記録し、後の再現・監査・レポートは旧 generator を参照する。旧 module 内へ producer を置くか、新しい producer record/path transition をユーザー裁定で追加する必要がある。

### A-8 — output path から凍結・approval・active namespace へ到達できる

- **所見 ID**: A-8
- **区分**: BLOCKER
- **主張**: 「既定出力なし」「basename exact」「AI は実凍結しない」は、protected namespace への書込みを機械的に遮断しない。
- **具体的な失敗経路**: W-3 は `output_path.name` しか制約しないため ([plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:242))、`--output output/s8b-freeze/active/tmp/holdout_freeze.v2.g1.json` が通るほか、parent symlink を canonical freeze directory に向ければ見かけ上 namespace 外から実凍結 pathへ書ける。W-4 はさらに無制約で、既存 writer は parent を自動作成して任意 pathへ書く ([s8b_oracle_manifest.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:772))。`--output output/s8b-freeze/active/<64hex>.json` とすれば active loader が manifest を pointer として parse して停止する ([s8b_ratified_freeze.py:1119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:1119))。W-3 の未知ファイルだけでも official preflight は拒否する ([s8b_floor_campaign.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1663))。hook は事故防止であり認証防壁でなく、Codex には未配線であることも [hooks/README.md:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/hooks/README.md:207) が認めている。
- **成果物への影響**: active resolution が失敗して certified 選択・report・ledger が全面停止するか、正しい create-only filename が先に消費される。「実凍結は人間手番」という所有境界自体は正しいが、それを path safety を省く根拠にはできない。

### A-9 — W-4 の「exact reviewed spec」は任意 schedule を official 化する

- **所見 ID**: A-9
- **区分**: BLOCKER
- **主張**: spec の key 集合が exact でも、その内容を承認済み schedule／freeze の全 cell 積へ束縛しないため、configuration を恣意的に間引いて自明な winner を作れる。
- **具体的な失敗経路**: active freeze の全 holdout を含めつつ、各 holdout について同じ1 configurationだけを置き、`n=1`、任意 `master_seed` の完全 block schedule を作る。`_validate_schedule` は与えられた cell 集合内での完全性しか見ない ([s8b_oracle_manifest.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:259))。builder は holdout が freeze の部分集合であることしか要求せず ([s8b_oracle_manifest.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:729))、binding もその縮小 schedule と一致すれば通る ([s8b_oracle_manifest.py:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:468))。report は manifest の行だけから `expected_cells` を作り ([s8b_oracle_report.py:1713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_report.py:1713))、judge は候補が1件なら `unique-best` にする ([s8b_oracle_judge.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_judge.py:222))。さらに module 自身は official CLI が active ratified freeze を束縛すると約束する ([s8b_oracle_manifest.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:64)) が、プランは任意 `--freeze PATH` を直接 builder に渡すだけである。
- **成果物への影響**: report の `expected_cells` と ledger の予約行数が縮み、本来比較すべき configuration を走らせず、選んだ1件が各 holdout の winner になるため certified 選択を直接改変する。

### A-10 — budget は shape だけで production 値として扱われる

- **所見 ID**: A-10
- **区分**: MUST
- **主張**: W-3 は budget の権威源を持たず、任意の有限非負値を意味的に妥当な candidate として出力する。
- **具体的な失敗経路**: 全 holdout に `10^15` 秒を割り当てた strict JSON も、全値ゼロの JSON も [plan.md:236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:236) の条件を満たす。既存 validator も有限非負と key 集合しか検査しない ([s8b_oracle_manifest.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:626))。候補単体は発効しないが、通常の approval/active 手順後は driver がその値をそのまま limit として読み ([s8b_oracle_driver.py:1161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_driver.py:1161))、ledger reservation に使う。
- **成果物への影響**: 巨大値なら事前登録されたはずの探索予算を実質無効化して追加試行から winner を得られ、ゼロなら全行が budget refusal となって certified 選択が空になる。後段の user approval が budget 数値そのものを承認する契約なのか、別の凍結済み authority から導出するのか裁定が必要である。

### A-11 — R-4 の M2/M4 は一般化しすぎている

- **所見 ID**: A-11
- **区分**: MUST
- **主張**: 「dataclass field を足すと import が倒れる」という実測は素朴な `asdict` 追加だけを否定し、contract hash を維持した toolchain 束縛の不可能性を示していない。
- **具体的な失敗経路**: 現 contract hash が全 dataclass fieldを含むこと ([env_contract.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/env_contract.py:154)) と reviewed golden が import 時に検査されることは事実だが、contract は既に hash-bound な `calibration_ref` を持つ ([env_contract.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/env_contract.py:245))。その実 calibration bytes は gcc path/version と C/CXX build argvを保持する ([calibration-753f…json:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:20))。したがって、これを derived toolchain authority として wrapper の実測値および build manifest と比較する経路は active contract hashを変えずに構成できる。floor は現在 `DEFAULT_CC/CXX` を直書きしている ([s8b_floor_campaign.py:1075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1075)) が、既に site別の `gcc/g++` selector が存在する ([buildcache.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/buildcache.py:454))。`build_v2` は実 compiler path/version の manifest を preimage に含めるため ([buildcache.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/buildcache.py:648))、legacy `cache_key` の default omissionを変更する必要もない。CXX の完全な version 文字列まで既存 calibration が十分かは別途裁定対象だが、M2 から不可能と結論することはできない。
- **成果物への影響**: 不完全な択一で A を選べば activation・floor protocol・selector pin を不要に再凍結し得る一方、B を admission 記録だけに限定すれば source digest／build binary の compiler 束縛が抜け、floor と後続 freeze が異なる toolchain を参照し得る。

### A-12 — 「contract hash に触れないから独立」は proof graph 上で偽である

- **所見 ID**: A-12
- **区分**: MUST
- **主張**: W-1・W-3・W-4 は編集ファイルが分離できても、成果物と発効順序では R-4／W-2を介して直列依存している。
- **具体的な失敗経路**: W-3 は W-1 を通過した `mode=official`・`eligible_for_refreeze=true` の floor result を必要とし、ratified verifier は protocol contract hash、execution receipt、floor source を equality chainで結ぶ ([s8b_ratified_freeze.py:2968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:2968))。W-4 の production consumer はさらに active W-3 freeze を要求する。したがって R-4未裁定・W-2未実測のまま W-3/W-4を「完了」としても、生成できるのは synthetic fixture または実走不能 artifactだけである。加えてプランは g2 candidate を生成可能にする ([plan.md:246](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:246)) 一方、active g2 は `launch_validate` が必ず拒否する ([s8b_ratified_freeze.py:2874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:2874))。
- **成果物への影響**: W-3/W-4が実装済み表示でも certified 選択・report・ledger は生成不能であり、g2を承認・active化すると現行 oracle 全体が launch refusalになる。`contract hash を編集しない` ことを `proof chain から独立` と読み替えてはならない。

## 総括

- **判定: NO-GO**
- 主因は、固定 FD が scheduler spool 証拠にならないこと、receipt が認可・revision authority に化けること、private core／mutable freeze の迂回、admission が downstream proof chainから消えること、W-4が縮小 scheduleで自明な winner を作れることである。
- T-749 は captured bytesだけを検証対象にし、`active-valid` で receipt mismatchなら即赤、legacy fallbackでも pathを再読しない形へ修正すべきである。
- 「実凍結はAI禁止」という所有境界は正しいが、producer の path containment、symlink拒否、approval/active namespace拒否を省く根拠にはならない。

ユーザー裁定が必要な点:

- W-1の認可を非機械的な運用前提に留めるのか、ユーザーが指した revision を束縛する別 authorityを設けるのか。
- scheduler-owned spool evidence の取得方式を、caller-opened FD以外へ変更すること。
- certificate v1不変を維持するか、admission receipt hash・source revision・spool identityを certificate/journal/result/ratified verifierへ通すか。
- W-3の実 producer identityを新 record／transitionとして凍結するか、旧 generator module内へ実装するか。
- budget authorityと、producerをg1専用にするかg2 launchまで同時に開くか。
- W-4の schedule/spec authority、全 freeze cell積・承認済み `n/master_seed` への束縛、active ratified freeze限定を本 waveへ含めるか。
- R-4の再裁定案に、既存 hash-bound calibrationからの derived toolchain束縛と `build_v2` の明示 compiler経路を追加するか。