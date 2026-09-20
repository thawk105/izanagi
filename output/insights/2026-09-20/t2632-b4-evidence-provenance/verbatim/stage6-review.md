# [T-2632] 段 6 read-only review (codex gpt-6-astra、2 レンズ 1 本、2026-09-20 19:24〜19:32 JST) — 逐語

## 所見

1. **real / must-fix — §7 裁定2(iii)：比較項目が完全な `PerfConfig` を覆わない。**

   一次資料：`orchestrator/campaign/pipeline.py:184`、D2150 項2、事前登録 §5.1.1。`PerfConfig` は `records / threads / workload / extime / reps` を持つ。稿の `run_cmd` 比較案には **`reps` が無く、workload の `ycsb_max_ope` も落ちている**。前 wave もこの不足を明記している。列挙された6項目だけの一致を、設定全体の exact 一致とは呼べない。

   訂正文案：「承認された `PerfConfig` の全 field（reps と workload 全 key を含む）および `env_tag` の一致を、出所を名指して確認する。`bench_done.run_cmd` だけでは全 field を確認できないため、確認不能な項目を不足として残す。」

   **放置時の影響：裁定2が、凍結された一致条件を部分一致へ弱める案になる。**

2. **real / must-fix — 結論・§2.2・§3.4：現行 carrier の探索漏れがあり、不在断定が広すぎる。**

   一次資料：`orchestrator/campaign/p3_autonomous_workload_trial.py:4394`、`p3_s4_loop_trigger_gating.py:299`、`autonomous_trial_completeness.py:3988`。

   稿に無い次の経路がある。

   - autonomous workload supervisor は `proposals/<...>.json` に proposal document を保存し、arm 経路では path・sha256 を generation record に記録する。同じ generation に harness outcome も保持する。
   - trigger driver の opt-in 経路は、proposal の **raw bytes hash** を名前にした `source-bindings/<sha256>.preimage` を保存する。内容は proposal JSON ではなく、materialized source の digest preimage。
   - completeness consumer は proposal、provenance、`build_attempt_id`、WAL start、source artifact を照合する。

   これは **base の赤 precursor に必要な辺が閉じた証拠ではない**。しかし「現行形式」「proposal bytes を保持する harness carrier は無い」を repo 全体へ広げることはできない。

   訂正文案：「調査した旧3 campaign、および B-4 が選択した base driver の precursor 保存経路では閉じない。別系列の autonomous trigger supervisor には proposal 保存と source-preimage 束縛の先例があるが、base precursor への接続と B-4 canonical identity の保証は別途必要である。」

   **放置時の影響：裁定1の不足が『base への接続・必要な束縛の追加』から『既存の先例も無い carrier 新設』へ過大化する。αの優位性も先例を追加して比較し直す必要がある。**

3. **real / must-fix — 結論表・§4.2(2)：`iteration` の出現0は現物と不一致。**

   一次資料：3 campaign の `loop_state.json`、`verbatim/parent-probe-procedure.md`。

   `iteration` は各 loop_state の top-level と whiteboard に存在し、文字列出現数は base **5**、sort **2**、trigger **3**。親の probe が検索したのは **WAL 文字列だけ**であり、その結果を loop_state・lock 全体へ拡張している。

   訂正文案：「3 campaign の WAL には `parent / ancestor / iteration` の文字列が無い。loop_state には iteration と行順があるが、それを proposal の祖先関係と定義する契約、および base の行から WAL attempt への束縛は無い。」

   **放置時の影響：裁定2の不足が『既存の順序の意味と対応の未確定』ではなく、『順序情報そのものの欠落』として説明される。**

