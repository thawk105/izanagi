## 所見

1. 反証対は、焦点 test の因果切り分けとして妥当。ただし「緑」は対象 test の `PASSED` を確認する必要がある。

   呼び出し経路は次の一本である。

   - 実 root を読む対象は `orchestrator/tests/test_plot_b10_extended_backoff.py:194-197`。
   - `load_measurements()` は外部入力の SHA-256 検査後、3 workload を `_load_workload()` へ渡す (`tools/plotting/plot_b10_extended_backoff.py:747-756`)。
   - `_load_workload()` は `backoff.load_campaign()` を呼ぶ (`tools/plotting/plot_b10_extended_backoff.py:675-680`)。
   - `load_campaign()` は明示的に `HISTORICAL_RAW` を指定する (`tools/plotting/plot_backoff.py:273-276`)。
   - admission はその purpose を `_inspect_campaign()` へ渡し (`orchestrator/campaign/artifact_admission.py:1477-1490`)、`_decode_campaign_lock_for_purpose()` の歴史分岐へ到達する (`orchestrator/campaign/artifact_admission.py:987-996`)。
   - 歴史 decoder は現行 exact-62 なら通常 decoder へ委譲し、それ以外は pre-T733 exact-24 として検証する (`orchestrator/campaign/campaign_lock.py:567-610`)。旧集合は独立 literal (`orchestrator/campaign/campaign_lock.py:114-142`)、検査は exact ordered tuple (`orchestrator/campaign/campaign_lock.py:391-403`)。
   - 分岐を外すと通常 decoder が現行 exact-62 だけを要求し、旧 map を `exact key 集合が不正` で拒否する (`orchestrator/campaign/campaign_lock.py:333-345`)。

   したがって、同一 bytes、同一 root、同一 test node で、唯一の差分が `artifact_admission.py:994-995` の除去であり、赤の内因が `campaign_lock.py:337-339` なら、「この test の通過に旧 grammar 用 decoder が必要」という必要性は切り分けられる。復元後の緑は十分性を示す。

   ただし次の対立仮説は、単に「file が緑／赤」だけでは残る。

   - 緑が実行ではなく skip: root は環境変数で差し替え可能 (`test_plot_b10_extended_backoff.py:21-24`) で、入力不足なら skip する (`同:60-71`)。最小追加観測は、対象 node が `PASSED` であり `SKIPPED` でないことと、解決後の `MEASUREMENT_ROOT` の記録。
   - 赤が旧 grammar 以外の一時編集事故: 通常 decoder の例外は admission で包み直されるため (`artifact_admission.py:965-973`)、同経路の最上位例外は通常 `ArtifactAdmissionError`、その chained cause が `CampaignLockCodecError` になる。最小追加観測は、両方を含む traceback と、内因が exact key 集合拒否であること。最上位が生の `CampaignLockCodecError` なら、想定した seam 以外を変えていないか再確認が必要。
   - root の取り違えや run 間 drift: generator は全外部入力を固定 SHA-256 と照合する (`plot_b10_extended_backoff.py:235-241`。3 lock の固定値は `同:132-150`)。最小追加観測は、対象 lock の digest と key tuple が `PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS` に一致した記録。
   - 「現行 main の受入全走でも、この一件だけが赤」という強い主張: 焦点 file の対だけでは証明できない。2026-09-05 の全走で唯一の赤だったことは一次記録済み (`verbatim-worklog-1279.md:27-31,51-52`)。現時点の全走について主張するなら、新しい受入全走そのものが追加観測として必要。

   よって、この対は「2026-09-05 に観測された唯一の失敗が旧 grammar に帰属する」の再現には十分だが、「現在の全受入が他にも赤を持たない」までは含めない。変異前後の diff と、復元後に `artifact_admission.py` が元の blob に戻った証拠も保存すべきである。

