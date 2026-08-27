---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1997-real-build-manifest
seq: 3
---

## 新規

### {{F:verbatim-projection-elided}}. 親が「逐語」と称した射影資料を省略記号で切り、子の fixture に同じ穴が空いた [テスト代表性] [手順漏れ]

- 事象: 実 build の逐語を job dir へ射影する際、`.o.d` の中身を `...` で省略した。実装子は
  その資料に合わせて fixture を作ったため、実物に在る `../` を含む非正規化絶対 path を
  1 件も再現しなかった。採取器の正規化経路が一度も検査されない fixture である。
  段 6 の敵対レビューが「fixture と実物の 1 文字照合」で指摘して初めて判明し、fix 子を 1 巡追加した。
- 根本原因: `DW-O02` は「必読資料と前提の既裁定は逐語を job dir へ取り出して渡す」と定めるが、
  **その資料自体を要約・省略してよいかを述べていない**。親は読みやすさのために切り、
  切った側に検査対象の形が入っていた。子は渡された資料の外を再現しない。
  親の実測を「逐語」と称した時点で、子はそれを完全な標本として扱う。
- 恒久対応: (a) 親の永続 memory へ `verbatim-projection-must-not-be-elided` を登録した
  (セッション開始時に読み込まれる)。(b) 段 6 のレビュー prompt に
  「fixture と実物の 1 文字照合」レンズを置く — 本 wave はこのレンズだけが捕らえた。
  (c) `docs/dev-wave/operations.md` の `DW-O02` へ 1 文で入れることを試みたが、
  L1.5 層の unique footprint が 9716 bytes となり予算 9566 bytes を 150 bytes 超えた。
  自己改善契約は予算のために安全義務を削ることを禁じるため、reference への追記は行わず
  本項を正本とする (F300 の同型先例と同じ扱い)。
- 再発検知: 子へ渡す射影資料に `...` や「(省略)」が在るとき。渡す前に、切った側へ
  検査対象の形が無いかを確認する。長い資料は切らずに別 file へ置き絶対 path で読ませる。

## 再発

### F542

- **再発: 2026-08-27** — 同じ述語が 2 度目も実物と食い違った。F542 の恒久対応で張り替えた
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` / `FETCHCONTENT_BASE_DIR` 経路のうち、
  **BASE_DIR 分岐が実物では構造的に到達不能**だった。CMake は `FetchContent_Declare` の時点で
  当該 key を**空値の cache entry として必ず作る**ため、「行が無い」ことを BASE_DIR 分岐の
  条件にしていた実装は、実 `CMakeCache.txt` で必ず SOURCE_DIR 分岐へ入り絶対 path 検査で落ちた。
  F542 が「positive control は実環境と同じ形の CMakeCache を使う」と宣言した当の positive control
  (`test_masstree_source_root_accepts_base_only_shape`) が、実 CMake の出さない「行なし」形を
  使っていた。さらに `test_masstree_source_root_invalid_source_does_not_fallback` の `empty`
  parametrize が、実 CMake が必ず出す形を**拒否として固定**しており、fixture が実物と逆向きに
  固まっていた。計算ノード (CMake 3.25.0、job `951893.nqsv`) とログインノード (3.22.1) の
  実 build 2 例で確定した。F542 の「再発検知」は `DW-O13` の未適用を指摘していたが、
  今回は key の**存在**でなく key の**値**について同じ未適用が起きた。恒久対応は
  {{D:empty-cache-entry-is-unset}} (空値を未設定として読む) と
  {{D:mock-shape-must-come-from-the-tool}} (正例 fixture を道具の実出力から作る) の 2 件、
  および実 CMake 形を固定する正例・負例テスト群である。
