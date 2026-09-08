## pin 閉包の残り (file:line)

- **blocker:** 契約正本が stale。`contract-v3.1.md:117,181` は opened の不変条件を `len(throughputs) + nonfinite_count + exec_failures == reps_expected` と固定している。一方、実装は `s8b_terminal_evidence.py:860-872` で `other_integrity_failures` を加えた別の式を受理する。段 4 裁定どおりの実装ではあるが、「契約 v3.1 が正本」という状態とは両立しない。契約の supersede または erratum が必要。
- `test_official_perf_closure.py:44-91,533-550,905-910` は更新不要と読める。新規 production file はなく、変更 file のうち runner、campaign、stats は既に `_REVIEWED_PERF_FILES` にある。terminal evidence に新しい直接 perf 分岐は増えていない。
- `test_t671_source_binding.py:67-129,267-269` の exact 63 path も path 増減がないため更新不要。`runner.py` は既存 member。
- `test_frozen_artifacts.py:44-114` の `FROZEN_MANIFEST` は、現差分が凍結 bytes と `FORMULA_ID` を変更していない限り stale ではない。ただし裁定で v3 改版を選べば `floor_protocol.json` とこの manifest が必須変更になる。
- AST で旧 6 field をすべて含む dict literal を走査した結果、現行 Python には 20 箇所あり、すべて `execution_failure` を含む 7 key だった。exact 6-key literal の残存は見つからない。
- base 時点の差分対象 15 file の全体 sha256 を値検索したが、現 tree に旧 hash の literal pin は見つからない。6 field 全部を含む canonical bytes の文字列 literal も見つからない。

したがって、指定された frozenset・件数・全体 sha256・canonical literal の機械的 pin に残りは見つからない。残るのは上記の**意味契約そのものの不一致**である。

## consumer 取り残し

- **blocker:** `orchestrator/campaign/floor_pair_driver.py:1590-1618` も `measure_point(..., rep_observations=...)` の production consumer であり、`2020-2034` で observation 全体を `floor-pair-window/v3` へ保存する。本 wave 後の実 runner では各 row に `execution_failure` が増え、window bytes と `finalize_floor()` が記録する `artifact_sha256` が変わる。
- ところが同 consumer の test fake は `test_floor_pair_driver.py:1457-1461,1670-1673,2331-2335` で依然 3 key しか生成しない。実 producer の 7-key 形を通さず、同じ `floor-pair-window/v3` が旧 3-key と新 7-key の双方を受理する。この成果物波及は段 4 の consumer 表にも commit message にもない。
- `orchestrator/campaign/backoff_extended_sweep.py:547-562,590-609` も未列挙の subset consumer。`rep_index` と `throughput` だけを読み、raw observation は成果物へ保存しないため、現状の値への影響はない。これは nit。
- `pipeline.py:2794-2866` は本 wave の AST pin で扱われている。ただし `test_backoff_extended_sweep.py:202-250` の検査は実行経路へ 7-key dict を通すものではなく、対象関数の `observation.get("throughput")` 3 箇所を静的に固定する検査である。
- `_derive_rep_integrity()` の arity は production 4 callsiteと test 5 callsiteを再走査し、すべて 4 値 unpack へ追随している。arity の取り残しは見つからない。

## 射程の正直さ — 測っていないものを測ったと書いていないか