2. (P1) は、権威と実装結果を区別すれば次の結論になる。

   - D1563 は明記されたユーザー裁定で、新閉包による別 lock の発行、歴史 decoder と別束縛案の不採用を命じている (`docs/decisions.md:48215-48220`)。
   - D1653 は明記上「親裁定」で、正反対に歴史閲覧限定 decoder を採り (`docs/decisions.md:50673-50678`)、新閉包での発行を却下している (`同:50702-50706`)。
   - 現行コードには D1653 側が実装済みである。旧 exact-24 literal は `campaign_lock.py:114-142`、専用 decoder は `同:567-610`、purpose 分岐は `artifact_admission.py:987-996`。記録 commit `da44dc7b1` が HEAD の祖先であることも静的確認した。
   - D1563 の発行命令は、少なくとも現在の外部 corpus について未完了で、旧 lock は現在 11 件ではなく B10 3 件と A-2 10 件の計13件である (`brief.md:27-29`)。

   後続の撤回・上書き裁定は、明示的には不在。`docs/decisions.md` 全体について D1563 の番号、三案の語句、「発行し直す」「歴史 decoder」「別の束縛」を検索した。D1563 の後で D1653 を引用するユーザー裁定は D1669 (`docs/decisions.md:51037-51052`) と D1680 (`同:51245-51260`) だが、前者は別 schema への類推、後者は追加 grammar の corpus 条件であり、該当 lock の三択や D1563 の撤回を裁定していない。

   したがって、D1653 がコード上で D1563 を事実上覆した、という読みは正しい。一方、D1653 がユーザー裁定 D1563 を正式に supersede した、とは現物から言えない。反証条件は、D1563 の撤回、または該当 lock について D1653 案を採ると明記した後続ユーザー裁定の提示である。

## 裁定パッケージ骨子

1. 版付き decoder を採る

   - 今からすること: すでに着地している D1653 実装を維持し、D1563 との衝突を新しいユーザー裁定で解消する。新規 decoder 実装は不要。
   - 規律2: certified は通常 decoder の現行 exact-62 のまま (`campaign_lock.py:333-345`)。旧 exact-24 は exact enum の `HISTORICAL_RAW` だけ (`artifact_admission.py:987-996`) で、返却型も別 (`campaign_lock.py:199-231`)。現行 certified の受理集合は変わらない。
   - 規律7: historical view は判定根拠を original verifier epoch とし、現行適合を `unknown` と表示する (`artifact_admission.py:451-471`)。旧記録を現行 certified へ遡及昇格しない。
   - 受理集合: 現在の main から変化なし。歴史閲覧だけが現行 exact-62 と pre-T733 exact-24 を受理し、certified は exact-62 のみ。
   - 撤回費用: 将来撤回する場合、旧 literal、歴史 decoder、purpose 分岐、歴史 epoch と別返却型を除去し、B10 図と他の旧 lock consumer に別解を与える必要がある。局所的だが複数層にまたがる。

2. 該当 lock を新閉包で発行し直す

   - 今からすること: D1653 を撤回して D1563 を再確認し、現在旧 exact-24 の13件について、旧 bytes を残したまま現行 exact-62 の新 lock と、それを参照する下流束縛を発行する。その後、三択を排他的に扱うなら現在の歴史 decoder を撤回する。
   - 規律2: decoder や certified 判定式は広げない。新 lock は現行 encoder が通常 decoder で自己検証する exact-62 になる (`campaign_lock.py:696-716`)。コード上の受理述語は不変で、corpus 側を現行述語へ移す。
   - 規律7: D1563 は「旧 bytes を残し、同じ内容への新しい束縛」と解した (`decisions.md:48230-48232`)。一方 D1653 は、測定後の hash 計算では測定時の disk bytes との一致を復元できず、lock hash が completion、receipt、manifest へ伝播すると反論している (`同:50684-50687`)。現行 encoder は与えられた authority の形式を検査するだけなので、この歴史的主張の衝突はコードから解消できない。ここをユーザー裁定で明示的に決着させる必要がある。
   - 受理集合: certified の grammar 集合は不変。新 artifact が現行集合へ加わり、歴史 exact-24 の受理は decoder 撤回後に縮む。
   - 撤回費用: 3案中で artifact 運用費用が最も大きい。図 generator は lock を含む外部入力を固定 hash で束縛している (`plot_b10_extended_backoff.py:132-154,235-241`)。新 lock と下流 digest 鎖を発行すると、後から「発行しなかった状態」には戻せない。旧参照へ戻すなら decoder の再実装も必要になる。

