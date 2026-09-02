# [T-2182] 知識水準 K2 のアーム 1 本の生死確認 (2026-09-02)

wave: `dev-wave-t2182-k2-arm-liveness` / branch `worktree-dev-wave-t2182-k2-arm-liveness`
tested tip: `d61e97e30`。受入: 19755 passed / 92 skipped。変異 matrix 5/5 KILLED。

## 一行で

**K2 の入力経路は端から端まで生きていた。評価経路は生きていない** — 段 4 loop の
ビルド系が Pegasus へ移植されておらず、condition gate の supply arm で止まる。
完了条件 4 つのうち達成は 1 つである。

## 完了条件の達成状況

| # | 条件 | 達成 | 根拠 |
|---|---|---|---|
| 1 | 知識 manifest の受領証 | 達成 | 実物。sha256 `f9a30d478405a700cf08d39215363be83833f6189057f5957ff21a5c2861a2f6` |
| 2 | 候補との provenance 束縛 | 未達成 | WAL の BUILD_START へ到達せず |
| 3 | stock と異なる identity | 未達成 | build へ到達せず `src_token` が未確定 |
| 4 | 既存 gate の terminal verdict | 未達成 | compile / identity / correctness のいずれにも未到達 |

**受領証の存在だけを完了と読んではならない。** 受領証は planner context の出力だけでも作られる。

## 固定した run card (走行後に変えていない)

- campaign 識別子 `p3-s4-loop-s4-autonomous-b6dde2ef`
- manifest digest `6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406`
- 知識 source 2 件 (いずれも commit `2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` の repo artifact)
  - `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/campaign.lock`
    sha256 `0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9`
  - 同 campaign の `runs/wal.jsonl`
    sha256 `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611`
- workload: YCSB rratio=50 / zipf 0.9 / rmw=false、records=100000、threads=4、extime=1、reps=2
- source と hole: `include/backoff.hh`、marker `silo-backoff-magnitude`
- 分類の事前宣言: 再現・選択、de novo 主張なし
- 出力 root: `/work/1/SFC/tanab/izanagi-exploration-t2182`

出力 root は走行前に 1 度訂正した。当初値は `.git` 祖先を持つため resolver に拒否され、
**1 command も走らなかった**。走行後の変更ではない。

## 入力経路について実物で確認した連鎖

1. manifest の raw bytes SHA-256 を照合して解決 (working tree ではなく commit の blob を読む)
2. create-only の受領証を出力。canonical manifest と observed_sha256 を保存
3. `search_config` へ知識水準と manifest digest を足し campaign 識別子を導出。
   manifest を渡さない経路の識別子は変わらない
4. `planner_context_payload` が `knowledge_input` を `whiteboard` の兄弟 key として出力し、
   検証済み source の本文を運ぶ
5. 親が規律 6 の枠付きで role へ渡し、planner と coder が構造化出力を返す

## role の応答 (逐語は `verbatim/`)

- planner: 方向 `decrease` / magnitude `medium`。過去 3 試行の値から勾配の向きを読んだ。
- coder: `value=20`、`double now_backoff = 20.0;`。測定済み 2 設定 (40 と 30) の間隔 10 を
  延長して 20 を出した。
- **両 role が知識を使ったと自己申告した。これは role 自身の申告であって、親が機械的に
  検証したものではない。知識の因果は主張しない。**
- **両 role が規律 6 の異常報告を返した。** いずれも知識 source に指示めいた文字列は無いと明記。
- planner は加えて、whiteboard が空なのに WAL には同 campaign の 3 試行があるという入力の
  不整合を報告した。K2 入力が harness の whiteboard 射影とは別経路で入っていることの現れである。
- **合成の経路は de novo ではない。** 既知の 2 設定の測定勾配を読んで外挿した。事前宣言どおり
  再現・選択に当たる。別の bytes であることは de novo の証拠にならない。

## 評価経路の停止点 (6 回投入した実測)

| 投入 | 実行場所 | 停止点 |
|---|---|---|
| 1 | login node | `supply=compiler-failed meaning=compiler-failed` |
| 2 | 計算ノード (env 未伝播) | 出力 root が worktree 配下と判定され停止 |
| 3 | 計算ノード | `supply=configure-failed meaning=declared-meaning-observed` |
| 4 | 計算ノード + gflags / glog | 同上 (masstree の FetchContent が network 不在で失敗) |
| 5 | 計算ノード + masstree offline | 同上 (mimalloc で同じ失敗) |
| 6 | 計算ノード + 3 依存すべて offline | configure rc=0、`supply=preprocess-failed` |

diff 検疫は通過した。condition gate の **meaning arm は全投入で通った**。

## 走行を止めた 8 件 (いずれも本 wave の変更と無関係)

1. repo 内 `output/` は `.claude/worktrees` 配下のため materialization gate が拒否する
2. `dev-wave-jobs/` 配下も `.git` 祖先を持つため exploration root にできない
3. `wal.py` を未 commit で触ると contract-loader-drift で campaign lock 作成が落ちる
4. driver の PIN と現行 submodule pin の乖離
5. `compilers_for_current_site()` は site が Pegasus compute のときだけ system compiler を選ぶ。
   login node では存在しない版へ落ちる
6. generic dispatch の env allowlist は空で、独自 env var を伝播しない
7. CCBench は gflags / glog を `find_package(REQUIRED)` で要求するがクラスタに無い
8. CCBench の CMake は masstree / mimalloc / googletest を FetchContent で git clone するが、
   計算ノードに network が無い。condition gate の cmake argv には `-D` を足せない

7 と 8 は job script 側で解けた。正規の third-party cache は存在し pin も一致していた。
**コードは 1 行も変えず、gate の緩和も pin の変更もしていない。**

## 実装側で分かったこと

- **`wal.py` への変異は contract-loader-drift のマスクを 48 件作る。** 同 file は enforcement
  source closure に含まれるため、変異するだけで campaign lock を作る全テストが落ちる。
  変異に依存しない一定のマスクなので、runner argv を絞って単一理由の kill を取った。
- **受入赤 4 件はすべて内容走査型の一覧検査だった。** 名前 grep では見つからない。
  新規 test file の自走 harness 不在 1 件、新しい process 起動点の未登録 2 件、
  driver の layout 呼出し宣言のずれ 1 件。
- **受理判定の正本は完全には closure 内に無い。** `wal.py` は manifest digest の自己整合性しか
  見ておらず、実在しない commit から自己整合した provenance を受理する。Git object の実在検証は
  closure 外の producer にある。この限界は主張せず明記する (規律 7、D387)。

## 主張の境界

- **言える:** human-supervised な K2 入力経路が harness の端から role の入力まで生きている。
- **言える:** 段 4 loop の評価経路は Pegasus では supply arm より先へ進まない。停止点は
  環境の未移植であって、正しさの問題でも本 wave の実装の問題でもない。
- **言わない:** 候補が gate を通った。terminal verdict を得た。stock と異なる identity を得た。
- **言わない:** role が知識を使ったことの因果。K0/K1 への優越。de novo 合成。新しい CC。
- 本走は pilot であり比較集合から除外する。ただし除外を強制する consumer は存在しない。
  これは運用上の制約である。
