## 総括

**推奨は (a) 復元。** 8月31日までは当該 pin が解決しており、matcher も本 wave も変わらないまま9月1日に消失したため、記録済みの exact 1 file を既知 SHA で戻すのが最小である。

## 親の結論の再検証

### 1. 本当に非帰属か — 支持

`428122575` は次の2 fileだけを変更し、pytest 設定・fixture・matcherには触れていない。

- `orchestrator/campaign/p3_b4_wiring_probe.py`
- `orchestrator/tests/test_p3_b4_wiring_probe.py`

問題側は `tools/codex_reasoning_ab.py` を直接ロードし、履歴 root も固定している。`orchestrator/tests/test_codex_reasoning_ab.py:109-128`。probe 側の import は専用 module だけである。`orchestrator/tests/test_p3_b4_wiring_probe.py:17-20`。

双方向検索も以下のとおり0件だった。

- probe 2 file → `codex_reasoning_ab|benchmark_snapshots|HISTORICAL_SESSIONS|.codex/sessions`: 0件
- reasoning test/tool → `p3_b4_wiring_probe`: 0件
- `conftest.py|pytest.ini` → `p3_b4_wiring_probe`: 0件
- wave差分中の `conftest.py|pytest.ini|test_codex_reasoning_ab.py|codex_reasoning_ab.py`: 0 file

共有fixture・collection面では、`benchmark_snapshots` consumerは既存のreal-repo群に列挙される。`orchestrator/tests/conftest.py:351-372`。collection hookはその既存集合へmarkerを付け、順序変更もitem identity集合を保存する。`orchestrator/tests/conftest.py:1983-2000`, `:1545-1564`。waveの変更はprobe test 1本の改名とassert追加だけである。`orchestrator/tests/test_p3_b4_wiring_probe.py:152-165`, `:288-300`。

改名によるcollection順・worker割当の変化は理論上ありうるが、本件原因にはならない。wave testを収集しない単独走と、wave差分を持たないdetached local mainの双方で同一26件が再現している。`facts-acceptance-red.md:82-90`。したがってimport、fixture、conftest、collection、worker割当のいずれにも本 wave からの到達経路はない。

### 2. 本当に決定的か — 「再現性」は支持、「0件＝file不在」は反証

現在の赤が安定再現する点は支持する。しかしmatcherの `rollout count is 0` は、物理fileが0本という意味ではない。「所有者として認識できたfileが0本」である。

0件になりうる条件は以下。

- 名前が `rollout-*.jsonl` でなければ走査されない。`tools/codex_reasoning_ab.py:628-631`
- unreadable file・broken symlinkなどでopenが `OSError` になると空rowsとして黙って無視する。`tools/codex_reasoning_ab.py:483-488`
- 部分書込み・切れたJSON・不正encodingはdecode/JSON errorとして無視する。`tools/codex_reasoning_ab.py:490-502`
- `payload.id` が存在するがnull・非文字列の場合、正しい `session_id` が併記されてもfallbackせず0件になる。`tools/codex_reasoning_ab.py:546-556`、その固定テストは `orchestrator/tests/test_codex_reasoning_ab.py:7522-7537`
- `id` が別sessionで `session_id` だけtargetなら「言及」であって所有ではない。`tools/codex_reasoning_ab.py:558-569`
- targetを所有する通常のfile symlinkは正しく解決されるため、symlink一般が原因ではない。`orchestrator/tests/test_codex_reasoning_ab.py:7955-7977`
- UTF-16/32・Unicode escapeは対応済み。`orchestrator/tests/test_codex_reasoning_ab.py:7162-7202`, `:7329-7338`
- SHA不一致だけならfast pathからfull scanへ落ちるので、直接の `rollout count 0` 条件ではない。`tools/codex_reasoning_ab.py:612-637`

したがって親の `find` / `grep` だけでは、権限・破損・書込み途中・schema変化を区別できない。ただし、8月31日には通っておりmatcherにその後の変更がなく、9月1日には記録済みの7月path自体が消えているという時系列から、今回は一時的部分書込みより「file消失」が最も整合する。

### 3. 本当にrepoの外か — triggerは支持、所有をrepo外だけとするのは反証

live素材の探索先は絶対path `/home/SFC/tanab/.codex/sessions` だけで、fixtureに代替rootはない。`orchestrator/tests/test_codex_reasoning_ab.py:128`, `:787-802`。toolも渡されたそのrootだけを検索する。`tools/codex_reasoning_ab.py:572-637`。

repo内21,139 fileを検索した結果、`rollout-*.jsonl` は1 fileだけで、別IDのsynthetic fixtureだった。`orchestrator/tests/fixtures/codex_ledger/readonly/rollout-2026-01-01T00-00-00-70000000-0000-0000-0000-000000000001.jsonl:1-5`。author rolloutのraw複製はない。

一方、repoは外部ambient corpusへの絶対依存、pin、そして「root directoryさえ存在すれば素材欠損をskipしない」挙動を所有する。`orchestrator/tests/test_codex_reasoning_ab.py:787-802`。したがって、今回のtriggerはrepo外のfile消失だが、脆弱な依存契約までrepo外所有とは言えない。

## いつから壊れているか

