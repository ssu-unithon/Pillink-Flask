from flask import Flask, request, jsonify
import os, traceback
import pandas as pd
import numpy as np
import requests, json
from urllib.parse import unquote
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# 어디서 파일을 찾는지 로그로 확인
print("CWD:", os.getcwd())
print("FILE DIR:", os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
def home():
    return "Flask Servre Testing..."

@app.get("/inquiry_answer")
def inquiry_answer():
    print("inquurifaidfjaidf")
    try:
        corpus = (request.args.get('corpus') or "").strip()
        if not corpus:
            return jsonify({"error": "corpus(문의사항)를 입력하세요"}), 400

        #질문_대답 파일
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Question_Answer.xlsx")
        if not os.path.exists(qa_path):
            return jsonify({"error": "QA file 존재하지 않음음", "path": qa_path}), 500
        
        QA = pd.read_excel(qa_path)
        QA["question"] = QA["question"].fillna("")
        QA["answer"] = QA["answer"].fillna("")

        model_name = 'jhgan/ko-sbert-sts'
        print("모델 로드 시작")
        embedder = SentenceTransformer(model_name)
        print("모델 로드 완료")
        
        # 임베딩
        corpus_emb = embedder.encode(corpus, convert_to_tensor=True)
        query_emb = embedder.encode(QA['question'].tolist(), convert_to_tensor=True)

        # 유사도 계산
        cos_scores = util.pytorch_cos_sim(query_emb, corpus_emb).cpu().numpy().ravel()

        # 최상위 1개
        best_idx = int(np.argmax(cos_scores))
        best_score = float(cos_scores[best_idx])

        if best_score <= 0.35:
            return jsonify({"result": "결과 없음", "score": best_score})

        return jsonify({
            "answer": QA['answer'].iloc[best_idx],
            "question": QA['question'].iloc[best_idx],
            "score": best_score
        })

    except Exception as e:
        print("inquiry_answer ERROR:", repr(e))
        traceback.print_exc()  # 콘솔에 자세한 Traceback
        return jsonify({"error": "server error", "detail": str(e)}), 500


@app.get('/medicine_info')
def medicine_info():
    try:
        entpName = request.args.get('entpName')
        itemName = request.args.get('itemName')

        if not entpName and not itemName:
            return jsonify({"error": "업체명(entpName) 또는 제품명(itemName) 중 하나는 필요합니다."}), 400

        # 인증키
        serviceKey = unquote('0zt0FUkd5LMT9nSUvUkxnyXvIkqWli%2Bbk0ulrUNTqhSlAfcMw0a9sMwR4FrMOjdwJ8m3%2Bt9HNGzvrMv8nUB6OQ%3D%3D')

        url = 'http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList'
        params = {
            'serviceKey': serviceKey, 'pageNo': '1', 'numOfRows': '3',
            'entpName': entpName or '', 'itemName': itemName or '',
            'itemSeq': '', 'efcyQesitm': '', 'useMethodQesitm': '', 'atpnWarnQesitm': '',
            'atpnQesitm': '', 'intrcQesitm': '', 'seQesitm': '', 'depositMethodQesitm': '',
            'openDe': '', 'updateDe': '', 'type': 'json'
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        payload = r.json()
        items = (payload.get('body') or {}).get('items') or []

        if not items:
            return jsonify({"message": "검색 결과가 없습니다."})

        item = items[0]
        result = {
            '효능': item.get('efcyQesitm'),
            '사용법': item.get('useMethodQesitm'),
            '주의사항': item.get('atpnQesitm'),
            '상호작용': item.get('intrcQesitm'),
            '부작용': item.get('seQesitm'),
            '보관법': item.get('depositMethodQesitm')
        }
        return jsonify(result)

    except Exception as e:
        print("medicine_info ERROR:", repr(e))
        traceback.print_exc()
        return jsonify({"error": "server error", "detail": str(e)}), 500


if __name__ == '__main__':
    # 디버그 켜면 에러 페이지가 더 자세히 나옵니다.
    app.run(host='0.0.0.0', port=3000, debug=True)
