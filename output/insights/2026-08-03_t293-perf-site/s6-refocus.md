結論は **NO-GO** です。静的検査のみ実施し、pytest・probe・perf・PBS job は実行していません。fix 子の「F-1〜F-7 全 closed」は成立しません。

## 1. 旧 14 所見の対応表

| 旧所見 | 判定・深刻度 | 根拠 | 再現条件／成果物影響 |
|---|---|---|---|
| A1 実コード未測定でも成功 | **closed**（旧 must-fix） | import 失敗は rc 3 で即終了し、全層の `attempted` を集約している。[probe.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:459) [probe.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:605) | import／一般例外時の旧 false-green は遮断された。新しい例外上の問題は後述 R4。 |
| A2 第2候補を機能測定しない | **closed**（旧 must-fix） | 全候補をループし、version・smoke・`functional` を個別記録する。[probe.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:249) [probe.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:438) | 第2候補だけ smoke に失敗すれば、その候補の `functional:false` が残る。ただし production との新しい不一致は R2。 |
| A3 marker を完了証拠にする | **closed**（旧 must-fix） | brief が marker の役割を訂正し、probe 終了後に done-marker を作る。[brief.md:71](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:71) [probe.pbs:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:57) | Python 起動前／実行中 kill では done-marker ができず、未完了 artifact は受理条件 4 を通らない。 |
| A4 failure stage が一意でない | **partial**・should-fix | executable ごとの結果は増えたが、`real_prepare_toolchain` 自体には安定した `failure_stage` がない。[probe.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:508) [probe.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:541) | 全 executable と smoke が成功後、gflags／glog の一方が失敗すると、どちらかは自由文依存。[submission.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:125) **影響:** exact blocker の機械集計がまだ不安定。 |
| A5 期待 commit／policy へ束縛されない | **partial**・must-fix | HEAD・policy は比較するが、`matched` の構成要素はその2つだけ。source SHA は記録するだけで期待値と比較しない。[probe.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:139) [probe.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:147) | 同じ HEAD の dirty/untracked source を実行しても binding は一致する。**影響:** 異なる実行 bytes の観測が基準 HEAD の証拠として受理され得る。 |
| A6 C1/M1 が false-success を検出しない | **partial**・must-fix | C1/M1 は撤回されたが、代替 control は負の1点だけ。[s4-adjudication.md:31](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:31) [probe.py:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:589) | resolver が常に reject しても actual/control とも false となり `ok:true`。**影響:** 測定器が stuck-false の artifact を候補不在として採用できる。 |
| B1 login で走らせる C1 | **closed**（旧 must-fix） | login C1 を撤回し、control は同一 compute run 内へ移した。[s4-adjudication.md:31](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:31) [brief.md:83](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:83) | 旧運用として login probe を必須実行する経路は消えた。直接起動防壁の欠如は R5。 |
| B2 output 上書き・symlink 追従 | **partial**・must-fix | leaf dir と直接親、個別ファイルは create-only。しかし中間 component と `$PBS_O_WORKDIR` は検査しない。[probe.pbs:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:17) [probe.pbs:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:21) | `output`／`env`／`pegasus` または workdir 自体が symlink なら追従する。**影響:** 証拠を許可外へ書くか、別 checkout の artifact と混同し得る。 |
| B3 control に kill 受理述語がない | **partial**・must-fix | control が正に解決した場合は `ok:false`／rc 3 になったが、stuck-false は通る。[probe.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:596) [probe.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:609) | always-false resolver で control と本候補の双方が false。**影響:** fail-closed 感度を裏取りしたという裁定が偽緑になる。 |
| B4 M1 の変異位置・復元契約 | **closed**（旧 must-fix） | M1 を撤回し、手編集変異 matrix 自体を対象外にした。[s4-adjudication.md:29](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:29) [s4-adjudication.md:44](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:44) | 曖昧 anchor／復元失敗を持つ mutation ledger は作られない。 |
| B5 N3 が compiler blocker を無視 | **closed**（旧 must-fix） | N3 は明示的に未裁定へ差し戻された。[s4-adjudication.md:13](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:13) [brief.md:79](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:79) | perf site だけを直す不要な D96 変更を確定する旧経路は閉じた。 |
| B6 1 node から全 site へ一般化 | **closed**（旧 should-fix） | hostname・epoch・policy SHA の1標本と JSON 自身に明記する。[probe.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:158) [brief.md:81](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:81) | 正しい consumer なら全 bnode／将来 allocation へ一般化しない。 |
| B7 source が commit に束縛されない | **partial**・must-fix | probe/PBS/submission SHA は出るが expected SHA がなく、CLI 必須値は HEAD と policy だけ。[probe.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:147) [probe.py:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:666) | 現在も probe/PBS は untracked。queued 後の編集でも HEAD は不変。**影響:** 記録 SHA は残るが、期待外 bytes を fail-closed に拒否できない。 |
| B8 NQSV `.o/.e` が output 外 | **not-addressed**・should-fix | PBS directive に `-o/-e` はなく、親の将来運用へ委譲しただけ。[probe.pbs:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:1) [s4-adjudication.md:64](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:64) | qsub caller が収容を忘れると会計痕跡が散る。**影響:** 裁定パッケージの F49(c) 証拠が欠落する。 |

