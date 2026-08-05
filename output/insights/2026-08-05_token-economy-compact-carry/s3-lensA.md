## 総括

- **P1′（ordinal 併記）を推す。** P1 の「直前」は受理済み履歴から一意に復元できない。
- 最重要 1: compact 形は `spool_fold` の意味的受理集合を変えるため、衝突 sentinel と負例が必要。
- 最重要 2: 生存 consumer `.claude/commands/rulings.md` が scope から漏れ、裁定参照を取り落としうる。
- 最重要 3: D70 の現行実装は脱落を検出するが、提案テストは ID 単独 source の脱落を固定していない。

### 1. [P1] P1 の「直前エントリ」は一意に導出できない

親は ordinal を情報量ゼロとするが、コードは ordinal の単調性・欠番を固定せず、現行末尾と全履歴最大値を別々に取得する。[brief.md:13](/work/1/SFC/tanab/dev-wave-jobs/token-economy/brief.md:13)、[spool_fold.py:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1110)、[spool_fold.py:1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1128)、[spool_fold.py:1792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1792)

具体入力:

```text
archive: 2026-07-31 (9)  - [T-001] 古い本文
current: 2026-08-01 (5)  - [T-001] 新しい本文
次の fold: ordinal は max+1 = (10)、prior_ordinal は current 末尾 = (5)
P1 出力: - [T-001]
```

数値上の前項 `(9)` と append 元の直前 `(5)` のどちらも「直前」になりうる。P1′なら `- [T-001] (5)` で一意である。

実 corpus にも反例がある。entry `(77)` の直前は `(76)` だが、同一 entry 内に `(73)`, `(74)`, `(75)` への参照が混在する。[worklog-phase3-0731-77.md:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/archive/worklog-phase3-0731-77.md:73) 静的全数では exact carry 23,635 行中 1,316 行が `参照先 != entry ordinal - 1` だった。現行 `(176)`〜`(182)` だけなら直前参照だが、履歴一般への主張は偽である。

**成果物影響:** P1 を採ると誤った本文 digest に束縛され、正しい fragment の拒否または stale fragment の受理により台帳本文が変わる。

### 2. [P1] P1′も `spool_fold` の意味的受理集合を変える

現行は旧 carry に完全一致しない項目を実体本文として digest する。[spool_fold.py:1151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1151) 提案は同じ fallback を維持しつつ `- [T-NNN] (N)` を carry に再分類する。[s2-plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/s2-plan.md:60)、[s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/s2-plan.md:74)

具体入力:

```text
entry (1): - [T-001] 本文 A
entry (2): - [T-001] (1)
fragment:  [T-001] を更新、base = sha256("- [T-001] 本文 A\n")
```

変更前は entry `(2)` 自身が実体なので `base-mismatch`。P1′導入後は `(1)` への carry と解釈され、同じ fragment が緑になる。したがって「D70 regex の受理集合は不変」は正しいが、brief の広い「受理集合の値は変わらない」は成立しない。[brief.md:30](/work/1/SFC/tanab/dev-wave-jobs/token-economy/brief.md:30)、[brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/token-economy/brief.md:41)

現行 worklog と archive には P1′同形・ID 単独実体行とも 0 件だったため、現在の凍結 corpus との衝突はない。ただし land 前 corpus sentinel が必要である。併せて次を負例に固定すべきである。

```text
- [T-001] (0)             # compact-like 誤形を実体へ fallback させるのか
- [T-001] (1) 実体本文    # fullmatch を緩めても carry に誤分類しないこと
```

提案された `id_only_item_remains_substantive` は後者を kill しない。

**成果物影響:** 衝突・緩和を放置すると stale `base` が通り、台帳の実体本文と後続参照が上書きされる。

### 3. [P1] `rulings` の生存 consumer が scope 漏れ

段 2 は追随先を worklog と spool の README に限定している。[s2-plan.md:146](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/s2-plan.md:146) しかし rulings dispatcher は旧語句「変わらず (前エントリ参照)」だけを carry として遡るよう指示している。[rulings.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.claude/commands/rulings.md:13)

具体入力:

```text
末尾: - [T-435] (181)
(181) 側の実体: 「ユーザー裁定要 …」
```

compact 行自身には「ユーザー」「裁定」も「変わらず」もないため、末尾だけを読む rulings が参照を辿らず索引から落としうる。これは歴史記録ではなく現役 consumer であり、同 wave の scope に必要である。現在 4,988/5,000 bytes なので、予算内の net 縮約で更新する必要がある。[check_docs.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:170)

