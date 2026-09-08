## 攻撃した仮説と結果

| 仮説 | 判定 | 結果 |
|---|---|---|
| 欠落は K2 env seam だけ | refuted | offline third-party 情報が condition gate に届かず、WAL 前で再停止する経路が残る |
| README の duplicate skip が K2 初回を殺す | refuted | K2 は知識水準と manifest digest で別 campaign identity になり、過去 K2 実測も別 output root で terminal 未到達 |
| 変異候補 5 件が単一 nodeid・単一理由 | refuted | 計画どおり逐語 pin を足すと全候補が別の静的検査も赤くする。候補 1 は fixture 次第で生存する |
| 小 harness は新規 test file を要求する | refuted | 既存契約 test に追加でき、自走入口も既存 |
| driver は変更不要 | refuted | 少なくとも condition gate への offline dependency 配線が driver 側で必要 |
| K2 env 四つをすべて必須にする必要がある | refuted | 現行アームでは classification と de-novo は driver の既定値で同じ identity・receipt になる |

## real 所見

1. real: prebuild receipt は condition gate を救わない。これは目的を直接阻害する blocker である。

job body は third-party 3 本を scratch へ複製し、そこで prebuild する (`tools/pegasus/p3_s4_loop_pegasus.sh:421-503`)。driver は receipt を `fetchcontent_options` に変換する (`orchestrator/campaign/p3_s4_loop.py:2331-2353`) が、その情報を使うのは `run_campaign` だけである (`同:1683-1708`)。

その直前に `_require_condition_gate(sub, genome)` が実行される (`同:1679`)。この関数は `source_root` と `genome` しか受けず、cmake/cxx だけで supply arm を起動する (`同:324-347`)。scratch の FetchContent base、source dir 3 本、prebuild receipt は渡らない。

これは仮想リスクではない。親の過去実測でも、全 third-party を offline 供給した最後の試行が `supply=preprocess-failed` で停止し (`output/insights/2026-09-02_t2182-k2-arm-liveness/README.md:63-72`)、同資料が「condition gate の cmake argv には `-D` を足せない」と記録している (`同:85-87`)。README §7 も receipt の到達先を shared measurement pipeline としか述べていない (`tools/pegasus/README.md:337-340`)。

scope 判定: `p3_s4_loop.py` の no-touch 裁定は誤り。まず driver の `_require_condition_gate` 呼出しへ offline dependency 情報を運ぶ必要がある。基盤 API の変更まで必要なら、`condition_meaning_gate.py` は別 wave 所有 (`brief.md:46-47`) なので、本 wave は依存待ちとして目的達成を主張できない。

影響: 放置すると condition gate で例外終了し、WAL の BUILD_START、候補 provenance、stock と異なる identity、compile/identity/correctness の terminal verdict がすべて生成されない。certified 選択・レポート・WAL の受理集合は現状から前進しない。

2. real: 「不足なし」は親の実測から一般化できていない。

README は、初回投入で到達したのが third-party 複製までであり、gflags/glog prologue、prebuild receipt を使った build、attestation、03:00:00 の充足は未実測だと明記する (`tools/pegasus/README.md:370-375`)。driver の `_assert_single_tenant()` も driver 起動後に初めて実行される (`orchestrator/campaign/p3_s4_loop.py:2424-2430`) ため、prebuild で止まった初回投入はこれを実測していない。

また `compute-result.json` の `driver_rc` は driver 専用値ではなく job body 全体の rc である (`tools/pegasus/README.md:375-376`)。これを rc=0/非0だけで terminal verdict の証拠にできない。

scope 判定: これは新しい gate を追加する理由ではない。Pegasus 実投入は本 wave 外だが、実測前に「env seam だけで terminal まで可能」と結論することもできない。

影響: 3 時間不足または single-tenant 拒否なら terminal artifact は生成されず、レポートが「配線済み」を「評価済み」と誤って参照する。

3. real: classification と de-novo まで all-or-none 必須にする P2 は、現行アームの受理集合を不要に狭める。

