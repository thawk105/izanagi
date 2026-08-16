## 事前登録変異の検証

| ID | 判定 | 落ちる node・行 | 独立検証 |
|---|---|---|---|
| M1 | kill する | `test_pipeline_extra_correctness_accepts_registered_empty_numactl` は `evaluate()` 呼出中に旧 ValueError となり、`test_campaign.py:7367` に到達しない。negative test も helper の `test_campaign.py:120` で診断不一致になる | Pegasus 正例による過剰拒否 kill は一意で、後段 guard に先取りされない。ただし期待失敗 node は H だけではなく、診断不一致の negative test も含む |
| M2 | kill する | linux 正例の `test_pipeline_fullscale_verify_and_bench_share_immutable_numactl` が `test_campaign.py:7329` の呼出中に ValueError となり、`:7339` に到達しない。Pegasus 正例も `:7367` 到達前に落ちる | 親の「正例で先取りされない」は正しい。契約外 prefix 側は後段 guard に先取りされ、`:120` の診断不一致でも赤になるため、完全な失敗 node 集合は単一ではない |
| M3 | kill する | `test_pipeline_fullscale_verify_and_bench_share_immutable_numactl` の `test_campaign.py:7343`。既存強化 test も `:7201` で list と tuple の差を検出 | 親の「gate が list を誤拒否」は誤り。正規化を外すと `pipeline.py:700` の exact-tuple 条件を list が迂回し、guard は list を受理する。落とすのは動的 immutable assert |
| M4 | kill する | `env_contract=None` の正例は `pipeline.py:698` で AttributeError。Pegasus 正例の `test_campaign.py:7367`、動的 test の `:7339`、unknown-env test の exact 例外 assert `:7388` へ到達しない | 後段先取りなし。ただし H 以外の複数 node も赤になるため、期待 node を H だけにすると DW-M08 の完全集合条件を満たさない |
| M5 | 帰属不能 | 第 3 引数を `None` にすれば AST の `test_campaign.py:7304-7307` と動的 test の `:7343` が赤。単なる同一オブジェクトの別名なら AST だけが赤 | `None/別名` は異なる変異である。挙動保存の別名は受理集合を変えず、AST 赤を kill に数えられない |
| M6 | 帰属不能 | screening bench を `None` にすれば AST `:7304-7307` と screening 周回の identity assert `:7345` が赤。同一オブジェクトを返す別式なら AST だけ | production の先取りはないが、「別式」の意味が非一意。具体式と期待 node 完全集合の再登録が必要 |
| M7 | 帰属不能 | 通常 bench を `None` にすれば AST `:7304-7307` と通常周回の `:7345` が赤。同一オブジェクトを返す別式なら AST だけ | M6 と同じく、挙動変異と等価な構文変異が混在している |
| M8 | 帰属不能 | 3 箇所を実際に異なる tuple へ替えれば AST `:7304-7307` と動的 equality `:7344` が赤。同じ値・同じ object の別名なら AST だけ | 「共通式 pin」とされた `:7309-7312` は、直前ですべて `Name("numactl")` と限定済みなので独自検出力がない。具体的な誤式が未登録 |
| M9 | kill する | `_run_one_pass` の `pipeline.py:970` を `None` にすると、動的 test の `test_campaign.py:7343` が赤 | AST は call site しか見ないので生存する。動的検査だけが helper forwarding を検出するという親判定は正しい |
| M10 | SURVIVED | `pipeline.py:462` の `record_rep_returncodes=True` 分岐だけで prefix を落とす変異は、追加・強化された6本すべてが緑のまま | 動的 test は既定の `record_rep_returncodes=False`、すなわち `pipeline.py:451-457` しか通らない。`:454` を変えれば `test_campaign.py:7345` が落ちるが、登録文言は2箇所を区別していない |
| M11 | kill する | 正規化除去なら動的 test の `test_campaign.py:7343` | M3 と同一のソース変異・同一の失敗理由であり、独立した変異ではない。11件という耐性件数には数えられない |

