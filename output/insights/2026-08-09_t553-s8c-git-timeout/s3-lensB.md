指定された 6 ファイルはすべて可読でした。変更・pytest は実行していません。baseline の赤を緑とは報告しません。

## 所見

### B-01 — 受理集合不変の主張と修正目的が矛盾

- 判定: real
- 重大度: blocker
- 根拠: [s1-brief.md:60-63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief.md:60)、[acceptance-baseline.txt:185-221](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/acceptance-baseline.txt:185)、[s2-plan.md:248-250](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:248)
- 現在の同じ candidate は `git-timeout` で reject されている。chunking によりそれが通れば、文字どおり受理集合が拡大し、同じ reason code も維持できない。plan 自身もこの矛盾を認めている。
- 成果物影響: `FreezeValidation` が失敗から成功へ変わり、`freeze_reason_code`、`effective`、段 8c 発効可否が変化する。

これは「資源枯渇による拒否を意味論的 reject と別扱いする」という親裁定が必要で、無裁定のまま GO にはできない。

### B-02 — chunk 境界で framing reason code が変わる

- 判定: real
- 重大度: high
- 根拠: [s2-plan.md:86-87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:86)、[s2-plan.md:151-153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:151)、[s8c_preregistration.py:1163-1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1163)
- 例えば要求 `oid1, oid2` に対し、旧 single invocation が

  ```text
  oid1 blob 0\n\n
  oid2 blob 0\n\n
  JUNK
  ```

  を返すと、旧 parser は `cat-file-extra` になる。
- chunk ごとに subprocess が `JUNK` を末尾へ付加すると、連結後は `oid1` の record と `oid2` の header の間に `JUNK` が入り、`cat-file-header` になる。
- header の末尾欠落でも、次 chunk の header と連結されて `cat-file-truncated` が `cat-file-header` 等へ変わり得る。単純な `b"".join()` は「旧 single invocation の EOF」を再現しない。

- 成果物影響: reject 自体が続いても `freeze_reason_code` と CLI/report の値が変わり、consumer 分岐および report digest が変化する。

chunk ごとの framing を検査して canonical な reason code へ写像するテストが必要である。

### B-03 — Git subprocess の失敗機会が増える

- 判定: real
- 重大度: high
- 根拠: [s2-plan.md:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:144)、[s2-plan.md:240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:240)、[s8c_preregistration.py:902-906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:902)
- 旧 single call は成功するが、分割後の 2 個目の Git が一時的に非 0 exit/OSError になる入力では、変更後だけ `git-failed` になる。
- 「どの chunk の失敗も同じ code」は、旧成功入力の受理を維持する保証ではない。

- 成果物影響: 旧来 valid だった freeze が `git-failed` で `effective=False` になり、受入全走が赤になる。

### B-04 — `_git(deadline=None)` が operation 締切の opt-out seam になる

- 判定: real
- 重大度: high
- 根拠: [s2-plan.md:50-66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:50)、[s8c_preregistration.py:880-901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:880)
- `None` 自体は per-call 15 秒へ戻るが、将来 caller が `time.monotonic()+10**9` を渡せば、各 call は 15 秒でも operation 全体の共有締切を実質消せる。
- 「省略時は安全」という default だけでは、将来の明示 caller による guard opt-out を防げない。

安全な形は `_git` の signature を変えず、内部専用 runner を分けること。

```python
def _git(root, args, *, stdin=None):
    return _git_run(root, args, stdin=stdin, timeout=GIT_TIMEOUT_SECONDS)

def _git_run(root, args, *, stdin=None, timeout):
    # timeout は必須。default なし
```

`_git_chunked` だけが期限計算済みの `timeout` を渡す。

- 成果物影響: 将来の caller が履歴長に比例した無制限実行を選べ、従来 reject される入力が発効・producer 到達する。

### B-05 — `MAX_GIT_INPUT_BYTES` の per-chunk 検査は発火不能

- 判定: real
- 重大度: medium
- 根拠: [s2-plan.md:24-26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:24)、[s2-plan.md:32-36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:32)、[s8c_preregistration.py:881-882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:881)
- helper は全 input bytes を先に合計する。したがって、ある chunk が 16 MiB を超えるなら全体も必ず超え、chunk loop に入る前に reject される。
- per-chunk の `MAX_GIT_INPUT_BYTES` は、chunked path では一度も発火しない。残るのは direct `_git` の既存 seam だけである。

- 成果物影響: 直ちには値は変わらないが、「per-chunk 検査を維持した」という保証は恒真で、当該検査の純増検出力はゼロである。

### B-06 — `_batch_blob_bytes` の request 数上限を追加しない判断

- 判定: refuted（受理集合について）
- 重大度: なし
- 根拠: 現行 [s8c_preregistration.py:1133-1141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1133) に `MAX_BATCH_REQUESTS` 検査はなく、plan も [s2-plan.md:130-134](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:130) で追加しないとしている。
- ここへ新しい `batch-request-limit` を足せば、既存 direct private caller の受理集合を縮めるため、受理集合不変という主張には反する。

