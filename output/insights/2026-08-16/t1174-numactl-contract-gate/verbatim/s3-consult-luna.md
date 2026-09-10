## 所見

### 1. A1〜A3から「不一致側の純増検出力 = 0」は一般化できない

- 所見: brief の結論は「現行の fresh authorization かつ同一 snapshot」の範囲に限られる。
- 根拠: 実測は A1 が gate、A2 が `execution_guard`、A3 が通過の各 1 点だけ (`brief.md:48-58`)。静的にも guard は `tuple(numactl) != registered.numactl` を拒否する (`execution_guard.py:124-135`)。
- 成立条件: `authorization_contract` と `lookup(env_tag)` が同一 current contract であること。未知 `env_tag`、古い receipt、将来の authority 更新では成立しない。
- 成果物への影響: gate を「純増防壁なし」と固定すると、実際には別 authority 間の過剰拒否や例外順序変更を見逃す。
- 推奨対応: 「fresh snapshot 内では純増なし」と限定し、古い receipt、未知タグ、list/tuple、Pegasus 空 tupleを別 vector として登録する。

### 2. 古い `AuthorizedContract` と新しい registry の不一致は、条件付きで過剰拒否になる

- 所見: `REGISTRY` と `authorize()` は通常同じ snapshot だが、guard は保持された receipt の契約を検証し、current snapshot との再照合はしていない。
- 根拠: snapshot の共有は `env_contract.py:576-586, 615-668`。一方 `_contract_from_authorization()` は receipt と `GENERATIONS` を検証するだけである (`execution_guard.py:44-104`)。テストの `_refresh_certified_writer_authority()` は毎回新しい receipt へ更新する (`test_campaign.py:102-106`)。
- 成立条件: 同一 `env_tag` の current contract だけを新しくし、古い authorization と `_AUTHORIZED_CONTRACTS` を保持する場合。現行 production では更新経路が限定的で、Pegasus g1/g2 の `numactl` も同じ空 tuple (`env_contract.py:245-273`) なので、現時点の実機到達は未確認。
- 成果物への影響: guard が受理する旧契約値を gate だけが拒否し、承認済み入力を過剰拒否する。
- 推奨対応: 古い receipt を保持したまま current snapshot だけを差し替える synthetic positive test を追加する。これを受理するのか、stale receipt として拒否するのかは実装前に裁定する。

### 3. P2 の AST 検査は有効な回帰検査だが、現在の defect 検出ではない

- 所見: 現在は verify と bench が同じ `numactl` 変数を渡すため、検査対象の性質は構造的に真である。
- 根拠: verify は `pipeline.py:1189`、bench は `pipeline.py:1123-1128,1225-1227`。既存 AST 検査は COMMIT の構文位置を固定する (`test_campaign.py:6895-6950`)。
- 成立条件: call-site の式を `None`、別名、条件式へ変える mutation には効く。`numactl` の束縛自体を変える mutation、`_run_bench`・`_run_trace` 内部の変換、実際の `measure_point` 内部には効かない。
- 成果物への影響: 「将来の refactor を防ぐ構造検査」としては価値があるが、「現行の launch prefix 検査が発火する」と記録すると恒真な安心になる。
- 推奨対応: P2 は採用してよい。ただし主張を call-site regression に限定し、mock の verify/bench 実引数記録または別層の検査を併記する。

### 4. 正例・負例の被覆は計画に含まれるが、古い authorization の正例がない

- 所見: Pegasus の `numactl=()` 正例と、`None`・別 prefix の負例は plan に含まれている。
- 根拠: `plan.md:40-44`、既存の非空 list 正例は `test_campaign.py:7184-7204`。契約上、空 tupleは解決済み prefix である (`env_contract.py:92-100`)。
- 成立条件: Pegasus 用の実際の `AuthorizedContract` を渡し、S2 の第 2 trace が実際に `()` で走ったことまで検証すること。
- 成果物への影響: 空 tupleを誤拒否する狭めすぎは検出できる。別 prefixを受理する広げすぎも検出できるが、stale receipt の過剰拒否は検出できない。
- 推奨対応: 正例は `certified` だけでなく第 2 trace の prefix と authorization 通過を確認する。stale authority は別の裁定対象にする。

### 5. 既存 test は guard 由来の赤を緑にしてしまう

