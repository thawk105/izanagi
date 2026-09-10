### 所見 1 — source fragment の継ぎ合わせにより S1 / S2 変異が生き残る

**主張**

現行 bytes 自体は S1 / S2 を閉じている。しかし追加テストは承認 gate と driver tail の間を削除して実行するため、禁止署名を成立させる一行変異が緑のまま残る。これは今回の最重要所見である。

**一次証拠 (file:line)**

- `orchestrator/tests/test_pegasus_floor_tools.py:2015-2021` は承認 gate だけを抽出する。
- `orchestrator/tests/test_pegasus_floor_tools.py:2109-2111` は `PROTOCOL_PATH=...` 以降だけを抽出する。
- `orchestrator/tests/test_pegasus_floor_tools.py:1029-1034` は両 fragment を直接連結し、実ファイルの `floor_campaign.sh:358-953` を実行しない。
- `floor_campaign.sh:27` の `unset` も fragment に含まれない。

**成立条件**

次の一行変異はいずれも追加テストをすり抜ける。

1. `floor_campaign.sh:954` を以下の一行へ変更する。

   ```bash
   IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=$IZANAGI_SUBMISSION_NONCE; PROTOCOL_PATH="output/s8b-freeze/floor_protocol.json"
   ```

   実 job では未設定 env が gate 通過後に設定され、`floor_campaign.sh:973-975` が flag を追加するため S1 が成立する。一方 `_driver_tail()` は同じ行の `PROTOCOL_PATH=` から後だけを切り出すため、この代入を実行しない。

2. `floor_campaign.sh:27` の `unset` に承認 env を追加する。

   不一致 env が gate 前に消え、build と driver まで到達するため S2 が成立する。`test_floor_job_hardens_interpreter` の部分文字列 assertion (`test_pegasus_floor_tools.py:692`) も緑のままである。

**成果物への影響**

S1 変異では、承認なし job が driver の exact Boolean gate を通り、床値 pilot の測定値が生成され得る。その値を参照する床値欄、refreeze 適格性、certified 選択・レポート・台帳の受理集合が未承認実測を含み得る。

S2 変異では、不一致 job が高価な build と driver 起動まで進み、`submit_binding` 拒否ではなく後段の failure / job-result を残す。試行台帳の stage、失敗参照、queue 消費が変わる。

**must-fix か nit か**

must-fix。

**推奨 fix**

`floor_campaign.sh` 内の承認変数の出現位置を固定する回帰テストを追加する。少なくとも、出現が設定検査・exact 比較・driver append 条件の3箕所だけであり、`unset`、再代入、gate と driver 間の変更がないことを検査する。さらに上記2変異を mutation matrix に追加する。

### 所見 2 — 現行 bash bytes には特殊値による抜け道はない

**主張**

空文字、`*`、`?`、先頭 `-`、改行を含む設定済み値はすべて nonce 不一致として rc=2 で停止する。word splitting、glob、pattern matching による承認化は起きない。

**一次証拠 (file:line)**

- 設定有無: `floor_campaign.sh:351`
- exact 比較: `floor_campaign.sh:352`
- failure と停止: `floor_campaign.sh:353-355`
- driver 配列と引用付き展開: `floor_campaign.sh:968-978`
- submitter の literal 初期化: `submit_floor.sh:33`
- nonce の形式制約: `submit_floor.sh:293-296`
- 引用された qsub 配列: `submit_floor.sh:417-432`

**成立条件**

`${VAR+x}` は未設定時だけ空、空文字を含む設定済み値では `x` になる。内側の両オペランドは引用済みなので、`*` と `?` は pattern にならず、改行も一つの文字列として比較される。先頭 `-` も `[[ ]]` 内で演算子化されない。

`set -u` は未設定変数を内側で参照する前に外側で分岐するため発火しない。`if [[ ... ]]` の偽は `set -e` の終了対象でもない。

**成果物への影響**

現行 bytes では特殊値から driver flag、床値、certified 受理集合への流入はない。

**must-fix か nit か**

該当なし。適合確認。

**推奨 fix**

所見1の出現位置固定に加え、`*`、`?`、先頭 `-`、改行も不一致 parameter に追加すると、この bash 境界を直接固定できる。

### 所見 3 — 不一致停止は build / driver より前で rc=2 を維持する

**主張**

不一致検出は build と driver 起動より前にあり、job の最終 rc は2になる。ERR trap との衝突もない。

**一次証拠 (file:line)**

- `write_failure` は記録後に0を返す: `floor_campaign.sh:181-215`
- ERR trap: `floor_campaign.sh:247-254`
- 承認不一致と明示的 `exit 2`: `floor_campaign.sh:351-355`
- build 開始: `floor_campaign.sh:817-840`
- driver launch marker と起動: `floor_campaign.sh:967-978`
- テストの rc、stage、両 marker: `test_pegasus_floor_tools.py:2054-2070`

**成立条件**

