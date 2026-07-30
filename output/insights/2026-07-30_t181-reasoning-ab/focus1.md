判定は **NO-GO** です。静的検分のみで、pytest・runner・mutation は実行していません。親実測の `27 passed` や `fix1.md` の緑は closure の証拠に使っていません。

## 旧 must-fix 対応表

| 旧所見 | 状態 | fix 後の静的根拠 |
|---|---|---|
| レビューA 1 — NEG allowlist | `closed` | 訂正版6件・`fix1.md` 不在が literal 化され、prompt 内 path 集合とも突合する。[実装:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:110) [実装:969](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:969) [test:371](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:371) |
| レビューA 2 — replay verifier 不在 | `partial` | `verify` は現在、snapshot、`collect_run()`、`score_run()` を再実行して保存 receipt/score と byte 比較する。[実装:2493](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2493) ただし launch argv/env/bwrap/world-state と `.done` 時刻は caller が書く JSON のままで、実 process との結線がない。[実装:1120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1120) [実装:1345](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1345) |
| レビューA 3 — stale/余剰 session | `partial` | session timestamp、ID三者一致、path/inodeを含む行集合一致は追加された。[実装:1513](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1513) [実装:2567](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2567) 一方、launch の run別 `codex_home` と verifier の単一 `sessions_root` は結合されない。合成fixture自身も両者を別場所に置いて受理される。[test:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:122) [test:138](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:138) |
| レビューA 4 — retry 上限が自己申告 | `partial` | 1〜3、連続性、親run、列挙された `launch.json` 集合は検査する。[実装:2453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2453) [実装:2555](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2555) しかし `attempts_root` 自体がmanifest自己申告で、外側・改名・削除済みattemptを閉じない。また manifest の slot/attempt と launch receipt の slot/attempt を照合していない。[実装:2406](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2406) [実装:1428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1428) |
| レビューA 5 — primary verdict join 不在 | `closed` | packet/verdict/map のbijection、output SHA、verdict row SHA、slot judgment を逐件joinする。[実装:2165](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2165) [実装:2231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2231) row-swap負例もある。[test:789](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:789) label masking 自体の破れはレビューB MF-5に残る。 |
| レビューA 6 — scorer の否定・曖昧・fence | `partial` | 歴史control、提示された否定、両decision混在、tilde-info反例は固定された。[test:535](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:535) [test:547](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:547) ただし `GOではない`、`GOか未裁定`、別語順の否定は依然validになり得る限定regexである。[実装:1869](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1869) [実装:1907](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1907) |
| レビューA 7 — golden 2経路の自己追認 | `partial` | route B は別の byte-preserving applicatorになり、実 rollout SHA、最終2ファイルの literal SHA、production entrypoint比較がある。[実装:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:423) [実装:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:503) [test:459](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:459) ただし両経路は同じ `_patch_updates()` parserを共有し、片方を実 `git apply` にする独立性には達していない。[実装:307](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:307) |
| レビューA 8 — turn graph/post-treatment | `partial` | context/start/complete のturn join、timestamp envelope、正token、構造的 treatment 判定は入った。[実装:1620](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1620) [実装:1663](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1663) ただし三者すべて `None`/空でも等値比較を通り、`logical_turns=0` のvalid runを作れる。turn_context自体の時刻・行順も検査しない。[実装:1542](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1542) [実装:1674](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1674) |
| レビューB MF-1 — arm treatment 同一性 | `partial` | prompt/snapshot/config/CLI/argv/bwrap/env等の identity をcase内濃度1で検査する。[実装:1085](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1085) [実装:2582](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2582) ただし path検査は区切られた literal `max/high` のみで、run-dir/CODEX_HOME差はidentityから置換除外される。[実装:919](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:919) [実装:1092](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1092) |
| レビューB MF-2 — Git object/history 漏洩 | `partial` | 期待ref一本、remote/reflog/packed-refs/loose replace/標準alternates、禁止2 object、focus履歴、unreachable objectを検査する。[実装:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:608) [実装:648](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:648) ただし後述する環境・grafts・submodule・`/proc`・TOCTOU経路が残る。 |
| レビューB MF-3 — NEG訂正版 | `closed` | レビューA 1と同じ。訂正版6件とprompt集合一致がproduction定数・実promptで固定されている。[実装:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:112) [test:388](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:388) |
| レビューB MF-4 — frozen artifact replay | `partial` | 保存receipt/scoreをそのまま信じる旧根拠は反証された。[実装:2498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2498) しかし schedule、launch、`.done`、sandbox、world-state、verdict は同じproducerが後付け可能なJSON/mtimeで、外部trust rootや実launcherへの束縛がない。[実装:2477](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2477) |
| レビューB MF-5 — label-masked primary | `partial` | 乱数packet ID、uniform filename、public row shuffle、freeze→unblind APIはある。[実装:2655](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2655) しかし秘密mapは同じdirectoryに置かれ、同じownerなら verdict凍結前でも `chmod 600` して読める。実際 `unblind()` 自身がそうしている。[実装:2679](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2679) [実装:2767](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2767) 独立第二読者もなく、`adjudicator` は単一文字列である。[実装:2175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2175) |
| レビューB MF-6 — retry/partial/all-attempt | `partial` | declared attempt全件のresource row、post-treatment優先、technical-invalid残存時のprimary停止は実装された。[実装:2527](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2527) [実装:2281](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2281) [実装:2361](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2361) ただし「実在した全attempt」閉包とpair単位retryがなく、incomplete時にも新規finding ledgerを出す。[実装:2381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2381) |
| レビューB MF-7 — 同時実行干渉 | `regressed` | revised schedule の「予定上の隣接順」は検査するが、実runの開始・終了順、非重複、block間逐次性を全く比較しない。[実装:2089](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2089) replayで時刻を集める用途はglobal session scanだけである。[実装:2547](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2547) よって同時・逆順・離れたrunまで新たに受理する。 |
| レビューB MF-8 — 全域 decision table | `partial` | completeness→POS→NEGのrowは出る。[実装:2333](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2333) しかし `experiment_complete` は verifier の `reasons` を見ないため、`valid=false`でもprimary品質値を出せる。[実装:2281](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2281) NEG rowも除外armを構造化せず、自己申告 `false_finding` に依存する。[実装:2312](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2312) |
| レビューB MF-9 — T-181必須指標 | `partial` | primary、新規finding、resource、reliability、decision row自体はaggregateから出る。[実装:2375](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2375) ただしprimaryは単一読者、新規findingは自己申告 `equivalent_to` とroot-cause文字列のexact dedup、resourceはdeclared attemptsだけ、logical turnは0でもvalid、decisionは完全な採否結果を持たない。[実装:2302](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2302) |

