# 床値 v2 protocol を AI が実発行し、live consumer を resolver へ配線した — 材料 (2026-08-17)

wave = `dev-wave-t1255-floor-freeze` / branch `worktree-dev-wave-t1255-floor-freeze`

[T-1255] (実凍結) と [T-419] (3) (配線) の実装 wave の一次資料。
裁定の逐語控えは `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-17-rulings-full4-11rulings.md` の
第 1 項と第 5 項。

## 実発行したもの

| 項目 | 値 |
|---|---|
| path | `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json` |
| byte 長 | 774 |
| sha256 | `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a` |
| 組 | contract `e576e9cd…e242c01` (現行 pegasus 契約) / pin `511c9538…3b706ec` (HEAD の gitlink) |
| 発行 command | `python3 -I -B orchestrator/campaign/s8b_floor_campaign.py reseal-protocol` |
| 実行者 | AI (親)。tty も PTY 偽装も使っていない |

### 「`ccbench_pin` 以外 1 byte も動いていない」の実測

| 検査 | 結果 |
|---|---|
| field 集合 | legacy と 18 件で一致 |
| 値が違う field | **`ccbench_pin` のみ** |
| byte 差 | 40 bytes の pin 置換ちょうど 1 箇所 (残り 734 bytes 同一) |
| size | legacy / artifact ともに 774 bytes |
| legacy bytes | 不変 (`261cec1c…`) |
| repository の差分 | 新規 1 file のみ |

### 「旧 protocol を退けた」の実測

発行前: index 1 件、`resolve-current-protocol` = `output/s8b-freeze/floor_protocol.json`。
発行後: index 2 件、`resolve-current-protocol` = **versioned artifact**。
legacy は削除していない (`FROZEN_MANIFEST` 23 key と系譜 anchor が bytes を縛る)。
「退ける」を削除ではなく解決優先度の後退として実装した。

## 裁定の前提のうち、実測で失効していたもの

**裁定文が閂として名指しした `freeze_protocol` の `sys.stdin.isatty()` は、v2 実凍結の経路ではない。**

- v2 実凍結の実経路は零引数 public issuer `reseal_protocol()` (`230fc757`、2026-08-16 14:27 着地)。
  **tty gate を持たない。** 裁定 (2026-08-17 02:51) はこの着地より後に書かれたが旧関数を測っていた。
- `freeze_protocol` の destination は legacy anchor 自身であり、既存のため create-only で必ず失敗する。
  ここの tty gate を明示フラグへ替えても実凍結は 1 mm も進まない。
- **裁定 inbox の逐語ではユーザーの言葉は「床値の操作？あなたでできるものを私にやらせないで。」の 1 文だけ**で、
  `freeze_protocol`・tty・「旧 protocol を退ける」は rulings 側の親 AI が付けた分析である。
  したがって手段の訂正はユーザー裁定の上書きではなく、別 AI の分析の誤りの訂正にあたる。
- **実際の閂は 2 つあった。** (i) 発行すると現行契約に一致する候補が 2 件になり
  `resolve_current_floor_protocol` が fail-closed する (T-1218 の残る限界 1)。
  (ii) 解決先を versioned へ移すと、凍結成果物の権威が Git の commit から作業ツリーへ後退する
  (段 3 レンズ A が発見)。(ii) を塞がずに (i) だけ直すのは規律 2 違反になる。

## 実装

| # | 内容 | 位置 |
|---|---|---|
| W4 | index の versioned record を committed-only にする。固定 commit の exact 100644 blob から読み、作業ツリー bytes と完全一致を要求。未 commit・dirty・削除・mode 違いを fail-closed。issuer の post-write 自己検査だけ分離 | `s8b_floor_campaign.py` |
| W5 | 現行契約候補 `C` を作り、`len(C) >= 2` のときだけ HEAD gitlink を読んで部分集合 `E` を構成。`len(E)==1` ならそれ、`len(C)==1` なら gitlink を読まず返す (変更前と同値)、他は fail-closed | 同上 |
| W6 | caller 引数を持たない `resolve-current-protocol` サブコマンド | 同上 |
| C-1 fix | `IndexedFloorProtocol` に固定 commit OID を持たせ consumer へ伝播。admission は素の HEAD でなくその OID の blob を読む | 同上 + `s8b_holdout_admission.py` |
| D-1 fix | 供給 protocol が resolver の record と食い違う場合を**最初の副作用の前**に拒否 | `s8b_floor_campaign.py:run_campaign` |
| W1 | `_authority` を resolver 経由へ。解決 record・固定 commit の blob・供給 protocol の三者一致 | `s8b_holdout_admission.py` |
| W2 | shell の固定 path を resolver 経由へ。解決失敗・空・複数行・絶対 path は driver 起動前に停止 | `tools/pegasus/floor_campaign.sh` |