- 所見: `except ValueError: pass` は gate、`CertifiedWriterAuthorizationError`、`EnvContractError` を区別しない。
- 根拠: test は `test_campaign.py:7252-7268`、guard 例外は `ValueError` の subclass (`execution_guard.py:40-42`)。gate は guard より前 (`pipeline.py:693-708`)。
- 成立条件: gate を削除しても、`numactl=None` または別 prefix は guard が拒否するため、現行 test は緑になり得る。plan のメッセージ検査は赤にできるが、実際の拒否主体は依然 guard である。
- 成果物への影響: gate mutation を「検出した」と誤記し、実効 gate が `execution_guard` である事実を隠す。
- 推奨対応: gate 呼出し前後の到達を識別できる検査を追加し、gate削除 mutation は独立防壁の mutation score に算入しない。未知 `env_tag` では `lookup()` が先に `EnvContractError` を出す (`env_contract.py:706-713`)ため、例外型の変更も明示的に固定する。

## 変異候補の帰属判定

| 変異候補 | 判定 | 実効的な赤の理由 |
|---|---|---|
| 旧式 `not numactl and qualification_policy is None` へ戻す | 登録可 | Pegasus 空 tuple正例が gate で失敗 (`pipeline.py:693-701`) |
| `!=` を `==` にする | 登録可 | 正しい linux prefix が gate 自身の ValueError で失敗 |
| `tuple(numactl)` を外す | 登録可 | list 表現を gate が誤拒否し、guardには到達しない |
| gate を削除または `False` 化 | 先取りされる | 実際に拒否するのは `execution_guard.py:125-135`。メッセージ検査で赤にはできるが、独立 gate の赤ではない |
| gate無効化と guard比較削除を同時に行う | 帰属不能 | 複合変異であり、どちらの欠落が原因か分離できない |
| `lookup` を `env_contract.numactl` に変更 | 登録可 | `env_contract=None` の正例で gate の AttributeError が出る |
| fullscale verify の第3引数を変更 | 登録可 | P2 AST検査に限定して登録可 |
| screening bench の第4引数を変更 | 登録可 | P2 AST検査に限定して登録可 |
| 通常 bench の第4引数を変更 | 登録可 | P2 AST検査に限定して登録可 |
| verify/bench 3箇所を同じ誤式へ変更 | 登録可（構文限定） | `Name("numactl")` pin が落とす。ただし upstream の値変更は捕捉しない |
| `qualification_policy is None` を再追加 | 帰属不能 | qualification 前段に隠れる等価変異で、観測可能な mutation ではない |
| runtime assert の追加 | 帰属不能 | 同じ変数の比較なら恒真。`python -O` でも消える |

## brief 自身への反証

- A1 は「Pegasus の空 tupleを旧 gateが誤拒否する」ことを示すだけで、A2 は 1 種類の不一致を後段 guard が拒否したことを示すだけである。
- A1〜A3は、未知タグ、古い receipt、authority 更新、screening bench、実際の prefix consumerを覆わない。
- `REGISTRY` と `authorize()` が同じ snapshotを使うという通常系の事実から、保持済み `AuthorizedContract` まで current contract と一致すると推論するのは誤りである。
- 反対に、P2 は現在失敗しなくても将来の call-site refactor を止める回帰検査としては成立する。既存の COMMIT AST 検査と同型だが、検出対象は「現行 defect」ではなく「将来の構造 drift」である。

## 裁定パッケージ候補 (scope 外の real 所見)

1. stale `AuthorizedContract` を承認済み正例として扱うのか、stale receipt として guard で拒否するのか。必要なら `env_contract.py` と `execution_guard.py` の current-snapshot 再束縛、および専用テストを別 scope に出す。
2. P2 は `pipeline.py` の call-site しか保証しない。`_run_trace` (`pipeline.py:963-966`)、bench の `measure_point` (`pipeline.py:450-463`)、実際の Pegasus launch は別層である。
3. 実機 campaign は brief の裁定どおり T-1112 の別 waveであり、本 waveの受入証拠にはできない。今回の受入は bounded local の単体・mutation・acceptance までに限定される。

## 総括

- A1〜A3から純増検出力ゼロを一般化するのは不成立で、fresh snapshot 内の条件付き結論に留めるべきである。
- gate削除の赤は後段 `execution_guard` に先取りされ、現行 test はそれを緑にしてしまう。
- P2 AST検査は将来の call-site driftには効くが、現在の恒真性や実際の launch consumerまでは証明しない。
- Pegasus空 tuple正例と非空・None負例は計画にあるが、stale authorization正例が欠けている。
- `lookup()`導入により未知タグの例外型と発火順も変わるため、明示的な裁定とテストが必要である。
- stale authority と実機・consumer層は本 waveのscope外の裁定パッケージ候補である。
- pytestは実行しておらず、以上は指定範囲の静的検査とbrief記載の実測に基づく。