結論は **GO** です。指定された13ファイルはすべて全文読了し、現行diffと実ファイルを静的に照合しました。編集、commit、pytest、runner、mutationは実行しておらず、検査緑も主張しません。

### 所有・diff境界

現在のtracked差分は6ファイルです。

- Codex author所有の実装面4ファイル:
  - `tools/check_ai_provenance.py`
  - `orchestrator/tests/test_check_ai_provenance.py`
  - `tools/check_docs.py`
  - `orchestrator/tests/test_check_docs.py`
- 親所有の文書面2ファイル:
  - `docs/ai-provenance.md`
  - `docs/decisions.md`

実装面の全hunkは指定4ファイルに収まり、所有外の実装hunkはありません。親所有面はMarkdownだけで、親の実装直編集を示す差分はありません。

なお、編集主体そのものはdiff bytesから復元できず、現在のsnapshotには独立した `author.patch` もありません。したがって、前段の「byte-for-byte一致」という報告には依存せず、ここで確認したのは現行hunkの所有範囲と所有外実装hunkゼロまでです。

### focus1対応表

| ID | 再判定 | 静的根拠 |
|---|---|---|
| A-1 LF以外の誤分割 | `closed` | parser出力をLF byteだけで分割し、UTF-8・record異常をfail-closedにする。[check_ai_provenance.py:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:94)、[同:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:122) |
| A-2 cwd `/`・ambient config | `closed` | 毎回freshなtemporary directory、その子cwd、親ceilingを使用。system/global/env configとrepo discoveryを遮断。[同:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:80)、[同:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:97) |
| A-3 既存AI受理集合への遡及 | `closed` | legacy AI parserは従来どおり先に必ず走り、CABだけが`check_cab`で分岐する。[同:140](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:140)、[同:165](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:165) |
| A-4 history simplification/rename | `closed` | commitごとに`--full-history --no-renames -S`を使用。[同:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245) |
| B-1 既存AI受理集合への遡及 | `closed` | R-1修正によりpre-policyではcanonical CAB経路を実行しない。scope・implementation判定は独立して残る。[同:378](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:378)、[同:383](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:383) |
| B-2 M1非単一理由 | `closed` | base/scopedを空、CAB findingだけを非空にする境界で`--no-divider`差を分離。[test_check_ai_provenance.py:291](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:291) |
| B-3 M2非単一理由 | `closed` | hostile local alias下でもCAB受理差を直接固定し、cwd/env構造assertと分離。[同:323](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:323) |
| B-4 policy needle自己追認 | `closed` | test-local独立literalを置き、production定数と実policy exact 1件を別々に照合。[同:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:16)、[同:539](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:539) |
| B-5 導入commit自身 | `closed` | 指定commit自身を含めて`git log -S`し、導入commit単独rangeの拒否境界がある。[同:628](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:628) |
| B-6 fence拒否 | `closed` | raw grammarは行頭候補を数えるため、fence内の列頭CABも候補となる。[check_ai_provenance.py:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:47) |
| R-1 pre-policy parser実行 | `closed` | ancestryを先に判定し、falseならconditional expressionによりraw grammar、CAB helper、canonical parser、temporary directoryのすべてを呼ばない。[同:175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:175)、[同:378](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:378) |

`partial`、`regressed`は残りません。

### R-1とlegacy検査

pre-policyでも実行されるのはpolicy activationを調べる`git log -S`とlegacy検査です。

- AI検査: `_ai_agent_values()`を常時実行。[check_ai_provenance.py:174](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:174)
- scope finding: CAB分岐と無関係に構築し、既存scope epoch条件で加算。[同:216](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:216)
- implementation検査: CAB finding加算後も独立して実行。[同:386](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:386)
- CAB raw grammar/parser: `check_cab=False`では未評価。

したがって、pre-policyのAI/scope/implementation受理集合を落とさず、CAB固有の失敗だけを非遡及化しています。

### D98のper-commit受理集合

