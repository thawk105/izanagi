# 敵対レビュー結果

静的検査のみを行った。ファイル変更・pytest 実行はしていない。将来モジュール `verify_joint_*` は未実装なので、その挙動は段2プランに列挙された契約だけを根拠に判定した。

## real

### R1 — 提案 topology の `F` は、現行 freeze の G/A topology を構成できない

(a) **主張**

プランは `F = freeze candidate/generation と下位承認` を1 commitとして描くが、現行実装では generation commit G と、approval + pointer commit A は必ず分離される。提案列には有効な下位 freeze を作る commit が1本足りない。

(b) **根拠**

- `F` を単一 commitとしている: [stage2-plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:45)
- generation commit は非 `none` の AI trailer 必須: [s8b_ratified_freeze.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:552)
- approval/pointer commit は逐語的 `AI-Agent: none` 必須: [s8b_ratified_freeze.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:537)
- G=A を拒否し、A の diff を `{approval,pointer}` のみに限定: [s8b_ratified_freeze.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189)

(c) **壊れ方**

- F に generation + lower approval + lower pointer を入れ、`AI-Agent: none` にすると `_assert_candidate_commit` が `generation-commit-none`。
- AI trailer にすると `_assert_user_commit` が `user-commit-trailer`。
- provenance を仮に迂回しても `_verify_pairing` が `generation-approval-same-commit`、かつ generation が余分なので `approval-commit-diff`。
- generation を先行 G、approval を F、lower pointer を上位 X に分けると、approval/pointer の導入 commit が異なり `pairing-commit`。
- lower pointer を省けば `resolve_active_generation` が `no-active`。

構成可能なのは `G_f = generationだけ`、`A_f = lower approval + lower pointerだけ` の2 commitであり、提示 topology にはこの分離がない。

(d) **判定: real**

---

### R2 — 「有効な未参照 suffix」と §6 の activation 検査は同時に維持できない

(a) **主張**

E に `00000002.json` を置いたまま active bundle を g0 に維持する設計は、§6 の「record 2 があるが head pin は1なら拒否」という検査を意図的に消す。

(b) **根拠**

- プランは valid inactive suffix を許す: [stage2-plan.md:88](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:88)
- 現行 loader は directory 全体を読み、terminal serial/hash を head literal と比較する: [env_contract_activation.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:365)、[env_contract_activation.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:408)
- production head は serial 1: [env_contract.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:373)
- §6 はこの組合せを正しい fail-closed とし、緩和禁止としている: [restore-floor-protocol.md:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md:159)、[restore-floor-protocol.md:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md:163)

(c) **壊れ方**

head literal=1 の treeへ正当な `00000002.json` を追加する。

- 現行検査を残す: terminal=2 / expected=1 となり、E commit単独で赤。
- catalog/selected-prefix 分離でEを緑にする: §6の terminal/head 検査は発火しなくなる。

同じ authoritative directoryを使う限り、両方を同時には満たせない。

(d) **判定: real**

---

### R3 — generation record 直参照が `no-active` を迂回する

(a) **主張**

上位 bundle が lower active pointer ではなく generation recordを直接参照できるため、「generationだけでは権限にならない」という現行境界が失われる。

(b) **根拠**

- 新 consumer は `resolve_active_generation()` を使わず exact-ref helperへ移る: [stage2-plan.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:31)
- g1以降の freeze authority として「lower pointer **または generation record**」を許している: [stage2-plan.md:155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:155)
- `verify_joint_approval` の列挙条件には lower approval/pointer成立がない: [stage2-plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:60)
- 現行 resolver は live pointer 不在を拒否する: [s8b_ratified_freeze.py:1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1253)

(c) **壊れ方**

有効な AI generation commit Gだけを作り、lower approval/pointerは作らない。Bを `{kind:"generation", path:g1, sha256:...}` としてQ/A/Xを作る。

列挙された上位検査ではrefのancestryとdigestは成立する一方、現行 `resolve_active_generation()` は `no-active`。新 consumerは禁止された旧resolverを呼ばないため、未批准generationがproduction authorityになり得る。

helperがlower pointerを必須にする意図だった可能性はあるが、その条件は設計契約に存在せず未確認。

(d) **判定: real**

---

### R4 — policy実装より先にXを発効している

(a) **主張**

段5でXを有効化し、seal・保証・副作用policyを段6で実装する順序は、Xが拒否されるか、policyなしでproductionへ入るかの二択になる。

(b) **根拠**

- unresolved profileのXは拒否すると明記: [stage2-plan.md:253](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:253)
- X activationは段5、policy実装は段6: [stage2-plan.md:264](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:264)
- 現行floor preflightはv1 freeze bytesを要求する: [s8b_floor_campaign.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:1432)、[s8b_floor_campaign.py:1457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:1457)
- prediction時のprotocolとのbyte一致も要求する: [s8b_floor_campaign.py:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:1493)

(c) **壊れ方**