4. **real / should-fix — §4.1・§7 裁定2(i)：`wal:` ref は「同じ関数」ではない。**

   一次資料：`agent_outputs.py:69`、`layer3_report.py:94`。

   `agent_outputs.canonical_sha256` は `allow_nan=False` の canonical JSON を hash する。layer3 の WAL 経路は独自の `_canonical_bytes` と `hashlib.sha256` を使い、`allow_nan=False` を指定しない。agent_outputs の関数を呼ぶのは **`ao` 経路だけ**である。現物の有限JSONでは結果が一致する。

   訂正文案：「現物では、両実装の serialization が同じ bytes となるため ref が一致する。関数自体と非有限値の受理域は異なる。裁定案では採用する canonicalization を明記する。」

   **放置時の影響：裁定2が hash の定義・受理域を一意に指定したように見えて、実際には二つの実装を混同する。**

5. **real / should-fix — §7 裁定2(ii)：祖先の読みの択一を明示すべき。**

   一次資料：事前登録 §5.1.1、`rulings-verbatim.md`、`p3_s4_loop.py:1826`。

   「同一 campaign の直前の success」は可能な読みだが、凍結文面から唯一には導けない。他には、proposal が派生した入力 snapshot の系譜、campaign をまたぐ明示的な parent 系譜が考えられる。重複 success は新しい評価を作らないので、行順と評価の系譜も同一ではない。

   訂正文案：「祖先関係は未確定であり、①同一 campaign の時間順、②proposal の派生元 snapshot の系譜、③campaign 間を含む明示的系譜の択一を返す。①を推奨する場合も、祖先無し・同着の複数候補・設定不一致では不適格とし、別基準へ切り替えない。」

   **放置時の影響：裁定2が、複数ある解釈からの選択を単なる用語確認として承認させる形になる。**

6. **real / should-fix — §2.3・§3.3・§8：K2 の親観測と独立確認の区別が必要。**

   一次資料：稿記載の repo 外 campaign path、`parent-ao-probe.json`、`parent-probe-procedure.md`。

   本レビュー環境では、指定された K2 campaign directory と、その journal・WAL・checkpoint・lock は **不在**だった。必読射影 file はすべて読めたため、検査は継続した。親JSONの `mode=ingested`、source hash と proposal raw hash の不一致は確認できるが、実物による再確認ではない。

   また、収録された probe は campaign 全 file 内の canonical hash 出現を検索していない。「campaign dir のどこにも無い」は、その逐語手順だけでは再現できない。

   訂正文案：「K2 campaign の現存と内容は親の2026-09-20観測。独立レビュー環境では指定 path が不在のため再確認できなかった。canonical hash の不在は、実際に確認した記録と範囲に限定して述べる。」

   **放置時の影響：裁定1を支える『現行形式の実例』と裁定4の実物例が、独立再確認済みと誤認される。コードによる欠陥の根拠は残る。**

7. **real / nit — §1・§3.1：精度を上げられる表現。**

   一次資料：`p3_b4_analysis_ledgers.py:124`、archive worklog の指定2エントリ。

   `B4ScheduledAttemptInput` 自体は17 fieldであり、12は D2100 が不足と分類した field 数。また §3.1 の表は「散文の消去法」と限定しているが、後段の「実際は」は推定を確定記録へ戻してしまう。

   訂正文案：「`B4ScheduledAttemptInput` のうち D2100 が不足とした12 field」「archive の記述と WAL 時刻順を合わせると、it2 は再利用、it3・4 は後続2 variant と推定される。」

   **放置時の影響：択一・推奨は変わらない。記録と推論の境界が読みづらくなる。**

## 再計算した値の照合表

以下の略号は稿 §2.1 の campaign directory を指す。

- B：`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/`
- S：`output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/`
- T：`output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/`

依頼の「12値」に対し、実際の §2.1 は **14値**。全14値を `sha256sum` で再計算した。稿欄は表示だけを短縮しており、比較は64桁全体で行った。