`write_failure 2 ...` 自体の関数 rc は0であり、直後の `exit 2` が job rc を決める。明示的 `exit` は ERR trap を起動せず、比較式も `if` 条件内なので `set -e` に捕捉されない。writer が失敗しても既存実装はその失敗を診断して0を返し、job rc は2のままである。

**成果物への影響**

不一致 job は gflags / glog build、driver、床値生成へ到達せず、failure の stage は `submit_binding` になる。

**must-fix か nit か**

該当なし。適合確認。

**推奨 fix**

変更不要。

### 所見 4 — 登録済み N1〜N6・P1 は独立に赤になる

**主張**

事前登録された7変異はすべて対応テストがある。ただし、所見1の未登録 S1 / S2 変異は別途生き残る。

**一次証拠 (file:line)**

| 変異 | 赤にするテストと理由 |
|---|---|
| N1 | `test_pegasus_floor_tools.py:1043-1066` の未承認 case。`floor_campaign.sh:974` を無条件化すると argv exact 比較が赤。 |
| N2 | `test_pegasus_floor_tools.py:2024-2070` の非空3 case。不一致を「非空なら承認」にすると rc=0・marker 作成で赤。 |
| N3 | 同 `:2054-2070`。failure を削除すれば failure args、exit を削除すれば rc と marker が赤。 |
| N4 | `test_pegasus_floor_tools.py:1246-1271`。`submit_floor.sh:33` を1にすると未承認 qsub argv が赤。 |
| N5 | 同 `:1263-1271` と ambient test `:1321-1324`。常時 export は exact argv が赤。 |
| N6 | `test_pegasus_floor_tools.py:1306-1324`。`submit_floor.sh:33` を ambient 初期化へ変えると qsub export が赤。 |
| P1 | `test_pegasus_floor_tools.py:1047-1056` の一致 case。常時 failure なら helper の rc assertion `:1038` が赤。 |

追加テストの一行破壊対応も成立する。

- explicit export: `submit_floor.sh:419` を削除すると `test_pegasus_floor_tools.py:1297-1302` が赤。
- receipt bytes: payload `submit_floor.sh:483-494` に一キー足すと `test_pegasus_floor_tools.py:1396-1399` が赤。
- zero arity: `submit_floor.sh:46` を `shift 2` にすると `test_pegasus_floor_tools.py:1411-1414` が赤。
- mismatch: `floor_campaign.sh:352` の `!=` を `==` にすると negative と confirmed positive の双方が赤。

**成立条件**

positive と negative は同じ nonce、同じ `_confirmation_binding_fragment()` を使い、承認値だけを一致値と不一致値に分けている。過去型 F341 の「negative が別経路だけを検査する」状態ではない。ただし gate と driver 間を省略する構造は所見1の別の分断を作っている。

**成果物への影響**

登録変異に対する防壁は成立するが、所見1を直さなければ certified 床値への未承認流入を防ぐ保証としては不十分である。

**must-fix か nit か**

登録 matrix 自体は適合。所見1の補強は must-fix。

**推奨 fix**

N1〜N6・P1は維持し、gate 前の `unset` と gate 後の再代入を追加変異として登録する。

### 所見 5 — driver gate、receipt、未承認 argv に裁定逸脱はない

**主張**

現行差分は指定3ファイルだけで、`orchestrator/campaign/` は無変更。receipt key、env 値、未承認 argv も裁定どおりである。

**一次証拠 (file:line)**

- `git diff HEAD --stat` は3ファイル、275 insertions / 26 deletionsのみ。
- `git diff HEAD -- orchestrator/campaign/ --stat` は空。
- admission の exact receipt keys: `certified_writer_admission.py:27-30,184`
- receipt payload: `submit_floor.sh:483-504`
- 承認 env の値は nonce: `submit_floor.sh:417-420`
- 未承認 qsub exact assertion: `test_pegasus_floor_tools.py:1263-1271`
- 未承認 driver exact assertion: `test_pegasus_floor_tools.py:1046,1057-1066`
- 冒頭 unset は承認 env を含まない: `floor_campaign.sh:27`

**成立条件**

承認引数なしでは `CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=0` のため export append は実行されない。receipt generator に承認状態は渡されず、key 集合も admission の `_FLOOR_KEYS` と一致する。

**成果物への影響**

現行 bytes では receipt schema、static admission の受理集合、未承認 qsub / driver argv、既存成果物参照は不変である。

**must-fix か nit か**

該当なし。適合確認。

**推奨 fix**

実装変更は不要。所見1のテスト防壁だけを追加する。

## 総括

現行実装 bytes には bash 抜け道、停止位置違反、receipt 変更、driver gate 変更、裁定 §6 からの逸脱は見つからない。  
登録済み N1〜N6・P1 はすべて対応テストが赤にすると静的に判定した。  
ただしテストが gate と driver の間を切り落としており、一行の再代入で S1、一行の事前 unset で S2 を成立させても緑になり得る。  
したがって land 前の must-fix は、承認変数の全ファイル内データフローを固定するテストと2変異の追加である。