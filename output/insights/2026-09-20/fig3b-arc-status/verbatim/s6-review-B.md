指定資料はすべて読了。変更・pytest・作図・変異実行は行っていません。以下の node 集合は静的予測です。

参照略号：G＝`tools/plotting/plot_arc_status.py`、T＝`orchestrator/tests/test_plot_arc_status.py`、P＝生成された provenance JSON。

## must-fix

### 1. Act 行の内部 ID が図に露出している

- **根拠：** G:244、351–353、T:46、P:48–93。作図規約 §5。
- **影響：** Act 全8行に `act1-evaluator:` 等の内部識別子が表示され、不要な文字量と折返しが増える。現行 test はこの表示を正解として固定している。
- **最小修正：**
  - G:244 の表示値を `item["label"]` にする。
  - G:351 は `ident = "" if "progress" in group else item["id"]` にする。
  - T:46 も Act 行では label＋sublabel のみを期待する。
  - `drawn_items.id`、所有領域の ID、証拠項目の `A-1` 等は維持する。
  - 修正後の図・provenance を親が生成する。

### 2. M2 の definition fixture は単一理由になっていない

- **根拠：** G:53、130、157–158、75、57、T:142–146、169。author 報告:38。DW-M01／M03。
- **影響：** `unknown-definition-key` の `extra: 1` は、未知 key を許しても後段の `_string(1)` が拒否する。test は期待した `key set` と診断が違うため赤になるだけで、この node を受理集合変化の kill と数えられない。
- **最小修正：** T:146 を次のようにする。

```python
target["extra"] = "Additional definition." if case == "unknown-definition-key" else 1
```

M2 の期待 node は item だけでなく未知 key の5ケース全部にする。M3・M4a についても下表の完全集合へ登録を修正する。

### 3. 証拠グループの表示 label が自由文検査を通らない

- **根拠：** G:136–140、157–158、255。
- **影響：** A/B グループの label を `38%` に変えると、その値を自由文検査せず見出しとして描ける。値なし表示の契約に穴がある。
- **最小修正：** `free.append(container["label"])` を `if is_act` の外へ移す。描画しない T3 に `group-percent` を追加し、グループ label の `38%` を拒否することを確認する。

## should

### 公開ファイルの mode が 0600 のまま

- **根拠：** G:395–405。現物の PNG・PDF・provenance はすべて `stat` でも `600`。
- **影響：** 別 UID の共同研究者や配信プロセスが、この作業ディレクトリの成果物を通常の権限では読めない。同じ UID の別プロセスは読める。
- **最小修正：** 公開前の一時ファイルに共有方針に合う mode を設定する。公開資料として 0644 が適切なら、`os.link` 前に `source.chmod(0o644)`。Git に登録しても、この場所の読み取り権限の問題は解消しない。

## nit

| 所見・根拠 | 放置時の影響 | 最小対応 |
|---|---|---|
| G:170 の `else Path(prefix).name` は正常実装では到達不能 | 通常成果物は変わらない。ただし M8 の不正 prefix を受理させる変異では、この fallback が必要 | 今回は維持してよい。削除するなら M8 を関数全体の置換として再登録 |
| T:13、G:18 は import 時に backend を変更 | 本ファイル単独の成果物は変わらない。suite 全体の環境・backend には副作用がある | 必要なら test import 前後で環境値を復元。ただし pyplot の backend 切替自体は環境値の復元だけでは戻らない |
| G:408–414 の cleanup は unlink 失敗を個別に処理しない | 通常失敗時は清掃されるが、清掃自身の I/O エラーでは残骸ゼロを保証できない | 今回の正常実走の不具合とは扱わない。「あらゆる失敗で必ずゼロ」とは報告しない |
| G:391 で作成したディレクトリは保存失敗後も残る | ファイルは清掃されても空ディレクトリは残り得る。裁定の「新規 file を残さない」とは矛盾しない | 対応不要。T6 は mkdir 前に拒否する経路の検査と説明する |

## 実装の正しさ・最小性

### 自由文・anchor・節抽出

- **G:75–83：** `\b` は単語境界なので、`none`、`tone`、`focus`、`second` を部分一致で拒否しない。**`status` も拒否しない**。依頼文の「`status`, `once` は拒否対象」のうち、`status` は裁定の拒否語集合に含まれず、現実装の受理が適切。`once` は拒否する。
- `sec` と `seconds` は拒否するが `second` は受理する。これは固定小集合の契約どおりであり、自然言語の単位判定へ広げる理由はない。
- token 分割は空白・`; , /`。`token in declared_ids` は全体一致なので、`A-1suffix` や `fig8.5` は許されない。`A-1.` や `(A-1)` も受理しないが、指定契約に沿った保守的挙動。
- NFKC 後の全角数字は ASCII 数字になり、数字検査に掛かる。全角 `%` も拒否対象になる。宣言 ID に正規化される表記は ID 例外に入る。
- **G:88–98：** 提示された `- **A-1 (`、`- **A-3.`、`- **B-10.` は一致する。`B-1` の直後に必要な `[ .(]` は `B-10` の `0` に一致しない。一意性は `findall` の件数で検査している。本文そのものは今回の射影外なので、現物の出現件数を独立再確認したという意味ではない。
- **G:119：** §0 の終端は文字どおり `## 1. `。`## 10. ` とは一致しない。§8 も同様に §9 直前まで。