件数は **closed 3 / partial 13 / regressed 1** です。

## 攻撃結果

### 1. 歴史 control と 33→27 の検出力

歴史 control の向きは静的に維持されています。test-localの独立SHAを実ファイルへ照合した後、`focus1 → NO-GO / true`、`focus2 → GO / false` を直接assertしているため、ここは自己採取期待値ではありません。[test:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:36) [test:535](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:535)

一方、pre-fix sourceを記録した `fix1.log` との静的比較では、次の検出面が同等の負例なしに消えています。33 passedというログ値は証拠にせず、node名とfixture内容だけを比較しました。

- snapshot mode、余剰untracked＋detached HEAD、focus artifact拒否:
  `test_snapshot_oracle_rejects_mode_change`、`...extra_untracked_and_detached_head`、`...focus_artifact`（`fix1.log:4170–4190`）。
- prompt replacement count負例と実rollout collector slice:
  `test_render_prompt_rejects_wrong_replacement_count`、`test_focus1_real_slice_reproduces_t179_literal_receipt`（`fix1.log:4246–4270`）。
- 旧9-vectorのうち、ID不一致、all-info-null、final cumulative null、非object JSON、context 0、effort変化、stale done、wrong inode、nonzero initial size（`fix1.log:4298`）。現行parametrizeは token 0件、all-zero、abort、turn mismatch、stale session の5件だけである。[test:502](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:502)
- `## 総括` 500-byte境界の独立負例 `test_summary_section_itself_must_be_500_bytes`（`fix1.log:4361`）。現在の歴史controlはいずれも長いため、500-byte gate削除変異 M12 を殺せない。
- actual sequential-order/non-overlap、post-treatment denominator、technical pair retryのend-to-end負例（`fix1.log:4483–4515`）。revised sequential contract用の置換testがない。
- unfrozen manifest拒否とCLI `verify` integration（`fix1.log:4552–4572`）。

