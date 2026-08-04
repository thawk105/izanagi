静的読解のみ。pytest は実行していない。real 候補は 5 件。

### 1. 固定 suffix の symlink が別 namespace へ逃げる

- 種別: 正しさ境界
- 深刻度: 致命的
- 根拠: `s2-plan.md:46-59` は env の base path だけを検査し、その後 `s2-plan.md:73-82` で `exploration/campaigns/<id>` を追加する。一方 `orchestrator/campaign/layout.py:231-237,315-319` は追加後の各 component を `lstat` せず `os.makedirs(..., exist_ok=True)` で辿る。`_campaign_slug()` は `layout.py:205-212` の leaf 字句検査にすぎない。
- 壊れ方: env を通常 directory `/work/job` とし、`/work/job/exploration/campaigns` を別 wave の `<repo>/output/campaigns` への symlink にすると resolver は受理する。marker は `/work/job/exploration/namespace.json` に残る一方、lock/WAL は別 repo の official `output/campaigns/<id>` に生成される。対象 official root には marker がないため、`s8b_oracle_report.py:301-318,321-345` の namespace gate はその root/campaign を後段へ通す。
- 修正方向: base だけでなく `exploration/campaigns/<id>` まで directory FD／capability 起点で no-follow 作成・照合し、`ensure_exploration_namespace()`／`ensure()` を不変とする裁定を撤回する。

### 2. 「現在 repo 外」は「job 専用 root」ではない

- 種別: 正しさ境界
- 深刻度: 高
- 根拠: `s2-plan.md:55-59` の拒否条件は現在の worktree 配下だけで、予定テストも `s2-plan.md:132-140` の集合に限られる。既存の厳密な admission は `layout.py:52-76` に approved-root capability として存在するが、exploration は `loop.py:125-126` から直接 `ensure()` へ進む。実利用は `s8b_floor_campaign.py:2843-2849` のみという親の棚卸しは正しい。
- 壊れ方: env の受理集合には main worktree の `output`、兄弟 wave の `output`、別 repo、共有 `/work`、world-writable `/tmp` が残る。前二者なら他 wave を汚して land を塞げる。同一 root・同一 config では output root が `ident.py:136-144` の campaign identity に入らないため同じ `<id>`、lock、WAL を共有し、別 job の実行を resume と誤認しうる。
- 修正方向: env 値自身を認可根拠にせず、launcher が与える approved job root/capability 配下の新規・所有者限定 leaf だけを受理し、main・兄弟 worktree・共有 root の負例を追加する。

### 3. guard のコード不変でも、防護の受理集合は実質的に緩む

- 種別: 正しさ境界
- 深刻度: 高
- 根拠: `guard_bash.py:98-101,780-801` は campaign tree を現在 repo 相対の二要素だけで認識し、repo 外絶対 path は明示的に防護外とする。`mv/find/tar/rsync` も `guard_bash.py:901-925` で同じ `_tree_violation` に依存する。`guard_write.py:46-63,84-100` も現在 repo の campaign roots だけを比較する。外部 marker の削除許可は既存テスト `test_hooks.py:421-448` に固定されている。
- 壊れ方: 静的帰結は次のとおり。

  - 外部 campaign dir 全体の `rm`／`mv`: ALLOW
  - `find <external-campaign> -delete`: ALLOW
  - tar 展開／rsync を外部 campaign dir へ向ける: ALLOW。archive 内の lock/WAL 名はコマンドに現れない
  - Bash の外部 `wal.jsonl`／`campaign.lock` への直接 redirect: `_LEAF_RE` により DENY
  - 外部 `namespace.json` への redirect／削除: ALLOW
  - Write/Edit tool による外部 WAL/lock の直接変更: `guard_write` の current-repo 比較外なので ALLOW

  `layout.py:8-10,284-297` と `loop.py:126-153` が示すとおり、外へ出るのは lock と WAL を含む proof chain そのものである。したがって `brief.md:75-77` の「proof chain 非接触」と `docs/orchestrator-design.md:110` の「hooks 防護は同一」は偽になる。後で repo へ写すまでの hash manifest／検証付き promotion もプランにない。
- 修正方向: 外部 root に application-level の同等防護と検証済み promotion receipt を設けるか、「防壁を緩めない」という採用条件を満たさないものとして scope を戻す。

### 4. env の再読で同一 process 内でも proof chain が分裂する

- 種別: 正しさ境界
- 深刻度: 高
- 根拠: resolver は `s2-plan.md:40` のとおり factory 呼出しごとに `os.environ` を読む。プラン自身も `s2-plan.md:115` で同一性を「env が不変なら」に依存させ、runbook の注意だけで済ませている。実際に `p3_kickoff.py:103-114` は campaign 実行後に factory を再度呼んで WAL を読む。`p3_s4_loop.py:678-680,803-805,896,926` にも再導出がある。
- 壊れ方: 最初の `run_campaign` を root A で実行後、env が B に変わると、同じ campaign id の読出し側は B の missing/stale WAL を参照する。process 再開時の env drift でも A と B に独立した同一 id の lock/WAL ができ、root は lock pre-image に入らないため IdentityMismatch で検出できない。
- 修正方向: trusted entry で root を一度だけ確定して immutable layout/context として渡し、canonical path・job identity・directory identity を launch receipt に束縛して変更を拒否する。

### 5. F98 テストは恒真ではないが、記載どおりでは標的 gate に到達しない

- 種別: 正しさ境界
- 深刻度: 中
- 根拠: `s2-plan.md:177,184` は `LAND._verify_repository()` を直接呼ぶが、同関数は `dev_wave_land.py:396-398` で cwd が exact wave worktree であることを必須とする。既存 helper はこのため `test_dev_wave_land.py:172-174` で `_cwd(request.wave_worktree)` を使う。
- 壊れ方: 合成 wave 外の通常 cwd から呼ぶと RC_IDENTITY で停止し、正例も負例も `_verify_wave_clean()` に到達しない。標的 gate の性質を実証できない。
- 修正方向: 両テストで `_verify_repository()` を `with _cwd(wave):` 内に置き、負例の例外捕捉範囲を `_verify_wave_clean()` だけに限定する。

### 攻撃したが破れなかった面

- [恒真ゲート]: 上記 cwd を直せば、正例は実物の `_verify_wave_clean()` を非 monkeypatch で通し、負例は同関数の `RC_DIRT` と理由まで照合するため、常時 pass 型ではない。
- campaign-id traversal: `_campaign_slug()` は factory 冒頭で維持され、`../`・separator・dot slug の字句迂回は破れなかった。ただし finding 1 の prefix symlink は射程外。
- 捏造・行番号ドリフト: `layout.py:323-330`、`dev_wave_land.py:785-787`、`s8b_floor_campaign.py:2845`、主要 p3 caller、各 test 引用を抜き取り照合し、機械的な file:line 不一致は見つからなかった。壊れているのは引用先から導いた一般化である。
- spec 凍結: 現行 exploration 経路では `spec/` は `layout.py:317-319` で directory が作られるだけで、spec card の writer は見つからなかった。WAL と campaign.lock は実際に admission 非接触で書かれるため、それだけで findings 2・3 は成立する。

## 総括

- real 候補所見数: 5
- 最深刻 1 件: 固定 suffix の symlink により exploration campaign を別 repo の official `output/campaigns` へ注入でき、namespace gate の受理集合まで変わる。
- プラン採否: 現状は不採用。外部化方針自体は維持できるが、trusted job-root admission、suffix 全体の no-follow、proof-chain 防護・promotion、immutable root binding を plan v2 に入れる必要がある。