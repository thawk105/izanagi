# 段 3 敵対相談 — レンズ A

静的検査のみ。HEAD は `6331284e`、作業木は clean。pytest・PBS 実投入・hash 実計算は行っていない。

## 所見

### BLOCKER 1 — S-B の “live root” も caller config が信頼の根

- 具体入力:
  - `validator_kwargs.repo_root="/tmp/fake-repo"`（caller が用意した正規 Git repo）
  - `approved_git_identity=resolve_git_identity("/tmp/fake-repo")`
  - `approved_git_identity_sha256=git_identity_digest(...)`
  - `work_root="/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/output/t810-work"`
- 期待: 実 izanagi repository 内への書込みとして、最初の `mkdir` より前に拒否。
- 実際: `_live_repository_roots()` は caller の `repo_root` を `resolve_git_identity()` するだけなので、自己整合した `/tmp/fake-repo` が authority になる。実 repo 内 `work_root` は fake root の外として受理され、manifest 等が作られる。
- 根拠: [s2-plan.md:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:111)、[t810_coordinator.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:443)、[t810_validator.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/campaign/t810_validator.py:365)、[t810_coordinator.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:660)。

S-B は caller 外の repo anchor を別途必要とする。現プランでは束縛の根が浮いたままである。

### BLOCKER 2 — 対案 X の `pbs_wrapper.__file__` は caller 外 authority ではない

- 具体入力 A:
  - `PYTHONPATH=/tmp/shadow:/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath`
  - `/tmp/shadow/tools/pegasus/t810_pbs_wrapper.py` に API 互換の任意実装を置く。
  - `/tmp/evil.py` をその同じ bytes にする。
  - `wrapper_path="/tmp/evil.py"`、`wrapper_sha256=sha256(/tmp/evil.py)`。
- 実際: `tools` と `tools/pegasus` は tracked `__init__.py` を持たない namespace package である。official coordinator を repo 側からロードしつつ、wrapper だけ `/tmp/shadow` から先に解決できる。X は同じ悪性 bytes 同士を比較して通る。
- 具体入力 B:
  - `/tmp/package/wrapper.py` は official wrapper と byte 同一。
  - `/tmp/package/tools/pegasus/t810_harness_schema.py` は official copy。
  - `/tmp/package/tools/pegasus/t810_runner_policy.py` は任意 executable を走らせる実装。
- 実際: wrapper 自身は X を通るが、実行時には絶対 import または fallback で staging 側依存をロードできるため、実行される意味は official module と一致しない。
- 期待: caller が選んだ module・依存閉包は scheduler effect 前に拒否。
- 根拠: coordinator の通常 import は [t810_coordinator.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:28)、node wrapper の二経路 import は [t810_pbs_wrapper.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_pbs_wrapper.py:19)、生成 script は単に pathname を実行する [t810_coordinator.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:543)。

`__file__` だけでなく、authority の取得元と node package の依存閉包が必要である。

### BLOCKER 3 — 検査地点が実 wrapper effect を束縛せず、private adapter でも迂回できる

- 具体入力 A:
  1. official wrapper/hash で `prepare_group()` を通す。
  2. `wrapper.py` を `b"tampered"` に変更。
  3. `_subprocess_scheduler(prepared.authorization, prepared, slot["qsub_argv"], cwd=..., env={})` を直接呼ぶ。
- 実際: プランの再 hash は `_scheduler_effect()` にしかない。低水準 adapter は job script の文字列だけを再検査し、tampered wrapper のまま qsub する。
- 具体入力 B:
  1. qsub 時点までは official wrapper。
  2. qsub 成功後、job 開始前に shared `wrapper_path` を `b"raise SystemExit(0)\n"` へ置換。
- 実際: node は後で pathname を読み直す。qsub 直前の X/hash 一致は、実行 bytes を束縛しない。
- 期待: 全 scheduler effect 入口、および node が実際に読む bytes で拒否。
- 根拠: 計画上の再検査位置は [s2-plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:57)、現 adapter は [t810_coordinator.py:1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:1634)、script は wrapper pathname を実行する [t810_coordinator.py:544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:544)。private 名が能力境界でないことは [D331:14869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/docs/decisions.md:14869) に明記されている。

