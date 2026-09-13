## 挿入位置

**現物の 205 行目直後、206 行目の `- **primary outcome**:` の前に挿入する。**  
対象：[事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2547-b4-descriptive-erratum/docs/phase3-b4-reflux-ablation-preregistration.md:205)。

「n と検定単位」bullet の継続段落として、既存の追記と同じく先頭を半角空白 2 字にする。既存行は変更しない。

| 候補 | 採否と理由 |
|---|---|
| §5.1、205 行目直後 | **採用。** 標本数不足時の分岐に隣接し、§0 が規範の配置先として指定している。P1 は独立検査後も妥当。 |
| §7 | 規範の配置先としては許容されるが、今回は全件報告規則の変更ではなく、既登録分岐の選択。§5.1 の方が直接的。 |
| §10 | 未閉鎖事項の説明が主題。今回確定する主張の制限を置く正本として適さない。 |
| 新節・別 file | 既存分岐から宣言が離れ、規範の所在が増える。今回の追記 1 ブロックには不要。 |
| §5.1.1 内 | 凍結 bytes を変更するため不可。 |

## 追補の全文

以下をそのまま挿入する。

```markdown
  **追記 (2026-09-14、[T-2547]、D1936 項 8)。** 2026-09-10 のユーザー裁定に従い、
  B-4 は「記述統計に留め有意性を主張しない」分岐を選択する。
  **この選択は本書に基づく B-4 の結果を見る前に行った。本追記時点で、その実走は
  1 件も行っていない。** §9 に開示した既知結果の扱いは変えない。
  今回の根拠は、§5.1.1「n と検定単位」の「適格な block を 201 件確保できない場合」
  である。上の「予算上 n を確保できないなら」という条件を確認したものではない。

  2026-09-14 の在庫実測では、合成ループ 3 campaign の whiteboard は合計 7 件、
  すべて `success` であり、`rejected` は 0 件、適格な赤 precursor は 0 件だった。
  証拠は次の 3 file の `whiteboard` 配列である —
  `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json` (4 件)、
  `output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/loop_state.json` (1 件)、
  `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json` (2 件)。
  別 campaign の
  `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/s4_rejections_digest.txt`
  には赤が 3 件あるが、同 campaign には `loop_state.json` が無く、
  `whiteboard.result` を要求する適格性述語の第 1 項を満たさないため、算入しない。

  **本追記は実走の許可ではない。** §5.1.1 の選択関数
  (適格行が n 未満なら `design_not_feasible` とし、実走しない)、§5 の未記入欄、
  §6 の前提条件はいずれも残り、本追記はそれらを 1 つも解消しない。
  供給源は合成ループ campaign の `loop_state.json` の whiteboard のままとし、
  §5.1.1 の適格条件・順序・選択関数・完全性要件を変更しない。
  D1880 の formal B-4 の母集合である analysis manifest の 201 行、
  §5 の `n = 201`、`p3_b4_analysis_contract.py` の `EXPECTED_BLOCK_COUNT = 201`、
  および現行 consumer は変更しない。少数行を受理可能にしたとは扱わない。
  成功例への置換、n の無言の削減、母集合を作るための追加基盤は採らない。
  **本追記が限定するのは主張の強さであり、正しさゲート・受理集合は緩めない。**
```

在庫値は現物の `jq` 読取りでも確認した。実走 0 件の宣言は、本書に基づく B-4 に対象を限定し、§9 の歴史的な on 相当走行を否定しない。

## 凍結境界の確認

**提案位置は両 section parser の本文抽出範囲外である。ただし、親資料の閉包説明には訂正が必要。**

- [`p3_b4_analysis_prereg_consumer.py:301`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2547-b4-descriptive-erratum/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301) の `_locate_section` は、正規化した fingerprint に一致する H4 を一意に探し、その開始から次の見出しレベル 4 以下の直前までを `document_bytes[h4.start:end]` として抽出する。現物では **364〜648 行目**。649 行目が §6。
- 同 file の 399〜407 行目は、その抽出 bytes の raw sha256 と、同じ bytes を正規化した semantic sha256 を検査する。205 行目直後への通常段落追加は開始 offset をずらすだけで、抽出 bytes を変えない。H4/H5・HTML comment・code fence も追加しない。
- 間接経路の `p3_b4_analysis_path.py:380` も、§5.1.1 の見出しから次のレベル 4 以下の見出し直前を抽出する。同じ理由で対象 bytes は不変。
- [`p3_b4_admission_record.py:624`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2547-b4-descriptive-erratum/orchestrator/campaign/p3_b4_admission_record.py:624) は、`## 5.` と `### 5.1` を一意に探し、645 行目でその間だけを表として抽出する。現物では見出しが 154・169 行目なので、205 行目直後は**表の抽出・セル検査範囲外**。

親資料の次の表現は修正するべきである。