- `ruling-package.md:73-96` は、実環境値域を供給していないことを明記している。この点の偽主張はない。
- **blocker:** `ruling-package.md:66-69` は「`rep_integrity_failures` が `execution_failure is True` の rep 本数だけ増える」と書くが、実 test の assertion は `post_spawn_execution_exception` の本数だけである (`test_s8b_floor_stats.py:429-432`)。pre-spawn exception は旧式でも既に integrity failure なので増分は 0。裁定パッケージが帰属を過大化している。
- `ruling-package.md:50-51` の「有効性・median・floor 合成は test で固定」は過大。新 test は floor 合成を呼ばず、session 側も同じ現行 `session_median()` を同一入力で2回呼ぶだけである。
- `ruling-package.md:15-16` の「実 `measure_point()` を通した post-spawn probe」は、提示差分内には対応する probe がない。新しい runner test は subprocess seam が直接例外を投げる形で、rc=0 の completed process 後に parse/open が失敗する形ではない。別の一次証拠が存在する可能性は否定できないが、この裁定パッケージ単体では追跡不能。
- commit `cc6475965` の「受理集合は狭まる方向にしか動かない」は全体については偽。exact 6-key と exact 7-key の受理集合は入れ替わるため、新 7-key 入力は旧 verifier では拒否される。段 4 裁定自身はこの点を「単純な縮小ではない」と正しく認めている。

## characterization test は恒真か

完全な恒真ではない。`exec_failures`、qualified throughputs、post-spawn integrity 増分の比較は実際に差を拘束する。しかし、裁定パッケージが主張する閉包には達していない。

- 網羅数は no-perf の `5^3` と perf の `6^3`、合計 **341 通り**。凍結 protocol は `reps=5` なので、同じ列挙だけでも完全直積は `5^5 + 6^5 = 10,901` 通りである。
- `test_s8b_floor_stats.py:314-355` は test 内の合成 observation factoryであり、producer を通していない。
- `legacy_projection()` は旧実装の notes regex を再現せず、`notes[0]` の先頭整数を読む (`:357-387`)。実 runner は個別 failure note の後に集約 note を置くため、実 notes 列の形とも違う。
- `old_valid` と `new_valid`、`old_median` と `new_median` は、先に等値を確認した同じ `exec_failures` と `qualified` を同じ現行関数へ渡す (`:389-396,434-437`)。この2 assertionはその前の等値から必ず従い、独立した characterization ではない。
- producer outcome も閉じていない。`throughput_tps()` は metrics が非空でも throughput と代替材料が無ければ `None` を返せる (`benchparse.py:53-63`)。その場合 runner は rc=0、`execution_failure=False`、`throughput=None` を産出する (`runner.py:1214-1232`) が、列挙 outcome にない。
- この欠落は実害を持つ。`_derive_rep_integrity()` はその row を complete と数すが qualified へは入れない (`s8b_floor_stats.py:595-605`)。terminal の新しい本数式では有限、非有限、execution failure、other integrity のどれにも属さず、`s8b_terminal_evidence.py:863-872` で seal が拒否される。partial-output の E1 行を作れない。

よって結論は、**診断差の一部を固定する test ではあるが、「producer の全 outcome class を exact に固定した」という主張は成立しない**。

## 成果物影響を言えない変更

production 変更には次の影響を言える。

- `runner.py`: 新しい floor/campaign と floor-pair window の rep observation bytes、そこから派生する digest を変える。
- `s8b_floor_campaign.py`: `exec_failures`、`rep_integrity_failures`、qualified throughputs、exclusion class、journal/result の受理を変える。
- `s8b_floor_stats.py`: 旧 6-key artifact の受理、top-level counter mismatch の受理、診断値を変える。
- `s8b_terminal_evidence.py`: sealed terminal の受理集合、証拠 digest、terminal row の発行可否を変える。

成果物影響を持たないのは test と合成 fixture の変更、および B5 の AST pinだけであり、これらは nit。問題は「影響を言えない」ことではなく、`floor_pair_driver` への影響が裁定資料で言及されていないこと。

## 変異の単一理由性

