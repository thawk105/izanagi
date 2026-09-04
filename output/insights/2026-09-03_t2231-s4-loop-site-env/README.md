# [T-2231]+[T-2199] 段 4 loop へ site-aware な環境契約配線を移植する

`orchestrator/campaign/p3_s4_loop_trigger_gating.py` に既にあった site 対応の配線を
`orchestrator/campaign/p3_s4_loop.py` へ移植した wave の一次資料。**新設ではなく移植である。**

## 何が変わったか

計測用 env bytes を生成してよい site が、無条件から `{OTHER, PEGASUS_COMPUTE}` の exact set へ
**縮小**した。site=OTHER の campaign identity は 1 bit も変わらず、PEGASUS_COMPUTE だけが
`measurement_env` marker 付きの別 identity に分かれる。

## 構成

- `s1-brief.md` — 段 1 brief (親)。割れうる前提 P1〜P4
- `s4-adjudication.md` — 段 4 裁定 (親)。C0〜C11、plan v2、変異事前登録 13 件
- `s6-adjudication-addendum.md` — 段 6 裁定追補 (親)。D1〜D6、must-fix 5 件
- `mutation-spec.json` — 本走に使った変異 spec (期待 node は probe の実測から機械生成)
- `mutation-ledger.json.gz` — 変異本走の台帳全文
- `verbatim/` — codex 子の出力逐語 ([T-686] により placeholder guard・三軸語検査の対象外)
  - `s2-plan.md` (plan)、`s3-lens-a.md` / `s3-lens-b.md` (敵対相談)
  - `s5-author.md` (実装)、`s6-review-a.md` / `s6-review-b.md` (敵対レビュー)
  - `s6-fix.md` (fix)、`s6-merge-author.md` (main 取込みの合成監査)
  - `merge-message.txt` — Codex `role=author` が起草した merge message

## 実測で覆した前提 (親の誤りを 2 件訂正した)

1. **「移植は site 注入込みでなければ既存テストを壊す」は誤りだった。**
   `orchestrator/tests/conftest.py` の autouse fixture `_declare_default_test_site` が
   テスト中の hostname を無効化するため、`_current_site()` は機体によらず常に `OTHER` を返す。
   実走で確認 (焦点 3 件 + `test_p2_2_site_aware.py` 21 件が緑)。この訂正により、公開入口へ
   注入引数を足す新設 seam が不要になり、移植元と同じ 3 分割をそのまま写す形へ縮小した。
2. **段 4 裁定 C3 の「公開 `run_campaign` seam は本 wave 起因ではない」は不正確だった。**
   base 版では `default_cfg` が契約を bind 済みで、異なる契約の再 bind を `ident.py:113` が
   拒否していた。未束縛化によりその拒否が消えたので、base に対しては実際の受理拡大である。
   ただし `p3_s4_loop.run_campaign` へ `default_cfg()` を直接渡す production caller は
   repo 内に実在しない (親が実測)。よって新 gate は足さず、保証範囲を明示して閉じた。

## 保証範囲 (これは主張の限界であって、隠さず書く)

本 wave が保証するのは driver 自身の入口 (`main` / `drive_iteration` / 公開 `run_one_iteration`) を
通る経路だけである。**再 export された `run_campaign` への直接呼出しは保証しない。**
これは変異表 13 件が捕まえない拡大である。

## 変異の結果 (13/13 KILLED、期待 node と完全一致)

| 変異 | 内容 | 落ちた node 数 | 単一理由か |
|---|---|---|---|
| M1 | admission 述語を常に真にする | 4 | 過剰決定 |
| M2 | admission 述語から OTHER を落とす (過剰拒否の正例) | 39 | 過剰決定 |
| M3 | compute の marker 付与分岐を消す | 2 | 過剰決定 |
| M4 | marker を常に付与する | 21 | 過剰決定 |
| M5 | `run_campaign` へ契約でなく固定 env tag を渡す | 1 | 単一 |
| M6 | 同じく固定 clock を渡す | 1 | 単一 |
| M7 | 同じく固定 numactl を渡す | 1 | 単一 |
| M8 | authorization を固定 env tag で取る | 1 | 単一 |
| M9 | `default_cfg` の環境契約 bind を復活させる | 2 | 過剰決定 |
| M10 | 片側注入の `TypeError` を消す | 1 | 単一 |
| M11 | 注入 site の admission 検査を消す | 1 | 単一 |
| M12 | 注入 contract の env_tag 照合を消す | 1 | 単一 |
| M13 | compute で `env_contract` を転送しない | 1 | 単一 |

**単一理由と確認できたのは 8 件 (M5〜M8、M10〜M13)。** M1〜M4 と M9 の 5 件は複数の層が同時に
反応する過剰決定であり、`DW-M03` / `DW-M04` に従い単独変異の証拠から外して冗長 gate と明記する。
期待 node は probe 走行の実測から機械生成した (手で転記していない)。

## scope 外と裁定した real 所見 (実装せず carry へ送った)

1. **base B4 launcher の site 射影漏れ** — `orchestrator/campaign/p3_b4_launcher.py:165-170` は
   `driver_kind == "trigger"` のときだけ site 射影する。PEGASUS_COMPUTE では base の
   campaign ID が launcher context と食い違い、正式 B4 経路が build へ到達しない。
   両レンズが独立に発見した。OTHER では ID 不変なので現に動いている経路の回帰ではない。
2. **`_assert_layout_matches_campaign` / `_with_campaign_location` の移植漏れ** — production は
   `layout=None` なので露出は dry/test 注入だけで、compute でしか差が出ない。
3. `_assert_resume_allowed` と execution receipt の caller-side 永続化 (裁定 C6)。
4. `p3_s4_loop_sort.py` は依然として linux-baremetal の定数と契約を直接使う。
5. `site_policy.current_site(require_evidence=False)` の OTHER fallback (移植元にもある既存境界)。
