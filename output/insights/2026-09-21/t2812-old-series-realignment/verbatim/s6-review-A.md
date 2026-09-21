## must-fix

以下、`README` はレビュー対象本文、コードの短縮名は `orchestrator/campaign/` 配下。HEAD は `5efd69367`。静的検査のみで、テスト・probe の再実行はしていない。

1. **real — S' の第3入口は、批准系列に限定する設計が閉じていない。**

   `README:79` は `b4_binary_record.place_record → store_binaries` を追加したが、現物の `b4_binary_record.py:169–173` は **receipt 自身から期待 pin・contract を取得する**。同入口には批准済み object や manifest を受け取る引数もない。

   したがって `README:78,92` の「receipt 由来の pin を期待値にしない」をこの入口でどう満たすか未定であり、`:105` の「他系列・他 consumer へ広げない」も実装範囲として確定できない。相談 B の配置経路の指摘は、入口名の追加だけでは閉じていない。

   **修正要求:** 検証済み chain からの pin・contract・対象 record の束縛、既存12 binaryの取得元、配置先 root、manifest の `store_path`・hash との対応、欠落時の拒否を明記する。一般の B-4 place／floor producer は現行 policy のまま保つ境界も示す。根拠は `b4_binary_record.py:149–175`、`s8b_floor_campaign.py:5825–5836`、`s8b_oracle_driver.py:1026–1052`。

2. **real — N 案は official 再測定の既裁定上の停止条件を落としている。**

   `README:101,109,119` は「successor commit → build・official → 新凍結・批准」と示す。しかし **D2120 項2(a)** は当該 holdout 集合の official 走行を打ち切り、chain を含む main と継承 checkout では clean scan が赤になり、後続 official は別 branch から起動すると明記している。

   現物も `s8b_floor_campaign.py:5515–5540,5616–5636` が zero-hit の clean scan を要求する。g2 契約と予算だけを裁定しても、提示された順序では閉じない。

   **修正要求:** 同じ rr20／rr80 の再測定を行う認可と D2120 項2(a)との関係、clean scan を満たす測定 checkout、現行修復の移植範囲、新成果物の取り込み順序を N の追加条件・費用に含める。scan 除外を広げる解決にしてはいけない。

3. **real — README と決定 fragment で、K2 の H 採択を誰が決めるか食い違う。**

   `README:106` は「固定 checkout／H／N、推奨 H」を裁定へ返す。一方、同 wave の [決定 fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2812-old-series-realignment/docs/spool/decisions/2026-09-21-worktree-t2812-old-series-realignment-1.md) の理由末尾は、既存 submodule 手順について「これを新しい択として提示し直さない」とする。

   D1777 は手順の存在を支持するが、今回の依頼 `verbatim/origin.md:9` は整合まで固定 checkout 継続を指定している。**既存手順の説明と、今回の新 main 経路の採択を分け、本文と fragment の裁定区分を一致させる必要がある。** pair／4巡目の予算再提示は D2187・D2194 項2どおり残す。

4. **refuted — 相談 A の3点が本文で限定されていない、という疑い。**

   段階4の残部・後段未観測は `README:11,134–135`、READONLY の限定は `:38,136`、失効保証の限界は `:84–89,137` に明記されている。これらの指摘は本文に反映済み。

5. **refuted — S' がそのまま D2184 の却下4種に当たる、という疑い。**

   `README:78,93,105` は exact policy 照合・旧 receipt bytes を保持し、権威の変更を別裁定へ返している。ただし第3入口の具体化不足は上記1のとおり。

## should

- **冒頭の「新 main の code が塞いでいるのは g1 だけ」は狭める。** `README:10` と、同本文の K2 codec 拒否（`:14`）、A-1 未認可（`:61`）は、そのままでは整合しない。「今回、期待 admission policy の変更を提案する対象は g1」とすれば観測範囲に収まる。
- **CLI の rc は保存証拠を補う。** 3つの CLI evidence には stderr／JSON 本体はあるが rc field はない。`README:44–46` の rc=1／1／2 は、指定 evidence だけから逐語確認できない。place の「書込み0」は preflight が書込みより先という静的根拠と分ける。
- **受入への申し送りを本文へ集約する。** `README:130` の `_ACTIVATED_G1_REFUSALS` 追随に加え、通常 consumer が現行 policy のままである負例、配置入口の receipt 由来期待値拒否、A-1 の0001・0002両 prior 残存ケースを名指しする。材料は `verbatim/s2-plan.md` にある。
- **択の対象を明記する。** `README:56` は O と N の併行を認めている。§5の N も「旧系列再開の代替として今回は選ぶか」であり、S'／H の採択が将来の N を禁止する意味ではないと揃える。

指定された D2150 項1、D2184、D1777、D2187、D2194 項2〜5、D2196、D2096 項5、D2172 項3の引用趣旨は一致した。主題語で後続 D も検索し、D2178 の0003再裁定、D2194の carrier・候補削除・歴史解析の限定を確認した。指定 HEAD の台帳末尾 D2199 までに、S' を認可する後続裁定は確認できなかった。

## nit

- `campaign_lock.py:491` は検査対象の代入行。拒否の直接参照は `:492–496` が正確。
- `README:46` の「hit 4件」は「rr20／rr80 **各4件、同じ4 path**」とすると集計単位が明確。
- `README:11` の「policy だけを記録値にすると」は、実際の呼出しどおり「`expected_policy=None` による個別歴史検証では」とする方が正確。`:32` では既に明記されている。

## 逐語照合の結果

