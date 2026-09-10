# 変異事前登録 v2 (DW-M01) — 段 6 レビューの帰属分析を反映

v1 (`mutation-prereg.md`) は段 6 レビュー前に登録した。レンズ D が**実装後のコードを読んで**
M4 / M5 / M6 の kill 意味論が成立しないと判定したため、`DW-M03` (kill は受理集合か
fail-closed 挙動が期待方向へ変わったときだけ数える) と `DW-M04` (両層変異は kill 期待を
必ず事前登録する) に従って再照準する。**v1 は消さず erratum として保存する。**

anchor は fix 統合後の最終 commit で `DW-M07` に従い再検証する。

## v1 からの変更と理由

| v1 | 処置 | 理由 (レンズ D、コード実読) |
|---|---|---|
| M4 (可視化先行を pin 側だけ戻す) | **単独 kill から外す** | production では inventory 層が拒否を継続する。pin helper のテストは赤くなるが受理集合は不変 |
| M5 (可視化先行を inventory 側だけ戻す) | **単独 kill から外す** | rc は pin 層が非ゼロに保つ。診断 finding だけの赤 |
| M7 (M4+M5 同時) | **B-02 の唯一の実効 kill として維持** | 両層同時でのみ hidden section が production で受理される |
| M6 (終端 allowlist を戻す) | **単独 kill から外し M10 へ再照準** | canonical literal 層が拒否を継続する。単独では受理集合が変わらない |
| M3 / M8 | 維持。ただし **S06 固有 nodeid の receipt を別記** | 既存 S02/S03 node も同時に赤くなるため、S06 固有性を件数でなく node で示す |
| (新) M9 | 追加 | canonical literal / 規範文 pin 層だけを外す単独変異 |
| (新) M10 | 追加 | M9 + 終端 allowlist 復元の両層同時。B-04 の実効 kill 候補 |
| (新) M11 | 追加 | F1 の raw HTML 可視化を戻す (pin + inventory 同時、F1 の実効 kill) |
| (新) M12 | 追加 | F4 の `DW-O16` effort 空 pin を外す |

## 本走で登録する変異

| # | 変異 | 層 | 期待 |
|---:|---|---|---|
| M1 | pin tuple から `DW-S06-A` を削る | 単層 | KILLED (S06-A production exact) |
| M2 | pin tuple から `DW-S06-C` を削る | 単層 | KILLED (S06-C production exact。F5 で新設) |
| M3 | exact-list 判定を membership へ弱める | 単層 | KILLED (S06 decoy node。S02/S03 も赤くなるので S06 node を別記) |
| M7 | 可視化先行を pin 側と inventory 側で**同時に**戻す | **両層** | KILLED (hidden whole-section production exact) |
| M8 | production path から pin 呼出しを削る | 単層 | KILLED (S06-A production exact) |
| M9 | 規範文 exact-one pin だけを外す | 単層 | KILLED (例示リンク decoy を受理する) |
| M10 | M9 + 終端 allowlist を旧 regex へ戻す | **両層** | KILLED (曖昧値を受理する) |
| M11 | raw HTML 可視化を pin 側と inventory 側で**同時に**戻す | **両層** | KILLED (`<x>` wrapper production exact) |
| M12 | `DW-O16` の effort 空 pin を外す | 単層 | KILLED (O16 に `reasoning=max` を足した負例) |

**参考のみ (単独走行、kill として数えない):** M4、M5、M6。
`DW-M02` に従い SURVIVED を記録し、mask の所在を台帳へ残す。

## 正例 (受理集合を縮小する wave の過剰拒否検出、DW-M01)

| # | 正例 | 期待 |
|---:|---|---|
| P1 | 実 repo の現行 docs (S02=max, S03=max, S06-A=high, S06-C=high, O16 に effort 無し) | 通る |
| P2 | S06-A / S06-C の可視 `high` + comment / fence 内の `max` | 通る |
| P3 | `DW-S06-B` に effort literal が無い現状 | 通る |
| P4 | 節内に `reasoning=` を含む URL / path があっても通る (C-03 の過剰拒否回帰) | 通る |
| P5 | `DW-O01` の `model_reasoning_effort="<効いた値>"` 雛形は拒否されない | 通る |

## 記録上の注意

- 台帳には「実効 kill」と「参考 (mask 済み)」を分けて書く。総数を水増ししない。
- v1 の M4 / M5 / M6 の登録と、その取り下げ理由を erratum として同じ台帳に残す。