**成果物影響:** 追随しない場合、裁定レポートの受理・参照集合から判断待ち項目が脱落し、後続作業が誤って未認識になる。

### 4. [P2] D70 本体は有効だが、提案テストは脱落検知を証明していない

ID 単独行は `$` 分岐で抽出される。[check_docs.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:521)、[check_docs.py:1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1012) source は次の一手、sink は直後 entry 全体と見送り台帳であり、欠落時は finding になる。[check_docs.py:1464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1464)、[check_docs.py:1489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1489)

具体入力:

```text
entry (1) 次の一手: - [T-001]
entry (2): [T-001] なし、別の通常 ID は存在
見送り台帳: [T-001] なし
```

現行コードは赤にする。よって保存則の実効性低下は現時点では反証された。

ただし提案 `test_backlog_guard_id_only_item_is_source_and_sink` は、source と sink の双方が抽出されない変異でも fixture 次第で緑になりうる。[s2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/s2-plan.md:128) `(?=$|[ \t])` を `(?=[ \t])` にする変異に対し、既存 drop テストは本文付き source なので生き残る。[test_check_docs.py:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_check_docs.py:760) ID 単独 source を次 entry から落とし、具体的な D70 finding を要求する負例を別に置くべきである。

**成果物影響:** この変異を kill できないと、ID 単独タスクが source から蒸発し、台帳の active ID が無警告で減る。

### 5. [P2] 混在・rotation・変異 fixture の帰属条件が不足

- 旧形式は提案 regex の旧分岐で byte-exact に維持できる。
- 新旧を同一 entry 内で別 ID に使う処理も、各 item ごとの `fullmatch` なので静的には成立する。ただし提案 test 名は entry 間 chain とも読めるため、同一 entry 混在を明示すべきである。
- archive は resolver 前に `worklog-*.md` 99 ファイルを読むため、P1′の明示 ordinal なら跨げる。[spool_fold.py:1723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1723)
- rotation は全 fragment 描画後に一度だけ行う。[spool_fold.py:1849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1849) したがって `rotation_between_two_new_entries` が初回 plan の bytes だけを見るなら、compact parser を削除しても kill しない。apply 後の第2 foldで元実体 digestを使った更新まで必要である。
- ordinal-gap テストは `current latest=(5)`, `archive max=(9)`, `new=(10)` として `(5)` を要求しなければならない。単に `(3),(4)` を欠番にして `(5)→(6)` とする fixture では `ordinal - 1` 変異が生存する。

同一 fold についても、第1 fragmentで本文を更新、第2 fragmentでcarry、apply・再読後に更新本文の digest が通る形が最も強い。[spool_fold.py:1797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1797)

**成果物影響:** fixture を強めない場合、gap・archive・連続 fold で旧本文へ巻き戻る実装が land し、台帳の `base` 受理値が変わる。

### 6. [P2] 実測値には広い grep と rotation 比率の混同がある

[brief.md:9](/work/1/SFC/tanab/dev-wave-jobs/token-economy/brief.md:9)、[brief.md:42](/work/1/SFC/tanab/dev-wave-jobs/token-economy/brief.md:42)、[s2-plan.md:152](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/s2-plan.md:152)

| 対象 | 静的全数 |
|---|---:|
| 現行 exact carry | 1,671 行 / 63,498 bytes |
| 現行 `変わらず` 部分一致 | 1,673 行 / 63,764 bytes |
| archive exact carry | 21,964 行 / 830,541 bytes |
| archive `変わらず` 部分一致 | 24,887 行 / 1,061,487 bytes |
| archive 全体 | 99 files / 46,488 行 / 2,975,578 bytes |

したがって親の archive 値は exact carry でも archive 全体でもなく、本文・旧形式を含む部分一致である。P1 の最新 237 行削減は 6,399 でなく **6,636 bytes**、P1′は **5,214 bytes**で段 2 の再計算どおり。

末尾 entry は見出しから 15,167 bytesで、P1′化後は約9,953 bytes。entry 全体に対する比は約1.52倍であり、「rotation が約2.5倍頻繁」は導出できない。2.38倍は carry 部分だけの `9,006/3,792` である。15,168との差1 byteは直前区切り LFを含めるかの nit。

**成果物影響:** 補正しない場合、certified 選択・台帳値は不変だが、節約量とrotation効果を報告する値が過大になり、最適化成果レポートを誤らせる。

scope 外の未消化237件整理・archive遡及圧縮・D70本体変更は、今回混ぜない判断でよい。例外は上記 `rulings` consumer だけである。

pytest、`check_docs.py` は実行しておらず、緑は主張しない。静的読取と全数計数のみ。