省略 SHA は現物の接頭辞として照合した。数値の誤転記は確認できなかった。

| 主張 | 現物 | 一致／不一致 |
|---|---|---|
| `K2-PIN-NEW / H`：不一致／通る | 新 pin `e9e477ca1b55` 対 full `511c9538…` の拒否／H `ok=true` | 一致 |
| `POLICY-CURRENT`：`db6bc9ea…`、pin `e9e477c` | full SHA `db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a` | 一致 |
| generator 7、review 3 | 7／3。review は記載された3名称 | 一致 |
| K2／A-1 canonical `511c9538…` | 両方 `511c9538e4e8efa54b45cda62e72389ed3b706ec` | 一致 |
| `K2-LOCK-PAIR`：exact key 拒否、歴史 codec 成功 | 記載文言そのもの。歴史 `readable=true`、policy preimage は現行と同値 | 一致 |
| `A1-BOUNDARY-NEW / H` | `canonical HEAD mismatch`／`ok=true` | 一致 |
| `A1-SOURCE-NEW / H` | pinned-clean 不一致／`ok=true` | 一致 |
| `A1-IDENTITY`：3件、差は1 field | `result.json` の3 workload。**admission preimage部分**の差は `repo_stock_pin` のみ | 一致 |
| `G1-LOAD`：generation 1、`7e1114…`、G `32ba8cae4` | 1、`7e111406…`、`32ba8cae45001697f050bee377413153e6d798a5` | 一致 |
| `G1-LAUNCH` の拒否文言・cause | 記載文言そのもの、cause `binary-admission` | 一致 |
| `G1-BINARIES`：2 holdout × 6構成 | 列挙された12 cell。全件 human-reviewed | 一致 |
| 同 policy／source／protocol／contract | `949ddcc2…`／full `511c9538…`／記載の versioned path／`e576e9cd…` | 一致 |
| `G1-BIN-HIST / CURRENT`：12成功／12拒否 | HIST 12/12成功、CURRENT 12/12同文言拒否 | 一致 |
| `POLICY-SERIES-PIN`：系列 pinで記録値と一致 | 3 pin源とも `949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44`。g1・B4・A1との比較 true | 一致 |
| 同対照：現行 policy・K2 preimageと一致 | `e9e477c` 対照の両比較 true | 一致 |
| `B4-PROTOCOL`：候補2、HEAD exact 0 | 文言一致。anchor `d706650…`、versioned `511c9538…` | 一致 |
| `B4-RECORD-HIST / CURRENT` | 歴史成功／現行 policy不一致。review は `READMIT-STOCK` で確認 | 一致 |
| `B4-W1-HEAD`：3本、`2ba40008…` | 全3本 `2ba4000870c63254132410b3002b5298c0c6a210`、旧HEAD一致・新HEAD不一致 | 一致 |
| `READMIT-STOCK`：stock-baseline 0 | 観測した g1 12件＋B4 1件は全て human-reviewed、review登録 true | 一致 |
| `READONLY`：3木の観測一致、store不在 | snapshots_equal=true、before=false／after=false | 一致 |
| B4 place の拒否文言 | `b4-place.err.txt` と一致 | 一致。rc／書込み数は出力に無し |
| B4 validate-only の lstat拒否 | `…/output/env/pegasus/binaries` 不在で停止 | 一致。rcは出力に無し |
| g1 gate-check：false、拒否2、held 3 | false／2／3。hitは各holdout 4件 | 一致。rcは出力に無し |
| probe逐語 SHA `6e280172…` | コードブロックからの再計算が記載 full SHA と一致 | 一致 |

## 私が確かめた file:line

- **policy・攻撃拒否:** `build_admission.py:474–519`、`s8b_binary_admission.py:324–445`。exact型、SHA、class、full source、contract照合は記載と一致。
- **g1:** `s8b_ratified_freeze.py:1880–1925,3167–3178,3268–3276,3330,3369,3394–3478`。世代1限定、protocol権威、段階4の残部を確認。
- **W-5:** `s8b_oracle_driver.py:1003–1052`。policy照合とstore実体確認を確認。
- **配置:** `b4_binary_record.py:149–175`、`s8b_floor_campaign.py:5799–5875`。receipt由来期待値と、preflight後の書込みを確認。
- **K2／A-1:** `p3_s4_loop.py:116,2005–2017,2089`、`paper_story_a1_paired.py:211,228–230,2385–2438,2681–2730,2795,2970`。pin、stock capability、0002限定認可、prior解除を確認。
- **codec:** `campaign_lock.py:485–496`。`:491`の参照精度以外は説明と一致。
- **reseal・B-10:** `s8b_floor_campaign.py:983–990,1032–1075,1110–1155`、`tools/pegasus/b10_backoff_grid.sh:22,585–597`。commit前の拒否と凍結木hashへの波及を確認。
- **固定木・root:** `tools/pegasus/submit_floor_pair.sh:173`、`t080_freeze_migration.py:2234–2237`。HEAD／rootの束縛を確認。
- **Nの追加制約:** `s8b_floor_campaign.py:5515–5540,5616–5636`、D2120 項2(a)。

## 総括

**real must-fix は3件：S' 配置経路の権威・取得元の未確定、N の official 再測定制約の欠落、K2 の裁定区分の文書間不一致。**

観測表の値は概ね正確で、相談 A の限定も本文に反映済み。S' は設計候補として維持できるが、上記を直すまでは、実装 wave が着手できる裁定パッケージとしては未完了。書込み・テスト・live 成功の確認は行っていない。