ただし残余リスクは real である。16 MiB の input cap は OID 行数を直接制限せず、数十万行規模を許す。`tuple(dict.fromkeys(oids))` も先に全 materialize される。

- 成果物影響: 巨大な direct caller は多数の Git subprocess を発生させ、`git-timeout` により発効判定・受入全走を赤にし得る。

### B-07 — 未分割の Git 呼び出しが残り、受入赤を閉じる保証がない

- 判定: real
- 重大度: blocker
- 根拠: [s2-plan.md:240-242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:240)、[s8c_preregistration.py:1063-1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1063)、[acceptance-baseline.txt:185-221](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/acceptance-baseline.txt:185)
- `_commit_graph`、`_history_namespace_paths` は単一 15 秒 call のままである。現在の赤を `_batch_oids` 以外へ移すだけになる可能性がある。
- chunk 4 process 化が実際に速くなる証拠もなく、plan 自身が process 起動・pack 読み直しで遅くなる可能性を認めている。

- 成果物影響: `validate_condition_freeze_at` が依然 `git-timeout` で失敗し、`effective=False`、候補 invariant と受入全走が赤のまま残る。

### B-08 — 親 brief の DW-O09/DW-O10 不成立宣言は誤り

- 判定: real
- 重大度: blocker
- 根拠: brief の宣言 [s1-brief.md:64-65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief.md:64)、validator の caller [s8c_preregistration.py:1686-1690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1686)、write path [s8c_preregistration.py:1713-1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1713)
- `prepare_revision` は既存 generation がある場合、変更対象の `validate_condition_freeze_at` を line 1688 で呼ぶ。その成功後に `gN.json` を exclusive-create し、bytes を write する。
- したがって変更は producer の write path に到達する。旧 `git-timeout` が新実装で通れば、旧来作成されなかった generation が作成され得る。

- 成果物影響: `output/s8c-preregistration/condition-freeze/*.json` の namespace・tip bytes・generation が変わり、DW-O09/O10 の pin/producer 棚卸しが必要になる。

### B-09 — テスト (a) は baseline との受理集合比較になっていない

- 判定: real
- 重大度: high
- 根拠: [s2-plan.md:161-164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:161)、現行の Git seam [test_s8c_preregistration_core.py:1025-1053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_core.py:1025)
- 「単一幅」は旧実装ではなく、新 helper を一度だけ呼ぶケースである。成功する OID/blob mapping の値と順序しか比較せず、reject reason を比較しない。
- 例えば chunk 途中の余剰 bytes を `cat-file-extra` ではなく `cat-file-header` とする変異は、valid fixture をすべて通過できる。

- 成果物影響: 不正 framing の reject は継続しても reason code が変わり、`freeze_reason_code` と report digest が変わる。

### B-10 — 集計 mutation の一部はテストで殺せる

- 判定: refuted
- 重大度: なし
- 根拠: [s2-plan.md:165-169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:165)
- input 合計、request 合計、output 合計を「各 chunk は上限内・全体は超過」で作るため、次の mutation は検出できる。

  - input 判定を per-chunk に戻す
  - `MAX_BATCH_REQUESTS` を chunk 内でリセットする
  - `MAX_GIT_OUTPUT_BYTES` を chunk 内でリセットする

- 成果物影響: これらの mutation を残した場合は過大入力・過大出力を通し得るが、計画されたテストなら reject を検出できる。

### B-11 — blob size 合計と phase 間集計の被覆が不足

- 判定: real
- 重大度: medium
- 根拠: [s2-plan.md:131-132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:131)、既存テスト [test_s8c_preregistration_core.py:1036-1053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_core.py:1036)
- 既存の total blob test は `_git_text` 自体を monkeypatch しており、新しい `stdin_lines` → chunk helper 経路を通らない。
- size phase の各 chunk は `MAX_TOTAL_BLOB_BYTES` 未満だが、全 chunk の合計だけ超える fixture がない。
- size phase と blob phase を誤って一つの output accumulator に統合する mutation も、各 phase 単独が上限内で合計だけ超える fixtureがないため検出できない。

- 成果物影響: 本来 `blob-total-byte-limit` で reject される OID 集合が blob read まで進み、freeze validation の受理集合が拡大し得る。

### B-12 — deadline reset mutation 自体はテストで殺せる

- 判定: refuted
- 重大度: なし
- 根拠: [s2-plan.md:168-169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:168)
- fake clock で各 chunk を 6 秒進め、3 chunk 合計 18 秒にするため、chunk ごとに締切を再生成する mutation は失敗する。
- per-call の `min(15, remaining)` も別テストで検出対象になっている。

- 成果物影響: この mutation を残せば旧来 15 秒だった operation が最大 N×15 秒になるが、計画テストは検出できる。

### B-13 — (c) は production default の chunk 幅と実 subprocess を検査しない

- 判定: real
- 重大度: high
- 根拠: [s2-plan.md:163-169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:163)、受入経路 [test_s8c_preregistration_invariant.py:124-158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:124)
- 計画テストは幅を monkeypatch して `2` または `1` にする。従って production 定数を `1` に変える mutation は検出されない。3 request の fake clock は、実際の 50,000 subprocess 起動コストを表さない。
- `MAX_GIT_BATCH_REQUESTS_PER_CALL = 1` なら、同じ 15 秒締切でも数万 process 起動で受入が赤になる可能性がある。