### 折返し・layout・provenance

- **G:181、198–212：** Agg renderer は固定寸法・dpi の Figure から取得し、描画と同じ `FontProperties` で幅を測っている。全体 draw 前に幅を測る構成は妥当。
- 分割不能な単語は縮小・切捨てせずそのまま残す。指定 wrap 幅を少し超えても所有領域に収まれば通るが、所有領域を超えるものは **G:297–315** の draw 後 bbox 検査で保存前に拒否する。
- **G:293：** 包含は各辺に1 px の許容。交差は **面積1 px²** の許容であり、別の基準として実装されている。
- **G:190、320–327：** `headings`／`acts`／`A`／`B`／`legend` ごとの兄弟を比較し、Act 内の行は各 Act を parent とする。親子包含を交差として拒否しない。異なる parent 集合の領域同士を全比較する設計ではない。
- `footnotes` は parent と領域名が同名なので領域包含検査は自己比較になる。ただし固定配置は figure 内で、脚注 Text 自体には figure 内包も掛かる。現在の成果物を変える不具合ではない。
- **G:328–338：** marker bbox を1 pt 膨らませて包含・Text 交差を検査する。中立横線は正の高さを要求せず、有限値と正の幅を確認してから padding する。
- **G:306–313：** 全可視・非空 Text を走査するため、未登録 Text の検出は実効性がある。現在は axes がなく、すべて helper の `fig.text` で登録されるので正常経路では発火しない。直接追加した `Text` や将来の axes のラベル等も走査対象になる。
- **G:341–355：** 期待値と actual は集合ではなく**順序付きリストの完全一致**。欠落・追加・順序・state・表示文を比較し、折返し改行を空白へ正規化する。Act ID 露出の修正以外は整合している。

### 出力公開と scope

- **G:395–405：** 一時ファイルを出力先と同じディレクトリに作るため、別 filesystem 間の hardlink 問題は避けている。NFS/Lustre という名称だけで可否は断定できず、実際の mount・権限が hardlink を許す必要がある。親の rc=0 はその実走先で成立した証拠であり、全共有 filesystem への保証ではない。
- `os.link` は既存 destination を置換しない。途中で失敗すれば、この呼出しが `published` に記録した出力と一時ファイルを清掃する。3ファイル全体の同時公開ではない。
- **G:387–389、425–426：** main の事前検査は無駄な描画を避け、publisher の検査は直接呼出しを守る。二重呼出しは削除必須ではない。M8 は共通 `_figure_number` の述語を変えるので両方に効き、`_destinations` は不正 basename を拒否しない。
- key・anchor・自由文・layout・既存出力検査は、この図の生成を拒否する局所検査。指定状態 JSON と本文、生成器自身、対象出力を読むだけで、repo 全体や他 wave を走査しない。scope 外の gate 新設には当たらない。
- 汎用 framework 化や検証コードの大幅削除は不要。削るべき表示は Act の内部 ID、追加すべき検査はグループ label の自由文検査で足りる。

## 変異の帰属

author の申告行は現物と一致する。ただし M3・M4a・M4b は関数開始行の申告で、逐語 anchor は以下のように具体化する必要がある。

全行の `file` は `tools/plotting/plot_arc_status.py`。表中の `\n` は harness 登録時に実改行へ展開する。提示した `old` は現物上それぞれ1か所。M4a/M4b の早期 return 後に残る旧本体は到達しない。

| 変異 | `old` → `new` | 現行29ケースで赤になる完全な集合 | 単一理由・等価性 |
|---|---|---|---|
| M1、G:151 | `state in STYLES` → `True` | `{T3[bogus-state]}` | 型検査を残すので null は引き続き拒否。bogus は load で受理される。非等価 |
| M2、G:53 | `set(value) == set(expected.split())` → `set(value) >= set(expected.split())` | `{T3[unknown-item-key], T3[unknown-top-key], T3[unknown-act-key], T3[unknown-group-key], T3[unknown-definition-key]}` | 最初の4件は受理へ変化。definition は現状、後段の型検査による**診断だけの赤**。上記 fixture 修正が必要 |
| M3、G:73 | `def check_display_text(value, declared_ids):\n` → `def check_display_text(value, declared_ids):\n    return\n` | `{T3[percent], T3[throughput], T3[latency], T3[assignment], T4}` | regex と数字検査の双方を通過させる。他の load 検査はこれらを拒否しない。非等価 |
| M4a、G:288 | `def _intersection(left, right):\n` → `def _intersection(left, right):\n    return 0\n` | `{T5[overlap], T6}` | 共通 helper は複数用途だが fixture は同一セル内 Text 衝突。T6 も同じ衝突を publisher に渡すので赤になる |
| M4b、G:292 | `def _contains(outer, inner):\n` → `def _contains(outer, inner):\n    return True\n` | `{T5[escape]}` | figure と owner の包含両方を無効化。移動先 `(1.2, 1.2)` は他 Text と交差しない。非等価 |
| M5、G:368 | `hashlib.sha256(raw).hexdigest()` → `("0" * 64)` | `{T7}` | inputs の2 hash が有効長の誤値になる。T2 は input hash を独立比較しない。非等価 |
| M6、G:185 | `return STYLES[state][:2]` → `return STYLES["obtained"][:2]` | `{T2}` | 色・形だけが obtained 化。Text/state は維持、中立行は別分岐のまま。独立 artist 比較が kill |
| M7、G:389 | `    check_figure_layout(fig, layout)\n` → 空文字列 | `{T6}` | `_drawn_items` は位置を見ないので衝突 fixture を拒否しない。公開まで進み、期待例外が出ない |
| M8、G:169 | `_require(match is not None, "output prefix basename must start with fig<N><letters>_")` → `_require(True, "output prefix basename must start with fig<N><letters>_")` | `{T8}` | 共通述語への1置換が main／publisher 両方に効く。G:170 の fallback により実際に受理・公開へ進む。非等価 |