- profileをunresolvedのままにする: 段5の正常X自身が拒否され、完了条件を満たせない。
- resolved tagだけ置きadapterを未実装にする: Xは切り替わるが、seal再利用/再封印の意味を検証する機構がない。
- 現行preflightを残す: 新freeze/prediction組を拒否して段5が赤。
- 段3でpreflightを先に外す: §6のprediction/journal防壁が段6まで欠落する。

(d) **判定: real**

---

### R5 — 完了判定に reject-all で通る段がある

(a) **主張**

段0・4・7の完了判定は、機構が正しい入力を一件も受理しなくても成立する。

(b) **根拠**

- 段0はfieldを「実在入力/新規出力」と分類できたこと自体を判定にする: [stage2-plan.md:259](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:259)
- 段4は不正Aの拒否だけで、正当なAがX候補として受理される陽性条件がない: [stage2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:263)
- 段7はg2 mutationだけで、unmutated g2の受理を要求しない: [stage2-plan.md:266](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:266)
- 現行launchは全generation≠1を先に拒否する: [s8b_ratified_freeze.py:2874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:2874)

(c) **壊れ方**

- 任意の自己申告fieldを「新規出力」と記載すれば段0は真になる。
- `verify_joint_approval()` を常に例外送出する実装でも、段4に列挙された全negative caseは失敗する。
- generation scope拒否を残せば、parent/gap/forkをどう変異しても最初に `certificate-generation-scope` で落ち、段7のmutationは全部「緑」になる。

(d) **判定: real**

---

### R6 — registered-inactive g2は現行historical resolverでも拒否される

(a) **主張**

親のM1/M2以外に、`ever-active` gateという独立した機械拒否がある。段2の完了判定は「候補権限を正に解決できる」ことを要求していない。

(b) **根拠**

- registered g2は存在する: [env_contract.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:262)
- `resolve_by_contract_sha256` はactivation chain上でever-activeでなければ拒否する: [env_contract.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:671)、[env_contract.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:690)
- 段2判定はsuffix不変・参照済みrecord破損・ASTだけ: [stage2-plan.md:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:261)

(c) **壊れ方**

Eに正当なpegasus g2 rowを置き、F/B検証で既存historical resolverを再利用すると、g2 hashはregisteredでもever-activeでないため `EnvContractError`。新しいcandidate resolverがreject-allでも、現行の段2判定には陽性の候補解決がない。

(d) **判定: real**

---

### R7 — M1/M2から「literal除去必須」は導けない

(a) **主張**

M1/M2の実測自体は正しいが、親P2(a)の「headをliteralからrecord由来へ移すことが必須」という一般化は成立しない。

(b) **根拠**

- 親の推論: [s1-brief.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:30)
- P2(a): [s1-brief.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:52)
- lower freezeのdiff制限はlower approval commitだけに適用される: [s8b_ratified_freeze.py:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1205)
- environment loaderはrecord terminalとliteralが一致すれば通る: [env_contract.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:524)

(c) **壊れ方／反例**

以下はliteralを残す恒久topologyである。

1. 全production consumerを上位g0 pointerへ移行する。
2. lower freeze Gとlower `{approval,pointer}` Aを別commitで先行導入する。
3. 環境候補record bytes/state hashはinactive candidate namespaceでB/Aに束縛する。
4. 最終の人間Xで、公式 `00000002.json`追加、`env_contract.py`のhead literal更新、上位joint pointer追加のexact 3-path diffを許す。

X後はrecord terminal=2とliteral=2が一致し、lower `_verify_pairing` は既に完了したlower Aにしか適用されない。したがってliteral除去は必要条件ではない。

(d) **判定: real（過剰一般化）**

---

### R8 — Q receiptがbundleにもapprovalにも束縛されていない

(a) **主張**

Qは「自動検査receipt」と命名されているだけで、schema、raw hash、Bとの対応を検査する契約がない。

(b) **根拠**

- topologyではBの後にQ: [stage2-plan.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:46)
- approvalはAのparentがQであることとB digestだけを確認する: [stage2-plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:60)
- field provenance表にQ receipt/schema/hashがない: [stage2-plan.md:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:124)
- 先行台帳にもQ fieldはない: [calibration-freeze-joint-generation-design.md:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:41)

(c) **壊れ方**

Qを空commit、または無関係な1ファイル追加commitにする。Aをその直接子にし、正しいB digestをapprovalへ入れる。列挙された `verify_joint_approval` 条件はすべて通るが、自動検査は一度も実施されていない。

併せて、planがconsumer入力に使う `source_commit` は実装上は実在するものの、先行field台帳にもplanのprovenance表にもない（実在箇所: [certified_writer_admission.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/certified_writer_admission.py:196)）。

(d) **判定: real**

---

### R9 — 親P1はauthority正本を二重化する

(a) **主張**

旧freeze文書を完全無改訂にすると、旧文書の「最終active-bundle resolver」と新しい上位authority resolverが同時に正本を主張する。

(b) **根拠**

