# 段 4 / 段 6 裁定 — [T-293]

軽量版のため段 2・3 の子は起動していない (DW-C00)。段 6 では敵対レビューを 2 レンズで実施した
(`s6-review-A.md` = 測定の妥当性・実コード性・fail-closed、`s6-review-B.md` = 副作用・親裁定への攻撃)。
**両者とも NO-GO を出した。親は全所見を real と裁定した。**

## 段 4 の所見と、段 6 レビューを受けた再裁定

| # | 所見 | 当初 | **再裁定 (段 6 後)** | 措置 |
|---|---|---|---|---|
| N1 | policy の候補 2 本は計算ノードには実在した (旧実測) | real | **real だが射程を 1 標本へ限定** (B6) | 引用証拠は 2026-07-19 (debug 867873) と 2026-07-29 (t141 873859) の観測。今日の probe も `hostname + epoch + policy sha` の 1 標本であり、gen_S 全 bnode へ一般化しない |
| N2 | login 側は解決順で `cc`(gcc-13) が先に落ち perf へ到達しない | real | **real (変更なし)** | probe の per-executable 解決で機械的に確定させる |
| N3 | T-293 の本質は「stale な値」ではなく「submit 前処理の実行サイト不一致」 | real (仮説) | **未裁定へ差し戻し** (B5) | `real (仮説)` は裁定ではない。**gcc-13 / g++-13 が両サイトに無いなら、perf の site を直しても qualification は cc で止まる** — 単因果として成立しない。今日の `real_prepare_toolchain` と per-executable 結果を見てから裁定する |

## 段 6 レビュー所見の裁定 (全 14 件)

**レビュー A (must-fix 3 / should-fix 3):** 1 (測定器の故障と否定結果の混同)、2 (非選択候補の機能未測定)、
3 (marker は測定完了の証拠でない)、4 (失敗段が一意でない)、5 (実行 bytes が期待値へ束縛されていない)、
6 (C1/M1 が false-success を検出しない) — **すべて real。全件 fix 対象。**

**レビュー B (must-fix 5 / should-fix 3):** B1 (C1 が login の perf 禁止と重量分類に抵触)、
B2 (出力の上書き・symlink 追従)、B3 (C1/M1 に kill の受理述語がない)、B4 (M1 の変異位置が一意でなく
復元契約も不成立)、B5 (N3 の裁定が compiler blocker を無視)、B6 (1 標本からの一般化)、
B7 (実行 source が commit へ束縛されていない)、B8 (NQSV の `.o/.e` が output 外へ出る) —
**すべて real。B1〜B7 は fix 対象、B8 は親の運用手順で閉じる。**

fix は 1 つの codex 単位 (`s6-fix-prompt.txt` の F-1 〜 F-7) へまとめた。横断所見のため分割しない。

## 変異事前登録の再設計 (DW-M01 / DW-M03)

**当初の C1 (ログインノードで probe を走らせる negative control) と M1 (候補読取箇所を `/bin/true` へ
一時変異) は撤回する。** 理由は次の 3 点であり、いずれもレビューが実証した。

- **B1:** ログインノードでの probe 実行は、候補が 1 本でも解決すれば `perf --version` と
  `perf stat` を login で実行してしまう。候補不在は期待値であって防壁ではない。加えて runbook §7.0 は
  「量が未知なら dispatch」であり、cgroup peak 未計測の probe を login で走らせる根拠がない。
- **B3:** C1 の `resolved:false` と M1 の `resolved:true` は**どちらも rc 0 / `ok:true`** で、
  fail-closed 挙動は変化しない。DW-M03 の「受理集合か fail-closed 挙動が期待方向へ変わる」を満たさず、
  kill と数えられない。`resolved = hostname.startswith("bnode")` のような policy を読まない定数でも
  C1 の期待差は通る。
- **B4:** `/bin/true` 変異の位置 (候補記録の行か resolver 入力の行か policy mapping 自体か) で
  結果が反転し、単一 anchor にならない。手編集 + `git checkout --` は DW-M05 の復元契約も満たさない。

**代替 (採用):** gate もテストも新設しない wave なので**変異 matrix は対象外**とし、代わりに
**同一 run 内 control** を probe 自身へ組み込む (fix F-6)。

- **控除法の control:** 実物の `_executable` を、存在し得ない control 候補列に対しても呼ぶ。
  同じサイト・同じ run・同じコードで `resolved: false` が出ることが、verdict が定数でなく
  **入力に駆動されている**証拠になる。`true` が出たら測定器の故障として `ok:false` / rc 非 0 にする
  (これは fail-closed 挙動の変化なので DW-M03 の意味で有効な受理述語である)。
- **受理述語 (親が段 6 で照合する):**
  1. `binding` の HEAD / policy sha256 が親の期待値と一致 (F-4)
  2. 全測定層の `attempted: true`、`ok: true`、probe rc = 0
  3. `control_resolution.resolved == false`
  4. `done-marker` が実在し、その rc が 0
  5. `probe.json` が parse でき、期待 field が完備
  上記のいずれかが欠ければ**測定失敗**として扱い、候補の可否を結論しない。

## 受入

実装差分があるため**受入全走は対象**であり、計算ノードへ dispatch する
(`tools/pegasus/dispatch_compute.py --task tests`)。ログインノードでは走らせない。

## 親の運用手順で閉じる項目 (B8)

- `qsub` は **repo root から**行い、`$PBS_O_WORKDIR` が repo root になることを確認する。
- NQSV の `.o` / `.e` が qsub 実行 dir へ落ちるので、job 終了後に**証拠 dir へ収容**し、
  worklog に会計痕跡の所在を書く (F49 (ii) (c))。
