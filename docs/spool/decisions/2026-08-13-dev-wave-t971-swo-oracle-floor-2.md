---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t971-swo-oracle-floor
seq: 2
---

## {{D:floor-oracle-dependency-transport}}. oracle の依存 root は明示 transport で受け、同一性は既存の凍結 pin で照合する

**決定:** 床値経路の SWO oracle が使う masstree source root は、明示引数または専用環境変数
だけで受け取る。floor policy へ path も HEAD も**書かない**。job は受け取った root の HEAD を
**凍結共有 `tools/pegasus/policy.json` に既にある pin** と照合し、`config.h` の regular file 性を
要求して sha256 を診断・marker へ記録する。compiler も同様に、floor が検証済みの `cxx` realpath を
`compiler=` で明示注入し、ambient `CXX` / `IZANAGI_SORT_SWO_CXX` に選ばせない。

**環境変数は transport であって authority ではない。** 所在だけを運び、同一性は既存の凍結 pin と
job 内の検査が決める。

**理由:**
- D152 決定 (3) が「cache root は明示必須とし policy から導出しない」と定めている。
  機体固有の値は環境専用 runbook に置く。
- masstree の pin は既に凍結共有 policy の `silo_ladder_rung1.third_party_sources` にあり
  (`pin` = `fetchcontent_ref`)、floor policy へ複写すると**同じ pin の正本が 2 つ**になる。
  D115 決定 (1) により共有 policy 自体は 1 byte も変えられない。
- oracle の compile は正しさゲートの一部なので、依存の同一性は判定に影響する。
  ただし masstree の `config.h` は上流 `.gitignore` が除外する**生成物で Git 非管理**であり、
  HEAD を固定しても中身は自由に変わりうる。HEAD pin だけを根拠に
  「受理集合は不変」と主張してはならない。
- 使い捨て checkout (`$TMPDIR` 配下) 上では `build/_deps` も祖先 fallback も届かないため、
  **明示 transport が唯一の解決経路**である。共有 checkout でしか成立しない祖先 fallback に
  依存し続けると、login で緑・計算ノードで赤という再現しない失敗が残る。

**却下した選択肢:**
- floor policy へ `masstree_source_path` / `masstree_expected_head` / `masstree_config_sha256` を
  足す — D152 に反し、pin が二重正本になる。
- 呼び手が repo root の sibling から cache を推測する — worktree 隔離下で誤る。
  generic campaign 層へ機体固有の配置を持ち込むことにもなる。
- 環境変数だけで同一性まで決める — 規律 6 に反する。外から来た path は data であって
  authority ではない。

**残余 (本 wave では閉じない):** compile closure の byte 封印と oracle receipt の proof chain 耐久化。
`expected config.h hash` をどこへ置くかは D115 (identity 非束縛の key だけ task policy へ) と
D152 (cache root は policy から導出しない) の双方に抵触しうる未解決の設計択一であり、裁定が要る。

## {{D:diagnostic-emission-never-masks-original-failure}}. 診断の生成失敗は元の失敗を置換せず、別事象として記録する

**決定:** 不可用の理由を成果物へ残す経路は、(a) 元の失敗の分類と終了コードを変えない、
(b) 診断そのものが失敗したら `diagnostic-emission-failed` として**別に**記録する、
(c) いずれの経路でも非ゼロ終了する、の 3 つを同時に満たす。診断 payload は bounded な
JSON primitive だけで構成し、full path は private artifact へ、durable / WAL 射影は
`origin` / `outcome` と機体非依存の値だけにする。

**理由:**
- 診断を足す変更は、握り潰しによって**元の失敗を隠す**方向へ倒れやすい。
  `result` が無い、payload が直列化できない、stdout が書けない、の 3 経路はいずれも
  診断ハンドラ自身が例外を投げうる。ここで元の例外が別の型に置換されると、
  「不可用だった」という一次事実まで失われる。
- 「診断が無い」ことと「診断が壊れた」ことは別事象であり、後者を前者に畳むと
  再発時にまた原因が分からなくなる。
- durable 側へ full path を流すと、機体・利用者固有の情報が恒久記録へ残り、
  試行参照の可搬性が壊れる。private artifact は `umask 077` かつ Git 管理外なので
  full path を残してよいが、同じ射影関数を無差別に再利用してはならない。

**却下した選択肢:**
- 診断の失敗を握り潰して元の例外だけ再送出する — 「診断が無い」ことに気づけない。
- 単一の `as_dict()` を durable と private の両方へ使う — 分離が規律ではなく偶然になる。
- 診断を実行履歴ファイルへ追記する — 再開状態機械の受理形を壊す構成がある。
  driver の標準出力は前提条件に依らず必ず存在し、書込権限にも再開契約にも依存しない。

## {{D:new-gate-must-not-reintroduce-opaque-failure}}. 不透明な失敗を塞ぐ wave は、自分が新設した前段が同じ不透明さを持たないことを確かめる

**決定:** 「失敗理由が成果物に残らない」ことを塞ぐ wave では、その wave が**新たに追加した
前段の検査**についても、失敗が構造化されて残ることを実装レビューの必須項目にする。
新設した検査が汎用例外で倒れるなら、その wave は自分が塞いだはずの穴を別経路で作り直している。

**理由:**
- 本 wave は oracle の不可用理由が残らない問題を塞いだが、同時に新設した依存 preflight は
  汎用例外で倒れる実装になっていた。しかも**計算ノードで最も起きやすい失敗要因**
  (共有 cache が見えない、生成物が無い) がその新しい経路を通る。
  結果として、直したつもりの症状が新しい場所で再現しうる状態だった。
- 敵対レビューが指摘するまで親も実装子も気づかなかった。検査の中身 (fail-closed か) は
  正しく、欠けていたのは「失敗理由が残るか」だけだったため、
  通常の正しさレビューの視線では素通りしやすい。

**却下した選択肢:**
- 「新設検査は元の scope 外」とする — 症状が同じである以上、利用者から見れば未解決である。
- 全 producer の例外を一律に構造化する族一般化 — 独立 2 例の再現がないため
  `DW-G03` に従い局所修復に留める。
