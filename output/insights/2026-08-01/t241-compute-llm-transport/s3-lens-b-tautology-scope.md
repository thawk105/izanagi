NO-GO。静的検証だけでも、S2 の受入は独立した oracle になっておらず、さらに live T-241 を阻む Pegasus admission と campaign identity 問題が scope から落ちている。

## 1. consumer 取り残し

`CLAUDE_ENV_ALLOWLIST` の実コード参照は全件以下である。

| 箇所 | 用途 | 判定 |
|---|---|---|
| [s8b_prediction_runner.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:70) | 定義 | — |
| [s8b_prediction_runner.py:1090](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1090) | 8b provider の env 投影 | wave 内 |
| [claude_projected_provider.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:23) | import | wave 内 |
| [claude_projected_provider.py:155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:155) | 8c provider の env 投影 | wave 内 |
| [test_s8b_prediction_runner.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_s8b_prediction_runner.py:23) | テスト import | oracle 汚染点 |
| [test_s8b_prediction_runner.py:556](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_s8b_prediction_runner.py:556) | 同じ定数を期待値にも使用 | F64 型盲点 |

したがって「allowlist を使う第3の campaign provider が残っている」という疑いは **refuted**。ただし、consumer 面全体は閉じていない。

- [s6_proposal_rounds.py:318](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s6_proposal_rounds.py:318) も `claude -p` を起動するが `env=` を渡さず、親の全環境を継承する。同じ transport 断は踏まない一方、allowlist の秘密境界も transport provenance もない。**本 wave 外でよいが、同一の安全性を持つ consumer ではない。**
- [tools/dev_waves/daemon.py:1060](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/tools/dev_waves/daemon.py:1060) は子環境を独自に再構成し proxy を捨てる。計算ノードで実 Claude worker を動かせば同型の断になる。campaign T-241 の scope 外ではあるが、別 task として台帳化しない限り取り残し。
- tracked な shell/PBS script に直接 `claude` を起動する別経路は見つからない。T-241 の未追跡 probe は全環境継承、`t241_before.sh` は 8c driver 経由である。
- journal v2 の downstream consumer は [s8b_floor_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_floor_campaign.py) と [s8b_ratified_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_ratified_freeze.py) に残る。プランは runner-local な v1/v2 検査だけで、v2 journal がこの2経路を最後まで通る検査を持たない。
- D79 は依然として「base 5 keys の exact allowlist」を現行裁定としている。[decisions.md:3321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/decisions.md:3321) を更新しないプランは規範 consumer の取り残しである。

**判定: real。**  
**成果物影響:** 8c の certified 選択だけは動き得るが、v2 journal の floor/ratified 受理集合は未保証。dev-wave 側では Claude worker が `unavailable/nonzero` と記録され得る。D79 参照は実装と矛盾したまま残る。

## 2. S2 実機受入は独立 oracle になっていない

[s2-plan.md:178](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:178) 以下の各条件には次の偽緑がある。

1. `rc=0` と `report.status=complete`

   古い report、fixture provider、壊れた driver が生成した自己申告でも通る。fresh run root、trial ID、provider kind、CLI/module/PBS script の hash、開始・終了時刻への binding がない。

2. 3 workloads、generation 1、全 cell dry-pass

   dry-pass は transport 成功の証明ではない。fixture 応答でも、report writer が outcome だけ捏造しても同じ集合になる。実 Claude invocation/session と cell の全単射が必要。

3. 12 role-attempt が valid、attempt 1、retry false

   件数だけなら同じ role を12回複製しても通る。期待集合を literal な  
   `(workload × generation=1 × {planner,coder,reviewer,judge})`  
   として固定し、重複なし、欠落なし、report↔attempts の双方向一致を検査すべきである。

4. `transport_env_keys == ジョブ開始時に存在した許可 key 集合`

   これは恒真である。同じ `os.environ` と同じ実装定数から「実値」と「期待値」を作るため、以下が全て緑になり得る。

   - key 名だけ journal に書き、実 subprocess へは渡さない
   - subprocess へ全環境を渡す
   - 誤った定数を実装と期待値の両方で参照する
   - 空・不正 URL の proxy 値を渡す

   非恒真化には、少なくとも以下が要る。

   - Pegasus 現行 profile の期待値を実装から独立した literal `{"http_proxy","https_proxy"}` として事前登録
   - `execve` 直前の child env を別 wrapper が key 名だけ捕捉した receipt
   - 同一 allocation で transport-off が失敗し、transport-on が成功する A/B
   - 値はログへ出さず、process 内で nonempty・URL 構文・site profile との一致を検証
   - receipt を PID、argv、trial ID、attempt/report hash に結合

5. journal に URL・credential・hash がない

   journal だけの scan では report、envelope、stderr、raw response、PBS stdout/stderr への漏洩が残る。文字列の percent/base64 表現も検出しない。成果物 closure 全体と closed schema を検査すべきである。

6. before control を保存し再実行しない

   保存は因果対照の証明ではない。before と after の source、driver、CLI、PBS script、node、env profile が結合されていないため、別変更・別 node・別 CLI でも「proxy fix による改善」と帰属できる。