driver には `reproduction_or_selection` と `false` の既定値がある (`orchestrator/campaign/p3_s4_loop.py:2304-2309`)。現行 run card も同じ宣言である (`output/insights/2026-09-02_t2182-k2-arm-liveness/README.md:32-35,60-61`)。campaign identity に追加されるのは knowledge level と manifest digest だけであり (`orchestrator/campaign/p3_s4_loop.py:1311-1319`)、classification と de-novo は receipt writer に渡るだけである (`同:1321-1326`)。

したがって manifest、coder role、proposal path を指定し、残る二値を driver の既定に任せる入力は、現在の宣言アームと同じ identity・receipt 内容を作れる。プランの四 env 必須化 (`stage2-plan.md:33-46,67-79`) はこの有効入力を shell で拒否する。

scope 判定: manifest、coder role、proposal path の早期整合検査は必要だが、将来変化し得る宣言まで env 化するのは今回の固定 K2 アームを越えた一般化である。明示伝送自体を成果条件にする裁定が無い限り、二つは driver の既定に任せるべきである。

影響: 値や terminal verdictは変わらないが、同一成果物を生成できる安全な qsub 入力が不受理になり、job body の受理集合だけが狭まる。

4. real: 変異事前登録は、厳密には 5 件とも「その nodeid だけが赤」ではない。

プランは `_assert_static_job_contract` に set 検出、非空完全性、proposal 必須、argv 順、driver 展開をすべて逐語 pin するとしている (`stage2-plan.md:149-158`)。したがって計画どおり実装すると、5 変異すべてが期待 nodeidに加えて `test_job_body_static_contract` (`test_p3_s4_loop_job_contract.py:452-453`) も赤くする。

個別判定は次のとおり。

| 候補 | 指定 runner での単一理由性 | 別に赤くなる nodeid |
|---|---|---|
| `-v` を非空検査へ変更 | 条件付き。empty manifest だけを設定する fixture でなければ mutant が生存する | `test_job_body_static_contract` |
| 完全性 `-n` を `-v` へ変更 | 成立 | `test_job_body_static_contract` |
| proposal 拒否を `true` へ変更 | 成立 | `test_job_body_static_contract` |
| manifest/role pair の順序交換 | 成立するが argv 表記だけの検査 | `test_job_body_static_contract` |
| proposal driver から array を除去 | 成立 | `test_job_body_static_contract` と、更新後の `test_registered_fragment_mutants_have_one_static_failure[proposal]` (`同:580-599`) |

候補 1 は特に未確定である。完全 bundle の manifest だけを空にすると、role など別の非空 env が `k2_requested=true` にするため、変異後も完全性検査で拒否される。期待どおり kill するには「manifest だけが設定済み空、他の K2 env は未設定」と fixture を固定する必要がある (`stage2-plan.md:189`)。

影響: 候補 1 が生存すると、設定済み空 manifest が K2 要求として認識されず、proposal が非 K2 identity/schema で走り得る。候補 3 と 5 も K2 bundle を fixtureまたは非 K2 proposal として処理し、成果物の campaign identity と provenance を変える。

## refuted 所見

1. refuted: README の duplicate skip は、通常の K2 初回走行を殺さない。

Pegasus env binding に加えて (`orchestrator/campaign/p3_s4_loop.py:147-161,2383-2393`)、K2 は knowledge level と manifest digest を identity に追加する (`同:1311-1319`)。既存 stock/fixture campaign の terminal record は別 campaign に属する。

過去の K2 生死確認は外部 root `/work/1/SFC/tanab/izanagi-exploration-t2182` を使用していた (`output/insights/2026-09-02_t2182-k2-arm-liveness/README.md:23-35`)。一方 job body は `IZANAGI_EXPLORATION_OUTPUT_ROOT` を unset し (`tools/pegasus/p3_s4_loop_pegasus.sh:39`)、driver は専用 checkout の `output/exploration/campaigns/...` へ解決する (`orchestrator/campaign/layout.py:370-409,589-597`)。さらに過去 K2 は BUILD_START 未到達で terminal record を作っていない (`output/insights/.../README.md:14-19`)。