1. **「`### 5.1` より後ろは一切読まない」は不正確。** 文書全体の Markdown context と見出しを走査する。後ろを読まないのは表の値としての評価である。
2. **「consumer が bytes を pin する唯一の経路」も不正確。** `p3_b4_admission_record.py:770–783` は宣言 commit の**文書全体**の sha256 を照合し、HEAD の文書 blob との一致も要求する。今回の追記で文書全体の hash は変わるため、旧全文に束縛された admission が有効のままとは言えない。これは §5.1.1 の固定 pin と別の拘束であり、今回これを緩めたり admission を更新したりする提案はしない。

## P4 の解決

**発火根拠は §5.1.1 の「適格な block を 201 件確保できない場合」とする。**

現物の 487〜489 行目は、適格 block 不足を条件として、結果を見る前に記述統計分岐を宣言することを認めている。実測の適格 precursor 0 件はこの不足を裏付ける。一方、総計測予算欄は未記入であり、今回の在庫調査は予算制約を立証していない。

D1936 項 8 に従って**主張の制限を選択する**が、§5.1.1 の選択関数による実走禁止は解除しない。この区別を追補本文にも明記した。

## 焦点走の対象 file 集合

文書の直接読取先から caller を辿り、共有 fixture の参照もさらに 2 段確認した。以下の **13 file** を焦点走の対象とする。すべて `orchestrator/tests/` 配下。

| test file | 確認した参照関係 |
|---|---|
| `test_p3_b4_analysis_prereg_consumer.py` | 23 行目で実文書を指定。consumer の section pin 検査。 |
| `test_p3_b4_analysis_path.py` | 13 行目で prereg consumer、14 行目で analysis path を import。別の section 抽出と source closure 経路。 |
| `test_p3_b4_admission_record.py` | 21 行目で admission validator を import。固定表と全文 binding の契約。 |
| `test_p3_b4_closed_critic.py` | 32 行目で admission validator を import。692 行目以降の共有 fixture が文書・commit・全文 hash を生成する。 |
| `test_p3_b4_floor_artifact_issuer.py` | 17 行目で issuer を import、689 行目以降で文書を受ける floor resolver を直接検査。 |
| `test_p3_b4_material_report.py` | 25〜26 行目で floor issuer・report を import。report の 215 行目が実文書を resolver へ渡す。 |
| `test_p3_b4_launcher.py` | 18 行目で admission validator、31 行目で closed critic の共有 fixture を import。 |
| `test_p3_b4_raw_record_producer.py` | 30 行目で report、57 行目で closed critic の共有 fixture を import。 |
| `test_p3_s4_loop.py` | 44〜45 行目で closed critic・launcher、912 行目で共有 fixture を import。 |
| `test_p3_s4_loop_sort.py` | 31〜32 行目で closed critic・launcher、47 行目で共有 fixture を import。 |
| `test_p3_s4_loop_trigger_gating.py` | 34〜35 行目で closed critic・launcher、156 行目で共有 fixture を import。 |
| `test_p3_b4_proposal_binding.py` | 16 行目で launcher を import。文書 → admission validator → launcher の間接経路。 |
| `test_p3_b4_producer_auth_experiment.py` | 365〜374 行目の子 process コードが report と raw producer の共有 fixture を import。 |

共有 fixture の 2 段は、具体的に  
`test_p3_b4_closed_critic` → `test_p3_b4_raw_record_producer` → `test_p3_b4_material_report` / `test_p3_b4_producer_auth_experiment`。

なお、fixture 文書を自作するテストは実文書の編集そのものを検査しない。実文書の pin 検査と、周辺契約の回帰検査は区別して扱う。

**本段では実走していない。** 親は `tools/run_tests.py` 経由で実行する。

## check_docs 抵触判定

**提示した追補に、実装上の抵触は見当たらない。checker 全体の成功は未確認。**

- **可変状態：** `tools/check_docs.py:6729` 以降の検出は `現在は Phase`、限定された文書の `次 =`、現在 pin の literal など。追補は該当しない。意味上も、在庫を **2026-09-14 の分岐選択根拠という過去の観測**に固定しており、更新し続ける現在在庫の正本にはしていない。ただし checker が一般的な意味上の再掲まで判定するわけではない。
- **行番号参照：** 175 行目以降の `LINE_REF_STRICT` に該当しない。追補本文は §番号・節名で参照し、この回答の作業用行番号は転記しない。
- **予算：** 283 行目以降の各 `*_LIMITS` と 5941 行目以降の適用先に、この事前登録はない。`LIVING_DOCS` 所属だけで一律の bytes・行長上限が課される実装ではない。
- **パス：** 1120 行目の `PATH_REF` は実在確認を行う。本文に列挙した 3 JSON と digest は実在する。未作成の insight file は参照していない。
- **裁定番号：** D1936・D1880 の見出しは現物の `docs/decisions.md` に存在する。ただし `D_REF` は `\bD(\d{1,3})\b` なので、これら 4 桁番号を checker が検証するとは言えない。

## 総括

205 行目直後への追記 1 ブロックを推奨する。適格 block 不足を根拠に、結果閲覧前の有意性主張なしを宣言し、実走禁止・201 件契約・供給源・適格条件を維持する。

親資料の「表 parser は後半を一切読まない」「bytes pin は唯一」の 2 点は訂正が必要。ファイル作成・変更・commit・テスト実走は行っていない。