**判定: real。** lowercase 2 key を必須とする条件だけは完全な空集合恒真ではないが、集合一致部分は自己参照である。  
**成果物影響:** report の accepted role-attempt 集合と attempts 台帳の transport attribution が偽緑になり、certified 選択が「Claude child に proxy が届いた」という未証明事実を根拠に受理される。

## 3. 新設テスト1〜7の検出力

プランの表は実際には9件あるが、指定された先頭7件を攻撃する。

| # | 赤にならない壊し方 | 判定・成果物影響 |
|---|---|---|
| 1 | fake runner のときだけ正しい env を渡し、実 `subprocess.run` の branch では `os.environ.copy()` を渡す。また期待値が `CLAUDE_ENV_ALLOWLIST` 自身なら、そこへ `AWS_SESSION_TOKEN` を追加しても同じ期待値が追随する。 | **real / F64 同型。** secrets が child へ漏れても report/台帳は正常扱い。 |
| 2 | テストした proxy key だけ特別扱いし、他4 key、大小文字同時存在、空値を壊す。presence 単体テストは緑。 | **real。** 別 site profile の受理集合が欠落する。 |
| 3 | schema version を v1 のままにして新 field を追加し、期待値も実装の `JOURNAL_SCHEMA_VERSION` を import する。 | **real / F64 同型。** v1 artifact の形を壊しても journal binding が受理され得る。 |
| 4 | `LEGACY_JOURNAL_SCHEMA_VERSION` と現行 version の値を入れ替え、テストの期待ラベルも同じ定数から作る。また runner-local validator だけ直して floor/ratified consumer を壊す。 | **real / F64 同型。** v2 journal が downstream で拒絶され、受理集合が空になる。 |
| 5 | `binding.transport_env_keys` と `provider.transport_env_keys` だけ一致させ、実 `provider.env` を invocation 前に削る。metadata 同士の比較は緑。 | **real。** attempts 台帳は proxy 有り、実 child は proxy 無しという虚偽になる。 |
| 6 | proxy forwarding を全部削除しても旧 response provenance の集合は変わらない。逆に別成果物へ proxy を漏らしてもこの検査は緑。 | **real。** transport 断・secret 漏洩の双方を検出しない。 |
| 7 | production の `environ is None` branch だけ旧 base-5 projection にし、テストの injected environ branch だけ helper を使う。fake runner と実 runner でも分岐できる。 | **real。** 実 S2 だけ planner-invalid に戻り、単体テストは緑。 |

追加の2件も弱い。valid attempt の期待値を `provider.transport_env_keys` から作れば同じ F64 型であり、invalid attempt の「値なし」検査は JSONL 外や符号化された漏洩を見ない。

**判定: real。**  
**成果物影響:** unit test の受理集合と実 subprocess の挙動が分離し、certified 選択、report、attempts ledger の三者が同時に誤った metadata を共有して緑になり得る。

## 4. T-241 達成不能の scope 切り

親 brief は [s1-brief.md:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:30) で「live build→legacy+S2→bench はこの wave で完了できない」と明記している。隠しているという攻撃は **refuted**。

しかし、「残りは compiler と gflags/glog の別 task」という切り分けは **real な欠落**である。

- [p3_s4_loop_trigger_gating.py:277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_s4_loop_trigger_gating.py:277) は Pegasus compute を measurement site として明示的に拒絶し、live path は [同:413](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_s4_loop_trigger_gating.py:413) でその admission を必ず通る。compiler を直しても実行不能。
- T265 の campaign identity/WAL replay 問題と T268 の Pegasus runnable env、attestation、isolation 条件も残る。fresh namespace なしでは linux-baremetal の terminal result を誤再利用し得る。
- `run_campaign` から pipeline へ Pegasus env/toolchain/dependency identity が通っていない。[pipeline.py:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/pipeline.py:453) の legacy build はそのまま既定 toolchain を使う。
- [certify_calibration.sh:351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/tools/pegasus/certify_calibration.sh:351) 以降には、計算ノードで gflags/glog と CCBench を fresh build する既存 recipe がある。少なくとも「計算ノード build は未知だから全面別 task」という根拠にはならない。

本 wave に切らずに加える最小面は、一般 buildcache 改造ではなく、次の限定 Pegasus pilot path である。

- Pegasus contract を明示的に resolve し、attestation・single-process・isolation を admission に含める
- fresh `/scr` campaign/cache namespace を使い、cross-env WAL reuse を禁止
- compiler realpath/version、dependency source/head/prefix を build identity と report に固定
- calibration recipe を再利用して generated patch を build
- live 3-cell legacy+S2 と bench まで走らせ、既存 linux-baremetal とは非比較・非formal と明記

**判定: 「親が未達を隠した」は refuted、「compiler/deps だけへ切れば残りが閉じる」は real。**  
**成果物影響:** 現プランでは certified 選択は no-build dry-pass に限られ、T-241 見出しが要求する live certified selection、benchmark report、build/measurement 台帳は生成されない。無理に走らせれば cross-env WAL による誤受理も起こる。

## 5. 文書訂正範囲が足りない

