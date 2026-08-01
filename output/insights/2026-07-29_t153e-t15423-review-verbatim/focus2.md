結論は **GO** です。指定13ファイルはすべて全文読了しました。編集、commit、pytest、runner、mutation は実行しておらず、検査緑も主張しません。

### 所有・帰属

**PASS**。静的に識別できる親の実装直編集 hunk はありません。

- 現在の実装4ファイル差分と Codex author worktree の staged 差分は、全体 SHA-256 がともに `acb19ed6a0da70cea566df9c7e46897c04c22208369a62b078471774a02759fc` で完全一致しました。
- `author.patch → fix1.patch → fix2.patch` の blob 鎖の末端は、現在の4ファイルおよび author worktree の index blob と一致します。
- author/fix1/fix2 は同じ隔離 worktree、`gpt-5.6-sol`、`reasoning=high`、`sandbox=workspace-write` で、所有は次の4ファイルに限定されています。[author-prompt.txt:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/author-prompt.txt:1) [fix2-prompt.txt:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/fix2-prompt.txt:15)
- 現在の所有外 tracked 差分は親所掌の `docs/ai-provenance.md` と `docs/decisions.md` だけです。untracked wave artifacts 内の patch も同じ4ファイルの author 差分です。

### focus1 再判定表

| ID | 判定 | 静的根拠 |
|---|---|---|
| A-1 | `closed` | parser stdout は LF byte のみで分割し、invalid UTF-8・空/colonなしrecordを例外化します。[check_ai_provenance.py:94](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:94) [同:122](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:122) |
| A-2 | `closed` | 毎回 fresh private directory、その子cwd、親ceilingを使い、system/global/env/local configを遮断します。[check_ai_provenance.py:80](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:80) [同:97](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:97) |
| A-3 | `closed` | AI-Agent は従来 parser のままです。履歴では ancestry 判定後に `check_cab` を渡すため、pre-policyへcanonical CAB意味論を遡及しません。[check_ai_provenance.py:140](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:140) [同:378](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:378) |
| A-4 | `closed` | per-commit query は `--full-history --no-renames -S`。rename、merge keep/drop、削除、複数needleの境界がコード構造と一致します。[check_ai_provenance.py:245](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:245) |
| B-1 | `closed` | canonical parser はCAB専用。scope/Codex-authorも引き続き legacy `_ai_agent_values()` を使用します。[check_ai_provenance.py:165](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:165) [同:280](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:280) |
| B-2 | `closed` | M1 control は base/scoped空、CAB findingのみ非空を固定し、`--no-divider` 有無のCAB受理差を単独化しています。[test_check_ai_provenance.py:291](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:291) |
| B-3 | `closed` | hostile ancestorの有効aliasを使い、fresh cwd/ceiling配線とCAB件数相殺を直接攻撃します。[test_check_ai_provenance.py:323](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:323) |
| B-4 | `closed` | test-local独立literalから履歴を作り、production定数・実policyとの一致を別assertしています。[test_check_ai_provenance.py:16](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:16) [同:539](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:539) |
| B-5 | `closed` | policy導入commit自身を単独rangeにし、そのsplit CABをrc=1とする境界があります。[test_check_ai_provenance.py:628](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:628) |
| B-6 | `closed` | raw grammarは列頭候補を数え、backtick/tilde fence内候補を各々拒否側へ固定しています。[test_check_ai_provenance.py:202](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:202) |
| R-1 | `closed` | `_has_co_authored_by_policy()`が先行し、falseならPythonの条件式により `_co_authored_by_findings()` 自体を呼びません。[check_ai_provenance.py:174](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:174) [同:378](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:378) |

`partial`、`regressed` は0件です。

### R-1・適用集合・finding合流

Pre-policyでは以下が成立します。

- `_co_authored_by_findings()`を呼ばないため、raw regexの`findall`、canonical parser、temporary directory作成のいずれも実行されません。
- `_ai_agent_values()`は常に先に実行されます。
- scope finding生成とepoch適用、implementation-author検査も従来分岐のまま残っています。[check_ai_provenance.py:174](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:174) [同:383](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:383)

D98のper-commit集合とも一致します。

| commit状態 | `_has_co_authored_by_policy` | CAB gate |
|---|---:|---|
| 導入changeを祖先に持たない | false | OFF |
| policy導入commit自身 | true | ON |
| 導入後 | true | ON |
| needle削除commit・削除後 | true | ON |
| needle再追加commit・再追加後 | true | ON |

削除も再追加も `-S` changeとして履歴に残り、過去の導入changeも祖先に残るため、適用済み状態は解除されません。別lineageは各commit自身の祖先だけで独立判定されます。[D98:4358](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4358)

