## 所見

### 1. 承認外の入力まで受理集合が広がる

- **所見:** 変更後に新しく局所 gate を通る集合は、正確には「S2 の Pegasus `()`」だけではない。`extra_correctness` が1件以上、`qualification_policy is None`、`numactl` が exact `[]` または `()`、かつ active contract の `numactl == ()` である全入力である。現在は Pegasus だけだが、任意の追加 workload、複数 workload、将来追加される空 prefix 環境も含む。
- **根拠（静的実測）:** 全 `extra_correctness` は内容を検査せず `fullscale_isolated=True` になる（`pipeline.py:690-694`）。S2 形状への exact 束縛は qualification にしかない（`pipeline.py:673-675`）。現 registry では Pegasus だけが `numactl=()`、linux-baremetal は非空である（`env_contract.py:245-250,283-304`）。提案式は exact list/tuple を tuple 化する（`plan.md:7-8`）。
- **成立条件:** 後段まで certified になるには、Pegasus の有効な authorization、正しい `env_tag`・clock、`env_contract=None` または authorization と同値の selector、成功する build/verify が必要。通常の `loop.run_campaign` は canonical S2 を組み立てる（`loop.py:138-144`）が、`evaluate()` の直接 caller は任意の tag/workload を渡せる。
- **成果物への影響:** Pegasus で `[(任意タグ, 軽量または別 workload)]` と `[]`／`()` の組が、従来の早期拒否を越えて certified になり得る。これは「Pegasus の canonical S2 だけ」という承認範囲を超える。
- **推奨対応:** 空 prefix の例外を canonical S2 形状または明示的な fullscale policy に束縛する。`[]` と将来の空 prefix 環境を承認対象に含めるか段4で個別裁定し、非 S2 workload、複数 extra、空 list、別の空契約環境を負例として事前登録する。

### 2. 空 list を許すと、照合後に実 launch prefix を変更できる

- **所見:** 提案式は `numactl=[]` を通す一方、照合後に immutable snapshot を作らない。呼び手が保持する list を別 thread から変更すれば、契約検査後の S2 verify または bench が未承認 prefix で起動できる。これは実 launch に対する fail-open である。
- **根拠（静的実測）:** execution guard は比較時に `tuple(numactl)` を作るだけで元の list を凍結しない（`execution_guard.py:125-135`）。その元オブジェクトを S2、screening bench、通常 benchへ渡す（`pipeline.py:1123-1128,1189,1225-1230`）。実 argv への copy は各起動時点で行われる（`pipeline.py:362-364`、`calibrator/runner.py:371-380,533-543`）。
- **成立条件:** Pegasus の有効な非 qualification 呼出しで空 list を渡し、gate・authorization 後から起動前までに alias を変更する。変更が両 run 前なら双方が契約外、両 run の間なら verify と bench が相互不一致になる。別 thread による変更可能性は推論だが、コード上の共有可変 alias は静的に確認できる。
- **成果物への影響:** P2 の AST が全 call-site を `Name("numactl")` に固定しても、値の時点一貫性は保証されず、契約外配置の実行が certified まで進み得る。
- **推奨対応:** 検査直前に exact str 要素を持つ immutable tuple へ一度だけ正規化し、その snapshot を gate、authorization、verify、bench の全てへ渡す。空 list 自体を承認外とするなら exact tuple のみに狭める。

### 3. P2 の AST は実際の launch prefix を保証しない

- **所見:** 提案 AST は `evaluate()` 内の3 call-site しか固定せず、「実際に subprocess へ届く prefix」という D36 の性質を閉じていない。検出力は call-site 変異に限れば本物だが、成果物が主張する保証には不足する。
- **根拠（静的実測）:** verify は `_run_one_pass`、`_run_trace` を経由する（`pipeline.py:951-966,333-370`）。bench は `_run_bench`、`measure_point`、`run_once` を経由する（`pipeline.py:405-462`、`calibrator/runner.py:474-543`）。例えば `pipeline.py:454,462` だけを `numactl=None` にする変異、または `pipeline.py:362` で prefix を捨てる変異は、`plan.md:31-36` の AST を生存する。
- **成立条件:** helper の forwarding を将来変更する場合。既存 multipass test は fake `_run_trace` が受けた値を検査する一方、fake `measure_point` は `numactl` を記録しない（`test_campaign.py:7105-7109,7136-7140,7184-7200`）。
- **成果物への影響:** `plan.md:64-66` の mutation kill 帰属は外側3箇所についてのみ成立する。「D36 要求を機械保証した」と記録すると過大主張になる。
- **推奨対応:** AST は補助防壁として残し、同じ評価で fake `_run_trace` と fake `measure_point` が受け取った immutable tuple を比較する動的配線テストを追加する。screening／通常 bench と `record_rep_returncodes` 両分岐を覆う。既存 COMMIT AST 前例（`test_campaign.py:6895-6950`）は閉じた構文位置の検査には転用できるが、複数 helper にまたがる実 argv の証明にはそのまま転用できない。