## 2. 回帰・新規欠陥

### R1. 負の control 1点では非定数性を証明できない

**深刻度: must-fix**

`CONTROL_CANDIDATES` を未解決にすることだけが条件で、本候補側との正負の対比を要求していません。[probe.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:28) [probe.py:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:589) [probe.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:605)

- 再現条件: `_executable` が全入力で `SubmissionPreparationError` を返す。actual/control とも `resolved:false`、全層 `attempted:true`、最終 `ok:true` になる。
- `/nonexistent/...` は OS が予約した不存在 namespace ではない。そこに正常な実行体が存在すれば、候補測定自体が完了していても control が正に解決して `ok:false`。存在するが version が失敗する実行体なら `resolved:false` のまま「不存在 control」と誤認する。[submission.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:73)
- **成果物影響:** stuck-false 測定器を候補不在として受理するか、逆に正常な候補測定を control path 衝突だけで廃棄し、D96 裁定を誤る。

### R2. per-candidate の `functional` は production と同値でない

**深刻度: must-fix**

probe の version timeout は 10 秒ですが、production `_run_text` は 20 秒です。[probe.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:196) [submission.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:34)

さらに production は canonical path の SHA-256 と測定中の inode/size/mtime 安定性を検査しますが、per-candidate はそれを行いません。[submission.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:47) [probe.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:249)

- 再現条件: `--version` が 10～20 秒で完了する、または candidate が probe 実行と production hash の間に変化する。per-candidate と `real_executable_resolution`／`real_prepare_toolchain` が反対になっても、整合性条件がなく `ok:true` になり得る。
- **成果物影響:** 同じ artifact が「候補は非機能」と「production は受理」を同時に示し、primary question の裁定が一意にならない。

### R3. 受理条件 5 の「期待 field 完備」が定義されていない

**深刻度: must-fix**

`schema_version` は文字列だけで、必須 field、型、条件分岐別の required set を定める schema／validator がありません。[probe.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:22) [s4-adjudication.md:51](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:51)

また `measurement_layers` が持つのは `attempted` だけで、受理述語を「各層の `ok:true`」と読む場合、その field は存在しません。[probe.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:182)

- 再現条件: consumer ごとに「期待 field」を別々に実装する。例えば未解決時の `simulated_smoke` には `functional` がないが、それを正当な条件分岐とするか欠落とするか決められない。
- **成果物影響:** 同じ JSON を一方の consumer は受理し、別の consumer は拒否でき、段 6 の機械受理が再現不能になる。

### R4. 一部の例外と実行不能が `ok`／`executed` に正しく投影されない

**深刻度: should-fix**

`perf_event_paranoid` 読取は全 `Exception` を内部で error record に変えますが、environment layer は `attempted:true` のままで `ok:true` に到達できます。[probe.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:98) [probe.py:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:426)

また `_run_record` は process spawn 前から `executed:true` とし、`OSError` 後も戻しません。[probe.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:197) [probe.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:228)

- 再現条件: `/proc/sys/kernel/perf_event_paranoid` が不可読、または access 判定後に executable が消える。
- **成果物影響:** 環境観測欠落や未起動 command を「全層完了／executed」と読む材料レポートを作り得る。

### R5. login-node 実行のコード内防壁がない

**深刻度: should-fix**

