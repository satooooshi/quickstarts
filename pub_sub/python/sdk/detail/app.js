import { addDetail, getDetailById } from './data.js'

import express from "express"
import bodyParser from 'body-parser'
import cors from 'cors'
const app = express();
const host = '0.0.0.0'
const port = 3006



app.use(cors());

// urlencodedとjsonは別々に初期化する
app.use(bodyParser.urlencoded({
  extended: true
}));
app.use(bodyParser.json());

app.get('/api/detail/test', function (req, res) {
    return res.send({
      data:'hello detail'
    })
})

app.get('/detail/:id', (req, res) => {
  const id = req.params.id;
  const result = getDetailById(id)
  return res.status(200).send(result)
});

app.get('/detail/:id/:content', (req, res) => {
  const id = req.params.id;
  const content = req.params.content
  addDetail({id:id, content:content})
  return res.status(200).send({id:id, content:content})
});

app.listen(port, host, () => console.log('detail service is running on '+host+':'+port));