- 成果物影響: `git-timeout`、`git-failed`、または全走 timeout により発効判定と acceptance が赤になる。

### B-14 — 代案 B は、テストの性質だけを基準にすれば規律 2 違反ではない

- 判定: refuted
- 重大度: なし（ただし条件付き）
- 根拠: invariant test は [test_s8c_preregistration_invariant.py:125-158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:125) で generation chain、hash、record 内容を断言しており、15 秒以内であることを断言していない。
- よって production default を変えず、テストだけ `timeout=180` を明示するのは「別の性質を甘くした」ことにはならず、fixture hardening と判定する。
- production の default 経路は、CLI check [s8c_preregistration.py:1803-1808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1803)、`activation_report_at` [s8c_preregistration.py:1547-1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1547)、`effective_at` [s8c_preregistration.py:1614-1619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1614)、`prepare_revision` [s8c_preregistration.py:1688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1688) が省略時 default を使う。

- 成果物影響: production caller の default 値を維持すれば既存 production の発効値は変わらない。ただし test は production 15 秒性能を証明しなくなる。

### B-15 — 代案 B の無制限 timeout は別の opt-out

- 判定: real
- 重大度: high
- 根拠: 現行 validator は [s8c_preregistration.py:1310-1317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1310) に timeout 引数を持たず、既存 consumer は上記の default 経路を使う。
- `timeout=10**9` を止める型・runtime 上限・caller guard は、代案に上限を追加しない限り存在しない。
- したがって「default は 15 秒だから防壁不変」とは言えず、API を呼ぶ将来 caller は明示的に防壁を外せる。

- 成果物影響: 長時間 Git 処理が `git-timeout` にならず、従来 reject される candidate が validation・activation・producer write へ進む。

代案 B を採るなら、production validator へ timeout を露出せず test-only private seam にするか、少なくとも有限・明示上限を設ける必要がある。

## §4 reason code の判定

| reason code | 判定 | 重大度 | 根拠 | 成果物影響 |
|---|---|---:|---|---|
| `batch-request-limit` | refuted | なし | plan:74-78、production:1105-1108 | 旧 reject/code を維持 |
| `git-input-limit` | refuted（aggregate） | なし | plan:24-26、production:881-882 | 旧 reject/code を維持 |
| `git-timeout` | real | blocker | plan:28-41,248-250 | valid/effective が変化し得る |
| `git-output-limit` | refuted（意図された累積実装） | なし | plan:36-39、production:895-897 | 旧 reject/code を維持 |
| `git-failed` | real | high | plan:144,240、production:902-906 | 旧 success が `git-failed` reject になり得る |
| `git-output-utf8` | refuted | なし | plan:145、production:909-913 | 連結後 decode なら同じ |
| `cat-file-count` | refuted（正常 framing） | なし | plan:146、production:1114-1116 | 同じ count reject |
| `cat-file-header` | real（異常 framing） | high | plan:147,151-153、production:1167-1169 | `truncated/extra` と code が入れ替わる |
| `path-not-blob` | refuted（正常 framing） | なし | plan:148、production:1120-1129 | 同じ reject |
| `blob-byte-limit` | refuted | なし | plan:149、production:1124-1126,1153-1155 | 同じ reject |
| `blob-total-byte-limit` | 実装案は refuted、テスト被覆は real gap | medium | plan:150、test:1036-1053 | mutation 次第で受理拡大 |
| `cat-file-truncated` | real | high | plan:151、production:1164-1166 | code が `header/size` に変わり得る |
| `cat-file-size` | real | high | plan:152、production:1171-1174 | code が `header` または受理へ変わり得る |
| `cat-file-extra` | real | high | plan:153、production:1177-1178 | `header` へ変わり得る |

## 総括

(i) 判定: **NO-GO**

(ii) must-fix:

- literal な受理集合不変と、現在の `git-timeout` を通す目的の衝突を親が裁定する。
- `_git` の optional `deadline` seam を廃止する。
- chunk 境界の framing を検査し、`cat-file-*` reason code を保存する。
- `prepare_revision` 経由の DW-O09/DW-O10 を再評価する。
- 未分割の `_commit_graph` / `_history_namespace_paths` が残る状態で、受入赤を閉じたと主張しない。
- テストに旧実装相当の oracle、reject reason 同一性、production default width、blob total cross-chunk、default production path の検査を追加する。

(iii) 親が裁定すべき択一:

- `git-timeout` を意味論的 reject として受理集合不変に含めるか、環境依存の false reject として例外扱いするか。
- F57 に従い test fixture hardening を採るか、production chunking を scope として維持するか。
- operation 締切を厳密に旧 15 秒へ固定するか。
- `_batch_blob_bytes` direct private caller に request 上限を追加するか。
- framing 異常を chunk ごとに parse するか、conforming Git 出力だけを契約対象とするか。
- 代案 B の test-only timeout seam を採るか、production API へ timeout を出さないか。