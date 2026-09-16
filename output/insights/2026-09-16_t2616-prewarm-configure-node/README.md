# [T-2616] prewarm を collection 前へ — 実測と、恒真になりかけた gate (2026-09-16)

wave `dev-wave-t2616-prewarm-configure-node`。依頼は「receipt memo の prewarm の起動を
`pytest_configure_node` (collection 前) へ移し、barrier を外す」。

## 結論 (最初に読む)

**受入全走が緑で通り、最遅 shard の pytest session wall は 289.1 秒だった。**
ただし **n=1 であり、同時刻の対照が無いので効果の因果は主張しない。**

| shard | pytest session wall (junit) | job Elapse | errors | failures |
|---|---|---|---|---|
| 0 | **289.103 秒** | 305 秒 | 0 | 0 |
| 1 | 227.654 秒 | 245 秒 | 0 | 0 |
| 2 | 273.059 秒 | 288 秒 | 0 | 0 |

受領証 (attempt 11): `verdict=child-green` / `red_nodeids=[]` / `flake_nodeids=[]` /
`tested_main=119895f5f18d0e3fcd396747da8eb4d7896c50a9` /
`tested_tip=365981846996298a93c54b9fee0a9b12c431ba5d` / `effective_scheduler=loadgroup`。
shard session root は `/work/1/SFC/tanab/.izanagi-acceptance-shards/97d66e1b04eb275fc5cc83580e0709b2`。

**因果を主張しない理由。** 前 wave 自身が「親は当初『438.5 秒 → 361.9 秒』と報告したが、これは
撤回した。単一走どうしの比較で効果を主張してはならない」と記録している。本 wave の 289.1 秒も
1 走であり、旧 91 走の対照とは実行窓が違う。**記録するのは「この走行の最遅 shard wall は
289.1 秒で、新規赤は 0 件だった」という事実だけ**である。

## 1. 設計が縮んだ理由 — 待ちは元から在った

`orchestrator/tests/real_repo_receipt_memo.py` の `_ReceiptMemo.prewarm` は、`write_once()` を
`self._locked(...)` の**内側**で実行し、その中で production resolver を呼ぶ。したがって
**cache の flock は解決の全所要 (前 wave の実測 28.328 秒) のあいだ保持される。**
reader 側の `read_existing()` も同じ `_locked(...)` の中にあり、`_locked` は blocking な
`fcntl.flock(LOCK_EX)` を取る。

**つまりプロセス跨ぎの待ちは元から実装されていた。** 欠けていたのは 1 点だけである —
reader が writer より先に lock を取ると `path.exists()` が偽で即 `cache-missing` になる。
早期起動では `pytest_configure_node` の直後に worker が走り出すので、この競走が実際に起きる。

足したのは「**早期 job が `workerinput` で明示されたときだけ**、本体不在で即赤にせず期限まで
retry する」であり、待ち機構の作り直しではない。依頼文の「worker 側は cache を最大 120 秒待ち
`.pending` / `.failed` marker で失敗を共有する」は、この 1 点のための記述だったと読み直した。

## 2. 恒真になりかけた gate (本 wave の最重要)

段 3 の相談 A が、実装前に次を指摘した。

> 既存 probe は「prewarm が collection 前だったこと」を検査していない。
> 「早期起動を削って collection 後の同期 barrier へ戻す」変異は既存 probe を素通りする。

段 4 はこれを受けて「新しい検査はこの変異を落とさなければならない」と定め、変異 M3 として
事前登録した。**本走で M3 は KILLED になり、`test_early_memo_starts_before_worker_collection_notification`
ほか 4 本が落とした。** 恒真性の穴が実際に塞がっていることを実走で示せた。

### さらに悪い形を段 6 が見つけた

除外する narrowing の destination 名が pytest の実 parser と食い違っていた。
`--ff` の destination は `ff` ではなく `failedfirst`、`--sw` / `--sw-skip`
(`stepwise` / `stepwise_skip`) と `-o` (`override_ini`) は列挙自体が無かった。

**そして同じ wave が追加した test も同じ誤名 (`("ff", True)`) を使っていた。**
述語を、その述語が生成した候補集合で検査していたので、列挙の誤りは構造的に検出できない。
放置すると `--ff` や `-o python_files=...` 付きの焦点走で早期 prewarm が発火し、
D518 が却下した「無条件 prewarm」が焦点走へ漏れる。

閉じ方は、実 `Parser` へ plugin の `addoption` を登録して destination を照合する対照 test と、
**独立した CLI 入力による検査**の 2 本立てにした。前者が綴り誤りを、後者が列挙漏れを落とす。

## 3. 前 wave の (b) の機序を変異で実測再現した

前 wave は「`_izanagi_acceptance_shard_spec` で閉じると、probe の入れ子 xdist 走行で worker が
crash する (赤 2 件)」と記録していた。本 wave の変異 M1
(`pytest_configure_node` の冒頭で早期 return) を当てると、

```
pytest.UsageError: xdist workerinput に acceptance ledger snapshot が無い
[gw238] node down: ...
```