### 4. lookup と古い authorization の分裂は現状到達不能だが、設計上の破断点になる

- **所見:** 親が示した「古い AuthorizedContract は guard が受理し、新 lookup だけが拒否する」状態は、現在の公開経路では到達できない。ただし将来、registry snapshot だけを refresh する機構を足すと直ちに成立する。
- **根拠（静的実測）:** `REGISTRY` と `authorize()` は同じ process-local snapshot を使う（`env_contract.py:576-586,615-644`）。test 用 cache clear と fork 後 reset は authorization cacheも同時に空にする（`env_contract.py:551-570,589-598`）。guard は receipt が `_AUTHORIZED_CONTRACTS` の現行 identity であることを要求する（`execution_guard.py:65-69`）。`_refresh_certified_writer_authority()` が各 test 前に必要なのは、古い global receipt がこの検査で拒否されるためである（`test_campaign.py:102-112`）。
- **成立条件:** 現在は private global を片側だけ改変しない限り不成立。将来、authorization cache を失効させず active snapshot だけを更新する refactor が入れば、prefix が変わる世代では gate だけが過剰拒否し、prefix が同じ世代では古い receipt と新 lookup の分裂が見えなくなる。
- **成果物への影響:** `plan.md:17,25` の「同じ current contract へ収束する」は現行 lifecycle を前提とした条件付き主張であり、一般的不変条件ではない。
- **推奨対応:** guard が返した `authorized_contract` を単一権威にするか、snapshot 更新と authorization 失効の原子性を明示的に固定する。現状では不可能状態を作る正例テストは追加せず、supported cache refresh 後は古い receipt が拒否され、fresh authorization と `lookup()` が同一 contract になる負例・不変条件テストを置く。

### 5. 未登録 env_tag は fail-closed だが、例外型と検査順が変わる

- **所見:** `env_contract=None`、selector 不一致、未登録 env_tag のいずれにも end-to-end の fail-open はない。ただし未登録 env_tag と fullscale の組は、従来の `CertifiedWriterAuthorizationError` より手前で `EnvContractError` へ変わる。
- **根拠（静的実測）:** `env_contract=None` は guard で許可されるが authorization の実行値照合は常に走る。selector 不一致は `execution_guard.py:160-169` で拒否される。未登録 tag は `lookup()` が `EnvContractError` を送出する（`env_contract.py:706-713`）。これは `ValueError` だが `ExecutionGuardError` ではない（`env_contract.py:46`、`execution_guard.py:36-41`）。
- **成立条件:** `evaluate()` を直接、fullscale extra、truthy な prefix、未登録 env_tag で呼ぶ場合。通常の `run_campaign` と screening driver は evaluate より前に guard を呼ぶため、この型変更には到達しない（`loop.py:61-74,130-133`、`screening_driver.py:144-162`）。
- **成果物への影響:** `test_campaign.py` の認可テスト群は extra を渡さず、既存 extra 負例は広い `except ValueError` なので、現存 node の期待値を直接壊すものは見当たらない（`test_campaign.py:2699-2937,7252-7268`）。壊れる主体は `evaluate()` の直接 callerで `ExecutionGuardError` を捕捉するコード、および例外クラス名を診断に使う consumer である。偽造 receipt と未登録 tag が併存すると registry エラーが receipt 検査を覆い隠す。
- **推奨対応:** 認可を先に行って返却 contract を gate に使うか、lookup 失敗を既存の認可例外 taxonomy へ包む。未登録 fullscale の exact exception と「sink 書込みなし」を固定するテストを追加する。

### 6. qualification では新 gate は完全に先行検査へ含意される