| file | 稿の値 | 独立再計算 sha256 | 照合 |
|---|---|---|---|
| B `campaign.lock` | `0b53a387…` | `0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9` | 一致 |
| B `loop_state.json` | `616a5a1d…` | `616a5a1d83a7881c90d37469f1fa69a117d72fb5cd6f54f18ff031b63f34279f` | 一致 |
| B `runs/wal.jsonl` | `2163b794…` | `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611` | 一致 |
| B `s4_loop_digest.txt` | `0eee68f1…` | `0eee68f16843e40abec9300a697dd6ffdfe45bc8c52aa5e8cc5a5879b1912e1f` | 一致 |
| S `campaign.lock` | `3be89e0d…` | `3be89e0ddad8e8b2b37d35168c49affe7889ea580831973dc0d6d9706aaa4f97` | 一致 |
| S `loop_state.json` | `f89b8b7c…` | `f89b8b7c1d46f17dd16b25c68069b46f69e9dd638dd9026e7a8e8d3ce1ec6cd8` | 一致 |
| S `runs/wal.jsonl` | `b901f23a…` | `b901f23a502e4d3843454de807ca01666c145ee7d9d424a957bb366ef3e793a5` | 一致 |
| S `s5_sort_loop_digest.txt` | `aed7e85b…` | `aed7e85bda1db38b25454c2fbaf145b36ac253d55d16c0370d6af4b2ea624a3f` | 一致 |
| T `campaign.lock` | `3f72ecd5…` | `3f72ecd58a6df4018d136bcbb8abb276114ba8d302c64aaf792c473ae4b1de0c` | 一致 |
| T `loop_state.json` | `18d5e40b…` | `18d5e40bd4b4c8e6a4d09b8d4ac4b94c0ffb173b79092dfc7a6abe7e1aa2c79d` | 一致 |
| T `runs/wal.jsonl` | `a539648d…` | `a539648d29afce9be036eba519b53f21fd1f8e1fb7bfe24549f4ec3ceac31ea3` | 一致 |
| T provenance report | `cfbcd125…` | `cfbcd1257ac96ff9500f50993938b9f99dceaa36e3e2ca51dea387ff0f72a056` | 一致 |
| T `reports/layer3_report.json` | `3f97e769…` | `3f97e7694e614bb51f2d7bde9824fea9b79c5bc19614427a0ebed9a927031320` | 一致 |
| T `s8a_trigger_loop_digest.txt` | `3825b398…` | `3825b39824096f97a61d95d89a37bd7d9616e5d40022a1e8182d7c66ce532e7e` | 一致 |

| 項目 | 稿の値 → 独立再計算 | 照合 |
|---|---|---|
| B WAL 行数 / variant数 / whiteboard行数 | `15 / 3 / 4` → `15 / 3 / 4` | 一致 |
| S 同上 | `6 / 1 / 1` → `6 / 1 / 1` | 一致 |
| T 同上 | `12 / 2 / 2` → `12 / 2 / 2` | 一致 |
| B whiteboard iteration | `[1,2,3,4]` → 同じ | 一致 |
| S whiteboard iteration | `[2]` → `[2]`、top-levelも2 | 一致 |
| T whiteboard iteration | `[1,2]` → 同じ | 一致 |
| success / rejected | `7 / 0` → `7 / 0` | 一致 |
| T entries `"1"` | `e1785940172e` → 同variantがWALに存在 | 一致 |
| T entries `"2"` | `ca5206c3dac5` → 同variantがWALに存在 | 一致 |
| loop_state の `iteration` 出現 | 0という断定 → B=5、S=2、T=3 | **不一致** |
| `wal:` ref の関数同一性 | 同じ関数 → 別実装、現物の結果は一致 | **不一致** |

WAL原文をJSONとして読み、`sort_keys=True, ensure_ascii=False, separators=(",",":"), allow_nan=False` の bytes を独立に SHA-256 計算した。