3. 図の生成経路を別の束縛へ移す

   - 今からすること: B10 図だけを中央 admission から外し、既存の固定 file SHA-256 束縛を読み取り権威とする。排他的な三択として採るなら、現在の歴史 decoder も撤回する。
   - 規律2: certified admission は変わらない。ただし現在の図経路は `load_campaign()` を介して中央 admission を通る (`plot_b10_extended_backoff.py:675-680`; `plot_backoff.py:273-276`)。別束縛へ移すと、固定 bytes の完全性は保てても、activation、記録 commit blob、overlay、WAL topology など admission 内の検査を図 consumer が失う (`artifact_admission.py:1307-1397`)。D1653 もこの低下を理由に却下している (`decisions.md:50688-50689`)。
   - 規律7: 旧 lock と測定 bytes をそのまま残す点では適合する。一方、現在の historical view が明示する original epoch と current conformance unknown という区別 (`artifact_admission.py:451-471`) は、単純な file hash 束縛だけでは表現しない。
   - 受理集合: certified は不変。図経路は grammar 受理から、コードに列挙された3組の exact file hash 受理へ変わる。歴史 decoder も撤回すれば、中央 historical admission の exact-24 受理は消える。A-2 を含む他 consumer の閉塞は解決しない。
   - 撤回費用: 図だけなら変更面は比較的小さいが、中央 admission に戻すには decoder の再導入か新 lock 発行が必要になる。別 consumer で同じ閉塞が再発するという既知の費用も残る (`decisions.md:48233,48239`)。

## 記録先

insight には次を残す。

- 対象 HEAD `542bfadb86b14625a99cca1bdef3583ea09a95ca`、実行日時、解決後の measurement root、環境変数の有無。
- baseline と変異走行の完全なコマンド、対象 node の `PASSED`／`FAILED`／`SKIPPED`、所要時間。
- 一時変異の exact diff。変更が `artifact_admission.py:994-995` だけだったこと。
- 赤の traceback。外側の `ArtifactAdmissionError`、内側の `CampaignLockCodecError`、exact key 集合拒否、対象 lock path と digest。
- 3 lock の key tuple が pre-T733 literal と一致した観測。
- 即時復元後の file hash または空 diff。復元後の再走結果は、実際に走らせた場合だけ記録する。
- 焦点 test が示す範囲と、全受入の唯一性までは新規証明していないという claim boundary。
- D1563 と D1653 の衝突、後続撤回裁定が不在だった検索方法、現在は D1653 側が着地済みという訂正。
- 上の三案を無推奨で掲載し、「選択はユーザーの手番」と明記する。
- 本回答ではテストを実行しておらず、静的検査だけだったこと。

worklog fragment は `docs/spool/README.md:28-49` の命名と frontmatter に従い、例えば `docs/spool/worklog/2026-09-07-dev-wave-t2254-old-grammar-cause-1.md` とする。本文 H2 は `## 本文` と `## 次の一手差分` の2つだけ (`docs/spool/worklog/README.md:5-23`)。

`## 本文` には git 差分から復元できない実測値、一時変異と復元、裁定衝突の発見、非実走事項を書く。`## 次の一手差分` では `[T-2254]` を「実測待ち」から「実測済み、ユーザー裁定待ち」へ `更新` し、古い「branch が未着地」という記述を現況へ直す。まだ `完了` にしない。`base:` は land 先 local main で取得した実体 item の SHA-256 が必須 (`同:81-97`)。

新しい D 番号は書かない (`docs/spool/README.md:55-67`)。ユーザーが三案を選ぶまでは decision fragment も作らず、選択後に別途記録する。

## 総括

反証対は、対象 test が実際に走ったこと、同じ pinned bytes を読んだこと、赤の chained cause が通常 decoder の exact key 集合拒否だったことを記録すれば、旧 grammar の因果を十分に切り分ける。全受入の現在の唯一性は別主張である。

D1563 を撤回した後続ユーザー裁定は不在。D1653 はそれと矛盾する親裁定として実装・着地したが、正式な supersede は記録されていない。したがって現在必要なのは、すでに実装済みの decoder を維持するか、D1563 の発行案へ戻すか、図だけを別束縛へ移すかについての、新しいユーザー裁定である。