同じ K2 campaign・同じ candidate を同じ checkout で再実行すれば README の skip は発火する。その回避は fresh な専用 checkout/output root、または terminal 未記録の候補を使うこと。EVIDENCE_ROOT の attempt directoryだけを変えても campaign WAL は変わらない。

影響: 正しい初回投入では certified 選択・レポート・WAL の値は変わらない。

2. refuted: CCBench PIN の検査が欠けているわけではない。

job body は driver の `PIN` を読み、CCBench HEAD と解決済み commitの完全一致を検査する (`tools/pegasus/p3_s4_loop_pegasus.sh:182-212`)。driver も clean/pin を再検査し、isolated worktree を同じ PIN から作る (`orchestrator/campaign/p3_s4_loop.py:2424-2447`)。

影響: PIN 不一致は build 前に拒否され、誤った commit の結果が certified 集合へ混入しない。

3. refuted: output root の unset 自体は欠落ではない。

unset 後は repo-local fallbackが選ばれ (`orchestrator/campaign/layout.py:384-391`)、専用 checkout は AI worktree container でないため exploration layout を作れる (`同:461-482,577-597`)。job body の claim root も同じ repo の Pegasus env rootへ作られる (`tools/pegasus/p3_s4_loop_pegasus.sh:317-320`)。

影響: 過去の外部 K2 rootとは物理的に分離され、初回走行の受理集合を狭めない。

4. refuted: 小 harness のための新規 test file は不要。

既存 `test_p3_s4_loop_job_contract.py` はすでに shell snippet を `bash -c` で実行する資材を持つ (`同:903-999`)。また plain runner `_run()` と `__main__` もある (`同:1297-1303`)。プラン自身も変更対象を既存の job body、契約 test、README の3本に限定している (`stage2-plan.md:206-208`)。

したがって既存 file へ追加すれば、新しい自走 harness fileも acceptance duration ledger の新規 file 登録も不要である。別 test fileを作る実装に変更した場合だけ、両方が必要になる。

影響: 既存 file追加なら certified 選択・レポート・台帳の値は変わらず、台帳更新を理由に scopeを広げる必要はない。

## nit / backlog

- 変異表が挙げる5 nodeidは、現行 test fileにはすべてまだ存在しない。名前は `stage2-plan.md:189-193` にしかなく、現行 fileは `test_p3_s4_loop_job_contract.py:1303` で終わる。段2時点では予定名なので blockerではないが、authorは変異実行前に exact nodeidを収集すべきである。現時点では成果物への直接影響はない。

- manifest が参照する commit `2fa13a...` は過去 run cardに明記される (`output/insights/.../README.md:27-31`)。driver は manifest loaderを repo root付きで呼ぶ (`orchestrator/campaign/p3_s4_loop.py:1285-1293,2372-2374`) が、指定資料だけでは将来の専用 checkoutの object databaseにその commitが存在するか確定できない。欠落時は driver入口で停止するが、実際に欠けている証拠はないため real blockerには数えない。READMEの運用前提として明記する程度でよい。

- pair順交換の変異は argparse上の意味を変えない。放置しても certified 選択、report、receipt、WALの値・受理集合・参照は変わらないため、これは correctness変異ではなく逐語安定性の nitである。

## 総括

job body の K2 argv seamだけでは目的を達成できない。最大の反証は、prebuild receiptとoffline source群が `run_campaign` には届く一方、その前段の condition gateには届かず、過去実測と同じ BUILD_START 前停止が残ることである。このため driver no-touch裁定は撤回し、少なくとも `_require_condition_gate` への offline dependency配線を scopeへ戻すか、別 wave依存として本 waveの完了主張を止める必要がある。

duplicate skip、PIN、output root、新規 test file問題は反証された。変異 matrixは候補1の fixtureを厳密化し、全5件が静的 pinでも赤くなる事実を明記すべきである。pytest・書込み・Pegasus投入は行っていない。