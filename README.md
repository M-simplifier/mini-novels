# Mini Novels

`stories/` に置いた Markdown を、読みやすい静的Webページとして出力するワークスペースです。

## 使い方

1. `stories/` に Markdown の短編を追加する
2. `python3 scripts/build_site.py` を実行する
3. `site/index.html` をブラウザで開く

ローカルでサーバーを立てて見る場合:

```sh
python3 -m http.server 8000 --directory site
```

その後、`http://localhost:8000` を開いてください。

## ホットリロード

Markdown を書きながらプレビューしたいときは、開発サーバーを使います。

```sh
python3 scripts/dev_server.py --port 8000
```

その後、`http://127.0.0.1:8000` を開いてください。
`stories/*.md` または `scripts/build_site.py` を保存すると自動で再ビルドされ、ブラウザもリロードされます。

## GitHub Pages

`main` への push ごとに、`.github/workflows/deploy-pages.yml` が `python3 scripts/build_site.py` を実行し、生成した `site/` を GitHub Pages へ公開します。

最初の一回だけ、リポジトリ側で GitHub Pages を有効にする必要があります。有効化後は、`main` に push すれば自動で更新されます。

## いまの仕様

- `stories/*.md` を一覧ページと個別ページに変換します
- 本文の `#`, `##`, 段落、箇条書き、`inline code` を拾います
- `##` 見出しから目次を作ります
- 文字数とだいたいの読了時間を表示します
- 開発サーバーでは自動再ビルドとホットリロードが使えます
