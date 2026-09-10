# 段 1 brief 追補 — 親が段 2 走行中に追加で実測した事実

brief.md と併せて読むこと。矛盾する場合は本追補が新しい。

## 追補 1 — 「どの oracle か」には答えが 2 つあり、片方は既に閉じている

repo には判定を行う oracle が 2 系統ある。

1. **s8b の選択 oracle** (`orchestrator/campaign/s8b_oracle_driver.py`)。
   こちらは **判定後の材料再取得を既に構造的に禁止している。** 実アンカー:
   - `_gate_check_core` の docstring (同 file 405-425 付近): 「freeze を再読込せず、その単一
     object の document/sha256 だけを使う (**A3-6: verify-use 間差替えの遮断**)」。
   - 同所: 「run-block から `verified_manifest` を与えた場合は manifest を再検証・再読込せず、
     その単一 object だけを使う (**C2-9**)」。
   - `_prepare_v2_execution` (同 file 913-925 付近): 「`validated` は run_block が一度だけ
     launch_validate して得た同一 object であり、**floor artifact の再読込・再 parse・
     再正規化は行わない**」。
   - `_t080_adapter_refusals` (同 file 224-232 付近): 「発火後の raw 再読で差替え・欠落を
     検出した場合は legacy へ戻さず migration 側の拒否にする」。

2. **floor の SWO oracle** (`orchestrator/campaign/sort_swo_oracle.py` を
   `s8b_floor_campaign.py` が駆動)。**こちらだけが未閉鎖である。** 依存材料 (masstree の
   HEAD / `config.h` / archive) を判定した後、cell build の cmake configure が同じ
   FetchContent base を再 populate しうる。現状の防壁は build **後**の内容再観測だけ
   (`buildcache.py` 2124-2151)。

**この非対称が本 wave の主張の核である。** 「判定と使用の間で材料を差し替えさせない」という
原則は repo 内に既に存在し (A3-6 / C2-9)、名前も付いている。本 wave はその原則を、
まだ適用されていない唯一の面 — floor SWO oracle の依存材料 — へ広げる作業である。
新しい原則の発明ではない。

### 子への含意

- 段 2 / 段 3 の子は、**新規設計を一から起こす前に A3-6 / C2-9 の実装形 (単一 object を
  持ち回り、再読込の経路自体を構造的に持たない) が floor 側にも転用できるかを検算せよ。**
  「flag を足して検査を書く」より「判定に使った材料の同一性を持ち回り、再取得の経路自体を
  無くす」ほうが、恒真化しにくいなら、そちらを推せ。
- 逆に、cmake は外部 process であり単一 object を持ち回れないという非対称があるなら、
  それを明記したうえで代替の閉じ方を示せ。

## 追補 2 — 親が独立に照合した exact 述語 2 件 (結果)

brief 表 E の 2 件について、親が条件式を読んで確かめた。子はこれを鵜呑みにせず再検算すること。

- `paper_story_a1_paired.py` `_trace0_commands_match` (1310-1380 付近): `len(configure_argv)
  != 10 + len(define_tokens)` の長さ検査に加え、`list(configure_argv) != expected_configure`
  の**完全一致**を要求する。index 9 に `-DCMAKE_PREFIX_PATH=` を期待しており、
  FetchContent 系 token が 1 本でも入れば壊れる。
- `paper_story_a2_certification.py` `_exact_trace0_configure_argv` (1295-1346 付近):
  `expected = fixed + prefix + ordered_define_tokens` に対する `list(argv) != expected` の
  **完全一致**。同じく FetchContent 系 token が 1 本でも入れば壊れる。

いずれも FetchContent base を渡さない経路なので、brief (P2) の条件付けが正しければ影響しない。
**「正しければ」の部分を子が検算すること** — base が渡る経路と渡らない経路の判定が、
argv 生成関数の実際の分岐と一致しているかを確かめよ。

## 追補 3 — 親の probe の regime

親の実測は login node の cmake 3.22.1、CCBench と同形の 1 引数 `FetchContent_Populate` を
使った使い捨て driver (repo 外) で行った。**実際に床値が走る計算ノードの cmake ではない。**
転移すると考えているのは「flag の意味論」であって「特定の版の挙動」ではない。
子はこの一般化の妥当性を攻撃してよい。床値が実際に使う cmake の解決経路
(`buildcache.compilers_for_current_site()` / toolchain manifest の `cmake` realpath) を読み、
版が違いうるか、違うなら結論のどこが揺らぐかを述べよ。

## 追補 4 — oracle は既に自分の材料を private copy している。穴は oracle と build の境界にある

`sort_swo_oracle.py` を読んだ結果、欠陥の所在がより正確になった。

- oracle の `dependency_root` は `<base>/masstree-src` そのものである
  (`_unavailable_result` が `environment.dependency_root / "config.h"` を読む、同 file 2655 付近)。
- oracle はその root に `SHA256SUMS` (`_DEPENDENCY_MANIFEST_NAME`, 89 行) を要求し、その manifest の
  sha256 が pin 定数 `DEPENDENCY_MANIFEST_SHA256` と一致することを要求する
  (`_prepare_verified_dependency`, 1897-1929)。
- そのうえで **oracle は材料を mode 0o700 の private root へ複製し、複製と原本の両方を
  再検証してから複製に対してコンパイルする** (同 1900-1929)。実行中の差替えに対しては
  `_assert_verified_dependency_unchanged` (1932-1943) がある。

**したがって oracle 自身は判定中の差替えに対して既に閉じている。** 未閉鎖なのは
**oracle と build の境界**である — oracle が PASS を出した後、cell build は private copy ではなく
共有の `<base>/masstree-src` を使い、その configure が再 populate しうる。

これは brief の主張を弱めるのではなく、**焦点を絞る**。禁止すべきは「oracle 判定後に、
**build が使う側の**材料が取り直されること」であって、oracle 内部の材料ではない。

### 子への含意

- 段 2 / 段 3 の子は、`_prepare_verified_dependency` が採っている形 (検証済み内容を持ち回り、
  取り直しの経路自体を無くす) を **build 側へ転用できるか**を検算せよ。
  できないなら、その非対称 (cmake は外部 process であり private copy を強制できない等) を
  実コードの根拠付きで述べ、そのうえでの最良の閉じ方を示せ。
- `SHA256SUMS` と `DEPENDENCY_MANIFEST_SHA256` は、build 側の事前検査が照合できる**既存の
  content 権威**である。新しい権威を発明する前に、これを使えるかを必ず検討せよ。
  使えないなら理由を書け。
