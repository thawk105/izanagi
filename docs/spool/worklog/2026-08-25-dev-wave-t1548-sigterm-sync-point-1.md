---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1548-sigterm-sync-point
seq: 1
title: [T-1548] SIGTERM 同期点を状態待ちへ作り替え、隔離台帳を空にして受入集合へ戻した (コード + テスト、branch worktree-dev-wave-t1548-sigterm-sync-point、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **親の段 1 の記述を 2 件撤回した。** 段 3 の 2 レンズが独立に同じ指摘へ到達した。
  (1) 「赤の機序は wall-clock 予算 2 本」は断定過剰だった。正しくは「**正常経路が依存する**予算が
  2 本」で、ほかに harness の hang timeout、SIGTERM 後の `communicate`、`_stop_process` の
  2 段、finally の wait がある。F57 の観測は rc=1 の 1 件で、どの予算が先に発火したかを示す
  phase 証拠を持たない。本 wave の原因記述は「F57 と整合する静的仮説」であって確定原因ではない。
  (2) baseline 焦点走 (112 passed / 1 skipped / 41.34 秒) は対象 node が skip された走行であり、
  再導入後の所要にも安定性にも外挿できない。
  「現状それを捕まえるテストは無い」も過大で、正しくは「**受入集合の中に** end-to-end の
  SIGTERM unwind を検査する node が無い」だった。

- **元テストが守っていたと親が数えた不変条件のうち 1 つが、実は守られていなかった。**
  段 6 レンズ A が実測外で見つけた。fixture の hang は pytest process 自身の sleep であり、
  process group に検査対象の子孫がいない。したがって harness の `os.killpg` を
  `process.terminate()` へ弱めても、rc・復元・ledger の全 assertion が通り緑のままになる。
  孫 process を runner の process group に置き、その消滅を検査する形へ直した。
  **変異 M3 がこれを実測で裏づけた** — 変更後は対象 node だけが赤になり、変更前 HEAD では SURVIVED する。

- **空 registry は隔離機構の attestation を消していた。** 段 6 レンズ A の最重要所見。
  controller は matched が非空のときだけ走行末尾の要約行を書くため、entry を消した瞬間に
  行自体が消え、「隔離ゼロ」と「隔離 hook が load / 配送 / 集約されていない」が同じ出力になる。
  空でも `0/0/0` と空 digest を必ず出す形にした ({{D:empty-flaky-registry-attestation}})。
  実測値は `registry_sha256` = `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。

- **契約テスト 15 本が、1 行退行で全部緑になる状態だった。** 段 6 レンズ B が
  `conftest.py` に registry view を空固定する 1 行を入れても 15 本すべてが緑になることを示した。
  注入 plugin と direct test が `conftest` の globals を直接上書きしていたため、
  台帳 module から collection への import 配線が非空状態で一度も通っていなかった。
  ほかに 3 つの穴 (production export が validator を呼ぶことの未 pin、受理条件 4 件の負例欠落、
  collection から summary への skipped 集約の未検査) も同レンズが名指しした。すべて塞いだ。

- **段 3 レンズ A の 1 件を refuted にした。** 「zombie を PID 消滅として受理するのは緩い」に対し、
  zombie は終了済みで実行できず、生存扱いにすると reaping の競合が入る —
  **本 wave が取り除こうとしている型の flake を持ち込む**。検出力も落ちない。
  問題の変異では孫は signal を受けずに走り続けるため zombie にならず、assertion は赤になる。

- **変異事前登録を 1 件差し替えた (erratum)。** 段 4 で登録した「export を
  `_validate_flaky_test_hold_rows(())` に固定」は、台帳を空にした後では
  `_FLAKY_TEST_HOLD_ROWS` が既に `()` なので **equivalent mutant** だった。
  DW-M02 に従い「validator を通らない raw 導出」へ実効 gate を再照準した。

- **判定量を実測前に訂正した。** 段 4 で凍結した負荷判定量は
  「calls に 3 が出てから SIGTERM まで」だったが、旧設計の窓は孫の `time.sleep(5)` 開始時点から
  5 秒であり、その位置は現在 marker を公開する場所と同じである。よって対応量は
  `readiness_to_sigterm_s`、副判定は Popen から marker までの `spawn_to_readiness_s` である。
  **負荷走を 1 回も行っていない時点での訂正**であり、測ってから基準を動かしたのではない。

- **1 回目の負荷実測は「負荷不足」と自己判定して破棄した。** 48 core に burner 44 本で 30 走し
  30/30 緑だったが、`readiness_to_sigterm_s` max = 0.0201 秒 (無負荷 0.0169 秒)、
  `spawn_to_readiness_s` max = 1.0596 秒 (無負荷 1.0486 秒) と**負荷ありと無負荷でほとんど差が無かった**。
  core が 4 本余っており被験プロセスが飢餓になっていない。**30 走緑は、その負荷が旧設計を
  壊せる強さであって初めて負荷耐性の証拠になる。** 凍結した基準どおり負荷を上げ直した。

- **burner をコア数超へ多重化した掃引で、旧設計が破れる水準を実測で特定した** (request `947101`)。
  全 45 走が緑である。

  | burner | 走行 | `readiness_to_sigterm_s` max | `spawn_to_readiness_s` max / median |
  |---:|---|---:|---:|
  | 0 | 5/5 緑 | 0.0182 | 1.0518 / 1.0475 |
  | 48 | 10/10 緑 | 0.0197 | 2.2839 / 2.2119 |
  | 96 | 10/10 緑 | 0.0186 | 3.1079 / 3.0759 |
  | 192 | 10/10 緑 | 0.0199 | 4.9760 / 4.8939 |
  | 384 | 10/10 緑 | 0.0228 | **8.8397** / 8.6657 |

  **旧設計の親側 5 秒 poll deadline は b384 で確実に超過する** (8.84 秒)。b192 でも 4.976 秒と
  上限の 0.5% 手前であり、F57 の実際の赤と整合する。
  一方 `readiness_to_sigterm_s` は 384 burner でも 0.023 秒のまま動かない。
  これは実験の失敗ではなく**発見**である — 新設計では親が marker 出現に即応するため、
  この量が負荷から切り離されている。
  **正確な主張は「旧設計が依存した 2 本の予算のうち親側 5 秒は実測で超過を示せた。
  孫側 5 秒窓は CPU 過負荷では破壊まで至らなかった。新設計はどちらも正常経路に無いため全域で緑」**
  である。「負荷でも壊れないことを一般に証明した」とは書かない。

- **DW-M08 の新旧両走で検出力の復活を直接示した。** 同じ 3 つの退行が、
  変更前 HEAD (`6d1d43ac`) では **3/3 SURVIVED** (対象 node が台帳で skip されるため誰も気づかない)、
  変更後 (`0298f367`) では **3/3 KILLED** になる。

- 子は 6 単位とも pytest 実走不能 (`qstat -Q preflight rc=1`、sandbox の構造的制約)。
  **本 wave のテスト結果はすべて親の実測である。** 子は全所見を partial と正直に申告した。

- 負荷 campaign script の author 子が 1 巡空振りした。親が出力先を job dir (repo 外) に指定したが、
  **Codex 子の sandbox は repo の外へ書けない** (`Read-only file system`)。
  repo 内に書かせ、親が実行後に退避する形へ変えた。これは `DW-O02` と凍結境界の衝突である
  (段 8 で扱う)。

- 変異 probe 走が F350 で rc=125 になった。親が変異走行中に別の子を走らせ、
  その子が worktree へ 2 file 書いたためである。probe のデータ自体は 6 変異とも完走して残っており、
  本走の `expected_nodes` はそこから採った。

## 次の一手差分

### 完了

- [T-1548] 隔離した SIGTERM テストを状態同期点へ作り替えて受入集合へ戻し、
  隔離台帳を空にした。負荷掃引で旧設計が破れる水準を実測し、新設計は全 45 走緑。
  変異 6/6 KILLED、旧 HEAD 走で 3/3 SURVIVED により検出力の復活を示した。
  remaining: none
  base: f7f37ac2f19817ad6622bc81ddf8dc64d0ecc41e2d901ee692debf0a1460c336
