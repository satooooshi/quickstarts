# Getting Started with Create React App auth tutorial commerceJs react router dom

This project is [Auth tutorial App with react-router and commerceJs](https://www.digitalocean.com/community/tutorials/how-to-add-login-authentication-to-react-applications).

UI reference
https://github.com/mui/material-ui/tree/master/docs/data/material/getting-started/templates/sign-in



## Available Scripts
react開発の流れこれ参考
あとrouterチュートリアルの参考にできる


index.jsで親のインポート先決める

import App from './components/App/App';
import reportWebVitals from './reportWebVitals';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);


how to save token??
const [token, setToken] = useState();
sessionStorage function setToken(userToken) {, <Login setToken={setToken} />
localStorage
Creating a Custom Token Hook 

セッションストレージ（Session Storage）は、ブラウザが起動している間だけ有効です。
一方、ローカルストレージ（Local Storage）は、オリジン単位でデータを管理します。 ブラウザを閉じてもデータが消えることはありませんし、異なるウィンドウ／タブからも同じデータを共有することが可能です。


material UI installation
npm install @mui/material @emotion/react @emotion/styled --save
npm install @mui/material @mui/styled-engine-sc styled-components --save
npm install @mui/icons-material --save


ほとんどのユースケースでは、(Input のような)下位レベルのコンポーネントではなく、TextField を使うべきです。
https://jpcodeqa.com/q/5355eb383e8e8ecf7d1c5308f8f544ce