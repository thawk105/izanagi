# 裁定 erratum 1 — 変異事前登録 (§6) の再照準と期待 node 訂正

`ruling.md` §6 は凍結として扱い、in-place で書き換えない (DW-O12: 凍結は自分が直前に書いたもので
あっても拘束する)。本 erratum が §6 を上書きする。出所は段 6 レビュー A の「変異の帰属判定」で、
親が採用した。**本走の前に、下記で確定した期待 node を probe で実測して確定する** (DW-M07:
KILLED 期待で node 空の spec は起動前に中止されるため、まず全件 SURVIVED 登録の probe を回す)。

## 変更しないもの (単一理由性 OK のまま)

| ID | 期待 node (静的判定) |
|---|---|
| M5 | `test_pegasus_calibration_workload.py` の argv 完全一致 (`[selected]` / `[literal_available]`)。CLI は available receipt を受けるので別層の拒否に依存しない |
| M9 | `test_calibrator_certify.py` の全 rep assertion。unavailable + 正常 stdout で counter 常時必須化すると最初の rep 後に `runner.py:1264` で停止する |
| M10 | `test_calibrator_certify.py` の停止位置 assertion と理由 assertion。第 2 rep の maxrss だけ欠損させ、過剰緩和すると後続 rep へ進む |
| M-POS | `[selected]` で選択先・available・argv 完全一致。**証明範囲は shell の argv 生成までで、認証 job の完走ではない** |

## 期待 node を訂正するもの (変異内容は変えない)

| ID | 旧 §6 の期待 | 訂正後の期待 node | 理由 |
|---|---|---|---|
| M1 | 「no-perf 正例 (分岐到達)」 | **receipt 読込みが先に失敗する node**。`[unavailable]` で即時 exit を復活させると receipt が生成されないため | 分岐 assertion には届かない。赤の原因は変異ただ一つなので単一理由性は保たれる (DW-M03 の「fail-closed 挙動が期待方向へ変わった」に該当) |
| M2 | 「perf 有り対照」 | **`[selected]` の status assertion**。base PATH に literal perf が無いので probe を前へ移すと FileNotFoundError 由来の unavailable になる | argv 一致より先に status が赤になる |
| M6 | 「no-perf 正例 (perf prefix 不在)」 | **`test_calibrator_certify.py` の rep 数 assertion**。unavailable receipt を無視して True にすると subprocess fixture が perf CSV を書かず `runner.py:1256` が counter 欠損で停止する | 現状の実効 gate は counter 必須検査。prefix 伝播を独立に証明したいなら subprocess 境界で argv を先に検査する別変異を立てる |

## 再照準するもの (変異の位置・内容を変える)

| ID | 旧 §6 の変異 | 再照準後 | 理由 |
|---|---|---|---|
| M3 | `probe_error` を `unavailable` として扱う | **抽出 shell 断片の「argv 生成に進ませない」だけに照準する。** receipt 自体を改変する変異は別 ID として分離する | wrapper だけで False に変換して元 receipt を渡しても CLI の `use_perf_from_receipt` が再び拒否する。全経路の最終拒否では帰属できない |
| M4 | 候補全滅でも symlink / selection JSON を作る | **selection JSON の生成と symlink の生成を分け、symlink 側は具体的な非空リンク先を定めた上で登録する** | 選択ブロックを単純に無条件化すると空 `PERF_SELECTED_REAL` への `ln -s` が先に失敗し、不在 assertion まで届かない |
| M7 | `_measure` closure で `use_perf=False` を渡さない | **rratio ごとに期待 gate を分けて登録する。** rr20/80 は `holdout_observation.py:945` の capability 不一致 (benchmark 前の拒否)、rr50 は counter 欠損 | 1 つの期待 node にまとめると帰属が割れる |
| M8 | 飽和判定不能でも noise を実行する | **rr50 を指定し、`sweep.py:288` の noise 測定呼出し / 追加 command に照準する。** rr20/80 版は「noise 遷移を試みた」ことの検査として別枠に落とす | rr20/80 では `holdout_observation.py:874` が noise 実行前に `records=0` を拒否する。観測 wrapper が捉えるのは「遷移を試みた」ことであり「noise が実行された」ことではない |

## 表記の訂正

- M8 の記述で「noise 未呼出し」と書いた箇所は、rr20/80 では **「noise 遷移未試行」** が正確である。
  観測 wrapper は内側の拒否を消していない。
- M-POS の証明範囲は「shell の argv 生成まで」であり、認証 job の完走ではない。

## 本走前の手順 (DW-M07 / DW-M08)

1. 全件を **SURVIVED 期待**で登録した probe を先に回し、観測 node を集める。
2. 観測 node と本 erratum の静的予測を突き合わせ、食い違いは erratum を追記して確定する。
3. 期待 node を**完全集合**として登録し、同形式へ正規化した記録 node との完全一致だけを KILLED とする。
4. 本走は `--runner-mode dispatch` + runner argv の `--force-dispatch`。
   `--attempt-out` と `--wrapper-attempt` は同時指定必須。`--out` / `--attempt-out` は checkout 外。
5. 変異中は親の編集と、worktree へ書きうる子の起動を止める (DW-M05)。