| commit位置 | CAB gate | split CAB |
|---|---:|---:|
| policy導入前 | OFF | legacy検査上は受理 |
| policy導入commit自身 | ON | 拒否 |
| 導入後 | ON | 拒否 |
| needle削除commit・削除後 | ON | 拒否 |
| needle再追加commit・再追加後 | ON | 拒否 |
| 独立lineageの導入前 | OFF | legacy検査上は受理 |
| `--message-file` | 常時ON | 拒否 |

`_has_co_authored_by_policy()`は「現在needleが存在するか」ではなく「ancestryにneedle件数を変えたcommitが一つでもあるか」を返します。そのため削除後もtrueで、再追加後もtrueのままです。[check_ai_provenance.py:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245)

### message-file、finding集約、新規3test

`--message-file`は`validate_message()`の既定`check_cab=True`を使用し、policy historyを参照しません。[同:358](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:358) parserのGit error、UTF-8異常、record異常、temporary-directory異常は`OSError/RuntimeError/UnicodeError`としてrc=2へ畳まれます。[同:394](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:394)

finding集約も正常です。

- message-file: base、scope、CAB、implementationを各1回加算。[同:367](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:367)
- history: base、条件付きscope、CAB、条件付きimplementationを各1回加算。[同:382](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:382)
- AI findingがある早期returnでもCAB findingを返す。[同:178](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:178)

新規3testはいずれも`sys.argv`から`main()`へ入るCLI entry境界でrc、stderr、call countを固定しています。

- pre-policy call count 0: [test_check_ai_provenance.py:583](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:583)
- post-policy parser異常 rc=2/count 1: [同:605](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:605)
- message-file parser異常 rc=2/count 1: [同:883](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:883)

production定数ではなくtest-local literalと実Git履歴を使い、mockはparser障害seam一つだけです。恒真・過剰mockとは判定しません。

### コスト評価

現在の履歴は834 commit、既定監査範囲は495 commitです。

| コスト | 導入時期 | 漸近・現状 |
|---|---|---|
| 既定の全履歴走査、commitごとのmessage取得・legacy AI parser | このwave以前 | `O(H)`、既存コスト |
| commitごとの`git log -S` | D98初期実装 | 線形履歴の最悪で`O(H²)`相当。現状は既定監査ごとに約495 Git process追加 |
| fresh temporary directory + canonical parser | D98初期実装 | policy適用commit数を`P`として`O(P)` |
| fix2追加分 | fix2 | 新規外部processなし。pre-policyの約494件からfresh parser/temp作成を除去する改善 |

`git log -S`の反復コストは実在しますが、静的情報だけでは受入timeout、台帳欠落、commit不能などの具体的成果物影響を示せません。したがってrelease findingではなくbacklogです。

| ID | severity | real/refuted | path:line | 成果物影響 | 最小fix |
|---|---|---|---|---|---|
| BK-PERF-01 | backlog | realなコスト、release findingとしてはrefuted | [check_ai_provenance.py:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245) | 現時点では具体的影響を静的に立証できない | 実測で受入予算超過が出た場合のみ、needle変更commitを一度列挙し、commit graph上でactivationを伝播してper-commit `git log`を除去する |

### budget・registry・D96

- `docs/ai-provenance.md`: **8,832 / 9,000 bytes**。
- 独立registry: [check_docs.py:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:162)
- text-budget集合への合流: [同:1466](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:1466)
- dispatch allowlistは引き続き`REFERENCE_LIMITS ∪ SELF_LIMITS`だけ: [同:231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:231)
- 9,000/9,001境界: [test_check_docs.py:427](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_docs.py:427)、[同:438](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_docs.py:438)
- D96が要求する新D98と境界testは同じ現行差分に含まれる。[decisions.md:4269](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4269)、[同:4335](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4335)

## 総括

**GO。** A-1〜A-4、B-1〜B-6、R-1はすべて静的に`closed`です。pre-policyからcanonical CAB parser・temporary directory・raw grammarが除外され、legacy AI/scope/implementation検査は保持されています。D98の導入commit、導入後、needle削除後、再追加後の受理集合、message-fileの常時適用とrc=2 fail-closed、finding集約、新規3test、9,000-byte独立registry、dispatch allowlist非拡張、D96同一変更も整合しています。新規real release findingはありません。反復`git log -S`のコストだけを、具体的成果物影響未立証のbacklogとして残します。