| variant | 稿 fitness_tps → 再読値 | 再計算した commit ref（稿と全桁一致） |
|---|---|---|
| `20bbb4c1a855` | `491796.5` → 同じ | `wal:9bce3bc47e9d1b603cf39733df061bb41fe8e4704234d239c0f60751cb10d989` |
| `27d1d016998e` | `525721.5` → 同じ | `wal:98af80643f35475046303f0abedfd9dd4e0e2ced77eb353f17181fe888975e60` |
| `dad58f9f9000` | `487088.5` → 同じ | `wal:6e598a426dee8bccd7ab65d7f0dc3b522323b064f4b7e9a56c582bc2742d0d47` |
| `aa32126d769f` | `274871.5` → 同じ | `wal:d3c74339da9f706053a6eaddcd1c0ab9290628495a5abb56526dae08744bcb98` |
| `e1785940172e` | `275614.5` → 同じ | `wal:4f40b669b157d87ee69a2c7cf2995ae9f1700911513ab7147ac3f9983c111a1e` |
| `ca5206c3dac5` | `276472.0` → 同じ | `wal:2d68cc8a15d25fe1bc5cd1d3af27fa8a76ba1bfdd242217442a437d371ff05fa` |

T の bench ref も独立再計算し、現物 layer3 の `source_ref` と一致した。

| variant | 稿 → 独立再計算 | 照合 |
|---|---|---|
| `e1785940172e` | `wal:562b9181…` → `wal:562b9181af2cb7d809c1a355aff94128d7fc88ddcfe68da5d4b23a82ca82d2d6` | 一致 |
| `ca5206c3dac5` | `wal:308850a3…` → `wal:308850a3a81b90cf98f476dafec908313646b70330d8c6ce9ae65b215d6c3c31` | 一致 |

K2および親probeの追加照合：

| 対象 | 稿 → 再計算・確認 | 照合 |
|---|---|---|
| insight `proposal-4.json` raw | `bd3e5fd2…` → `bd3e5fd2110cc75313a8692f9c6e4c3ba4b20aa5050f0c99a50ab049ea12d53f` | 一致 |
| 同 canonical B-4 hash | `c9b2595a…` → `c9b2595a90fc30b0e030e26379cbdfa2dd7d80b7fd35d3d3dee9cc2e55d56f55` | 一致 |
| insight `run-summary.json` | `245ebeb3…` → `245ebeb314b44c95a6c0d68dcb915820508de099b3005ac9d35f7f9993306b18` | 一致 |
| insight `wal-refs.json` | `c03aa8a6…` → `c03aa8a6faea7dceed455bce08b50802d4c0bfb7e6de36552886c034d1c782ad` | 一致 |
| `parent-edge-probe.json` | `fa32cae3…` → `fa32cae3b29556b8e776195265b7f9c17fc68b96f6d47efe46aa911a419e797b` | 一致 |
| `parent-ao-probe.json` | `a54b8950…` → `a54b8950e7c725c232c59fe81992d7e91d3ab7c0b1ebd60d3a4691b7788eff09` | 一致 |
| K2 journal / WAL / checkpoint / lock | 稿掲載hash → 指定repo外path不在 | 再計算不能 |
| journal source hash 2件とproposal raw hash | `[false,false]` → 親JSON内の2値はいずれも独立再計算したproposal hashと異なる | 保存されたprobe内では一致、journal実物は未確認 |
| canonical hash のcampaign全域不在 | 不在 → campaign自体が不在、収録手順にも全域検索なし | 独立確認不能 |
| v2 lock内 `trial` | inner JSON内 → 実物lock不在。callerとcodecの構造的不整合はコードで確認 | 実物は未確認 |

## 見落とし carrier の探索結果

指定の `proposal_sha256|initial_proposal|provenance` を `orchestrator/campaign/*.py` で検索した。**稿に無い carrier はあった**。所見2の supervisor proposal 保存、trigger source-preimage 保存、その照合 consumer が該当する。

ただし、次を区別する必要がある。

| 候補 | 保存・束縛するもの | 本件での限界 |
|---|---|---|
| `p3_autonomous_workload_trial.py` | proposal JSON、generationのharness outcome、arm経路のproposal path/hash | trigger系列。base precursorの閉包実績ではない |
| `p3_s4_loop_trigger_gating.py` の source-preimage | proposal raw hashを名前に持つmaterialized source preimage | proposal JSON自体ではない。opt-inで、検疫拒否・dry-passより後の経路 |
| `autonomous_trial_completeness.py` | proposal・provenance・attempt・WAL等の照合 | consumerの存在と、本件の現物が閉じることは別 |
| `p3_b4_material_report.py` / raw producer | registry宣言値とartifactの転記整合 | 実campaign precursorからの出所を追加しない |
| sort oracleの `proposal_sha256` | oracle側proposalのhash | B-4 proposal document identityと同一とはいえない |
| knowledge provenance | knowledge manifest・source群 | proposal documentと走行の辺を閉じない |

