結論は、現行 HEAD では「有効な A-1 探索値を得られない」が維持されます。ただし「A-1 は投入自体できない」「批准が実ジョブの最初の失敗になる」という表現は強すぎます。scheduler 投入と invalid raw bundle の生成は機構上可能です。

## 所見

1. **real — 「投入不能」は字義どおりには誤り**

`run_campaign()` の批准例外は workload ごとに捕捉され、`campaign-error` を持つ invalid workload に変換されます。3 workload 後には `result.json` と `receipt.json` が作られ、driver は 0 を返します。

根拠:

- `paper_story_a1_paired.py:2551-2565` — 例外を捕捉して collector を続行
- `paper_story_a1_paired.py:2568-2611` — invalid result でも成果物を書き driver rc=0
- `paper_story_a1_paired.py:2377-2406` — invalid workload も terminal result になり得る
- `paper_story_a1_paired.sh:748-761` — driver rc を job rc とする

したがって、正確な結論は「qsub 不能」ではなく、**「qsub はでき、finished な invalid raw bundle も作れるが、受理可能な探索値は得られない」**です。段2 plan の `stage2-plan.md:28-30` は既にこの区別をしています。

2. **refuted — login node の cwd 差で批准結果が受理側へ変わる、という反証は成立しなかった**

`_REPO_ROOT` は cwd ではなく import 元の `__file__` から固定されます。

- `enforcement_source_ratification.py:25,232-262`
- `contract_loader_binding.py:17,98-131`

さらに Git subprocess は `/usr/bin/git` 固定で、主要な ambient `GIT_*` override が存在すれば受理せず例外になります。

- `enforcement_source_ratification.py:30,40-56,157-177,180-209`
- `contract_loader_binding.py:19,30-46,252-316`

job body が設定する差は主に `TMPDIR` で、driver 起動前に実在 directory を作っています。cwd は変更せず absolute driver path を実行しますが、上記 root 解決には影響しません。`paper_story_a1_paired.sh:289-305,748-759`

反証 probe として cwd を `/` に変え、同じ checkout を `PYTHONPATH` から importして検査しました。結果は同じ HEAD `9463bcbc...` と同じ `strict prefix extension` 例外でした。

残る未同定差は compute node の `/usr/bin/git` の版と bytes です。job はこれを記録も版固定もしません。ただし異なる Git が documented `--full-history` 意味論に従う限り、受理側へ変わる根拠はありません。ambient override や一時領域故障は、むしろより手前の拒否になります。

3. **refuted — `-m` が無いから merge が出ない、という反証は成立しなかった**

現行 Git 2.34.1 での実測は次です。

```text
git rev-list --count --full-history HEAD -- <ledger>             -> 17
git rev-list --count --merges --full-history HEAD -- <ledger>    -> 16
git rev-list --count --full-history -m HEAD -- <ledger>          -> 17
git rev-list --count HEAD -- <ledger>                            -> 1
git rev-list --count --full-history --simplify-merges ...        -> 1
git rev-list --count --first-parent --full-history ...           -> 1
```

`-m` は merge の parent 別 diff 表示に必要ですが、`--full-history` の commit 選択には不要です。`git log --full-history -m --raw` では16 mergeすべてについて、ledger が一方の parent に存在せず、merge tree では OID `42885e36...` として追加された差が出ました。

ここには親説明への **real な精度訂正**があります。16件は「両 parent に対して path-neutral」ではなく、ledger を持つ parent には TREESAME、古い parent には非 TREESAME です。そのため `--full-history` で列挙されます。連続する選択 commit 間では blob が不変なので、2件目で `len(blob) <= len(previous_raw)` が成立する結論は変わりません。`enforcement_source_ratification.py:278-320`

17という個数は HEAD や CLI strategy に依存し、普遍定数ではありません。しかし production argv は exact に `--full-history` を指定しており、現行 DAG では17です。別 Git 版で異なるという実測証拠は得られていません。

なお `stage2-plan.md:5` は「親の18 commit」を訂正したと書いていますが、親 brief 自身は `brief.md:64` で17と記録しています。これは文書上の real な食い違いですが、機構結論には影響しません。

