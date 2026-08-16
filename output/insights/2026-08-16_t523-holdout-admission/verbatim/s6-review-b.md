### 所見 1
- severity: must-fix
- 攻撃シナリオ: caller が公開済み `issue_holdout_observation_admission` に実 freeze と同形の合成 dict を渡して token を発行し、その token で rr80 の `run_once` を繰り返す。cell claim、ledger、attempt ticket は一度も通らない。
- 根拠: `orchestrator/holdout_observation.py:136-150` は authority 検証を caller の責任に置き、`orchestrator/holdout_observation.py:191-217` はその未検証 dict だけで identity token を発行する。`orchestrator/calibrator/runner.py:417-438` は identity token だけ確認して subprocess へ進む。実際に `orchestrator/tests/test_holdout_observation.py:23-50` は合成 freeze から token を発行している。
- 成果物影響: 台帳外で得た rr20／rr80 の反復値を選別でき、下流が台帳を検査しない非主張範囲と組み合わさると、certified 選択やレポートが台帳内測定と区別できない。
- 提案: raw issuer を公開 API から外し、durable ticket 消費が返す非偽造 capability を持つ場合だけ observation token を発行する。合成 freeze から直接発行できない負例を追加する。

### 所見 2
- severity: must-fix
- 攻撃シナリオ: token 無しで `--ycsb_rratio=+80` または `--ycsb_rratio=080` を `run_once` に渡す。分類器は文字列 `"80"` と一致しないため非保護と判定するが、CCBench 側では `uint64` の 80 として解釈され、holdout 測定が起動する。
- 根拠: `orchestrator/holdout_observation.py:154-182` は flag 名しか正規化せず、値を raw 文字列のまま `_NEUTRAL_BY_RATIO` と照合する。`external/ccbench/include/ycsb.hh:22-25` は `ycsb_rratio` を数値型 `DEFINE_uint64` として定義し、`external/ccbench/cc/silo/ycsb_silo.cc:24-27` が gflags で解釈する。`orchestrator/calibrator/runner.py:417-438` は分類後その raw argv をそのまま spawn する。
- 成果物影響: 字句だけ異なる rr20／rr80 が admission 無しで観測され、一回性台帳の受理集合外に holdout 値が増える。
- 提案: `ycsb_rratio` を gflags の型意味論に合わせて整数へ正規化してから分類するか、canonical decimal 以外を fail-closed に拒否する。`+80`、`080`、境界値の負例を追加する。

### 所見 3
- severity: must-fix
- 攻撃シナリオ: fresh campaign が 12 cell の claim を取得した直後、環境 attestation、reservation、clean scan、perf preflight、run directory 作成のいずれかで失敗する。測定も manifest も無いのに claim は残り、次の fresh run は拒否される。run directory／journal が無ければ resume にも入れない。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:4312-4322` は後続 preflight より前に reservation を取得し、環境検査は `orchestrator/campaign/s8b_floor_campaign.py:4329-4387`、run directory 作成は `orchestrator/campaign/s8b_floor_campaign.py:4457-4475` まで後ろにある。claim は `orchestrator/campaign/s8b_holdout_admission.py:584-614` で不可逆な `O_EXCL` 作成となる。manifest 無しの空 journal は `orchestrator/campaign/s8b_floor_contract.py:454-458` で resume 不可である。
- 成果物影響: holdout を一度も測っていない通常の起動失敗だけで全 cell が恒久拒否され、8b floor の result／台帳を生成できなくなる。
- 提案: cell claim より先に durable な resumable run-intent を作り、失敗後に同一 run を復元できるようにする。外部 seam より前という順序は維持しつつ、claim 後の全失敗点を resume 可能にする境界テストを追加する。

### 所見 4
- severity: must-fix
- 攻撃シナリオ: 現在唯一許可される `--mode pilot` を canonical protocol で実行する。pilot は cell key を消費するが artifact は refreeze 不適格である。その後 official gate が解除されても、mode を含まない同じ key のため official fresh run は拒否される。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:315-325` と `orchestrator/campaign/s8b_floor_campaign.py:5292-5299` は official を無条件拒否して pilot のみ許可する。一回性 key は `orchestrator/campaign/s8b_holdout_admission.py:349-361` に mode を含まず、mode は claim の証跡にしか入らない `orchestrator/campaign/s8b_holdout_admission.py:578-581`。pilot result は `orchestrator/campaign/s8b_floor_campaign.py:4771-4776` で `eligible_for_refreeze=False` になる。
- 成果物影響: 現在実行可能な正規 CLI を一度使うだけで、将来の certified floor 候補を生成する official 受理集合が空になる。
- 提案: canonical holdout に対する pilot 実測を拒否するか、「pilot が official の一回性を消費する」ことを明示した不可逆確認を要求する。少なくとも現在の「pilot のみ実行可」という案内は安全な起動経路へ変更する。

