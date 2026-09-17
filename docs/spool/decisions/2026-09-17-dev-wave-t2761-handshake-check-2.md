---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2761-handshake-check
seq: 2
---

## {{D:path-independent-word-absence-check}}. 生成 script への語不在検査は、環境値を位置限定で除いた本文へ掛け、検出語の候補行を全件拒否する

**決定:** `_job_script` の出力に対する `release` 不在検査 (FA-4 の「親→job の release handshake を作らない」の代理検査) は、
次の形を標準とする。

1. **環境依存の埋込み値だけを、その埋込み位置で除く。** 検索は「改行 + 代入名 + `shlex.quote(str(path))` の完全表現」、
   置換は環境由来の部分だけを token (`<REPO>` / `<SUBMISSION>`) にし、固定 basename・固定 suffix・production 定数
   (`DC._COMPUTE_MARKER_NAME`) は置換文字列に残す。行ごとの削除、`str(path)` の全域置換、環境依存でない値 (job name) の置換はしない。
2. **置換の前提が崩れた入力は保守的に拒否する。** 各検索文字列は出現数がちょうど 1 で、直後が shell word 終端
   (改行・空白・tab・`;`・`&`・`|`・末尾) でなければ赤にする。厳しくする方向だけで受理を増やさない。
3. **検出語を含む行を全件列挙して空を要求する** (大小無視、assert メッセージに該当行)。「marker を操作する release 行」
   に限る狭い同一行共起は採らない — 旧検査が拒否していた `RELEASE=1` 単独行・comment・alias 経由の複数行待機を見逃し、
   規律 2 (検査を甘くしない) に反する。構文解析をしたとは説明しない (候補行の保守的拒否)。
4. **正例対照を test 自身に持たせる。** 検出語を含む合成 path (実在不要) で parametrize し、環境値の偽赤を test が守る。

**理由:**
- F1022 は「語 1 つの不在で構文の不在を代理させ、検査対象に環境依存文字列 (repo path) が混ざる」ことが根本原因で、
  wave 名の暫定防壁 (memory) は機構でない。位置限定の除去は、環境値の偽赤を消しつつ template 由来の検出力を落とさない。
- 固定部分を残す置換は、production 定数の改名 (`compute-visible.release`) を隠さない (login probe で実測)。word 終端の
  前提検査は、環境値の接頭辞に template 側の文字が連結される境界 (`/…/rele` + `ase`) を旧検査どおり拒否する (同 probe)。
- テスト強化でなく偽赤是正の wave では、DW-M08 の新旧両走は「新 baseline が合成 release path を受理、旧検査を復元した
  変異が同 path を拒否 (偽赤の再現)、handshake 注入は新旧とも拒否」の 3 点で示す。旧 HEAD の別 container への注入走を
  含める (「新テストだけが検出する差分」は存在しない旨を台帳に書く)。

**却下した選択肢:**
- `str(path)` の全域置換 — 値の後ろに足された handshake 構文まで消しうる (規律 2)。
- 行ごとの削除 — 同上。
- job name (`#PBS -N`) の置換 — pytest `tmp_path` 由来で環境依存でない。置換すると `izdw-` 定数を隠す。
- 引用値内部を除外する代入位置 parser — 改行を含む一時 dir path で置換前提検査が偽赤になる経路は残るが (段 6 レビュー A-1)、
  現実の basetemp に改行と自 repo path の埋込みは生じない仮想リスクで、本題の検査置換を超える (DW-G05)。既知の限界として記録。
- `"while" not in script` の同型是正 — 依頼が名指す release 検査だけを置換し、`while` の path 反転は別件 (裁定パッケージ候補)。
