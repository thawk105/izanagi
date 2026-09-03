---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-loop-liveness-repo-external
seq: 1
---

## {{D:external-input-guard-by-content}}. repo 外入力の guard は根 directory でなく要求 file 集合で判定する

**決定:** テストが git 管理外の絶対 path を読むとき、skip 判定を次の形にする。

1. **要求集合は checked-in artifact から導出する。** file 名を test 側へ手打ちした literal 表を
   作らない。導出元がずれたら guard もずれるべきである。
2. **欠落は `os.stat` の `FileNotFoundError` だけを skip とする。** `Path.exists()` を使わない。
   同 API は `ENOTDIR` と `ELOOP` でも False を返すため、非 directory component や
   symlink loop という**構造的な壊れ方を「欠落」として隠す**。それらと権限エラー、内容不正、
   SHA 不一致は従来どおり失敗させる。
3. **guard の粒度は「その node が読む file」に合わせる。** 1 file だけを読む node を、
   無関係な file の不在で skip させない。
4. **skip 理由に欠けた relative path を列挙し、「完全な入力集合なら全 assertion が走る」旨を書く。**
   後から「テストを緩めて緑にした」と「外部入力が無いので測れなかった」を区別できるようにする。
5. **各 module に対照を 2 本置く。** 「root は在るが要求 file が 1 件欠ける → skip する」正例と、
   「完全な集合なら skip しない」対照。前者が root-only guard の偽実装を直接殺す。
6. **要求集合が exact であることのテストを置く。ただし期待値を guard と同じ factory から
   導出しない。** 導出すると恒真になる。

**理由:**
- 2026-09-01 に `~/.codex/sessions` の 2026/07 が剪定され、根 directory の有無しか見ない
  skip 判定が発火せず **26 node が hard red** になった。同時刻の別 wave 3 本も同数で落ちた。
  特定 wave の赤ではなく、**全 wave の land を同時に止める可用性障害**である。
- 外部測定 root は論文図の provenance 検証にも使われている
  (`/work/1/SFC/tanab/b10-backoff-grid-runs5` が 22 file の sha256 を支える)。
  ここが消えても同じことが起きる。
- `Path.exists()` を使うと、壊れた外部証拠木を「測定不能」へ再分類してしまう。
  それは絶対規律 2 が禁じる正しさゲートの緩和に接近する。

**却下した選択肢:**
- 根 directory の有無だけを見る — まさに 2026-09-01 の事故形である。
- guard を module 全体へ一律に掛ける — 1 file しか読まない node まで巻き込み、
  外部資源が部分的に在る環境で不要に検出力を失う。
- 例外を広く捕まえて skip する — 構造的な壊れ方を隠す。

## {{D:lexical-prefilter-must-normalise-nfkc}}. AST 発見の字句 prefilter は NFKC 正規化後の source に対して行う

**決定:** AST で発見した集合を字句 prefilter で絞り込むとき、判定は
`unicodedata.normalize("NFKC", source_text)` に対して行う。生の source text に対して行わない。

**理由:**
- Python は識別子を NFKC 正規化する (PEP 3131)。したがって
  `layout.ｅxploration_campaign_layout(x)` (先頭が全角 e、U+FF45) は、生 source に ASCII の
  `exploration_campaign_layout` を**含まない**のに、`ast.parse` 後の `Attribute.attr` は
  `exploration_campaign_layout` に**なる**。
- 生 source に対する prefilter はこの file を捨てるが、AST 経路は driver として発見する。
  **これは「族から外す条件」であり、D872 決定 1「編入は AST の発見だけで決め、除外述語・
  `skip`・名前による分岐を作らない」に抵触する。**
- NFKC 正規化後に判定すれば必要条件が回復する。識別子 token の境界は空白や ASCII 記号で
  区切られるので、識別子の NFKC 結果は source 全体の NFKC にも連続部分文字列として必ず残る。
- 費用は実測でほぼ変わらない。187 file に対して生 source 版 0.247 秒、NFKC 版 0.285 秒、
  無 prefilter 1.718 秒 (best-of-5、ログインノード単一 process)。**83.4% 削減**、
  正規化の追加費用は 0.038 秒、発見集合は 7 件で完全一致。

**却下した選択肢:**
- 生 source に対する部分文字列判定 — 上記のとおり必要条件を満たさない。
- marker を `run_campaign` や `CampaignLayout` にする — どちらも単独では必要条件でない。
  `p3_autonomous_workload_trial` は `CampaignLayout` branch で `run_campaign` を持たず、
  `p3_kickoff` は `run_campaign` branch で `CampaignLayout` を持たない。
- 実 repo を prefilter 有無で二重走査する既定テストを置く — 187 file を毎回 2 回 parse する
  新しい成長比例テストになり D335 に抵触する。固定本数 fixture で production 関数を
  両設定で呼ぶ形にする。
- 発見を遅延化する — `_CAMPAIGN_DRIVERS` は 5 箇所の `@pytest.mark.parametrize` へ
  `ids=` 込みで渡されており、collection 中に値が要る。遅延化できない。

## {{D:external-binding-census-stays-manual}}. repo 外束縛の全数走査 gate は新設せず、局所修復に留める

**決定:** テスト source を全走査して未登録の repo 外束縛を検出する gate を新設しない。
既知の束縛は module-local な内容 guard で個別に修復する。

**理由:**
- D335 は「repository の成長に比例して実行コストが増える構造のテストは新設しない」と定める。
  `orchestrator/tests/*.py` の全走査はこれに当たる。字句 prefilter を付けても
  345 file の `read_text` は残り、`O(file 数)` の構造は消えない (実測 0.610 秒、
  345 file 中 16 file を `ast.parse`)。
- **決定的な先例がある。** 既存の repo 全体走査 `test_campaign_import_invariant.py` は
  まさにこの理由で `growth_test_holds.py` に 6 node 恒久保留されている。新設すれば同じ扱いになり、
  保留されれば gate として機能しない。
- `DW-G03` の「異なる producer/consumer で独立に 2 件」も成立しない。git 履歴では
  dev-wave-jobs 系 2 file が同一作者・同日 (`56ae5e848` / `f24550a01`)、
  B-10 系 2 file が**同一 commit** (`637dafa17`) である。同型欠陥の独立再現とは言えない。
- 字句走査には原理的な限界もある。`output_snapshot_ignores.py:91-111` は
  `git rev-parse --git-path info/exclude` と `git config --get core.excludesFile` が返す path を
  読むが、これは string literal ではないので**どんな字句走査でも検出できない**。

**却下した選択肢:**
- 登録簿 JSON + 全走査メタ gate — 上記のとおり D335 と `DW-G03` の両方に抵触する。
- 全走査を保留登録簿へ入れて新設する — 保留された gate は発火しないので、
  「全数防護済み」という主張だけが残り実体が伴わない。より悪い。
- 何もしない — 既知の 4 file は 2026-09-01 と同型の穴を持っており、放置すれば
  外部 root の剪定で全 wave の land が同時に止まる。局所修復は行う。

**申し送り:** 「全数性を機械で保証したいが、その gate 自体が成長比例になる」というジレンマは
ユーザー裁定へ返す。0.610 秒・1 走 1 回 (collection ではないので 48 worker x 3 shard に
掛からない) という費用で D335 の明示例外を与えるかどうかは人間の判断である。