少なくとも2026-08-31の受入後から2026-09-01の間に壊れた。

- 2026-08-12にはauthor fileがexact pathで解決され、before/after双方のpathが一致していた。`output/insights/2026-08-12_t886-rollout-fastpath/beforeafter.json:37-42`, `:85-90`
- 2026-08-16には全3,646 rolloutでscan error・unreadableが0、authorを含む5 pinがexact pathへ解決していた。`output/insights/2026-08-16_t936-rollout-identity/mutation/a4-corpus-measurement.json:6-25`, `:29-34`
- 直近で確認できた正式なfull acceptance緑は2026-08-28。`18727 passed / 62 skipped / child-green`。`docs/archive/worklog-phase3-0828-1084-0829-1085.md:1-8`
- さらに2026-08-31の受入attempt 1は、唯一の赤が別testの1件だった。reasoning-abの26件は発生していない。`docs/worklog.md:63`, `:100-105`
- 2026-09-01にはreasoning-abだけ26件赤。`output/insights/2026-09-01_t1909-b4-probe-closure/acceptance-child-1.log:1-30`

8月30日以降の `tools/codex_reasoning_ab.py` / `test_codex_reasoning_ab.py` commitは0件で、8月31日時点のmain `d03855e92` から現tipまで、両file・`conftest.py`・`pytest.ini` の差分も0 fileだった。

よって「前から壊れていて誰かが迂回していた」証拠はない。復元対象は広い7月directory全体ではなく、既知の次の1 fileに限定すべきである。広域復元は現存する他4 pinを重複させる危険がある。

- path: `/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T14-49-01-019fac6b-4f74-7a03-aa4d-8a9de22b352c.jsonl`
- SHA-256: `e1ffc1e5b5e6d354701798d41a97a5e6da622423214531f356db3f1bb3ce6cbe`  
  `tools/codex_reasoning_ab.py:196-208`

(b) は歴史的benchmarkのprovenanceを変更し、(d) は部分欠損を受理し、(c) は決定的環境欠損を隠す。(e) を続ける必要も、上の復元情報が揃った現在はない。

## 他 wave の記録

同じlive赤の過去記録は見つからなかった。

`rollout count` の8 file・15行は、今回9月1日の2 fileと、8月16日のmatcher設計・synthetic負例6 fileだけである。8月16日の `rollout count is 0` は意図的なschema負例で、共有author rollout消失ではない。

`benchmark_snapshots` の61 file・105行は、fixture性能・real-repo直列化・consumer登録・mutation実行の記録が中心だった。近い既存障害はconsumerのserial registry登録漏れで、今回の素材消失とは原因が異なる。`docs/failures.md:1718-1727`

逆に、8月12・16・21・25・28・31の各記録は同fixtureまたはfull acceptanceが成立していた証拠であり、既存のskip・pin張り替え・holdによる迂回は確認できない。

## 全件検索の記録

母集合と除外:

- repo素材検索: worktree直下21,139 file。`.git/**`のみ除外。symlinkは0件。`output/`、untracked、binaryは含めた。
- wave記録検索: `docs/**` と `output/insights/**`。複製mutation checkoutである `output/insights/**/scratch/**` のみ除外。
- 外部sessionsの現物はdispatch射影外なので再走査せず、射影factsの7,120 file・author言及3 fileを使用した。`facts-acceptance-red.md:67-78`

検索式と結果:

```text
git show --name-only 428122575
→ 2 file

rg 'p3_b4_wiring_probe' test_codex_reasoning_ab.py tools/codex_reasoning_ab.py
→ 0行

rg 'codex_reasoning_ab|benchmark_snapshots|HISTORICAL_SESSIONS|\.codex/sessions'
   p3_b4_wiring_probe.py test_p3_b4_wiring_probe.py
→ 0行

rg --files -uu --hidden -g '!.git/**'
→ 21,139 file

rg --files -uu --hidden -g '!.git/**' | basename pattern rollout-*.jsonl
→ 1 file（synthetic、別ID）

rg -a -l -uu -F <exact term> .
author ID → 11 file
POS ID → 14 file
NEG ID → 8 file
fix2 ID → 7 file
fix1 ID → 9 file
author SHA → 4 file
5 IDs + author SHA のunion → 16 file
```

author ID一致はsource定数、manifest、過去path記録、今回の失敗log、`.pyc`だけだった。compiled bytecodeを除く一致fileに対する `session_meta` とauthor IDの同一行候補は0件。

```text
rg -a -n -F -i 'rollout count' docs output/insights
→ 8 file / 15 matched lines

rg -a -n -F -i 'benchmark_snapshots' docs output/insights
→ 61 file / 105 matched lines

rg -a -n -F -i '019fac6b' docs output/insights
→ 7 file / 11 matched lines

git log --since='2026-08-30' -- tools/codex_reasoning_ab.py
    orchestrator/tests/test_codex_reasoning_ab.py
→ 0 commit

git diff --name-only d03855e92 --
    tools/codex_reasoning_ab.py
    orchestrator/tests/test_codex_reasoning_ab.py
    orchestrator/tests/conftest.py pytest.ini
→ 0 file
```

pytestは実行しておらず、緑は新たに主張していない。