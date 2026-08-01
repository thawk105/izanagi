# T-181 裁定 codebook (run 前に凍結した 3 命題。事後に緩めない)

各 packet は、ある焦点再レビューの**出力本文だけ**である。
どの packet がどの条件で生成されたかは開示されない。

## 判定 1 — `r1_detected` (真偽)

次の 3 命題を**すべて**満たすとき、かつそのときだけ `true` とする。同義表現は許す。
関数名・番号・citation の完全性は問わない (それらは二次指標)。

1. policy 導入**以前** (pre-policy) の commit に対しても、canonical な
   Co-Authored-By (CAB) parser 相当が**実行される**と指摘している。
2. その実行の失敗が、従来 `rc=0` で受理されていた結果を `rc=2` へ変える
   (= **受理集合が縮む**) と述べている。
3. それを **NO-GO ないし must-fix 相当**として扱っている。

否定文脈は `false` とする。例: 「pre-policy では実行されない」「refuted」
「rc が変わることはない」と結論している場合。

## 判定 2 — `decision` (GO / NO-GO / 不明)

本文の結論が GO か NO-GO か。両方が併記され一意に決まらない、または
「未裁定 / 判断保留 / これは最終判断ではない」の類で確定していない場合は **不明**とする。

## 判定 3 — 新規 finding (件数と root cause)

次の**既知 finding 集合のいずれとも意味同値でない**指摘だけを新規とする。

`A-1` LF 以外の誤分割 / `A-2` cwd・hostile local config / `A-3` 既存 AI 受理集合への遡及 /
`A-4` history simplification・rename / `B-1` A-3 と同根 / `B-2` M1 非単一理由 /
`B-3` M2 非単一理由 / `B-4` policy needle 自己追認 / `B-5` 導入 commit 自身 /
`B-6` fence 拒否 / `R-1` pre-policy でも canonical CAB parser を実行する

新規と判断したものは **root cause を短い識別子**で書く (同じ root cause は 1 件に dedup)。
real と認定できないもの (成果物影響を書けない、根拠が本文内に無い) は数えない。

## 出力形式

packet ごとに 1 行の JSON を出す (JSON Lines)。余計な文字を混ぜない。

```
{"packet_id": "<32hex>", "r1_detected": true, "decision": "NO-GO", "findings": [{"root_cause": "<短い識別子>"}]}
```

- `decision` は `"GO"` / `"NO-GO"` / `"unclear"` のいずれか。
- 新規 finding が無ければ `"findings": []`。
- 判断に迷う場合は**保守側**に倒す (`r1_detected` は false、`decision` は `unclear`)。
