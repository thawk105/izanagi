結論は **GO** です。指定13資料を全文読了し、前段の緑報告を根拠にせず、現在のdiffと実ファイルだけで静的再判定しました。pytest・runner・mutation・編集・commitは実行していません。

### 所有・差分境界

**PASS**。`git diff HEAD` の実装面は、Codex author unit の所有4ファイルだけです。

- [check_ai_provenance.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py)
- [test_check_ai_provenance.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py)
- [check_docs.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py)
- [test_check_docs.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_docs.py)

残るtracked差分は親所有の [ai-provenance.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/ai-provenance.md) と [decisions.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md) のMarkdownだけです。untracked成果物も6本すべてMarkdownで、第5の実装面、patch/diff、所有外実装hunkはありません。前段の「byte-for-byte一致」という断言には依存せず、現在観測可能なpath/hunk閉包で判定しました。

### focus1 対応表

| ID | severity | 判定 | 静的根拠 |
|---|---:|---|---|
| A-1 | HIGH | `closed` | CAB parser出力はUTF-8 bytesをLFだけで分割し、異常bytes/recordを例外化する。[実装:94-137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:94) |
| A-2 | HIGH | `closed` | 毎回fresh private directory、その子cwd、親ceilingを使い、system/global/env/local configとrepo discoveryを隔離する。[実装:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:80) |
| A-3 | HIGH | `closed` | AI-Agentは従来parserのまま。[実装:140](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:140) CAB applicabilityを先に決め、pre-policyではCAB経路を短絡する。[実装:378](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:378) |
| A-4 | HIGH | `closed` | commitごとに`--full-history --no-renames -S`を使う。[実装:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245) rename、merge keep/drop、削除、件数変化fixtureも対応する。[test:679](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:679) |
| B-1 | HIGH | `closed` | canonical化はCAB限定。AI-Agent・scope・Codex-authorはrepo cwd・divider既定parserを維持する。[実装:140](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:140) |
| B-2 | HIGH | `closed` | M1 fixtureはlegacy AI結果を空に固定し、CAB findingだけが変わる構造。[test:291](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:291) |
| B-3 | HIGH | `closed` | hostile local repoとvalid aliasを実際のfresh cwd/ceiling経路に置き、alias相殺の受理集合変化を固定する。[test:323](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:323) |
| B-4 | HIGH | `closed` | test-local独立literalをfixtureへ使い、production定数と実policy exact 1件を別assertする。[test:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:16)、[test:539](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:539) |
| B-5 | MEDIUM | `closed` | policy導入commit自身がsplit CABで、そのcommit単独rangeを拒否する境界になっている。[test:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:64)、[test:628](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:628) |
| B-6 | MEDIUM | `closed` | raw grammarはfence内の列頭候補も数え、backtick/tilde双方を負例にしている。[実装:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:47)、[test:202](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:202) |
| R-1 | HIGH | `closed` | `_has_co_authored_by_policy`を先行評価し、falseならconditional expressionが`_co_authored_by_findings`全体を呼ばない。[実装:175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:175)、[実装:378](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:378) call-count 0のCLI境界もある。[test:583](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:583) |