通常の qsub 経路が login へ戻る箇所は見つかりません。しかし Python 本体は PBS／hostname を検査せず、per-candidate 測定で直ちに perf を実行します。[probe.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:277) [probe.py:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:662)

PBS 側も scheduler marker の真正性ではなく環境変数の非空だけを見ています。[probe.pbs:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:7)

- 再現条件: login で Python を直接起動するか、PBS 変数を設定して `.pbs` を shell script として起動する。
- **成果物影響:** I5 違反の perf を複数回実行し、5受理条件だけでは login 標本を機械拒否できない。F49 の qstat／会計照合は別途必要。

### R6. create-only は requeue/restart を正常継続できない

**深刻度: should-fix**

- 再現条件: scheduler が同じ `PBS_JOBID` で requeue する、または最初の試行が末端 dir 作成後に停止する。次試行は既存 `$OUT` により即 exit 2。[probe.pbs:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:21)
- **成果物影響:** 再実行可能な正常 job が測定前に落ち、計算枠を消費して証拠を得られない。
- 初回実行で parent dir が既存なのは問題なく、`TMPDIR` 依存も見つからなかった。既存末端 dir の拒否自体は stale 混在を防ぐ正しい fail-closed である。

## 3. 受理述語 5 条件

| 条件 | 機械判定 | 点検結果 |
|---|---|---|
| 1. HEAD／policy SHA binding | **形式上は可能、意味は partial** | `binding.matched/head/policy_sha256/expected_*` がある。ただし HEAD は dirty/untracked probe・PBS・submission bytes を拘束しない。 |
| 2. 全層 attempted、ok、probe rc 0 | **形式上は可能** | `measurement_layers.*.attempted`、top-level `ok`、`probe.rc` がある。ただし層別 `ok` は存在せず、R1/R4 のため意味が弱い。 |
| 3. control unresolved | **値は判定可能、目的は判定不能** | `control_resolution.resolved` はあるが、負の1点では非定数性を証明できず、control path の不存在も field にない。 |
| 4. done-marker と rc 0 | **可能** | done-marker と `probe.rc` の双方を検査できる。[probe.pbs:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:52) ただし symlink-safe な evidence root ではない。 |
| 5. parse 可能・期待 field 完備 | **不可** | parse 可否は判定できるが、「期待 field」の正本・schema・条件別 required set がない。 |

引数については、空値は PBS が exit 2、不正長／非 hex は argparse が exit 2 にするため、直接的な空・不正形式迂回は見つかりませんでした。[probe.pbs:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:7) [probe.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:650)

迂回可能なのは値の形式ではなく、同一 HEAD の dirty/untracked bytes、hash 後から import までの変更、symlink 経由の別 checkout です。現在の独立 `git status --short` 確認でも probe 2 ファイルは untracked のままでした。

## 総括

- 14 所見の内訳:
  - **closed: 7 件**
  - **partial: 6 件**
  - **regressed: 0 件**
  - **not-addressed: 1 件**
- 新規 must-fix: **3 件**
  1. R1: 負の control 1点では stuck-false を検出できず、control path も不存在保証されない
  2. R2: per-candidate `functional` が production の timeout／hash・安定性契約と一致しない
  3. R3: 受理条件 5 の必須 field schema がなく、機械受理が非一意
- 計算ノード投入: **NO-GO**
  - 旧所見由来でも source binding（A5/B7）と中間 symlink（B2）が未閉鎖。
  - 新規 R1～R3 により、rc 0・`ok:true`・done-marker が揃っても測定感度／production 同値性／field 完備を保証できない。
  - B8 の `.o/.e` 収容も qsub caller 側で未実施。
- 実行していないもの: pytest、probe、perf、PBS job、性能計測のすべて。
- 実際に全文を読んだファイル:
  - `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md`
  - `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md`
  - `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s6-review-A.md`
  - `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s6-review-B.md`
  - `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s6-fix-prompt.txt`
  - `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s6-fix.md`
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py`
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs`
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py`
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/CLAUDE.md`
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/.agents/skills/dev-wave/SKILL.md`
- 関連箇所のみ確認:
  - `tools/pegasus/policy.json` の `perf_candidates`
  - ユーザー提示の `AGENTS.md` 全文
  - `git status`、HEAD、対象4ファイルの SHA-256、現 checkout の path component（いずれも read-only）