### BLOCKER 4 — S-D は staged wrapper を実行せず、production staging producer も無い

- 具体入力:
  - `_prepared()` 後、script 最終行を  
    `exec python3.10 /tmp/evil.py --request <generated-request>`  
    にする。
  - 計画どおり `W.main(argv[2:])` を呼ぶ。
- 期待: `/tmp/evil.py` が正規 wrapper でないため正例テストが失敗。
- 実際: `argv[1]` の wrapper path を捨て、既に import 済みの official `W.main` を呼ぶためテストは通り得る。これは staged artifact の実行検査ではない。
- さらに repo 全文検索では、launch intent/config や `package/wrapper.py` を作る非 test producer は 0 件だった。CLI は caller の config を読むだけである。`wrapper_path="/tmp/run/package/wrapper.py"` が未配置の production 入力は、新 gate で拒否される一方、テストだけが official bytes を配置する。
- 根拠: planned 呼出しは [s2-plan.md:215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:215)、test-only copy は [s2-plan.md:238](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:238)、現 fixture の package 作成は [test_t810_coordinator.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:104)、CLI の外部 config 消費は [t810_coordinator.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:1663)。

したがって「S-A gate が絶対に発火しない」は言い過ぎである。不一致入力には発火する。しかし「production 正例経路を検証する」は成立せず、test-only producer が欠落を隠す。

### BLOCKER 5 — budget verifier も caller 指定 ledger との自己整合に留まる

- 具体入力:
  - 本来の ledger `/var/tmp/izanagi/t810-budget.jsonl` は `counted_node_seconds=100000` で全額消費済み。
  - caller は `/tmp/fresh-ledger.jsonl` に同じ canonical genesis と、`group_id="group-1"`、`run_kind="liveness"`、`attempt=1` の reservation を書く。
  - receipt の `ledger_path="/tmp/fresh-ledger.jsonl"`、before/after hash と reservation fields をその bytes に合わせる。
- 期待: authoritative ledger で予算切れのため拒否。
- 実際: policy は ledger を `repository-external` としか指定せず、path を固定しない。計画 verifier は receipt 自身が指す fresh ledger を読み、全比較を通す。複数 ledger に予算を複製できる。
- 根拠: path を含む receipt は [t810_budget.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_budget.py:50)、path gate は external 判定だけの [t810_budget.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_budget.py:412)、policy に固定 path がない [t810_admission_v1.json:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/policies/t810_admission_v1.json:54)、計画述語は [s2-plan.md:143](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:143)。

新 verifier は「receipt と、ある ledger bytes の一致」には有効だが、「唯一の予算台帳との一致」ではない。

### BLOCKER 6 — guard producer 不足という段 2 の主張は正しい

- 具体入力:
  - policy pattern `main_patterns=["^t139-main-[0-9]+$"]`
  - 実 qstat transcript: `request_id="900001.nqsv"`、`Job_Name="t139-main-1"`、`Job_Owner="alice@nqsv"`、`job_state="R"`
  - caller receipt: `decision="allow"`、`a_series_jobs=[]`、`reason_codes=[]`、`snapshot_sha256="a"*64`。
- 期待: `a-series-active` で拒否。
- 現行/プランの実際: coordinator config には transcript/owner/B identity が無く、receipt の形だけなら受理できる。計画は producer 結線を保留するため、この入力は閉じない。
- 根拠: config fields は [t810_coordinator.py:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:473)、形式検査だけの consumer は [t810_coordinator.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:357)、guard の実入力は [t810_guard.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_guard.py:333)、receipt 読取が qsub より前なのは [t810_coordinator.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:686)、B identity が得られる submission は [t810_coordinator.py:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:807)。

2 相 API と snapshot provider の裁定なしに S-C 完了を名乗れない。

### BLOCKER 7 — wrapper だけ X で閉じても binary は任意のまま

- 具体入力:
  - official wrapper を使用。
  - `binary_source_path="/tmp/package/CCBench-Silo"`
  - bytes は任意実装 `b"#!/bin/sh\nexit 0\n"`。
  - `binary_sha256=sha256(these bytes)`
  - validator の `executable` と `expected_executable_sha256` も同じ値。