- **所見:** `qualification_policy is not None` の経路では、提案 gate は新しい防壁にならない。現状の受理結果に矛盾はないが、「契約一致」の意味は qualification が exact tuple、提案 gate が list/tuple 正規化で異なる。
- **根拠（静的実測）:** qualification は先に exact Pegasus contract、exact env 値、`type(numactl) is tuple`、canonical S2 形状を要求する（`pipeline.py:655-678`）。これを通れば後続の `lookup(env_tag).numactl` 比較も必ず通る。空 list を拒否する既存テストもある（`test_t126_qualification_driver.py:460-493`）。
- **成立条件:** `qualification_policy` が non-None の全呼出し。invalid 入力は新 gate に達せず、valid 入力では新 gate が恒真になる。
- **成果物への影響:** `qualification_policy is None` の再追加は現状では等価変異という plan の判定は正しい。ただし新 gate を qualification の exact 検査の代替や追加検出力として数えてはならない。
- **推奨対応:** qualification 側の exact 検査と空 list 負例を維持し、重複だから削除できるとは記録しない。二重 lookup も保証として数えない。

### 7. legacy verify は文字どおり bench と異なる prefix で走る

- **所見:** legacy verify は bench と異なる配置で verify する経路そのものである。ただし D36 本文は「S2 verify run」だけを対象にしており、legacy の例外は D36 とは整合する。brief 冒頭の「verify の launch prefix が bench と同一」という無限定表現とは整合しない。
- **根拠（静的実測）:** legacy は常に `_run_one_pass(..., None)`、fullscale は `numactl`、bench も `numactl` を受ける（`pipeline.py:1156-1191,1123-1128,1223-1230`）。D36 決定4-4は明示的に S2 verify run だけを規定する（`docs/decisions.md:909-918`）。
- **成立条件:** linux-baremetal のような非空 contract で bench を走らせれば、legacy の実 prefix は空、bench は非空となる。Pegasus では `None` と `()` の実 argv はどちらも空なので、sentinel は異なっても実配置は同じ。
- **成果物への影響:** T-1174 裁定を全 verify へ読むなら plan は未実装である。D36 の S2 限定として読むなら plan の fullscale 限定が正しく、brief の一般化だけが過大である。
- **推奨対応:** 段4で裁定文を「S2／fullscale verify の launch prefix」に限定するか、全 verify を意味したのか明示する。legacy を暗黙に変更せず、legacy は None、S2 と bench は同じ immutable contract prefix、という二つの性質を別々に固定する。

## brief 自身への反証

A1/A2/A3 は3点の例であり、「不一致側の純増検出力は0」という無条件の一般化を実測していない。A1 は `()` だけで `[]`、任意 extra、将来の空契約環境を扱わず、A2 は単一の非空 mismatch だけで未登録 tag、authority 世代差、検査後の list 変更を扱わない（`brief.md:48-58`）。

静的には「同一 process snapshot、有効な current authorization、immutable な引数、guard が必ず実行される」という条件下なら、execution guard が型と tuple 等値を検査するため、不一致に対する end-to-end の純増拒否は0である。この限定命題は支持できる。一方、局所 gate の発火順・例外 taxonomy・TOCTOU・承認された空 prefix の適用範囲まで含めた無条件命題は反証される。

P2 の方向自体は妥当だが、「唯一の純増検出力」と呼べるのは外側 call-site の構文変異だけである。実 launch の保証には helper forwarding と値の不変性が欠けている（`brief.md:63-70`）。

古い authorization の過剰拒否については、現行の supported lifecycle では refuted である。`_refresh_certified_writer_authority()` は古い receipt が有効だからではなく、cache clear 後には無効になるため必要である。片側だけを更新する将来 refactor には real な設計リスクが残る。

## 所見ゼロなら、ゼロである根拠

該当しない。重大2件を含む7件の所見がある。

## 総括

- plan のまま段5へ進めるべきではない。空 prefix 例外の対象が canonical Pegasus S2 に閉じていない。
- 新規通過集合は `()` だけでなく `[]`、任意の extra workload、将来の空 prefix 契約を含む。
- 特に可変 list は照合後に実 prefix を変更できるため、immutable snapshot が必須である。
- P2 AST は外側 call-site 変異には効くが、helper を経た実 argv の同一性を保証しない。
- qualification、selector 不一致、未登録 tag は fail-closed のままだが、未登録 tag の例外型と順序は変わる。
- stale authorization の過剰拒否は現状到達不能だが、権威を二重化する設計は将来 refactor に弱い。
- legacy は D36 の対象外であり、T-1174 裁定を S2 限定とするか段4で明文化する必要がある。
- Web 検索・pytest・実機実行は行っておらず、結論は限定した静的検査に基づく。