# [T-2182] K2 アーム 1 本の走行記録 (2026-09-02)

親の運用記録。段 3 レンズ B が指摘したとおり、**「実際に role へ投入した」ことの機械証明は無く、
根拠はこの記録である。**

## 実施した手順 (run-procedure.md の S0 から S7)

| 手順 | 実施 | 結果 |
|---|---|---|
| S0 submodule を `028f34d` へ一時変異 | 実施 | 変異前 `--porcelain` 空を確認。変異は `external/ccbench` の単一 entry のみ |
| S1 campaign 識別子の検算 | 実施 | `p3-s4-loop-s4-autonomous-b6dde2ef`。run card と一致 |
| S2 planner context 出力 + 受領証生成 | 実施 | rc=0。受領証と `namespace.json` を生成 |
| S3 planner-v4 起動 | 実施 | 方向 `decrease` / magnitude `medium` |
| S4 coder-v4-autonomous 起動 | 実施 | `value=20`、`double now_backoff = 20.0;` |
| S5 1 iteration の実 build | 実施 (6 回投入) | condition gate の supply arm で停止 |
| S6 terminal verdict 確定 | **不成立** | gate へ到達しなかったため |
| S7 submodule 復元 | 実施 | `511c9538` へ復元、superproject clean、記録 pointer と一致 |

## 固定した成果物

- campaign 識別子: `p3-s4-loop-s4-autonomous-b6dde2ef`
- manifest digest: `6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406`
- 受領証: `/work/1/SFC/tanab/izanagi-exploration-t2182/exploration/campaigns/p3-s4-loop-s4-autonomous-b6dde2ef/knowledge_manifest_receipt.json`
  sha256 `f9a30d478405a700cf08d39215363be83833f6189057f5957ff21a5c2861a2f6`
- harness 権威の planner context: `s3-planner-input-authoritative.json`
  sha256 `7ec116f2feca06c6a4e98d42e3f832447cdefc00ab2ce46ad0636fc3f17d9bd7`
- planner 出力: `s3-planner-output.json` (逐語)
- coder 出力: `s4-coder-output-verbatim.md` (逐語)
- proposal: `proposal.json`

## 完了条件の達成状況 (正直に書く)

| # | 完了条件 | 達成 | 根拠 |
|---|---|---|---|
| 1 | 知識 manifest の受領証 | **達成** | 上記 sha256 の実物。source 2 件の commit / path / sha256 と observed_sha256 を持つ |
| 2 | 候補との provenance 束縛 | **未達成** | WAL の BUILD_START へ到達しなかった。機構は実装済みで変異 M4 / M5 が殺すことを確認済みだが、実走行での束縛は無い |
| 3 | stock と異なる identity | **未達成** | build へ到達しなかったため `src_token` が確定していない |
| 4 | 既存 gate が返した terminal verdict | **未達成** | compile / source identity / correctness gate のいずれにも到達していない |

**達成は 4 分の 1 である。** 受領証の存在だけを完了と読んではならない
(段 3 レンズ B がこの誤読経路を指摘し、親は裁定 C6 で明確に否定した)。

## K2 入力経路について言えること

**入力経路は端から端まで生きている。** 実物で確認した連鎖は次のとおり。

1. 知識 manifest (commit + path + sha256) を読み、raw bytes の SHA-256 を照合して解決した。
2. 受領証を create-only で出し、canonical manifest と observed_sha256 を残した。
3. `search_config` へ `knowledge_level` と `knowledge_manifest_sha256` を足し、
   campaign 識別子 `b6dde2ef` を導出した。manifest を渡さない経路の識別子は変わっていない。
4. `planner_context_payload` が `knowledge_input` を `whiteboard` の兄弟 key として出し、
   検証済み source の本文 (`content_utf8`) を運んだ。
5. 親がそれを規律 6 の枠付きで role へ渡し、planner と coder の両方が構造化出力を返した。

**両 role が知識を実際に使ったと自己申告した。** planner は過去 3 試行の値から勾配の向きを読み、
coder は測定済み 2 設定の間隔 10 を延長して 20 を出した。**これは role 自身の申告であって、
親が機械的に検証したものではない。因果は主張しない。**