**据え置いたもの (移すと過去の受理集合や生成 bytes が変わる)**:
`s8b_prediction_runner._PROTOCOL_PATH` と `s8b_ratified_freeze._SELECTOR_PROTOCOL_PATH` は
`pre_oracle_head` の歴史 blob を読む証明鎖の錨定。
`s8b_holdout_freeze.FLOOR_PROTOCOL_REL` は producer write-path と closure 除外集合。

## 敵対検証の結果

| 段 | 子 | 判定 |
|---|---|---|
| 段 3 | レンズ A (正しさ防壁) | **NO-GO** (blocker 4) |
| 段 3 | レンズ B (裁定整合・実効性) | **NO-GO** (blocker 2) |
| 段 6 | レンズ C (門を緩めていないか) | **NO-GO** (blocker 1、major 3) |
| 段 6 | レンズ D (回帰・発行後の状態) | **NO-GO** (major 1、minor 3) |

**4 本すべて NO-GO を返した。** 親は所見ごとに real/refuted を裁定し、
must-fix 3 件 (A-1 / C-1 / D-1) を scope に入れて実装した。
段 3 の 2 本が根拠にした「ユーザー再裁定が要る」は、裁定 inbox の逐語で崩れた (上記)。

### must-fix にしなかった real 所見 (裁定パッケージ / backlog へ)

- **R-a** driver CLI `--protocol` の caller 選択面 (A-3 / B-3)。公開 CLI 契約の変更を伴う。
  ただし D-1 fix により、不一致は副作用の前に拒否されるようになった。
- **R-b** official preflight (`_PREFLIGHT_FIXED_FILES`、`:3632`) の v2 接続。
- **R-c** v2 candidate producer (`s8b_holdout_freeze:1293-1341`) の v2 接続。
- **C-3** 作業ツリーの mode drift (commit 後の `chmod`) を拒否しない。
- **C-4** 祖先 directory の symlink 差し替え競合。
- **C-2 / D-2** 単独候補で gitlink を読まない。**変更前からの挙動であり回帰ではない。**
  読むように変えると submodule を持たない一時 repository が全滅する (fix 1 で実測)。

## 変異 matrix

`mutation-spec.json` / `mutation-ledger.json` が正本。
runner scope = `test_s8b_protocol_builder.py` + `test_s8b_holdout_admission.py` +
`test_pegasus_floor_tools.py` + `test_s8b_floor_campaign.py` (`--force-dispatch`、`-rf`、dispatch runner)。
anchor commit = `9dcae82f`。

**本走 (round 3): baseline PASSED、KILLED 10 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0。期待 node と完全一致。**

| ID | 守っている性質 | 期待 node 数 | 結果 |
|---|---|---|---|
| M1 | 権威が固定 commit の blob にある (読み取り自体) | 3 | KILLED |
| M2 | 同上 (作業ツリー bytes との一致比較) | 1 | KILLED |
| M3 | `E` を `C` の部分集合として作る (stale contract を pin だけで選ばない) | 1 | KILLED |
| M4 | 単独候補への fallback (変更前との同値性) | 84 | KILLED |
| M7 | 権威不一致を副作用の前に拒否する | 1 | KILLED |
| M8 | shell が resolver を通る | 8 | KILLED |
| M9 | shell が解決失敗で driver を起動しない | 4 | KILLED |
| M10 | 曖昧時に先頭候補へ倒れない (= 旧 protocol が退いた性質) | 8 | KILLED |
| M11 | 解決後に HEAD が動いても固定 commit を読む | 2 | KILLED |
| M12 (正例) | 承認外の過剰拒否をしない | 1 | KILLED |

### 生存 2 件を等価変異と判定して再照準した経緯 (DW-M02)

probe 走 (全件 SURVIVED 期待、観測 node 収集) で 2 件が生存した。

- **旧 M5** (`len(head_exact) == 1` → `if head_exact`)。`head_exact` は現行契約で絞った候補を
  さらに単一の pin 値で絞ったもので、index の key が `(contract_sha256, ccbench_pin)` で一意なため
  **常に 1 件以下**である。件数判定を真偽判定へ替えても差が出ない = 等価変異。