M1、M2、M4の「正例方向では後段に先取りされない」は正しいです。M3は先取りなしという結論こそ正しいものの、gate が拒否するという説明が実コードと逆です。M5〜M8は構文だけ違う等価変異を含むため、現状の文言では kill を確定できません。

登録しなかった変異については、次の判断です。

- gate 削除／`False` 化を kill に登録しない判断は正しいです。None と契約外 tuple は `execution_guard.py:125-132` が引き続き拒否します。`test_campaign.py:120` や exact 例外 test は赤になりますが、受理集合は変わらず診断感度だけです。
- `qualification_policy is None` の再追加を等価変異とした判断も、現行コードでは正しいです。qualification 経路は先に `pipeline.py:655-678` で exact Pegasus contract、exact tuple、exact shape を要求し、後段 guard も同じ値を検査します。

## 登録漏れの変異

### 1. 実 `_run_trace` で argv prefix を落とす

- 変異内容: `pipeline.py:362` の `(list(numactl) if numactl else [])` を `[]` にする。
- 6本が緑のままである理由: 動的 test は `test_campaign.py:7167` で `_run_trace` 自体を fake に差し替え、AST test は `evaluate()` の `_run_one_pass` 呼出しか見ない。Pegasus 正例は空 prefix なので argv 差もない。
- 実際に変わる挙動: linux-baremetal の fullscale verify subprocess が numactl なしで走る一方、bench は契約 prefix で走る。qualification 台帳には `pipeline.py:1077-1082` が prefix ありの argv を記録するため、実 argv と台帳参照も食い違う。

### 2. qualification 用 bench 分岐だけ prefix を落とす

- 変異内容: `pipeline.py:462` を `numactl=None` にする。
- 6本が緑のままである理由: 動的 test は `record_rep_returncodes` を指定せず、既定 False (`pipeline.py:592`) の `:451-457` だけを実行する。他の5本は bench を実行しないか、その手前で停止する。
- 実際に変わる挙動: qualification は `pipeline.py:677` で `record_rep_returncodes=True` を必須にするため、verify は契約配置、性能 bench は prefix なしになる。certified の `fitness_tps` と選択順位が契約外配置の値へ変わる。

### 3. 正規化を qualification 検査より前へ移す

- 変異内容: `pipeline.py:693-696` を `:655` より前へ移す。
- 6本が緑のままである理由: 6本はいずれも `qualification_policy=None` であり、`:664` の exact-tuple 要求を通らない。
- 実際に変わる挙動: Pegasus qualification の `numactl=[]` が先に `()` へ変換され、従来の `type(numactl) is not tuple` 拒否を通過する。qualification の受理集合が exact tuple から list に広がり、従来は生成されなかった certified 選択・レポート・台帳が生成され得る。

疑点別には、型集合を `{list}` のみにする変異は base tuple に対して等価です。`{tuple}` のみにする変異は動的 test の `:7343` が殺します。gate 内の拒否項を落とす変異は negative test の診断照合か invalid-type exact path が赤になりますが、後段 guard があるため単独では受理集合を広げません。

## must-fix

### 1. 実 trace subprocess argv が未検査

- 所見: fake 境界より下で numactl を落としても6本すべてが通る。
- 根拠: `orchestrator/campaign/pipeline.py:362-370`、`orchestrator/tests/test_campaign.py:7106-7109,7167`
- 成立条件: 非空 numactl 契約で fullscale verify を実行する場合。
- 成果物影響: 契約外配置の verify が certified 受理集合へ入り、qualification レポート／台帳の `verify.argv` は実 argv と異なる prefix を参照する。
- 推奨対応: 実 `_run_trace` と subprocess spy を使い、非空 tuple が `subprocess.run` の argv 先頭へ exact に入ることを検査する。M11の重複枠をこの変異へ再照準する。

