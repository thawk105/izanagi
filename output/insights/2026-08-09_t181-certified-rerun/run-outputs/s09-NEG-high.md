判定は **GO** です。fix2 後の静的照合では、新規の real finding はありません。pytest、runner、mutation は実行せず、前段の緑報告も根拠にしていません。

## 所有境界

変更面ベースでは PASS です。

- tracked 差分6ファイル中、実装面は指定された所有4ファイルだけです。
  - `tools/check_ai_provenance.py`
  - `orchestrator/tests/test_check_ai_provenance.py`
  - `tools/check_docs.py`
  - `orchestrator/tests/test_check_docs.py`
- 残りは親所有の `docs/ai-provenance.md` と `docs/decisions.md`。
- untracked は指定レビュー成果物の Markdown 6本だけで、所有外の実装ファイルはありません。
- HEAD は `8c8dc5e`、staged 差分はありません。

ただし、前レビューが参照する `author.patch` / `author-prompt.txt` はこの snapshot に収録されていません。そのため「誰が打鍵したか」の byte-for-byte 再鑑定まではできません。現在の全実装 hunk が Codex author の所有4ファイル面に厳密に収まり、親所有面に実装 hunk がないことまでは独立確認できました。

## focus1 対応表

| ID | 再判定 | 根拠 |
|---|---|---|
| A-1 | `closed` | canonical 出力は LF byte のみで分割し、UTF-8・record異常を例外化しています。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:94) |
| A-2 | `closed` | 毎回 private temporary directory、その子を cwd、親を ceiling とし、system/global/env/repo config を隔離します。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:80) |
| A-3 | `closed` | AI-Agent は従来 parser のままです。fix2 により pre-policy では CAB 経路自体が呼ばれません。[legacy parser](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:140) [分岐](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:378) |
| A-4 | `closed` | per-commit query は `--full-history --no-renames`。rename、merge、削除、0→2→1 の境界も独立しています。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245) |
| B-1 | `closed` | CAB canonical parser と既存 AI/scope/Codex-author parser が分離され、旧履歴への CAB 実行遡及も解消しました。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:165) |
| B-2 | `closed` | M1 は base/scoped を空、CAB finding のみ非空にする単一理由 control です。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:291) |
| B-3 | `closed` | M2 は hostile ancestor の valid alias と private ceiling を直接対比し、malformed env に依存しません。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:323) |
| B-4 | `closed` | test-local 独立 literal を使い、production 定数と実 policy の exact 1件を別々に固定しています。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:539) |
| B-5 | `closed` | policy 導入 commit 自身の単独 range が CAB gate 対象です。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:628) |
| B-6 | `closed` | raw grammar は列頭の SP/HTAB を含めて数え、backtick/tilde fence 内も拒否境界です。[grammar](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:47) |
| R-1 | `closed` | ancestry を先に判定し、pre-policy は `check_cab=False`。call-count 0 の CLI 境界があります。[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:374) [test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:583) |

`partial`、`regressed` は残っていません。

## 必須判定の照合

### R-1とper-commit受理集合

pre-policy でも legacy `_ai_agent_values()` は走る一方、CAB raw regex、canonical parser、temporary directory は `_co_authored_by_findings()` ごと不達です。base AI finding、scope epoch、Codex-author検査も従来の位置で維持されています。

| commit位置 | `_has_co_authored_by_policy` | CAB gate |
|---|---:|---|
| 導入前 | false | 適用しない |
| policy導入commit自身 | true（0→1） | 適用 |
| 導入後 | true | 適用 |
| needle削除commit・削除後 | true（導入/changeがancestryに残る） | 適用継続 |
| 再追加commit・再追加後 | true | 適用継続 |
| policyを導入していない別lineage | false | 適用しない |
| 独立に導入した別lineage | true | 適用 |

これは [D98の規範](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4358) と一致します。

### `--message-file` とfinding合成

`--message-file` はhistory判定を経ず、既定の `check_cab=True` で常にCAB parserへ進みます。[main](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:358)

