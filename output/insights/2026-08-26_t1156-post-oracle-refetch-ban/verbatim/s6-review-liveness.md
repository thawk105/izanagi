結論は採用不可です。H1 は `build_cells` の契約として real、H2 も real です。静的検査のみで、pytest は実走していません。

## 所見 1

- **所見 1**: `build_fn` の object identity が偽になると capability が黙って消えるため、`build_cells` は fail-open である
- **具体的失敗**: [s8b_floor_campaign.py:4022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4022) は `build_fn is buildcache.build_v2` の場合だけ capability を追加する。wrapper、partial、spy、別 materializer では、base、旧 receipt、archive だけで [s8b_floor_campaign.py:4041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4041) の build が始まる。事後検査 [s8b_floor_campaign.py:3472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3472) は base/source/root を見るが、disconnected flag と population policy を要求しないため、再取得後に同じ HEAD/config/archive へ戻れば受理する。

  capability が落ちる経路の全分類は次のとおり。

  | 経路 | 未渡し | 禁止が消えるか |
  |---|---:|---:|
  | public fresh official、既定引数 | no | no。注入は [s8b_floor_campaign.py:6653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:6653) で拒否され、core が exact `build_v2` に固定する |
  | direct core official への `build_fn` 注入 | no | no。[s8b_floor_campaign.py:6767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:6767) で build 前に拒否 |
  | fresh pilot、既定 builder | no | no。exact `build_v2` へ正規化される |
  | direct core pilot または direct `build_cells` に truthy な wrapper/spy/custom builder | yes | yes。flag、材料検査、実効値検査、policy identity が全部消える |
  | custom `prepare_fn` | yes | yes。`dependency_binding` が作られず、合成された `oracle_attempt` が non-None なら postflight も省略して build が進む |
  | `build_v2` の direct generic base-only 呼び出し | yes | post-oracle 用に誤用すれば yes。generic 呼び出しとしては裁定どおり意図的 |
  | capability 付き cache hit | no | no。policy identity は有効で、configure/build 自体が無い |
  | capability 無しの旧 generic cache hit | yes | yes。旧 flag 無し entry を hit でき、事後検査は flag/policy を確認しない |
  | resume 状態 L | 原則 no | rebuild するため既定経路では capability が付く |
  | resume 状態 M以降 | yes | current build は無いが、旧 binary の受理に禁止情報は使われない |
  | capability 作成または検証中の例外 | no | exact 経路は build 前に停止 |
  | capability 無し custom builder が実行後に例外 | yes | artifact は返らないが、再取得などの副作用は既に起こりうる |
  | non-sort cell | yes | 対象外なので禁止は不要 |

  H1 の「fresh official でも条件が偽になりうる」という部分だけは refuted です。しかし要求された「sort_best かつ binding ありなら capability 無し build を拒否」は成立していません。

  修正は [s8b_floor_campaign.py:4022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4022) で非 exact builder を明示的に `FloorCampaignError` へ倒し、capability を無条件に構築することです。さらに [s8b_floor_campaign.py:4041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4041) の直前に、dependency-bound `sort_best` なら capability key が必須という実行時 gate を置くべきです。最適化で消える Python `assert` は使えません。
- **成果物影響**: 注入経路では、oracle PASS receipt が flag/policy 無し binary と [s8b_floor_campaign.py:4125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4125) で結合され、レポートと binary receipt が誤った参照を持つ。supported core では非既定 seam により refreeze 不適格になるため fresh certified 集合は直接広がらないが、pilot、直接 helper 利用、resume report は影響を受ける。
- **must-fix / nit / 裁定行き**: **must-fix**

## 所見 2

- **所見 2**: H2 は real であり、production oracle と追加 build 検査を同時に満たす実ファイル集合が無い
- **具体的失敗**: production の source root は必ず `<base>/masstree-src` で、Git top-level であることを [s8b_floor_campaign.py:2810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:2810) と [s8b_floor_campaign.py:2871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:2871) が要求する。親資料どおり oracle inventory が `.git` を含むなら、oracle PASS 用 manifest は `.git` の regular file を宣言しなければならない。一方、追加された build inventory は [buildcache.py:1037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1037) で `.git` を必ず除外する。したがって、oracle に通る manifest は build 側の `actual != expected_actual` で拒否され、`.git` を宣言しない manifest は oracle 側で拒否される。

  別 root も逃げ道にならない。oracle へ渡す root は [s8b_floor_campaign.py:3942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3942) で固定される。明示 staged base は非既定 seam で、public official は [s8b_floor_campaign.py:6653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:6653) で拒否する。既定 prebuild [s8b_floor_campaign.py:3044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3044) と [buildcache.py:1889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1889) に `SHA256SUMS` を作成または配置する処理も無い。指定 3 ファイル中で生成するのはテスト fixture だけである。

  よって repo 外 staging が manifest を配置しても `.git` inventory の不一致が残る。official `sort_best` は build へ到達せず安全側に停止するが、新禁止は production で一度も成功経路を持たない。
