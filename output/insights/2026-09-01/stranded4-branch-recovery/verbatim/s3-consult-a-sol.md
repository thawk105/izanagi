静的検査のみであり、pytest は実走していない。

## 所見

### 対象 test は「collector 全体」ではなく、四つの異なる束縛を一つに混在させている

- 判定: 重要
- 根拠: [test_codex_reasoning_ab.py:8611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_reasoning_ab.py:8611) は、順に 1) manifest 由来の rollout SHA と外部 file 全体、2) token slice と同じ test file 内の SHA literal、3) 外部 file 16 行目と token slice、4) `_validated_usage` の正経路を検査する。collector や `collect_run` は呼ばず、token slice の JSON を直接 validator に渡すだけである。
- 含意: 親の「golden の書き換えを検出」は、原本と pin を固定したまま `_REAL_TOKEN_SLICE` だけを書き換える場合には正しい。一方、「捏造を検出」は過大であり、slice、slice SHA、manifest の期待値を同じ主体が揃えて変更すれば防げない。この限界は [CLAUDE.md:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/CLAUDE.md:103) と F715 の「揃えて書き換えれば通る」事例 [docs/failures.md:18854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/docs/failures.md:18854) に一致する。

### 既存 test は大部分を代替するが、原本内の行所属だけは代替していない

- 判定: 重要
- 根拠: manifest の session ID、rollout SHA、prompt SHA は [test_codex_reasoning_ab.py:1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_reasoning_ab.py:1765) が literal に固定する。SHA pin による rollout 選択と mismatch 拒否は [test_codex_reasoning_ab.py:7714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_reasoning_ab.py:7714) 以降の合成 test 群、usage schema の正負例は [test_codex_worker_ledger.py:430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_worker_ledger.py:430) から [test_codex_worker_ledger.py:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_worker_ledger.py:536) が担う。対して `_REAL_ROLLOUT` と `_REAL_TOKEN_SLICE` を結ぶ参照は対象 test だけで、原本 SHA と一致する working-tree file または到達可能 Git blob も静的検索では見つからなかった。親の探索結果も [consult-materials.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-stranded4-recheck-20260901/consult-materials.md:47) と一致する。
- 含意: 対象 test が失われても、production の SHA verifier と usage validator の受理集合が丸ごと無防備になるわけではない。失われる固有の保証は「SHA `9b90...` の byte image の 16 行目が `_REAL_TOKEN_SLICE` だった」という再検証可能性であり、原本なしに同じ保証を再構成することはできない。

### もう一方の壊れた test は、`replacements=9` を完全には pin していない

- 判定: BLOCKER
- 根拠: [test_codex_reasoning_ab.py:8575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_reasoning_ab.py:8575) は 0、9、10 の三値を試すが、正例か否かを `TOOL.PROMPT_SOURCE["POS"]["replacements"]` 自身で決める。manifest literal test は prompt SHA だけを固定し、chars、bytes、replacements は固定していない [test_codex_reasoning_ab.py:1776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/orchestrator/tests/test_codex_reasoning_ab.py:1776)。したがって `replacements` を 8 など三値外へ変えると、三 case 全てが負例になって通り得る、というのがコードからの推論である。
- 含意: 案 1 を単なる合成 fixture 化だけで済ませると、凍結 prompt provenance の受理集合が既に持つ穴を残す。`prompt_source` の dict 全体を literal 固定し、合成 test では 9 を独立した正例、0 と 10 を負例として固定する必要がある。

### 規律 7 の第一 bullet 単独では案 3 を禁じないが、案 3 の in-place 上書きは規律 7 全体に反する

- 判定: 重要
- 根拠: 「現行コードとの差だけを理由に無効にしない」という [CLAUDE.md:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/CLAUDE.md:100) の条件は本件に直接当たらない。案 3 の動機は現行コードとの差ではなく原本消失であり、別 rollout への変更も過去測定の「無効化」とは同義でない。一方、記録を続けるという本文 [CLAUDE.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/CLAUDE.md:98) と、過去の判定を追記でのみ訂正する規定 [CLAUDE.md:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/CLAUDE.md:102) は、T-181 manifest を別 session の記録へ上書きする案を退ける。
- 含意: 親の結論は正しいが、「再現不能でも事実は変わらない」という第一 bullet だけを禁止根拠にするのは拡大解釈である。別 rollout は新しい versioned manifest と新しい測定として追加できるが、既存 `TASK_MANIFEST` を上書きすると manifest digest、prompt receipt、旧 T-181 成果物との参照関係が別物になる。

### 案 4 と曖昧な案 1 は恒真ゲートになり、案 3 は別対象を検査する偽の代替になる

