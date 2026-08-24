### 所見 1

- 主張: `DW-O28` の D271 admission は、条件 2・3への反証には耐えるが、必須の意味検索記録と `DW-G03` を満たしていないため現状の brief だけでは成立しない。
- 具体的な破れ方: 入力=`F26` の 2026-08-01/08-05 再発、状態=両件を「独立 2 例」と数えて全 dev-wave へ L2 義務を一般化、結果=`F26` 自身が「同一経路」と明記する同一 producer/consumer の反復だけで制度一般化が通る。
- 根拠:
  - 条件1は少なくとも1件の実害で成立するが、独立2例ではない。[failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/failures.md:589) は「2026-08-01 の再発と同一経路」、同:596 は「前回の経路欠落」と明記する。一方 `DW-G03` は異なる producer/consumer の2件を要求する。[core.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/dev-wave/core.md:69)
  - 条件2への反証は見つからない。`check_wave_startup.py` は観測専用で mutating git を拒否する。[check_wave_startup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_wave_startup.py:2) `dev_wave_land.py` は land 後 cleanup を呼ばず、daemon も cleanup/branch deletion を持たない。[daemon.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/dev_waves/daemon.py:1)
  - 条件3の意味検索では、`DW-O20`=開始、`DW-O23`/`DW-O25`=land前、`cleanup-branches` §3=明示 cleanup 実行時だった。同一発火点「land成功後」の既存運用正本は見つからず、F26は事故・恒久対応の物語、historical insight の `land 後の branch/worktree cleanup` はタスク候補にすぎない。[cleanup-branches.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/.claude/commands/cleanup-branches.md:28) [s2-integration-plan-verbatim.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/output/insights/2026-08-01_t207-adoption-audit/s2-integration-plan-verbatim.md:54)
  - ただしD271は検索範囲・検索語・hit・real/refutedの記録を要求するのに、briefは結論だけである。[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/decisions.md:12458) [brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-stage9-self-cleanup/brief.md:82)
- 提案する対処: scope 外として裁定へ返す。第二の独立経路を示すか、D516型の明示適用除外として `DW-O28` admission を記録する。

### 所見 2

- 主張: 「post-landだから既存正本と別発火点」と主張しながら pre-land の条件23で読む設計は、P1とP2が論理的に両立しない。
- 具体的な破れ方: 入力=`dev_wave_land.py` が `landed` を返す、状態=`DW-O28` を読んだのは land 起動前の一度だけ、結果=cleanup直前には条件を再評価・再読せず、前段記憶で事後義務を実行する。
- 根拠: 読み込み契約は「各条件成立操作の直前」に再評価・読了し、記憶で代用しない。[dev-wave.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/.claude/commands/dev-wave.md:19) 条件23は「local main を取り込む直前」である。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/.claude/commands/dev-wave.md:112) briefはO28の発火点を「land成功後」として条件3を正当化する一方、同じ節を条件23へ載せる。[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-stage9-self-cleanup/brief.md:82)
- 提案する対処: 実装で閉じる。条件27を「land成功後の自己撤去直前」として新設し、そこで `DW-O28` を読む。条件23への併載は採らない。

### 所見 3

- 主張: P2のbyte収支は最終的には収まるが、全角括弧7対の置換はexact trigger pinを1件壊す。
- 具体的な破れ方: 入力=条件20の `（最遅: …）` をASCII括弧へ変更、状態=`CONDITION_TRIGGER_CONTRACT["20"]` は全角のまま、結果=`check_docs.py` が条件20のtrigger不一致を報告する。
- 根拠:
  - 7対14文字の `（`/`）` は各3→1 byteなので、減少は正確に28 bytes。
  - 行23への `` , `DW-O28` `` の追加分は11ではなく10 bytes。結果は `9497 - 28 + 10 = 9479 bytes`、最長行は121 charsで、上限9500/140を満たす。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:263)
  - 条件20だけはtrigger全文が逐語登録されている。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:890) 比較箇所は同:5836-5853。
  - `D2_ROLLBACK_STRUCTURE` と `CODEX_AUTHORING_STRUCTURE` は括弧自体を要求しないため影響しない。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:899)
  - `docs/skill-self-improvement.md` は変更されず、5963/6000 bytes・最長79/100 charsのまま。
