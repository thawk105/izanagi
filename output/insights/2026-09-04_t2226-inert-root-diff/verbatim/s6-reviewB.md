## 裁定との一致

実装差分については反証なし。段4裁定 4.1〜4.3 の順序、条件、理由コードと一致している。

- compiler identity、comparable argv が先行する。[condition_meaning_gate.py:2495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2495)
- 非 inert は、旧 `preprocess-root-dependent-builtin`、closure equality、bytes difference の順を維持している。[condition_meaning_gate.py:2508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2508)
- raw bytes 一致は分類器を通らず、旧 `stock-inert-preprocess-identical` のままである。[condition_meaning_gate.py:2546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2546)
- 分類不能または残差ありは旧 `stock-inert-mismatch` に戻る。[condition_meaning_gate.py:2584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2584)
- 旧差分との突合せでも、非 inert の受理集合、理由コード、判定順序を変える差はない。

字面上の余分は、分類器が空 root も分類不能にする点である。[condition_meaning_gate.py:2261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2261) production root は `resolve(strict=True)` 後の絶対 path なので到達不能であり、これは nit。成果物への影響はない。

ただし、裁定自身に must-fix がある。4.4 が主張する「置き場所由来のみ」は、この分類器では証明できない。

- root は行中の任意位置で一致すればよく、path token の左境界を検査しない。[condition_meaning_gate.py:2300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2300)
- suffix が requested closure の既存 identity と一致することしか要求しない。[condition_meaning_gate.py:2321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2321)
- builtin 条件は、どこかの dependency の生 bytes に `__FILE__` があれば満たせる。コメント内でも成立する。[condition_meaning_gate.py:2029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2029) [condition_meaning_gate.py:2331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2331)
- inert 経路では closure digest equality も要求しない。[condition_meaning_gate.py:2508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2508) [condition_meaning_gate.py:2546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2546)

したがって、requested/control の異なる source にそれぞれ `"tag:<root>/cc/silo/transaction.cc"` を埋め込み、同じ dependency のコメントへ `__FILE__` を置けば、実際の builtin 展開でない差でも新 green になる。M1 の「closure 外 literal」負例ではこの closure 内 literal を落とせない。

成果物影響: source 差から生じた文字列を置き場所由来と誤認した green record が certified selection に入り、材料レポートと試行台帳がその record を参照し得る。

## A-2 への到達性

現在の実 A-2 については反証なし。6本すべてが新 green に到達する。

1 workload あたり次の3本であり、2 workload で計6本になる。

- stock の `BACKOFF_FIXED=-1`
- stock の `BACKOFF_NOINLINE=0`
- adopted の `BACKOFF_NOINLINE=0`

defaults、macro loop、request 構築は [paper_story_a2_certification.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/paper_story_a2_certification.py:583)、[paper_story_a2_certification.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/paper_story_a2_certification.py:613) にある。`stock_comparison` が明示されるのは `BACKOFF_FIXED=-1` だけだが、gate の inert 判定は default equality も含むため、`BACKOFF_NOINLINE=0` も同じ stock 経路へ入る。

path 表記も整合する。

- A-2 の clean source は `resolve(strict=True)` 済みである。[paper_story_a2_certification.py:3039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/paper_story_a2_certification.py:3039)
- variant と stock は `capture_define_inputs` で再度 resolve され、その表記が `-S` に入る。[condition_meaning_gate.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:748) [condition_meaning_gate.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:1583)
- 親の実測にある実際の展開形は `<variant_root>/cc/silo/transaction.cc` と `<source_root>/cc/silo/transaction.cc` である。これはそれぞれ `source/cc/silo/transaction.cc` に対応する。
- relative include 表記が `cc/silo/../../include/debug.hh` のように `..` を含んでも、分類器は closure 確認用だけ `source/include/debug.hh` へ字句正規化する。[condition_meaning_gate.py:2306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2306)
- 実際の出力へは suffix を変更せず root だけを写すため、control 側も同じ relative suffix なら byte 一致する。[condition_meaning_gate.py:2322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2322)
- closure 側は `resolve(strict=True)` 後に `source/<relative>` を作る。[condition_meaning_gate.py:2035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2035)

通常 directory 上の `..` なら字句正規化と `resolve()` は一致する。symlink をまたぐ `..` では一般論として一致しないが、提示された A-2 の owner path と親実測にはその反例がない。compile source operand が root を含まない相対表記なら置換ゼロで赤になるが、これも現在の A-2 の実測表記には該当しない。

成果物影響: 6本が condition admission を通過し、A-2 は campaign、raw material、trial ledger の生成へ進める。

## scope の逸脱

反証なし。

production 差分は inert 専用 private helper、その import、既存 evaluator と既存 green validator への分岐追加だけである。新しい gate、台帳、一般 path utility、A-2 driver の変更はない。

テスト差分も test-only helper と裁定済み6 caseの追加であり、既存テストの期待値は変更していない。[test_condition_meaning_gate.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/tests/test_condition_meaning_gate.py:148) [test_condition_meaning_gate.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/tests/test_condition_meaning_gate.py:614)