で worker が落ちる。冒頭 return が nonce と所要台帳の `workerinput` 伝播ごと飛ばすためである。
**session ごと落ちて FAILED 行が 1 本も出ない**ので `DW-M08` が要求する期待 node の完全集合を
作れず、M1 は matrix から外して session 単位の fail-closed 実証として別枠に記録した。
記録は `mutation-probe-ledger` (親 job dir) の
`injection_diff_sha256 = dc7e05743f7542d3420eec8b726eb424ff97ba3e06e915d5ab0e63fc3ee046b2`。

**locus は外側 session なので、前 wave の記述と同型の機序であって同定ではない。**

## 4. 親自身の読解が 1 件誤っていた

親は段 1 で「`DSession.pytest_sessionstart` は `-p` で載る plugin の `pytest_sessionstart` より
先に走るので、prewarm を `pytest_configure_node` へ移すと FakeMemo の差し替えが間に合わない」と
書いた。**これは誤りである。** `xdist/dsession.py` の当該 hook には `@pytest.hookimpl(trylast=True)`
が付いており、pluggy は trylast の impl を list 先頭へ挿入して `reversed()` で回すので
**trylast は最後に呼ばれる**。段 3 の相談 A が反証し、親が現物で追認して撤回し、
子へ渡した射影 file も訂正した。逐語は `verbatim/parent-probe-findings.md` の項 4。

## 5. 変異 matrix

baseline PASSED・**6/6 KILLED**・SURVIVED 0・MISMATCH 0・期待 node 完全一致・anchor 全件一意。
spec は `mutation-spec-final.json` (sha256
`0fe24ccfc90dae280882000096ea84d671107a2a6a0b599ade64f0fba3e82897`)、台帳は
`mutation-final-ledger.json`。runner argv は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_real_repo_serialization.py
orchestrator/tests/test_p3_s4_loop.py -q -rf` で、**F982 を避けるため `test_p3_s4_loop.py` を
必ず含める**。

| 変異 | 内容 | 落とした node |
|---|---|---|
| M2 | timeout で worker が resolver を呼ぶ | `test_receipt_memo_module_identity_and_resolver_caller_are_fixed` (**既存 test**) |
| M3 | 早期起動を削り collection 後 barrier へ戻す | `test_early_memo_starts_before_worker_collection_notification` ほか計 4 本 |
| M4 | `keyword` narrowing を外す | `test_early_memo_parsed_narrowing_keeps_nonce_and_never_resolves` ほか 1 本 |
| M5 | `.failed` 優先を外す | `test_early_memo_publication_wait_is_explicit_bounded_and_fail_closed` ほか計 3 本 |
| M6 | I/O 後の deadline 再確認を外す | `test_early_memo_success_checks_shared_deadline_after_io` |
| M7 | 未通知 miss も待つ | `test_early_memo_publication_wait_is_explicit_bounded_and_fail_closed` |

**M2 を落としたのが既存 test だった**ことは、「worker が production resolver を呼ばない」という
規律 2 の核心が本 wave より前から gate に守られていることの裏取りになる。

## 6. 踏んだ既知の障害

- **F982** (選択形固有の偽赤)。`test_real_repo_writers_do_not_materialize_oracle_environment_candidates`
  が単独 file 走で決定的に赤。`test_p3_s4_loop.py` を選択へ足すと緑 (503 → fix 後 505 passed)。
  commit 前後の両方で再現し、未 commit 由来の drift ではないと切り分けた。
- **F945** (t1259 の Git 走査 30 秒 timeout)。受入 attempt 2 で **28 件**。直近の再発と件数まで同じ。
  単独再走 51 passed / 15.92 秒 / rc=0 で非再現。
- **[T-2622] dispatch job exit hang**。3 shard とも junit.xml を書き終えた後、job `888.nqsv` が
  Elapse 3528 秒 / CPU 0.25 秒で終了せず wrapper が `do_wait` で停止。さらにその job が
  **orphan hold** を残し、後続 6 回の受入投入が
  `preclaim-history-provenance rc=70 source_rc=16` で弾かれた。walltime で job が消えるまで待った。
- **受入 attempt 1 の postcheck 競走**。claim 時 main `d70bffd88` → postcheck 時 `95cf1caa5`。
  子 log 不在・`raw_child_rc=null` で**テストは 1 本も走っておらず赤ではない**。

## 7. この dir の中身

- `mutation-spec-final.json` / `mutation-final-ledger.json` — 変異 matrix の事前登録と台帳。
- `verbatim/parent-probe-findings.md` — 親が現物確認・実測した事実と、撤回した読解 (項 4)。
- `verbatim/s2-plan.md` — 段 2 plan (親の前提を 2 件反証した)。
- `verbatim/s3-consult-a-nested-and-fire-condition.md` — 入れ子走行の全列挙と発火条件の攻撃。
- `verbatim/s3-consult-b-correctness-barrier.md` — 正しさ防壁・受理集合の攻撃。
- `verbatim/s4-ruling.md` — 親の段 4 裁定 (R1〜R11)。
- `verbatim/s6-review-a.md` / `verbatim/s6-review-b.md` — 段 6 の敵対レビュー 2 本。
