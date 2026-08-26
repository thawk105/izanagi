# 静的調査に基づく投入 plan

結論は、現行 `HEAD=9463bcbc...` では、凍結済み A-1 を有効な `formal=false` 探索値として投入できない、です。

ただし、親の「批准履歴は 18 commit」という個数は再現しませんでした。現行 HEAD では 17 commit、wave 971 時点とされた `f4c2c5de` では 16 commit です。個数の誤りを直しても、2 件目の不変 blob で必ず例外になるという構造的結論は変わりません。

## 1. 経路の全数列挙

批准への到達条件は次の 3 分岐で尽きます。

| identity 経路 | 批准検査 | 結果 |
|---|---:|---|
| `require_environment_contract=True`、lock 無し | 到達する | `_capture_current_loader_binding()` から批准へ進む |
| `True`、既存 v2 lock | 到達しない | activation、live closure、environment contract だけを再検査する |
| `False` | 到達しない | 新規なら v1 lock。既存 v2 は拒否 |

根拠は [ident.py:305-365](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:305) と [ident.py:410-475](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:410) です。

### A. 正規 qsub → `measure` → `run_campaign`

- job body は [paper_story_a1_paired.sh:748-759](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/tools/pegasus/paper_story_a1_paired.sh:748) で `measure` を 1 回だけ起動します。
- driver は workload ごとに [paper_story_a1_paired.py:2500-2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:2500) の `run_campaign()` を呼びます。
- `run_campaign` は [loop.py:288-291](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/loop.py:288) で `require_environment_contract` を渡しません。
- したがって [ident.py:367-382](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:367) の既定値 `True` になります。
- A-1 CLI は既存の output/cache/result root を拒否します。[paper_story_a1_paired.py:1218-1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:1218)
- よって各 workload は新規 lock 分岐に入り、[ident.py:443-458](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:443) から批准検査へ必ず到達します。

判定: **測定値の投入としては成立しません。**

例外は workload 単位で捕捉されるため、driver は `campaign-error` を持つ invalid result を組み立て得ます。[paper_story_a1_paired.py:2551-2579](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:2551) これは「失敗を記録した raw bundle」であって A-1 の探索値ではありません。

### B. `run_campaign` の直接呼出し

`run_campaign` の公開引数には `require_environment_contract` がありません。[loop.py:201-215](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/loop.py:201)

- fresh layout: 正規経路と同じく批准へ到達し失敗。
- v1 lock を事前配置: `True` lane が [ident.py:322-326](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:322) で拒否。
- 正規に作成済みの v2 lock: 批准を再実行せず resume 可能。ただし sized-v1 A-1 の正規 v2 lock は一度も作成できていません。
- forged v2 lock: 技術的には通ります。既存 v2 の検証は批准集合を再照合せず、activation、live binding、contract SHA の照合で終わるためです。[ident.py:343-364](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:343)

最後の経路では、批准を呼ばない `capture_contract_loader_binding()` と公開 v2 encoder から形式上有効な lock を構成できます。[contract_loader_binding.py:349-362](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/contract_loader_binding.py:349)、[campaign_lock.py:255-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/campaign_lock.py:255)

判定: **既存 v2 分岐は技術的迂回として成立するが、採ってはなりません。**

### C. `require_environment_contract=False`

直接 `ident.ensure_campaign_identity()` または `ensure_resumable_wal()` を呼べば指定できます。新規 lock は [ident.py:459-461](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:459) の v1 になります。

しかし現行 A-1 は、

- `run_campaign` へ False を渡せない
- collector が authority 付き canonical v2 lock だけを受理する
- v1 では `campaign-lock-preimage-mismatch` となる

という構造です。[paper_story_a1_paired.py:1984-2016](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:1984)、[paper_story_a1_paired.py:2283-2291](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:2283)

判定:

- False を指定するだけ: **測定は成立しない**
- `loop.py` へ引数を追加し、A-1 collector も v1 を受けるよう変更: **技術的には成立するが、採ってはならない**

### D. `pipeline.evaluate`、calibrator、ccbench の直接起動

これらは identity API を経由しなければ批准へ到達しません。数値だけを発生させることは技術的に可能です。

一方、A-1 consumer は canonical campaign layout、v2 lock、exact WAL stage、build admission、verify、trace0 source binding を要求します。[paper_story_a1_paired.py:1683-1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:1683)

