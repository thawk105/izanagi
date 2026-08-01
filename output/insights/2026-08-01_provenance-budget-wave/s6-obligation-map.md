# 義務対応表 — 縮約前 (`18d7fc3` 版 8,942 bytes) → phase 2 後の family

親目録 O1〜O45 (`s1-parent-obligation-inventory.md`) の各義務が、分割後のどこに実在するかの逆引き。
略号は E = `docs/ai-provenance.md` (入口)、C = `docs/provenance/correction.md`、
A = `docs/provenance/audit.md`。**削除した義務はゼロ**である。

| 親 ID | 位置 | 備考 |
|---|---|---|
| O1 正本は commit message / worklog へ二重記録しない | E 目的 | |
| O2 導入 commit 自身と以後へ適用・既存履歴不変 | E 目的 | |
| O3 全 commit が末尾 trailer 1 行以上 | E 必須形式 | |
| O4 フィールド順・区切り固定、`;` と改行禁止 | E 必須形式 | |
| O5 最終段落に `AI-Agent`・本文任意・ここまでが機械検査対象 | E 必須形式 | |
| O6 CAB は空行なしで連続 | E 必須形式 | |
| O7 CAB 候補行はすべて最終 block / 件数照合し**一致しなければ拒否** | E 必須形式 | 逐語 (exactly-once)。「拒否」は段 3 C-03 で復元 |
| O8 trailer 形式 literal | E 必須形式 | `scope=` の唯一の出現 |
| O9 product 値 | E 必須形式 | |
| O10 model slug・正規化・`not-exposed`/`unknown`・**世代を推測しない** | E 必須形式 (共通則へ集約) | C-05 で復元 |
| O11 reasoning・**明示的に既定を選んだ場合の** `default` | E 必須形式 | A-07 で復元 |
| O12 role 5 種・複数役割は行を分ける | E 必須形式 | |
| O13 scope の意味・複数同 role 必須・非遡及・**checker も内容検出** | E 必須形式 | A-06 で復元 |
| O14 識別子正規表現 (**waiver の `reason` を含む**) | E 必須形式 | B-02 で追加 |
| O15 `AI-Agent: none` の 1 行 | E 必須形式 | |
| O16 `none` は唯一の `AI-Agent` trailer のときだけ有効・併記禁止 | E 必須形式 | A-03 で言い換えを却下し原文維持 |
| O17 導入後の trailer 欠落は規約違反 | E 必須形式 | |
| O18 実装面を変更する AI commit は Codex author 必須 | E Codex author 契約 | 逐語 (exactly-once) |
| O19 実装面の path・拡張子定義 (**`.md` / `.rst` 以外**) | E Codex author 契約 | B-03 で checker と一致させた |
| O20 test/checker/hook/probe 等も含む | E Codex author 契約 | |
| O21 codex author 行 / Claude 親の記録可能 role | E Codex author 契約 | |
| O22 docs-only 等は対象外 | E Codex author 契約 | |
| O23 小規模等は免除理由でない・不能なら停止しユーザー裁定 | E Codex author 契約 | |
| O24 waiver 形式・最終 block・`role=author` 併記 (+ **免除件数と理由の stdout / worklog**) | E Codex author 契約 | 逐語 (exactly-once)。運用義務は C-07 で追加 |
| O25 checker の path 照合・導入 epoch・`--message-file` の staged path | E Codex author 契約 | |
| O26 同一構成を人数分重複させない・scope で分ける | E 記録単位 | |
| O27 実質影響した構成だけ記録 | E 記録単位 | |
| O28 Git 操作代行は非記録・integrator / reviewer の判定 | E 記録単位 | |
| O29 CAB は代用不可・session URL 禁止 (裁定日と理由) ・`sessionUrl=false` | E 記録単位 | |
| O30 token / 料金は対象外・工数と棄却 finding の routing | E 記録単位 | |
| O31 rewrite せず strict descendant 1 件 | C PR-C01 | |
| O32 correction trailer の物理 1 行 | C PR-C01 | |
| O33 自身の `AI-Agent` と同じ最終 block | C PR-C02 | |
| O34 成立条件の連言 (自身の通常 green を含む) + **waiver 排他** | C PR-C02 | A-01 / B-02 で追加 |
| O35 allowlist・設定・CLI 免除へ拡張しない | C PR-C01 | 併せて「消費済み・新 carrier 禁止」を明記 |
| O36 両 commit を含む range か full-history が権威 | C PR-C03 | 入口 `history` から直接到達 (E-04 で追加) |
| O37 green 時に両 SHA を `forward-corrected=1` | C PR-C03 | |
| O38 構成を UI・CLI・設定・frontmatter で確認 | E commit 前の確認 | |
| O39 `not-exposed` / `unknown` / 推測禁止 | E commit 前の確認 (必須形式へのポインタ) | |
| O40 Git の trailer 解釈の確認例 | A PR-A02 | **義務ではない任意の補助手段**と明示裁定 (A-10) |
| O41 range の確認例 | A PR-A02 | 同上。`--format` の範囲版として保持 |
| O42 導入 commit から HEAD の checker 監査 | A PR-A02 | |
| O43 `--range` / `--message-file` / legacy 境界 | A PR-A01, PR-A02 | |
| O44 観察データであり優劣を断定しない | A PR-A03 | D105 却下案 (f) の歯止め。逐語保存 |
| O45 タスク種別を揃え他指標と併せて評価 | A PR-A03 | |

## 分割で新設された義務 (逆方向 map、C-07 の指摘)

| 新義務 | 位置 | 機械強制 |
|---|---|---|
| 全 commit で入口を読む | E 冒頭 | なし (規律) |
| 条件成立時だけ指定 reference の指定節を読む | E 条件 dispatch | dispatch 契約の逐語照合 |
| reference が不在・非一意・読取不能なら操作を止める | E 条件 dispatch | 欠落 / 重複 H2 の finding |
| forward correction の新しい担い手を追加しない | C PR-C01 | checker の candidate 1 件規則 |
| commit 前 preflight の rc=0 を確認してから commit する | E commit 前の確認 / A PR-A01 | `--message-file` の rc |

## 常時読量の実測 (4 指標、レンズ E の再計測に親が同意)

単一の削減率で語らない。`-29.6%` は入口単体の値である。

| 指標 | bytes | 旧 8,942 比 |
|---|---:|---:|
| family 合計 | 8,930 | -0.1% |
| 入口だけ | 6,287 | -29.7% |
| 入口 + `PR-A02` | 約 6,880 | 約 -23% |
| dev-wave 通常列 (入口 + `PR-A01` + `PR-A02`) | 約 7,090 | 約 -21% |
| 既定 full-history 監査で correction まで読む場合 | 約 8,070 | 約 -9.7% |
| reference をファイル単位で読む場合 | 8,930 | -0.1% |

「上限を上げていない」ことと「schema が同値である」ことは別である。旧受理集合は
「単一ファイル ≤ 9,000」、新受理集合は「入口 ≤ 6,300 / 各 reference ≤ 1,600 / family ≤ 9,000 +
三面 registry と dispatch の閉包」であり、**非同値 (狭い方向)** である。
