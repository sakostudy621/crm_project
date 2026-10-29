# !/usr/bin/env bash
# エラーが起きたら即停止する設定
set -o errexit

# 1.ライブラリのインストール
pip install -r requirements.txt

# 2.静的ファイルの収集(CSS等をstaticfilesフォルダに集める)
python manage.py collectstatic --no-input

# 3.データベースのマイグレーション(本番DBにテーブル作成)
python manage.py migrate

# もし環境変数が変更されていたら実行する
if [[ -n "$DJANGO_SUPERUSER_USERNAME" ]]; then
    echo "Creating superuser..."
    #  --noinut:対話入力をスキップ
    # || true:すでにユーザーが存在してエラーになっても、無視して次へ進む
    python manage.py createsuperuser --noinput||echo"Superuser already exists."
fi