`--parse`と`--no-divider`の選択も、commit messageだけを入力するときの[Git公式仕様](https://git-scm.com/docs/git-interpret-trailers)と整合します。

### R-1とper-commit受理集合

pre-policyでは次の到達関係です。

```text
_has_co_authored_by_policy == false
  → validate_message(check_cab=False)
  → legacy AI-Agent検査
  → scope epoch検査
  → implementation epochならCodex-author検査
  ✕ raw CAB regex
  ✕ canonical CAB parser
  ✕ temporary directory
```

D98との対応も一致します。

| commit状態 | `_has_co_authored_by_policy` | CAB受理集合 |
|---|---:|---|
| policy導入前 | false | CAB gate非適用、legacy検査のみ |
| policy導入commit自身 | true | CAB gate適用 |
| 導入後 | true | CAB gate適用 |
| needle削除後 | true | ancestryの導入changeが残るため適用継続 |
| needle再追加後 | true | 過去の導入・削除・再追加hitのいずれでもtrue |

別lineageも、そのlineageのancestry内に独立導入がある場合だけtrueです。[D98:4358](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4358) の集合と一致します。

### message-file・finding合成・新規3 test

`--message-file` は `validate_message()` の既定 `check_cab=True` を変更せず呼ぶため、CABがないmessageでもcanonical parserを1回呼びます。[実装:359](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:359) `RuntimeError`、`OSError`、`UnicodeError` はmainでrc=2になります。[実装:394](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:394)

findingの合成も、base AI、条件付きscope、CAB、implementationを各1回だけ加算します。[実装:361](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:361)、[実装:379](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:379) CAB二重加算・消失、AI finding消失の経路はありません。

新規3 testはいずれも `sys.argv` と `main()` を通すCLI境界です。

- pre-policy: `_parsed_trailers`を呼べば未捕捉`AssertionError`で即赤となり、call count 0とrc=0を固定。[test:583](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:583)
- post-policy: 独立literalで作った導入commit自身を使い、parser `RuntimeError`をrc=2、call count 1へ固定。[test:605](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:605)
- message-file: policy履歴なし、CABなしの正常messageでもparserを1回呼び、異常をrc=2へ固定。[test:883](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:883)

mock対象はparser障害の注入点だけで、argparse、履歴判定、CLI分岐、exception→rc変換はproduction経路です。production needle由来の恒真でも過剰mockでもありません。

### コスト評価

現在HEADは834 commit、既定監査範囲は495 commit、policy pathの履歴変更は6 commitです。

| 区分 | 静的コスト |
|---|---|
| wave以前 | 既定rangeの`rev-list`、scope/implementation用`git log -S`各1回、commitごとの`git show`×2、legacy parser、epoch後のmerge-base/diff-tree等。概ね履歴長に線形で、複数subprocessは既存コスト。 |
| 今回追加 | commitごとの`git log --full-history -S`。線形履歴の最悪形では反復ancestry走査がO(N²)。現在の既定監査なら約495回の新規Git起動。 |
| canonical parser | post-policy commit数Pに対して、fresh temporary directory＋Git parserがO(P)。 |
| fix2の効果 | pre-policyのcanonical parser/tempdir/raw grammarを除去し、fix1時点のO(N) fresh-parser負担をO(P)へ縮小。per-commit `git log -S`は残る。 |

新しい `git log -S` の反復はコスト構造として実在しますが、静的資料から現在の受入を実用不能にするwall time、timeout、成果物欠落は示せません。DW-G05に従いreal findingにはせず、次のbacklogへ分離します。

- ID: `BL-PERF-1`
- severity: `nit/backlog`
- real/refuted: コスト増はreal、現waveのblockerという主張はrefuted
- path: [check_ai_provenance.py:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245)、[同:374](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:374)
- 具体的成果物影響: 現時点では未立証。将来、大履歴でprovenance受入が遅延・timeoutする可能性のみ
- 最小fix: policy hitを一括取得し、単一のparent graph上でlineageごとのactivationを伝播する。実測で受入時間がblocker化した時点で実施

### 9,000 bytes・registry・D96

[ai-provenance.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/ai-provenance.md) は現在 **8,832 / 9,000 bytes** です。

- 独立registry: [check_docs.py:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:162)
- 全budget consumerへの合流: [check_docs.py:1466](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:1466)
- dispatch allowlistはREFERENCE/SELFだけで非拡張: [check_docs.py:231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:231)
- 9,000受理／9,001拒否とregistry独立性: [test_check_docs.py:417](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_docs.py:417)

D98と境界testは同じ現在差分にあり、D96の「新D＋境界testの同一変更単位」を満たします。[D96:4271](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4271) ただし「緑を確認してland」は本read-only reviewの検証範囲外です。

新規real findingは **0件**、したがって新規finding IDの採番はありません。

## 総括

**GO。** A-1〜A-4、B-1〜B-6、R-1は全件`closed`、`partial`・`regressed`は0件です。pre-policyからcanonical CAB parser・temporary directory・raw grammarが除外され、legacy AI/scope/implementation検査は維持されています。per-commit集合、message-fileのrc=2、finding合成、新規3 test、9,000-byte独立registry、dispatch非拡張、D96同一変更も静的に整合します。性能上のO(N²)懸念だけをbacklogへ分離しました。テスト・runner・mutationの緑は主張していません。