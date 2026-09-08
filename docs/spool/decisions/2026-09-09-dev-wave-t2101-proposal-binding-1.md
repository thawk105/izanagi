---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2101-proposal-binding
seq: 1
---

## {{D:b4-bootstrap-proposal-binding}}. B-4 の提案束縛は bootstrap でだけ閉じ、continuation は登録値が別の対象を指すため返す

**決定:** D1343 の「実行ループが提案の canonical hash を再導出して封印 registry と照合し、
不一致なら実行前に拒否する」を、**formal B-4 の bootstrap 経路にだけ実装する。**
continuation では同じ等式を強制せず、束縛引数が渡された場合は拒否する。
continuation の閉じ方はユーザー裁定へ返す。

実装の形は次で固定する。

- 照合は base / sort / trigger の各 proposal loader 内に置き、既存の receipt gate と
  closed schema 検査の**後**、`drive_iteration` へ渡す前に行う。
- proposal file を開くのは各 loader で 1 回だけとし、同じ buffer から parse と hash の両方を導く。
- canonical hash は `attempt_registry_core.canonical_json_bytes` に parse 結果を渡した bytes の
  sha256 とする。束縛する同一性は **document exact value** であり、`1` と `1.0` は別の提案とする。
- 登録値は `load_b4_prerun_publication` が返す封印 registry から `attempt_id` が exact に
  1 件一致する行を選んで取り、その行の `driver` が実行中の driver と一致することも検査する。
- 束縛引数の欠落、publication の load 失敗、attempt の不在・重複、登録値の形式不正、
  driver 不一致、hash 不一致はすべて拒否する。素通しの分岐を作らない。

**理由:**

- 事前登録 §5.1 の適格性述語は「初期 proposal が、事前に固定した bootstrap 集合に属する」であり、
  同 §の `precursor_hash_mismatch` は 1 block の両アームが同じ `precursor_hash` を持つことを要求する。
  raw record producer は `precursor_hash` を registry の `initial_proposal_sha256` から出している。
  したがって**登録値が指すのは block 共有の初期 proposal**である。
- continuation で driver へ渡る提案は、critic pair を実行した後に main session が書く
  **アームごとに異なる次の synthesis** である。ここに同じ等式を強制すると、1 block の on / off に
  同一の提案を強制することになり、測ろうとしている treatment 効果を構成的にゼロにする。
  これは正しさ防壁ではなく実験そのものの破壊である。
- continuation で登録値を強制する唯一の筋は「この campaign を種付けした初期 proposal が
  登録値と一致する」の検査だが、**ループはそれを再導出できない。** checkpoint が焼く辞書は
  whiteboard の 5 field だけで、提案の値も実装も D39 決定 3 のリーク遮断として意図的に落としている。
  閉じるには耐久 carrier の新設かリーク遮断の設計変更が要り、いずれも本 wave の scope 外である。
- 照合を launcher へ前倒しする案は採らない。launcher が読んで driver が再度開けば、
  その間に proposal file を差し替えられる二重 open の窓ができる。単一 buffer は
  この窓を構造的に消す。
- 行選択で `driver` を照合するのは追加 gate ではない。`attempt_id` だけで引くと、
  sort の実行が base の登録行を引けてしまい、比較する登録値そのものが誤りになる。

**却下した選択肢:**

- **continuation の提案を `initial_proposal_sha256` と比較する** — 両アームに同一提案を強制し、
  treatment を構成的に消す。
- **continuation でも束縛引数を必須にし、行の実在だけ検査する** — 強制しない引数を要求するのは
  D1343 が問題視した「ラベルを付けるだけ」の再生産である。
- **照合を launcher へ前倒しする** — driver 側の再読取りと合わせて二重 open の差し替え窓を作る。
- **canonical 化を raw file bytes の hash にする** — D1343 は canonical hash を、D302 は内容の
  再導出を要求する。raw bytes では key 順や空白だけが違う同一内容が別の提案になる。
- **duplicate key を新たに拒否する** — 束縛するのは実行される提案 (parse 結果) であって
  file の raw bytes ではない。raw bytes の固定性は本決定が主張しない別命題であり、
  そのための検査を足さない。