- **旧 M6** (record の `commit_oid` 整合検査の除去)。全 record は同じ走査で同じ
  `commit_oid` を入れているため比較が構造上恒真 = 冗長 gate。

どちらも実効 gate へ再照準した (M10 / M11)。再照準後の SURVIVED は 0 件。

## 親の実測

| 走行 | 結果 |
|---|---|
| 焦点走 (実装 3 file + 凍結 pin) | 213 passed, 2 skipped, 0 failed (計算ノード 915295.nqsv) |
| 焦点走 (consumer 5 file、fix 前) | **81 failed** |
| 焦点走 (12 file、fix 5 後・発行前) | 1121 passed, 16 skipped, 0 failed |
| 焦点走 (12 file、**発行後**) | **1121 passed, 17 skipped, 0 failed** |
| 全史 AI provenance 監査 | rc=0、3926 件、新規違反なし |
| 変異本走 | baseline PASSED、10/10 KILLED |

## 段 6 で踏んだ回帰と、その意味

- **81 件 (fix 1)**: 新 resolver が `external/ccbench` の gitlink を**無条件に**読んだため、
  submodule を持たない一時 repository の fixture が全滅した。候補が 1 件なら pin を見ても
  結果は同じ record になるので、読み取りを `len(C) >= 2` まで遅延させて解消した。
- **3 件 (fix 3 / 5)**: 一時 repository の合成契約が世代レジストリから逆引きできず、
  さらに較正 artifact の path が content-addressed でなかった。fixture 側を既存の正しい作り方へ揃えた。
- **1 件 (fix 6 / 7、発行後にのみ発現)**: 歴史 seal 再生 E2E の複製が
  (i) 親 repository の gitlink を現 HEAD のまま持ち、(ii) 封印当時に存在しなかった versioned artifact を
  含んでいた。複製を封印当時の状態へ忠実化して解消した。実測した差分 path は
  versioned artifact の 1 件のみ (repository_files 13411 → 13410)。

**段 6 レビュー D は「発行後に赤くなる既存 node は 0 件」と根拠つきで断定したが、実測では 1 件あった。**
レビューは index / resolver を直接読む node を探しており、
「供給した protocol が admission で拒否される」形の破断は検索から漏れた。

## 親の訂正

段 4 で親は「official preflight と v2 candidate producer は official mode の CLI 拒否の背後で休眠」と
書いたが、**理由付けが不正確だった** (段 6 レビュー D による指摘)。
v2 candidate producer は独立した公開 CLI (`generate-v2-candidate`) から入れる。
休眠の実際の理由は、予算承認が未設定 (`BUDGET_APPROVAL_SHA256=None`) で official floor result が
0 件であること。休眠という結論自体は維持できる。

## 残る限界 (land しても閉じていないもの)

1. 上記 R-a / R-b / R-c は未接続。official 解禁時に一括で配線するのが自然。
2. 作業ツリーの mode drift と祖先 symlink 競合は拒否しない (防御的堅牢化として見送り)。
3. 単独候補では gitlink を読まないため、gitlink 欠落 repository でも protocol authority 段は通る。
   変更前からの挙動である。
4. 次に pin を前進させると versioned record が 2 件並ぶ。そのとき現行契約が同じなら
   HEAD pin exact が 1 件に決まるので解決は続く。契約も同時に変わる場合は未検証。

## erratum — 逐語の行末空白を可逆正規化した

`git diff --check` が `verbatim/` の 2 file で行末空白を検出したため、
**行末の空白だけ**を取り除いた (可視文字は 1 文字も変えていない)。
復元は各行の末尾へ元の空白を戻すことで行える。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 対象行数 |
|---|---|---|---|---|---|
| `verbatim/s3-lensB.md` | `c3444ec5cca1b0eba31cd8d2148979bbfc5de5b453da0efbd9394319df42ee84` | 11784 | `3ed0e537d771d5d0598ef1c3ba6aa7943dc009a25ec244a8acc758e191e6542a` | 11774 | 5 |
| `verbatim/s6-lensD.md` | `db5259fa4d1f86240d4870fd6ea8cc49409a89d352b7fbfe4725bb2a5748ed72` | 11324 | `92b6bc785d0a37b9aa7b72b358fe92e21b09cbfb65003b1acd45edae7eafd90e` | 11308 | 8 |
