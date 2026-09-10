# 段 4 裁定 — [T-897] build gateway の trigger axis semantic admission

裁定時刻: 2026-08-13 01:40 JST / base: `adf7997f` (main 取り込み済み)

## 0. 裁定を決めた実測 (親が段 4 で自ら測った)

**`GeneratorId` を増やすと凍結 bytes が壊れる。**
`_new_policy()` の preimage は `"generator_registry": sorted(member.value for member in GeneratorId)`
を含む (`build_admission.py:361-368`)。policy_sha256 は全 admission receipt body の field であり
(`:553-566`)、outer `receipt_sha256` を決める。つまり **enum member を 1 つ足すだけで、
過去・現在の全 admission receipt の SHA が変わる。** brief の不変条件 2 に真正面から抵触する。

→ **レンズ A の推奨 (iii)「characterization 専用の typed 状態を新 GeneratorId で分離」は
本 wave では実装不能**である。これは推奨の質の問題ではなく、凍結 pin 閉包の帰結である。

**emitter の 32 述語は要因 7 種のうち 5 種 + 番兵しか覆わない。**
`reflux_ir.py:38-54` の `_ENUM_MEMBERS` は 5 件、`axis_trigger_gating.py:41` の `REASON_NAMES` は
8 件 (`insert-node` / `scan-node` を含む)。したがって mask 31 と template 初期値 `true` は
**意味が一致しない** — `insert-node` / `scan-node` で前者は抑制せず後者は抑制する。
`true` は emitter 言語で表現不能な骨格の単位元であり、mask 31 での代替は不可。
そして「この 2 種が実際に起きない」ことこそ coverage driver が測る対象なので、
mask 31 で代用すると測りたい前提を答えに使う循環になる。

## 1. 所見の裁定

### レンズ A

| # | 判定 | 採否 | 理由 |
|---|---|---|---|
| F1 marker 不在 no-op が bypass | **real** | **採用** | marker を消す/大小を変えると骨格は残るのに no-op になる。骨格 token (`BACKOFF_TRIGGER_GATING` / `izanagi_gate_pass`) の残存を検出して reject する |
| F2 frame・`#if`・hole 外代入が未検査 | **real (部分採用)** | **block 逐語束縛で採用、hole 外代入は scope 外** | 下記 plan v2 の「block 全体 bytes 束縛」で N01/N03/N05/N09/N10/N11/N13/N14 を一括で閉じる。END 後の代入 (N12) は任意 C++ の検証になり境界が引けないため残存限界として記録し裁定パッケージへ |
| F3 splitter は正しい | **refuted (懸念が)** | 採用 (現行維持) | 長さ 0〜6 の全列で logical/raw 行数不一致 0 件という列挙を提示。私の「`split('\n')` とのずれ」懸念も同時に解消 |
| F4 missing root/file の no-op は不要 | **一部 real** | **非 ENOENT の reject だけ採用、ENOENT no-op は維持** | 偽 `SourceEvidence` は in-process caller であり、`build_admission.py` の docstring が明示的に scope 外と宣言済み。逆に ENOENT を reject にすると合成 evidence の既存 12 nodeid が赤くなる (レンズ B が列挙) |
| F5 `true` を裸の 33 番目にするな | **real** | **代替案で採用** | (iii) は §0 の実測で実装不能。block 逐語束縛付きの (ii) を採る (下記 §2) |
| F6 二重呼出しは snapshot を閉じない | **real (部分採用)** | **単一 read 化を採用、ABA は残存限界** | validator 内で raw bytes を 1 回だけ読み、同じ bytes で decode / parse / slice する。compiler までの ABA は既存の明示的残存境界として記録 |
| F7 経路 inventory の誤り | **real** | **採用** | 段 2 は S8b oracle を落とし `between_run_floor` (stock baseline) を混ぜていた。brief の 5 件が正 |
| F8 P1/P3/P4 refuted | **real** | 採用 | P1 は「marker 実在 → 軸」は真だが「marker 不在 → 非軸」が偽。P3 は hole だけでは不足。P4 は非 ENOENT で fail-open |

### レンズ B

