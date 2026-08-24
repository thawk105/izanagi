---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-paper-story-a2-cert-20260824
seq: 1
---

## {{D:a2-expected-argv-grammar-lives-in-policy}}. 検証専用の期待 argv 文法は versioned policy に置く

**決定:** 実測した argv を検証するだけで build を起動しない consumer は、期待する
configure / build の argv 文法を code 内の文字列 literal でなく versioned policy へ置く。
policy bytes は成果物へ同梱し、文法を pin された証拠の一部にする。比較の厳しさ (完全列一致、
未消費 token・分離 define・重複・未知 flag の拒否) は移動前と同一に保つ。

**理由:**
- 期待値の単一起点を policy に揃える方針と同じ性質の値である。code に literal を残すと
  policy と二重化し、片方だけが更新されうる。
- 成果物へ同梱される policy に置けば、文法は hash された証拠になる。code 内の裸の literal は
  成果物からは検証できない。
- 副次的に、`orchestrator/campaign/` 配下の .py を文字列走査する direct CMake census の
  偽陽性が消える。census は「CMake を起動する code site」を探すための近似であり、
  データ化した期待値はその対象ではない。真の検出力は減らない。

**却下した選択肢:**
- 検証専用 site を direct materializer として registry へ登録する — 既存の分類語彙
  (direct / delegating / coder entrypoint) に validation-only の受け皿が無く、既存登録は
  いずれも実 build seam である。偽の分類で gate を通すのは絶対規律 2 に反する。
- registry の語彙を拡張して validation-only の site kind を新設する — 共有 registry の
  意味論と census の判定条件に手を入れる一般改訂であり、同型欠陥の独立 2 例も無い。
- 上流の build 実装へ argv 文法の公開定数を新設して参照する — 上流は当該 token を複数箇所へ
  直書きしており、広く共有される file への定数新設は別 wave の scope である。
- literal を難読化して census を避ける — 検出回避であり採らない。

## {{D:a2-scheduler-absence-form-is-observed-not-assumed}}. scheduler の request 消滅形式は実測してから受理条件に書く

**決定:** 終端観測のうち「request が消えた」形式は、想定でなく実際の scheduler 出力を観測して
から exact な受理条件に書く。観測前に受理条件を書いた実装は、実形式を取りこぼしていないか
land 前に確かめる。

**理由:**
- この scheduler は存在しない request の照会に対し、非 0 でも空でもなく **rc=0・stderr 空・
  stdout に "does not exist" 行**を返し、その行は request ID を含む。
- 想定で書かれた実装は「消滅終端に request ID を含んではいけない」という逆向きの条件を持って
  おり、実形式を拒否していた。合成した空 stdout の fixture がこの不一致を隠していた。
- 取りこぼすと、正常終了した測定が終端として認識されず、成功した計測が成果物へ到達しない。

**却下した選択肢:**
- 消滅終端の受理を無条件に広げる — 未知出力・非 0 rc・非空 stderr まで終端に数えてしまう。
- 実形式の確認を計測の本走まで先送りする — 計算資源を消費してから初めて露見する。
