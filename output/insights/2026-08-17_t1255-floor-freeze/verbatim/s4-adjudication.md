# 段 4 裁定 (確定版) — [T-1255] + [T-419] (3)

wave = `dev-wave-t1255-floor-freeze` / 2026-08-17 / 親裁定

段 3 は 2 本とも NO-GO。所見を real/refuted へ裁定し、plan v2 を確定する。

## 結論

**実装して実発行まで進む。** 段 3 の NO-GO は 2 本とも「ユーザー再裁定が要る」を根拠にしていたが、
その根拠は裁定 inbox の逐語で崩れる。技術面の blocker (A-1) は本 wave の scope 内で塞ぐ。

### なぜ再裁定へ返さないか — 裁定 inbox の逐語

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-17-rulings-full4-11rulings.md:70-81` が
[T-1255] の一次資料である。**ユーザーの言葉は
「床値の操作？あなたでできるものを私にやらせないで。」の 1 文だけ**である。

`freeze_protocol`・`sys.stdin.isatty`・「tty 判定を明示フラグへ置換」・
「create-only なので旧 protocol を退ける手順」は、すべて rulings 側の親 AI が付けた**分析**であり、
ユーザーが承認した実装方向ではない。台帳エントリ (`docs/archive/worklog-phase3-0817-611.md:565-573`)
はその分析を写している。

本 wave の実測は、その分析が**どの経路が v2 実凍結を行うかを取り違えている**ことを示した
(`freeze_protocol` は出力先が既存で create-only により必ず失敗する死んだ経路、
実経路は `reseal_protocol()`)。したがって手段の訂正は**ユーザー裁定の上書きではなく、
別 AI の分析の誤りの訂正**である。拘束するのは「AI が凍結を完遂する」という意図の方である。

これにより A-4 / B-1 は **refuted** とする。

### なぜ D460 / D471 に阻まれないか

- **D471 は禁止ではなく先送りである。** 却下理由 (ii) authority 分裂は「実 driver が固定 legacy path を
  渡すから」であり、本 wave の W1 / W2 がその前提を消す。却下理由 (iii) は
  「配線は [T-419] (3)、実発行は [T-1255] が所有する」であり、**本 wave が両方を所有する**。
  残るのは (i) D460 の明文禁止だけ。B-2 は **partially refuted**。
- **D460 の禁止は理由ごと失効する。** D460 の理由節は「pin を条件に入れると今日 0 件になり、
  床値の受理経路が壊れる」と実測を根拠にしている。P1 の fallback 節がその状態を保つため、
  理由が指す害は発生しない。新 D で禁止だけを撤回し、caller 非選択・現行契約優先・
  曖昧時 fail-closed は残す。
- decisions は戦術層であり、新 D による改訂は AI が行える (D444 → D460 → D471 が既にその形)。

### なぜ規律 2 を破らないか

段 3 レンズ A の blocker A-1 (versioned record の権威が作業ツリーにある) は **real** であり、
これを塞がずに解決先を versioned へ移すと**受理集合を緩める**。よって W4 を scope に入れ、
resolver が見る index は固定 HEAD commit の 100644 blob だけを権威とする。
これは現状より厳しくなる方向であり、規律 2 に適う。

## 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | versioned record の権威が固定 HEAD blob でなく作業ツリーにある | **real** | **採用 (W4)** |
| A-2 / B-4 / B-5 | official preflight と v2 candidate producer が v2 を拒否する | **real** | **scope 外**。両者とも official mode の CLI 拒否 (`s8b_floor_campaign.py:6740-6747`) の背後で休眠。`output/s8b-freeze-candidates/` は不在、official floor result も 0 件と実測。DW-G04 の「発火条件を書けない条件付き機能」に該当するため設計メモへ送る |
| A-3 / B-3 | driver CLI の `--protocol` が caller 選択のまま | **real** | **scope 外** → 裁定パッケージ。[T-419] (3) の原文は「shell wrapper と 5 module」であり CLI 引数面を含まない。公開 CLI 契約の変更になる |
| A-4 / B-1 | T-1255 の手段記述を親が失効と断定できない | **refuted** | 上記のとおり逐語で崩れる |
| A-5 | 「旧 protocol を退ける」が P1 では不成立 | **partially real** | W4 が主因を消す。作業ツリーからの削除では legacy へ戻らなくなる。HEAD gitlink を旧 pin へ戻す経路は残るが、それは repository 履歴の巻戻しであり本 wave の対象外 |
| A-6 | 結合状態で赤になる既存テストが段 2 の 2 件より多い | **real** | **採用**。段 2 の 2 件に加え、レンズ A が挙げた `test_pegasus_floor_tools.py` の 4 node を焦点走に含める |
| B-2 | P1 は D471 とも衝突する | **partially refuted** | 上記 |
| B-6 / B-7 | 「候補 2 件」「774 bytes / `2c8cf9be…`」は投影値 | **real** | **採用**。発行前は投影値と明記し、発行後に実測値へ置き換える |
| B-8 | live 閉包 3 点という一般化は過大 | **real** | **採用**。「pilot 経路に限れば」と限定して記録する |
| B-9 | T-419 (1)(2) の混入 | なし | 両レンズが独立に 0 件を確認 |

## 実装する (段 5 / 6)

**W4 — resolver が見る index を committed-only にする。**
`_scan_floor_protocol_index_at_commit` の versioned entry 走査に、
「同じ固定 commit の exact 100644 blob として存在し、bytes が一致する」検査を足す。
untracked / dirty / HEAD 不在の entry は fail-closed で拒否する。
issuer の post-write 自己検査は full index scan に依存しない別経路へ分ける
(read-back、strict parse、導出 path、継承、canonical bytes は維持)。

**W5 — resolver の曖昧性解消。**
`resolve_current_floor_protocol` は `_head_commit_oid` を 1 回だけ解決し、その OID を
index 走査と `_ccbench_gitlink` の双方へ渡す。現行 env 契約に一致する候補集合 `C` を作り、
その部分集合として `ccbench_pin == HEAD gitlink` の `E` を作る。
`len(E) == 1` ならそれ、`len(E) == 0 and len(C) == 1` なら fallback、他は fail-closed
(`current_count` と `head_exact_count` を message に含める)。
辞書順・mtime・最大 pin・namespace 優先は使わない。公開 API は `root` だけ。

**W6 — `resolve-current-protocol` サブコマンド。** caller 引数を一切持たず、
解決した sanctioned relative path を 1 行出力する。`--path` / `--contract-sha256` /
`--ccbench-pin` / `--root` は argparse が拒否する。

**W1 — `s8b_holdout_admission._authority` を resolver 経由へ。**
literal `_PROTOCOL_REL` を外し、record の path から HEAD blob を読み、bytes と sha256 を
record と照合してから既存検査へ進む。resolver 失敗は cell claim 作成前に拒否する。

**W2 — `tools/pegasus/floor_campaign.sh:954` を resolver 経由へ。**
literal 代入を `resolve-current-protocol` の 1 回の呼出しへ置換し、
driver 引数・metrics 再読・job-result の 3 箇所で同じ値を共有する。
resolver 非 0 は `floor_protocol_resolution` として記録し、
`floor-driver.launch-attempted` を作る前に終了する。

**W3 — 残る 3 module は legacy 据え置き。** `s8b_prediction_runner._PROTOCOL_PATH` と
`s8b_ratified_freeze._SELECTOR_PROTOCOL_PATH` は `pre_oracle_head` の歴史 blob を読む証明鎖の錨定で、
移すと過去 journal の受理集合が変わる。`s8b_holdout_freeze.FLOOR_PROTOCOL_REL` は
producer write-path と closure 除外集合で、移すと生成 candidate の bytes が変わる (DW-O10)。

**W7 (親が実行、子には渡さない) — 実発行。**
統合 commit の後に `reseal-protocol` を実行し、artifact を commit してから
resolver・index・field 単位比較・byte 単位比較を実測する。
**W4 により、artifact は commit するまで resolver に見えない。** したがって
「発行 → 検証 → commit」ではなく「発行 → artifact 単体検証 → commit → resolver 検証」の順とする。
`FROZEN_MANIFEST` へは登録しない。

### 受理集合への影響 (DW-G05)

- **実装しない場合**: 床値 campaign は HEAD の ccbench pin (`511c9538…`) で build した成果物では
  1 件も走れない (`s8b_floor_campaign.py:6037-6040` が protocol の `ccbench_pin` を build へ再束縛する)。
  pilot result・材料レポート・試行台帳が HEAD の ccbench では生成されない。
- **実装した場合**: 受理集合は「legacy protocol を要求」から「HEAD pin の versioned protocol を要求」へ
  移る。緩まない — W4 が committed-only を課すことで、現状より厳しくなる面が増える。

## 裁定パッケージへ返す (実装しない)

- **R-a** driver CLI `--protocol` の caller 選択面 (A-3 / B-3)。公開 CLI 契約の変更を伴う。
- **R-b** official preflight (`_PREFLIGHT_FIXED_FILES` と `:3632`) の v2 接続 (A-2 / B-4)。
- **R-c** v2 candidate producer (`s8b_holdout_freeze:1293-1341`) の v2 接続 (B-5)。
- R-b / R-c は official mode の解禁が発火条件。解禁時に一括で配線するのが自然。

## 変異事前登録 (DW-M01)

| ID | 変異 | 位置 | 期待 |
|---|---|---|---|
| M1 | versioned entry の committed blob 検査を削除する | `s8b_floor_campaign.py` (W4) | KILLED |
| M2 | committed blob の bytes 一致比較を削除する | 同上 | KILLED |
| M3 | resolver の `E` を index 全体から作る (現行契約の絞りを外す) | 同上 (W5) | KILLED |
| M4 | resolver の fallback 節を削除する | 同上 | KILLED |
| M5 | resolver の複数候補 fail-closed を最初の 1 件返却へ替える | 同上 | KILLED |
| M6 | `_authority` の resolver 呼出しを literal へ戻す | `s8b_holdout_admission.py` (W1) | KILLED |
| M7 | `_authority` の record bytes / sha256 照合を削除する | 同上 | KILLED |
| M8 | shell の resolver 呼出しを literal 代入へ戻す | `floor_campaign.sh` (W2) | KILLED |
| M9 | shell の resolver 非 0 早期終了を削除する | 同上 | KILLED |
| M10 (正例) | `resolve-current-protocol` に `--path` を受理させる | `s8b_floor_campaign.py` (W6) | KILLED |
| M11 (正例) | resolver を「現行契約候補も HEAD pin 不一致なら拒否」へ厳格化する (過剰拒否) | 同上 (W5) | KILLED |

M10 / M11 は過剰受理・過剰拒否の双方の検出力を示す正例。
期待 node の完全集合は fix 後の最終 commit で `--junitxml` から再導出する
(probe 走は全件 SURVIVED 期待で登録する)。

## 段 5 の分割

| 単位 | 所有ファイル | 依存 |
|---|---|---|
| A | `orchestrator/campaign/s8b_floor_campaign.py`, `orchestrator/tests/test_s8b_protocol_builder.py` | なし (先行) |
| B | `orchestrator/campaign/s8b_holdout_admission.py`, `orchestrator/tests/test_s8b_holdout_admission.py` | A の resolver |
| C | `tools/pegasus/floor_campaign.sh`, `orchestrator/tests/test_pegasus_floor_tools.py` | A の CLI |

A を先行完了させ、所有パス限定 patch を展開してから B と C を並列投入する。