4. **real — 現行 HEAD では valid な closure map のどれに対しても批准関数は値を返さない**

現行 closure digest の再計算値は次でした。

```text
6d497998c4b80a186cd9ee3fc98154e29ddd0aa23f82f7da215558b90e32bf5a
```

ledger は `db511c3d...` の1行だけです。しかし membership 比較 `enforcement_source_ratification.py:333-338` より前に、履歴2件目で `:311-316` の例外になります。

したがって現行 checkout、現行 production argv、documented Git 意味論という範囲では、「どの valid digest 入力にも return しない」は正しいです。「全環境で絶対に」は、Git版や shallow/graft を明示検査していないため過大です。

5. **real — merge DAG を試すテストが無く、CI の検出力に穴がある**

`test_enforcement_source_ratification.py` はすべて線形履歴です。

- fixture 初期化: `test_enforcement_source_ratification.py:60-73`
- ledger commit helper: `:94-117`
- positive 1 commit: `:207-216`
- replacement、reorder、複数行追加もすべて直列: `:238-317`

branch、checkout、merge を作るテストはありません。また多くの campaign test が使う `ratified_enforcement_source` fixture も、一時 repo に ledger commit を1件追加するだけです。`conftest.py:190-232`。A-1 test 全体はこの fixture を使います。`test_paper_story_a1_paired.py:18`

このため、production DAG の「ledger を持たない古い branch を後で mergeする」形を一度も通さず、CI は緑のままです。**実装せず裁定パッケージ候補**です。

6. **real — v2 resume は批准を再検査せず、意図された resume と防壁の穴の両方である**

既存 lock では `ensure_campaign_identity()` が `verify_against_lock()` を呼びます。`ident.py:427-433`

再検査するのは次だけです。

- canonical identity: `ident.py:333-338`
- activation tuple: `:343-345`
- recorded binding と live closure: `:345-351`
- environment contract SHA: `:353-364`

`verify_ratified_contract_loader_binding()` は呼ばれません。批准を呼ぶのは fresh lock の `_capture_current_loader_binding()` だけです。`ident.py:234-245,443-458`

これは、正規に作られた lock を同じ closure で再開するという honest-path では意図された resume 設計です。しかし v2 lock は署名物ではなく、公開 encoder と現在の blob map から構成できます。test helper 自身が批准なしでそれを行っています。`campaign_lock_test_support.py:10-48`。さらに、批准 fixture を使わず preseeded v2 lock を resumeする正例が `test_campaign.py:9789-9842` にあります。

よって untrusted output root を攻撃者が書ける threat model では、**批准済み lock か、形式だけ正しい forged lock かを区別できない防壁の穴**です。ただし正規 A-1 CLI は fresh roots を要求するため、通常の A-1 qsub からこの分岐へは入りません。`paper_story_a1_paired.py:1218-1275`

**A-1 投入とは独立の real 所見で、実装せず裁定パッケージ候補**です。

7. **refuted — 批准より前に必ず落ちる別 blocker は静的には確認できなかった**

実際の順序は次です。

1. PBS変数、HEAD、clean tree、compute site: `paper_story_a1_paired.sh:27-85`
2. acquisition receipt: `:87-287`
3. attempt root、qstat allocation、reservation binding: `:289-405`
4. gflags/glog pin、clean tree、依存 build: `:580-746`
5. policy、receipt、site、calibration、attestation: `paper_story_a1_paired.py:2430-2496`
6. workload ごとの single-tenant probe: `:2500-2512`
7. authorization、perf preflight、layout作成: `loop.py:262-285`
8. fresh lock 作成から批准: `loop.py:288-291` → `ident.py:443-458`

現在静的に確認できた範囲では、HEADは clean、policy/preregistration hash は固定値と一致し、gflags/glog は期待 HEAD かつ clean でした。compute site、qstat、calibration、競合 process は未投入なので確認不能です。