**本件のbase precursorについて、両端を結ぶ未記載の現存証拠は確認できなかった。** 一方、module名に snapshot / receipt が無いことだけでは producer 不在の十分な証拠にならない。B-4参照fieldの構築点も照合した範囲では、実祖先から構成するproduction producerは確認できず、自己検査用fixtureとは区別できた。

## 照合して一致を確認した範囲

- 必読射影17 fileはすべて読めた。書き込み・commit・push・pytest・build・測定は行っていない。
- `canonical_b4_proposal_sha256` は receipt keyを除いたdocumentを `attempt_registry_core.canonical_json_bytes` でhashする。親probeもこの関数を直接呼ぶ。`require_b4_proposal_registry_binding` はregistryの `initial_proposal_sha256` とexact比較する。
- proposalを `implementation` だけに縮めればコード片の束縛は増えるが、上記B-4 identityの代わりにならない。走行を `build_attempt_id` と読んでも、proposal canonical hashやwhiteboardとの対応は自動では得られない。
- `diffq_variant_id` はgenome・implementation（指定時はgrammar versionも）から導出される。`auditor_diff_digest` はworking_diffのhashで、proposal JSONのhashではない。
- D39 決定3とwhiteboardの5 fieldは一致する。archiveの2026-07-09(3)はit2によるit1のWAL再利用を明記し、2026-07-10(2)はsortのdry-passによるcounter消費を明記する。単純な行番号順の結合は支持できない。
- D2100の12不足fieldはcallerの静的分類と一致する。D2120 項5は、対応証拠を調べた後のcarrier別裁定を明示的に許す。
- D1936 項8との線引きを未裁定の提案として返すことは妥当。αを今回実装済み・承認済みとする記述は無い。D39を変更しないαの方向はなお合理的だが、所見2の先例を含めて根拠を限定する必要がある。
- D2150 項2はB-4本走のtagを `pegasus` と確定している。旧6 variantの `linux-baremetal` とは一致せず、§4.2(3)の不適合判断は支持される。reps候補5の承認済み扱いはできない。
- D1483の記入順序、D2120のbootstrap定義延期を本waveで変えない扱いは整合する。
- callerの `lock.get("trial")` とv2 codecの構造は不整合。codecの実fileは **`orchestrator/campaign/campaign_lock.py`** で、`campaign_lock_codec` はimport alias。探索した同名 `campaign_lock_codec.py` は不在だった。
- 旧3 campaignの閉包不能は赤0件だけを根拠にしていない。§8はK2をB-4供給源とせず、親probeの作成主体も開示している。「失われた」としない限定も適切である。

## GO / NO-GO

**NO-GO。現稿のまま凍結することは勧めない。**

must-fixは次の3件。

1. 裁定2の設定一致案から `reps`・workload全体が落ちる点を訂正する。
2. 未記載carrierを追記し、不在断定をB-4のbase precursor経路へ限定する。
3. loop_stateの `iteration` 出現0という誤記と、その根拠の射程を訂正する。

いずれも文書訂正で対応できる。本waveでcarrier・台帳・gate・testを作る必要はない。

## 総括

旧3 campaignの数値・全14 hash・commit refは一致した。
「本件の現存資料では3辺が閉じない」という限定された結論は支持する。
ただし、現行carrier全体への不在断定には探索漏れがある。
裁定2の設定比較案は完全なPerfConfigを覆っていない。
K2のrepo外実物は本レビュー環境では不在で、親観測から独立に再確認できなかった。
上記3 must-fixを直し、関数同一性・祖先の択一・観測限界も明確にしてから返すべきである。