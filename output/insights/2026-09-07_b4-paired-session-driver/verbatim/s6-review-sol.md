## 所見

- **id**: correctness-gate-1
- **対象**: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2368
- **主張**: finalizer は probe の `status` と `competitors` を raw の `returncode`、`stdout`、`stderr` から再導出しない。このため、中間 probe の生出力が競合を示していても session を `complete` として受理できる。
- **具体例**: finalizer の PID が 100 の状態で、完備した 2 measurement を持つ session の `mid_probe` を `{"status":"clear","returncode":0,"stdout":"321 ycsb_foreign.exe\n","stderr":"","competitors":[],"error":null}` とする。実行時分類器なら PID 321 を競合として返すが、`_probe_payload_status` は空の自己申告 `competitors` だけを見て `clear` を返す。続く `_session_outcome` は 2 measurement と 3 個の自己申告 status がすべて complete/clear なので session を `complete` と再導出し、summary を生成する。
- **成果物影響**: 汚染前が candidate 120、110、reference 100、100 なら D は 0.1 だが、競合により candidate 2 が 120 へ上がった標本は D が 0 になる。この標本を残す 1 標本 stratum では `candidate_floor` が 0.1 から 0 に下がり、雑音差を勝ちとして受理する集合が広がる。逆向きの汚染なら D と床値を大きくすることもできる。
- **確度**: 高。validator が分類器を呼ばず、`clear` 時に raw rc/stdout/stderr の整合を検査していないことがコード上で確定している。

- **id**: correctness-gate-2
- **対象**: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1423, /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2166
- **主張**: `FloorPairSpec` は凍結 bytes に由来する capability ではなく、自己申告 `spec_sha256` を持つ通常の dataclass として扱われる。plan に含まれない field は `dataclasses.replace` で load 後に変更しても正しさゲートを通る。
- **具体例**: 第一に、loaded spec の `environment.numactl_argv` だけを `("/bin/sh","-c","shift; exec /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/bin/candidate.exe \"$@\"","floor-wrapper")` へ置換する。元の plan は environment を含まないため `_assert_plan_exact` を通る。runner はこの列を planned binary より前へ置くので、reference 測定でも planned reference path を捨てて candidate を実行する。header に `numactl_argv` は無く、元 spec を使う finalizer も検出できない。第二に、finalize 時だけ `failure_policy.max_dropped_fraction` を `Fraction(1,1)` へ置換すると、59 pair-sample 中 58 件欠測でも受理される。plan と window header はこの field を束縛せず、summary は表示上の閾値を `"1/20"` のまま `admissible:true` にする。
- **成果物影響**: 前者では candidate の実測値を reference として計上できる。candidate 120、110、正しい reference 100、100 なら本来 D は 0.1 だが、各 reference も同じ candidate を動かせば D を 0 にできる。後者では 98.3% 欠測した campaign の唯一の残存値を床値として生成でき、残存 D が 0 なら `candidate_floor:0` となる。いずれも summary は元の凍結 spec SHA を名乗る。
- **確度**: 高。environment と failure policy は plan hash に入らず、run/finalize は dataclass の由来や内容 hashを再検証しない。runner の prefix 組み立ても /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/calibrator/runner.py:536 で確認できる。

- **id**: correctness-gate-3
- **対象**: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2053, /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1971
- **主張**: binary は session 冒頭で path を hash 検査した後、保持した file descriptor ではなく同じ path 名で測定される。record の `binary_sha256` も spawn した実体の hash ではなく spec 値の転記なので、検査後の置換を検出できない。
- **具体例**: measurement 順が candidate、reference の side session で、冒頭の reference hash 検査後に別 process が reference path を candidate bytes の regular fileへ atomic rename する。mid probe は ycsb process だけを見るため clear のままで、runner は置換後の path を spawn する。exec 後に正しい reference file を戻せば次 session の冒頭検査も通る。reference record には実際に走った bytes ではなく `artifact.binary_sha256` の正規 reference hash が記録され、finalizer もその自己申告値と spec を比較するだけである。
- **成果物影響**: candidate 120、110、正しい reference 100、100 の D 0.1 を、reference role でも candidate bytes を走らせて D 0 にできる。逆に別の遅い binary を差し込めば D と `candidate_floor` を大きくできる。
- **確度**: 高。検査から spawn まで Path しか保持せず、spawn 境界の hash または fd 実行が無いこと、record が実測 hash を受け取らないことが静的に確定している。

## 所見が無い領域

- exact 2 measurement は、canonical plan、実行時の `["complete","complete"]` 判定、finalizer の長さ検査と strict zip の三箇所で閉じている。1 件、3 件、重複 ID、順序交換を complete として通す経路は見つからなかった。
- raw の role、artifact ID、measurement ID、order index は canonical plan と exact 比較される。raw metadata だけの candidate/reference 交換は通らない。
- `_derive_strata` は candidate 1/reference 1 と candidate 2/reference 2 を別々に `compute_gain_difference` へ渡しており、分母の流用は見つからなかった。
- 通常の loader 由来 spec を改変せず使う経路では、欠測選択は status のみ、5% の分母は `sample_count * pair数` の pair-sample 数である。
- reference 数と D 式の spec 単独改変は `_parse_statistics` の module 定数との exact 比較で拒否される。比較が恒真になる経路は見つからなかった。

## 総括

所見は 3 件。特に finalizer の probe 再導出は中間 gate を raw 自己申告へ戻している。  
さらに未封印の spec dataclass と spawn 前 binary TOCTOU により、candidate を reference として測定できる。  
焦点テストの緑とは両立する具体的な `candidate_floor` 偽装経路である。