歴史control、余剰session、verdict row-swapは現行testへ有効に置換されていますが、上記の失われた境界は明確な mutation sensitivity 低下です。

### 2. Git object 閉包の残経路

狭い事実として、親実測の「禁止2 commit不可視・ref一本・focus log空」は成立しています。しかし `base_only` という出力名が保証する一般閉包は成立しません。

| 経路 | 現状 |
|---|---|
| `packed-refs` | 明示削除・空検査済み。ここはclosed。[実装:628](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:628) |
| reflog | `.git/logs` 削除・検査済み。closed。 |
| 標準 alternates | `.git/objects/info/alternates` だけは削除・検査済み。 |
| replace | loose `refs/replace` とpacked refsは閉じるが、`GIT_REPLACE_REF_BASE`、別namespace、run時の環境注入は未閉鎖。 |
| grafts | `.git/info/grafts` を列挙・拒否しない。 |
| `.git/objects/info` | `alternates` 以外の `http-alternates`、commit-graph、packs関連metadataをmanifest化しない。 |
| pseudo refs | `FETCH_HEAD`、`ORIG_HEAD` 等を明示allowlist/拒否していない。clean-env下ではprune/fsckが多くを抑えるがassertではない。 |
| submodule object store | object closureをsealした後で、local sourceからsubmoduleをcloneする。[実装:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:733) `.git/modules/**/objects`・config・local URLは検査せず、`submodule status`だけである。[実装:873](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:873) |
| `--reference` / extra bind | recorded `bwrap_argv`の意味を検査せず、別repo/object storeのbindやreference pathを許す。[実装:1222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1222) |
| snapshot外の `GIT_*` | `_run()` は実環境をそのまま継承し、launch環境はcaller提供mappingしか検査しない。[実装:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:223) `GIT_DIR`、`GIT_COMMON_DIR`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`、config注入を実processから消していない。 |
| ignored filesystem | `git status --untracked-files=all` はignored fileを閉じない。別名の答えfile、global exclude、`.git/info/exclude`を全filesystem walkで否定していない。[実装:763](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:763) |
| `/proc` | `proc_isolated` は任意の `world_state` JSONにすぎない。新PID namespaceやfresh `/proc` を検証しないため、親/兄弟processのenviron、cmdline、fd経由が残る。[実装:1139](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1139) |
| TOCTOU | replayはrun後の現在snapshotを再検査するだけ。run中だけanswer object/alternateを注入し、後で除去する経路を検出しない。snapshotの実 `--ro-bind` もassertしない。 |

### 3. replay verifier がまだ信じる自己申告

`verify` が raw artifactから `collect_run` / `score_run` を再実行していない、という旧指摘は現在はrefutedです。ただし次は依然自己申告です。

- `create-launch-receipt` に渡す argv、bwrap argv、環境、sandbox、world-state。
- `.done` の exit code、monotonic exit時刻、wall-clock。
- scheduleがprelaunchだったことを示すmtime。
- attempts rootが「全attemptを含む」という宣言。
- verdictのadjudicator、findingのreal/equivalent/false_finding/root-cause。
- packet秘密mapを凍結前に見なかったという宣言。

最小限必要なのは、receiptを作った同じsupervisorが実processを `exec` し、実argv/env/mount/PID namespaceとwait結果を直接捕捉する一体型launcherです。

### 4. slot / attempt と品質停止

全ての「manifestに列挙された」attemptはresource ledgerへ入ります。しかし実在した全attemptではありません。固定rootを外部trust rootにせずmanifest自身が選べるため、失敗attemptのdirectory削除・root外配置・`launch.json`改名で消せます。また初版仕様のpair単位無効化・pair再実行を表すblock attempt関係がありません。

technical-invalidが最終attemptに残れば `primary_judgment_ledger=None`、decisionのqualityも`None`になる点は有効です。ただし `new_finding_ledger`、reliability、escalation候補はそのまま出るため、「資源値のみ報告」にはなっていません。さらに verifier-level `reasons` があって `valid=false`でも、final attemptsがtechnical-invalidでなければ品質裁定を出します。

### 5. label-masked 漏洩

- 最大の直通経路は同じownerが読める `.packet-map.private.json`。mode `000` はconfidentiality boundaryではありません。
- packet filesはschedule順に作成後、public JSON rowだけshuffleするため、inode/mtime/作成順がslot順を漏らす。[実装:2649](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2649)
- filename/ID自体は `secrets.token_hex(16)` で、arm導出規則は見当たりません。この経路はrefutedです。
- file長と本文長はそのまま見えるため、effort推測残差がある。これは正本も残差として認めています。
- 独立第二読者、二読者一致率、保守側miss裁定がschemaに存在しません。

### 6. arm同一性

recorded identityが異なれば最終verifyはrc≠0になります。しかし「recorded」と「actual」の同一性がありません。特に以下は通ります。

- `run-A` / `run-B`、`deep` / `compact`、`e1` / `e2`、`max1` / `high2`、Unicode・hex・base64等でarmを符号化する。
- run-dir/CODEX_HOME/event/done pathはidentity計算前にplaceholderへ置換されるため、そこへの符号化は濃度1検査から消える。
- slot/run IDの生成規則をarmと一対一にし、`/proc`、PWD、CODEX_HOMEから復元する。
- auth.json、quota/account状態、実environment、実bwrap mountをarm別に変え、receiptには同じJSONを書く。

最小fixはliteral語検査ではなく、乱数run IDのarm独立生成、共通case root下の均一path、actual-env scrub、auth/config closure hash、実bwrap mount allowlist、fresh PID namespaceをlauncherが直接証明することです。

### 7. T-181 指標

aggregateには要求名のfieldが揃いましたが、意味がまだ確定していません。

- primary judgment: 単一親読者で、label secrecyが破れる。
- 新規finding: `equivalent_to=None` と任意root-cause文字列を信じ、semantic dedupを実施しない。
- 全attempt資源: declared attemptのみ。wall-clockは`.done`自己申告。
- logical turn: 空IDでも0としてvalidになり得る。
- 決定row: NEGで除外すべきarmを構造化せず、invalid verifierでも品質値を残す。
- `experiment_complete=false`: primaryは止めるが新規finding等を止めない。

したがってfieldの存在を「T-181指標が測定済み」と読むのは恒真化です。

### 8. 自己追認

有効な独立pinはあります。

- focus1/focus2はtracked実ファイル＋test-local SHAであり、歴史controlは有効。
- prompt sourceとauthor/fix rolloutsはproductionでsource rollout SHAを照合する。[実装:271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:271)
- golden最終2ファイルはtest-local literal SHAへ照合する。

残る自己追認は次です。

- `_raw_run()` が合成rolloutを作り、同じproduction `collect_run()`でreceiptを作り、同じproduction関数でreplayする。[test:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:98)
- `_full_manifest()` はproductionから作ったreceipt/score/hash/verdictをそのままproduction verifierの正例にする。[test:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:575)
- retry exhaustion testはraw verifierを通さずprivate `_aggregate_verified()`へ手書きrowを渡す。[test:869](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:869)
- collectorに対するtrackedな実 rollout golden はない。historical sessionsは絶対path依存で、不在ならmodule fixtureをskipする。[test:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:29) [test:344](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:344)

## 残存 finding

1. **RF-1 — Git/filesystem/process閉包**
   - severity: **CRITICAL**
   - real/refuted: **real**
   - 成果物影響: POS/NEGが歴史回答・別repo・親fdを読めれば、R-1、新規finding、NEG偽陽性、arm差の全値が汚染される。
   - 最小fix: object store・grafts・全refs・submodule storeを再帰manifest化し、actual `GIT_*`を空にした同一launcher内でverify→snapshot `--ro-bind`→fresh PID/proc→execを不可分に行う。全filesystem walkでignored/余剰fileも拒否する。

2. **RF-2 — launch/treatment の自己attestation**
   - severity: **CRITICAL**
   - real/refuted: **real**
   - 成果物影響: config、auth、mount、env、CLI実引数の差をreasoning差に誤帰属し、T-184 routingを反転できる。
   - 最小fix: `create-launch-receipt` を独立コマンドにせず、実processを起動・waitするsupervisorへ統合し、実argv/env/bwrap/config/auth/binaryとOS取得時刻を直接記録する。

3. **RF-3 — label mask は同一ownerのmode bitだけ**
   - severity: **CRITICAL**
   - real/refuted: **real**
   - 成果物影響: 親または第二読者がarmを知ったままprimaryを付け、max/high別 `k/3` を期待方向へ動かせる。
   - 最小fix: secret mapをpacket directory外・別credentialのkeeperに置き、verdict二読者分をappend-onlyで凍結後にだけkeeperがmapを公開する。packet metadataも乱数順で生成・mtime正規化する。

4. **RF-4 — 全attempt閉包とpair retry不在**
   - severity: **CRITICAL**
   - real/refuted: **real**
   - 成果物影響: 失敗attemptのtoken/wall/partialを消し、成功するまで回した結果をzero-missにできる。
   - 最小fix: trusted supervisorが事前に10 slotとblockを固定し、append-only attempt ledgerを唯一のrun rootから生成する。slot/attempt/parentをlaunch receiptとmanifestで照合し、pair両memberを同じattempt世代で再実行する。

5. **RF-5 — revised sequential crossover の実時刻gate欠落**
   - severity: **HIGH**
   - real/refuted: **real / fixによるregression**
   - 成果物影響: 同時実行によるquota・queue干渉や逆順・大幅な時刻差をreasoning効果として報告できる。
   - 最小fix: supervisor取得monotonic時刻で、schedule順に `previous.exit <= next.start`、block内順、block隣接、全run非重複をassertし、同時・逆順・gap変異を追加する。

6. **RF-6 — completeness/decision/T-181 ledgerが全域でない**
   - severity: **HIGH**
   - real/refuted: **real**
   - 成果物影響: `valid=false`・incomplete実験でも新規findingや品質文言が残り、T-184が未成立結果を引用できる。
   - 最小fix: verifier reasonまたはincompleteならresource以外を全て`null`にする。NEG除外arm、採否可能性、適用rowを型付きfieldにし、false-findingをcase・severity・must-fix adjudicationから導出する。

7. **RF-7 — turn/scorerの受理境界**
   - severity: **HIGH**
   - real/refuted: **real**
   - 成果物影響: logical turn、arm failure、valid_n、online escalation候補が過小・誤分類される。
   - 最小fix: nonempty turn ID、全関連eventの順序/timestamp、actual process wallを必須化し、`GOではない`等の否定・未裁定fixtureと500-byte M12を復元する。

8. **RF-8 — acceptance testの検出力縮小**
   - severity: **HIGH**
   - real/refuted: **real**
   - 成果物影響: object/mode/path/freshness/summary/pair/attempt gateの削除変異が27-test受入を生存し、欠陥ledgerを段7へ送れる。
   - 最小fix: 消えた独立負例をschema v2 fixtureへ移植し、tracked・sanitized実 rollout sliceをcollector goldenに追加する。新旧testへM1〜M12を走らせ、新testだけでなく各事前登録変異の期待nodeを固定する。

## 総括

**NO-GO。closed 3件、partial 13件、regressed 1件です。この実装で10 runの実走へ進んではいけません。** NEG訂正版、歴史focus1/focus2 controlの向き、receipt/scoreのraw replay、primary row joinなど、旧実装より実質的に閉じた面はあります。しかし、実runの信頼境界を決めるlaunch argv・environment・bwrap・process時刻がcaller提供JSONのままで、snapshot閉包もsubmodule object store、grafts、snapshot外GIT_*、ignored file、`/proc`、run中だけの注入を閉じていません。さらにlabel-masked mapは同じownerが単なるchmodで凍結前に読め、仕様で必須化された独立第二読者もありません。attempt台帳は「列挙された全件」にすぎず、失敗attemptをroot外へ捨てる経路とpair retry欠落が残ります。revised sequential crossoverは予定表だけで、実時刻の同時・逆順・非隣接を受理する明確な回帰です。`experiment_complete=false`でも新規finding ledgerが残り、verifier自体がinvalidでも品質値を出し得ます。加えて33→27への再編で、500-byte境界、mode/untracked/focus、prompt replacement、real rollout collector、pair timing、post-treatment denominatorなどのmutation検出力が消えました。まずRF-1〜RF-5を実装し、tracked実rollout goldenと失われた境界testを戻し、M1〜M12の期待nodeを再固定してから、もう一度focused reviewを行うべきです。