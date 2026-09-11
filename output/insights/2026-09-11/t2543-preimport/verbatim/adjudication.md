# 段4裁定・plan v2・変異事前登録

- plan/consult2本ともaccepted、done rc=0、output checker rc=0。両レンズの欠落と既存Python testの非検出はreal、scope内として採用。
- 全PBSの最終拒否だけでは下流検査にmaskされる所見はreal。実PBSの配列とdirty部分を固定文字列anchorで抽出し、実Git fixtureに対して実行する局所契約で検証する。
- fixtureが必ず先に落ちるとの一般化はrefuted。fixture構築後に対象だけdirtyにし、PBS fixtureは置換しない。
- 「Python起動前」は版確認まで含めず、probe起動・条件関門import前と記録する。
- productionはBOUND_PATHSへの1行だけ。testは既存module内100行以内。新file/汎用harness/防護機構/Python本体変更なし。
- 既存5pathを独立literalでparametrizeし各unstaged/stagedのdirty拒否を確認。cleanと対象外dirtyは通す。実PBSにおけるdirty→blob/runtime照合→probe起動順序を静的に確認する。
- 受理: 既存4pathと条件関門がcleanなら従来どおり進む。拒否: 条件関門単独dirtyなら既存exit 3となり後続markerへ到達しない。
- 対象外dirty正例は承認外の過剰拒否を防ぐ正例として採用。他の提案変異（順序入替/status限定除去）は今回の1行修正で変更しない挙動なので本waveの実装・matrixに足さない。
- M1事前登録: PBSへ追加する `  orchestrator/campaign/condition_meaning_gate.py\n` を1箇所除去。期待KILLED。期待失敗集合は条件関門のunstaged/staged 2nodeのみ。node名はauthor実装後に固定する。
- M1の観測: 抽出dirty検査だけを動かし、変異後のrc=0/marker到達による結果assertの赤を数える。配列一致やfixture失敗だけはkillにしない。clean正例も走らせ、無条件拒否を除く。
- shell全体の実機probe/benchmarkは未実走と明記。今回のテストは局所Bash/実Git + 静的順序契約。
- 正本D1936項30の更新なし。裁定方向を覆す未見事実なし。親によるコード/test編集なし。
