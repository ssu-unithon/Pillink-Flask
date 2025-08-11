const axios = require("axios");
/*
axios
  .get("http://127.0.0.1:3000/inquiry_answer", {
    params: { corpus: "알림 설정은 어떻게 설정하나요" },
  })
  .then((res) => {
    console.log("응답:", res.data);
  })
  .catch((err) => {
    if (err.response) {
      console.error("상태:", err.response.status);
      console.error("바디:", err.response.data);
    } else {
      console.error("에러:", err.message);
    }
  });
*/
/*
axios
  .get("http://127.0.0.1:3000/inquiry_answer", {
    params: {
      corpus: "이 약은 상호작용하는 약이 있나요?", // 엑셀 9번 질문 내용
      //entpName: "한미약품", // 업체명
      itemName: "타이레놀", // 제품명
    },
  })
  .then((res) => {
    console.log("응답:", res.data);
  })
  .catch((err) => {
    if (err.response) {
      console.error("상태:", err.response.status);
      console.error("바디:", err.response.data);
    } else {
      console.error("에러:", err.message);
    }
  });
*/

axios
  .get("http://127.0.0.1:3000/inquiry_answer", {
    params: {
      corpus: "칼타제산과 상호작용하는 약을 알려줘", // 엑셀 9번 질문 내용
      //entpName: "한미약품", // 업체명
      //itemName: "타이레놀", // 제품명
    },
  })
  .then((res) => {
    console.log("응답:", res.data);
  })
  .catch((err) => {
    if (err.response) {
      console.error("상태:", err.response.status);
      console.error("바디:", err.response.data);
    } else {
      console.error("에러:", err.message);
    }
  });
