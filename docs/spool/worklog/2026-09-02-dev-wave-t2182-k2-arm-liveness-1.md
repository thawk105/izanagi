---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2182-k2-arm-liveness
seq: 1
title: [T-2182] 知識水準 K2 の入力経路は端から端まで生きていた。評価経路は段 4 loop が Pegasus へ未移植のため supply arm で止まり、完了条件は 4 分の 1 (code + docs、branch worktree-dev-wave-t2182-k2-arm-liveness、変異 5/5 KILLED)
---

## 本文

- **完了条件 4 つのうち達成は 1 つである。** 知識 manifest の受領証だけが実物として得られた。
  候補との provenance 束縛、stock と異なる identity、既存 gate の terminal verdict は
  **いずれも未達成**である。受領証の存在だけを完了と読んではならない。
- **K2 入力経路は端から端まで生きている。** 実物で確認した連鎖は、manifest の raw bytes SHA-256
  照合 → create-only の受領証 → `search_config` 経由の campaign 識別子導出 →
  `planner_context_payload` が `knowledge_input` を `whiteboard` の兄弟 key として出力 →
  親が規律 6 の枠付きで role へ渡す → planner と coder が構造化出力を返す、である。
- **両 role が知識を使ったと自己申告した。** planner は過去 3 試行の値から勾配の向きを読み、
  coder は測定済み 2 設定の間隔を延長して値を出した。**これは role 自身の申告であって親が
  機械的に検証したものではない。知識の因果は主張しない。**
- **両 role が規律 6 の異常報告を返した。** いずれも知識 source に指示めいた文字列は無いと明記した。
  planner は加えて、whiteboard が空なのに WAL には同 campaign の 3 試行があるという入力の
  不整合を報告した。K2 入力が harness の whiteboard 射影とは別経路で入っていることの現れである。
- **合成の経路は de novo ではない。** coder は既知の 2 設定の測定勾配を読んで外挿した。事前宣言
  どおり再現・選択に当たる。別の bytes であることは de novo の証拠にならない。
- **評価経路は生きていない。原因は本 wave の変更ではない。** diff 検疫は通過し、condition gate の
  meaning arm も通った。supply arm が止まった。停止点は環境の阻害要因を外すたびに
  compiler-failed → configure-failed → preprocess-failed と前進した。6 回投入して打ち切った。
- **走行を止めた 8 件はいずれも既存の性質である。** repo 内 `output/` が worktree 配下で拒否される、
  `dev-wave-jobs/` も `.git` 祖先を持つ、`wal.py` を未 commit で触ると contract-loader-drift、
  driver の PIN と現行 submodule pin の乖離、login node に対象 compiler が無い、
  generic dispatch が独自 env var を伝播しない、CCBench の gflags/glog がクラスタに無い、
  CCBench の FetchContent が network を要求する。
- **打ち切りはユーザーの scope 指定に従った判断である。** 阻害要因を 1 つ外すたびに次が出る形で、
  これは段 4 loop のビルド系を Pegasus へ移植する作業である。段 4 loop は `linux-baremetal` 向けに
  作られており、runbook も正式採用には 4 つの前提が要ると書いている。移植は本題の実装でも
  1 本の走行でもないため続けなかった。**コードは 1 行も変えず、gate の緩和も pin の変更もしていない。**
- **段 6 レビューが「受理判定の正本が closure 外へ漏れている」と判定し、親は主張を下方修正した。**
  `wal.py` は manifest digest の自己整合性しか見ておらず、実在しない commit から自己整合した
  provenance を受理する。Git object の実在と bytes identity の検証は closure 外の producer にある。
  閉じるには closure の所有範囲を変える必要があり、読み出し時に当該 commit が到達可能である保証も
  ない。規律 7 と D387 が「repo 内の挙動検査は完全な防壁ではない、限界は
  主張せず明記する」と定めているので、実装ではなく主張のほうを正確な形にした。
- **変異事前登録を 1 件差し替えた。** parser の SHA 照合を狙う変異は単一理由性が成り立たなかった。
  両レンズが独立に、無効化しても WAL writer の受領証照合が同じ不一致を拒否すると反証した。
  consumer 側の形状検査を狙う変異へ再照準した。
- **`wal.py` への変異は contract-loader-drift のマスクを 48 件作る。** 同 file は enforcement source
  closure に含まれるため、変異するだけで campaign lock を作る全テストが落ちる。変異に依存しない
  一定のマスクなので、runner argv を絞ってマスクを収集対象から外し単一理由の kill を取った。
- 受入は 19755 passed / 92 skipped で緑。変異 matrix は 5/5 KILLED、期待 node と exact 一致。

## 次の一手差分

### 更新

- [T-2182] **P1・部分完了**: K2 入力経路の生死確認は済んだ。残るのは評価経路で、
  段 4 loop のビルド系を Pegasus で通す前提 (専用 env タグ、calibration の取り直し、binding の固定、
  provenance の追跡) が未了である。この前提を作るか、`linux-baremetal` で走らせるかを決める。
  受領証・campaign 識別子・投入した role 入力・role 出力の逐語は保存済みなので、
  評価経路が通った時点で残り 3 条件だけを確かめればよい。
  base: c8b568f8ef3d403533c90648a826cd2969f02f83f18ec5f3b8b1c9c9043d27fe

### 新規

- {{T:s4-loop-pegasus-port}} **P1・新規**: 段 4 loop のビルド系を Pegasus で通す。
  本 wave が実測した 8 件の阻害要因のうち、環境で解けるもの (gflags/glog の事前ビルド、
  third-party の offline 配置、計算ノードでの実行) は job script 側で解けた。残るのは
  condition gate の supply arm が preprocess で止まる件と、正式採用に要る 4 前提である。
  移植せずに `linux-baremetal` を使う選択肢も併せて諮る。
- {{T:k2-role-contract}} **P2・新規**: K2 を宣言したアーム用の合成 role 契約を作る。
  現行 `coder-v4-autonomous` の遮断条項は「他実験の勝ち筋値・候補順位・未評価候補の性能を
  使わない」と定めており、真の K2 投入と必ず衝突する。本 wave は親が prompt で上位裁定を示して
  回避したが、role file の bytes は変えていないので K0/K1 のアームでは従来の遮断がそのまま効く。
  既存 role を書き換えるのではなく sibling role を足す形が、対照を壊さない。
  agent 登録は session 開始時に読まれるため、新 role を作った session では行使できない。
