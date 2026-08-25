---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1641-t755-report-binding
seq: 3
title: [T-1641]+[T-755] TRACE=0 検査 report を pilot 受領証と job-result へ束縛した。転記でなく invocation との結合にした (コード + テスト、branch worktree-dev-wave-t1641-t755-report-binding、変異 matrix = baseline PASSED・23/23 KILLED・SURVIVED 1 (登録済み冗長 gate)・MISMATCH 0)
---

## 本文

- 起点は D779 (択 (a))。TRACE=0 の値を正式材料へ上げる前に、pilot の final receipt と job-result が
  checker report の path・SHA-256・schema・guarantee を束縛するようにする。[T-755] の残件だった
  verifier interpreter の実体 path の記録も同じ閉包で閉じた。
- **裁定の条項だけを実装すると証拠の鎖にならなかった。** 段 3 の敵対相談 2 本が独立に
  「report が自分で名乗った値を写しても、その検査がその保証を与えた証拠にならない」と反証した。
  親は D779 の理由節 (証拠の鎖として辿れない) を実装要件へ落とし、report の invocation identity を
  producer の実引数と照合する述語を足した。経緯は {{F:transcription-mistaken-for-proof-chain}}、
  設計は {{D:bind-report-to-invocation}}。
- **段 1 の前提実測が述語を 1 つ救った。** checker は `--repo` と `--cxx` を内部で realpath 正規化して
  いるため、渡した値をそのまま比較する述語は偽陰性になる。親が実 pair で checker を実走して
  発見した (`/usr/bin/g++-12` を渡すと report は `/usr/bin/x86_64-linux-gnu-g++-12` を名乗る)。
  測っていなければ実 PBS まで露見しなかった。
- **段 6 のレビュー 2 本が独立に同じ穴を挙げた。** 受領証の SHA を可変な sidecar ファイルにしか
  残していなかったため、受領証と sidecar を辻褄を合わせて同時に差し替えると三者照合を通過する。
  同型の穴が読み取り側にもあった (`islink` / `stat` / `open` が別 lookup)。恒久対応は
  {{D:immutable-path-for-check-and-use}}。
- **その修理自身にも同じ形の穴が出た。** 増やした照合 3 点のうち、単独で取り除いても SURVIVED
  したものが 2 点あった。shell 側は job-result writer が包含する冗長層、sidecar 照合は既存負例が
  受領証本体も一緒に書き換えるため単独の拒否理由になっていなかった。前者は冗長 gate と明記して
  単独変異の証拠から外し、後者には単一理由の負例を足した。{{F:redundant-gate-looks-like-coverage}}。
- **計算ノードで落ちる実装を焦点再レビューが止めた。** 前巡が入れた
  `os.path.realpath(..., strict=True)` は Python 3.10 以上でしか動かない。受領証 writer は
  `python3` を素の名前で起動しており、この計測系は計算ノードの既定 `python3` が 3.10 未満で
  実際に落ちた実績がある。拒否の中身を変えずに版依存だけを外した。
  {{D:no-3-10-only-api-in-compute-job-writers}}。
- 変異 matrix は 24 件登録、baseline PASSED、23 KILLED、SURVIVED 1 (登録どおりの冗長 gate)、
  MISMATCH 0、TIMEOUT 0。本走の 1 回目は MISMATCH 3 件だったが、期待 node の取りこぼしはゼロで、
  観測 pass の後に足した node が追加で赤くなったためである。現 HEAD の観測で登録し直して再走した。
- 逐語資料・変異 spec・台帳は `output/insights/2026-08-25_t1641-report-binding.md` と
  同 dir の `2026-08-25_t1641-mutation-{spec,ledger}-final.json`。
- 子の工数: plan 1 / consult 2 / author 1 / review 2 / fix 3 / focus 1。fix が 3 巡になったのは
  レビューが実装だけでなく**前巡の修理**にも穴を見つけたためで、いずれも real 所見である。

## 次の一手差分

### 完了

- [T-755] pilot script が選んだ verifier interpreter の実体 path を receipt へ記録する改修を実装した。
  TRACE=1 では選定済みの実体 path、TRACE=0 では未選定を表す null を
  `environment.verifier_interpreter_path` へ記録し、変異 M17 が単独で守る。
  記録するのは名前であって実行 bytes ではないという限界は insight に明記した。
  remaining: none
  base: e0eb0a8fbbffbe11535859ef9b365e9850debfda3bfc3474658cc466760452d5

### 更新

- [T-1641] **P1・producer 側は完了・昇格はユーザー裁定待ち**: pilot receipt と job-result へ
  checker report の path・SHA-256・schema・guarantee を束縛する実装は着地した。加えて report の
  invocation identity を producer の実引数と照合する。**ただし既存の TRACE=0 観測値は
  この改修では正式材料へ上がらない** — script の改修は将来の run にしか効かず、既存受領証に
  4 項目は増えない。旧受領証を書き換えれば SHA と create-only の歴史性が壊れる。昇格の道筋は
  {{T:trace0-promotion-path}} で裁定を仰ぐ。正本 = D779、
  実装 = `output/insights/2026-08-25_t1641-report-binding.md`。
  base: e0ef503fc2cb67c498844aa5d9953cb8337be21bd7d8e5b8be941adb12678d8b

### 新規

- {{T:trace0-promotion-path}} **P1・ユーザー裁定待ち**: 既存の TRACE=0 観測値を正式材料へ
  上げる道筋を決める。択は (a) 束縛を実装した script で再計測する、(b) D779 を改めて
  append-only の事後 attestation を認める。親は決めない。[T-1641] の producer 側実装は着地済みで、
  この裁定だけが昇格を止めている。
- {{T:mocc-promotion-consumer-gate}} **P2・ユーザー裁定待ち**: 材料レポートを書く経路に gate が
  無いため、producer が 4 項目を出しても D779 の関門は実効発火しない。加えて job-result が
  拒否されても `status=completed` の受領証は残るので、昇格側は受領証単体でなく
  受領証 × job-result × failure 不在の積で判定する必要がある。mocc 用の昇格 validator または
  材料記述規約を作るかを裁定する。
- {{T:interpreter-identity-closure}} **P3・裁定済み・据え置き**: interpreter の bytes 級同定
  (実行 bytes・version・checker source bytes) は、D780 の別防壁 ([T-1642]/[T-1644]) と同じ閉包で
  だけ設計する。path の記録は producer 実体の同定と同じ保証ではない。単独 wave にしない。
- {{T:independent-gate-vs-defensive-invariant}} **P3・新規**: 前段の相互排他的分岐で値が固定されて
  いる防御的 invariant と、独立に発火する gate を、変異事前登録の段階で分けて数える規律を検討する。
  本 wave では 3 点の照合のうち 2 点が単独発火しないことを実走で確認しており、区別しないと
  検出力を過大に見積もる。
