**限定移行の方向は妥当ですが、保留集合と受入条件は補完が必要です。** 静的調査のみ実施し、実装・pytest・完了 checker は実行していません。

1. **重要度: 高 — 計画の保留表に、受理判定へ直結する実体が漏れています。**

   次は今回、旧位置に残すべき追加集合です。パスは `output/insights/` 相対です。

   | 対象 | 根拠 | 最小対処 |
   |---|---|---|
   | `2026-08-27_t1969-axis1-search-execution/` 全体 | `orchestrator/axis1_search/validator.py:24`。`:782` で固定 commit と登録時 tree、`:801` で現在の path 集合、`:810` で現在の bytes を照合する | ディレクトリを保留。履歴参照だけとして移さない |
   | `2026-08-24_paper-story-a1-paired/` | `tools/verify_paper_story_a1_headline_sizing.py:24` に pilot path、`:26` に digest、`:494` に exact path 検査 | 少なくとも `result.json` を旧位置に残す。今回は親ディレクトリ保留が簡単 |
   | `2026-09-03_t2103-producer-auth-layer/` | `orchestrator/campaign/p3_b4_producer_auth_experiment.py:28` の事前登録を、`:2027` から現物読取・登録内容照合 | 少なくとも `mutation-prereg.json` を保留 |
   | `2026-08-26_mocc-trace-pair-receipt.json` | `orchestrator/tests/test_mocc_trace_pair.py:48` の実体パスと `:51` の独立 digest | 旧位置に保留 |
   | `2026-09-01_paper-story-a1-balanced5-pilot/` と同名末尾 `-preregistration/` | `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:31`、`:88` | v2 だけでなく v3 の登録先も保留表へ追加 |

   既存計画の7月16日5文書、recon・sort・N1、A2、headline、登録済み出力先の保留は支持します。ただし、その表を閉包済み集合とは扱えません。

2. **重要度: 高 — 現役 consumer を本体コードだけで数えると、既存検査が資料移動で壊れます。**

   **根拠:** `orchestrator/tests/test_s8b_oracle_n_pilot.py:285` と `:299` は先行 protocol、`:303` は後継 protocol を現在位置から読みます。`test_backoff_profile_pegasus.py:1227`、`test_backoff_requested_us.py:1077` も実在する insight 内の `job-body.sh` を読みます。

   **最小対処:** 次を「保留または個別 consumer 修正」の確定表に追加してください。

   - `2026-08-16_t1142-n-pilot-prereg/`
   - `2026-09-09_t2154-n-pilot-prereg-successor/`
   - `2026-08-26_b10-balanced-profile/`
   - `2026-08-28_t1941-backoff-requested-us/`

   単なる fixture の入口ならパスだけ個別修正できます。登録済み protocol 内の束縛へ波及するものは保留します。検査の削除や期待値変更は不要です。

3. **重要度: 中 — 「現役参照がある」と「移動禁止」は分けるべきです。**

   **根拠:** `tools/plotting/plot_t2266_tail_mechanism.py:35` は現役の既定参照です。一方、`p3_b4_wiring_probe.py:48` の出力先は `:1828` で既存成果物の再発行を拒否するため、移動すると同じ ID の旧位置への再発行を許す可能性があります。

   **最小対処:** 通常の入力先は digest・登録内容への波及を確認して個別修正し、移動候補に戻します。既存性が受理条件になる producer は旧位置に保留します。後者の実在例は `2026-08-27_t1769-b4-wiring-probe/` です。全 consumer の一律保留も、一律新配置化も避けられます。

4. **重要度: 中 — 相対リンク例の一つは既存破損です。また、日付接頭辞除去は別の破損原因になります。**

   **根拠:** `2026-08-11_t813-acceptance-sharding/verbatim/s3-luna-out.md:31` のリンクは、現在の checkout では `facts.md:57` が存在せず、行番号部分を除いても参照先がありません。これだけでは新規破損を理由に保留できません。

   対して `2026-09-02_cicada-adaptive-three-constants.md:54` の画像は実在します。本文と figures を同じ日付へ移しても、figures 側の接頭辞を除くと本文内の旧 basename と一致しません。

   **最小対処:** この組は両方保留するか、日付フォルダ内の figures 名だけ旧 basename を維持します。後者なら bytes 不変で移動できます。接頭辞除去に局所例外を認める方が、リンク両端の一律保留より多く移せます。

5. **重要度: 中 — Git 履歴参照を移動障害とする一般化は不要ですが、現在実体との二重照合を見落とせません。**

   **根拠:** `orchestrator/publication/approval_d291.py:62` は commit・path・digest の組です。`tools/codex_reasoning_ab.py:3343` は固定 commit の旧 path から snapshot を構成します。現在配置に合わせた更新は誤りです。一方、所見1の axis1 は固定履歴と現在実体の両方を比較します。

   **最小対処:** 固定 `commit:path` と snapshot 内パスは据え置き、その存在だけでは HEAD の移動を禁止しません。旧資料中の code span も対応表で追跡する親判断を支持します。

6. **重要度: 中 — 親の件数と計画の検査範囲を、同じ集合へ揃える必要があります。**

   **根拠:** `handoff.md:36` の17,330 filesに対し、本段では Git 管理下・作業ツリーとも **17,328 files**、未追跡の追加ファイルは0でした。直下1,077件、日付付き1,075件、72日、同日最大52件、深部1,422件・1,424件は一致しました。

   `plan.md:78` は直下と新日付階層の件数確認が中心ですが、親は深部の閲覧障害も認識しています。さらに `plan.md:76` の「tracked file 全件を完全一致」は、予定する `output/README.md` や checker の編集まで含めると成立しません。

   **最小対処:** 保存照合の対象を「既存 insights 全ファイル」と明記し、可変 consumer・案内の編集集合を別に列挙します。深部2ディレクトリには生証拠を動かさず分割索引を置き、全 leaf への直接リンクの網羅性を確認します。件数の2件差は採取時点・対象差として解消してください。

7. **重要度: 中 — checker は新配置で動くだけでなく、旧検査対象が落ちないことを確認してください。**

   **根拠:** `tools/check_docs.py:2618` と `:2654` は直下 Markdown だけを列挙します。`plan.md:60` の旧直下＋日付直下への局所修正は適切ですが、`:80` の追加ケースだけでは移動した既存対象の検査漏れを直接確認できません。

   **最小対処:** 一回限りの確認で、移行前の対象集合を移動表で変換した集合が、移行後の列挙に全て含まれることを比較します。深い逐語記録への無条件再帰は不要です。placeholder の2文書は今回据え置けば、例外台帳へ触れずに済みます。

## 総括

**追加の実在保留集合を確定し、残りのディレクトリを内部 bytes 不変で広く移す案を推奨します。** 通常 consumer は個別修正、相対リンクは名前維持の局所例外、履歴参照と旧 code span は据え置き＋対応表で扱えます。汎用 resolver は不要です。

未確定なのは最終移動表とその参照閉包です。本段の追加集合も網羅済みとは主張しません。139件・142件の候補数を安全性の根拠にせず、確定表から移行後件数と検査対象を再計算してください。