- 提案する対処: 実装で閉じる。最小案は条件20の1対を残し、他6対だけ半角化する。この場合も総量9483 bytesで収まる。全7対を変えるなら、識別子key `20` のtrigger定数と独立literalテストも同時更新する。

### 所見 4

- 主張: 「予算引き上げを提案しないD433」という前提は、決定番号も現行方針も誤っている。
- 具体的な破れ方: 入力=条件27が予算超過する、状態=旧先例を絶対禁止と誤読、結果=予算都合で条件23へ事後義務を押し込み、所見2の発火点不整合を作る。
- 根拠:
  - O25不変更・158-byte追記撤回はD433ではなくD432末尾にある。[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/decisions.md:17995)
  - D433はmutation fan-outの機体不成立に関する別決定である。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/decisions.md:18009)
  - より新しいD671は、dev-wave docsと`COMMAND_LIMITS`を必要最小限だけ引き上げてよいと明示する。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/decisions.md:26602)
  - 87-byteの最短例 `| 27 | land 成功後の自己撤去直前 | ... DW-O28 |` なら、28-byte縮約後でも9556 bytes、現上限から56 bytes超過する。
- 提案する対処: 実装で閉じる。条件27の逐語を先に確定し、安全な縮約後に残る分だけD671に従って最小引き上げを記録する。

### 所見 5

- 主張: `DW-O28`を条件23または条件27だけへ結ぶ限り層予算上はL2であり、L1へ落ちるのはU段dispatchへも追加した場合だけである。
- 具体的な破れ方: 入力=「段9の義務だから」と段9のU行にも`DW-O28`を追加、状態=現L1が10624/10625、結果=見出しだけでも1 byteを超えるためL1予算違反になる。
- 根拠: 層分類はU edgeだけからL1/L1.5を作り、残りをL2とする。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:4706) 条件edgeはmode=`C`として構築される。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:4483)
- 提案する対処: 検査で閉じる。`DW-O28 ∈ L2`、`DW-O28 ∉ L1∪L1.5`を独立literalで固定する。`_OPERATION_NUMBERS`はD561どおり変更しない。そこへ28を足しても層自体はL2だが、`_ALL_OPERATIONS`・条件28・段5/6セルへ不要な連鎖を起こす。[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/decisions.md:22795)

### 所見 6

- 主張: planには`DW-O28`の逐語案が存在せず、byte上限とpinを実装前に検証できない。
- 具体的な破れ方: 入力=訂正後briefを実装、状態=実装子がplanの唯一の逐語blockを採用、結果=`DW-O25`を変更して訂正後P1とO25 exact pinに反するか、未審査のO28本文を即興する。
- 根拠:
  - planの唯一の逐語案は `DW-O25 — …自己撤去関門` である。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-stage9-self-cleanup/plan.md:198)
  - そのUTF-8 byte数は末尾LF込みで959 bytesであり、plan記載の960ではない。
  - 訂正後briefは新規`DW-O28`を要求する。[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-stage9-self-cleanup/brief.md:82)
  - checkerの順序pinは`DW-O25 > DW-O23`だけで、O26/O27/O28の番号順は検査しない。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:5526)
- 提案する対処: 実装で閉じる。plan v2へO28全文と実測byteを置き、O27の後へ配置する。番号順は現状の慣例であって既存checker要件ではない。破壊・権限義務なのでO28自体も節全文exact pinへ追加するのが妥当である。

### 所見 7