- **成果物影響**: fresh official は `sort_best` binary、manifest、certified floor 値を生成できず、新たな certified 選択の受理集合は空になる。誤った数値を受理するのではなく、campaign 全体が成立しない。
- **must-fix / nit / 裁定行き**: **裁定行き。ただし採用 blocker**。oracle と [buildcache.py:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1025) の inventory 仕様を同一の正本へ揃え、[s8b_floor_campaign.py:3044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3044) の prebuild と oracle の間に独立して pin された manifest authority を用意する必要がある。live tree からその場で期待値を生成する修正は恒真化するため不可。

## 所見 3

- **所見 3**: manifest file 集合検査が未宣言 archive を特例受理しており、裁定 §2 点3から逸脱する
- **具体的失敗**: [buildcache.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1084) は `libkohler_masstree_json.a` を manifest の宣言有無にかかわらず `expected_actual` へ加える。実際、追加 fixture [test_buildcache_v2.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:376) は archive を `SHA256SUMS` に入れていないのに正例として通す。裁定は「宣言外 regular file が無いこと」を要求しているため、この特例は不一致である。
- **成果物影響**: 合成または誤配線された capability では、oracle manifest authority に含まれない archive から binary を publish できる。completion identity には run-local archive hash が入るが、「oracle が受理した全 file 権威」という certified 参照にはならない。
- **must-fix / nit / 裁定行き**: **must-fix**。[buildcache.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1084) を `declared | {"SHA256SUMS"}` 相当にし、テスト manifest に archive の literal fixture digest を宣言する必要がある。

## 所見 4

- **所見 4**: unit 検査は局所的には発火するが、production 配線の独立 oracle が無く、正例の期待値には自己観測がある
- **具体的失敗**: flag token と policy ID は [test_buildcache_v2.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:746) と [test_buildcache_v2.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:875) に literal であり、production 定数の import はしていない。この点は裁定どおりである。

  一方、`_post_oracle_binding` は [test_buildcache_v2.py:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:399) で live `SHA256SUMS` と archive を自分で hash し、その値を同じ live tree と比較させる。正例だけなら「観測値と観測値」の比較であり、oracle receipt からの配線違いを検出できない。変更後に file を書き換える負例は実際に発火可能なので、buildcache の個別検査すべてが恒真というわけではない。実効値 OFF、manifest hash 不一致、file hash 不一致、extra file、schema 不一致はいずれも具体的な拒否入力を持つ。

  決定的な欠落は、追加テストが `s8b_floor_campaign.py` を一度も import せず、[s8b_floor_campaign.py:4022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4022) の capability 配線、非 exact `build_fn`、production oracle-shaped inventory を検査していないことである。そのため、H1 と H2 を全テストが見逃す。局所検査は非恒真だが、production の成功経路自体が空なので、システム保証は恒真である。
- **成果物影響**: テストが通っても、production certified binary が一件も作れないことと、注入経路で flag 無し binary が oracle receipt に結合されることを検出できない。テスト結果を wave の受理根拠にできない。
- **must-fix / nit / 裁定行き**: **must-fix**。少なくとも「dependency-bound sort_best で非 exact builder は呼び出し回数 0」「exact builder へ oracle receipt の literal 値が渡る」「oracle と build の inventory が同じ」を独立に検査する必要がある。

## 所見 5

- **所見 5**: resume 状態 M以降は capability を一度も再要求せず、裁定済み X5 がそのまま残る
- **具体的失敗**: [s8b_floor_campaign.py:7203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:7203) は durable manifest の binary を読み、[s8b_floor_campaign.py:7219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:7219) と [s8b_floor_campaign.py:7223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:7223) で binary/store hash を照合するだけで `build_v2` を呼ばない。旧 manifest に population policy や disconnected 証跡は無いため、禁止前の sort_best binary も受理される。
- **成果物影響**: resume の result、レポート、台帳は旧 binary の値と参照を保持できる。ただし [s8b_floor_campaign.py:6576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:6576) により resume は `eligible_for_refreeze: false` なので、現行の certified 選択集合は直接広がらない。
- **must-fix / nit / 裁定行き**: **裁定行き**。これは裁定済み X5 であり、本差分が scope 外の migration を実装しなかったこと自体は逸脱ではない。

## 総括

- H1: `build_cells` の fail-closed 性について **real**。ただし fresh official では exact builder が固定されるため、その限定反証は成立する。
- H2: **real**。Git root、oracle の `.git` inventory、build 側の `.git` 除外により、両 gate の共通受理入力が無い。
- 追加された局所検査は個別には発火可能だが、production 成功経路が空なのでシステム保証は恒真である。
- flag と policy ID のテスト literal 化は守られている。campaign 配線の独立テストは無い。
- 編集は裁定 §6 の 3ファイルだけで、X1からX5への実装拡張や既存事後検知の削除は見当たらない。
- pytest は未実走であり、緑とは判定していない。