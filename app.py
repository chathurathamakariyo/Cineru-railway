from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

# ============================================================
# Hardcoded cookies (Python script එකෙන් ගත්තා)
# cf_clearance expire වුණාම මේක update කරන්න
# ============================================================
DEFAULT_COOKIES = {
    '_gid': 'GA1.2.1094272377.1776402540',
    '_gat_gtag_UA_180195992_1': '1',
    '_ga': 'GA1.1.210850885.1776402540',
    '_ga_0S6DVQ9W0M': 'GS2.1.s1776402540$o1$g1$t1776406449$j56$l0$h0',
    'cf_clearance': 'PG91aa_HdgtMbjbedar5pAoAIKrZ.QbtTSxA3X4VDwU-1776406452-1.2.1.1-42viijPMGOVqZn_8fXVXfn7bxGHVx2AV0mlj0f_8fUHrHX47YzIe2q4.aPvprYqMhNdcpfdt6FltIyonkXzZOiz_L8cCxb3bkPpOif85K2ktfCI7zq08BGJ8_TJkuORr98q6.urLsd5uGBc_RdQpWLhTefd8D0a0B3zfqrrGXyD7bgBDaDt.hK8fGgS1Gs6rNNXn9KMZ71ITU0jz4ltD8NoctFTR43aZONMpLV0VyU51QgT_8qkwHtkrciiIXK.tF9j1.ayTrozTfcu.H_bV7X2S4m1t1azVlG05C1wu.vniRsbNvQKBGuY28LsbgRm6u9xENghcP2lK04_V.z0yPg'
}

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Referer': 'https://cineru.lk/once-we-were-us-2026-sinhala-subtitles/',
    'Origin': 'https://cineru.lk'
}


def get_download_links(post_id):
    data = {
        'action': 'cs_download_data',
        'post_id': post_id
    }

    try:
        response = requests.post(
            'https://cineru.lk/wp-admin/admin-ajax.php',
            headers=DEFAULT_HEADERS,
            cookies=DEFAULT_COOKIES,
            data=data,
            timeout=30
        )

        if response.status_code != 200:
            return None, f'Cineru returned HTTP {response.status_code}'

        result = response.json()

        if not result.get('success'):
            return None, 'Cineru API returned success=false'

        html_content = result.get('data', '')
        token_urls = re.findall(
            r'data-link="(https://dl\.cineru\.lk/dl\.php\?token=[^"]+)"',
            html_content
        )
        token_urls = list(dict.fromkeys(token_urls))  # duplicates remove

        return token_urls, None

    except Exception as e:
        return None, str(e)


def download_subtitle(token_url):
    dl_cookies = {
        'cf_clearance': DEFAULT_COOKIES['cf_clearance'],
        '_ga': DEFAULT_COOKIES['_ga'],
        '_gid': DEFAULT_COOKIES['_gid'],
    }
    dl_headers = {
        'User-Agent': DEFAULT_HEADERS['User-Agent'],
        'Referer': 'https://cineru.lk/'
    }

    try:
        dl_response = requests.get(token_url, headers=dl_headers, cookies=dl_cookies, timeout=30)

        if dl_response.status_code != 200:
            return None, None, f'Download failed HTTP {dl_response.status_code}'

        content = dl_response.content
        is_zip = content[:2] == b'PK'

        return content, 'zip' if is_zip else 'srt', None

    except Exception as e:
        return None, None, str(e)


# ============================================================
# GET /links?post_id=98355
# Token URLs list return කරනවා
# ============================================================
@app.route('/links', methods=['GET'])
def links():
    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({'success': False, 'error': 'post_id required'}), 400

    token_urls, error = get_download_links(post_id)

    if error:
        return jsonify({'success': False, 'error': error}), 502

    return jsonify({
        'success': True,
        'post_id': post_id,
        'count': len(token_urls),
        'token_urls': token_urls
    })


# ============================================================
# GET /download?post_id=98355
# පළමු token URL එකෙන් subtitle file download කරලා return කරනවා
# ============================================================
@app.route('/download', methods=['GET'])
def download():
    from flask import send_file
    import io

    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({'success': False, 'error': 'post_id required'}), 400

    # index param — කොයි token URL එක download කරන්නද (default: 0)
    idx = int(request.args.get('index', 0))

    token_urls, error = get_download_links(post_id)
    if error:
        return jsonify({'success': False, 'error': error}), 502

    if not token_urls:
        return jsonify({'success': False, 'error': 'No token URLs found'}), 404

    if idx >= len(token_urls):
        idx = 0

    content, file_type, dl_error = download_subtitle(token_urls[idx])
    if dl_error:
        return jsonify({'success': False, 'error': dl_error}), 502

    mime = 'application/zip' if file_type == 'zip' else 'text/plain'
    filename = f'subtitle_{post_id}.{file_type}'

    return send_file(
        io.BytesIO(content),
        mimetype=mime,
        as_attachment=True,
        download_name=filename
    )


# ============================================================
# GET /
# ============================================================
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Cineru Subtitle Scraper API',
        'endpoints': {
            'GET /links?post_id=98355': 'Token URLs list ගන්න',
            'GET /download?post_id=98355': 'Subtitle file direct download',
            'GET /download?post_id=98355&index=1': 'Second token URL download'
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