- 判定: BLOCKER
- 根拠: file 不在時の skip は、対象不在を黙って通した F9 [docs/failures.md:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/docs/failures.md:208) と、依存欠落のまま rc=0 になった F697 [docs/failures.md:18550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/docs/failures.md:18550) の同型である。案 3 は新 rollout の byte 束縛としては実効的でも、T-181 の束縛を守る test ではなくなるため、元の説明を残せば「説明が実装より強い」F564 [docs/failures.md:15741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/docs/failures.md:15741) の同型になる。期待値も同時に変更して緑化すれば F27 [docs/failures.md:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/docs/failures.md:733) と F80 [docs/failures.md:3401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/docs/failures.md:3401) に近い。
- 含意: 案 4、または案 1 を `skip`、`xfail`、条件付き no-op として実装すると、外部 file が永久に無い現環境では検査せずに受入 rc=0 となり、受理集合が広がる。案 3 は検査強度を保っても、受理する provenance を T-181 から別測定へ交換するため、規律 2 [CLAUDE.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/CLAUDE.md:67) に照らして無審査の期待値変更として扱うべきである。

### 四案の外には「履歴証拠」と「現行の挙動 test」を分離する解がある

- 判定: 重要
- 根拠: 過去の実測 artifact は POS rollout が一意に解決され、当時 pin SHA と一致したことを記録している [premise.json:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/output/insights/2026-08-12_t886-rollout-fastpath/premise.json:10)。現行 production は source 不在時に `_find_rollout` の件数不一致で fail-closed になる [codex_reasoning_ab.py:628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/tools/codex_reasoning_ab.py:628)。また `render_prompt` の SHA、size、replacement 検査は [codex_reasoning_ab.py:3671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stranded4-recheck-20260901/tools/codex_reasoning_ab.py:3671) に独立した production 挙動として存在する。
- 含意: T-181 の literal と過去の合格記録は保持しつつ、「原本 membership の現在の再検証は unavailable」と追記できる。既定受入では manifest 全 dict の literal 固定、合成 rollout による `render_prompt` の正負例、既存 ledger test を走らせ、原本監査は `matched / mismatch / unavailable` の三状態を返す別監査にする。`unavailable` を pass や skip と数えず、受入結果にも「source-bound を再確認した」と主張しなければ恒真化しない。

## 各案の評価

### 案 1: 条件付きで採る

単なる条件付き skip としては採らない。条件は、凍結 `TASK_MANIFEST` を不変に保ち、原本再検証の unavailable を追記し、`prompt_source` 全体の literal pin、独立した正例 9 と負例 0・10、合成 rollout による production 経路の挙動 test へ分解することである。

さらに、T-181 source が必要な production 操作は現状どおり fail-closed にし、別監査の unavailable を受入の緑や source-bound 合格として扱ってはならない。この具体形なら「壊れた検査を消して通す」のではなく、再取得不能な履歴保証を正直に状態化し、現行コードの挙動保証を hermetic に残せる。

### 案 2: 条件付きで採る

既存 pin `9b90...` に byte 一致する原本を、信頼できる backup から回収できた場合に限り採る。その bytes を一切再生成せず repo 相対 fixture とし、既存 pin を変更しないなら最も強い解である。

現時点では working tree、通常 filesystem、到達可能 Git blob のいずれにも一致物がなく実施不能である。token slice や記録値から似た file を組み立て、その file の新 hash へ期待値を変える形は案 2 ではなく F27 型なので採らない。

### 案 3: 採らない

別 rollout への in-place 張り替えは、T-181 の測定記録を別測定の provenance に置換する。規律 7 の第一 bullet が直接禁じるわけではないが、記録継続と追記訂正の規定に反する。

別 rollout を使うなら、新しい task ID、manifest version、事前条件、成果物を持つ新測定として追加すべきである。その successor の raw rollout は今回は repo 内へ同時保全し、再び retention 領域だけに置いてはならない。

### 案 4: 採らない

file 不在時の skip は F9 と F697 の直接的な再発であり、現環境では恒久的に発火しない test になる。pytest の rc=0 を得ても source binding は一度も検査されず、DW-O18 の `child-green` を誤った意味で満たす。

これは規律 2 に対しても「赤い検査を走らなくして通す」変更である。案 1 の具体化と異なり、保証の分解も主張の降格も行わないため受理集合だけを広げる。

## 総括

推奨は、案 1 を「skip」ではなく履歴証拠と hermetic な挙動 test への分解として具体化する案である。T-181 literal は不変、原本再検証は unavailable と追記し、prompt provenance 全体と production の正負例を固定する。新 rollout が必要なら既存記録を上書きせず successor 測定を作る。

この推奨が誤りになるのは、原本 16 行目との live membership が現行 certification の必須条件であり、過去の合格記録では代替不能だと裁定される場合である。