判定: **ベンチ値は作れても、凍結 A-1 の投入としては成立しません。**

### E. `materialize` だけを呼ぶ

`materialize` は raw WAL と全 receipt を再検証する consumer で、測定 producer ではありません。[paper_story_a1_paired.py:3312-3435](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:3312)

判定: **既存の正当な raw bundle がなければ成立しません。**

### F. 歴史 commit

批准 commit `6188a8d4` では、

- closure digest が台帳行の `db511c3d...` と一致
- path 履歴が台帳開設 commit 1 件だけなので構造エラーがない

ため、旧 study は gate を通り得ます。

しかし当時の driver は `paper-story-a1-20260824-exploratory-v1` と policy v1 で、policy v2 と sized-v1 事前登録はありません。現在の policy v2 は `2056935b` で追加されています。

判定: **旧 commit のままでは凍結 A-1 ではありません。**

旧批准 closure の `loop.py` / `pipeline.py` と現行 A-1 tree を履歴改変で合成する経路も構成上は可能ですが、後述の正しさゲート改善を巻き戻すため却下です。

### G. 入力、引数、環境だけによる回避

実在しません。

- `formal=false` は search identity と成果物 authority の値であり、identity gate の分岐には使われません。
- `declared_use_class="exploration"` は layout constructor の選択だけです。[loop.py:216-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/loop.py:216)
- A-1 CLI に gate 選択引数はありません。[paper_story_a1_paired.py:3439-3458](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:3439)
- `GIT_DIR`、replace refs、alternate object などの環境迂回は明示拒否されます。[enforcement_source_ratification.py:30-56](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/enforcement_source_ratification.py:30)、[enforcement_source_ratification.py:157-209](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/enforcement_source_ratification.py:157)

## 2. `require_environment_contract` の実効的な決定点

A-1 での決定点は `ident` ではなく、その caller である `loop.run_campaign` です。

`run_campaign` が値を渡さないため、caller である A-1 driver は現状制御できません。直接 `ident` API を使う caller だけが False を制御できます。repo 内の production code で False を明示するのは `guided.py` の 2 箇所だけです。

`guided.py` が False を使う理由は、これは新しい source build や bench を行う campaign ではなく、既存 P2-2 WAL の fitness を replay して誘導用 WAL を作る harness だからです。[guided.py:2-16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/guided.py:2)、[guided.py:54-61](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/guided.py:54)、[guided.py:193-223](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/guided.py:193)

False が外すものは trace verifier 全体ではありません。`run_campaign` 前半の execution authorization は別に残ります。[loop.py:123-157](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/loop.py:123)

False が外すのは主として、

1. live enforcement closure と HEAD の束縛
2. closure digest の批准集合照合
3. environment contract と activation tuple を持つ v2 lock
4. resume 時の authority 再検証

です。

現行批准検査の受理集合が空なので、「受理された closure は批准済み」という保証は現在は恒真です。しかし、そこから False が安全とは導けません。False は壊れた履歴走査だけでなく、上記の非重複な source authority までまとめて外します。新規 build と bench を行わない guided の例外を、A-1 測定へ一般化する根拠にはなりません。

したがって、A-1 で False にする変更は **実効的に正しさ・出所ゲートを緩める変更**です。

## 3. 批准検査の健全性

独立 probe の結果は次のとおりです。

- 現行 HEAD: path 履歴 17 commit
- 内訳: 開設 commit 1件、merge commit 16件
- wave 971 時点とされた `f4c2c5de`: 16 commit、うち開設後の merge 15件
- 全 commit の ledger blob OID: `42885e36...`
- 全 blob 長: 112 bytes
- 台帳行: `db511c3d...` 1件
- 現行 closure digest: `6d497998...`

コードは各 `git log --full-history` commit を順に読み、2件目以降すべてに「前の bytes の真の接頭辞で、かつ長さが増えたこと」を要求します。[enforcement_source_ratification.py:265-328](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/enforcement_source_ratification.py:265)

2件目で `112 <= 112` となるため、digest の内容に関係なく例外です。したがって現行 HEAD では、well-formed な closure map のどれに対しても `_committed_ratification_digests()` は値を返しません。

ただし影響範囲は「全 campaign」ではありません。

- **停止する:** fresh layout から v2 lock を新設する、すべての `require_environment_contract=True` campaign
- **このバグでは停止しない:** 既存 v2 lock の resume
- **対象外:** guided の False lane
- **別理由で停止:** v1 lock を True lane で開く場合

