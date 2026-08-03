# [T-342]+[T-343]+[T-344] provenance の capability 化 — 逐語

ユーザー裁定 3 件を一体で実装した dev-wave の逐語一式。設計判断の正本は `docs/decisions.md` の
「build provenance を source 由来 capability にし、admission を cache / replay / 選択の identity へ
束縛する」エントリ、経緯は `docs/worklog.md` の当該エントリ。ここは**逐語の凍結**であり、
可変状態は書かない。

## 段別の索引

| ファイル | 段 | 何か |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。scope・不変条件・成果物影響・provisional 裁定 (P1)-(P6) |
| `s2-plan.md` | 2 | codex read-only プラン (file:line 粒度)。親 brief への反論を含む |
| `s3-lens-a.md` | 3 | 敵対レンズ A = 受理集合。残る迂回路を分岐 file:line と対応付けて列挙 |
| `s3-lens-b.md` | 3 | 敵対レンズ B = 発火性と後方互換。**親の段 1 実測を反証した節を含む** |
| `s3-lens-c.md` | 3 | 敵対レンズ C = scope と成果物影響。裁定パッケージ候補を分離 |
| `s4-ruling.md` | 4 | **親の裁定。段 5 以降の唯一の契約。** 変異事前登録と正例を含む |
| `u1-report.md` 〜 `u5-report.md` | 5 | 実装 5 単位の完了報告。U1 の公開 API が後続の正本 |
| `s6-review-1.md` | 6 | 敵対レビュー 1 = 歯。Critical 2 件はいずれも overlay の中核 |
| `s6-review-2.md` | 6 | 敵対レビュー 2 = 回帰と検出力。変異 11 件の静的判定表を含む |
| `f1-report.md` 〜 `f3-report.md` | 6 | fix 1 巡目 (統合赤 290 件 → 18 件) |
| `g1-report.md` 〜 `g3-report.md` | 6 | fix 2 巡目 (敵対レビュー所見。gate 強化で 61 件へ増) |
| `h1-report.md` 〜 `h4-report.md` | 6 | fix 3〜4 巡目 (fixture を post-policy 形へ。0 件へ) |
| `h5-report.md` | 6 | fix 5 巡目。**受理集合を広げずに停止した報告** (no-build 正規形の不在) |
| `mutspec-report.md` | 6 | 変異 spec の作成報告。再照準 5 件の根拠 |
| `mutation-spec.json` | 6 | 変異 12 件の事前登録 (機械可読) |

## 読むときの注意

- `s1-brief.md` の「不変条件」1 と 3 は**段 3 レンズ B が反証した**。pin は 3 箇所でなく
  4 ファイル・7 field、凍結 doc の source pin は 63 record / 31 distinct path である。
  訂正は `s4-ruling.md` 冒頭と worklog 本文にある。**brief 単体を根拠にしない。**
- `s2-plan.md` の後方互換表と scope 提案は、親が `s4-ruling.md` §1・§3 で採否を裁定した後の形が正本である。
- 段 6 レビュー 2 の所見 7 (silo ladder の refusal 埋め込み) は**親裁定で却下した**。
  埋め込みは committed evidence の exact-key schema と driver sha 束縛を壊す。
- 実装子は共有ログインノードの規律により pytest を実走していない。**緑の根拠は親が計算ノードで
  走らせた受入全走だけ**である。子の報告にある「未実行」はそのまま読むこと。