したがって批准は「最初に実際に観測される失敗」とはまだ証明されていませんが、先行 gate がすべて通った場合に必ず到達する downstream blocker です。親の blocker 帰属はこの限定で正しいです。

8. **refuted — 6時間と610 rep が名目上不整合、という主張は成立しない**

凍結見積は610 rep、約34.2分です。`preregistration/README.md:45`

依存 build の timeout 上限は gflags 3×60秒、glog 3×120秒で合計9分です。内部再測定が最大3 roundすべて発生しても bench 見積は約102.6分であり、6時間には大きな余裕があります。

ただし **real な運用上限の穴**があります。

- A-1 の `build_v2()` は timeoutなしで呼ばれます。`pipeline.py:1073-1075`、`buildcache.py:1976-2008`
- 1 rep の timeout は120秒です。`calibrator/runner.py:518-524`
- reservation の campaign入口検査は `required_s=1` だけです。`loop.py:160-168`

例えば多数の rep が各120秒 timeoutする故障条件では、balanced 1 armだけでも205×120秒で6時間を越えます。したがって正常時に終わらない設計ではありませんが、**end-to-end 完了を6時間内へ機械的に束縛してはいません**。実装せず裁定パッケージ候補です。

9. **real — 単独性と外乱回避は runbook 要求を完全には満たさない**

満たす部分は、1 job、1 driver、workloadとarmの直列実行、および各 workload 冒頭と各 bench 前の `pgrep ycsb_.*\.exe` です。`p2_2.py:291-310`、`pipeline.py:590-612`

不足は次です。

- gen_S は scheduler 専有を保証しません。`pegasus-runbook.md:45-48`
- probe が検出するのは ycsb executable だけで、compilerや別種のCPU、cache、memory、I/O負荷を検出しません。
- first bench の `settle()` は20秒後に `settled=False` でも進みます。`calibrator/runner.py:110-129`
- `run_campaign()` は workloadごとの最初の成功 benchにしか settleを渡しません。`loop.py:328,411-450`
- A-1 collector は `rep_notes`、`rounds`、`unstable` は検査しますが `settled` を検査しません。`paper_story_a1_paired.py:1793-1799`
- bench 後の競合 post-probe がありません。runbook は臨界区間を「probe → bench → post-probe → journal」としています。`pegasus-runbook.md:1293-1297`
- PID visibility canary は runbook 自身が未実装と認めています。`pegasus-runbook.md:726-735`

したがって、他負荷が bench 中に始まる、または ycsb 以外の負荷が同居する場合、汚染値が valid になり得ます。**批准問題とは独立の real 所見で、実装せず裁定パッケージ候補**です。

## 受理・拒否の含意

受理の含意: 履歴 walker が同一 blob の merge projection を ledger version と数えない形へ直り、その修正後 closure digest が D905 の主体により批准された場合だけ、fresh A-1 lock は受理されます。

拒否の含意: 現行 gate の拒否は scheduler投入や invalid forensic bundle の生成を禁止するものではなく、有効な `formal=false` 探索値としての受理を禁止します。

通る正例は commit `6188a8d4` です。実測で path履歴は1 commit、当時の25-path closure digest は `db511c3d...` となり ledger行と一致しました。unit正例も `test_enforcement_source_ratification.py:207-216` にあります。ただしこの commit の studyは現行 sized-v1ではありません。

pytest は実行しておらず、緑とは記録しません。実施したのは read-only の Git、hash、Python probeと静的検査だけです。

## 総括

親の核心である「現行 HEAD から受理可能な A-1 探索値は得られない」は維持されます。一方で、次の4点は realです。

- qsub と finished invalid bundle は機構上可能であり、「投入不能」は過大表現
- merge DAG を試さない CI の検出力の穴
- forged v2 lock が批准を再検査せず resumeできる独立の防壁穴
- walltimeのhard bound不足と、post-probe・settled gateを欠く外乱防護不足

Git環境差と `-m` 不在によって現行批准が通るという反証は試みましたが成立しませんでした。現行 production argvでは17 commitが列挙され、2件目の同一112-byte blobで必ず失敗します。