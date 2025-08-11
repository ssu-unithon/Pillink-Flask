from flask import Flask, request, jsonify
import os, traceback
import pandas as pd
import numpy as np
import requests, json
from urllib.parse import unquote
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

#파일 위치 확인
print("CWD:", os.getcwd())
print("FILE DIR:", os.path.dirname(os.path.abspath(__file__)))

#약 정보
def get_medicine_info(entpName=None, itemName=None):
    try:
        if not entpName and not itemName:
            return None, {"error": "업체명과 제품명을 입력해주세요"}

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
            return None, {"message": "검색 결과가 없습니다."}

        item = items[0]
        result = {
            '효능': item.get('efcyQesitm'),
            '사용법': item.get('useMethodQesitm'),
            '주의사항': item.get('atpnQesitm'),
            '상호작용': item.get('intrcQesitm'),
            '부작용': item.get('seQesitm'),
            '보관법': item.get('depositMethodQesitm')
        }
        return result,None

    #예외 처리 
    except Exception as e:
        print("medicine_info ERROR:", repr(e))
        traceback.print_exc()
        return None, {"error": "server error", "detail": str(e)}


#루트(확인 용도)
@app.get("/")
def home():
    return "Flask Servre Testing..."


#질문_대답 
@app.get("/inquiry_answer")
def inquiry_answer():
    try:
        #문의사항
        corpus = (request.args.get('corpus') or "").strip()
        if not corpus:
            return jsonify({"error": "문의사항을 입력하세요"}), 400

        #질문_대답 파일
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Question_Answer.xlsx")
        if not os.path.exists(qa_path):
            return jsonify({"error": "QA file 존재하지 않음", "path": qa_path}), 500
        
        QA = pd.read_excel(qa_path)
        QA["question"] = QA["question"].fillna("")
        QA["answer"] = QA["answer"].fillna("")

        #문장 유사도 평가 모델
        model_name = 'jhgan/ko-sbert-sts'
        embedder = SentenceTransformer(model_name)
        
        #임베딩
        corpus_emb = embedder.encode(corpus, convert_to_tensor=True)
        query_emb = embedder.encode(QA['question'].tolist(), convert_to_tensor=True)

        #유사도 계산
        cos_scores = util.pytorch_cos_sim(query_emb, corpus_emb).cpu().numpy().ravel()

        #최상위 1개
        best_idx = int(np.argmax(cos_scores))
        best_score = float(cos_scores[best_idx])

        #유사도가 너무 낮은 경우 결과 없음 처리
        if best_score <= 0.35:
            return jsonify({"result": "결과 없음", "score": best_score})

        response = {
            "question": QA['question'].iloc[best_idx],
            "answer": QA['answer'].iloc[best_idx],
            "score": best_score
        }

        if best_idx in [7,8,9]:
            #entpName = request.args.get('entpName')
            
            
            itemName = request.args.get('itemName')
            
            
            
            
            medicine_result, err = get_medicine_info(entpName,itemName)
            if medicine_result:
                if best_idx == 7:
                    response['medicine_info'] = medicine_result['사용법']
                elif best_idx == 8:
                    response['medicine_info'] = medicine_result['부작용']
                elif best_idx == 9:
                    response['medicine_info'] = medicine_result['상호작용']
                print("best_idx:", best_idx, "-------------")
            else:
                response["medicine_info"] = err or {"message": "약 정보 조회 실패"}
        
        return jsonify(response)

    #예외 처리
    except Exception as e:
        print("inquiry_answer ERROR:", repr(e))
        traceback.print_exc() 
        return jsonify({"error": "server error", "detail": str(e)}), 500

#약 정보
@app.get('/medicine_info')
def medicine_info():
    entpName = request.args.get('entpName')
    itemName = request.args.get('itemName')
    if not entpName and not itemName:
        return jsonify({"error": "업체명과 제품명을 입력해주세요"}), 400

    medicine_result, med_err = get_medicine_info(entpName, itemName)
    if medicine_result:
        return jsonify(medicine_result)
    return jsonify(med_err), 500 if "error" in (med_err or {}) else 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