| # | 判定 | 採否 | 理由 |
|---|---|---|---|
| 1 cache hit も gateway を再発火 | real | 情報として採用 | `require_build_admission` は cache 判定より前 (`buildcache.py:1273/1538`)。最大の攻撃面は既に閉じている |
| 2 `true` は sweep の stock 行も止める | **一部 refuted** | 影響を縮小して採用 | 実測: 既存 report で stock は既に `build-error` (`...c2d838b8/reports/...md:17`)。失われる能力は coverage / freq のみ、stock 行は abort reason 表記が変わるだけ |
| 3 (i) と (ii) は再現性が両立しない | real | 採用 (§2 で決着) | |
| 4 receipt bytes は保全可能 | real | 採用 (不変条件として維持) | |
| 5 P4 の実装順を誤ると fail-open | **real** | **採用** | `parse_template_file` は全 `OSError` を `None` にする (`diff_quarantine.py:557-561`)。raw 読取で先に切り分ける |
| 6 marker ≠ axis (`#if` 未検査) | real | 採用 (F2 と統合) | `TemplateMarker.frame_text[if_line]` で逐語が取れる (実測) |
| 7 既存テストは新 gate の帰属にならない | **real** | **採用** | 列挙された 11 nodeid は `pipeline._require_materialized_trigger_predicate` を直接呼ぶので、新 validator を消しても赤くならない。新 nodeid が必須 |
| 8 新 gate による既存赤は静的には空 | real (要実測) | 採用 (段 6 で実測) | |

## 2. `izanagi_gate_pass = true;` の裁定 — **(ii) を block 逐語束縛付きで採用**

**裁定: 受理言語 = {marker block が凍結 template の逐語 bytes と完全一致} ∪
{marker block が凍結 template と hole 行だけ異なり、その hole 行が emitter 32 出力のいずれかと
exact 一致}。それ以外はすべて reject。**

根拠:

1. (iii) は §0 の実測で実装不能 (policy_sha256 が壊れる)。
2. (i) は coverage / freq driver を恒久的に再走不能にする。両者の成果物
   (`s8a_trigger_gating_coverage.json` / `s8a_trigger_freq_t48.json`) は sweep の必須入力である
   (`s8a_trigger_sweep.py:136`)。正しさの利得ゼロで研究能力だけを失う。
3. **`true` は「33 番目の候補」ではなく骨格の単位元である** (§0 の実測)。emitter 言語で
   表現不能なので、これを含めることは候補空間の拡大ではない。
4. レンズ A の「裸の (ii) は無限個の source を通す」は正しい。**だからこそ hole 単独でなく
   block 全体の逐語束縛にする。** 束縛後に自由に残るのは block 外だけであり、
   block 外の任意 C++ は本 wave の scope 外 (§3)。
5. 規律 2 の判定: 現状 gate は存在せず全 source が受理される。新受理集合はその真部分集合であり、
   いかなる意味でも受理集合を広げない。

**残存限界 (worklog に明記する):** quarantine の置換が黙って失敗した candidate は pristine 状態と
区別できず、report が mask M を主張しつつ実バイナリは pristine になりうる。
現状は `s8a_trigger_sweep.py:449-456` と `s1_direct_comparison.py:564` の `res.passed` 検査が
先に捕まえるため live ではない。恒久的な分離には generator id の分離が要り、それは
policy_sha256 を壊すので別裁定 (裁定パッケージ RP-1)。

## 3. scope

**実装する (本 wave):**
- `build_admission.py` に共有 validator 1 本。`derive_build_admission` と
  `require_build_admission` の class 判定より前から呼ぶ。
- raw bytes を **1 回だけ** 読み、同じ bytes で decode / marker 走査 / block slice を行う。
  `parse_template_file` の再 open に依存しない。
- 受理述語 = §2。block 逐語は凍結 template patch 由来の定数とし、**patch の bytes と一致することを
  機械検査するテストを必ず添える**。
- marker pair の一意性は directive 行の regex で数える (ID を含む説明コメントに当たらないよう
  BEGIN/END directive だけを数える)。
- **骨格 token 残存検査**: marker pair が整合しないのに `BACKOFF_TRIGGER_GATING` または
  `izanagi_gate_pass` が file に残っていれば reject (F1 の N02/N08)。
