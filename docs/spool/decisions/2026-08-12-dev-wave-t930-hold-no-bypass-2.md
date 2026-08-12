---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t930-hold-no-bypass
seq: 2
---

## {{D:hold-two-layer-enforcement}}. 成長比例テストの保留は runner を問わず発火させ、解除は明示 opt-in 1 本に限る

**決定:** 恒久保留した成長比例テストは、pytest の起動形を変えても実行できてはならない。
保留の発火点を conftest の collection hook だけに置かず、**保留対象 module の読み込み時**と
**保留対象関数の呼び出し時**の二層に置く。

- 読み込み時: 保留 node を含む module は、enforcement を持つ pytest session の下でも、
  exact な解除 token の下でもないなら、**読み込みの時点で拒否する**。
  例外は `__main__` かつ plain runner が pytest へ委譲すると宣言した module だけで、
  その宣言は `__main__` の終端 statement が直接 `pytest.main(...)` へ委譲する形かを
  AST で機械照合する。
- 呼び出し時: 保留関数は registry 由来の wrapper で包み、exact token が無ければ本体へ入らない。
  読み込み時拒否を免れた経路 (直接 import して呼ぶ等) の最後の砦とする。
- 解除口は既存の 1 本 (`IZANAGI_RUN_GROWTH_HELD_TESTS` の exact token) だけとし、
  新しい env・CLI flag・設定ファイル・公開 API を追加しない。

**理由:**
- 保留の目的は成長比例コストを払わないことなので、**拒否メッセージが出ても本体前に高コストな
  fixture や helper が走るなら保留になっていない**。実測で、呼び出し時のみの拒否では
  `--noconftest` 経路が 38.01 秒かけて実 repository 全走査を完走してから拒否していた。
  読み込み時へ前倒しすると 2.33 秒で止まり fixture へ到達しない。
- 「conftest が読み込まれたか」を enforcement の証拠にしてはいけない。module の存在は
  hook の作動を意味せず、conftest を手で import するだけで解除できてしまう。
- 拒否は本体到達前に起きるため、封鎖のコストは repo 成長に比例しない。
- 二層にするのは、片方が構造的に届かない経路が互いに異なるためである。読み込み時は
  fixture 先払いを止め、呼び出し時は import 済み module や直接 call を止める。

**却下した選択肢:**
- conftest が置く sentinel を読み込み時の唯一の根拠にする案 — 敵対検証 2 本が独立に、
  conftest を手で import するだけで解除できると示した。
- 保留 node を含む module を丸ごと拒否する案 (module 単位保留) — 同じ module の保留対象でない
  test まで巻き添えにし、現に保留が正しく効いている plain 実行経路を退行させる。
- runner 側 (`_run()` 等) の harness を個別に改修する案 — 保留を知る責務を各 test file へ
  分散させ、file が増えるたびに付け忘れが発生する。registry 由来の一括結線と AST 照合にする。
- 期待値 literal に実行件数を焼き込む検査 — 無関係な test が 1 本増えるだけで赤になり、
  他 wave を偽赤で止める。意味契約 (rc・拒否 prefix の不在・skip の存在) で書く。

**適用範囲:** 封鎖対象は runner の起動形である。同一 process 内で任意コードを書ける者は
必ず回避できるため、それを防壁の要件にしない。production 側の保留機構はこの決定の対象外で、
env による解除口を作らない方針は従来どおり維持する。