parserが起こし得る OSError、RuntimeError、UnicodeError はrc=2へ畳まれます。[例外境界](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:394)

通常分岐では、

- base AI finding は常に1回加算
- scope finding は従来epoch条件で1回加算
- CAB finding は1回だけ加算
- implementation author finding も従来どおり

となり、CABの二重加算・消失、AI findingの消失はありません。parser異常時に通常findingではなくrc=2になるのは意図されたfail-closedです。

### 新規3testの検出力

3件とも `main()`、argparse、range/message-file分岐、出力、rc変換を通るCLI関数境界です。

- pre-policy: `_parsed_trailers` を「呼ばれたら失敗」にし、rc=0かつcall count 0を固定。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:583)
- post-policy: 導入commit単独rangeでparser例外、rc=2、call count 1。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:605)
- message-file: 実ファイル入力でparser例外、rc=2、call count 1。[test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_ai_provenance.py:883)

policy fixture は production 定数ではなく test-local literal から構成され、その一致を別assertしています。mockもparser異常の注入点だけで、ancestry判定やCLI処理を置換していないため、恒真・過剰mockとは判定しません。

## コスト評価

現HEADでは全履歴834 commit、既定監査範囲は495 commitです。

このwave以前から存在するコストは、commitごとのsubject/message取得、legacy trailer parser、epoch ancestry判定、必要時のpath取得とCodex-author再parseです。すでに多数のGit subprocessと、最悪時には反復 ancestry walkを持っています。

今回の追加分は次のとおりです。

- 全commitにper-commit `git log -S`: worst-caseで履歴長に対し二次的なwalk量を追加。
- policy適用後commitごとにfresh directory＋canonical Git parser: 適用後commit数に対して線形。
- `--message-file`: fresh parser 1回のみ。
- fix2後のpre-policy 495 commitではfresh parser/tempdirは0回。ただし `git log -S` は495回追加されます。

現履歴規模で受入を実用不能にする具体的成果物影響は静的資料から示せません。したがって blocker ではありません。

- ID: `PERF-BL-1`
- severity: `backlog`
- real/refuted: 漸近コストの増加自体はreal、現成果物を阻害するreal findingはrefuted
- path: [check_ai_provenance.py:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:245)、[同:374](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_ai_provenance.py:374)
- 放置時の具体的成果物影響: 現時点では未提示。将来、履歴増加によりprovenance受入時間が運用閾値を超える可能性のみ
- 最小fix: 実測で閾値超過した時点で、needle change commitを一走査で列挙し、選択rangeの親グラフ上で適用状態を伝播・cacheする

## policy・D96

- `docs/ai-provenance.md` は実測8,832 bytesで9,000未満。
- `PROVENANCE_LIMITS` は独立registryです。[check_docs.py:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:162)
- 合流先はtext budget consumerの `all_limits` だけです。[check_docs.py:1466](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:1466)
- dispatch allowlistは `REFERENCE_LIMITS` と `SELF_LIMITS` のままで、provenance pathは追加されていません。[check_docs.py:231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/tools/check_docs.py:231)
- 9,000受理・9,001拒否は独立literal境界です。[tests](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/orchestrator/tests/test_check_docs.py:417)
- D96が要求する新D98と境界testは同じ未commit変更単位に存在します。[D96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4269) [D98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/neg/docs/decisions.md:4335)

新規 real finding はありません。検査緑は主張しません。

## 総括

**GO。** focus1のA-1〜A-4、B-1〜B-6、R-1は全件 `closed` です。fix2はpre-policy履歴からCAB raw grammar、canonical parser、fresh temporary directoryを除外しつつ、legacy AI/scope/Codex-author検査を維持しています。導入commit、導入後、削除後、再追加後の受理集合、`--message-file` の常時適用とrc=2、finding合成、新規3境界test、9,000-byte独立registry、dispatch非拡張、D96同一変更も静的にD98と一致します。残るのはper-commit `git log -S` の非blockingな性能backlogと、snapshotにauthor.patchがないため変更者身元のbyte-for-byte再鑑定まではできないという監査上の限界だけです。