- P1は旧文書を改訂しない: [s1-brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:50)
- 旧文書はactive-bundle pointerを一度だけ読むresolverをproduction authorityとしている: [freeze-permanent-design.md:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:297)
- 新planは既存resolverをcompatibility専用に降格する: [stage2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:34)

(c) **壊れ方**

旧文書だけを参照したconsumerがfreeze-only resolverをproductionで使い続ける。環境は新joint resolver、freezeは旧resolverから取得され、上位bundleが承認していない直積が再生成される。

(d) **判定: real**

---

### R10 — 親P3の「段4以降すべて未定義」は過剰だが、planの再分割も壊れている

(a) **主張**

P3はpolicy非依存のA/X topologyまで未定義扱いしており過剰。一方planはそれを定義した後、policy実装前にXを置いている。

(b) **根拠**

- P3: [s1-brief.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:55)
- planはAのdiff/digest/cross-pairとX同時切替を機械判定可能としている: [stage2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:263)

(c) **壊れ方**

P3どおりならcross-pairやatomic switchの合格条件が裁定待ちとして放置される。planどおりならR4のとおりpolicyなしXが先に発効する。親とplanのどちらの段階分割も、そのままでは単独green列を構成しない。

(d) **判定: real**

## §6の6検査との同時整合

| §6の検査 | 判定 |
|---|---|
| 同一floor pathの別bytes | versionedな新pathなら回避可能。下記F2のとおり疑いはrefuted |
| floor更新・prediction/journal旧 | R4。policy実装順序に穴がある |
| activation 2・floor G1 | planにはcontract hash照合とcross-pair mutationがあり、設計記述上は拒否可能。実装は未確認 |
| record 2あり・head 1 | R2。inactive suffix設計と両立しない |
| generationだけ・pointerなし | R3。generation direct-refで迂回可能 |
| active freeze generation ≥2 | R5。現行reject-allのまま段7完了を偽装できる |

したがって、6検査すべてを保持しながら提案遷移を構成することはできない。

## refuted

### F1 — M1/M2の実測事実そのものが誤り、という疑い

(a) **主張**

M1/M2の事実部分を反証できるか検査した。

(b) **根拠**

M1のexact diffは [s8b_ratified_freeze.py:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1205)、M2のliteral authorityは [env_contract.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:373) と [env_contract.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:528) に実在する。

(c) **検査構成**

lower Aへのextra pathは `approval-commit-diff`、valid suffix + head1はactivation head mismatchになる。

(d) **判定: refuted**

M1/M2は事実として正しい。誤りはR7の一般化部分である。

---

### F2 — versioned floor path自体も `_immutable_introductions` に拒否される、という疑い

(a) **主張**

新pathでも履歴不変検査が無条件に失敗するか検査した。

(b) **根拠**

検査は同一pathについて、全ancestorのOIDが absentまたはHEAD OIDであることだけを要求する: [s8b_ratified_freeze.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:469)

(c) **検査構成**

過去に存在しないversioned pathを一度だけ追加すれば条件を満たす。旧固定pathを別bytesへ更新した場合だけ `history-mutated`。

(d) **判定: refuted**

---

### F3 — core結合に使う既存fieldがすべて架空、という疑い

(a) **主張**

`activation_serial`、`activation_state_sha256`、`active_contracts[]`、floor `contract_sha256`、freeze `floor_protocol.{path,sha256}` の実在を検査した。

(b) **根拠**

activation schemaは [env_contract_activation.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:17)、active rowは [env_contract_activation.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:24)、freeze source recordは [s8b_ratified_freeze.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:875) に実在する。

(c) **検査構成**

planのcore field表のこれらについて、台帳との不一致は見つからなかった。問題はR8のQ schemaなど追加部分である。

(d) **判定: refuted**

---

### F4 — `new env + old freeze` の拒否条件がplanに全く無い、という疑い

(a) **主張**

cross-pair refusalが記述上欠落しているか検査した。

(b) **根拠**

floor contract hashと選択environment rowの一致要求が [stage2-plan.md:104](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:104)、両cross-pair mutationが [stage2-plan.md:264](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:264) にある。

(c) **検査構成**

B内でpegasus g2 rowとG1 protocol contract hashを組み合わせれば、記述されたresolver契約上は拒否対象になる。

(d) **判定: refuted**

ただし将来resolverは未実装なので、実際の検出力は未確認。

## 総括

最も重い3件は次のとおり。

1. **lower freezeのG/A commitがtopologyから欠落し、Fを1 commitとしては機械的に構成不能**。
2. **inactive activation suffixと、§6で保存すると宣言されたterminal/head検査が両立しないうえ、generation直参照で`no-active`も迂回できる**。
3. **policy実装前にXを発効し、段4・7はreject-allでも完了できる**。

**判断: この設計を進めてはならない。** 現状は、正常遷移を構成できない経路と、未批准generationをproductionへ昇格できる経路が同時に存在し、完了判定もそれらを検出しない。