- 主張: `REQUIRED_REFERENCE_SECTIONS`へO28を足す変更は、現planが列挙していない複数の手書きfixtureとmutation registryへ連鎖する。
- 具体的な破れ方: 入力=productionのregistry・command・operationsだけを更新、状態=合成repoのoperations ID tupleにO28なし、結果=各`_build_min_repo()`が「H2 DW-O28が0件」「registryとtyped edgeの閉包不一致」を出し、多数のguardテストが同時に落ちる。
- 根拠: 合成operationsは`REQUIRED_REFERENCE_SECTIONS`ではなく手書き`_SYNTHETIC_REGISTERED_OPERATION_SECTION_IDS`から生成される。[test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:194) [同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:858)
- 提案する対処: 検査で閉じる。更新閉包は次の全部である。
  - `tools/check_docs.py`: `REQUIRED_REFERENCE_SECTIONS`、選んだ条件の`CONDITION_DISPATCH_CONTRACT`、条件27なら`CONDITION_TRIGGER_CONTRACT`。`_OPERATION_NUMBERS`と`_ALL_OPERATIONS`は不変。
  - O28をexact pinする場合: `DEV_WAVE_DW_O28_SECTION_LITERAL`と`DEV_WAVE_EXACT_VISIBLE_SECTIONS`。
  - `test_check_docs.py`: `_SYNTHETIC_REGISTERED_OPERATION_SECTION_IDS`、O28本文renderer、L2 literal集合2箇所（現2358–2365、2796–2803）。
  - `test_operation_contract_pins_exact_section_set`: registered集合、条件23併載ならO23の期待pair、条件27なら独立target/trigger assertion、`_OPERATION_CONDITION_KEYS`非所属assertion。
  - command guard: 「O28 edgeだけ削除」「O28 H2だけ削除」のmutation callback、`_COMMAND_GUARD_CASES`、needle、expected-count、登録完全性meta-test。
  - exact pin時: production/fixture一致、UTF-8 byte assertion、exact-map assertion、raw HTML拒否cases、heading-only/contract-weakened mutation、実repo正例。
  - O28本文へ`tools/dev_wave_land.py`を再掲しない。checkerはそのpathをoperations全体でexact 1件かつO23内だけに制限する。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:5750)

### 所見 8

- 主張: 今回の発話をD204の通常適用とみなして将来すべてのdev-waveへ自動branch削除を常設する解釈は誤りである。
- 具体的な破れ方: 入力=将来ユーザーが削除を指示せず通常の`/dev-wave`を起動、状態=O28が恒久規則として成功後にbranchを削除、結果=対象を特定した当該実行時の削除指示なしにAIがbranch削除を行う。
- 根拠: D204は「対象を特定したユーザー発話がある場合のみ」とし、恒久permission ruleの常設を明示的に禁じる。[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/decisions.md:9824) 引数なし`cleanup-branches`を対象特定と認めなかった実例もある。[worklog-phase3-0813-519.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/archive/worklog-phase3-0813-519.md:3)
- 提案する対処: scope 外として裁定へ返す。採用するならdecisionには「本発話はD204の通常適用ではなく、次の狭い恒久例外としてD204を部分supersedeする」と書き、対象を同一invocationのexact wave path/ref、`tested_tip ⊆ refs/heads/main`、`branch -d`、localのみ、非一括、force/remote禁止へ束縛する。その他のbranchにはD204を維持する。

### 所見 9

- 主張: briefの実測値は概ね再現するが、そこからの一般化に2件の誤りと1件の未検証主張がある。
- 具体的な破れ方: 入力=現在の1 worktreeとF26の同一経路2回を全EnterWorktree・独立2例へ一般化、状態=将来のunlocked worktreeまたは同型単一経路、結果=unlock必須を普遍前提とし、G03を満たしたと誤記する。
- 根拠:
  - 静的再計算は入口9497/9500、L1 10624/10625、L1.5 9565/9566、O25 649/1000で一致した。
  - 現worktreeはHEAD `59ef288c…`、`locked claude session …`であり、現在例は正しい。ただしrepo側の規範は「子を走らせるworktreeはlockする」であり、外部harnessが全EnterWorktreeを常にlockする実装証明ではない。[operations.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/dev-wave/operations.md:151)
  - 「dev-wave docs/commandに撤去義務0件」はその狭い範囲では正しいが、repo全体ではF26とcleanup §3が存在する。
  - `check_docs.py baseline rc=0`はこのread-only consultでは実走しておらず、緑として再確認していない。
  - F26の2回を独立例とする結論は所見1のとおり誤り。
- 提案する対処: 検査で閉じる。測定記録を「checkout 59ef288cの現worktree」に限定し、harness一般化を削るか外部実装の一次証拠を追加する。F26は「発火2回・独立経路1件」と記録する。

## 総括

最も重い所見は、条件23ではpost-land義務の直前再読にならないこと、D204を恒久permissionへ拡張していること、D271の検索記録とDW-G03が未閉鎖なことである。  
いずれもcheckerの表面整合だけでは検出できず、現案のまま実装へ進めてはならない。

置き場所の最終推奨は、`DW-O28`をO27後に新設し、独立した条件27「land成功後の自己撤去直前」から読む案である。  
条件23併載は不採用。入口予算はD671に従う必要最小限の引き上げ、O28全文exact pin、D204の狭い部分supersedeを同じ裁定で確定する。