`check_cab` 分岐にも加算異常はありません。

- `cab_findings`は早期returnを含む全経路で保持。
- historyはbaseを1回、scopeをepoch条件で1回、CABを1回だけ加算。
- message-fileもbase/scope/CAB/implementationを各1回だけ合流。
- AI format、scope、CABの同時findingも直接固定されています。[test_check_ai_provenance.py:247](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:247)

### `--message-file` と新規3 test

`--message-file` はancestryを参照せず、既定の `check_cab=True` で常時CAB parserへ進みます。読み取りやlegacy parserが先に異常終了した場合も受理せずrc=2です。CAB parserのRuntimeError/OSError/UnicodeErrorもmainでrc=2になります。[check_ai_provenance.py:358](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:358) [同:394](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:394)

新規3 testはいずれもCLI境界を固定しています。

- pre-policy: 実git履歴と実ancestry判定を通し、parser seamを「呼ばれたらAssertionError」にしてcall count 0・rc=0を固定。[test_check_ai_provenance.py:583](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:583)
- post-policy: test-local独立needleで導入commitを作り、そのcommit単独rangeでparser failure、call count 1、rc=2を固定。[同:605](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:605)
- message-file: policy履歴なしの実ファイル入力からcall count 1、rc=2を固定。[同:883](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:883)

mockは異常注入対象のparser leafだけで、argparse、main、history/message-file routing、policy判定、rc変換はproductionを通ります。production定数由来の恒真でも、routing全体を置換する過剰mockでもありません。

### コスト評価と新規所見

このwave以前から存在するコストは、default 495 commitの全履歴列挙、commitごとのsubject/message取得、legacy AI parser、scope/implementation epoch用の単発`git log -S`です。全体は概ね線形でした。

今回の追加は次の2点です。

- 全commitごとの `git log --full-history --no-renames -S`。深さを \(H_i\) とすると合計は \(O(\sum H_i)\)、線形履歴の最悪は \(O(N^2)\)。現snapshotでは495本の追加Git subprocessになります。
- CAB適用commitごとのfresh directory＋canonical Git parser＋raw scan。これはpost-policy commit数を \(K\) として \(O(K)\)。needleはまだ未commitなので現HEADではK=0、同一commitでland直後は導入commitの1件から始まります。

新規 correctness findingは0件です。性能面だけをbacklogへ分離します。

- **ID:** BL-PERF-1
- **severity:** LOW / backlog
- **real/refuted:** 漸近コストはreal、現wave blockerはrefuted
- **path:line:** [check_ai_provenance.py:245](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:245)、[同:374](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:374)
- **具体的成果物影響:** 現時点でなし。静的情報だけではtimeout、受入不能、provenance台帳の誤受理・誤拒否を示せません。
- **最小fix:** 将来実測で問題化した場合、対象tip群への1回の`-S`走査でchange commit集合を得て、parent graph上で「祖先にchangeあり」を伝播・cacheする。受理集合は現境界表で維持する。

### 9,000-byte・registry・D96

- policy実体は **8,832 / 9,000 bytes**。
- `PROVENANCE_LIMITS`は独立registryで、唯一のbudget consumer集合へ合流しています。[check_docs.py:162](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:162) [同:1466](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:1466)
- dispatch allowlistは`REFERENCE_LIMITS`と`SELF_LIMITS`だけで、provenance pathは未追加です。[check_docs.py:231](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:231)
- 9,000 exact / 9,001 rejectは、コピーしたproduction checkerをCLI実行する合成repo境界で固定され、production定数だけの恒真ではありません。[test_check_docs.py:417](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:417)
- D96が要求する新Dと境界testは、現在の同一未commit変更集合にD98・checker・policy・両testとして揃っています。[D96:4271](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4271) [D98:4335](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4335)  
  まだcommit前なので、land時にもこの6 trackedファイルを分割しないことが必要です。

## 総括

**GO。** focus1のA-1〜A-4、B-1〜B-6、R-1はすべて静的に`closed`、`partial`・`regressed`はありません。fix2はpre-policyからcanonical CAB parser・temporary directory・raw grammarを除外しつつ、legacy AI/scope/implementation検査を維持しています。D98の導入・削除・再追加を含むper-commit集合、message-fileの常時適用とrc=2、finding合流、新規3 CLI test、9,000-byte独立registry、dispatch非拡張、D96同一変更も整合しています。残る二次的コストは成果物影響未立証のbacklogであり、このfocused reviewのNO-GO理由にはなりません。