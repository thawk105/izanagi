## 所見

### 1. `meta.ccbench_commit` の表現揺れは正式受理集合を追加で狭めない

- 主張: 既存 Layer 3 成果物 7 件はすべて短縮値 `d706650` であり、generic build は短縮値と完全値の双方を同一 HEAD として扱えるものの、正式 trial は既存 completeness gate が現行 pin との文字列完全一致を要求するため、混在束は新検査がなくても受理されない。
- 原典: `output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/layer3_report.json:1`、`orchestrator/campaign/layer3_report.py:571`、`orchestrator/campaign/buildcache.py:2632`、`orchestrator/campaign/pin.py:37`、`orchestrator/campaign/autonomous_trial_completeness.py:819`
- 判定: nit、修正要求なし。generic 経路には既知の full/short 表現差が残る。
- 成果物影響: 正式受理集合、receipt、certified 選択、台帳値は変わらない。将来 formal gate が複数表現を許す場合は、現在の raw 文字列比較ではなく、immutable source に対して解決した完全 OID の一致を述語にする必要がある。

### 2. `env_tags` の「ちょうど 1 要素」は producer と一致する

- 主張: 既存成果物 7 件はすべて `["linux-baremetal"]` であり、production serializer は WAL 内の env tag が複数なら report 生成自体を拒否するため、2 要素以上の正当な現行 Layer 3 report は生成されない。
- 原典: `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json:1`、`orchestrator/campaign/layer3_report.py:540`、`orchestrator/campaign/layer3_report.py:551`、`orchestrator/campaign/layer3_report.py:586`
- 判定: nit、修正要求なし。
- 成果物影響: 受理集合は production の既存値域から狭まらない。正しい述語は現実装どおり「各 report が非空文字列 1 件の list を持ち、その唯一値が 6 report で同一」である。

### 3. 完全 build 束の母数 6 は正式 trial の既存構造から導ける

- 主張: 正式受入は manifest の 6 trial を一度ずつ覆う 6 report を要求し、各 report は最大 1 cell、完全 build ならその cell が 1 campaign root を持つため、正当な完全束が 6 件以外の Layer 3 report を持つ経路はない。
- 原典: `orchestrator/campaign/trial_registry.py:1598`、`orchestrator/campaign/trial_registry.py:1618`、`orchestrator/campaign/trial_registry.py:5526`、`orchestrator/campaign/trial_registry.py:5856`、`orchestrator/campaign/autonomous_trial_completeness.py:819`、`orchestrator/campaign/autonomous_trial_completeness.py:4092`
- 判定: nit、修正要求なし。
- 成果物影響: 正当な正式受理集合は変わらない。1 trial 複数 cell と 1 cell 複数 campaign は既存 shape が拒否し、campaign root 共有も trial ID を含む campaign identity と期待 path の照合を通らない。

### 4. 正例 fixture は Layer 3 producer を利用している

- 主張: 登録 build fixture は Layer 3 JSON を手書きせず `layer3_report.build_report` から report object を生成しており、producer の field 構造変更に追随する。
- 原典: `orchestrator/tests/test_trial_registry.py:1019`、`orchestrator/tests/test_trial_registry.py:1154`、`orchestrator/tests/test_trial_registry.py:1167`、`orchestrator/tests/test_trial_registry.py:1682`
- 判定: nit、修正要求なし。永続化だけは `render` ではなく `json.dumps` を使用している。
- 成果物影響: 今回検査する `meta.ccbench_commit` と `env_tags` の production shape に乖離はない。atomic create や canonical byte 表現はこの fixture の検証対象外だが、受理集合や receipt 値には影響しない。

### 5. 不一致エラーから trial と値を特定できない

- 主張: CCBench/env の横断不一致、Layer 3 欠落、受入中の bytes 変更はいずれも trial ID、相違値または対象 path を失った総称エラーになり、要求された原因追跡ができない。
- 原典: `orchestrator/campaign/trial_registry.py:5494`、`orchestrator/campaign/trial_registry.py:5503`、`orchestrator/campaign/trial_registry.py:5508`、`orchestrator/campaign/trial_registry.py:5965`、`orchestrator/tests/test_trial_registry.py:1743`、`orchestrator/tests/test_trial_registry.py:1778`、`orchestrator/tests/test_trial_registry.py:1809`
- 判定: **must-fix**
- 成果物影響: 不一致束は receipt を発行せず、certified 選択から除外されるが、運用者はどの trial を再計測すべきか判断できない。診断修正は受理集合や receipt preimage を変えず、エラーへ基準 trial、相違 trial、値の安全な短縮表現または digest、欠落・変更 path を追加すればよい。現テストは診断不能な exact 文言を固定しているため同時修正が必要である。

### 6. Layer 3 再読は既存処理と重複している

- 主張: 新検査は完全束で Layer 3 を最初に 6 回読み JSON decode し、receipt 作成直前にさらに 6 回 raw bytes を読む一方、既存の deep chain と cross-binding も各 report を再読するため、直接の Layer 3 read は最低 12 回から24回へ倍増する。
- 原典: `orchestrator/campaign/trial_registry.py:5458`、`orchestrator/campaign/trial_registry.py:5911`、`orchestrator/campaign/trial_registry.py:5927`、`orchestrator/campaign/trial_registry.py:5965`、`orchestrator/campaign/autonomous_trial_completeness.py:3611`、`orchestrator/campaign/autonomous_trial_completeness.py:4133`
- 判定: nit
- 成果物影響: 成果物値と受理集合への影響はなく、所要時間だけが増える。増分は 12 open、6 JSON decode、`2 × 6 report の総 byte 数`。既存成果物の 10,699〜47,906 bytes/件を当てると追加読込量は約 0.12〜0.55 MiB であり、wall-clock 増分は未実測だが小さいと推定する。

### 7. 世代数照合は混入していない

- 主張: 差分には `loop_state.iteration` や世代数照合はなく、tracked 実装差分も裁定された 2 ファイルだけであるが、Layer 3 bytes の受入中不変検査は裁定 §2 の三述語には明記されていない追加防御である。
- 原典: `/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s4-adjudication.md:39`、`/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s4-adjudication.md:66`、`orchestrator/campaign/trial_registry.py:5965`、`orchestrator/campaign/layer3_report.py:696`
- 判定: nit
- 成果物影響: producer は Layer 3 出力を排他的に新規作成するため、正当な静的成果物の受理集合は変わらない。並行して bytes が変化する入力だけが追加で拒否される。世代数、receipt、台帳値への変更はない。

## 総括

- must-fix は 1 件: 不一致、欠落、snapshot 変更のエラーが trial・値・path を示さず診断不能。
- `ccbench_commit` の full/short 差は generic 経路に存在するが、正式 gate の既存 exact pin が混在束を既に拒否するため新たな過剰拒否ではない。
- `env_tags` 1 件、完全束 6 件、producer 使用 fixture は現行 production 契約と一致する。
- 性能は Layer 3 の直接 read が最低 12 回から24回へ増えるが、静的規模では nit。
- `loop_state.iteration` 照合は混入していない。