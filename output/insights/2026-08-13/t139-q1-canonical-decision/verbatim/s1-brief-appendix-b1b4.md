# 段 1 brief 付録 — B1〜B4 の逐語根拠 (親が承認済み文書を直接読んで確認した)

**これは親の実測であり、段 3 の攻撃対象である。** 逐語の読み違い・過度な一般化を疑ってよい。

出典 = `output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md` (D282 で exact bytes 承認済み)
および同 dir の `receipt-schema-v1.json` (43,106 bytes、同じく承認済み)。

## B1 — これは「不足」ではなく**承認済み文書内の矛盾**である

親は、パッケージが「raw pointer の欠落」と分類した B1 を、より強い形で読み直した。

**§6.3 (`record-items-v2.md:600-611`) の逐語:**

> **申告値を単独で信用しない** — validator は次の 3 者を再読して一致を要求する。
> 1. `configure_argv[]` 中の `-DCCBENCH_TRACE=` / `-DCCBENCH_ADD_ANALYSIS=` (または同等の macro 定義)、
> 2. `compile_commands` 実体に現れる当該 TU の compile argv、
> 3. `cmake_cache` の申告値 (`CMakeCache.txt` 由来)。

**§7.1 (12) (`record-items-v2.md:775`) の逐語:**

> (12) 申告値と実体の 3 者一致 (§6.3 の argv macro / compile_commands / CMakeCache)

**§8 (`record-items-v2.md:784-799`) の逐語 (否定検査の列挙):**

> 消費側が次のいずれかを**受理条件の入力**に使ったら落ちるテストを置く。prose の禁止だけにしない。
> …
> `arms.*.compile.trace_enabled / analysis_enabled / cmake_cache`
> …
> いずれも producer が書く申告値であり、受理は validator の再計算だけが決める。

**schema 側の実測:** `performanceCompileStock.required` は
`[source, mode_macro, configure_argv, translation_units, identity_sha256, trace_enabled,
analysis_enabled, cmake_cache, compile_commands]` を持つ。このうち `cmake_cache` が指す
`performanceCmakeCache` は `required = [trace, add_analysis]` の **2 boolean だけの値 object** で、
`fileRecord` ではない。`cmake_cache_raw` という key は schema 全体で **0 件**。

**したがって矛盾は次の形をとる。**

- §7.1(12) は 3 者目 (CMakeCache) の再読を validator の必須責務と定める。
- しかし schema が持つ CMakeCache 由来の値は `arms.*.compile.cmake_cache` **だけ**である。
- §8 はその field を受理条件の入力に使うことを**明示的に禁じ、落ちるテストを要求する**。

**使ってよい唯一の入力が、使ってはならないと名指しされている。** これは「後で足せばよい欠落」では
なく、承認済み 2 文書が同時には満たせない条件を課している状態である。
decision はこの形で書く必要がある — 「raw pointer を足す」だけでは、§8 の否定検査と
§7.1(12) のどちらを優先するかが依然として定まらない。

## B2 — 欠けているのは「母集合の authority」であって、`intent_ref` そのものではない

**§4.13 (`record-items-v2.md:450-477`) の逐語:**

> `intent_ref  fileRecord   qsub より前に書いた durable submission intent`
> **`intent_ref` は create-only で書かれた durable submission intent を指す** — qsub より**前**に
> 書き、以後上書きしない。validator は同一 path の内容が attempt 間で変化していないことを要求する。
> **`attempts[]` は durable intent の全 attempt を exact に被覆する (部分被覆を許さない)。**

**§6.1 (`record-items-v2.md:583-584`) の逐語:**

> `attempts[]` は durable submission intent の全 attempt を **exact に被覆**する。
> qsub が失敗した attempt も **row を省略できない**。

**schema 側の実測:** `intent_ref` は 2 件実在する (attempt ごとの `fileRecord`)。

**欠けているもの:** 受領証は producer が**列挙することにした** attempt しか含まない。
「全 attempt を exact に被覆した」ことを検査するには、受領証の**外**に母集合の権威
(canonical namespace + `O_EXCL` の発行履歴) が要る。それが無い限り、producer が失敗 attempt を
1 行落とした受領証は、内部的に完全に整合したまま通る。
**§8 は `attempts[].reason_code == "completed"` と `attempts[].qsub_result.returncode` を
受理条件の入力から外しているので、落とされた行を他の申告値から推論する経路も塞がれている。**

## B3 — discovery 契約が無いので、§6.1 の stage 間整合は起動できない

**§6.1 (`record-items-v2.md:585-586`) の逐語:**

> **`allocations[]` は `allocation_role == verification` をちょうど 1 件持つ。**
> 同一 study の別 stage の受領証は、同じ `allocation_id` と同じ bytes でその 1 本を記録する。

**schema 側の実測:** `peer_receipt` = 0 件、`receipt_set` = 0 件。
1 stage 1 receipt の exact top-level しか無く、**peer receipt を誰がどう同定するか**が定まっていない。

「同じ bytes で記録する」という要求は、比較相手を取得できて初めて検査になる。
現状では validator は自分の 1 本しか見えないので、この制約は**構造的に恒真**である。

## B4 — raw pointer は実在するが、「再計算」の対象 bytes が未定義

**§4.12 (`record-items-v2.md:421-448`) の逐語:**

> `receipt        fileRecord   transcript の raw pointer`
> **producer の `pass` 申告を権威にしない。** validator は transcript を再計算する。

**§6.8 (`record-items-v2.md:677-684`) の逐語:**

> `study_stage == main_run` では昇順・重複なしの 1..13 の部分集合とし、要素数は `J` に一致する。

**schema 側の実測:** `admissionTelemetry` は
`required = [ordinal, kind, receipt, fixed_inputs, ledger_evidence]` を持ち、
`kind` の enum に `j_derivation` がある。raw pointer は**実在する**。

**欠けているもの:** transcript の canonical byte grammar (どの bytes をどう parse して何を得るか)、
その grammar の authority binding (誰が定めた grammar が権威か)、および `J` の数値実装契約。
「再計算する」と書いてあるが、**何を再計算するのかが定義されていない。**
実装者ごとに parse が変われば受理集合が動く — これは §7 の
「engine の差で受理集合が変わってはならない」に直接抵触する。

## Q2 の envelope は「新設する機構」ではなく、承認済み文書が既に要求しているものである

**これは K1 (D320 の但し書き) の判断に直接効く。**

**§7 (`record-items-v2.md:741-745`) の逐語:**

> **conformance vectors** (正例 1 本と、§6 の各制約に対する負例 1 本以上) を実装 wave が発行し、
> **その digest を approval manifest が pin する。**

**§7.1 (19) (`record-items-v2.md:782`) の逐語:**

> (19) `receipt_schema.sha256` が **approval manifest の pin** と一致すること (§4.2)

**したがって approval manifest は、本 wave が新しく思いついた bytes 級 provenance 機構ではない。**
D282 が 2026-08-11 に exact bytes 承認した文書が、その内部で 2 箇所にわたり明示的に要求している
構成要素である。D320 (2026-08-12) は「**新設・維持は既定で見送り**」と書いており、
既に承認済み文書が要求している構成要素を事後に取り消す文言は持たない
(「既存機構の撤去・緩和は個別裁定で行う」と明記している)。

**親の (P2) はこれで補強されるが、依然として攻撃対象である。**
「§7 / §7.1(19) が言う approval manifest は、D320 が見送ると言った当のものではないか」という
読みは成立しうる。その場合は実装差分ゼロの precheck としてユーザー裁定へ返す。