## schema と record の整合

反証なし。

- 4 field は分類直後、record 発行前に evidence へ入る。[condition_meaning_gate.py:2569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2569)
- 新 reason のときだけ exact key 集合が4件増える。[condition_meaning_gate.py:3443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3443)
- exact `int`、`tuple[str, str]`、exact `False`、`-S` source root との束縛を検査する。[condition_meaning_gate.py:3535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3535)
- `status_contract` は新 comparison と digest inequality を要求し、既存2契約は不変である。[condition_meaning_gate.py:3573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3573)
- `_canonical_value` は tuple/list を再帰変換し、新しい str、int、bool をすべて扱える。[condition_meaning_gate.py:681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:681)
- `_issue_arm_record` は新 evidence を含む digestを生成してから integrity 検査し、issuer capability を付与する。[condition_meaning_gate.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:963)

red record は arm-specific green schema を通らないため、4 field を載せても整合する。[condition_meaning_gate.py:3862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3862) ただし従来の `stock-inert-mismatch` と比べ record digest と record ID は変わる。

成果物影響: red の受理集合は変わらないが、新規診断 receipt や試行記録が参照する red record ID は旧版と一致しなくなる。

## 他 driver への影響

| driver | 変更後の挙動 |
|---|---|
| `backoff_sweep` と helper 利用群 | 別 checkout 間の root-only inert mismatch が新 green になり、campaignへ進む。 |
| `s1_direct_comparison` | 別 worktree の default-equality arm が新 green になる。 |
| `screening_driver` | default equality と spec-declared inert の root-only mismatch が新 greenになる。 |
| `silo_ladder_rung1` | distinct stock root を使う inert armへ同じ変更が届く。 |
| `paper_story_a1_paired` | root-only inert armが受理される。 |
| T1683 | distinct stock root の inert comparison が同様に受理される。 |
| SS2PL study | requested==default の stock comparison が同様に受理される。 |

これは A-2 専用ではないが、共通 `evaluate_define_supply_effectuation` の inert 経路を対象とする裁定どおりである。raw-identical fixture は引き続き旧 reason、semantic residual は引き続き red、非 inert は不変である。

既知の例外は T316 である。新 green 自体は出るが、T316 固有 validator が旧 reason/comparison の exact 一致しか許さないため、実 receipt は引き続き `S6_CONDITION_GATE_UNPROVEN` になる。これは裁定済み scope 外で、overall verdict の後退ではない。ただし内部 reason、record ID、runtime hash は変わる。

成果物影響: 上表の driver は新しい試行台帳や材料を生成可能になる。T316 は receipt の参照値だけ変わり、sandbox backend 採用判断は前進しない。

## 費用の見積り

現在の A-2 には実用上耐える。

1出力あたりを `B` bytes、`N` 行とすると、分類器の追加 peak は概ね次のとおりである。

- 2側の `split(b"\n")` による payload 複製: 約 `2B`
- bytes object と list pointer: 約 `82N` bytes
- 元の requested/control 出力も存続するため、分類中の合計は概ね `4B + 82N`

例として片側50 MiB、30万行なら、分類器追加は約124 MiB、元出力を含む合計は約224 MiBである。片側100 MiBでも概ね424 MiBで、14 GiB級の上限に対して十分小さい。

時間は `split` と2回の対応行走査で `O(B+N)`。A-2 の root-only 差では inner byte scan は差のある数行だけなので、数十万行でも1評価あたり概ね秒未満から数秒、6評価合計でも数秒から十数秒程度と見積もる。configure と2回の preprocess に比べ支配的ではない。

全行が異なる失敗入力では Python の1 byteずつの走査が数十秒級になり得るが、二乗化はない。さらに詰めるなら、line count を分類 loop 内で同時計上して全走査を1回減らし、差分行の root 探索を `bytes.find` へ替え、offset iteratorで split payload 複製を避けられる。費用面の must-fix ではない。

## must-fix 一覧

1. root 置換が実際の `__FILE__` または `__BASE_FILE__` 展開に由来することを証明する。現在の「closure 内 suffix と、どこかに builtin token」という条件では、closure 内 path を含む任意 literalを green にできる。

   具体的な修正案は、raw mismatch 時に両側を追加で preprocessし、requested/control それぞれへ同じ canonical tokenを出力する `-fmacro-prefix-map=<source_root>=<TOKEN>` を与えて byte 完全一致を要求すること。compiler が書き換える genuine builtin pathだけが消え、hard-coded literal は残差として red になる。未対応 compiler は fail-closed にする。

## 総括

裁定 4.1〜4.3 の実装、A-2 6本の到達性、scope、schema、他 driverへの予定された波及、線形費用には反証なし。非 inert の受理集合、理由コード、判定順序も不変である。

ただし裁定 4.4 の「置き場所由来のみ」という根幹の主張は、現分類器では成立しない。closure 内 root-shaped literalを builtin由来と誤認できるため、must-fix 1件として受入不可と判断する。