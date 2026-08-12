---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t316-r2-oracle
seq: 2
---

## {{D:sort-swo-independent-oracle}}. sort comparator の SWO 検査は実型 harness で行い、文法判定は compiler に委ねる

**決定:** coder 自律ループが合成する sort comparator に対し、候補が制御する trace/stdout に依存しない
独立 oracle を build 前の gate として置く。実現方式は次の 4 点で固定する。

1. **実 `WriteElement<Tuple>` を使い、模擬型を置かない。** 実型は standalone TU で
   compile → link → 実行が成立する (`common.hh` を避け `-DGLOBAL=extern` を与えれば gflags 依存が消え、
   masstree の include dir と CCBench の define 群で足りる)。既定構築は `OpElement()` が
   `std::string` を null ポインタから作るため実行時 abort するので実 ctor を使う。
2. **comparator を字句抽出しない。** 候補の `sort(...)` 文をそのまま oracle の TU へ置き、
   `sort` を oracle 自身の関数 template へ名前解決させて comparator を第一級の値として受け取る。
   C++ の文法判定は compiler に委ね、構造検査は「単一の `sort(...)` 文であること」まで縮める。
   修飾形は名前解決を迂回するため reject する。
3. **判定は trusted 側で行う。** C++ 側は固定長 binary の relation matrix を専用経路へ返すだけで、
   公理判定は Python が行う。候補の stdout/stderr は判定に使わず破棄する。corpus の全 field bytes、
   要素 index、pair 座標、呼び出し順、反例の選び方は trusted 側が確定し、候補に許す制御は
   各 pair の `bool` 戻り値だけとする。
4. **返り値は `PASS` / `REJECT` / `UNAVAILABLE` の閉じた tagged result にする。** 判定不能を合格に
   しない。環境故障 (compiler 不在・trusted 正例 TU の compile 失敗・wall timeout・protocol 異常) は
   候補の `REJECT` ではなく `UNAVAILABLE` とし、候補の受理集合・fitness・試行台帳に混ぜない。

**主張の範囲:** 有限 corpus 上で SWO 公理の**反例を探す gate** であり、任意 C++ の全入力に対する
SWO の証明ではない。対象は coder 自律ループの合成 comparator に限り、s6 sweep の列挙候補
(SWO-by-construction かつ Python 有限モデルで全対検査済み) は対象外。fairness 型の機械観測点は
依然として未実装である。

**理由:**
- 模擬型を置くと「模擬では SWO を満たすが実型では満たさない」comparator が通る。field 名の一致は
  意味の一致を保証せず、`sizeof` / type trait / cast などで実型と分岐できる。実型を使えばこの穴は
  構造的に消える。
- 字句抽出は C++ の翻訳フェーズ (raw string・代替トークン・行連結・UCN・template 引数の `,` と `>`) を
  自前で再実装することになり、危険構文の誤受理と正当な合成の誤拒否を同時に招く。実際、v1 の抽出器は
  既存 fixture の `const auto&` 形 generic lambda を誤拒否していた。誤拒否は合成能力の実証 (D39) を
  削るため、受理集合の縮小と同じ重さで避ける。
- 候補が自分の実行結果を報告する形にすると、reward hack がそのまま通る。再計測・再検査を検証者側で
  行うのが独立 oracle の要件である。
- 判定不能を合格に倒すと、gate は恒真になる。環境故障を候補へ帰属すると、逆に台帳が偽の reject で
  汚れ、次の合成へ誤った修正指示が還流する。両方向を分けて閉じる。

**却下した選択肢:**
- **sort comparator への typed IR / AST allowlist** — 純粋な field 読取りと比較演算だけに制限すれば
  同一 process 内の干渉も閉じられるが、「合成」が「事前 allowlist からの選択」に化け、
  raw C++ comparator の独立合成という実証点 (D39) を別実験に変える。既裁定の非対称構成
  (sort は raw 合成維持) と非同値に衝突するため、親は決めずユーザー裁定へ返す。
- **pair ごとに子 process を起こして bool を 1 つだけ取り出す** — 干渉面は最小になるが、
  corpus サイズの二乗個の process が要り、gate の常時実行に見合わない。
  代わりに複数 corpus × 複数順序 × 別 process の relation 不変性と、corpus の呼び出し前後
  snapshot 照合で取れる分を取る。
- **C++ 側に公理名を出力させる** — 候補と同じ実行文脈が判定結果を作ることになり、独立性を失う。

## {{D:oracle-contract-in-campaign-identity}}. 受理集合を変える gate の契約 ID は campaign identity へ焼く

**決定:** 候補の受理集合を変える gate を導入したら、その契約 ID (corpus・TU template・compile flags・
checker version を束ねた値) を campaign の `search_config` へ入れ、gate 導入前後の試行が同じ
campaign identity に混ざらないようにする。導入前の campaign は歴史成果物として再開不可と明示する。

**理由:**
- 同じ identity のまま受理条件だけが変わると、材料レポートと proof chain が「gate を通っていない」
  旧参照を「通った」ものとして引く。
- 並行 wave との編集競合は、証跡の世代を分けない理由にはならない。競合は順序の問題であって
  設計の問題ではない。

**却下した選択肢:**
- **identity 据え置き** — gate が build 前に reject するので新しい非適合候補は入らない、という理由で
  一度は暫定採用したが、旧 identity 配下に既に記録された結果との混在を解けない。