### 所見 5
- severity: must-fix
- 攻撃シナリオ: 既存 claim／ledger から公開されている `campaign_run_id`、`run_relpath`、manifest hash を読み、実 journal が無くても `resume=True, journal_exists=True` を渡す。claim 比較を通して cell admission を再発行し、未消費の planned／retry ticket を利用できる。
- 根拠: `orchestrator/campaign/s8b_holdout_admission.py:486-491` は journal の実体でなく caller の bool だけを検査し、`orchestrator/campaign/s8b_holdout_admission.py:598-604` は claim 内容一致だけで resume を許す。`orchestrator/campaign/s8b_holdout_admission.py:701-747` は渡された manifest hash が ledger と一致すれば token を再発行する。`orchestrator/tests/test_s8b_holdout_admission.py:216-230` も journal を作らず bool だけで resume 成功を構成している。
- 成果物影響: 「同一 run identity を証明した resume のみ」という台帳の受理集合が、公開値を再提示できる caller 全体へ広がり、未認可の追加 holdout observation が可能になる。
- 提案: bool と hash の自己申告を廃止し、canonical run directory の実 journal／manifest bytes、状態機械、terminal 状態を admission 層自身が検証する。完了済み run と retry trigger 不在の ticket 再発行も拒否する。

### 所見 6
- severity: must-fix
- 攻撃シナリオ: `test_measure_fn_closure_passes_contract_numactl_to_measure_point` を収集すると、public pilot entrypoint に `probe_fn` と `perf_preflight_fn` を渡すため、対象の default measure closure に到達する前に必ず拒否される。
- 根拠: `orchestrator/tests/test_s8b_freeze_io.py:367-398` は public `floor.run_campaign` へ両 seam を注入する。一方、`orchestrator/campaign/s8b_floor_campaign.py:4160-4170` は mode に関係なくその注入を拒否する。Unit 2 側の他テストは `orchestrator/tests/test_s8b_floor_campaign.py:380-406` の private helper へ移されたが、この consumer は更新されていない。
- 成果物影響: 従来受理されていた pilot integration 経路は result を生成せず、contract の `clocks_per_us`／`numactl` が default measurement へ届く保証テストも失われる。
- 提案: 当該テストを private core と明示的な test admission fixture へ移し、public production rejection の期待値は別テストに限定する。

### 所見 7
- severity: should
- 攻撃シナリオ: `orchestrator/campaign/new_producer.py` に `def launch(exe): subprocess.run([exe, "--ycsb_rratio=80"])` を追加する。新しい direct producer だが、引数名が `binary` でないため inventory に一件も追加されず、閉集合テストは緑のままになる。
- 根拠: `orchestrator/tests/test_ccbench_spawn_sites.py:62-77` の追跡は名前 `binary` だけを特別扱いする。`orchestrator/tests/test_ccbench_spawn_sites.py:80-136` は `_references_binary` が真の call だけを候補に数えるのに、`orchestrator/tests/test_ccbench_spawn_sites.py:144-151` はその不完全な集合を「closed」「every throughput spawn」と主張する。
- 成果物影響: 将来の rr20／rr80 producer が台帳と gateway を迂回しても meta-test が検出せず、台帳外の holdout 値が選択材料へ混入し得る。
- 提案: parameter 名に依存せず subprocess sink を全件列挙してから CCBench 非該当を明示除外する方式へ反転し、`exe`、attribute、hardcoded path の負例 fixture を追加する。

### 所見 8
- severity: should
- 攻撃シナリオ: canonical ledger から observation token への結線を壊しても、実 artifact E2E は injected measure を使うため `run_once` gateway を通らず、gateway テストは合成 freeze の公開 issuer を直接使うため、双方が独立に通り得る。
- 根拠: 実 protocol／freeze を使う E2E は `orchestrator/tests/test_s8b_floor_campaign.py:5812-5827` で外部 `measure` を注入する。wrapper は `orchestrator/campaign/s8b_floor_campaign.py:3267-3274` で default measure のときだけ observation token を下流へ渡す。対して gateway 正例は `orchestrator/tests/test_holdout_observation.py:23-50` と `orchestrator/tests/test_holdout_observation.py:189-198` の合成 freeze／直接 issuer である。
- 成果物影響: canonical authority → cell claim → ledger → ticket 消費 → `run_once` という中心 proof chain が切れても受入テストが検出せず、台帳と実測値の参照関係が偽陽性になる。
- 提案: 実 protocol／freeze を入れた一時 clone で real reservation、finalize、ticket 消費を行い、その observation token を subprocess spy 付き `run_once` まで通す単一 E2E を追加する。

## 総括

NO-GO。公開 issuer と数値 flag の字句別名により、「台帳を通さず holdout を実測できない」という中心保証が成立していない。  
また、claim が resumable 状態より先に不可逆消費されるため、未測定の通常失敗で campaign が詰む。現在唯一許可される pilot は将来の official 一回性も消費する。  
実 protocol の canonical bytes は一致し、`n_sessions=8` と `retry_slots_per_cell=2` に対する 10 tickets/cell は実 schedule と一致した。T-524／T-525 の実質実装は確認しなかった。  
静的検査のみであり、pytest の緑は主張しない。既知の CLI 赤は所見に含めていない。