- I/O: `FileNotFoundError` (root / 対象 file) だけ no-op。**他の `OSError` は reject。**
  `parse_template_file` を先に呼ばない (レンズ B 所見 5)。
- `validate_build_admission_receipt` には入れない (replay を壊す)。
- receipt の key 集合・bytes は 1 byte も変えない。

**実装しない (裁定パッケージへ):**
- RP-1: characterization と candidate の恒久的分離 (新 `GeneratorId` が要るが policy_sha256 を壊す。
  代替は policy schema の版上げか、pristine 受理の producer 束縛)。
- RP-2: marker block **外**の `izanagi_gate_pass` 上書き代入 (レンズ A の N12)。
- RP-3: derive/require から compiler read までの ABA 窓 (F6)。既存の明示的残存境界。
- RP-4: S8b の content-addressed binary store が admission を束縛しない (レンズ B)。
- RP-5: gate 導入前に生成された既存 artifact の遡及再検証 (レンズ B)。

## 4. plan v2 (実装子への指示の骨子)

1. `axis_trigger_gating.py` に凍結 template の block 逐語定数を置く (親の裁定: 定数 + patch 束縛テスト。
   import 時の patch file 読取はしない — 合成 root のテストと packaging を壊す)。
2. `build_admission.py`:
   - import 追加は `os`、`re`、`axis_trigger_gating` の定数群、`reflux_ir` の
     `TriggerGateIR` / `emit_predicate`。`diff_quarantine` は**使わない**
     (全 `OSError` を潰すため。走査は validator 内で自前に行う)。
   - 32 の期待 hole bytes は module import 時に 1 度だけ tuple 化する。
   - validator は `(evidence: SourceEvidence) -> None`、reject は `BuildAdmissionError`、
     エラー文は単一定数、`from None` で原因を秘匿。
3. `derive_build_admission` は `_source_map` 直後、class 分岐より前で呼ぶ。
   `require_build_admission` は exact 型検査直後、sealed body 検証より前で呼ぶ。
4. テストは `test_build_admission.py` に置く。**既存の
   `pipeline._require_materialized_trigger_predicate` を呼ぶ nodeid を流用しない**
   (レンズ B 所見 7 — 帰属が成立しない)。

## 5. 変異事前登録 (DW-M01)

**wave 前の実コードの形を必ず含める。** wave 前は「validator 呼出しが存在しない」形なので、
M1/M2 がそれに当たる。

| ID | 変異 | 期待 kill node (段 6 で実測再導出) | 先取り関係 |
|---|---|---|---|
| M1 | `derive_build_admission` から validator 呼出しを削除 (= wave 前の形) | derive 経路の負例全件 | gate 不発火 → 後段は従来どおり通る |
| M2 | `require_build_admission` から validator 呼出しを削除 (= wave 前の形) | require 経路の負例 | 同上 |
| M3 | hole 比較に `.strip()` を入れる | 外周空白 / tab の負例 | — |
| M4 | 1 物理行制約を削除 | 空 hole / 複数行 hole の負例 | — |
| M5 | mask 範囲を `range(31)` にする | mask 31 の正例 | — |
| M6 | CR を payload に残す処理を削除 | CRLF / CR 単独の負例 | — |
| M7 | block 逐語比較を hole 行だけの比較に落とす | frame 改変 / `#if 0` / 大小変更 marker の負例 | gate 発火が pipeline の mask 検査を先取りする点に注意 |
| M8 | 非 ENOENT `OSError` を no-op にする | 読取不能の負例 | — |
| M9 | 骨格 token 残存検査を削除 | marker 削除 / 大小変更の負例 | — |
| M10 | marker pair 一意性検査を削除 | 重複 block の負例 | — |
| **M11 (正例 / 過剰拒否検出)** | pristine block の受理を削除する | **characterization 正例が赤** | DW-M01 の「承認外の過剰拒否を検出する正例」 |

**先取りの数え方 (期待 node 導出時):** 新 gate が発火すると
`pipeline._require_materialized_trigger_predicate` の mask 検査、`buildcache` の
sidecar / manifest identity 検査は**走らない**。したがって gate を消す変異 (M1/M2/M7) では
後段の既存 node が代わりに赤くなる組合せがある。期待 node は段 6 の fix 後に
**実測で完全集合を再導出する** (DW-M07)。
