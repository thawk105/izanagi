結論は **GO** です。R-1 は静的に閉じており、新規 must-fix はありません。編集、commit、pytest、runner、mutation は実行しておらず、検査緑も主張しません。

## 所有境界

`git diff HEAD` の tracked 差分は6ファイルです。

- Codex author 所有の実装面4ファイル:
  `tools/check_ai_provenance.py`、`orchestrator/tests/test_check_ai_provenance.py`、`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`
- 親所有のMarkdown 2ファイル:
  `docs/ai-provenance.md`、`docs/decisions.md`

D95の実装面定義と、plan v2の所有4ファイル指定に一致します。[D95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4244) [所有指定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/output/insights/2026-07-29_t153e-t15423-review-verbatim/adjudication-plan-v2.md:53)

全実装hunkはこの4ファイル内にあり、所有外の実装ファイル、mode変更、test削除はありません。untracked成果物もMarkdownだけです。したがってpath/hunk境界は **PASS** です。

ただし、このsnapshotには以前参照された `author.patch` が残っていないため、作業者の打鍵主体そのものをbyte-for-byte再鑑定はできません。最終的なrole帰属の正本は未作成のcommit trailerなので、land時にCodex `role=author`を含めることが必要です。

## 対応表

| ID | 再判定 | 静的根拠 |
|---|---|---|
| A-1 | `closed` | parser出力をLF byteだけで分割し、UTF-8・異常recordをfail-closed。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:122) [境界test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:414) |
| A-2 | `closed` | 毎回fresh private directory、その子cwd、親ceiling、ambient Git config除去。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:80) [temp処理](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:97) |
| A-3 | `closed` | legacy AI parserは不変で、pre-policyではCAB関数全体を迂回。[legacy parser](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:140) [分岐](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:174) |
| A-4 | `closed` | commitごとに`--full-history --no-renames -S`。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245) rename/merge/delete境界も存在。 |
| B-1 | `closed` | AI-Agent、scope、Codex-authorは従来parserのまま。CAB導入前にcanonical parserを共有しない。 |
| B-2 | `closed` | M1はbase/scopeを空に固定し、CAB findingだけを変える単一理由境界。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:291) |
| B-3 | `closed` | hostile local repoとvalid alias、system/global/env aliasを独立に固定。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:323) |
| B-4 | `closed` | test-local独立needleをproduction定数と実policy exact 1件へ照合。[literal](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:16) [照合](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:539) |
| B-5 | `closed` | policy導入commit自身の単独rangeがCAB gate対象。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:628) |
| B-6 | `closed` | backtick/tilde fence内の列頭CABを負境界として固定。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:202) |
| R-1 | `closed` | ancestry判定が先、`check_cab=False`ならraw regex・canonical parser・temporary directoryのcall chainへ入らない。[history loop](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:378) [call-count test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:583) |

`partial`、`regressed` は0件です。

## 必須境界の照合

D98のper-commit受理集合と一致します。

| commit状態 | CAB gate |
|---|---|
| policy導入前 | OFF。legacy AI/scope/implementation結果だけを使用 |
| policy導入commit自身 | ON。自身の`-S` changeが見える |
| 導入後 | ON。ancestryに導入changeが残る |
| needle削除後 | ON。過去のaddition/deletion hitがancestryに残る |
| 再追加後 | ON。同じく過去changeが少なくとも1件存在 |

`--message-file` は`validate_message()`の既定値`check_cab=True`を変更せず呼び、CAB parser異常はmainの`RuntimeError`／`OSError`／`UnicodeError`捕捉でrc=2になります。[message-file経路](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:359) [rc=2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:394)

finding配線も整合しています。

- legacy AI findingはCAB分岐より先に生成される。
- AI欠落、`none`、形式異常、通常経路の各returnがCAB listを保持する。
- mainはbase、cab、implementationを各1回だけ加算する。
- scopeは従来epoch条件のままで、CAB追加による消失や二重加算はない。

新規3testはいずれも`sys.argv`から`main()`へ入るCLI境界を通し、parser seamだけを置換しています。

- pre-policy: call count 0、rc=0。
- policy適用状態: call count 1、parser異常rc=2。
- message-file: policy履歴なしでもcall count 1、parser異常rc=2。

policy適用testは導入commit自身を使いますが、production上は後続commitと同じ`cab_policy_applies=True`分岐です。test fixtureのneedleは独立literalで、production定数由来の恒真ではありません。過剰mockとも判定しません。

## コスト評価

既存コストと今回の増分は次のとおりです。

| 面 | 漸近・現在規模 | 判定 |
|---|---|---|
| wave以前 | H commitの列挙、各commitの`git show`×2、legacy parser、implementation epoch判定などで概ねO(H) subprocess | 既存 |
| 今回の`git log -S` | commitごとにancestryを走査するため、線形履歴では最悪O(H²)・H subprocess | 新規 |
| canonical parser/temp | policy適用commit数Pに対してO(P) subprocess＋temporary directory | 新規 |
| raw CAB scan | policy適用message総bytesに線形 | 新規 |

現repoは全834 commit、既定監査範囲は495 commitです。線形近似ではpickaxeの祖先訪問量は約122,760 commit相当、追加Git processは495本です。一方、呼出wrapperには固定timeoutがなく、現在の成果物で受入が実用不能になる静的証拠はありません。[caller](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/task_run_check.py:15)

`PERF-B1` — severity: `nit/backlog`; real/refuted: 漸近コスト自体は`real`、受入阻害findingとしては`refuted`。path: [check_ai_provenance.py:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245)。具体的成果物影響は現時点で示せません。実測で運用閾値を超えた場合の最小fixは、policy-change commitを一度だけ列挙してDAG上の適用状態を事前計算することです。

## Policy・D96

- `docs/ai-provenance.md` は実測 **8,832 / 9,000 bytes**。
- `PROVENANCE_LIMITS`は独立registry。[定義](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:162)
- budget consumerへ合流済み。[合流](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:1466)
- normative dispatch allowlistはREFERENCE/SELFのみで非拡張。[allowlist](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:231)
- 9,000受理、9,001拒否の独立境界がある。[tests](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_docs.py:417)
- D98、production変更、境界testは現行diffの同一変更単位に存在し、D96の構造要件を満たします。まだcommit前なので、最終的に同一commitへlandすることが条件です。

## 総括

**GO。** A-1〜A-4、B-1〜B-6、R-1は全件`closed`、新規real findingは0件です。pre-policy履歴はcanonical CAB parser・temporary directory・raw CAB grammarを呼ばず、legacy AI/scope/implementation検査を維持します。policy適用境界、message-fileのrc=2、finding共存、3つの新規CLI境界、9,000-byte registry、dispatch非拡張、D96同一変更も静的に整合しています。性能面のO(H²)増分だけを成果物影響未立証のbacklogへ分離します。