### 2. `record_rep_returncodes=True` の bench 配線が未検査

- 所見: `measure_point` の2本ある forwarding のうち、qualification が使う側だけが未被覆。
- 根拠: `orchestrator/campaign/pipeline.py:450-466,592,677`
- 成立条件: qualification、または `record_rep_returncodes=True` を指定する certified evaluation。
- 成果物影響: `fitness_tps`、性能レポート、certified 選択順位が契約外メモリ配置の値になり、contract SHA との帰属が偽になる。
- 推奨対応: 動的配線 test を `record_rep_returncodes=False/True` の双方で回し、両 measure_point call が同一 immutable prefix を受け取ることを pin する。M10を2箇所へ分割して再登録する。

### 3. qualification より後という正規化順序が未固定

- 所見: 親が明示した受理集合境界を、追加6本のどれも検査していない。
- 根拠: `orchestrator/campaign/pipeline.py:655-666,693-696`
- 成立条件: qualification に契約値と同内容の list、Pegasus なら `[]` を渡す場合。
- 成果物影響: qualification の受理集合が exact tuple から list へ広がり、従来 abort した入力から certified 選択・レポート・台帳が新規生成される。
- 推奨対応: qualification に list を渡して `pipeline.py:666` の shape mismatch で拒否され、sink 書込みがないことを確認する回帰 test を追加する。

## should-fix

- M3とM11は同じ変異です。M3を immutable snapshot 除去、M11を実 `_run_trace` argv omission など別層へ再照準し、重複した検出力件数を数えないでください。
- M5〜M8は `None`、異なる値、同値の別名を分けて再登録すべきです。同値別名を AST が赤にしても、受理集合も fail-closed 挙動も変わらず DW-M03 上の kill ではありません。
- AST test は `if fullscale_isolated` の exact `ast.Name` を `next()` で選ぶため、同値な条件式への変更や別の同名 if の追加で `StopIteration`／誤選択になります。また、`evaluate()` 内の `_run_bench` を常に2 call と決めるため、共通 helper への集約、正当な第三経路、nested function 内の無関係な call でも偽赤になります。実効配線 test を主防壁にし、ASTは限定的な構造感度検査として扱うべきです。
- worklog には、identity assert が保証するのは「通常分岐と screening 分岐で、fake `_run_trace` と fake `measure_point` のAPI境界が同一 tuple objectを受け取ったこと」まで、と明記すべきです。実 `_run_trace` の subprocess argv、`measure_point` から各 rep の runner argv、`record_rep_returncodes=True` 分岐、OS上の実配置は保証していません。

## nit

- `test_campaign.py:7308-7312` の AST dump 同一性 assert は、`:7304-7307` が全要素を同じ `Name("numactl")` に限定した後なので、追加の変異検出力がありません。
- `test_pipeline_extra_correctness_requires_numactl` という node 名は、現在の性質である「環境契約との exact 一致」より旧仕様の「非空必須」を示しており、診断時に誤解を招きます。
- invalid-type test は有用ですが、受理集合を守る kill ではなく「後段 authorization error path の診断感度 pin」として台帳上区別するのが適切です。

## 総括

- 静的検査のみを行い、pytest は実行していない。
- M1、M2、M3、M4、M9、M11は kill できるが、M3とM11は同一変異である。
- M5〜M8は等価な別名変異を含み、現状の事前登録文言では kill を一意に認定できない。
- M10は qualification が使う `record_rep_returncodes=True` 側で SURVIVED する。
- 実 `_run_trace` の subprocess argv omission も、追加6本すべてを通過する重大な登録漏れである。
- qualification より後という正規化順序も未固定で、list を受理する回帰が全緑になる。
- gate削除の非登録と `qualification_policy is None` 再追加の等価判定は、現行 registry・guard の下では正しい。
- must-fix 3件を閉じるまでは、検査が環境契約の実 launch を保証したとは扱えない。