- **M1/M2:** direct/capture 別の flag pin は存在する。ただし test 名の「all outcomes」は post-spawn rc=0 parse failure を含まず、射程表記が広すぎる。
- **M3/M4:** notes と flag の不一致、nonzero rc の分離入力は実装済み (`test_s8b_floor_campaign.py:9431-9471`)。local projection の感度はある。
- **M5a/M5b:** padding の `None` と key 存在は固定されている (`:9474-9489`)。
- **M6:** 段 4 が要求した「rc=0・counter complete・flag=True で、`execution_failure is False` だけを外せば complete」の専用 test がない。現 test の flag-only row は `returncode=None` でも落ちるため M6 を殺さない。実装後の事前登録は未充足。
- **M7:** old-six negative は exact-key 診断を固定するが、集合を6 keyへ戻しても `execution_failure` の exact-bool 検査が旧 rowを拒否する。段 4 記載どおり semantic kill ではなく diagnostic sensitivity としてのみ数えるべき。
- **M9:** `test_s8b_floor_stats.py:1760-1765` は top-level `exec_failures` だけを1へ変え、元の cell/floor 集約を残す。等値 gateを外しても `session_median()` が exec failureを理由に sessionを無効化し (`s8b_floor_stats.py:192-205`)、cell 再計算 (`:1024-1055`) が別理由で赤になる。単一理由入力ではない。
- **M11:** nonzero rc の sealed positive は旧本数式だけで拒否される形になっており、成立する。
- **M12:** `test_s8b_terminal_evidence.py:551-558` は flagだけを変え、campaign record の throughputs、exec count、integrity countを元のまま残す。対象の矛盾検査を外しても `s8b_terminal_evidence.py:1227-1234` の後続等値で拒否される。mutation kill は診断 message の変化であって受理集合反転ではない。
- **M10:** 段 4 が「probe 後に登録」としたものは本差分に登録されていない。取り下げとしては整合するが、kill 数へ含めてはならない。

少なくとも **M6 は未実装、M9とM12は F900 型の非単一理由**である。

## 過去の型の再発

- **F28 / F820 / F900:** M6、M9、M12で再発。対象述語への到達、後続 gate、変異点内外の検査を同時に数えていない。
- **F856 / F894:** `runner` の出力 schema を広げながら、`floor_pair_driver` の保存・再検証経路を scopeから落とした consumer 取り残し。
- **F54:** 裁定パッケージが「post-spawn 増分」を「execution_failure=True 全件の増分」へ集約し、要素単位の帰属を失っている。
- **F70 / F892:** 実 probe の一次証拠が裁定資料から追えず、test が固定していない範囲まで「固定済み」と記述している。
- **F30 / F39 / F842 / F864:** 指定された manifest、全体 sha256、path count、canonical literalについては再発を見つけなかった。ただし意味契約の stale と floor-pair の出力波及はこれらの検索だけでは見つからない。

## blocker と nit の仕分け

blocker:

1. 契約 v3.1 の本数式と実装が不一致。
2. `floor_pair_driver` の raw window schema・digest波及が consumer closureから欠落。
3. rc=0、`execution_failure=False`、`throughput=None` の producer outcomeが未分類で、terminalを sealできない。
4. characterization は341合成形に限られ、session比較の末尾は恒真。裁定パッケージの「全 outcome exact」と `execution_failure=True` 全件増分の記述は訂正が必要。
5. 変異 M6 が未充足。M9とM12の実装 testは単一理由性を満たさない。

nit:

- `backoff_extended_sweep` の subset consumerを資料へ明記していない。
- B5 は静的 AST pinであり、実経路へ7-key値を通してはいない。
- test/fixture変更そのものには production 成果物影響がない。

## 総括

**reject。現状を「実装完了」としてユーザー裁定へ出すのは不可。**

機械的な 6-key literal、既知の sha256 golden、63-path count、official perf inventory、`_derive_rep_integrity()` arity は閉じている。一方で、意味契約、共有 runner の別 consumer、producer outcome分類、裁定用 characterization、変異の帰属に blockerが残る。

実装ハンクは3 commitすべてに Codex `role=author` trailerがあり、著者条件による停止対象ではない。テストは実行しておらず、この結論は指定どおり静的読解・AST走査・grepだけによる。