親の commit 個数は誤りですが、「fresh certified campaign 全体を止める既存障害」という結論は正しいです。

さらに、履歴走査を修正しても現行 `6d497998...` は台帳の `db511c3d...` と一致しません。単独の walker 修正でも、単独の現行 digest 追記でも A-1 は開きません。

## 4. 凍結境界と許容可能な変更集合

凍結値はコードでも固定されています。

- reps 72 / 205 / 28: [paper_story_a1_paired.py:98-117](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:98)
- policy SHA-256: `83b9c1a1...`
- preregistration SHA-256: `c85279e9...`
- 両 hash の runtime 検査: [paper_story_a1_paired.py:646-659](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:646)
- 凍結文書自身も loop の変更を本 study の範囲外としています。[README.md:124-130](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md:124)

現時点で、凍結を守り、D905/D758/絶対規律2にも従い、直ちに投入まで成立させる変更集合はありません。

将来の許容可能な plan は次だけです。

1. `_committed_ratification_digests()` を、path-neutral な merge の同一 blob を「新しい ledger version」と数えず、異なる ledger version 間だけ append-only 性を検査する実装へ修正する。
2. merge、分岐、置換、削除、複数行追加を含む DAG テストを追加する。既存テストには不変 merge のケースがありません。
3. 修正後の最終 closure digest を計算する。checker 自身が closure 内なので、現在の `6d497998...` を先に批准しても無効です。
4. D905 が要求する「AI が成りすませない実行主体」を着地させ、ユーザーが承認した最終 digest だけをその主体が台帳へ追記する。
5. A-1 の driver、job、policy v2、preregistration、reps、判定規則は変更せず、正規 qsub 経路を再実行する。

これは統計的凍結を壊さない infrastructure 修復です。ただし手順4の主体が未実装なので、**現在は実行可能な plan ではなく unblock 条件**です。

## 5. 成立するが採ってはならない経路

次は技術的成立性と規律上の許容性を分けた却下一覧です。

- **forged v2 lock を事前配置する:** 既存-lock 分岐が批准を再検査しないため技術的に成立。D905 の自己批准禁止と絶対規律2に反する。
- **A-1 用に False を `run_campaign` へ追加し、collector を v1 対応する:** 技術的に成立。closure/source authority を外し、凍結装置も変更するため不可。
- **A-1 driver 内で `run_campaign` を複製、monkeypatch、または直接 `pipeline.evaluate` を呼ぶ:** 数値生成は可能。凍結 evidence contract と正規 producer を迂回するため不可。
- **AI が ledger 行を追記する:** walker 修正と組み合わせれば技術的に成立。D758 決定3、D905 に正面から反する。
- **ユーザーに行貼付やコマンド実行を求める:** 技術的には成立し得るが、D758 決定2・4と D905 が明示的に却下。
- **平文承認へ移す:** 技術的には成立するが、AI が承認を合成できないという保証を失うため D905 違反。
- **`6188a8d4` の closure へ rollback、または履歴を squash して旧批准 digest を再利用する:** gate は通し得るが、後続の `loop.py` / `pipeline.py` の正しさ強化と凍結装置を巻き戻す。絶対規律2に反する。
- **Git env、replace refs、alternate object で履歴を偽装する:** 実装上も拒否され、仮に別の in-process 改変で可能にしても批准迂回なので不可。

D510 決定7により、これらで作った探索値を後から正式値へ昇格する余地もありません。[decisions.md:21257-21260](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/decisions.md:21257)

本調査は read-only のコード、Git 履歴、hash probe のみです。pytest は実行しておらず、緑とは記録しません。

## 総括

**投入は現状成立しない。** 技術的な迂回は存在するが、許容可能な A-1 探索値にはならない。

最も強い根拠は次の3点です。

1. 正規 A-1 は fresh root を強制し、引数や `formal=false` に関係なく `require_environment_contract=True` の新規-lock分岐から批准へ必ず到達する。
2. 批准履歴 walker は現行 HEAD の2件目の不変 merge blobで必ず例外になり、修正後も現行 closure digest は台帳行と不一致である。
3. 批准を避けて値を作る経路は、v2 lock 偽造、False lane 化、直接 producer、rollback、ledger 手動追記のいずれかであり、凍結境界、D905、D758、絶対規律2の少なくとも1つに反する。