「計算ノードは外部 network 不可」を訂正するなら、少なくとも次を閉じなければならない。

現行規範・運用文書:

- [pegasus-runbook.md:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/pegasus-runbook.md:390): external network 不可、FetchContent は常に失敗
- [pegasus-runbook.md:415](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/pegasus-runbook.md:415): compute で Claude を開始しないという checklist
- [decisions.md:4946](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/decisions.md:4946): D108 の network/Claude 前提と再掲
- [worklog.md:1183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/worklog.md:1183): 現行裁定文
- [tools/pegasus/README.md:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/tools/pegasus/README.md:21): pinned staging の理由を network 不可としている
- [tools/run_tests.py:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/tools/run_tests.py:11): no-network 前提の説明。pip を避ける保守的挙動自体は残せるが、理由は未実測

履歴として書換えず、追記で supersede/限定すべきもの:

- `docs/archive/worklog-phase3-0729-59-0730-67.md`
- `docs/archive/worklog-phase3-0801-83-84.md`
- `docs/archive/worklog-phase3-0801-87-88.md`
- `output/insights/2026-07-29_t139-*`
- `output/insights/2026-08-01_8c-one-allocation-budget-design.md`
- `output/insights/2026-08-01_compute-network-split-*`
- その配下の dispatch plan、adjudication、adversarial review

また runbook は network 裁定を D106 と参照しているが、該当する split 裁定は D108 である。これは小さいが **real な参照バグ**。

一方、次の飛躍は禁止される。

> Claude CLI が proxy 経由で成功した ⇒ HTTPS 全般、GitHub clone、CMake FetchContent、pip も成功する

実測が示すのは、bnode002 の特定 job/profile で Claude CLI が成功したことだけである。過去には GitHub clone 失敗もある。calibration の fresh build 成功は反証材料だが、それが proxy、既存 mirror、cache のどれによるものかを receipt なしには決められない。

正しい訂正は「direct DNS/socket は失敗した。特定 profile では Claude HTTPS が proxy 経由で動いた。git/CMake/pip は command・node・profile ごとに未確定」である。staging は再現性・offline fallback として維持できるが、「network 上必須」とは言えない。

**判定: real。**  
**成果物影響:** certified/report の値を直ちに変えないが、次 wave の受理条件、staging 選択、D108/D79 参照、worklog の blocker 台帳が誤った前提を保持する。FetchContent を未検証で許可すれば build receipt の受理集合まで過大化する。

## 6. 親の実測手続の穴

### ノード記録が自己矛盾している

「全て bnode002 の単一ノード」という攻撃は字義上 **refuted**。before control の [context.txt:1](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/before/0_876813.nqsv/context.txt:1) は `hostname=bnode145` である。bnode002 は preliminary A/B/C probes のノードで、統合 8c failure は bnode145 だった。

問題はむしろ、[handoff-t241.md:13](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/handoff-t241.md:13) が request 876813 を bnode002 と誤記していることだ。異なるノードの probe と control を一つの因果系列として扱っている。

**判定: 単一 bnode002 は refuted、handoff の node provenance と portability は real。**  
**成果物影響:** before/after report の host 参照が誤り、transport fix の受理集合を「Pegasus compute 一般」へ拡張できない。certified 選択は少なくとも node/profile 限定に下げる必要がある。

### proxy は秘匿されていない

値を秘匿したという前提は **refuted**。raw endpoint は probe artifact、brief、handoff に平文で残っている。[s1-brief.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:12) にも記載されている。

今後 key 名だけにする方向自体は正しいが、それだけでは「空値・別 proxy・壊れた proxy」を区別できない。非秘密の profile ID、site attestation receipt、process 内妥当性検査が必要である。

**判定: 「秘匿済み」は refuted、機密性と再現性の両方の欠陥は real。**  
**成果物影響:** 現 before artifact は endpoint を漏洩し、将来 report は逆に値同一性を一切証明できない。台帳の transport attribution が両極端に壊れている。

### 同一 driver 対照の証明がない

`t241_before.sh` が 8c driver を呼んだことは分かるが、before report/attempts には shell script、Python module、repo HEAD、Claude CLI binary/config の hash がない。[attempts.jsonl](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/before/0_876813.nqsv/run/attempts.jsonl) は planner-invalid 3件だけで、実行面の同一性を証明しない。

同じコマンド文字列は同じ driver の証明ではない。同一 allocation A/B、または source/PBS/CLI/env-profile hash を before/after 共通 envelope に固定すべきである。

**判定: real。**  
**成果物影響:** after が 12/12 になっても差分を proxy fix に帰属できず、before control は certification evidence ではなく参考 artifact に格下げされる。

## 総括

- 最重: S2 の `transport_env_keys` は実装と同じ job 環境から期待値を作る恒真検査で、実 child への伝達を証明しない。  
- 次点: compiler/deps 以外に Pegasus admission、T265/T268、env-scoped WAL/build identity が残り、live T-241 はなお実行不能。  
- 次点: before は bnode145 なのに handoff は bnode002 と誤記し、source/CLI/PBS hash もないため、before/after の因果対照が成立していない。