上表の node 略記は、次の完全名への機械的な置換である。各 node の先頭にはすべて `orchestrator/tests/test_plot_arc_status.py::` を付ける。

| 略記 | test 名 |
|---|---|
| `T2` | `test_t2_independent_styles_and_changed_state` |
| `T3[id]` | `test_t3_invalid_json_without_drawing[id]` |
| `T4` | `test_t4_free_text_contract` |
| `T5[id]` | `test_t5_layout_rejects_overlap_and_escape[id]` |
| `T6` | `test_t6_publisher_rejects_collision_without_files` |
| `T7` | `test_t7_cli_outputs_and_independent_hashes` |
| `T8` | `test_t8_cli_rejects_invalid_prefix` |

**fix 後の差分：**

- definition fixture を直しても M2 の予測 node 集合は同じ。ただし5件すべてが受理集合変化の赤になる。
- 推奨した `group-percent` を追加した場合、M3 の集合に `test_t3_invalid_json_without_drawing[group-percent]` が加わる。
- M4a/M4b は複数検査を無効化するが、各 fixture の欠陥は一種類。複数 node が赤になることと、単一理由性の欠如は別問題。
- M4a/M4b を別注入として数えるため、M1〜M8 は**8系列・9変異実行**になる。「8件」とだけ登録しない。
- これは実測 kill 結果ではない。fix 後の source に対して逐語一意性と期待 node を再確定する必要がある。

## test の予算・既存環境との干渉

**実寸 Figure は6個、全体描画は保存込みで7回**という author の説明と整合する。

| 経路 | Figure 数 | 全体描画 |
|---|---:|---:|
| module scope `production` | 1 | T1 の layout で1 |
| T2 の変更入力 | 1 | 0。renderer による artist 測定 |
| T5 overlap／escape | 2 | 各1 |
| T6 overlap | 1 | layout で1 |
| T7 正常 CLI | 1 | layout・PNG・PDF の3 |
| T7 再実行／T8 | 0 | 事前拒否 |

T3 は21ケース、T5 は2ケース、ほか6ケースで計29。実 JSON の行数・文字量を保ち、衝突 fixture も実図の位置だけを変えるため §10 を満たす。9.06秒の親実測と矛盾しないが、今回それを再測定したわけではない。

T:238–254 は timestamp や環境依存 hash bytes を期待値へ固定せず、実ファイルから独立計算して比較している。T:255–258 の bytes 比較は再実行時の不変確認であり、環境依存の golden file ではない。

T:20–22 は `sys.modules` へ明示登録していないため、`arc_status_under_test` 名の汚染はない。依存 module の import と backend の副作用は残る。

T:226 の `{**os.environ, "MPLBACKEND": "Agg"}` は、CLI 呼出し時の環境を継承し backend だけを上書きする。autouse fixture が環境を隔離していれば、その隔離後の値を継承する構成。ただし **conftest と既存 test 本文は指定射影に含まれない**ため、その具体的な隔離内容・suite 全体との無干渉は独立確認できない。author 報告だけを検証済みの根拠にはしない。

## 総括

**must-fix は3件。**

1. Act 行から内部 ID の表示を削除し、provenance の表示文・test の期待値を追随させる。
2. M2 の `unknown-definition-key` を正常な文字列値にし、診断だけの赤を排除する。
3. A/B グループ label を自由文検査へ含める。

fix 子には上記の局所変更と、描画不要の `group-percent` ケース追加を渡す。公開 mode 0600 は should として共有方針に合わせて修正する。

変異登録は **M2＝5 node、M3＝現状5 node／追加後6 node、M4a＝2 node** に修正する。M8 は共通述語へ注入し fallback を維持する。M4a/M4b を分けた9注入として、fix 後の逐語 anchor と完全な期待 node 集合を確定する。