**両 role が規律 6 の異常報告を返した。** いずれも「知識 source に指示めいた文字列・振る舞いの
誘導は含まれていない」と明記した。planner は加えて、入力の不整合 (whiteboard は空なのに
WAL には同 campaign の 3 試行がある) を報告した。これは K2 入力が harness の whiteboard 射影とは
別経路で入っていることの直接的な現れである。

## 評価経路について言えること

**評価経路は生きていない — ただし本 wave の変更が原因ではない。**

diff 検疫は通過した。condition gate の **meaning arm は通った** (`declared-meaning-observed`)。
**supply arm が止まった。** 停止点は環境の阻害要因を外すたびに前進した。

| 投入 | 実行場所 | 停止点 |
|---|---|---|
| 1 | login node | `supply=compiler-failed meaning=compiler-failed` |
| 2 | 計算ノード (env 未伝播) | 出力 root が worktree 配下と判定され停止 |
| 3 | 計算ノード | `supply=configure-failed meaning=declared-meaning-observed` |
| 4 | 計算ノード + gflags / glog | 同上 (masstree の FetchContent が git clone を試み network 不在で失敗) |
| 5 | 計算ノード + masstree offline | 同上 (mimalloc で同じ失敗) |
| 6 | 計算ノード + 3 依存すべて offline | **configure rc=0**、`supply=preprocess-failed meaning=declared-meaning-observed` |

## 走行を止めた 8 つの阻害要因 (いずれも本 wave の変更と無関係)

1. repo 内 `output/` は `.claude/worktrees` 配下のため materialization gate が拒否する。
2. `dev-wave-jobs/` 配下も `.git` 祖先を持つため exploration root にできない。
3. `wal.py` を未 commit で触ると `contract-loader-drift` で campaign lock 作成が落ちる。
4. `p3_s4_loop.PIN = 028f34d` と現行 submodule `511c9538` の乖離。
5. `compilers_for_current_site()` は site が Pegasus compute のときだけ `gcc`/`g++` を選ぶ。
   login node では存在しない `gcc-13` へ落ちる。
6. `dispatch_compute.py --task generic` の env allowlist は空で、独自 env var を伝播しない。
7. CCBench は `gflags` / `glog` を `find_package(REQUIRED)` で要求するがクラスタに無い。
   B-10 の正式 job script は job 内で pin 済みソースからビルドしている。
8. CCBench の CMake は masstree / mimalloc / googletest を `FetchContent` で git clone するが、
   計算ノードに network が無い。正規の third-party cache は存在するが、condition gate の
   cmake argv には `-D` を足せない。

## 打ち切りの判断

阻害要因を 1 つ外すたびに次が出る形であり、これは**段 4 loop のビルド系を Pegasus へ移植する
作業**である。段 4 loop は `linux-baremetal` 向けに作られており (`ENV_TAG = "linux-baremetal"`)、
runbook も Pegasus での正式採用には 4 つの前提 (専用 env タグ、calibration の取り直し、
binding の固定、provenance の追跡) が要ると書いている。いずれも未了である。

**この移植は [T-2182] の scope ではない。** ユーザーの引数は「本題の実装と 1 本の走行だけ。
仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と定めている。移植を続けるのは
本題の実装でも 1 本の走行でもない。したがって 6 回目の投入で打ち切った。

**コードは 1 行も変えていない。** 6 回の投入で行ったのは環境の用意だけで、
測定の意味を変える変更 (compiler の差し替え、pin の変更、gate の緩和) は 1 つもしていない。

## 主張の境界 (これを超えて書かない)

- **言える:** human-supervised な K2 入力経路が harness の端から role の入力まで生きている。
- **言える:** 段 4 loop の評価経路は Pegasus では supply arm より先へ進まない。
  停止点は環境の未移植であって、正しさの問題でも本 wave の実装の問題でもない。
- **言わない:** 候補が gate を通った。terminal verdict を得た。stock と異なる identity を得た。
- **言わない:** role が知識を使ったことの因果。K0/K1 への優越。de novo 合成。
- **言わない:** 本走の throughput (そもそも測っていない)。
- 本走は pilot であり比較集合から除外する。ただし除外を強制する consumer は存在しない
  (裁定 A13 のとおり、これは運用上の制約である)。