- 期待: 承認済み build artifact でないため scheduler effect 前に拒否。
- 実際: slot と validator はどちらも caller config。publisher はその任意 binary の実 hashから runner policy を生成し、runner は名称、同じ動的 hash、preregistered argv だけを検査するため、自己整合した任意 executable を拒否できない。
- 根拠: caller 値同士を比較する計画は [s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:47)、実 binary hash から policy を作る箇所は [t810_pbs_wrapper.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_pbs_wrapper.py:360)、policy constructor は [t810_runner_policy.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_runner_policy.py:60)、consumer 検査は [t810_runner_policy.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_runner_policy.py:120)。

prereg は benchmark 名を持つだけで、binary hash の値を持たない。completion manifest に `binary_sha256` という必須 field はあるが、値やその artifact への coordinator 結線はない。[t810_prereg_v1.json:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/policies/t810_prereg_v1.json:159)、[t810_prereg_v1.json:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/policies/t810_prereg_v1.json:592)。

binary authority は裁定へ返すべきである。wrapper-only の land は「部分 hardening」以上を主張できない。

### MAJOR — budget の “current ledger/last event” 条件は正当な並行 reservation を殺す

- 具体入力:
  1. group `g1` を予約し receipt R1 を得る。
  2. R1 の coordinator 検証前に、別 group `g2` の正当な予約 R2 が同じ ledger に append される。
- 期待: R1 event が chain 内に存在し、その reservation の最新状態が `reserved` なら R1 は有効。
- 計画の実際: current hash は R1 の `ledger_sha256_after` と異なり、last event も R2 なので R1 を拒否する。
- 根拠: last-event/current-hash 条件は [s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s2-plan.md:145)、ledger は異なる reservation を append できる [t810_budget.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_budget.py:527)。

厳密直列化を運用契約にするなら明文化が必要であり、そうでなければ event を chain 内で検証すべきである。

## 独立検算

- 焦点 #1: exact `--request` argv、production の request publication、runtime identity 補完は現行に存在するため、旧 incompatibility 自体は閉じている。[t810_coordinator.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:677)、[t810_coordinator.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:716)、[t810_pbs_wrapper.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_pbs_wrapper.py:1115)。ただし production positive route まで「閉」と一般化するのは BLOCKER 4 により不可。
- 焦点 #2: wrapper の `False/False/True/False` と barrier の期待は exact に一致する。これは閉じている。[t810_pbs_wrapper.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_pbs_wrapper.py:404)、[t810_coordinator.py:1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:1008)。
- 受理拡大: 現プランに、変更前に拒否された production 入力を新たに受理する変更、skip/xfail、期待値緩和は見つからなかった。問題は既存穴を「閉じた」と誤認する方向と過剰拒否である。
- 規律 1: 計画された hash/git/ledger I/O は qsub 前の orchestration にあり、性能計測 build や timed benchmark 内への分岐追加は見つからなかった。
- D328: P1 の「live bytes admission は保留対象外」という結論は維持可能。D328 は admission・信頼境界を明示的に除外する。[D328:14786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/docs/decisions.md:14786)。held 21 ID に t810 が無いことも確認したが、未存在の新 gate に対する負の列挙だけでは根拠にならない。[freeze_verification_hold.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/campaign/freeze_verification_hold.py:16)。本件は predicate 単位で admission と判断するのが F240 とも整合する。[failures.md:6022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/docs/failures.md:6022)。対案 X を裁定へ返す理由は D328 ではなく、authority・dependency closure・binary 未解決である。
- prereg authority: wrapper hash field は存在しない。`node_hash_checkpoints` は binary の実測 checkpoints であって wrapper authority ではない。[t810_prereg_v1.json:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/policies/t810_prereg_v1.json:185)。

外部の未提示 staging service/operator 手順は未確認。repo 内には producer が無い。

## 総括

**NO-GO。BLOCKER 7 件。**

対案 X、S-B、budget verifier はいずれも信頼の根が caller 由来のまま残る。さらに actual wrapper bytes は qsub 後まで束縛されず、planned S-D は staged module を実行しない。guard の 2 相設計と binary authority を裁定へ返し、production producer・全 effect 入口・node 実行時の束縛を含む plan v2 が必要である。