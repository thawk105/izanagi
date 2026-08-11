---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t316-semantic-gate-impl
seq: 1
---

## {{D:coder-hole-effect-gate}}. [T-316] coder hole に有限 lexical な効果 gate を置く — 測定済み 4 種に対する受理集合の縮小であって、裁定 案 2 の build 段防壁ではない

**背景 (実測).** 段 1 で sort 軸の実路 (`p3_s4_loop.quarantine`) に 1 行注入を通したところ、
`std::system` / `execl` / `std::ofstream` / `while(true){}` の 4 種が `DiffQuarantine` を
**4/4 通過**した。auditor が実 working_diff の digest を echo して `verdict="pass"` を返せば
auditor gate も **4/4 通過**する。backoff 軸の `assert_value_literal_consistent` も、value と
literal が一致していれば同居する任意文を 4/4 通す。この層に効果を見る検査は存在せず、既存の
注入テストは前処理指令と include の**構造**検査 2 件だけだった。

**決定 (1): 有限 lexical な効果 gate を `quarantine()` の単一 seam に置く。**
新規 `orchestrator/campaign/coder_effect_gate.py` が C++ tokenizer を持ち、exact identifier token
として 5 category (process-shell / file-stdio / network / sleep-block-thread / escape-hatch) を
拒否し、明示的に無条件な loop header を拒否する。lexer が解釈できない入力と、byte / token 上限
超過は固定 rule ID で fail-closed に倒す。`quarantine()` は structural quarantine が pass した
ときだけ scanner を呼び、finding があれば `DiffRejectSubtype.HOST_EFFECT` へ変換してファイル
書き込みへ到達させない。3 driver・2 sweep・direct comparison・extime calibration・autonomous
preview の全 hole materialization がこの seam を通ることを実コードで確認した。

**決定 (2): scanner が見るのは coder の hole 実装そのものであり、骨格を含む全文ではない。**
`edited_text` を渡すと CCBench 固定部の `open` / `read` / `write` / `thread` / `syscall` により
**恒真拒否**になる (段 3 レンズ A が `external/ccbench/include/fileio.hh` 等で実証)。
spy test と、materialized source から marker の hole を再抽出して byte-exact に比較するテストで
機械固定した。

**決定 (3): これは裁定 案 2 の build 段防壁ではない。** ユーザー裁定 案 2 (worklog 403) が
指定した別防壁は「source の DSL/IR 化」または「build 出力 copy-out の厳格化」の二択であり、
有限 lexical な効果 denylist は**どちらでもない第 3 の形**である。段 3 の 2 レンズが独立に
これを blocker と判定した。したがって本 gate は **測定済み 4 種に対する受理集合の縮小
(defense-in-depth)** としてのみ主張し、host-security boundary とも意味論的に閉じているとも
書かない。案 2 の build 防壁本体の択一は [T-316] の「次の一手」R-1 としてユーザー裁定へ返す。

**決定 (4): auditor は既に deny-only であり、本 wave は新しい安全性を獲得していない。**
段 3 レンズ A が実コードで示したとおり、変更前から machine reject は auditor より先に返り、
machine pass のときだけ verdict が評価されていた。`apply_mandatory_deny_only_veto()` は
その既存性質の factoring であり、加えて mutable dataclass の事後書き換えに備えて sink で
scalars と entries を再検証する。docstring は R1 の指定どおり
「mandatory deny-only veto; affirmative security credit なし」で固定し、**「advisory」と書かない**。
`diff_digest` は attribution/provenance 専用である。

**決定 (5): 非反射の対象は候補が自由記述した bytes に限る。**
`implementation`、そこから抽出した literal、例外 message、診断文は投影に出さない。
一方 `genome` の宣言済みスカラー `BACKOFF_FIXED` は**設計上の帰属フィールド**であり
(D39 決定 7 で campaign identity と fitness 帰属がこの値に依存する)、非反射の対象外とする。
opaque 化すると帰属が壊れる。**ただしこの帰属は整数値についてのみ健全である** — 段 6 の焦点
再レビューが、非整数 `coder.value` (例 20.5) が整合検査を通る一方 genome は `int()` で 20 を
記録することを見つけた。既存の欠陥であり本 wave では実装せず {{T:backoff-value-truncation}} へ送る。

**決定 (6): 閉じていないことを docstring に列挙する。** 未収載 identifier (`close` / `fsync` 等)、
`File(...)` のように constructor 内部が `open()` を呼ぶ型経由の間接効果、定数畳み込みを要する
無退出 loop header、macro token-pasting、走査対象より前に取得した function pointer、
deny table 外の compiler extension を残余として書く。`while (true) { break; }` を到達可能性
解析なしに保守的拒否することも書く。**scope 外・未閉鎖の層**も同じ docstring に逐語で並べる:
`p3_s4_red.py`、手動 patch + `--allow-coder-derived-build`、直接 `buildcache` caller、
`s5_permutation_coverage` の直接 CMake build、shell materializer と任意 binary path、
cache / WAL / COMMIT / freeze への gate 結果の非束縛、`forbidden_identifiers` の恒偽。

**決定 (7): critic には候補由来 text を出さず、allowlist 済みの構造化理由を通す。**
固定 `rule_id` / `category` / 件数を独立フィールドで WAL → loader → render へ渡し、
`read()` と `connect()` が別の理由として還流するようにした (規律 3)。remediation 文言は
「通過は計算のみを意味せず host 安全性を証明しない」と明記する。

**研究状態への影響:** 受理集合は狭まる方向にだけ変わる。現行の正常候補
(`s6_sort_sweep` の 15 件、`reflux_ir.emit_predicate` の全 32 wire、正常 backoff 形) は
すべて通り続ける (親が偽陽性 0 件を実測、焦点再レビューが最大 379 bytes / 64 token と独立確認)。
certified 選択の既存値、凍結 bytes、レポート数値、campaign identity、WAL golden は不変である。
**certified の安全性は主張しない** — sort の reward hack (R2-b 独立 oracle 未実装)、
cache / WAL / COMMIT / freeze への gate 結果の非束縛、`quarantine()` 外の materializer は
いずれも未閉鎖のまま残る。
